"""Retell AI webhook handlers.

Handles webhook events from Retell AI:
- call_started: Initialize call record
- call_ended: Update call status and store transcript  
- call_analyzed: Trigger post-processing

The webhook endpoint receives events and dispatches to appropriate handlers.
"""

import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from supabase import Client

from app.core.database import get_db
from app.core.config import get_settings
from app.core.constants import RetellEventType
from app.core.state_machine import StateMachine
from app.models.schemas import ScenarioType
from app.services.post_processing import get_post_processing_service, PostProcessingService
from app.webhooks.models import RetellWebhookPayload, WebhookResponse
from app.webhooks.security import verify_webhook_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# =============================================================================
# Payload Normalization
# =============================================================================

def normalize_retell_payload(payload_dict: dict) -> dict:
    """
    Normalize Retell webhook payload structure.
    
    Retell nests call data inside a 'call' object, but our models
    expect a flat structure. This function flattens the payload.
    
    Args:
        payload_dict: Raw webhook payload from Retell
        
    Returns:
        Normalized payload with call fields at top level
    """
    if "call_id" in payload_dict:
        # Already normalized
        return payload_dict
    
    if "call" not in payload_dict:
        return payload_dict
    
    call_obj = payload_dict.get("call", {})
    if not isinstance(call_obj, dict):
        return payload_dict
    
    # Flatten call object fields to top level
    normalized = {
        "event": payload_dict.get("event"),
        "call_id": call_obj.get("call_id"),
        "agent_id": call_obj.get("agent_id"),
        "call_type": call_obj.get("call_type"),
        "call_status": call_obj.get("call_status"),
        "duration_ms": call_obj.get("duration_ms"),
        "transcript": call_obj.get("transcript"),
        "transcript_object": call_obj.get("transcript_object", []),
        "metadata": call_obj.get("metadata"),
        "start_timestamp": call_obj.get("start_timestamp"),
        "end_timestamp": call_obj.get("end_timestamp"),
    }
    
    return normalized


# =============================================================================
# Event Handlers
# =============================================================================

async def handle_call_started(
    payload: RetellWebhookPayload,
    db: Client,
) -> dict:
    """
    Handle call_started event.
    
    - Look up call record by metadata (if we created it)
    - Update call status to 'in_progress'
    - Store Retell call_id for future reference
    """
    logger.info(f"Call started: {payload.call_id}")
    
    # Extract our internal call ID from metadata
    internal_call_id = None
    if payload.metadata:
        internal_call_id = payload.metadata.get("internal_call_id")
    
    if internal_call_id:
        # Update existing call record
        update_data = {
            "retell_call_id": payload.call_id,
            "status": "in_progress",
            "started_at": datetime.utcnow().isoformat(),
        }
        
        db.table("calls").update(update_data).eq("id", internal_call_id).execute()
        logger.info(f"Updated call {internal_call_id} to in_progress")
    else:
        # Create new call record for inbound/unexpected calls
        logger.warning(f"No internal_call_id in metadata for call {payload.call_id}")
    
    return {"status": "processed", "call_id": payload.call_id}


async def handle_call_ended(
    payload: RetellWebhookPayload,
    db: Client,
) -> dict:
    """
    Handle call_ended event.
    
    - Update call status to 'completed'
    - Store call duration
    - Save transcript to database
    """
    logger.info(f"Call ended: {payload.call_id}")
    
    # Find call by retell_call_id
    call_response = db.table("calls").select("*").eq(
        "retell_call_id", payload.call_id
    ).execute()
    
    if not call_response.data:
        logger.warning(f"No call record found for retell_call_id: {payload.call_id}")
        return {"status": "no_record", "call_id": payload.call_id}
    
    call = call_response.data[0]
    call_id = call["id"]
    
    # Calculate duration
    duration_seconds = None
    if payload.duration_ms:
        duration_seconds = payload.duration_ms // 1000
    
    # Update call record
    update_data = {
        "status": "completed",
        "ended_at": datetime.utcnow().isoformat(),
        "duration_seconds": duration_seconds,
    }
    
    db.table("calls").update(update_data).eq("id", call_id).execute()
    
    # Store transcript
    if payload.transcript or payload.transcript_object:
        transcript_data = {
            "call_id": call_id,
            "raw_transcript": payload.transcript,
            "utterances": [u.model_dump() for u in (payload.transcript_object or [])],
        }
        
        db.table("transcripts").insert(transcript_data).execute()
        logger.info(f"Stored transcript for call {call_id}")
    
    # Check for emergency in transcript
    if payload.transcript:
        state_machine = StateMachine()
        is_emergency = state_machine.handle_emergency(payload.transcript)
        
        if is_emergency:
            logger.warning(f"Emergency detected in call {call_id}: {state_machine.context.emergency_type}")
    
    return {"status": "processed", "call_id": payload.call_id, "internal_call_id": call_id}


async def process_transcript_task(
    call_id: str,
    transcript: str,
    scenario_type: ScenarioType,
    db: Client,
) -> None:
    """
    Background task for processing transcript.
    
    This function is called asynchronously to avoid blocking the webhook response.
    """
    from uuid import UUID
    
    post_processing_service = get_post_processing_service()
    
    try:
        await post_processing_service.process_transcript(
            call_id=UUID(call_id),
            transcript=transcript,
            scenario_type=scenario_type,
            db=db,
        )
    except Exception as e:
        logger.error(f"Error in background transcript processing for call {call_id}: {e}")


async def handle_call_analyzed(
    payload: RetellWebhookPayload,
    db: Client,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Handle call_analyzed event.
    
    - Trigger post-processing to extract structured data
    - Extracts structured information from transcript using OpenAI GPT-4
    - Falls back to regex extraction if OpenAI fails
    """
    logger.info(f"Call analyzed: {payload.call_id}")
    
    # Find call by retell_call_id
    call_response = db.table("calls").select("*").eq(
        "retell_call_id", payload.call_id
    ).execute()
    
    if not call_response.data:
        logger.warning(f"No call record found for retell_call_id: {payload.call_id}")
        return {"status": "no_record", "call_id": payload.call_id}
    
    call = call_response.data[0]
    call_id = call["id"]
    agent_config_id = call.get("agent_config_id")
    
    # Determine scenario_type from agent_config (no hardcoded defaults)
    scenario_type = None
    if agent_config_id:
        config_response = db.table("agent_configs").select("scenario_type").eq(
            "id", agent_config_id
        ).execute()
        if config_response.data:
            scenario_type_str = config_response.data[0].get("scenario_type")
            try:
                scenario_type = ScenarioType(scenario_type_str)
            except ValueError:
                logger.error(f"Unknown scenario_type {scenario_type_str} for agent_config {agent_config_id}")
    
    if not scenario_type:
        logger.error(f"No valid scenario_type found for call {call_id} (agent_config_id: {agent_config_id}). Cannot process transcript.")
        return {
            "status": "error",
            "call_id": payload.call_id,
            "message": "Missing or invalid scenario_type for post-processing"
        }
    
    # Store analysis data if provided by Retell
    if payload.call_analysis:
        logger.info(f"Retell analysis for call {call_id}: {payload.call_analysis}")
    
    # Trigger post-processing in background
    if payload.transcript:
        background_tasks.add_task(
            process_transcript_task,
            str(call_id),
            payload.transcript,
            scenario_type,
            db,
        )
        logger.info(f"Queued transcript processing for call {call_id} (scenario: {scenario_type.value})")
    else:
        logger.warning(f"No transcript available for call {call_id}, skipping post-processing")
    
    return {
        "status": "processed",
        "call_id": payload.call_id,
        "internal_call_id": call_id,
        "analysis_received": payload.call_analysis is not None,
        "post_processing_queued": payload.transcript is not None,
    }


# =============================================================================
# Main Webhook Endpoint
# =============================================================================

@router.post("/retell", response_model=WebhookResponse)
async def retell_webhook(
    background_tasks: BackgroundTasks,
    body: bytes = Depends(verify_webhook_signature),
    db: Client = Depends(get_db),
) -> WebhookResponse:
    """
    Main webhook endpoint for Retell AI events.
    
    Receives webhook events and dispatches to appropriate handlers:
    - call_started: Initialize call record
    - call_ended: Store transcript and update status
    - call_analyzed: Trigger post-processing
    
    Webhook signature is verified before processing.
    """
    try:
        # Parse and normalize payload
        payload_dict = json.loads(body)
        normalized = normalize_retell_payload(payload_dict)
        payload = RetellWebhookPayload(**normalized)
        
        logger.info(f"Received Retell webhook: {payload.event} for call {payload.call_id}")
        
        # Dispatch to appropriate handler
        if payload.event == RetellEventType.CALL_STARTED:
            result = await handle_call_started(payload, db)
        elif payload.event == RetellEventType.CALL_ENDED:
            result = await handle_call_ended(payload, db)
        elif payload.event == RetellEventType.CALL_ANALYZED:
            result = await handle_call_analyzed(payload, db, background_tasks)
        else:
            logger.warning(f"Unknown webhook event type: {payload.event}")
            result = {"status": "unknown_event", "event": payload.event}
        
        return WebhookResponse(
            success=True,
            message=f"Processed {payload.event} event",
            data=result,
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )


# =============================================================================
# Health Check for Webhooks
# =============================================================================

@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoint."""
    return {"status": "healthy", "endpoint": "webhooks"}


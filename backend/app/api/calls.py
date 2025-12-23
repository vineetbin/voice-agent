"""Call Management API endpoints.

Provides endpoints for creating, listing, and retrieving call records.
Calls are created when a test call is triggered and updated as the call progresses.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.core.database import get_db
from app.models.schemas import (
    Call,
    CallCreate,
    CallStatus,
    CallType,
    CallWithDetails,
    CallTriggerRequest,
    CallTriggerResponse,
    ScenarioType,
)
from app.services.retell import get_retell_service, RetellService, RetellServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calls", tags=["Calls"])

# Table names
CALLS_TABLE = "calls"
TRANSCRIPTS_TABLE = "transcripts"
SUMMARIES_TABLE = "structured_summaries"


@router.get("", response_model=List[Call])
async def list_calls(
    status_filter: Optional[CallStatus] = Query(None, alias="status", description="Filter by call status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Client = Depends(get_db),
) -> List[Call]:
    """
    List all calls with optional filtering and pagination.
    
    Results are ordered by creation date (newest first).
    """
    query = db.table(CALLS_TABLE).select("*")
    
    if status_filter:
        query = query.eq("status", status_filter.value)
    
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
    
    response = query.execute()
    return response.data


@router.get("/{call_id}", response_model=CallWithDetails)
async def get_call(
    call_id: UUID,
    db: Client = Depends(get_db),
) -> CallWithDetails:
    """
    Get a specific call with its transcript and structured summary.
    
    This endpoint returns the complete call data needed for the results view.
    Raises 404 if the call is not found.
    """
    # Get the call
    call_response = db.table(CALLS_TABLE).select("*").eq("id", str(call_id)).execute()
    
    if not call_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with id {call_id} not found"
        )
    
    call_data = call_response.data[0]
    
    # Get related transcript
    transcript_response = db.table(TRANSCRIPTS_TABLE).select("*").eq(
        "call_id", str(call_id)
    ).limit(1).execute()
    
    # Get related structured summary
    summary_response = db.table(SUMMARIES_TABLE).select("*").eq(
        "call_id", str(call_id)
    ).limit(1).execute()
    
    # Build response with related data
    result = {
        **call_data,
        "transcript": transcript_response.data[0] if transcript_response.data else None,
        "structured_summary": summary_response.data[0] if summary_response.data else None,
    }
    
    return result


@router.post("", response_model=Call, status_code=status.HTTP_201_CREATED)
async def create_call(
    call: CallCreate,
    db: Client = Depends(get_db),
) -> Call:
    """
    Create a new call record.
    
    This is called when the admin triggers a test call from the UI.
    The call starts in 'pending' status and will be updated by webhooks.
    """
    # If agent_config_id is provided, verify it exists
    if call.agent_config_id:
        config_check = db.table("agent_configs").select("id").eq(
            "id", str(call.agent_config_id)
        ).execute()
        
        if not config_check.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent configuration with id {call.agent_config_id} not found"
            )
    
    # Create the call record
    call_data = call.model_dump(mode="json")
    if call_data.get("agent_config_id"):
        call_data["agent_config_id"] = str(call_data["agent_config_id"])
    
    response = db.table(CALLS_TABLE).insert(call_data).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create call record"
        )
    
    return response.data[0]


@router.post("/trigger", response_model=CallTriggerResponse)
async def trigger_call(
    request: CallTriggerRequest,
    db: Client = Depends(get_db),
    retell: RetellService = Depends(get_retell_service),
) -> CallTriggerResponse:
    """
    Trigger a new call to a driver.
    
    This is the main endpoint for the "Start Test Call" button.
    It will:
    1. Get the active agent configuration for the scenario
    2. Update the Retell agent with the config's prompt
    3. Create the call (phone or web)
    4. Save the call record in our database
    
    For web calls, returns an access_token for the Retell Web SDK.
    """
    # 1. Get the single active configuration (unified config handles both scenarios)
    config_response = db.table("agent_configs").select("*").eq(
        "is_active", True
    ).limit(1).execute()
    
    if not config_response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active configuration found. Please activate a configuration in the Configuration page first."
        )
    
    config = config_response.data[0]
    
    # Derive scenario_type from the active config (not from request)
    scenario_type = ScenarioType(config.get("scenario_type", ScenarioType.DISPATCH_CHECKIN.value))
    
    # 2. Update Retell agent with config's prompt and settings (partial update)
    # Only updates the specific fields we manage, preserving other Retell settings
    try:
        # Replace placeholders in initial message
        initial_message = config.get("initial_message") or ""
        initial_message = initial_message.replace("{{driver_name}}", request.driver_name)
        initial_message = initial_message.replace("{{load_number}}", request.load_number)
        
        retell.update_agent(
            system_prompt=config["system_prompt"],
            initial_message=initial_message if initial_message else None,
            enable_backchanneling=config.get("enable_backchanneling"),
            interruption_sensitivity=config.get("interruption_sensitivity"),
        )
    except RetellServiceError as e:
        logger.error(f"Failed to update Retell agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to configure Retell agent: {str(e)}"
        )
    
    # 3. Create call record in our database first
    call_data = {
        "driver_name": request.driver_name,
        "phone_number": request.phone_number,
        "load_number": request.load_number,
        "agent_config_id": config["id"],
        "call_type": request.call_type.value,
        "status": CallStatus.PENDING.value,
    }
    
    call_response = db.table(CALLS_TABLE).insert(call_data).execute()
    
    if not call_response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create call record"
        )
    
    internal_call_id = call_response.data[0]["id"]
    
    # 4. Create the call via Retell API
    try:
        dynamic_variables = {
            "driver_name": request.driver_name,
            "load_number": request.load_number,
        }
        
        metadata = {
            "internal_call_id": internal_call_id,
            "scenario_type": scenario_type.value,  # Use scenario_type from active config
        }
        
        access_token = None
        
        if request.call_type == CallType.WEB:
            # Create web call (for non-USA testing)
            retell_call = retell.create_web_call(
                metadata=metadata,
                dynamic_variables=dynamic_variables,
            )
            access_token = retell_call.access_token
        else:
            # Create phone call
            if not request.phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number is required for phone calls"
                )
            retell_call = retell.create_phone_call(
                to_number=request.phone_number,
                metadata=metadata,
                dynamic_variables=dynamic_variables,
            )
        
        # Update our call record with Retell's call ID
        db.table(CALLS_TABLE).update({
            "retell_call_id": retell_call.call_id,
            "status": CallStatus.IN_PROGRESS.value,
        }).eq("id", internal_call_id).execute()
        
        logger.info(f"Triggered {request.call_type.value} call {retell_call.call_id}")
        
        return CallTriggerResponse(
            call_id=internal_call_id,
            retell_call_id=retell_call.call_id,
            status=CallStatus.IN_PROGRESS,
            call_type=request.call_type,
            access_token=access_token,
        )
        
    except RetellServiceError as e:
        # Mark call as failed
        db.table(CALLS_TABLE).update({
            "status": CallStatus.FAILED.value,
        }).eq("id", internal_call_id).execute()
        
        logger.error(f"Failed to create Retell call: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create call via Retell: {str(e)}"
        )


@router.patch("/{call_id}/status", response_model=Call)
async def update_call_status(
    call_id: UUID,
    new_status: CallStatus,
    db: Client = Depends(get_db),
) -> Call:
    """
    Update a call's status.
    
    This endpoint is primarily used internally by webhook handlers
    to update call status as it progresses through its lifecycle.
    """
    # Check if call exists
    existing = db.table(CALLS_TABLE).select("*").eq("id", str(call_id)).execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with id {call_id} not found"
        )
    
    # Update status
    response = db.table(CALLS_TABLE).update({
        "status": new_status.value
    }).eq("id", str(call_id)).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update call status"
        )
    
    return response.data[0]


@router.get("/recent/completed", response_model=List[CallWithDetails])
async def get_recent_completed_calls(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Client = Depends(get_db),
) -> List[CallWithDetails]:
    """
    Get recent completed calls with their transcripts and summaries.
    
    This is useful for the admin dashboard to show recent call results.
    """
    # Get recent completed calls
    calls_response = db.table(CALLS_TABLE).select("*").eq(
        "status", CallStatus.COMPLETED.value
    ).order("ended_at", desc=True).limit(limit).execute()
    
    if not calls_response.data:
        return []
    
    # For each call, fetch transcript and summary
    results = []
    for call_data in calls_response.data:
        call_id = call_data["id"]
        
        # Get transcript
        transcript_response = db.table(TRANSCRIPTS_TABLE).select("*").eq(
            "call_id", call_id
        ).limit(1).execute()
        
        # Get summary
        summary_response = db.table(SUMMARIES_TABLE).select("*").eq(
            "call_id", call_id
        ).limit(1).execute()
        
        results.append({
            **call_data,
            "transcript": transcript_response.data[0] if transcript_response.data else None,
            "structured_summary": summary_response.data[0] if summary_response.data else None,
        })
    
    return results


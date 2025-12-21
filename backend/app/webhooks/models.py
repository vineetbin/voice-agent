"""Pydantic models for Retell AI webhook payloads.

These models define the structure of webhook events received from Retell AI.
See: https://docs.retellai.com/api-references/webhooks
"""

from datetime import datetime
from typing import Optional, List, Any, Literal
from pydantic import BaseModel, Field


# =============================================================================
# Transcript Models
# =============================================================================

class TranscriptUtterance(BaseModel):
    """Single utterance in a call transcript."""
    role: Literal["agent", "user"]
    content: str
    words: Optional[List[dict]] = None
    
    
class TranscriptData(BaseModel):
    """Transcript data from Retell."""
    transcript: Optional[str] = None
    transcript_object: Optional[List[TranscriptUtterance]] = Field(default_factory=list)
    transcript_with_tool_calls: Optional[List[dict]] = None


# =============================================================================
# Call Analysis Models
# =============================================================================

class CallAnalysis(BaseModel):
    """Analysis data from call_analyzed event."""
    call_summary: Optional[str] = None
    user_sentiment: Optional[str] = None
    call_successful: Optional[bool] = None
    custom_analysis_data: Optional[dict] = None


# =============================================================================
# Webhook Event Models
# =============================================================================

class RetellWebhookEvent(BaseModel):
    """Base model for all Retell webhook events."""
    event: str
    call_id: str = Field(..., alias="call_id")
    
    class Config:
        populate_by_name = True


class CallStartedEvent(RetellWebhookEvent):
    """Webhook payload for call_started event."""
    event: Literal["call_started"] = "call_started"
    
    # Call metadata
    agent_id: Optional[str] = None
    call_type: Optional[str] = None  # "web_call" | "phone_call"
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    direction: Optional[str] = None  # "inbound" | "outbound"
    
    # Custom metadata passed when creating the call
    metadata: Optional[dict] = None
    retell_llm_dynamic_variables: Optional[dict] = None


class CallEndedEvent(RetellWebhookEvent):
    """Webhook payload for call_ended event."""
    event: Literal["call_ended"] = "call_ended"
    
    # Call metadata
    agent_id: Optional[str] = None
    call_type: Optional[str] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    direction: Optional[str] = None
    
    # Call timing
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    duration_ms: Optional[int] = None
    
    # Call status
    call_status: Optional[str] = None  # "ended" | "error" | etc.
    disconnection_reason: Optional[str] = None
    
    # Transcript
    transcript: Optional[str] = None
    transcript_object: Optional[List[TranscriptUtterance]] = Field(default_factory=list)
    
    # Custom metadata
    metadata: Optional[dict] = None
    retell_llm_dynamic_variables: Optional[dict] = None


class CallAnalyzedEvent(RetellWebhookEvent):
    """Webhook payload for call_analyzed event."""
    event: Literal["call_analyzed"] = "call_analyzed"
    
    # Call metadata
    agent_id: Optional[str] = None
    call_type: Optional[str] = None
    
    # Transcript
    transcript: Optional[str] = None
    transcript_object: Optional[List[TranscriptUtterance]] = Field(default_factory=list)
    
    # Analysis results
    call_analysis: Optional[CallAnalysis] = None
    
    # Custom metadata
    metadata: Optional[dict] = None


# =============================================================================
# Unified Webhook Payload
# =============================================================================

class RetellWebhookPayload(BaseModel):
    """
    Unified webhook payload that can handle any Retell event.
    
    Use this for initial parsing, then cast to specific event type.
    """
    event: str
    call_id: str
    
    # Common fields
    agent_id: Optional[str] = None
    call_type: Optional[str] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    direction: Optional[str] = None
    
    # Timing (for call_ended)
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    duration_ms: Optional[int] = None
    
    # Status (for call_ended)
    call_status: Optional[str] = None
    disconnection_reason: Optional[str] = None
    
    # Transcript
    transcript: Optional[str] = None
    transcript_object: Optional[List[TranscriptUtterance]] = Field(default_factory=list)
    
    # Analysis (for call_analyzed)
    call_analysis: Optional[CallAnalysis] = None
    
    # Custom metadata
    metadata: Optional[dict] = None
    retell_llm_dynamic_variables: Optional[dict] = None
    
    class Config:
        extra = "allow"  # Allow additional fields we haven't modeled


# =============================================================================
# Response Models
# =============================================================================

class WebhookResponse(BaseModel):
    """Standard response for webhook endpoints."""
    success: bool
    message: str
    data: Optional[dict] = None


"""Pydantic models for API request/response validation.

These models map directly to the database schema and provide:
- Type validation for API inputs
- Serialization for API responses  
- Documentation via OpenAPI/Swagger
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Enums - Type-safe constants matching database constraints
# =============================================================================

class ScenarioType(str, Enum):
    """Available agent scenario types."""
    DISPATCH_CHECKIN = "dispatch_checkin"
    EMERGENCY = "emergency"


class CallStatus(str, Enum):
    """Call lifecycle states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CallType(str, Enum):
    """How the call is made."""
    PHONE = "phone"
    WEB = "web"


class CallOutcome(str, Enum):
    """Possible call outcomes for structured summary."""
    IN_TRANSIT_UPDATE = "In-Transit Update"
    ARRIVAL_CONFIRMATION = "Arrival Confirmation"
    EMERGENCY_ESCALATION = "Emergency Escalation"


class DriverStatus(str, Enum):
    """Driver status options for dispatch check-in."""
    DRIVING = "Driving"
    DELAYED = "Delayed"
    ARRIVED = "Arrived"
    UNLOADING = "Unloading"


class EmergencyType(str, Enum):
    """Emergency type classification."""
    ACCIDENT = "Accident"
    BREAKDOWN = "Breakdown"
    MEDICAL = "Medical"
    OTHER = "Other"


# =============================================================================
# Agent Configuration Models
# =============================================================================

class AgentConfigBase(BaseModel):
    """Base fields for agent configuration."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scenario_type: ScenarioType
    system_prompt: str = Field(..., min_length=1)
    initial_message: Optional[str] = None
    
    # Retell AI advanced settings (Task A requirements)
    enable_backchanneling: bool = True
    enable_filler_words: bool = True
    interruption_sensitivity: float = Field(default=0.5, ge=0.0, le=1.0)
    
    is_active: bool = False


class AgentConfigCreate(AgentConfigBase):
    """Schema for creating a new agent configuration."""
    pass


class AgentConfigUpdate(BaseModel):
    """Schema for updating an agent configuration. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scenario_type: Optional[ScenarioType] = None
    system_prompt: Optional[str] = Field(None, min_length=1)
    initial_message: Optional[str] = None
    enable_backchanneling: Optional[bool] = None
    enable_filler_words: Optional[bool] = None
    interruption_sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None


class AgentConfig(AgentConfigBase):
    """Complete agent configuration with database fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Call Models
# =============================================================================

class CallBase(BaseModel):
    """Base fields for a call record."""
    driver_name: str = Field(..., min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=50)
    load_number: str = Field(..., min_length=1, max_length=100)
    agent_config_id: Optional[UUID] = None
    call_type: CallType = CallType.PHONE


class CallCreate(CallBase):
    """Schema for creating a new call."""
    pass


class CallUpdate(BaseModel):
    """Schema for updating a call. Used internally for status updates."""
    status: Optional[CallStatus] = None
    retell_call_id: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


class Call(CallBase):
    """Complete call record with database fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    retell_call_id: Optional[str] = None
    status: CallStatus = CallStatus.PENDING
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Transcript Models
# =============================================================================

class Utterance(BaseModel):
    """Single utterance in a conversation."""
    role: str  # "agent" or "user"
    content: str
    timestamp: Optional[float] = None


class TranscriptBase(BaseModel):
    """Base fields for a transcript."""
    call_id: UUID
    raw_transcript: Optional[str] = None
    utterances: List[Utterance] = Field(default_factory=list)


class TranscriptCreate(TranscriptBase):
    """Schema for creating a transcript."""
    pass


class Transcript(TranscriptBase):
    """Complete transcript with database fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime


# =============================================================================
# Structured Summary Models
# =============================================================================

class StructuredSummaryBase(BaseModel):
    """Base fields for structured call summary."""
    call_id: UUID
    call_outcome: Optional[CallOutcome] = None
    
    # Dispatch Check-in fields (Scenario 1)
    driver_status: Optional[DriverStatus] = None
    current_location: Optional[str] = None
    eta: Optional[str] = None
    delay_reason: Optional[str] = None
    unloading_status: Optional[str] = None
    pod_reminder_acknowledged: Optional[bool] = None
    
    # Emergency fields (Scenario 2)
    emergency_type: Optional[EmergencyType] = None
    safety_status: Optional[str] = None
    injury_status: Optional[str] = None
    emergency_location: Optional[str] = None
    load_secure: Optional[bool] = None
    escalation_status: Optional[str] = None
    
    # Raw extraction from LLM
    raw_extraction: Optional[dict[str, Any]] = None


class StructuredSummaryCreate(StructuredSummaryBase):
    """Schema for creating a structured summary."""
    pass


class StructuredSummary(StructuredSummaryBase):
    """Complete structured summary with database fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime


# =============================================================================
# API Response Models
# =============================================================================

class CallWithDetails(Call):
    """Call with related transcript and summary for full results view."""
    transcript: Optional[Transcript] = None
    structured_summary: Optional[StructuredSummary] = None


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_more: bool


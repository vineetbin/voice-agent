"""
Extraction schemas for structured transcript analysis.

These Pydantic models define the exact JSON structure expected
for dispatch check-in and emergency scenarios per the assignment requirements.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# =============================================================================
# Dispatch Check-in Extraction Schema
# =============================================================================

class DispatchCheckInExtraction(BaseModel):
    """
    Structured data extraction for dispatch check-in scenario.
    
    Matches the exact specification from the assignment.
    """
    call_outcome: Literal["In-Transit Update", "Arrival Confirmation"]
    
    driver_status: Literal["Driving", "Delayed", "Arrived", "Unloading"]
    
    current_location: Optional[str] = Field(
        None,
        description="Current location description (e.g., 'I-10 near Indio, CA')"
    )
    
    eta: Optional[str] = Field(
        None,
        description="Estimated time of arrival (e.g., 'Tomorrow, 8:00 AM')"
    )
    
    delay_reason: Optional[Literal["Heavy Traffic", "Weather", "None"]] = Field(
        None,
        description="Reason for delay if applicable"
    )
    
    unloading_status: Optional[Literal["In Door 42", "Waiting for Lumper", "Detention", "N/A"]] = Field(
        None,
        description="Current unloading status"
    )
    
    pod_reminder_acknowledged: Optional[bool] = Field(
        None,
        description="Whether POD reminder was acknowledged"
    )


# =============================================================================
# Emergency Escalation Extraction Schema
# =============================================================================

class EmergencyExtraction(BaseModel):
    """
    Structured data extraction for emergency escalation scenario.
    
    Matches the exact specification from the assignment.
    """
    call_outcome: Literal["Emergency Escalation"] = "Emergency Escalation"
    
    emergency_type: Literal["Accident", "Breakdown", "Medical", "Other"]
    
    safety_status: Optional[str] = Field(
        None,
        description="Safety status description (e.g., 'Driver confirmed everyone is safe')"
    )
    
    injury_status: Optional[str] = Field(
        None,
        description="Injury status description (e.g., 'No injuries reported')"
    )
    
    emergency_location: Optional[str] = Field(
        None,
        description="Emergency location (e.g., 'I-15 North, Mile Marker 123')"
    )
    
    load_secure: Optional[bool] = Field(
        None,
        description="Whether the load is secure"
    )
    
    escalation_status: Literal["Connected to Human Dispatcher"] = "Connected to Human Dispatcher"


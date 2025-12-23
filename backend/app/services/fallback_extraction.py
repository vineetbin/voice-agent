"""
Limited fallback extraction using regex patterns.

Only extracts high-confidence, low-ambiguity categorical fields.
Used when OpenAI extraction is incomplete or missing critical fields.

Fields covered:
- driver_status (categorical: Driving, Delayed, Arrived, Unloading)
- emergency_type (categorical: Accident, Breakdown, Medical, Other)
- call_outcome (categorical: In-Transit Update, Arrival Confirmation, Emergency Escalation)
- load_secure (boolean)
- pod_reminder_acknowledged (boolean)

NOT covered (too free-form for regex):
- location strings
- ETA
- safety/injury descriptions
"""

import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def extract_driver_status(transcript: str) -> Optional[str]:
    """
    Extract driver_status using high-confidence patterns.
    
    Returns one of: "Driving", "Delayed", "Arrived", "Unloading", or None
    """
    transcript_lower = transcript.lower()
    
    # High-confidence patterns
    if re.search(r"\b(arrived|just got here|pulled in|at the destination|made it here)\b", transcript_lower):
        return "Arrived"
    elif re.search(r"\b(unloading|in door|at the dock|unloading now)\b", transcript_lower):
        return "Unloading"
    elif re.search(r"\b(delayed|running late|behind schedule|running behind)\b", transcript_lower):
        return "Delayed"
    elif re.search(r"\b(driving|on the road|still driving|en route|on the way)\b", transcript_lower):
        return "Driving"
    
    return None


def extract_emergency_type(transcript: str) -> Optional[str]:
    """
    Extract emergency_type using high-confidence patterns.
    
    Returns one of: "Accident", "Breakdown", "Medical", "Other", or None
    """
    transcript_lower = transcript.lower()
    
    # High-confidence patterns
    if re.search(r"\b(accident|crash|collision|wreck|hit something)\b", transcript_lower):
        return "Accident"
    elif re.search(r"\b(breakdown|broke down|blowout|tire|mechanical issue|engine problem)\b", transcript_lower):
        return "Breakdown"
    elif re.search(r"\b(medical|sick|ambulance|need medical|having a medical)\b", transcript_lower):
        return "Medical"
    elif re.search(r"\b(emergency|need help|something wrong|pulling over|stopping)\b", transcript_lower):
        # Only return "Other" if we have high confidence it's an emergency
        # but can't classify it further
        return "Other"
    
    return None


def extract_call_outcome(transcript: str, is_emergency: bool = False) -> Optional[str]:
    """
    Extract call_outcome using high-confidence patterns.
    
    Args:
        transcript: Full transcript text
        is_emergency: Whether this is an emergency scenario
        
    Returns one of: "In-Transit Update", "Arrival Confirmation", "Emergency Escalation", or None
    """
    if is_emergency:
        if re.search(r"\b(emergency|accident|breakdown|medical|help|escalat)\b", transcript.lower()):
            return "Emergency Escalation"
        return None
    
    transcript_lower = transcript.lower()
    
    if re.search(r"\b(arrived|just got here|pulled in|at the destination|made it)\b", transcript_lower):
        return "Arrival Confirmation"
    elif re.search(r"\b(driving|in transit|on the way|en route|still driving)\b", transcript_lower):
        return "In-Transit Update"
    
    return None


def extract_load_secure(transcript: str) -> Optional[bool]:
    """
    Extract load_secure using high-confidence boolean patterns.
    
    Returns True, False, or None if uncertain
    """
    transcript_lower = transcript.lower()
    
    # Check negative patterns FIRST (more specific)
    if re.search(r"\b(load\s+(?:is\s+)?not\s+secure|load\s+(?:is\s+)?loose|load\s+shifted|load\s+(?:is\s+)?moving|not\s+secure)\b", transcript_lower):
        return False
    
    # Then check positive patterns (but avoid matching "secure" in "not secure")
    if re.search(r"\b(load\s+(?:is\s+)?secure\b|load\s+(?:is\s+)?fine|load\s+(?:is\s+)?good|no\s+(?:problem|issue))\b", transcript_lower):
        return True
    
    return None


def extract_pod_reminder_acknowledged(transcript: str) -> Optional[bool]:
    """
    Extract pod_reminder_acknowledged using high-confidence boolean patterns.
    
    Returns True, False, or None if uncertain
    """
    transcript_lower = transcript.lower()
    
    # Check if POD was mentioned
    if not re.search(r"\b(pod|proof of delivery|remember to get|don't forget.*pod)\b", transcript_lower):
        return None
    
    # Positive acknowledgment patterns
    if re.search(r"\b(yes|got it|will do|sure|okay|ok|i will|absolutely|definitely)\b", transcript_lower):
        return True
    
    # Negative acknowledgment patterns
    if re.search(r"\b(no|forgot|didn't|won't|can't)\b", transcript_lower):
        return False
    
    return None


def fill_missing_categorical_fields(
    extracted_data: Dict[str, Any],
    transcript: str,
    scenario_type: str,
) -> Dict[str, Any]:
    """
    Fill only missing categorical fields using limited regex fallback.
    
    This function only extracts high-confidence, low-ambiguity fields.
    Free-form fields (location, ETA, descriptions) are left to the LLM.
    
    Args:
        extracted_data: Data extracted by OpenAI (may be incomplete)
        transcript: Full transcript text
        scenario_type: 'dispatch_checkin' or 'emergency'
        
    Returns:
        Updated extracted_data with missing categorical fields filled
    """
    updated = {**extracted_data}
    is_emergency = scenario_type == "emergency"
    
    # Only fill missing fields with high-confidence patterns
    if scenario_type == "emergency":
        # Emergency scenario fields
        if not updated.get("emergency_type"):
            emergency_type = extract_emergency_type(transcript)
            if emergency_type:
                updated["emergency_type"] = emergency_type
                logger.info(f"Fallback extracted emergency_type: {emergency_type}")
        
        if not updated.get("call_outcome"):
            call_outcome = extract_call_outcome(transcript, is_emergency=True)
            if call_outcome:
                updated["call_outcome"] = call_outcome
                logger.info(f"Fallback extracted call_outcome: {call_outcome}")
        
        if updated.get("load_secure") is None:
            load_secure = extract_load_secure(transcript)
            if load_secure is not None:
                updated["load_secure"] = load_secure
                logger.info(f"Fallback extracted load_secure: {load_secure}")
    
    else:  # dispatch_checkin
        # Dispatch check-in scenario fields
        if not updated.get("driver_status"):
            driver_status = extract_driver_status(transcript)
            if driver_status:
                updated["driver_status"] = driver_status
                logger.info(f"Fallback extracted driver_status: {driver_status}")
        
        if not updated.get("call_outcome"):
            call_outcome = extract_call_outcome(transcript, is_emergency=False)
            if call_outcome:
                updated["call_outcome"] = call_outcome
                logger.info(f"Fallback extracted call_outcome: {call_outcome}")
        
        if updated.get("pod_reminder_acknowledged") is None:
            pod_ack = extract_pod_reminder_acknowledged(transcript)
            if pod_ack is not None:
                updated["pod_reminder_acknowledged"] = pod_ack
                logger.info(f"Fallback extracted pod_reminder_acknowledged: {pod_ack}")
    
    return updated

"""Application constants and configuration values.

Centralizes magic strings and configuration values for consistency.
"""

from typing import FrozenSet


# =============================================================================
# Emergency Detection
# =============================================================================

EMERGENCY_KEYWORDS: FrozenSet[str] = frozenset({
    "blowout",
    "accident", 
    "medical",
    "help",
    "emergency",
    "fire",
    "crash",
    "injured",
    "ambulance",
    "police",
    "911",
    "hurt",
    "bleeding",
})

# Minimum confidence threshold for emergency detection
EMERGENCY_CONFIDENCE_THRESHOLD = 0.7


# =============================================================================
# Conversation State Machine
# =============================================================================

class ConversationState:
    """Valid conversation states for the dispatch agent."""
    INITIAL = "initial"
    GATHERING_STATUS = "gathering_status"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    COMPLETED = "completed"
    EMERGENCY_DETECTED = "emergency_detected"
    ESCALATION = "escalation"
    FAILED = "failed"


# Valid state transitions
STATE_TRANSITIONS = {
    ConversationState.INITIAL: [
        ConversationState.GATHERING_STATUS,
        ConversationState.EMERGENCY_DETECTED,  # Can detect emergency at any time
    ],
    ConversationState.GATHERING_STATUS: [
        ConversationState.IN_TRANSIT,
        ConversationState.ARRIVED,
        ConversationState.EMERGENCY_DETECTED,
        ConversationState.FAILED,
    ],
    ConversationState.IN_TRANSIT: [
        ConversationState.COMPLETED,
        ConversationState.EMERGENCY_DETECTED,
    ],
    ConversationState.ARRIVED: [
        ConversationState.COMPLETED,
        ConversationState.EMERGENCY_DETECTED,
    ],
    ConversationState.EMERGENCY_DETECTED: [
        ConversationState.ESCALATION,
    ],
    ConversationState.ESCALATION: [
        ConversationState.COMPLETED,
    ],
    ConversationState.COMPLETED: [],  # Terminal state
    ConversationState.FAILED: [],  # Terminal state
}


# =============================================================================
# Edge Case Handling (Task B)
# =============================================================================

# Maximum retry attempts for uncooperative driver
MAX_UNCOOPERATIVE_RETRIES = 3

# Maximum times to ask driver to repeat (noisy environment)
MAX_REPEAT_REQUESTS = 2

# Phrases indicating need to repeat
UNCLEAR_RESPONSE_INDICATORS = [
    "[inaudible]",
    "[unclear]",
    "...",
    "[noise]",
]


# =============================================================================
# Retell AI Configuration
# =============================================================================

# Webhook event types from Retell AI
class RetellEventType:
    """Retell AI webhook event types."""
    CALL_STARTED = "call_started"
    CALL_ENDED = "call_ended"
    CALL_ANALYZED = "call_analyzed"


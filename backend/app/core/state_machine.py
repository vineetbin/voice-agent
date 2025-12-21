"""Conversation State Machine for managing call flow.

Handles state transitions during a call, including:
- Normal dispatch check-in flow
- Emergency detection and escalation
- Edge case handling (uncooperative driver, noisy environment)
"""

from typing import Optional, List, Tuple
from dataclasses import dataclass, field

from app.core.constants import (
    ConversationState,
    STATE_TRANSITIONS,
    EMERGENCY_KEYWORDS,
    MAX_UNCOOPERATIVE_RETRIES,
    MAX_REPEAT_REQUESTS,
    UNCLEAR_RESPONSE_INDICATORS,
)


@dataclass
class ConversationContext:
    """Tracks the current state and context of a conversation."""
    
    state: str = ConversationState.INITIAL
    
    # Collected information
    driver_status: Optional[str] = None
    current_location: Optional[str] = None
    eta: Optional[str] = None
    delay_reason: Optional[str] = None
    unloading_status: Optional[str] = None
    pod_acknowledged: bool = False
    
    # Emergency context
    is_emergency: bool = False
    emergency_type: Optional[str] = None
    safety_status: Optional[str] = None
    injury_status: Optional[str] = None
    emergency_location: Optional[str] = None
    load_secure: Optional[bool] = None
    
    # Edge case tracking
    uncooperative_count: int = 0
    repeat_request_count: int = 0
    
    # Conversation history
    utterances: List[dict] = field(default_factory=list)


class StateMachine:
    """
    Manages conversation state transitions and emergency detection.
    
    State Flow:
        initial → gathering_status → in_transit | arrived → completed
        any_state → emergency_detected → escalation
    """
    
    def __init__(self, context: Optional[ConversationContext] = None):
        """Initialize state machine with optional existing context."""
        self.context = context or ConversationContext()
    
    def can_transition(self, new_state: str) -> bool:
        """Check if transition to new_state is valid from current state."""
        current = self.context.state
        valid_transitions = STATE_TRANSITIONS.get(current, [])
        return new_state in valid_transitions
    
    def transition(self, new_state: str) -> bool:
        """
        Attempt to transition to a new state.
        
        Returns True if transition was successful, False otherwise.
        """
        if not self.can_transition(new_state):
            return False
        
        self.context.state = new_state
        return True
    
    def detect_emergency(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if the given text contains emergency indicators.
        
        Returns:
            Tuple of (is_emergency, emergency_type)
        """
        text_lower = text.lower()
        
        for keyword in EMERGENCY_KEYWORDS:
            if keyword in text_lower:
                # Determine emergency type
                emergency_type = self._classify_emergency(text_lower)
                return True, emergency_type
        
        return False, None
    
    def _classify_emergency(self, text: str) -> str:
        """Classify the type of emergency based on text content."""
        if any(word in text for word in ["accident", "crash", "collision", "hit"]):
            return "Accident"
        elif any(word in text for word in ["blowout", "tire", "breakdown", "engine", "broke"]):
            return "Breakdown"
        elif any(word in text for word in ["medical", "ambulance", "hurt", "injured", "bleeding", "sick"]):
            return "Medical"
        else:
            return "Other"
    
    def handle_emergency(self, text: str) -> bool:
        """
        Process potential emergency in the conversation.
        
        Returns True if emergency was detected and state was updated.
        """
        is_emergency, emergency_type = self.detect_emergency(text)
        
        if is_emergency:
            self.context.is_emergency = True
            self.context.emergency_type = emergency_type
            # Force transition to emergency state (overrides normal flow)
            self.context.state = ConversationState.EMERGENCY_DETECTED
            return True
        
        return False
    
    def is_unclear_response(self, text: str) -> bool:
        """Check if the response indicates audio/speech issues."""
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in UNCLEAR_RESPONSE_INDICATORS)
    
    def handle_unclear_response(self) -> Tuple[bool, str]:
        """
        Handle unclear/noisy audio response.
        
        Returns:
            Tuple of (should_escalate, suggested_response)
        """
        self.context.repeat_request_count += 1
        
        if self.context.repeat_request_count > MAX_REPEAT_REQUESTS:
            return True, "I'm having trouble hearing you. Let me connect you with a human dispatcher."
        
        return False, "I'm sorry, I didn't catch that. Could you please repeat?"
    
    def is_uncooperative_response(self, text: str) -> bool:
        """Check if response is minimal/uncooperative (one-word answers, etc.)."""
        # Very short responses that don't provide useful information
        words = text.strip().split()
        short_unhelpful = ["yes", "no", "yeah", "nah", "ok", "okay", "fine", "whatever", "sure"]
        
        return len(words) <= 2 and any(word.lower() in short_unhelpful for word in words)
    
    def handle_uncooperative_response(self) -> Tuple[bool, str]:
        """
        Handle uncooperative driver responses.
        
        Returns:
            Tuple of (should_end_call, suggested_response)
        """
        self.context.uncooperative_count += 1
        
        if self.context.uncooperative_count >= MAX_UNCOOPERATIVE_RETRIES:
            return True, "I understand you're busy. I'll try calling back later. Have a safe drive."
        
        probing_questions = [
            "Can you give me a bit more detail about your current status?",
            "I need a bit more information for our records. Where are you right now?",
            "Just to confirm - are you still en route or have you arrived at the destination?",
        ]
        
        idx = min(self.context.uncooperative_count - 1, len(probing_questions) - 1)
        return False, probing_questions[idx]
    
    def add_utterance(self, role: str, content: str) -> None:
        """Add an utterance to the conversation history."""
        self.context.utterances.append({
            "role": role,
            "content": content,
        })
    
    def get_state(self) -> str:
        """Get current conversation state."""
        return self.context.state
    
    def is_terminal(self) -> bool:
        """Check if conversation is in a terminal state."""
        return self.context.state in [
            ConversationState.COMPLETED,
            ConversationState.FAILED,
        ]
    
    def to_dict(self) -> dict:
        """Serialize context to dictionary for storage."""
        return {
            "state": self.context.state,
            "driver_status": self.context.driver_status,
            "current_location": self.context.current_location,
            "eta": self.context.eta,
            "delay_reason": self.context.delay_reason,
            "unloading_status": self.context.unloading_status,
            "pod_acknowledged": self.context.pod_acknowledged,
            "is_emergency": self.context.is_emergency,
            "emergency_type": self.context.emergency_type,
            "safety_status": self.context.safety_status,
            "injury_status": self.context.injury_status,
            "emergency_location": self.context.emergency_location,
            "load_secure": self.context.load_secure,
            "uncooperative_count": self.context.uncooperative_count,
            "repeat_request_count": self.context.repeat_request_count,
            "utterances": self.context.utterances,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "StateMachine":
        """Deserialize state machine from dictionary."""
        context = ConversationContext(
            state=data.get("state", ConversationState.INITIAL),
            driver_status=data.get("driver_status"),
            current_location=data.get("current_location"),
            eta=data.get("eta"),
            delay_reason=data.get("delay_reason"),
            unloading_status=data.get("unloading_status"),
            pod_acknowledged=data.get("pod_acknowledged", False),
            is_emergency=data.get("is_emergency", False),
            emergency_type=data.get("emergency_type"),
            safety_status=data.get("safety_status"),
            injury_status=data.get("injury_status"),
            emergency_location=data.get("emergency_location"),
            load_secure=data.get("load_secure"),
            uncooperative_count=data.get("uncooperative_count", 0),
            repeat_request_count=data.get("repeat_request_count", 0),
            utterances=data.get("utterances", []),
        )
        return cls(context)


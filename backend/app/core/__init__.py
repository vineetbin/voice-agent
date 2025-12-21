"""Core configuration and utilities."""

from app.core.config import get_settings, Settings
from app.core.database import get_db, get_supabase_client
from app.core.constants import (
    EMERGENCY_KEYWORDS,
    ConversationState,
    STATE_TRANSITIONS,
    RetellEventType,
    MAX_UNCOOPERATIVE_RETRIES,
    MAX_REPEAT_REQUESTS,
)
from app.core.state_machine import StateMachine, ConversationContext

__all__ = [
    "get_settings",
    "Settings",
    "get_db",
    "get_supabase_client",
    "EMERGENCY_KEYWORDS",
    "ConversationState",
    "STATE_TRANSITIONS",
    "RetellEventType",
    "MAX_UNCOOPERATIVE_RETRIES",
    "MAX_REPEAT_REQUESTS",
    "StateMachine",
    "ConversationContext",
]

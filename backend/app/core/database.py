"""Supabase database client configuration."""

from functools import lru_cache
from supabase import create_client, Client

from app.core.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    """
    Get cached Supabase client instance.
    
    Uses service role key for full database access.
    The client is cached to avoid creating multiple connections.
    """
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )


def get_db() -> Client:
    """
    Dependency injection function for FastAPI.
    
    Usage:
        @app.get("/items")
        async def get_items(db: Client = Depends(get_db)):
            ...
    """
    return get_supabase_client()


"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


# Get the project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # App
    app_name: str = "AI Voice Agent"
    debug: bool = False
    
    # Retell AI
    retell_api_key: str
    retell_agent_id: str
    retell_webhook_secret: str
    
    # OpenAI
    openai_api_key: str
    
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    
    # App Configuration
    call_mode: str = "simulated"  # simulated | real
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


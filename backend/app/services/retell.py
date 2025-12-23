"""
Retell AI service for agent management and call creation.

This service handles all interactions with the Retell AI API:
- Updating agent configuration (prompt, voice settings)
- Creating phone calls
- Creating web calls (for non-USA testing)
"""

import logging
from typing import Optional, Dict, Any, Union
from retell import Retell
from retell.types import WebCallResponse, PhoneCallResponse

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RetellService:
    """
    Service class for Retell AI operations.
    
    Uses the pre-configured agent from RETELL_AGENT_ID environment variable.
    Updates agent settings and creates calls as needed.
    """
    
    def __init__(self):
        """Initialize Retell client with API key."""
        settings = get_settings()
        self.client = Retell(api_key=settings.retell_api_key)
        self.agent_id = settings.retell_agent_id
        self.from_number = settings.retell_from_number  # Default caller ID
        self.webhook_url = f"{settings.backend_url}/webhooks/retell"
    
    def update_agent(
        self,
        system_prompt: Optional[str] = None,
        initial_message: Optional[str] = None,
        enable_backchanneling: Optional[bool] = None,
        interruption_sensitivity: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Partially update the Retell agent with new configuration.
        
        IMPORTANT: This only updates the fields that are explicitly provided.
        All other Retell settings remain unchanged.
        
        In Retell's architecture:
        - Agent: voice settings (backchanneling, interruption sensitivity)
        - LLM: prompt settings (general_prompt, begin_message)
        
        Args:
            system_prompt: The main prompt (only updated if provided)
            initial_message: First message agent says (only updated if provided)
            enable_backchanneling: Use acknowledgment sounds (only updated if provided)
            interruption_sensitivity: How sensitive to interruptions (only updated if provided)
            
        Returns:
            Updated agent/LLM data
        """
        try:
            # Step 1: Get the agent to find its LLM ID
            agent = self.client.agent.retrieve(agent_id=self.agent_id)
            
            # Extract LLM ID from response_engine
            llm_id = None
            if hasattr(agent, 'response_engine') and agent.response_engine:
                response_engine = agent.response_engine
                if hasattr(response_engine, 'llm_id'):
                    llm_id = response_engine.llm_id
            
            # Step 2: Update the LLM with prompt settings (only fields that are provided)
            if llm_id:
                llm_update_params = {}
                if system_prompt is not None:
                    llm_update_params["general_prompt"] = system_prompt
                if initial_message is not None:
                    llm_update_params["begin_message"] = initial_message
                
                if llm_update_params:
                    self.client.llm.update(
                        llm_id=llm_id,
                        **llm_update_params
                    )
                    logger.info(f"Updated Retell LLM {llm_id} with: {list(llm_update_params.keys())}")
            else:
                logger.warning(f"No LLM ID found for agent {self.agent_id}, skipping prompt update")
            
            # Step 3: Update the agent with voice settings (only fields that are provided)
            agent_update_params = {}
            if enable_backchanneling is not None:
                agent_update_params["enable_backchannel"] = enable_backchanneling
            if interruption_sensitivity is not None:
                agent_update_params["interruption_sensitivity"] = interruption_sensitivity
            
            if agent_update_params:
                self.client.agent.update(
                    agent_id=self.agent_id,
                    **agent_update_params
                )
                logger.info(f"Updated Retell agent {self.agent_id} with: {list(agent_update_params.keys())}")
            
            return {"agent_id": self.agent_id, "llm_id": llm_id, "updated": True}
            
        except Exception as e:
            logger.error(f"Failed to update Retell agent: {e}")
            raise RetellServiceError(f"Failed to update agent: {str(e)}")
    
    def create_phone_call(
        self,
        to_number: str,
        from_number: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        dynamic_variables: Optional[Dict[str, str]] = None,
    ) -> PhoneCallResponse:
        """
        Create an outbound phone call.
        
        Args:
            to_number: Phone number to call (E.164 format)
            from_number: Caller ID (optional, uses RETELL_FROM_NUMBER from config if not provided)
            metadata: Custom metadata (e.g., internal_call_id)
            dynamic_variables: Variables to inject (driver_name, load_number)
            
        Returns:
            Call registration response from Retell
            
        Raises:
            RetellServiceError: If from_number is not configured and not provided
        """
        try:
            # Retell SDK requires from_number as a required parameter
            # Use provided from_number, or fall back to configured default
            if from_number is None:
                from_number = self.from_number
            
            if not from_number:
                raise RetellServiceError(
                    "from_number is required for phone calls. "
                    "Please configure RETELL_FROM_NUMBER in your .env file, "
                    "or provide a from_number parameter. "
                    "The from_number must be a phone number registered in your Retell account."
                )
            
            call = self.client.call.create_phone_call(
                from_number=from_number,
                to_number=to_number,
                override_agent_id=self.agent_id,  # Note: phone calls use override_agent_id
                metadata=metadata or {},
                retell_llm_dynamic_variables=dynamic_variables or {},
            )
            
            logger.info(f"Created phone call {call.call_id} from {from_number} to {to_number}")
            return call
            
        except RetellServiceError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error(f"Failed to create phone call: {e}")
            raise RetellServiceError(f"Failed to create phone call: {str(e)}")
    
    def create_web_call(
        self,
        metadata: Optional[Dict[str, Any]] = None,
        dynamic_variables: Optional[Dict[str, str]] = None,
    ) -> WebCallResponse:
        """
        Create a web call for browser-based testing.
        
        This is useful for non-USA testing where phone calls aren't available.
        Returns access token for Retell Web SDK.
        
        Args:
            metadata: Custom metadata (e.g., internal_call_id)
            dynamic_variables: Variables to inject (driver_name, load_number)
            
        Returns:
            Call registration with access_token for web SDK
        """
        try:
            call = self.client.call.create_web_call(
                agent_id=self.agent_id,  # Note: web calls use agent_id directly
                metadata=metadata or {},
                retell_llm_dynamic_variables=dynamic_variables or {},
            )
            
            logger.info(f"Created web call {call.call_id}")
            return call
            
        except Exception as e:
            logger.error(f"Failed to create web call: {e}")
            raise RetellServiceError(f"Failed to create web call: {str(e)}")
    
    def get_call(self, call_id: str) -> Dict[str, Any]:
        """
        Get details of a specific call.
        
        Args:
            call_id: Retell call ID
            
        Returns:
            Call details from Retell API
        """
        try:
            call = self.client.call.retrieve(call_id)
            return call
        except Exception as e:
            logger.error(f"Failed to get call {call_id}: {e}")
            raise RetellServiceError(f"Failed to get call: {str(e)}")
    
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get current configuration from Retell agent and its LLM.
        
        Returns:
            Dictionary with agent and LLM settings merged
        """
        try:
            # Get agent settings
            agent = self.client.agent.retrieve(agent_id=self.agent_id)
            
            config = {
                "agent_id": self.agent_id,
                "agent_name": getattr(agent, 'agent_name', None),
                "enable_backchannel": getattr(agent, 'enable_backchannel', True),
                "interruption_sensitivity": getattr(agent, 'interruption_sensitivity', 0.5),
                "boosted_keywords": getattr(agent, 'boosted_keywords', []),
            }
            
            # Get LLM settings if available
            llm_id = None
            if hasattr(agent, 'response_engine') and agent.response_engine:
                response_engine = agent.response_engine
                if hasattr(response_engine, 'llm_id'):
                    llm_id = response_engine.llm_id
            
            if llm_id:
                llm = self.client.llm.retrieve(llm_id=llm_id)
                config["llm_id"] = llm_id
                config["general_prompt"] = getattr(llm, 'general_prompt', None)
                config["begin_message"] = getattr(llm, 'begin_message', None)
            
            logger.info(f"Retrieved Retell config for agent {self.agent_id}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to get Retell agent config: {e}")
            raise RetellServiceError(f"Failed to get agent config: {str(e)}")


class RetellServiceError(Exception):
    """Custom exception for Retell service errors."""
    pass


# Singleton instance for dependency injection
_retell_service: Optional[RetellService] = None


def get_retell_service() -> RetellService:
    """
    Get or create Retell service instance.
    
    Used as FastAPI dependency.
    """
    global _retell_service
    if _retell_service is None:
        _retell_service = RetellService()
    return _retell_service


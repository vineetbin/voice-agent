"""Agent Configuration API endpoints.

Provides CRUD operations for managing voice agent configurations.
Each configuration defines prompts and Retell AI settings for a scenario.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.core.database import get_db
from app.models.schemas import (
    AgentConfig,
    AgentConfigCreate,
    AgentConfigUpdate,
    ScenarioType,
)
from app.services.retell import get_retell_service, RetellService, RetellServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/configs", tags=["Agent Configurations"])

# Table name constant for consistency
TABLE_NAME = "agent_configs"


@router.get("", response_model=List[AgentConfig])
async def list_configs(
    scenario_type: Optional[ScenarioType] = Query(None, description="Filter by scenario type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Client = Depends(get_db),
) -> List[AgentConfig]:
    """
    List all agent configurations.
    
    Optionally filter by scenario_type or active status.
    Results are ordered by creation date (newest first).
    """
    query = db.table(TABLE_NAME).select("*")
    
    if scenario_type:
        query = query.eq("scenario_type", scenario_type.value)
    if is_active is not None:
        query = query.eq("is_active", is_active)
    
    query = query.order("created_at", desc=True)
    
    response = query.execute()
    return response.data


@router.get("/{config_id}", response_model=AgentConfig)
async def get_config(
    config_id: UUID,
    db: Client = Depends(get_db),
) -> AgentConfig:
    """
    Get a specific agent configuration by ID.
    
    Raises 404 if the configuration is not found.
    """
    response = db.table(TABLE_NAME).select("*").eq("id", str(config_id)).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent configuration with id {config_id} not found"
        )
    
    return response.data[0]


@router.post("", response_model=AgentConfig, status_code=status.HTTP_201_CREATED)
async def create_config(
    config: AgentConfigCreate,
    db: Client = Depends(get_db),
) -> AgentConfig:
    """
    Create a new agent configuration.
    
    If is_active is True, this will deactivate other configs of the same scenario_type.
    """
    # If this config should be active, deactivate others of same scenario type
    if config.is_active:
        db.table(TABLE_NAME).update({"is_active": False}).eq(
            "scenario_type", config.scenario_type.value
        ).execute()
    
    response = db.table(TABLE_NAME).insert(config.model_dump(mode="json")).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent configuration"
        )
    
    return response.data[0]


@router.put("/{config_id}", response_model=AgentConfig)
async def update_config(
    config_id: UUID,
    config: AgentConfigUpdate,
    db: Client = Depends(get_db),
    retell: RetellService = Depends(get_retell_service),
) -> AgentConfig:
    """
    Update an existing agent configuration.
    
    Only provided fields will be updated.
    If is_active is set to True, other configs of same scenario_type are deactivated.
    If the config is active, changes are also pushed to Retell.
    """
    # Check if config exists
    existing = db.table(TABLE_NAME).select("*").eq("id", str(config_id)).execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent configuration with id {config_id} not found"
        )
    
    existing_config = existing.data[0]
    
    # Build update data (only non-None values)
    update_data = config.model_dump(exclude_none=True, mode="json")
    
    if not update_data:
        # Nothing to update, return existing
        return existing_config
    
    # If activating, deactivate others of same scenario type
    if config.is_active:
        scenario = config.scenario_type or existing_config.get("scenario_type")
        db.table(TABLE_NAME).update({"is_active": False}).eq(
            "scenario_type", scenario
        ).neq("id", str(config_id)).execute()
    
    response = db.table(TABLE_NAME).update(update_data).eq("id", str(config_id)).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent configuration"
        )
    
    updated_config = response.data[0]
    
    # If this config is active, push changes to Retell
    if updated_config.get("is_active"):
        try:
            retell.update_agent(
                system_prompt=updated_config.get("system_prompt"),
                initial_message=updated_config.get("initial_message"),
                enable_backchanneling=updated_config.get("enable_backchanneling"),
                interruption_sensitivity=updated_config.get("interruption_sensitivity"),
            )
            logger.info(f"Pushed active config {config_id} to Retell")
        except RetellServiceError as e:
            logger.warning(f"Failed to push to Retell (config saved anyway): {e}")
    
    return updated_config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: UUID,
    db: Client = Depends(get_db),
) -> None:
    """
    Delete an agent configuration.
    
    Raises 404 if the configuration is not found.
    """
    # Check if exists
    existing = db.table(TABLE_NAME).select("id").eq("id", str(config_id)).execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent configuration with id {config_id} not found"
        )
    
    db.table(TABLE_NAME).delete().eq("id", str(config_id)).execute()


@router.get("/active/{scenario_type}", response_model=Optional[AgentConfig])
async def get_active_config(
    scenario_type: ScenarioType,
    db: Client = Depends(get_db),
) -> Optional[AgentConfig]:
    """
    Get the currently active configuration for a scenario type.
    
    Returns None if no active configuration exists.
    This endpoint is used when triggering calls to get the current prompts.
    """
    response = db.table(TABLE_NAME).select("*").eq(
        "scenario_type", scenario_type.value
    ).eq("is_active", True).limit(1).execute()
    
    if not response.data:
        return None
    
    return response.data[0]


@router.patch("/{config_id}", response_model=AgentConfig)
async def patch_config(
    config_id: UUID,
    config: AgentConfigUpdate,
    db: Client = Depends(get_db),
    retell: RetellService = Depends(get_retell_service),
) -> AgentConfig:
    """
    Partially update an existing agent configuration.
    
    Only provided fields will be updated.
    If is_active is set to True, other configs of same scenario_type are deactivated
    and changes are pushed to Retell.
    """
    # Check if config exists
    existing = db.table(TABLE_NAME).select("*").eq("id", str(config_id)).execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent configuration with id {config_id} not found"
        )
    
    existing_config = existing.data[0]
    
    # Build update data (only non-None values)
    update_data = config.model_dump(exclude_none=True, mode="json")
    
    if not update_data:
        # Nothing to update, return existing
        return existing_config
    
    # If activating, deactivate others of same scenario type
    is_being_activated = config.is_active and not existing_config.get("is_active")
    if config.is_active:
        scenario = config.scenario_type or existing_config.get("scenario_type")
        db.table(TABLE_NAME).update({"is_active": False}).eq(
            "scenario_type", scenario
        ).neq("id", str(config_id)).execute()
    
    response = db.table(TABLE_NAME).update(update_data).eq("id", str(config_id)).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent configuration"
        )
    
    updated_config = response.data[0]
    
    # If this config is active (or being activated), push changes to Retell
    if updated_config.get("is_active"):
        try:
            retell.update_agent(
                system_prompt=updated_config.get("system_prompt"),
                initial_message=updated_config.get("initial_message"),
                enable_backchanneling=updated_config.get("enable_backchanneling"),
                interruption_sensitivity=updated_config.get("interruption_sensitivity"),
            )
            logger.info(f"Pushed active config {config_id} to Retell")
        except RetellServiceError as e:
            logger.warning(f"Failed to push to Retell (config saved anyway): {e}")
    
    return updated_config


# =============================================================================
# Retell AI Sync Endpoints
# =============================================================================

@router.get("/retell/current")
async def get_retell_config(
    retell: RetellService = Depends(get_retell_service),
) -> Dict[str, Any]:
    """
    Get the current configuration directly from Retell AI.
    
    Returns the actual settings configured on the Retell agent and LLM.
    Use this to sync your local configs with what's on Retell.
    """
    try:
        config = retell.get_agent_config()
        return config
    except RetellServiceError as e:
        logger.error(f"Failed to fetch Retell config: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


@router.post("/retell/sync", response_model=AgentConfig)
async def sync_from_retell(
    scenario_type: ScenarioType = Query(..., description="Scenario to create/update config for"),
    db: Client = Depends(get_db),
    retell: RetellService = Depends(get_retell_service),
) -> AgentConfig:
    """
    Sync configuration FROM Retell AI to local database.
    
    Fetches current Retell agent settings and creates/updates a local config.
    This is useful when you've configured the agent directly in Retell's dashboard.
    """
    try:
        # Get current Retell config
        retell_config = retell.get_agent_config()
        
        # Check if we have an existing config for this scenario
        existing = db.table(TABLE_NAME).select("*").eq(
            "scenario_type", scenario_type.value
        ).limit(1).execute()
        
        config_data = {
            "name": retell_config.get("agent_name") or f"Synced from Retell ({scenario_type.value})",
            "description": "Configuration synced from Retell AI dashboard",
            "scenario_type": scenario_type.value,
            "system_prompt": retell_config.get("general_prompt") or "",
            "initial_message": retell_config.get("begin_message"),
            "enable_backchanneling": retell_config.get("enable_backchannel", True),
            "enable_filler_words": True,  # Not directly available from Retell
            "interruption_sensitivity": retell_config.get("interruption_sensitivity", 0.5),
            "is_active": True,
        }
        
        if existing.data:
            # Update existing config
            config_id = existing.data[0]["id"]
            
            # Deactivate others first
            db.table(TABLE_NAME).update({"is_active": False}).eq(
                "scenario_type", scenario_type.value
            ).neq("id", config_id).execute()
            
            response = db.table(TABLE_NAME).update(config_data).eq("id", config_id).execute()
        else:
            # Deactivate others first
            db.table(TABLE_NAME).update({"is_active": False}).eq(
                "scenario_type", scenario_type.value
            ).execute()
            
            # Create new config
            response = db.table(TABLE_NAME).insert(config_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save synced configuration"
            )
        
        logger.info(f"Synced Retell config to local database for {scenario_type.value}")
        return response.data[0]
        
    except RetellServiceError as e:
        logger.error(f"Failed to sync from Retell: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


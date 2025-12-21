"""Agent Configuration API endpoints.

Provides CRUD operations for managing voice agent configurations.
Each configuration defines prompts and Retell AI settings for a scenario.
"""

from typing import List, Optional
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
) -> AgentConfig:
    """
    Update an existing agent configuration.
    
    Only provided fields will be updated.
    If is_active is set to True, other configs of same scenario_type are deactivated.
    """
    # Check if config exists
    existing = db.table(TABLE_NAME).select("*").eq("id", str(config_id)).execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent configuration with id {config_id} not found"
        )
    
    # Build update data (only non-None values)
    update_data = config.model_dump(exclude_none=True, mode="json")
    
    if not update_data:
        # Nothing to update, return existing
        return existing.data[0]
    
    # If activating, deactivate others of same scenario type
    if config.is_active:
        scenario = config.scenario_type or existing.data[0].get("scenario_type")
        db.table(TABLE_NAME).update({"is_active": False}).eq(
            "scenario_type", scenario
        ).neq("id", str(config_id)).execute()
    
    response = db.table(TABLE_NAME).update(update_data).eq("id", str(config_id)).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent configuration"
        )
    
    return response.data[0]


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


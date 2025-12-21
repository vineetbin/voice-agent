"""Main API router that mounts all sub-routers.

All API endpoints are mounted under /api prefix.
This provides a clean separation between API routes and webhook routes.
"""

from fastapi import APIRouter

from app.api.configs import router as configs_router
from app.api.calls import router as calls_router

# Main API router - all routes mounted under /api
api_router = APIRouter(prefix="/api")

# Mount sub-routers
api_router.include_router(configs_router)
api_router.include_router(calls_router)


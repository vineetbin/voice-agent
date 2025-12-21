"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.router import api_router
from app.webhooks import retell_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="AI Voice Agent for logistics dispatch calls",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Include webhook routes
app.include_router(retell_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Voice Agent API", "docs": "/docs"}


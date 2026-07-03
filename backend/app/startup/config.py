"""
Application configuration and factory for Bijmantra API.

This module creates and configures the FastAPI application instance.
Extracted from main.py as part of Task 16.
"""

import logging

from fastapi import FastAPI

from app.core.config import settings
from app.startup.database import lifespan

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="Bijmantra API",
        description="BrAPI v2.1 compatible Plant Breeding Application with Real-time Collaboration",
        version=settings.APP_VERSION,
        docs_url=None,  # Disabled for custom override with nonce
        redoc_url=None,  # Disabled for custom override with nonce
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    logger.info("FastAPI application created")
    
    return app


def mount_socketio(app: FastAPI):
    """Mount Socket.IO for real-time communication."""
    try:
        from app.core.socketio import socket_app
        app.mount("/ws", socket_app)
        logger.info("Socket.IO mounted at /ws")
    except Exception as e:
        logger.warning("Socket.IO not available: %s", e)

"""
Database and service initialization for Bijmantra API.

This module handles startup/shutdown of all external services and connections.
Extracted from main.py as part of Task 16.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)


async def initialize_redis():
    """Initialize Redis for ephemeral data (jobs, search cache)."""
    try:
        from app.core.redis import redis_client
        connected = await redis_client.connect()
        if connected:
            logger.info("Redis connected for job/cache storage")
        else:
            logger.warning("Redis using in-memory fallback (not recommended for production)")
    except Exception as e:
        logger.warning("Redis initialization skipped: %s", e)


async def initialize_meilisearch():
    """Initialize Meilisearch for full-text search."""
    try:
        from app.core.meilisearch import meilisearch_service
        if meilisearch_service.connect():
            meilisearch_service.setup_indexes()
            logger.info("Meilisearch initialized")
    except Exception as e:
        logger.warning("Meilisearch initialization skipped: %s", e)


async def initialize_task_queue():
    """Start background task queue."""
    try:
        from app.services.task_queue import task_queue
        await task_queue.start()
        logger.info("Task queue started")
    except Exception as e:
        logger.warning("TaskQueue initialization skipped: %s", e)


async def initialize_redis_security():
    """Initialize Redis security storage."""
    try:
        from app.modules.core.services.redis_security_service import init_redis_security
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            await init_redis_security(redis_url)
            logger.info("Redis security storage initialized")
        else:
            logger.warning("No REDIS_URL configured, using in-memory storage for security")
    except Exception as e:
        logger.warning("Redis security storage initialization skipped: %s", e)


async def shutdown_redis():
    """Disconnect Redis on shutdown."""
    try:
        from app.core.redis import redis_client
        await redis_client.disconnect()
        logger.info("Redis disconnected")
    except Exception:
        pass


async def shutdown_task_queue():
    """Stop task queue on shutdown."""
    try:
        from app.services.task_queue import task_queue
        await task_queue.stop()
        logger.info("Task queue stopped")
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    
    This replaces the old @app.on_event("startup") and @app.on_event("shutdown")
    decorators with the modern lifespan pattern.
    """
    # Startup
    logger.info("Starting up Bijmantra API...")
    
    await initialize_redis()
    await initialize_meilisearch()
    await initialize_task_queue()
    await initialize_redis_security()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Bijmantra API...")
    
    await shutdown_redis()
    await shutdown_task_queue()

"""Monitoring domain router aggregator."""
from fastapi import APIRouter

from app.api.bijmantra.monitoring import (
    monitoring,
    metrics,
    performance,
    progress,
    workers,
)

monitoring_router = APIRouter()

monitoring_router.include_router(monitoring.router, tags=["Monitoring"])
monitoring_router.include_router(metrics.router, tags=["Metrics"])
monitoring_router.include_router(performance.router, tags=["Performance Optimization"])
monitoring_router.include_router(progress.router, tags=["Progress Tracker"])
monitoring_router.include_router(workers.router, tags=["Workers"])

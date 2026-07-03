"""Developer domain router aggregator."""

from fastapi import APIRouter

from app.api.bijmantra.developer import (
    chaitanya,
    developer_control_plane,
    developer_control_plane_indigenous_brain,
    developer_control_plane_mem0,
    developer_control_plane_project_brain,
    dispatch,
)

developer_router = APIRouter()

# Developer control plane endpoints
developer_router.include_router(
    developer_control_plane.router,
    tags=["Developer Control Plane"]
)
developer_router.include_router(
    developer_control_plane_indigenous_brain.router,
    tags=["Developer Control Plane"]
)
developer_router.include_router(
    developer_control_plane_mem0.router,
    tags=["Developer Control Plane"]
)
developer_router.include_router(
    developer_control_plane_project_brain.router,
    tags=["Developer Control Plane"]
)

# CHAITANYA orchestrator endpoints
developer_router.include_router(
    chaitanya.router,
    tags=["CHAITANYA Orchestrator"]
)

# Dispatch management endpoints
developer_router.include_router(
    dispatch.router,
    tags=["Dispatch Management"]
)

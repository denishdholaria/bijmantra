"""Control Plane domain router aggregator."""

from fastapi import APIRouter

from app.api.bijmantra.control_plane import (
    lanes,
    missions,
    telemetry,
    verification,
)

control_plane_router = APIRouter()

# Include all control plane domain routers
control_plane_router.include_router(lanes.router, tags=["Control Plane - Lanes"])
control_plane_router.include_router(missions.router, tags=["Control Plane - Missions"])
control_plane_router.include_router(telemetry.router, tags=["Control Plane - Telemetry"])
control_plane_router.include_router(verification.router, tags=["Control Plane - Verification"])

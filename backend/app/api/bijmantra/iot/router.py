"""IoT domain router aggregator."""

from fastapi import APIRouter

from app.api.bijmantra.iot import (
    devices,
    telemetry,
)

iot_router = APIRouter()

# Include all IoT domain routers
iot_router.include_router(devices.router, tags=["IoT"])
iot_router.include_router(telemetry.router, tags=["IoT"])

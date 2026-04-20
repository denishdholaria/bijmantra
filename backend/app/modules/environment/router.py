"""
Environment Domain API Router

Consolidates all environment-related endpoints under /api/v2/environment/*
Migrated from flat api/v2/ structure to domain-based organization.

Endpoints organized by subdomain:
- Weather Intelligence (forecasts, impacts, activity windows, GDD)
- Climate Analysis (long-term trends, drought monitoring)
- Field Environment (soil profiles, input logs, irrigation, field history)
- Environmental Physics (GDD calculations, PTU, soil moisture indices)
- Weather Service (weather stations, forecasts, historical records, climate zones, alerts)
"""

from fastapi import APIRouter

# Import all environment-related routers
from app.api.v2 import (
    climate,
    field_environment,
    weather,
)
from app.api.v2.environmental import router as environmental_router
from app.modules.weather.router import router as weather_module_router

# Create main environment router with /api/v2 prefix
# Individual routers will be included with their own prefixes
router = APIRouter(prefix="/api/v2", tags=["Environment"])

# Include all environment sub-routers
# These maintain their original prefixes for backward compatibility
router.include_router(weather.router, tags=["Weather Intelligence"])
router.include_router(climate.router, tags=["Climate Analysis"])
router.include_router(field_environment.router, tags=["Field Environment"])
router.include_router(environmental_router, prefix="/environmental", tags=["Environmental Physics"])
router.include_router(weather_module_router, tags=["Weather Service"])

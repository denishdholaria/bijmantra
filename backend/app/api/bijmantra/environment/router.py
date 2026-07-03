"""
Environment Domain Router Aggregator
Combines all environment-related endpoints: weather, climate, carbon, emissions, environmental physics.
"""
from fastapi import APIRouter

from app.api.bijmantra.environment import (
    carbon,
    climate,
    emissions,
    environmental,
    weather,
)

environment_router = APIRouter()

# Weather & Climate
environment_router.include_router(weather.router, tags=["Weather Intelligence"])
environment_router.include_router(climate.router, tags=["Climate Analysis"])

# Carbon & Emissions
environment_router.include_router(carbon.router, tags=["Carbon Monitoring"])
environment_router.include_router(emissions.router, tags=["Emissions Tracking"])

# Environmental Physics
environment_router.include_router(environmental.router, prefix="/environmental", tags=["Environmental Physics"])

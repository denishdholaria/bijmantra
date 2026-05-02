"""Compute domain router aggregator."""
from fastapi import APIRouter

from app.api.bijmantra.compute import (
    analytics,
    biosimulation,
    calculators,
    compute,
    mixed_model,
    simulation,
    statistics,
)

compute_router = APIRouter()

compute_router.include_router(compute.router, tags=["Compute Engine"])
compute_router.include_router(analytics.router, tags=["Analytics"])
compute_router.include_router(calculators.router, tags=["Calculators"])
compute_router.include_router(mixed_model.router, tags=["Mixed Models"])
compute_router.include_router(statistics.router, tags=["Statistics"])
compute_router.include_router(biosimulation.router, tags=["Biosimulation"])
compute_router.include_router(simulation.router, tags=["Simulation"])

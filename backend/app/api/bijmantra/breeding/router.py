"""
Breeding Domain Router Aggregator

Composes all breeding-related routers into a single mountable router.
"""

from fastapi import APIRouter

from app.api.bijmantra.breeding import (
    breeding_pipeline,
    breeding_value,
    crosses,
    crossing_planner,
    doubled_haploid,
    parent_selection,
    progeny,
    selection,
    selection_decisions,
    speed_breeding,
)

breeding_router = APIRouter()

# Include all breeding domain routers
breeding_router.include_router(breeding_pipeline.router, tags=["Breeding Pipeline"])
breeding_router.include_router(breeding_value.router, tags=["Breeding Value"])
breeding_router.include_router(crosses.router, tags=["Cross Prediction"])
breeding_router.include_router(crossing_planner.router, tags=["Crossing Planner"])
breeding_router.include_router(doubled_haploid.router, tags=["Doubled Haploid"])
breeding_router.include_router(parent_selection.router, tags=["Parent Selection"])
breeding_router.include_router(progeny.router, tags=["Progeny"])
breeding_router.include_router(selection.router, tags=["Selection Index"])
breeding_router.include_router(selection_decisions.router, tags=["Selection Decisions"])
breeding_router.include_router(speed_breeding.router, tags=["Speed Breeding"])

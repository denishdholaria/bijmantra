"""
Breeding Domain API Router

Consolidates all breeding-related endpoints under /api/v2/breeding/*
Migrated from flat api/v2/ structure to domain-based organization.

Endpoints organized by subdomain:
- Breeding Values (BLUP/GBLUP)
- Cross Prediction & Planning
- Pedigree Analysis
- Parent Selection
- Breeding Pipeline
- Nursery Management
- Trial Design & Planning
- Selection Decisions
- Speed Breeding
"""

from fastapi import APIRouter

# Import all breeding-related routers
from app.api.v2 import (
    breeding_pipeline,
    breeding_value,
    crosses,
    crossing_planner,
    nursery,
    parent_selection,
    pedigree,
    selection,
    selection_decisions,
    speed_breeding,
    trial_design,
    trial_network,
    trial_planning,
)

# Create main breeding router with /api/v2 prefix
# Individual routers will be included with their own prefixes
router = APIRouter(prefix="/api/v2", tags=["Breeding"])

# Include all breeding sub-routers
# These maintain their original prefixes for backward compatibility
router.include_router(breeding_value.router, tags=["Breeding Value"])
router.include_router(crosses.router, tags=["Cross Prediction"])
router.include_router(crossing_planner.router, tags=["Crossing Planner"])
router.include_router(pedigree.router, tags=["Pedigree Analysis"])
router.include_router(parent_selection.router, tags=["Parent Selection"])
router.include_router(breeding_pipeline.router, tags=["Breeding Pipeline"])
router.include_router(nursery.router, tags=["Nursery Management"])
router.include_router(selection.router, tags=["Selection Index"])
router.include_router(selection_decisions.router, tags=["Selection Decisions"])
router.include_router(speed_breeding.router, tags=["Speed Breeding"])
router.include_router(trial_design.router, tags=["Trial Design"])
router.include_router(trial_network.router, tags=["Trial Network"])
router.include_router(trial_planning.router, tags=["Trial Planning"])

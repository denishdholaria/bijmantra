"""Trials domain router aggregator."""
from fastapi import APIRouter

from app.api.bijmantra.trials import (
    stability_analysis,
    trial_design,
    trial_network,
    trial_planning,
    trial_summary,
)

trials_router = APIRouter()

trials_router.include_router(stability_analysis.router, tags=["Stability Analysis"])
trials_router.include_router(trial_design.router, tags=["Trial Design"])
trials_router.include_router(trial_network.router, tags=["Trial Network"])
trials_router.include_router(trial_planning.router, tags=["Trial Planning"])
trials_router.include_router(trial_summary.router, tags=["Trial Summary"])

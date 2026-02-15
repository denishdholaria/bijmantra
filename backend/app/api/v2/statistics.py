"""
Statistics API
Endpoints for statistical analysis of breeding data
"""
from typing import Optional, List
from fastapi import APIRouter, Query, Depends

from app.services.statistics import statistics_service
from app.api.deps import get_current_user


router = APIRouter(prefix="/statistics", tags=["Statistics"], dependencies=[Depends(get_current_user)])


@router.get("/trials")
async def get_trials():
    """Get available trials for analysis."""
    trials = statistics_service.get_trials()
    return {"trials": trials, "total": len(trials)}


@router.get("/traits")
async def get_traits():
    """Get available traits."""
    traits = statistics_service.get_traits()
    return {"traits": traits, "total": len(traits)}


@router.get("/overview")
async def get_overview(trial_id: Optional[str] = Query(None)):
    """Get overview statistics for a trial."""
    return statistics_service.get_overview(trial_id=trial_id)


@router.get("/summary")
async def get_summary_stats(
    trial_id: Optional[str] = Query(None),
    trait_ids: Optional[str] = Query(None, description="Comma-separated trait IDs"),
):
    """Get descriptive statistics for traits."""
    trait_list = trait_ids.split(",") if trait_ids else None
    return statistics_service.get_summary_stats(trial_id=trial_id, trait_ids=trait_list)


@router.get("/correlations")
async def get_correlations(
    trial_id: Optional[str] = Query(None),
    trait_ids: Optional[str] = Query(None, description="Comma-separated trait IDs"),
):
    """Get correlation matrix between traits."""
    trait_list = trait_ids.split(",") if trait_ids else None
    return statistics_service.get_correlations(trial_id=trial_id, trait_ids=trait_list)


@router.get("/distribution")
async def get_distribution(
    trait_id: str = Query("yield"),
    trial_id: Optional[str] = Query(None),
    bins: int = Query(10, ge=5, le=50),
):
    """Get distribution data for a trait."""
    return statistics_service.get_distribution(trial_id=trial_id, trait_id=trait_id, bins=bins)


@router.get("/anova")
async def get_anova(
    trait_id: str = Query("yield"),
    trial_id: Optional[str] = Query(None),
):
    """Calculate ANOVA for a trait."""
    return statistics_service.calculate_anova(trial_id=trial_id, trait_id=trait_id)

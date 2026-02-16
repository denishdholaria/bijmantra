"""
Field Planning API
Field and season planning — queries Trial, Study, Season, Location tables.

Refactored: Session 94 — migrated from DEMO_FIELD_PLANS/DEMO_SEASON_PLANS to real DB queries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.core import Trial, Study, Season, Location

from app.api.deps import get_current_user

router = APIRouter(prefix="/field-planning", tags=["Field Planning"], dependencies=[Depends(get_current_user)])


@router.get("/plans")
async def get_field_plans(
    field_id: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get field plans — derived from Trials with their Studies."""
    query = select(Trial).where(Trial.organization_id == organization_id)
    if status:
        query = query.where(Trial.active == (status == "active"))

    result = await db.execute(query)
    trials = result.scalars().all()

    plans = []
    for t in trials:
        # Get studies for this trial
        studies_q = await db.execute(
            select(Study).where(Study.trial_id == t.id)
        )
        studies = studies_q.scalars().all()

        plan = {
            "id": str(t.id),
            "name": t.trial_name,
            "field_id": str(t.location_id) if t.location_id else None,
            "field_name": None,
            "season": None,
            "crop": t.common_crop_name,
            "total_plots": sum(s.observation_units_count or 0 for s in studies) if studies else 0,
            "allocated_plots": sum(s.observation_units_count or 0 for s in studies) if studies else 0,
            "trials": [{"trial_id": str(t.id), "name": t.trial_name, "plots": sum(s.observation_units_count or 0 for s in studies)}],
            "start_date": t.start_date.isoformat() if hasattr(t, "start_date") and t.start_date else None,
            "end_date": t.end_date.isoformat() if hasattr(t, "end_date") and t.end_date else None,
            "status": "active" if t.active else "completed",
        }
        plans.append(plan)

    return plans


@router.get("/plans/{plan_id}")
async def get_field_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get single field plan (Trial)."""
    t = (await db.execute(
        select(Trial).where(Trial.id == plan_id, Trial.organization_id == organization_id)
    )).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Plan not found")

    studies = (await db.execute(select(Study).where(Study.trial_id == t.id))).scalars().all()

    return {
        "id": str(t.id),
        "name": t.trial_name,
        "crop": t.common_crop_name,
        "total_plots": sum(s.observation_units_count or 0 for s in studies),
        "studies": [{"id": str(s.id), "name": s.study_name, "plots": s.observation_units_count or 0} for s in studies],
        "status": "active" if t.active else "completed",
    }


@router.get("/seasons")
async def get_season_plans(
    year: Optional[int] = Query(None),
    season_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get season plans — from Season table."""
    query = select(Season).where(Season.organization_id == organization_id)
    if year:
        query = query.where(Season.year == year)

    result = await db.execute(query)
    seasons = result.scalars().all()

    plans = []
    for s in seasons:
        # Count trials in this season
        trial_count = (await db.execute(
            select(func.count(Trial.id)).where(
                Trial.organization_id == organization_id,
                Trial.season_id == s.id
            )
        )).scalar() or 0

        plans.append({
            "id": str(s.id),
            "name": s.season_name,
            "year": s.year,
            "season_type": s.season_name,
            "total_trials": trial_count,
            "status": "active",
        })

    return plans


@router.get("/seasons/{plan_id}")
async def get_season_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get single season plan."""
    s = (await db.execute(
        select(Season).where(Season.id == plan_id, Season.organization_id == organization_id)
    )).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Season plan not found")

    trial_count = (await db.execute(
        select(func.count(Trial.id)).where(Trial.organization_id == organization_id, Trial.season_id == s.id)
    )).scalar() or 0

    return {
        "id": str(s.id),
        "name": s.season_name,
        "year": s.year,
        "total_trials": trial_count,
    }


@router.get("/resources/{plan_id}")
async def get_resource_allocation(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get resource allocation for a plan. Returns empty structure — resource tracking table not yet created."""
    t = (await db.execute(
        select(Trial).where(Trial.id == plan_id, Trial.organization_id == organization_id)
    )).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {
        "plan_id": str(plan_id),
        "resources": [],
        "budget": {"total": 0, "allocated": 0, "spent": 0},
        "note": "Resource allocation tracking not yet implemented. Table creation pending.",
    }


@router.get("/calendar")
async def get_calendar(
    year: int = Query(...),
    month: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get planning calendar — derived from Trial start/end dates."""
    query = select(Trial).where(Trial.organization_id == organization_id)
    result = await db.execute(query)
    trials = result.scalars().all()

    events = []
    for t in trials:
        if hasattr(t, "start_date") and t.start_date:
            if t.start_date.year == year and (not month or t.start_date.month == month):
                events.append({
                    "id": f"trial-start-{t.id}",
                    "date": t.start_date.isoformat(),
                    "activity": "Trial Start",
                    "field": t.trial_name,
                    "trial": t.trial_name,
                })
        if hasattr(t, "end_date") and t.end_date:
            if t.end_date.year == year and (not month or t.end_date.month == month):
                events.append({
                    "id": f"trial-end-{t.id}",
                    "date": t.end_date.isoformat(),
                    "activity": "Trial End",
                    "field": t.trial_name,
                    "trial": t.trial_name,
                })

    events.sort(key=lambda x: x["date"])
    return events


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get planning statistics from real Trial/Season data."""
    trial_count = (await db.execute(
        select(func.count(Trial.id)).where(Trial.organization_id == organization_id)
    )).scalar() or 0

    active_count = (await db.execute(
        select(func.count(Trial.id)).where(Trial.organization_id == organization_id, Trial.active == True)
    )).scalar() or 0

    season_count = (await db.execute(
        select(func.count(Season.id)).where(Season.organization_id == organization_id)
    )).scalar() or 0

    return {
        "total_field_plans": trial_count,
        "total_season_plans": season_count,
        "active_plans": active_count,
        "total_plots_planned": 0,
        "total_plots_allocated": 0,
        "utilization_rate": 0,
    }

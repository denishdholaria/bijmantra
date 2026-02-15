"""
Field Map API
Field and plot spatial data — queries Location + ObservationUnit + Study tables.

Refactored: Session 94 — migrated from in-memory demo data to DB queries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.core import Location, Study, Trial
from app.models.phenotyping import ObservationUnit

from app.api.deps import get_current_user

router = APIRouter(prefix="/field-map", tags=["Field Map"], dependencies=[Depends(get_current_user)])


# ============================================================================
# Helpers
# ============================================================================

def _location_to_field(loc: Location, trial_count: int = 0) -> dict:
    return {
        "id": str(loc.id),
        "name": loc.location_name,
        "locationType": loc.location_type,
        "country": loc.country_name,
        "trials": trial_count,
    }


# ============================================================================
# Field Endpoints
# ============================================================================

@router.get("/fields")
async def list_fields(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """List fields (locations) with trial counts."""
    q = select(Location).where(Location.organization_id == organization_id)
    if search:
        q = q.where(Location.location_name.ilike(f"%{search}%"))

    total = (await db.execute(
        select(func.count()).select_from(q.subquery())
    )).scalar() or 0

    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    locations = result.scalars().all()

    fields = []
    for loc in locations:
        trial_count = (await db.execute(
            select(func.count(Trial.id)).where(Trial.location_id == loc.id)
        )).scalar() or 0
        fields.append(_location_to_field(loc, trial_count))

    return {"data": fields, "total": total, "page": page, "page_size": page_size}


@router.get("/fields/{field_id}")
async def get_field(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get field details."""
    loc = (await db.execute(
        select(Location).where(
            Location.id == field_id,
            Location.organization_id == organization_id,
        )
    )).scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=404, detail="Field not found")

    trial_count = (await db.execute(
        select(func.count(Trial.id)).where(Trial.location_id == loc.id)
    )).scalar() or 0

    return _location_to_field(loc, trial_count)


@router.get("/fields/{field_id}/plots")
async def get_field_plots(
    field_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get plots (observation units) for a field via its studies."""
    # Get studies linked to trials at this location
    study_ids_q = (
        select(Study.id)
        .join(Trial, Study.trial_id == Trial.id)
        .where(Trial.location_id == field_id, Trial.organization_id == organization_id)
    )
    study_ids = (await db.execute(study_ids_q)).scalars().all()

    if not study_ids:
        return {"data": [], "total": 0, "page": page, "page_size": page_size}

    q = select(ObservationUnit).where(
        ObservationUnit.study_id.in_(study_ids),
        ObservationUnit.organization_id == organization_id,
    )
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    units = result.scalars().all()

    plots = []
    for u in units:
        plots.append({
            "id": str(u.id),
            "name": u.observation_unit_name,
            "observationUnitDbId": u.observation_unit_db_id,
            "studyId": str(u.study_id) if u.study_id else None,
            "positionX": u.position_coordinate_x,
            "positionY": u.position_coordinate_y,
            "entryType": u.entry_type,
            "observationLevel": u.observation_level,
        })

    return {"data": plots, "total": total, "page": page, "page_size": page_size}


# ============================================================================
# Summary
# ============================================================================

@router.get("/summary")
async def get_field_map_summary(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get field map summary statistics."""
    location_count = (await db.execute(
        select(func.count(Location.id)).where(Location.organization_id == organization_id)
    )).scalar() or 0

    trial_count = (await db.execute(
        select(func.count(Trial.id)).where(Trial.organization_id == organization_id)
    )).scalar() or 0

    plot_count = (await db.execute(
        select(func.count(ObservationUnit.id)).where(ObservationUnit.organization_id == organization_id)
    )).scalar() or 0

    return {
        "total_fields": location_count,
        "total_trials": trial_count,
        "total_plots": plot_count,
    }

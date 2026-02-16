"""
Plot History API
Plot event history and timeline — queries ObservationUnit + Observation tables.

Refactored: Session 94 — migrated from in-memory demo data to real DB queries.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.phenotyping import ObservationUnit, Observation
from app.models.core import Study, Location

from app.api.deps import get_current_user

router = APIRouter(prefix="/plot-history", tags=["Plot History"], dependencies=[Depends(get_current_user)])


class CreateEventRequest(BaseModel):
    type: str
    description: str
    date: Optional[str] = None
    value: Optional[str] = None
    notes: Optional[str] = None
    recorded_by: Optional[str] = None


class UpdateEventRequest(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    value: Optional[str] = None
    notes: Optional[str] = None


@router.get("/stats")
async def get_stats(
    field_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get plot history statistics."""
    plot_count = (await db.execute(
        select(func.count(ObservationUnit.id)).where(ObservationUnit.organization_id == organization_id)
    )).scalar() or 0

    obs_count = (await db.execute(
        select(func.count(Observation.id)).where(Observation.organization_id == organization_id)
    )).scalar() or 0

    study_count = (await db.execute(
        select(func.count(func.distinct(ObservationUnit.study_id))).where(
            ObservationUnit.organization_id == organization_id
        )
    )).scalar() or 0

    return {
        "total_plots": plot_count,
        "total_events": obs_count,
        "total_fields": study_count,
        "active_plots": plot_count,
    }


@router.get("/event-types")
async def get_event_types():
    """Get available event types — static reference data."""
    return {
        "types": [
            {"value": "observation", "label": "Observation", "icon": "eye"},
            {"value": "treatment", "label": "Treatment", "icon": "syringe"},
            {"value": "planting", "label": "Planting", "icon": "sprout"},
            {"value": "harvest", "label": "Harvest", "icon": "wheat"},
            {"value": "irrigation", "label": "Irrigation", "icon": "droplets"},
            {"value": "fertilizer", "label": "Fertilizer", "icon": "flask"},
            {"value": "pest_control", "label": "Pest Control", "icon": "bug"},
            {"value": "note", "label": "Note", "icon": "pencil"},
        ]
    }


@router.get("/fields")
async def get_fields(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get available fields (Studies)."""
    result = await db.execute(
        select(Study).where(Study.organization_id == organization_id).limit(100)
    )
    studies = result.scalars().all()
    return {
        "fields": [
            {"id": str(s.id), "name": s.study_name, "study_id": str(s.id)}
            for s in studies
        ]
    }


@router.get("/plots")
async def get_plots(
    field_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get plots (ObservationUnits) with optional filters."""
    query = select(ObservationUnit).where(ObservationUnit.organization_id == organization_id)

    if field_id and field_id.isdigit():
        query = query.where(ObservationUnit.study_id == int(field_id))
    if search:
        query = query.where(
            ObservationUnit.observation_unit_name.ilike(f"%{search}%")
        )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.order_by(ObservationUnit.id).offset(offset).limit(limit))
    units = result.scalars().all()

    plots = []
    for u in units:
        plots.append({
            "id": str(u.id),
            "plot_id": u.observation_unit_db_id or str(u.id),
            "name": u.observation_unit_name,
            "study_id": str(u.study_id) if u.study_id else None,
            "position": u.observation_unit_position,
            "status": "active",
        })

    return {"plots": plots, "total": total, "limit": limit, "offset": offset}


@router.get("/plots/{plot_id}")
async def get_plot(
    plot_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get a single plot with its observations."""
    unit = (await db.execute(
        select(ObservationUnit).where(
            ObservationUnit.id == plot_id, ObservationUnit.organization_id == organization_id
        )
    )).scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Plot not found")

    obs_result = await db.execute(
        select(Observation).where(Observation.observation_unit_id == unit.id).order_by(desc(Observation.created_at)).limit(50)
    )
    observations = obs_result.scalars().all()

    events = [
        {
            "id": str(o.id),
            "type": "observation",
            "description": f"Observation: {o.observation_variable_name or 'measurement'}",
            "date": o.observation_time_stamp.isoformat() if o.observation_time_stamp else (o.created_at.isoformat() if o.created_at else ""),
            "value": o.value,
        }
        for o in observations
    ]

    return {
        "id": str(unit.id),
        "plot_id": unit.observation_unit_db_id or str(unit.id),
        "name": unit.observation_unit_name,
        "events": events,
        "event_count": len(events),
    }


@router.get("/plots/{plot_id}/events")
async def get_plot_events(
    plot_id: int,
    event_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get observations for a specific plot."""
    query = select(Observation).where(Observation.observation_unit_id == plot_id)
    if start_date:
        query = query.where(Observation.observation_time_stamp >= start_date)
    if end_date:
        query = query.where(Observation.observation_time_stamp <= end_date)

    query = query.order_by(desc(Observation.created_at)).limit(200)
    result = await db.execute(query)
    observations = result.scalars().all()

    return [
        {
            "id": str(o.id),
            "type": "observation",
            "description": f"Observation: {o.observation_variable_name or 'measurement'}",
            "date": o.observation_time_stamp.isoformat() if o.observation_time_stamp else "",
            "value": o.value,
        }
        for o in observations
    ]


@router.post("/plots/{plot_id}/events")
async def create_event(
    plot_id: int,
    request: CreateEventRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Create a new observation for a plot."""
    unit = (await db.execute(
        select(ObservationUnit).where(
            ObservationUnit.id == plot_id, ObservationUnit.organization_id == organization_id
        )
    )).scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Plot not found")

    obs = Observation(
        organization_id=organization_id,
        observation_unit_id=unit.id,
        observation_variable_name=request.type,
        value=request.value or request.description,
        observation_time_stamp=request.date,
    )
    db.add(obs)
    await db.commit()
    await db.refresh(obs)

    return {
        "id": str(obs.id),
        "type": request.type,
        "description": request.description,
        "date": request.date,
        "value": request.value,
    }


@router.patch("/events/{event_id}")
async def update_event(
    event_id: int,
    request: UpdateEventRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Update an existing observation."""
    obs = (await db.execute(
        select(Observation).where(Observation.id == event_id, Observation.organization_id == organization_id)
    )).scalar_one_or_none()
    if not obs:
        raise HTTPException(status_code=404, detail="Event not found")

    if request.value is not None:
        obs.value = request.value
    if request.description is not None:
        obs.observation_variable_name = request.description
    if request.date is not None:
        obs.observation_time_stamp = request.date

    await db.commit()
    await db.refresh(obs)

    return {"id": str(obs.id), "type": obs.observation_variable_name, "value": obs.value}


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Delete an observation."""
    obs = (await db.execute(
        select(Observation).where(Observation.id == event_id, Observation.organization_id == organization_id)
    )).scalar_one_or_none()
    if not obs:
        raise HTTPException(status_code=404, detail="Event not found")

    await db.delete(obs)
    await db.commit()
    return {"success": True, "message": "Event deleted"}

"""
Growing Degree Day (GDD) API

Endpoints for tracking crop development through accumulated heat units.

Scientific Formula (preserved per scientific-documentation.md):
    GDD = max(0, (Tmax + Tmin) / 2 - Tbase)
    
    Where:
    - Tmax = Daily maximum temperature (°C)
    - Tmin = Daily minimum temperature (°C)
    - Tbase = Base temperature (crop-specific)

Common Base Temperatures:
    - Corn/Maize: 10°C
    - Wheat: 0°C
    - Rice: 10°C
    - Cotton: 15.5°C
"""

from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import gdd as gdd_crud
from app.schemas.future.crop_intelligence import (
    GrowingDegreeDayLog,
    GrowingDegreeDayLogCreate,
    GrowingDegreeDayLogUpdate,
)
from app.models.core import User

router = APIRouter(prefix="/gdd", tags=["Growing Degree Days"])


@router.get("/", response_model=List[GrowingDegreeDayLog])
async def list_gdd_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    List all GDD log entries for the organization.
    
    Returns paginated list of Growing Degree Day records.
    """
    logs, _ = await gdd_crud.gdd_log.get_multi(db, skip=skip, limit=limit, org_id=org_id)
    return logs


@router.get("/{id}", response_model=GrowingDegreeDayLog)
async def get_gdd_log(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single GDD log entry by ID."""
    log = await gdd_crud.gdd_log.get(db, id=id)
    if not log or log.organization_id != org_id:
        raise HTTPException(status_code=404, detail="GDD log not found")
    return log


@router.post("/", response_model=GrowingDegreeDayLog, status_code=201)
async def create_gdd_log(
    log_in: GrowingDegreeDayLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new GDD log entry.
    
    GDD Formula: GDD = max(0, (Tmax + Tmin) / 2 - Tbase)
    """
    log = await gdd_crud.gdd_log.create(db, obj_in=log_in, org_id=current_user.organization_id)
    await db.commit()
    await db.refresh(log)
    return log


@router.put("/{id}", response_model=GrowingDegreeDayLog)
async def update_gdd_log(
    id: int,
    log_in: GrowingDegreeDayLogUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Update a GDD log entry."""
    log = await gdd_crud.gdd_log.get(db, id=id)
    if not log or log.organization_id != org_id:
        raise HTTPException(status_code=404, detail="GDD log not found")
    
    log = await gdd_crud.gdd_log.update(db, db_obj=log, obj_in=log_in)
    await db.commit()
    await db.refresh(log)
    return log


@router.delete("/{id}", status_code=204)
async def delete_gdd_log(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a GDD log entry."""
    log = await gdd_crud.gdd_log.get(db, id=id)
    if not log or log.organization_id != org_id:
        raise HTTPException(status_code=404, detail="GDD log not found")
    
    await gdd_crud.gdd_log.delete(db, id=id)
    await db.commit()
    return None


@router.post("/calculate")
async def calculate_gdd(
    tmax: float = Query(..., description="Maximum temperature (°C)"),
    tmin: float = Query(..., description="Minimum temperature (°C)"),
    tbase: float = Query(10.0, description="Base temperature (°C)")
):
    """
    Calculate Growing Degree Days for a single day.
    
    GDD = max(0, (Tmax + Tmin) / 2 - Tbase)
    
    Args:
        tmax: Daily maximum temperature in °C
        tmin: Daily minimum temperature in °C
        tbase: Base temperature for the crop (default 10°C for corn)
    
    Returns:
        Calculated GDD value and interpretation
    """
    avg_temp = (tmax + tmin) / 2
    gdd = max(0, avg_temp - tbase)
    
    return {
        "tmax": tmax,
        "tmin": tmin,
        "tbase": tbase,
        "average_temperature": round(avg_temp, 2),
        "gdd": round(gdd, 2),
        "formula": "GDD = max(0, (Tmax + Tmin) / 2 - Tbase)"
    }


@router.get("/field/{field_id}/summary")
async def get_field_gdd_summary(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get cumulative GDD summary for a field.
    
    Returns total accumulated GDD, date range, and days logged.
    """
    summary = await gdd_crud.gdd_log.get_cumulative_summary(db, field_id=field_id, org_id=org_id)
    return summary


@router.get("/field/{field_id}/history", response_model=List[GrowingDegreeDayLog])
async def get_field_gdd_history(
    field_id: int,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get GDD history for a field within a date range."""
    logs = await gdd_crud.gdd_log.get_by_field_and_date_range(
        db, field_id=field_id, start_date=start_date, end_date=end_date, org_id=org_id
    )
    return logs

"""
Irrigation Schedule API

Endpoints for irrigation planning and scheduling.

Scientific Framework (preserved per scientific-documentation.md):
    Crop Water Requirement (FAO-56):
        ETc = ET0 × Kc
        
        Where:
        - ETc = Crop evapotranspiration (mm/day)
        - ET0 = Reference evapotranspiration (mm/day)
        - Kc = Crop coefficient (varies by growth stage)
    
    Net Irrigation Requirement:
        NIR = ETc - Effective Rainfall - Soil Moisture Contribution
    
    Common Crop Coefficients (Kc):
        - Initial: 0.3-0.5
        - Development: 0.7-0.85
        - Mid-season: 1.0-1.2
        - Late season: 0.6-0.8
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import irrigation_schedule as irrigation_crud
from app.schemas.future.water_irrigation import (
    IrrigationSchedule,
    IrrigationScheduleCreate,
    IrrigationScheduleUpdate,
)
from app.models.core import User

router = APIRouter(prefix="/irrigation-schedules", tags=["Irrigation Schedules"])


@router.get("/", response_model=List[IrrigationSchedule])
async def list_irrigation_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all irrigation schedules for the organization."""
    records, _ = await irrigation_crud.irrigation_schedule.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )
    return records


@router.get("/{id}", response_model=IrrigationSchedule)
async def get_irrigation_schedule(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single irrigation schedule by ID."""
    record = await irrigation_crud.irrigation_schedule.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Irrigation schedule not found")
    return record


@router.post("/", response_model=IrrigationSchedule, status_code=201)
async def create_irrigation_schedule(
    record_in: IrrigationScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new irrigation schedule.
    
    Crop Water Requirement: ETc = ET0 × Kc
    Net Irrigation = ETc - Effective Rainfall - Soil Contribution
    """
    record = await irrigation_crud.irrigation_schedule.create(
        db, obj_in=record_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.put("/{id}", response_model=IrrigationSchedule)
async def update_irrigation_schedule(
    id: int,
    record_in: IrrigationScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an irrigation schedule."""
    record = await irrigation_crud.irrigation_schedule.get(db, id=id)
    if not record or record.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Irrigation schedule not found")

    record = await irrigation_crud.irrigation_schedule.update(
        db, db_obj=record, obj_in=record_in
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{id}", status_code=204)
async def delete_irrigation_schedule(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete an irrigation schedule."""
    record = await irrigation_crud.irrigation_schedule.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Irrigation schedule not found")

    await irrigation_crud.irrigation_schedule.delete(db, id=id)
    await db.commit()
    return None


@router.get("/field/{field_id}", response_model=List[IrrigationSchedule])
async def get_field_irrigation_schedules(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all irrigation schedules for a field."""
    records = await irrigation_crud.irrigation_schedule.get_by_field(
        db, field_id=field_id, org_id=org_id
    )
    return records


@router.get("/field/{field_id}/upcoming", response_model=List[IrrigationSchedule])
async def get_upcoming_irrigation(
    field_id: int,
    days_ahead: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get upcoming irrigation schedules for a field.
    
    Returns schedules within the specified number of days ahead.
    """
    records = await irrigation_crud.irrigation_schedule.get_upcoming(
        db, field_id=field_id, org_id=org_id, days_ahead=days_ahead
    )
    return records

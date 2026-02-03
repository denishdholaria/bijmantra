"""
Water Balance API

Endpoints for tracking field water balance.

Scientific Framework (preserved per scientific-documentation.md):
    Water Balance Equation:
        ΔS = P + I - ET - R - D
        
        Where:
        - ΔS = Change in soil water storage
        - P = Precipitation
        - I = Irrigation
        - ET = Evapotranspiration
        - R = Runoff
        - D = Deep percolation
    
    Soil Water Storage:
        Available Water = Field Capacity - Wilting Point
        Readily Available Water = Available Water × MAD
        
        Where MAD = Management Allowable Depletion (typically 50%)
    
    Deficit Irrigation:
        Controlled water stress to improve quality or save water.
        Requires careful monitoring of soil moisture status.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.services.water_balance_service import water_balance_service
from app.schemas.future.water_irrigation import (
    WaterBalance,
    WaterBalanceCreate,
)
from app.models.core import User

router = APIRouter(prefix="/water-balance", tags=["Water Balance"])


@router.get("/", response_model=List[WaterBalance])
async def list_water_balance_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all water balance records for the organization."""
    return await water_balance_service.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )


@router.get("/{id}", response_model=WaterBalance)
async def get_water_balance_record(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single water balance record by ID."""
    record = await water_balance_service.get(db, id=id, org_id=org_id)
    if not record:
        raise HTTPException(status_code=404, detail="Water balance record not found")
    return record


@router.post("/", response_model=WaterBalance, status_code=201)
async def create_water_balance_record(
    record_in: WaterBalanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new water balance record.
    
    Water Balance: ΔS = P + I - ET - R - D
    """
    return await water_balance_service.create(
        db, obj_in=record_in, org_id=current_user.organization_id
    )


@router.delete("/{id}", status_code=204)
async def delete_water_balance_record(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a water balance record."""
    result = await water_balance_service.delete(db, id=id, org_id=org_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Water balance record not found")
    return None


@router.get("/field/{field_id}", response_model=List[WaterBalance])
async def get_field_water_balance(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all water balance records for a field."""
    return await water_balance_service.get_by_field(
        db, field_id=field_id, org_id=org_id
    )


@router.get("/field/{field_id}/summary")
async def get_field_water_summary(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get water balance summary for a field.
    
    Returns totals for precipitation, irrigation, ET, and average soil moisture.
    """
    return await water_balance_service.get_field_summary(
        db, field_id=field_id, org_id=org_id
    )

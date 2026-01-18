"""
Soil Moisture API

Endpoints for soil moisture sensor readings and monitoring.

Scientific Framework (preserved per scientific-documentation.md):
    Volumetric Water Content (VWC):
        VWC = Volume of water / Total soil volume
        Expressed as decimal (0-1) or percentage (0-100%)
    
    Soil Moisture Thresholds:
        - Saturation: All pores filled (0.4-0.5 VWC)
        - Field Capacity: After drainage (0.25-0.35 VWC)
        - Wilting Point: Plants cannot extract water (0.1-0.15 VWC)
        - Available Water: Field Capacity - Wilting Point
    
    Sensor Types:
        - Capacitance: Measures dielectric permittivity
        - TDR: Time Domain Reflectometry
        - Tensiometer: Measures soil water tension
        - Gypsum blocks: Electrical resistance
    
    Depth Considerations:
        - 10-20 cm: Root zone for shallow crops
        - 30-60 cm: Main root zone for most crops
        - 60-100 cm: Deep root zone, drainage monitoring
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import soil_moisture as moisture_crud
from app.schemas.future.water_irrigation import (
    SoilMoistureReading,
    SoilMoistureReadingCreate,
)
from app.models.core import User

router = APIRouter(prefix="/soil-moisture", tags=["Soil Moisture"])


@router.get("/", response_model=List[SoilMoistureReading])
async def list_soil_moisture_readings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all soil moisture readings for the organization."""
    records, _ = await moisture_crud.soil_moisture.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )
    return records


@router.get("/{id}", response_model=SoilMoistureReading)
async def get_soil_moisture_reading(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single soil moisture reading by ID."""
    record = await moisture_crud.soil_moisture.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Soil moisture reading not found")
    return record


@router.post("/", response_model=SoilMoistureReading, status_code=201)
async def create_soil_moisture_reading(
    record_in: SoilMoistureReadingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new soil moisture reading.
    
    VWC expressed as decimal (0-1):
        - 0.4-0.5: Saturation
        - 0.25-0.35: Field Capacity
        - 0.1-0.15: Wilting Point
    """
    record = await moisture_crud.soil_moisture.create(
        db, obj_in=record_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{id}", status_code=204)
async def delete_soil_moisture_reading(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a soil moisture reading."""
    record = await moisture_crud.soil_moisture.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Soil moisture reading not found")
    
    await moisture_crud.soil_moisture.delete(db, id=id)
    await db.commit()
    return None


@router.get("/field/{field_id}", response_model=List[SoilMoistureReading])
async def get_field_soil_moisture(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all soil moisture readings for a field."""
    records = await moisture_crud.soil_moisture.get_by_field(
        db, field_id=field_id, org_id=org_id
    )
    return records


@router.get("/device/{device_id}", response_model=List[SoilMoistureReading])
async def get_device_readings(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all readings from a specific sensor device."""
    records = await moisture_crud.soil_moisture.get_by_device(
        db, device_id=device_id, org_id=org_id
    )
    return records


@router.get("/device/{device_id}/latest", response_model=Optional[SoilMoistureReading])
async def get_device_latest_reading(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get the most recent reading from a sensor device."""
    record = await moisture_crud.soil_moisture.get_latest_by_device(
        db, device_id=device_id, org_id=org_id
    )
    return record


@router.get("/field/{field_id}/timeseries", response_model=List[SoilMoistureReading])
async def get_field_moisture_timeseries(
    field_id: int,
    hours: int = Query(24, ge=1, le=168, description="Hours of data to retrieve"),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get soil moisture timeseries for a field.
    
    Returns readings over the specified time period (default 24 hours).
    """
    records = await moisture_crud.soil_moisture.get_timeseries(
        db, field_id=field_id, org_id=org_id, hours=hours
    )
    return records

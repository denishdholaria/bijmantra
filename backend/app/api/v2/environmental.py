from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.services.environmental_physics import environmental_service
from app.models.environmental import EnvironmentalUnit
from pydantic import BaseModel

router = APIRouter()

class EnvironmentalRecordCreate(BaseModel):
    location_id: int
    date_record: date
    t_max: float
    t_min: float
    day_length: Optional[float] = None
    crop_base_temp: float = 10.0

class EnvironmentalRecordResponse(BaseModel):
    id: int
    location_id: int
    date_calculated: date
    gdd_accumulated: Optional[float]
    ptu_accumulated: Optional[float]
    soil_moisture_index: Optional[float]

    class Config:
        from_attributes = True

@router.post("/calculate", response_model=EnvironmentalRecordResponse)
async def calculate_daily_indices(
    record: EnvironmentalRecordCreate,
    db: AsyncSession = Depends(deps.get_db),
    # current_user: models.User = Depends(deps.get_current_active_user) # Uncomment when auth is ready
):
    """
    Calculate and record environmental indices (GDD, PTU) for a specific day/location.
    """
    try:
        result = await environmental_service.record_daily_environment(
            db=db,
            location_id=record.location_id,
            date_record=record.date_record,
            t_max=record.t_max,
            t_min=record.t_min,
            day_length=record.day_length,
            crop_base_temp=record.crop_base_temp
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class LiveWeatherSyncRequest(BaseModel):
    location_id: int
    crop_base_temp: float = 10.0

@router.post("/sync-live", response_model=EnvironmentalRecordResponse)
async def sync_live_weather(
    request: LiveWeatherSyncRequest,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Fetch live weather from Google Maps API and record indices for today.
    """
    try:
        return await environmental_service.sync_todays_weather(
            db=db,
            location_id=request.location_id,
            crop_base_temp=request.crop_base_temp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gdd-calculator", response_model=float)
async def dry_run_gdd(
    t_max: float,
    t_min: float,
    base_temp: float = 10.0
):
    """
    Simple GDD calculator (no database storage).
    Useful for frontend calculators.
    """
    return await environmental_service.calculate_gdd(t_max, t_min, base_temp)

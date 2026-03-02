"""
IoT Telemetry API
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.core import User
from app.schemas.iot.telemetry import TelemetryCreate, TelemetryListResponse, TelemetryResponse
from app.services.iot.telemetry_service import telemetry_service


router = APIRouter(prefix="/iot/telemetry", tags=["IoT Telemetry"])

@router.post("/", response_model=TelemetryResponse, status_code=status.HTTP_201_CREATED)
async def record_reading(
    telemetry_in: TelemetryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record a new sensor reading.
    """
    try:
        telemetry = await telemetry_service.record_reading(
            db=db,
            telemetry_in=telemetry_in
        )
        return telemetry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record reading: {str(e)}")


@router.get("/", response_model=TelemetryListResponse)
async def get_readings(
    device_db_id: str | None = Query(None, description="Filter by Device ID"),
    sensor_code: str | None = Query(None, description="Filter by Sensor Type Code"),
    start_time: datetime | None = Query(None, description="Start time"),
    end_time: datetime | None = Query(None, description="End time"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get sensor readings with filtering.
    """
    try:
        items, total = await telemetry_service.get_readings(
            db=db,
            device_db_id=device_db_id,
            sensor_code=sensor_code,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        return {"total": total, "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch readings: {str(e)}")

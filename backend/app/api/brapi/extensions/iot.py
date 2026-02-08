"""
BrAPI IoT Extension Endpoints

Implements: /brapi/v2/extensions/iot/
Specification: docs/gupt/SensorIOT/sensor-iot.md

PRODUCTION-READY: All data from database, no in-memory mock data.
This extension bridges IoT sensor data with BrAPI breeding workflows.
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.iot import (
    IoTDevice, IoTSensor, IoTTelemetry, IoTAlertRule,
    IoTAlertEvent, IoTAggregate, IoTEnvironmentLink
)

router = APIRouter(prefix="/extensions/iot", tags=["BrAPI IoT Extension"])


# ===========================================
# BrAPI Response Models
# ===========================================

class Pagination(BaseModel):
    currentPage: int = 0
    pageSize: int = 100
    totalCount: int = 0
    totalPages: int = 0


class Metadata(BaseModel):
    pagination: Pagination
    status: List[Dict] = []
    datafiles: List[str] = []


class BrAPIResponse(BaseModel):
    metadata: Metadata
    result: Dict[str, Any]


# ===========================================
# Helper Functions
# ===========================================

def device_to_response(device: IoTDevice) -> dict:
    """Convert IoTDevice model to BrAPI response format"""
    return {
        "deviceDbId": device.device_db_id,
        "deviceName": device.name,
        "deviceType": device.device_type,
        "connectivity": device.connectivity,
        "status": device.status,
        "location": {
            "lat": None,
            "lon": None,
            "elevation": device.elevation
        } if device.elevation else None,
        "environmentDbId": device.environment_id,
        "lastSeen": device.last_seen.isoformat() + "Z" if device.last_seen else None,
        "additionalInfo": {
            "firmware": device.firmware_version,
            "battery": device.battery_level,
            "signalStrength": device.signal_strength,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "serialNumber": device.serial_number,
        }
    }


def sensor_to_response(sensor: IoTSensor) -> dict:
    """Convert IoTSensor model to BrAPI response format"""
    return {
        "sensorDbId": sensor.sensor_db_id,
        "deviceDbId": sensor.device.device_db_id if sensor.device else None,
        "sensorType": sensor.sensor_type,
        "sensorName": sensor.name,
        "unit": sensor.unit,
        "accuracy": sensor.accuracy,
        "additionalInfo": {
            "minValue": sensor.min_value,
            "maxValue": sensor.max_value,
            "precision": sensor.precision,
            **(sensor.additional_info or {})
        }
    }


def aggregate_to_response(agg: IoTAggregate) -> dict:
    """Convert IoTAggregate model to BrAPI response format"""
    return {
        "environmentDbId": agg.environment_db_id,
        "environmentalParameter": agg.parameter,
        "value": agg.value,
        "unit": agg.unit,
        "period": agg.period,
        "startDate": agg.start_time.strftime("%Y-%m-%d") if agg.start_time else None,
        "endDate": agg.end_time.strftime("%Y-%m-%d") if agg.end_time else None,
        "minValue": agg.min_value,
        "maxValue": agg.max_value,
        "sampleCount": agg.sample_count,
        "additionalInfo": {
            "qualityScore": agg.quality_score,
            "calculationMethod": agg.calculation_method,
            **(agg.additional_info or {})
        }
    }


def alert_to_response(alert: IoTAlertEvent) -> dict:
    """Convert IoTAlertEvent model to BrAPI response format"""
    return {
        "alertDbId": alert.event_db_id,
        "alertType": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "deviceDbId": alert.device.device_db_id if alert.device else None,
        "sensorDbId": alert.sensor.sensor_db_id if alert.sensor else None,
        "triggerValue": alert.trigger_value,
        "startTime": alert.start_time.isoformat() + "Z" if alert.start_time else None,
        "endTime": alert.end_time.isoformat() + "Z" if alert.end_time else None,
        "status": alert.status,
        "acknowledged": alert.acknowledged,
    }


def link_to_response(link: IoTEnvironmentLink) -> dict:
    """Convert IoTEnvironmentLink model to BrAPI response format"""
    return {
        "id": str(link.id), # Or a specific link_db_id if we had one, but id is int
        "environmentDbId": link.environment_db_id,
        "deviceDbId": link.device.device_db_id if link.device else None,
        "deviceName": link.device.name if link.device else None,
        "studyDbId": str(link.study_id) if link.study_id else None,
        "isPrimary": link.is_primary,
        "isActive": link.is_active,
        "startDate": link.start_date.isoformat().split('T')[0] if link.start_date else None,
        "endDate": link.end_date.isoformat().split('T')[0] if link.end_date else None,
    }


# ===========================================
# BrAPI IoT Extension Endpoints
# ===========================================

@router.get("/devices", summary="Get IoT devices", response_model=BrAPIResponse)
async def get_iot_devices(
    page: int = Query(0, ge=0, description="Page number"),
    pageSize: int = Query(100, ge=1, le=1000, description="Page size"),
    deviceType: Optional[str] = Query(None, description="Filter by device type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    environmentDbId: Optional[str] = Query(None, description="Filter by environment"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get IoT device metadata for traceability and audit.
    """
    query = select(IoTDevice)
    
    conditions = []
    if deviceType:
        conditions.append(IoTDevice.device_type == deviceType)
    if status:
        conditions.append(IoTDevice.status == status)
    if environmentDbId:
        conditions.append(IoTDevice.environment_id == environmentDbId)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    count_query = select(func.count(IoTDevice.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    query = query.offset(page * pageSize).limit(pageSize)
    
    result = await db.execute(query)
    devices = result.scalars().all()
    
    return BrAPIResponse(
        metadata=Metadata(
            pagination=Pagination(
                currentPage=page,
                pageSize=pageSize,
                totalCount=total,
                totalPages=(total + pageSize - 1) // pageSize if total > 0 else 0
            )
        ),
        result={"data": [device_to_response(d) for d in devices]}
    )


@router.get("/sensors", summary="Get IoT sensors", response_model=BrAPIResponse)
async def get_iot_sensors(
    page: int = Query(0, ge=0, description="Page number"),
    pageSize: int = Query(100, ge=1, le=1000, description="Page size"),
    sensorType: Optional[str] = Query(None, description="Filter by sensor type"),
    deviceDbId: Optional[str] = Query(None, description="Filter by device"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get sensor catalog describing available sensors.
    """
    query = select(IoTSensor).options(selectinload(IoTSensor.device))
    
    conditions = []
    if sensorType:
        conditions.append(IoTSensor.sensor_type == sensorType)
    if deviceDbId:
        query = query.join(IoTDevice)
        conditions.append(IoTDevice.device_db_id == deviceDbId)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    count_query = select(func.count(IoTSensor.id))
    if deviceDbId:
        count_query = count_query.join(IoTDevice)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    query = query.offset(page * pageSize).limit(pageSize)
    
    result = await db.execute(query)
    sensors = result.scalars().all()
    
    return BrAPIResponse(
        metadata=Metadata(
            pagination=Pagination(
                currentPage=page,
                pageSize=pageSize,
                totalCount=total,
                totalPages=(total + pageSize - 1) // pageSize if total > 0 else 0
            )
        ),
        result={"data": [sensor_to_response(s) for s in sensors]}
    )


@router.get("/telemetry", summary="Get telemetry data", response_model=BrAPIResponse)
async def get_iot_telemetry(
    deviceDbId: str = Query(..., description="Device ID (required)"),
    sensorDbId: Optional[str] = Query(None, description="Sensor ID (optional)"),
    startTime: str = Query(..., description="ISO 8601 start time (required)"),
    endTime: str = Query(..., description="ISO 8601 end time (required)"),
    downsample: Optional[str] = Query(None, description="Downsample interval"),
    page: int = Query(0, ge=0, description="Page number"),
    pageSize: int = Query(1000, ge=1, le=10000, description="Page size"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get time-series telemetry data with controlled access.
    """
    try:
        start_dt = datetime.fromisoformat(startTime.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(endTime.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")
    
    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="endTime must be after startTime")
    
    if end_dt - start_dt > timedelta(days=30):
        raise HTTPException(status_code=400, detail="Time range cannot exceed 30 days")
    
    device_query = select(IoTDevice).where(IoTDevice.device_db_id == deviceDbId)
    device_result = await db.execute(device_query)
    device = device_result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    sensor_query = select(IoTSensor).where(IoTSensor.device_id == device.id)
    if sensorDbId:
        sensor_query = sensor_query.where(IoTSensor.sensor_db_id == sensorDbId)
    
    sensor_result = await db.execute(sensor_query)
    sensors = sensor_result.scalars().all()
    
    if not sensors:
        raise HTTPException(status_code=404, detail="No sensors found for device")
    
    telemetry_data = []
    
    for sensor in sensors:
        telem_query = select(IoTTelemetry).where(
            and_(
                IoTTelemetry.device_id == device.id,
                IoTTelemetry.sensor_id == sensor.id,
                IoTTelemetry.timestamp >= start_dt,
                IoTTelemetry.timestamp <= end_dt
            )
        ).order_by(IoTTelemetry.timestamp).limit(pageSize)
        
        telem_result = await db.execute(telem_query)
        readings = telem_result.scalars().all()
        
        telemetry_data.append({
            "sensorDbId": sensor.sensor_db_id,
            "deviceDbId": deviceDbId,
            "sensorType": sensor.sensor_type,
            "unit": sensor.unit,
            "readings": [
                {
                    "timestamp": r.timestamp.isoformat() + "Z",
                    "value": r.value,
                    "quality": r.quality or "good"
                }
                for r in readings
            ]
        })
    
    return BrAPIResponse(
        metadata=Metadata(
            pagination=Pagination(
                currentPage=page,
                pageSize=pageSize,
                totalCount=len(telemetry_data),
                totalPages=1
            )
        ),
        result={"data": telemetry_data}
    )


@router.get("/aggregates", summary="Get environmental aggregates", response_model=BrAPIResponse)
async def get_iot_aggregates(
    environmentDbId: str = Query(..., description="Environment ID (required)"),
    parameter: Optional[str] = Query(None, description="Filter by parameter name"),
    period: Optional[str] = Query(None, description="Filter by period"),
    startDate: Optional[str] = Query(None, description="Filter by start date"),
    endDate: Optional[str] = Query(None, description="Filter by end date"),
    page: int = Query(0, ge=0, description="Page number"),
    pageSize: int = Query(100, ge=1, le=1000, description="Page size"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get BrAPI-aligned environmental summaries.
    """
    conditions = [IoTAggregate.environment_db_id == environmentDbId]
    if parameter:
        conditions.append(IoTAggregate.parameter == parameter)
    if period:
        conditions.append(IoTAggregate.period == period)
    if startDate:
        try:
            start_dt = datetime.strptime(startDate, "%Y-%m-%d")
            conditions.append(IoTAggregate.start_time >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid startDate format")
    if endDate:
        try:
            end_dt = datetime.strptime(endDate, "%Y-%m-%d")
            conditions.append(IoTAggregate.end_time <= end_dt + timedelta(days=1))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid endDate format")
    
    query = select(IoTAggregate).where(and_(*conditions))
    
    count_query = select(func.count(IoTAggregate.id)).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    query = query.order_by(IoTAggregate.start_time.desc())
    query = query.offset(page * pageSize).limit(pageSize)
    
    result = await db.execute(query)
    aggregates = result.scalars().all()
    
    return BrAPIResponse(
        metadata=Metadata(
            pagination=Pagination(
                currentPage=page,
                pageSize=pageSize,
                totalCount=total,
                totalPages=(total + pageSize - 1) // pageSize if total > 0 else 0
            )
        ),
        result={"data": [aggregate_to_response(a) for a in aggregates]}
    )


@router.get("/alerts", summary="Get alert events", response_model=BrAPIResponse)
async def get_iot_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment"),
    deviceDbId: Optional[str] = Query(None, description="Filter by device"),
    startTime: Optional[str] = Query(None, description="Filter alerts after this time"),
    endTime: Optional[str] = Query(None, description="Filter alerts before this time"),
    page: int = Query(0, ge=0, description="Page number"),
    pageSize: int = Query(100, ge=1, le=1000, description="Page size"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get environment-driven stress or anomaly events.
    """
    query = select(IoTAlertEvent).options(
        selectinload(IoTAlertEvent.device),
        selectinload(IoTAlertEvent.sensor)
    )
    
    conditions = []
    if severity:
        conditions.append(IoTAlertEvent.severity == severity)
    if status:
        conditions.append(IoTAlertEvent.status == status)
    if acknowledged is not None:
        conditions.append(IoTAlertEvent.acknowledged == acknowledged)
    if deviceDbId:
        query = query.join(IoTDevice)
        conditions.append(IoTDevice.device_db_id == deviceDbId)
    if startTime:
        try:
            start_dt = datetime.fromisoformat(startTime.replace("Z", "+00:00"))
            conditions.append(IoTAlertEvent.start_time >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid startTime format")
    if endTime:
        try:
            end_dt = datetime.fromisoformat(endTime.replace("Z", "+00:00"))
            conditions.append(IoTAlertEvent.start_time <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid endTime format")
    
    if conditions:
        query = query.where(and_(*conditions))
    
    count_query = select(func.count(IoTAlertEvent.id))
    if deviceDbId:
        count_query = count_query.join(IoTDevice)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    query = query.order_by(IoTAlertEvent.start_time.desc())
    query = query.offset(page * pageSize).limit(pageSize)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return BrAPIResponse(
        metadata=Metadata(
            pagination=Pagination(
                currentPage=page,
                pageSize=pageSize,
                totalCount=total,
                totalPages=(total + pageSize - 1) // pageSize if total > 0 else 0
            )
        ),
        result={"data": [alert_to_response(a) for a in alerts]}
    )


@router.get("/environment-links", summary="Get environment links", response_model=BrAPIResponse)
async def get_iot_environment_links(
    environmentDbId: Optional[str] = Query(None, description="Filter by environment"),
    deviceDbId: Optional[str] = Query(None, description="Filter by device"),
    page: int = Query(0, ge=0, description="Page number"),
    pageSize: int = Query(100, ge=1, le=1000, description="Page size"),
    db: AsyncSession = Depends(get_db)
):
    """Get links between devices and environments."""
    query = select(IoTEnvironmentLink).options(selectinload(IoTEnvironmentLink.device))

    conditions = []
    if environmentDbId:
        conditions.append(IoTEnvironmentLink.environment_db_id == environmentDbId)
    if deviceDbId:
        query = query.join(IoTDevice)
        conditions.append(IoTDevice.device_db_id == deviceDbId)

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count(IoTEnvironmentLink.id))
    if deviceDbId:
        count_query = count_query.join(IoTDevice)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    query = query.offset(page * pageSize).limit(pageSize)

    result = await db.execute(query)
    links = result.scalars().all()

    return BrAPIResponse(
        metadata=Metadata(
            pagination=Pagination(
                currentPage=page,
                pageSize=pageSize,
                totalCount=total,
                totalPages=(total + pageSize - 1) // pageSize if total > 0 else 0
            )
        ),
        result={"data": [link_to_response(l) for l in links]}
    )


# ===========================================
# Reference Endpoints (Static data)
# ===========================================

@router.get("/sensor-types", summary="Get available sensor types")
async def get_sensor_types():
    """Get list of available sensor types with their units."""
    return {
        "result": {
            "data": [
                {"sensorType": "air_temperature", "unit": "C", "category": "temperature"},
                {"sensorType": "soil_temperature", "unit": "C", "category": "temperature"},
                {"sensorType": "canopy_temperature", "unit": "C", "category": "temperature"},
                {"sensorType": "water_temperature", "unit": "C", "category": "temperature"},
                {"sensorType": "relative_humidity", "unit": "%", "category": "humidity"},
                {"sensorType": "soil_moisture", "unit": "%", "category": "soil"},
                {"sensorType": "soil_ph", "unit": "pH", "category": "soil"},
                {"sensorType": "electrical_conductivity", "unit": "dS/m", "category": "soil"},
                {"sensorType": "atmospheric_pressure", "unit": "hPa", "category": "weather"},
                {"sensorType": "wind_speed", "unit": "km/h", "category": "weather"},
                {"sensorType": "rainfall", "unit": "mm", "category": "precipitation"},
                {"sensorType": "par", "unit": "umol/m2/s", "category": "radiation"},
                {"sensorType": "leaf_wetness", "unit": "%", "category": "plant"},
                {"sensorType": "water_level", "unit": "%", "category": "water"},
                {"sensorType": "flow_rate", "unit": "L/min", "category": "water"},
            ]
        }
    }


@router.get("/environmental-parameters", summary="Get environmental parameters")
async def get_environmental_parameters():
    """Get list of environmental parameters available for aggregation."""
    return {
        "result": {
            "data": [
                {"parameter": "air_temperature_mean", "unit": "C", "aggregation": "mean", "category": "temperature"},
                {"parameter": "air_temperature_max", "unit": "C", "aggregation": "max", "category": "temperature"},
                {"parameter": "air_temperature_min", "unit": "C", "aggregation": "min", "category": "temperature"},
                {"parameter": "growing_degree_days", "unit": "C-day", "aggregation": "sum", "category": "temperature"},
                {"parameter": "heat_stress_days", "unit": "days", "aggregation": "count", "category": "stress"},
                {"parameter": "frost_days", "unit": "days", "aggregation": "count", "category": "stress"},
                {"parameter": "relative_humidity_mean", "unit": "%", "aggregation": "mean", "category": "humidity"},
                {"parameter": "soil_moisture_mean", "unit": "%", "aggregation": "mean", "category": "soil"},
                {"parameter": "drought_stress_days", "unit": "days", "aggregation": "count", "category": "stress"},
                {"parameter": "precipitation_total", "unit": "mm", "aggregation": "sum", "category": "precipitation"},
                {"parameter": "precipitation_days", "unit": "days", "aggregation": "count", "category": "precipitation"},
                {"parameter": "solar_radiation_total", "unit": "MJ/m2", "aggregation": "sum", "category": "radiation"},
                {"parameter": "leaf_wetness_hours", "unit": "hours", "aggregation": "sum", "category": "plant"},
            ]
        }
    }

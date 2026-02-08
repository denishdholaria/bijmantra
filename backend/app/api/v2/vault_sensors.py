"""
Vault Sensor Integration API

Endpoints for managing environmental sensors in Seed Bank vaults.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel

from ...services.vault_sensors import vault_sensor_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user


router = APIRouter(prefix="/vault-sensors", tags=["Vault Sensors"])


# Pydantic Models
class LinkSensorRequest(BaseModel):
    vault_id: str
    vault_name: str
    vault_type: str  # base, active, cryo
    sensor_id: str
    sensors: List[str]  # temperature, humidity, door_status, etc.


class RecordReadingRequest(BaseModel):
    sensor_type: str
    value: float
    unit: str


class SetThresholdsRequest(BaseModel):
    sensor_type: str
    min_value: float
    max_value: float
    unit: str


class AcknowledgeAlertRequest(BaseModel):
    user: str


# Sensor Management Endpoints
@router.post("/link")
async def link_sensor_to_vault(
    request: LinkSensorRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Link a sensor device to a vault for monitoring."""
    sensor =  await vault_sensor_service.link_sensor_to_vault(db, current_user.organization_id, 
        vault_id=request.vault_id,
        vault_name=request.vault_name,
        vault_type=request.vault_type,
        sensor_id=request.sensor_id,
        sensors=request.sensors,
    )
    return {"success": True, "sensor": sensor}


@router.delete("/unlink/{sensor_id}")
async def unlink_sensor(
    sensor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Remove a sensor from vault monitoring."""
    success =  await vault_sensor_service.unlink_sensor(db, current_user.organization_id, sensor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return {"success": True, "message": "Sensor unlinked"}


@router.get("/sensors")
async def list_vault_sensors(
    vault_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all vault sensors or sensors for a specific vault."""
    sensors =  await vault_sensor_service.get_vault_sensors(db, current_user.organization_id, vault_id)
    return {"sensors": sensors, "count": len(sensors)}


@router.get("/sensors/{sensor_id}")
async def get_sensor(
    sensor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get sensor details by ID."""
    sensor =  await vault_sensor_service.get_sensor_by_id(db, current_user.organization_id, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor


# Readings Endpoints
@router.post("/sensors/{sensor_id}/readings")
async def record_reading(
    sensor_id: str, request: RecordReadingRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Record a new sensor reading."""
    reading =  await vault_sensor_service.record_reading(db, current_user.organization_id, 
        sensor_id=sensor_id,
        sensor_type=request.sensor_type,
        value=request.value,
        unit=request.unit,
    )
    if not reading:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return {"success": True, "reading": reading}


@router.get("/readings")
async def get_readings(
    sensor_id: Optional[str] = None,
    vault_id: Optional[str] = None,
    sensor_type: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get sensor readings with filters."""
    readings =  await vault_sensor_service.get_sensor_readings(db, current_user.organization_id, 
        sensor_id=sensor_id,
        vault_id=vault_id,
        sensor_type=sensor_type,
        hours=hours,
        limit=limit,
    )
    return {"readings": readings, "count": len(readings)}


# Vault Conditions Endpoints
@router.get("/conditions")
async def get_all_conditions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get current conditions for all vaults."""
    conditions =  await vault_sensor_service.get_all_vault_conditions(db, current_user.organization_id)
    return {"conditions": conditions, "count": len(conditions)}


@router.get("/conditions/{vault_id}")
async def get_vault_conditions(
    vault_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get current conditions for a specific vault."""
    conditions =  await vault_sensor_service.get_vault_conditions(db, current_user.organization_id, vault_id)
    if not conditions:
        raise HTTPException(status_code=404, detail="Vault not found or no sensors linked")
    return conditions


# Threshold Management
@router.get("/thresholds/{vault_id}")
async def get_thresholds(
    vault_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get thresholds for a vault."""
    thresholds =  await vault_sensor_service.get_thresholds(db, current_user.organization_id, vault_id)
    return {"vault_id": vault_id, "thresholds": thresholds}


@router.post("/thresholds/{vault_id}")
async def set_thresholds(
    vault_id: str, request: SetThresholdsRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Set custom thresholds for a vault."""
    thresholds =  await vault_sensor_service.set_thresholds(db, current_user.organization_id, 
        vault_id=vault_id,
        sensor_type=request.sensor_type,
        min_value=request.min_value,
        max_value=request.max_value,
        unit=request.unit,
    )
    return {"success": True, "vault_id": vault_id, "thresholds": thresholds}


# Alert Endpoints
@router.get("/alerts")
async def get_alerts(
    vault_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get vault sensor alerts."""
    alerts =  await vault_sensor_service.get_alerts(db, current_user.organization_id, 
        vault_id=vault_id,
        severity=severity,
        acknowledged=acknowledged,
        limit=limit,
    )
    return {"alerts": alerts, "count": len(alerts)}


@router.get("/alerts/{alert_id}")
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get alert by ID."""
    alert =  await vault_sensor_service.get_alert_by_id(db, current_user.organization_id, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str, request: AcknowledgeAlertRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Acknowledge an alert."""
    alert =  await vault_sensor_service.acknowledge_alert(db, current_user.organization_id, alert_id, request.user)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"success": True, "alert": alert}


# Statistics & Reference
@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get vault sensor statistics."""
    return await vault_sensor_service.get_statistics(db, current_user.organization_id)


@router.get("/vault-types")
async def get_vault_types(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get available vault types with default thresholds."""
    return {"vault_types": vault_sensor_service.get_vault_types()}

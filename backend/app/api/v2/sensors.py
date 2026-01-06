"""
Sensor Networks API

IoT device management, sensor data, and alerts.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from app.services.sensor_network import sensor_network_service

router = APIRouter(prefix="/sensors", tags=["Sensor Networks"])


# Request/Response Models
class DeviceCreate(BaseModel):
    device_id: str
    name: str
    device_type: str
    location: str
    sensors: List[str]
    field_id: Optional[str] = None


class DeviceStatusUpdate(BaseModel):
    status: str
    battery: Optional[int] = None
    signal: Optional[int] = None


class ReadingCreate(BaseModel):
    device_id: str
    sensor: str
    value: float
    unit: str
    timestamp: Optional[str] = None


class AlertRuleCreate(BaseModel):
    name: str
    sensor: str
    condition: str  # above, below, equals
    threshold: float
    unit: str
    severity: str = "warning"
    notify_email: bool = True
    notify_sms: bool = False
    notify_push: bool = True


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None
    notify_email: Optional[bool] = None
    notify_sms: Optional[bool] = None
    notify_push: Optional[bool] = None


# Device Endpoints
@router.post("/devices", summary="Register a new sensor device")
async def register_device(data: DeviceCreate):
    """Register a new IoT sensor device."""
    device = sensor_network_service.register_device(
        device_id=data.device_id,
        name=data.name,
        device_type=data.device_type,
        location=data.location,
        sensors=data.sensors,
        field_id=data.field_id,
    )
    return device


@router.get("/devices", summary="List all sensor devices")
async def list_devices(
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    field_id: Optional[str] = Query(None, description="Filter by field ID"),
):
    """List all registered sensor devices."""
    devices = sensor_network_service.list_devices(
        device_type=device_type,
        status=status,
        field_id=field_id,
    )
    return {"devices": devices, "total": len(devices)}


@router.get("/devices/{device_id}", summary="Get device details")
async def get_device(device_id: str):
    """Get details of a specific device."""
    device = sensor_network_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/devices/{device_id}/status", summary="Update device status")
async def update_device_status(device_id: str, data: DeviceStatusUpdate):
    """Update device status (online/offline/warning)."""
    device = sensor_network_service.update_device_status(
        device_id=device_id,
        status=data.status,
        battery=data.battery,
        signal=data.signal,
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.delete("/devices/{device_id}", summary="Remove a device")
async def delete_device(device_id: str):
    """Remove a sensor device from the network."""
    success = sensor_network_service.delete_device(device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"message": "Device removed successfully"}


# Reading Endpoints
@router.post("/readings", summary="Record a sensor reading")
async def record_reading(data: ReadingCreate):
    """Record a new sensor reading."""
    reading = sensor_network_service.record_reading(
        device_id=data.device_id,
        sensor=data.sensor,
        value=data.value,
        unit=data.unit,
        timestamp=data.timestamp,
    )
    return reading


@router.get("/readings", summary="Get sensor readings")
async def get_readings(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    sensor: Optional[str] = Query(None, description="Filter by sensor type"),
    since: Optional[str] = Query(None, description="Filter readings since timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum readings to return"),
):
    """Get sensor readings with optional filters."""
    readings = sensor_network_service.get_readings(
        device_id=device_id,
        sensor=sensor,
        since=since,
        limit=limit,
    )
    return {"readings": readings, "total": len(readings)}


@router.get("/readings/live", summary="Get live sensor readings")
async def get_live_readings():
    """Get simulated live readings from all online devices."""
    readings = sensor_network_service.generate_live_readings()
    return {"readings": readings, "timestamp": readings[0]["timestamp"] if readings else None}


@router.get("/readings/{device_id}/latest", summary="Get latest readings for a device")
async def get_latest_readings(device_id: str):
    """Get the latest reading for each sensor on a device."""
    device = sensor_network_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    latest = sensor_network_service.get_latest_readings(device_id)
    return {"device_id": device_id, "readings": latest}


# Alert Rule Endpoints
@router.post("/alerts/rules", summary="Create an alert rule")
async def create_alert_rule(data: AlertRuleCreate):
    """Create a new threshold-based alert rule."""
    rule = sensor_network_service.create_alert_rule(
        name=data.name,
        sensor=data.sensor,
        condition=data.condition,
        threshold=data.threshold,
        unit=data.unit,
        severity=data.severity,
        notify_email=data.notify_email,
        notify_sms=data.notify_sms,
        notify_push=data.notify_push,
    )
    return rule


@router.get("/alerts/rules", summary="List alert rules")
async def list_alert_rules(
    enabled_only: bool = Query(False, description="Only return enabled rules"),
):
    """List all alert rules."""
    rules = sensor_network_service.list_alert_rules(enabled_only=enabled_only)
    return {"rules": rules, "total": len(rules)}


@router.put("/alerts/rules/{rule_id}", summary="Update an alert rule")
async def update_alert_rule(rule_id: str, data: AlertRuleUpdate):
    """Update an existing alert rule."""
    updates = data.model_dump(exclude_none=True)
    rule = sensor_network_service.update_alert_rule(rule_id, updates)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule


@router.delete("/alerts/rules/{rule_id}", summary="Delete an alert rule")
async def delete_alert_rule(rule_id: str):
    """Delete an alert rule."""
    success = sensor_network_service.delete_alert_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return {"message": "Alert rule deleted successfully"}


# Alert Event Endpoints
@router.get("/alerts/events", summary="List alert events")
async def list_alert_events(
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=500, description="Maximum events to return"),
):
    """List alert events (triggered alerts)."""
    events = sensor_network_service.list_alert_events(
        acknowledged=acknowledged,
        severity=severity,
        limit=limit,
    )
    return {"events": events, "total": len(events)}


@router.post("/alerts/events/{event_id}/acknowledge", summary="Acknowledge an alert")
async def acknowledge_alert(event_id: str, user: str = Query(..., description="User acknowledging the alert")):
    """Acknowledge an alert event."""
    event = sensor_network_service.acknowledge_alert(event_id, user)
    if not event:
        raise HTTPException(status_code=404, detail="Alert event not found")
    return event


# Statistics & Reference Endpoints
@router.get("/stats", summary="Get network statistics")
async def get_network_stats():
    """Get overall sensor network statistics."""
    return sensor_network_service.get_network_stats()


@router.get("/device-types", summary="Get available device types")
async def get_device_types():
    """Get list of available device types."""
    return {"types": sensor_network_service.get_device_types()}


@router.get("/sensor-types", summary="Get available sensor types")
async def get_sensor_types():
    """Get list of available sensor types."""
    return {"types": sensor_network_service.get_sensor_types()}

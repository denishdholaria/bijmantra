"""
Sensor Network Service

IoT device management, sensor data collection, and alert handling.
Production implementation using SQLAlchemy and AsyncSession.
"""

from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func, desc
from sqlalchemy.orm import selectinload

from app.models.iot import (
    IoTDevice, IoTSensor, IoTTelemetry, IoTAlertRule, IoTAlertEvent
)
from app.models.core import Organization  # Assuming we might need this, but maybe not if we rely on input


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class SensorNetworkService:
    """Service for managing IoT sensor networks."""

    # Device Management
    async def register_device(
        self,
        db: AsyncSession,
        device_id: str,
        name: str,
        device_type: str,
        location: str,
        sensors: List[str],
        field_id: Optional[str] = None,
        organization_id: int = 1, # Default or passed context
    ) -> Dict:
        """Register a new sensor device."""

        # Check if device exists
        query = select(IoTDevice).where(IoTDevice.device_db_id == device_id)
        result = await db.execute(query)
        existing_device = result.scalar_one_or_none()

        if existing_device:
            # Update existing? Or fail? For now, let's update basic info
            existing_device.name = name
            existing_device.device_type = device_type
            existing_device.location_description = location
            # Field ID in model is integer (ForeignKey("locations.id")), but input is string?
            # If input is string, we might need to resolve it or store it in environment_id if it's a brapi ID.
            # For this implementation, I'll assume field_id maps to environment_id for now if it's a string,
            # or we need to handle the Integer FK.
            # The mock treated it as a string. The model has `field_id = Column(Integer, ForeignKey("locations.id"))`
            # AND `environment_id = Column(String(255))`.
            # I will store the string ID in environment_id.
            existing_device.environment_id = field_id

            device = existing_device
        else:
            device = IoTDevice(
                device_db_id=device_id,
                name=name,
                device_type=device_type,
                location_description=location,
                environment_id=field_id,
                organization_id=organization_id,
                status="offline",
                battery_level=100,
                signal_strength=0,
                last_seen=None,
                additional_info={"firmware": "unknown"}
            )
            db.add(device)
            await db.flush() # Get ID

        # Handle sensors
        # First, get existing sensors
        sensor_query = select(IoTSensor).where(IoTSensor.device_id == device.id)
        sensor_result = await db.execute(sensor_query)
        existing_sensors = {s.sensor_type: s for s in sensor_result.scalars().all()}

        current_sensor_types = set(sensors)

        # Add new sensors
        for sensor_type in current_sensor_types:
            if sensor_type not in existing_sensors:
                new_sensor = IoTSensor(
                    sensor_db_id=f"{device_id}-{sensor_type}-{uuid4().hex[:4]}",
                    device_id=device.id,
                    sensor_type=sensor_type,
                    name=f"{name} {sensor_type}",
                    unit=self._get_unit_for_type(sensor_type),
                    is_active=True
                )
                db.add(new_sensor)

        # We don't delete sensors that are not in the list to preserve history,
        # but we could mark them inactive if needed. For now, just add.

        await db.commit()
        await db.refresh(device)

        # Re-fetch with sensors
        query = select(IoTDevice).options(selectinload(IoTDevice.sensors)).where(IoTDevice.id == device.id)
        result = await db.execute(query)
        device = result.scalar_one()

        return self._device_to_dict(device)

    async def get_device(self, db: AsyncSession, device_id: str) -> Optional[Dict]:
        """Get device by ID."""
        query = select(IoTDevice).options(selectinload(IoTDevice.sensors)).where(IoTDevice.device_db_id == device_id)
        result = await db.execute(query)
        device = result.scalar_one_or_none()
        return self._device_to_dict(device) if device else None

    async def list_devices(
        self,
        db: AsyncSession,
        organization_id: Optional[int] = None,
        device_type: Optional[str] = None,
        status: Optional[str] = None,
        field_id: Optional[str] = None,
    ) -> List[Dict]:
        """List all devices with optional filters."""
        query = select(IoTDevice).options(selectinload(IoTDevice.sensors))

        conditions = []
        if organization_id:
            conditions.append(IoTDevice.organization_id == organization_id)
        if device_type:
            conditions.append(IoTDevice.device_type == device_type)
        if status:
            conditions.append(IoTDevice.status == status)
        if field_id:
            conditions.append(IoTDevice.environment_id == field_id)

        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        devices = result.scalars().all()

        return [self._device_to_dict(d) for d in devices]

    async def update_device_status(
        self,
        db: AsyncSession,
        device_id: str,
        status: str,
        battery: Optional[int] = None,
        signal: Optional[int] = None,
    ) -> Optional[Dict]:
        """Update device status."""
        query = select(IoTDevice).where(IoTDevice.device_db_id == device_id)
        result = await db.execute(query)
        device = result.scalar_one_or_none()

        if not device:
            return None

        device.status = status
        device.last_seen = _utcnow()

        if battery is not None:
            device.battery_level = battery
        if signal is not None:
            device.signal_strength = signal

        await db.commit()
        await db.refresh(device)
        # Need to load sensors for dict conversion
        await db.refresh(device, attribute_names=['sensors'])

        return self._device_to_dict(device)

    async def delete_device(self, db: AsyncSession, device_id: str) -> bool:
        """Remove a device."""
        query = select(IoTDevice).where(IoTDevice.device_db_id == device_id)
        result = await db.execute(query)
        device = result.scalar_one_or_none()

        if device:
            await db.delete(device)
            await db.commit()
            return True
        return False

    # Sensor Readings
    async def record_reading(
        self,
        db: AsyncSession,
        device_id: str,
        sensor: str,
        value: float,
        unit: str,
        timestamp: Optional[str] = None,
    ) -> Dict:
        """Record a sensor reading."""
        # Find device and sensor
        query = select(IoTDevice).where(IoTDevice.device_db_id == device_id)
        result = await db.execute(query)
        device = result.scalar_one_or_none()

        if not device:
            # Optionally create device on the fly? No, fail.
            raise ValueError(f"Device {device_id} not found")

        # Find sensor
        sensor_query = select(IoTSensor).where(
            and_(IoTSensor.device_id == device.id, IoTSensor.sensor_type == sensor)
        )
        sensor_result = await db.execute(sensor_query)
        iot_sensor = sensor_result.scalar_one_or_none()

        if not iot_sensor:
            # Create sensor if not exists
            iot_sensor = IoTSensor(
                sensor_db_id=f"{device_id}-{sensor}-{uuid4().hex[:4]}",
                device_id=device.id,
                sensor_type=sensor,
                name=f"{device.name} {sensor}",
                unit=unit,
                is_active=True
            )
            db.add(iot_sensor)
            await db.flush()

        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if timestamp else _utcnow()

        telemetry = IoTTelemetry(
            timestamp=ts,
            device_id=device.id,
            sensor_id=iot_sensor.id,
            value=value,
            quality="good"
        )
        db.add(telemetry)

        # Update device status
        device.last_seen = ts
        device.status = "online"

        await db.commit()
        await db.refresh(device)
        await db.refresh(iot_sensor)

        # Check alerts
        await self._check_alerts(db, device, iot_sensor, value)

        return {
            "id": str(uuid4()), # We don't have UUID on telemetry table usually, just composite key or internal int ID.
            "device_id": device_id,
            "sensor": sensor,
            "value": value,
            "unit": unit,
            "timestamp": ts.isoformat()
        }

    async def get_readings(
        self,
        db: AsyncSession,
        device_id: Optional[str] = None,
        sensor: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Get sensor readings with filters."""
        query = select(IoTTelemetry, IoTDevice, IoTSensor).join(
            IoTDevice, IoTTelemetry.device_id == IoTDevice.id
        ).join(
            IoTSensor, IoTTelemetry.sensor_id == IoTSensor.id
        )

        conditions = []
        if device_id:
            conditions.append(IoTDevice.device_db_id == device_id)
        if sensor:
            conditions.append(IoTSensor.sensor_type == sensor)
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                conditions.append(IoTTelemetry.timestamp >= since_dt)
            except ValueError:
                pass

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(IoTTelemetry.timestamp)).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        readings = []
        for telem, dev, sens in rows:
            readings.append({
                "id": str(telem.timestamp.timestamp()), # Fake ID
                "device_id": dev.device_db_id,
                "device_name": dev.name,
                "sensor": sens.sensor_type,
                "value": telem.value,
                "unit": sens.unit,
                "timestamp": telem.timestamp.isoformat(),
            })

        return readings

    async def get_latest_readings(self, db: AsyncSession, device_id: str) -> Dict[str, Dict]:
        """Get latest reading for each sensor on a device."""
        query = select(IoTDevice).where(IoTDevice.device_db_id == device_id)
        result = await db.execute(query)
        device = result.scalar_one_or_none()

        if not device:
            return {}

        # This is a bit complex in SQL to get "latest per group".
        # Easiest is to query per sensor or use a window function.
        # Given limited sensors per device, query per sensor is okay, or just fetch recent telemetry for device and filter in python (if not too many).
        # Let's try to get all sensors for device, then latest telemetry for each.

        sensor_query = select(IoTSensor).where(IoTSensor.device_id == device.id)
        sensor_result = await db.execute(sensor_query)
        sensors = sensor_result.scalars().all()

        latest = {}
        for s in sensors:
            t_query = select(IoTTelemetry).where(
                and_(IoTTelemetry.device_id == device.id, IoTTelemetry.sensor_id == s.id)
            ).order_by(desc(IoTTelemetry.timestamp)).limit(1)
            t_result = await db.execute(t_query)
            t = t_result.scalar_one_or_none()

            if t:
                latest[s.sensor_type] = {
                    "id": str(t.timestamp.timestamp()),
                    "device_id": device_id,
                    "sensor": s.sensor_type,
                    "value": t.value,
                    "unit": s.unit,
                    "timestamp": t.timestamp.isoformat()
                }

        return latest

    async def generate_live_readings(self, db: AsyncSession) -> List[Dict]:
        """Get latest readings from all online devices (simulated 'live' view)."""
        # In a real app, this might be the last reading for every online device.
        query = select(IoTDevice).where(IoTDevice.status == "online")
        result = await db.execute(query)
        devices = result.scalars().all()

        readings = []
        for device in devices:
            latest_map = await self.get_latest_readings(db, device.device_db_id)
            for sensor_type, reading in latest_map.items():
                readings.append({
                    "id": reading["id"],
                    "device_id": device.device_db_id,
                    "device_name": device.name,
                    "sensor": sensor_type,
                    "value": reading["value"],
                    "unit": reading["unit"],
                    "timestamp": reading["timestamp"],
                    "trend": "stable" # Hard to calc without history
                })

        # Sort by timestamp desc
        readings.sort(key=lambda x: x["timestamp"], reverse=True)
        return readings

    # Alert Management
    async def create_alert_rule(
        self,
        db: AsyncSession,
        name: str,
        sensor: str,
        condition: str,
        threshold: float,
        unit: str,
        severity: str = "warning",
        notify_email: bool = True,
        notify_sms: bool = False,
        notify_push: bool = True,
        organization_id: int = 1,
    ) -> Dict:
        """Create a new alert rule."""
        rule_db_id = f"rule-{uuid4().hex[:8]}"
        rule = IoTAlertRule(
            rule_db_id=rule_db_id,
            name=name,
            sensor_type=sensor,
            condition=condition,
            threshold=threshold,
            threshold_unit=unit,
            severity=severity,
            enabled=True,
            notify_email=notify_email,
            notify_sms=notify_sms,
            notify_push=notify_push,
            organization_id=organization_id
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        return self._rule_to_dict(rule)

    async def list_alert_rules(self, db: AsyncSession, organization_id: Optional[int] = None, enabled_only: bool = False) -> List[Dict]:
        """List all alert rules."""
        query = select(IoTAlertRule)

        conditions = []
        if organization_id:
            conditions.append(IoTAlertRule.organization_id == organization_id)
        if enabled_only:
            conditions.append(IoTAlertRule.enabled == True)

        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        rules = result.scalars().all()
        return [self._rule_to_dict(r) for r in rules]

    async def update_alert_rule(self, db: AsyncSession, rule_id: str, updates: Dict) -> Optional[Dict]:
        """Update an alert rule."""
        query = select(IoTAlertRule).where(IoTAlertRule.rule_db_id == rule_id)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()

        if not rule:
            return None

        if "name" in updates: rule.name = updates["name"]
        if "enabled" in updates: rule.enabled = updates["enabled"]
        if "threshold" in updates: rule.threshold = updates["threshold"]
        if "severity" in updates: rule.severity = updates["severity"]
        if "notify_email" in updates: rule.notify_email = updates["notify_email"]
        if "notify_sms" in updates: rule.notify_sms = updates["notify_sms"]
        if "notify_push" in updates: rule.notify_push = updates["notify_push"]

        await db.commit()
        await db.refresh(rule)
        return self._rule_to_dict(rule)

    async def delete_alert_rule(self, db: AsyncSession, rule_id: str) -> bool:
        """Delete an alert rule."""
        query = select(IoTAlertRule).where(IoTAlertRule.rule_db_id == rule_id)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()

        if rule:
            await db.delete(rule)
            await db.commit()
            return True
        return False

    async def _check_alerts(self, db: AsyncSession, device: IoTDevice, sensor: IoTSensor, value: float):
        """Check if a reading triggers any alerts."""
        # Find rules that match this sensor type
        # In a real system, we'd also check device_id specificity if supported
        query = select(IoTAlertRule).where(
            and_(
                IoTAlertRule.sensor_type == sensor.sensor_type,
                IoTAlertRule.enabled == True
            )
        )
        result = await db.execute(query)
        rules = result.scalars().all()

        for rule in rules:
            # Check device specific rule? (Model has device_id optional)
            if rule.device_id and rule.device_id != device.id:
                continue

            triggered = False
            if rule.condition == "above" and value > rule.threshold:
                triggered = True
            elif rule.condition == "below" and value < rule.threshold:
                triggered = True
            elif rule.condition == "equals" and abs(value - rule.threshold) < 0.01:
                triggered = True

            if triggered:
                await self._create_alert_event(db, rule, device, sensor, value)

    async def _create_alert_event(self, db: AsyncSession, rule: IoTAlertRule, device: IoTDevice, sensor: IoTSensor, value: float):
        """Create an alert event."""
        # Check if there is already an active alert for this rule/device/sensor to avoid spam
        # For simplicity, just create new one

        event = IoTAlertEvent(
            event_db_id=f"event-{uuid4().hex[:8]}",
            rule_id=rule.id,
            device_id=device.id,
            sensor_id=sensor.id,
            alert_type="threshold",
            severity=rule.severity,
            message=f"Sensor {sensor.name} value {value} is {rule.condition} {rule.threshold}",
            trigger_value=value,
            trigger_threshold=rule.threshold,
            trigger_condition=rule.condition,
            start_time=_utcnow(),
            status="active",
            acknowledged=False
        )
        db.add(event)
        await db.commit()

    async def list_alert_events(
        self,
        db: AsyncSession,
        acknowledged: Optional[bool] = None,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """List alert events."""
        query = select(IoTAlertEvent).options(
            selectinload(IoTAlertEvent.rule),
            selectinload(IoTAlertEvent.device),
            selectinload(IoTAlertEvent.sensor)
        )

        conditions = []
        if acknowledged is not None:
            conditions.append(IoTAlertEvent.acknowledged == acknowledged)
        if severity:
            conditions.append(IoTAlertEvent.severity == severity)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(IoTAlertEvent.start_time)).limit(limit)

        result = await db.execute(query)
        events = result.scalars().all()

        return [self._event_to_dict(e) for e in events]

    async def acknowledge_alert(self, db: AsyncSession, event_id: str, user: str) -> Optional[Dict]:
        """Acknowledge an alert event."""
        query = select(IoTAlertEvent).where(IoTAlertEvent.event_db_id == event_id)
        result = await db.execute(query)
        event = result.scalar_one_or_none()

        if not event:
            return None

        event.acknowledged = True
        event.acknowledged_by = user
        event.acknowledged_at = _utcnow()
        event.status = "acknowledged"

        await db.commit()
        await db.refresh(event)
        # Load relations for dict
        await db.refresh(event, attribute_names=['rule', 'device', 'sensor'])

        return self._event_to_dict(event)

    # Statistics
    async def get_network_stats(self, db: AsyncSession, organization_id: Optional[int] = None) -> Dict:
        """Get overall network statistics."""
        # Helper to apply org filter
        def filter_org(query):
            if organization_id:
                return query.where(IoTDevice.organization_id == organization_id)
            return query

        # Total devices
        device_count = await db.scalar(filter_org(select(func.count(IoTDevice.id))))

        # By Status
        online_count = await db.scalar(filter_org(select(func.count(IoTDevice.id)).where(IoTDevice.status == 'online')))
        offline_count = await db.scalar(filter_org(select(func.count(IoTDevice.id)).where(IoTDevice.status == 'offline')))
        warning_count = await db.scalar(filter_org(select(func.count(IoTDevice.id)).where(IoTDevice.status == 'warning')))

        # Active Alerts (Need join for organization if checking rules, but alert events have devices/rules)
        # Assuming alert rules belong to organization.
        alert_query = select(func.count(IoTAlertEvent.id)).join(IoTAlertRule).where(IoTAlertEvent.acknowledged == False)
        if organization_id:
            alert_query = alert_query.where(IoTAlertRule.organization_id == organization_id)
        active_alerts = await db.scalar(alert_query)

        # Total Readings (approx) - Need join with devices
        reading_query = select(func.count(IoTTelemetry.timestamp)).join(IoTDevice)
        if organization_id:
            reading_query = reading_query.where(IoTDevice.organization_id == organization_id)
        total_readings = await db.scalar(reading_query)

        return {
            "total_devices": device_count,
            "online": online_count,
            "offline": offline_count,
            "warning": warning_count,
            "active_alerts": active_alerts,
            "total_readings": total_readings,
            # "by_type" could be added via group_by if needed
        }

    # Reference Data
    def get_device_types(self) -> List[Dict]:
        """Get available device types."""
        return [
            {"value": "weather", "label": "Weather Station", "icon": "🌤️"},
            {"value": "soil", "label": "Soil Sensor", "icon": "🌱"},
            {"value": "plant", "label": "Plant Sensor", "icon": "🌿"},
            {"value": "water", "label": "Water Sensor", "icon": "💧"},
            {"value": "gateway", "label": "Gateway", "icon": "📡"},
        ]

    def get_sensor_types(self) -> List[Dict]:
        """Get available sensor types."""
        return [
            {"value": "temperature", "label": "Temperature", "unit": "°C"},
            {"value": "humidity", "label": "Humidity", "unit": "%"},
            {"value": "pressure", "label": "Pressure", "unit": "hPa"},
            {"value": "wind_speed", "label": "Wind Speed", "unit": "km/h"},
            {"value": "soil_moisture", "label": "Soil Moisture", "unit": "%"},
            {"value": "soil_temp", "label": "Soil Temperature", "unit": "°C"},
            {"value": "ec", "label": "Electrical Conductivity", "unit": "dS/m"},
            {"value": "ph", "label": "pH Level", "unit": ""},
            {"value": "leaf_wetness", "label": "Leaf Wetness", "unit": "%"},
            {"value": "par", "label": "PAR (Light)", "unit": "µmol/m²/s"},
            {"value": "water_level", "label": "Water Level", "unit": "%"},
            {"value": "flow_rate", "label": "Flow Rate", "unit": "L/min"},
        ]

    # Helpers
    def _device_to_dict(self, device: IoTDevice) -> Dict:
        return {
            "id": device.device_db_id,
            "name": device.name,
            "type": device.device_type,
            "status": device.status,
            "battery": device.battery_level,
            "signal": device.signal_strength,
            "location": device.location_description,
            "field_id": device.environment_id, # Mapping environment_id back to field_id for frontend
            "firmware": device.additional_info.get("firmware") if device.additional_info else None,
            "sensors": [s.sensor_type for s in device.sensors] if device.sensors else [],
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "registered_at": device.installation_date.isoformat() if device.installation_date else None,
        }

    def _rule_to_dict(self, rule: IoTAlertRule) -> Dict:
        return {
            "id": rule.rule_db_id,
            "name": rule.name,
            "sensor": rule.sensor_type,
            "condition": rule.condition,
            "threshold": rule.threshold,
            "unit": rule.threshold_unit,
            "severity": rule.severity,
            "enabled": rule.enabled,
            "notify_email": rule.notify_email,
            "notify_sms": rule.notify_sms,
            "notify_push": rule.notify_push,
            "created_at": None, # We don't have created_at in model, maybe additional_info?
        }

    def _event_to_dict(self, event: IoTAlertEvent) -> Dict:
        return {
            "id": event.event_db_id,
            "rule_id": event.rule.rule_db_id if event.rule else None,
            "rule_name": event.rule.name if event.rule else "Unknown Rule",
            "device_id": event.device.device_db_id if event.device else None,
            "device_name": event.device.name if event.device else "Unknown Device",
            "sensor": event.sensor.sensor_type if event.sensor else None,
            "value": event.trigger_value,
            "threshold": event.trigger_threshold,
            "condition": event.trigger_condition,
            "message": event.message,
            "severity": event.severity,
            "timestamp": event.start_time.isoformat() if event.start_time else None,
            "acknowledged": event.acknowledged,
            "acknowledged_by": event.acknowledged_by,
            "acknowledged_at": event.acknowledged_at.isoformat() if event.acknowledged_at else None,
        }

    def _get_unit_for_type(self, sensor_type: str) -> str:
        types = self.get_sensor_types()
        for t in types:
            if t["value"] == sensor_type:
                return t["unit"]
        return ""


# Global service instance
sensor_network_service = SensorNetworkService()

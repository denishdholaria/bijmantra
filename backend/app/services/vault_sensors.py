"""
Vault Sensor Integration Service

Links IoT sensors to Seed Bank vaults for environmental monitoring.
Tracks temperature, humidity, and other conditions critical for seed preservation.

Converted to use real database queries per Zero Mock Data Policy.
Uses IoTDevice, IoTSensor, IoTTelemetry, IoTAlertEvent models.
"""

from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.iot import IoTDevice, IoTSensor, IoTTelemetry, IoTAlertEvent, IoTAlertRule


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class VaultSensorService:
    """
    Service for managing vault environmental sensors.
    
    Uses IoT models for database-backed storage:
    - IoTDevice: Vault sensor devices (device_type='vault')
    - IoTSensor: Individual measurement sensors
    - IoTTelemetry: Time-series readings
    - IoTAlertEvent: Alert instances
    """
    
    # Default thresholds for different vault types
    DEFAULT_THRESHOLDS = {
        "base": {
            "temperature": {"min": -20, "max": -15, "unit": "°C"},
            "humidity": {"min": 3, "max": 7, "unit": "%"},
        },
        "active": {
            "temperature": {"min": 2, "max": 8, "unit": "°C"},
            "humidity": {"min": 20, "max": 40, "unit": "%"},
        },
        "cryo": {
            "temperature": {"min": -200, "max": -180, "unit": "°C"},
            "humidity": {"min": 0, "max": 5, "unit": "%"},
        },
    }
    
    # Vault-Sensor Linking
    async def link_sensor_to_vault(
        self,
        db: AsyncSession,
        organization_id: int,
        vault_id: str,
        vault_name: str,
        vault_type: str,
        sensor_id: str,
        sensors: List[str],
    ) -> Dict:
        """
        Link a sensor device to a vault.
        
        Creates an IoTDevice with device_type='vault' and associated IoTSensors.
        """
        device_db_id = f"vault-{sensor_id}"
        
        # Create IoTDevice for the vault sensor
        device = IoTDevice(
            device_db_id=device_db_id,
            name=vault_name,
            description=f"Vault sensor for {vault_name}",
            device_type="vault",
            status="online",
            battery_level=100,
            signal_strength=100,
            organization_id=organization_id,
            additional_info={
                "vault_id": vault_id,
                "vault_type": vault_type,
                "sensor_id": sensor_id,
                "installed_date": _utcnow().strftime("%Y-%m-%d"),
                "alerts_enabled": True,
            }
        )
        db.add(device)
        await db.flush()
        
        # Create IoTSensor for each sensor type
        for sensor_type in sensors:
            thresholds = self.DEFAULT_THRESHOLDS.get(vault_type, self.DEFAULT_THRESHOLDS["active"])
            sensor_config = thresholds.get(sensor_type, {"unit": ""})
            
            iot_sensor = IoTSensor(
                sensor_db_id=f"{device_db_id}-{sensor_type}",
                device_id=device.id,
                sensor_type=sensor_type,
                name=f"{sensor_type.title()} Sensor",
                unit=sensor_config.get("unit", ""),
                min_value=sensor_config.get("min"),
                max_value=sensor_config.get("max"),
                is_active=True,
            )
            db.add(iot_sensor)
        
        await db.commit()
        await db.refresh(device)
        
        return self._device_to_dict(device)
    
    async def unlink_sensor(
        self,
        db: AsyncSession,
        organization_id: int,
        sensor_id: str,
    ) -> bool:
        """Remove sensor from vault."""
        stmt = select(IoTDevice).where(
            and_(
                IoTDevice.organization_id == organization_id,
                IoTDevice.device_type == "vault",
                IoTDevice.device_db_id.like(f"vault-{sensor_id}%")
            )
        )
        result = await db.execute(stmt)
        device = result.scalar_one_or_none()
        
        if device:
            await db.delete(device)
            await db.commit()
            return True
        return False
    
    async def get_vault_sensors(
        self,
        db: AsyncSession,
        organization_id: int,
        vault_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get all vault sensors or sensors for a specific vault."""
        stmt = select(IoTDevice).options(
            selectinload(IoTDevice.sensors)
        ).where(
            and_(
                IoTDevice.organization_id == organization_id,
                IoTDevice.device_type == "vault"
            )
        )
        
        if vault_id:
            stmt = stmt.where(
                IoTDevice.additional_info["vault_id"].astext == vault_id
            )
        
        result = await db.execute(stmt)
        devices = result.scalars().all()
        
        return [self._device_to_dict(d) for d in devices]
    
    async def get_sensor_by_id(
        self,
        db: AsyncSession,
        organization_id: int,
        sensor_id: str,
    ) -> Optional[Dict]:
        """Get sensor by its ID."""
        stmt = select(IoTDevice).options(
            selectinload(IoTDevice.sensors)
        ).where(
            and_(
                IoTDevice.organization_id == organization_id,
                IoTDevice.id == int(sensor_id) if sensor_id.isdigit() else IoTDevice.device_db_id == sensor_id
            )
        )
        result = await db.execute(stmt)
        device = result.scalar_one_or_none()
        
        return self._device_to_dict(device) if device else None
    
    # Readings
    async def record_reading(
        self,
        db: AsyncSession,
        organization_id: int,
        sensor_id: str,
        sensor_type: str,
        value: float,
        unit: str,
    ) -> Optional[Dict]:
        """Record a new sensor reading."""
        # Find the device
        stmt = select(IoTDevice).options(
            selectinload(IoTDevice.sensors)
        ).where(
            and_(
                IoTDevice.organization_id == organization_id,
                or_(
                    IoTDevice.id == int(sensor_id) if sensor_id.isdigit() else False,
                    IoTDevice.device_db_id == sensor_id
                )
            )
        )
        result = await db.execute(stmt)
        device = result.scalar_one_or_none()
        
        if not device:
            return None
        
        # Find the specific sensor
        iot_sensor = next(
            (s for s in device.sensors if s.sensor_type == sensor_type),
            None
        )
        
        if not iot_sensor:
            return None
        
        # Create telemetry record
        telemetry = IoTTelemetry(
            timestamp=_utcnow(),
            device_id=device.id,
            sensor_id=iot_sensor.id,
            value=value,
            raw_value=value,
            quality="good",
        )
        db.add(telemetry)
        
        # Update device last_seen
        device.last_seen = _utcnow()
        device.status = "online"
        
        await db.commit()
        
        # Check thresholds and create alerts if needed
        await self._check_thresholds(db, organization_id, device, iot_sensor, value)
        
        return {
            "id": str(telemetry.id),
            "sensor_id": str(device.id),
            "vault_id": device.additional_info.get("vault_id") if device.additional_info else None,
            "sensor_type": sensor_type,
            "value": value,
            "unit": unit,
            "timestamp": telemetry.timestamp.isoformat(),
        }
    
    async def get_sensor_readings(
        self,
        db: AsyncSession,
        organization_id: int,
        sensor_id: Optional[str] = None,
        vault_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        hours: int = 24,
        limit: int = 500,
    ) -> List[Dict]:
        """Get sensor readings with filters."""
        cutoff = _utcnow() - timedelta(hours=hours)
        
        # Build query joining telemetry with devices
        stmt = (
            select(IoTTelemetry, IoTDevice, IoTSensor)
            .join(IoTDevice, IoTTelemetry.device_id == IoTDevice.id)
            .join(IoTSensor, IoTTelemetry.sensor_id == IoTSensor.id)
            .where(
                and_(
                    IoTDevice.organization_id == organization_id,
                    IoTDevice.device_type == "vault",
                    IoTTelemetry.timestamp >= cutoff
                )
            )
        )
        
        if sensor_id:
            if sensor_id.isdigit():
                stmt = stmt.where(IoTDevice.id == int(sensor_id))
            else:
                stmt = stmt.where(IoTDevice.device_db_id == sensor_id)
        
        if vault_id:
            stmt = stmt.where(
                IoTDevice.additional_info["vault_id"].astext == vault_id
            )
        
        if sensor_type:
            stmt = stmt.where(IoTSensor.sensor_type == sensor_type)
        
        stmt = stmt.order_by(IoTTelemetry.timestamp.desc()).limit(limit)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        return [
            {
                "id": str(telemetry.id),
                "sensor_id": str(device.id),
                "vault_id": device.additional_info.get("vault_id") if device.additional_info else None,
                "sensor_type": sensor.sensor_type,
                "value": telemetry.value,
                "unit": sensor.unit,
                "timestamp": telemetry.timestamp.isoformat(),
            }
            for telemetry, device, sensor in rows
        ]
    
    async def get_vault_conditions(
        self,
        db: AsyncSession,
        organization_id: int,
        vault_id: str,
    ) -> Optional[Dict]:
        """Get current conditions for a vault."""
        stmt = select(IoTDevice).options(
            selectinload(IoTDevice.sensors)
        ).where(
            and_(
                IoTDevice.organization_id == organization_id,
                IoTDevice.device_type == "vault",
                IoTDevice.additional_info["vault_id"].astext == vault_id
            )
        )
        result = await db.execute(stmt)
        device = result.scalar_one_or_none()
        
        if not device:
            return None
        
        vault_type = device.additional_info.get("vault_type", "active") if device.additional_info else "active"
        thresholds = self.DEFAULT_THRESHOLDS.get(vault_type, self.DEFAULT_THRESHOLDS["active"])
        
        # Get latest readings for each sensor
        current_readings = {}
        for sensor in device.sensors:
            stmt = (
                select(IoTTelemetry)
                .where(IoTTelemetry.sensor_id == sensor.id)
                .order_by(IoTTelemetry.timestamp.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            latest = result.scalar_one_or_none()
            if latest:
                current_readings[sensor.sensor_type] = latest.value
        
        # Count unacknowledged alerts
        alert_stmt = select(func.count(IoTAlertEvent.id)).where(
            and_(
                IoTAlertEvent.device_id == device.id,
                IoTAlertEvent.acknowledged == False
            )
        )
        alert_result = await db.execute(alert_stmt)
        alerts_count = alert_result.scalar() or 0
        
        # Determine status based on readings
        status = "normal"
        for sensor_type, value in current_readings.items():
            if sensor_type in thresholds:
                thresh = thresholds[sensor_type]
                if value < thresh["min"] or value > thresh["max"]:
                    status = "critical"
                    break
                elif value < thresh["min"] * 1.1 or value > thresh["max"] * 0.9:
                    status = "warning"
        
        return {
            "vault_id": vault_id,
            "vault_name": device.name,
            "vault_type": vault_type,
            "sensor_status": device.status,
            "last_reading": device.last_seen.isoformat() if device.last_seen else None,
            "current_readings": current_readings,
            "thresholds": thresholds,
            "status": status,
            "alerts_count": alerts_count,
        }
    
    async def get_all_vault_conditions(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> List[Dict]:
        """Get conditions for all vaults."""
        stmt = select(IoTDevice).where(
            and_(
                IoTDevice.organization_id == organization_id,
                IoTDevice.device_type == "vault"
            )
        )
        result = await db.execute(stmt)
        devices = result.scalars().all()
        
        conditions = []
        for device in devices:
            vault_id = device.additional_info.get("vault_id") if device.additional_info else None
            if vault_id:
                condition = await self.get_vault_conditions(db, organization_id, vault_id)
                if condition:
                    conditions.append(condition)
        
        return conditions
    
    # Threshold Management
    async def _check_thresholds(
        self,
        db: AsyncSession,
        organization_id: int,
        device: IoTDevice,
        sensor: IoTSensor,
        value: float,
    ):
        """Check if reading exceeds thresholds and create alert if needed."""
        vault_type = device.additional_info.get("vault_type", "active") if device.additional_info else "active"
        thresholds = self.DEFAULT_THRESHOLDS.get(vault_type, self.DEFAULT_THRESHOLDS["active"])
        
        if sensor.sensor_type not in thresholds:
            return
        
        thresh = thresholds[sensor.sensor_type]
        
        # Check critical thresholds
        if value < thresh["min"]:
            await self._create_alert(
                db, device, sensor, value, thresh["min"],
                "below_threshold", "critical",
                f"{sensor.sensor_type.title()} below minimum threshold"
            )
        elif value > thresh["max"]:
            await self._create_alert(
                db, device, sensor, value, thresh["max"],
                "above_threshold", "critical",
                f"{sensor.sensor_type.title()} above maximum threshold"
            )
        # Check warning thresholds (within 10% of limits)
        elif value < thresh["min"] * 1.1:
            await self._create_alert(
                db, device, sensor, value, thresh["min"],
                "approaching_min", "warning",
                f"{sensor.sensor_type.title()} approaching minimum threshold"
            )
        elif value > thresh["max"] * 0.9:
            await self._create_alert(
                db, device, sensor, value, thresh["max"],
                "approaching_max", "warning",
                f"{sensor.sensor_type.title()} approaching maximum threshold"
            )
    
    async def _create_alert(
        self,
        db: AsyncSession,
        device: IoTDevice,
        sensor: IoTSensor,
        value: float,
        threshold: float,
        condition: str,
        severity: str,
        message: str,
    ):
        """Create a new alert event."""
        alert = IoTAlertEvent(
            event_db_id=f"alert-{uuid4()}",
            device_id=device.id,
            sensor_id=sensor.id,
            alert_type="threshold",
            severity=severity,
            message=message,
            trigger_value=value,
            trigger_threshold=threshold,
            trigger_condition=condition,
            start_time=_utcnow(),
            status="active",
            acknowledged=False,
        )
        db.add(alert)
        await db.commit()
    
    async def set_thresholds(
        self,
        db: AsyncSession,
        organization_id: int,
        vault_id: str,
        sensor_type: str,
        min_value: float,
        max_value: float,
        unit: str,
    ) -> Dict:
        """Set custom thresholds for a vault sensor."""
        # Find the device and sensor
        stmt = select(IoTDevice).options(
            selectinload(IoTDevice.sensors)
        ).where(
            and_(
                IoTDevice.organization_id == organization_id,
                IoTDevice.device_type == "vault",
                IoTDevice.additional_info["vault_id"].astext == vault_id
            )
        )
        result = await db.execute(stmt)
        device = result.scalar_one_or_none()
        
        if not device:
            return {}
        
        # Update sensor min/max values
        for sensor in device.sensors:
            if sensor.sensor_type == sensor_type:
                sensor.min_value = min_value
                sensor.max_value = max_value
                sensor.unit = unit
                break
        
        await db.commit()
        
        return {
            sensor_type: {
                "min": min_value,
                "max": max_value,
                "unit": unit,
            }
        }
    
    async def get_thresholds(
        self,
        db: AsyncSession,
        organization_id: int,
        vault_id: str,
    ) -> Dict:
        """Get thresholds for a vault."""
        stmt = select(IoTDevice).options(
            selectinload(IoTDevice.sensors)
        ).where(
            and_(
                IoTDevice.organization_id == organization_id,
                IoTDevice.device_type == "vault",
                IoTDevice.additional_info["vault_id"].astext == vault_id
            )
        )
        result = await db.execute(stmt)
        device = result.scalar_one_or_none()
        
        if not device:
            vault_type = "active"  # Default
        else:
            vault_type = device.additional_info.get("vault_type", "active") if device.additional_info else "active"
        
        # Return sensor-specific thresholds if set, otherwise defaults
        thresholds = {}
        if device:
            for sensor in device.sensors:
                if sensor.min_value is not None and sensor.max_value is not None:
                    thresholds[sensor.sensor_type] = {
                        "min": sensor.min_value,
                        "max": sensor.max_value,
                        "unit": sensor.unit,
                    }
        
        # Fill in defaults for missing sensor types
        defaults = self.DEFAULT_THRESHOLDS.get(vault_type, self.DEFAULT_THRESHOLDS["active"])
        for sensor_type, default_thresh in defaults.items():
            if sensor_type not in thresholds:
                thresholds[sensor_type] = default_thresh
        
        return thresholds
    
    # Alert Management
    async def get_alerts(
        self,
        db: AsyncSession,
        organization_id: int,
        vault_id: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Get alerts with filters."""
        stmt = (
            select(IoTAlertEvent, IoTDevice, IoTSensor)
            .join(IoTDevice, IoTAlertEvent.device_id == IoTDevice.id)
            .outerjoin(IoTSensor, IoTAlertEvent.sensor_id == IoTSensor.id)
            .where(
                and_(
                    IoTDevice.organization_id == organization_id,
                    IoTDevice.device_type == "vault"
                )
            )
        )
        
        if vault_id:
            stmt = stmt.where(
                IoTDevice.additional_info["vault_id"].astext == vault_id
            )
        
        if severity:
            stmt = stmt.where(IoTAlertEvent.severity == severity)
        
        if acknowledged is not None:
            stmt = stmt.where(IoTAlertEvent.acknowledged == acknowledged)
        
        stmt = stmt.order_by(IoTAlertEvent.start_time.desc()).limit(limit)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        return [
            {
                "id": str(alert.id),
                "event_db_id": alert.event_db_id,
                "vault_id": device.additional_info.get("vault_id") if device.additional_info else None,
                "vault_name": device.name,
                "sensor_type": sensor.sensor_type if sensor else None,
                "severity": alert.severity,
                "message": alert.message,
                "value": alert.trigger_value,
                "threshold": alert.trigger_threshold,
                "condition": alert.trigger_condition,
                "timestamp": alert.start_time.isoformat(),
                "acknowledged": alert.acknowledged,
                "acknowledged_by": alert.acknowledged_by,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            }
            for alert, device, sensor in rows
        ]
    
    async def acknowledge_alert(
        self,
        db: AsyncSession,
        organization_id: int,
        alert_id: str,
        user: str,
    ) -> Optional[Dict]:
        """Acknowledge an alert."""
        stmt = (
            select(IoTAlertEvent)
            .join(IoTDevice, IoTAlertEvent.device_id == IoTDevice.id)
            .where(
                and_(
                    IoTDevice.organization_id == organization_id,
                    or_(
                        IoTAlertEvent.id == int(alert_id) if alert_id.isdigit() else False,
                        IoTAlertEvent.event_db_id == alert_id
                    )
                )
            )
        )
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()
        
        if not alert:
            return None
        
        alert.acknowledged = True
        alert.acknowledged_by = user
        alert.acknowledged_at = _utcnow()
        alert.status = "acknowledged"
        
        await db.commit()
        
        return {
            "id": str(alert.id),
            "acknowledged": True,
            "acknowledged_by": user,
            "acknowledged_at": alert.acknowledged_at.isoformat(),
        }
    
    async def get_alert_by_id(
        self,
        db: AsyncSession,
        organization_id: int,
        alert_id: str,
    ) -> Optional[Dict]:
        """Get alert by ID."""
        stmt = (
            select(IoTAlertEvent, IoTDevice, IoTSensor)
            .join(IoTDevice, IoTAlertEvent.device_id == IoTDevice.id)
            .outerjoin(IoTSensor, IoTAlertEvent.sensor_id == IoTSensor.id)
            .where(
                and_(
                    IoTDevice.organization_id == organization_id,
                    or_(
                        IoTAlertEvent.id == int(alert_id) if alert_id.isdigit() else False,
                        IoTAlertEvent.event_db_id == alert_id
                    )
                )
            )
        )
        result = await db.execute(stmt)
        row = result.one_or_none()
        
        if not row:
            return None
        
        alert, device, sensor = row
        return {
            "id": str(alert.id),
            "event_db_id": alert.event_db_id,
            "vault_id": device.additional_info.get("vault_id") if device.additional_info else None,
            "vault_name": device.name,
            "sensor_type": sensor.sensor_type if sensor else None,
            "severity": alert.severity,
            "message": alert.message,
            "value": alert.trigger_value,
            "threshold": alert.trigger_threshold,
            "condition": alert.trigger_condition,
            "timestamp": alert.start_time.isoformat(),
            "acknowledged": alert.acknowledged,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        }
    
    # Statistics
    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict:
        """Get vault sensor statistics."""
        # Count devices by status
        stmt = select(IoTDevice).where(
            and_(
                IoTDevice.organization_id == organization_id,
                IoTDevice.device_type == "vault"
            )
        )
        result = await db.execute(stmt)
        devices = result.scalars().all()
        
        online = sum(1 for d in devices if d.status == "online")
        warning = sum(1 for d in devices if d.status == "warning")
        offline = sum(1 for d in devices if d.status == "offline")
        
        # Count by vault type
        by_vault_type = {"base": 0, "active": 0, "cryo": 0}
        for d in devices:
            vault_type = d.additional_info.get("vault_type") if d.additional_info else None
            if vault_type in by_vault_type:
                by_vault_type[vault_type] += 1
        
        # Count readings in last 24h
        cutoff = _utcnow() - timedelta(hours=24)
        device_ids = [d.id for d in devices]
        
        if device_ids:
            readings_stmt = select(func.count(IoTTelemetry.id)).where(
                and_(
                    IoTTelemetry.device_id.in_(device_ids),
                    IoTTelemetry.timestamp >= cutoff
                )
            )
            readings_result = await db.execute(readings_stmt)
            total_readings = readings_result.scalar() or 0
        else:
            total_readings = 0
        
        # Count active alerts
        if device_ids:
            alerts_stmt = select(func.count(IoTAlertEvent.id)).where(
                and_(
                    IoTAlertEvent.device_id.in_(device_ids),
                    IoTAlertEvent.acknowledged == False
                )
            )
            alerts_result = await db.execute(alerts_stmt)
            active_alerts = alerts_result.scalar() or 0
            
            critical_stmt = select(func.count(IoTAlertEvent.id)).where(
                and_(
                    IoTAlertEvent.device_id.in_(device_ids),
                    IoTAlertEvent.severity == "critical",
                    IoTAlertEvent.acknowledged == False
                )
            )
            critical_result = await db.execute(critical_stmt)
            critical_alerts = critical_result.scalar() or 0
        else:
            active_alerts = 0
            critical_alerts = 0
        
        return {
            "total_sensors": len(devices),
            "online": online,
            "warning": warning,
            "offline": offline,
            "by_vault_type": by_vault_type,
            "total_readings_24h": total_readings,
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts,
        }
    
    def get_vault_types(self) -> List[Dict]:
        """Get available vault types with their default thresholds."""
        return [
            {
                "value": "base",
                "label": "Base Collection",
                "description": "Long-term storage at -18°C to -20°C",
                "thresholds": self.DEFAULT_THRESHOLDS["base"],
            },
            {
                "value": "active",
                "label": "Active Collection",
                "description": "Working collection at 2°C to 8°C",
                "thresholds": self.DEFAULT_THRESHOLDS["active"],
            },
            {
                "value": "cryo",
                "label": "Cryopreservation",
                "description": "Ultra-cold storage in liquid nitrogen",
                "thresholds": self.DEFAULT_THRESHOLDS["cryo"],
            },
        ]
    
    def _device_to_dict(self, device: IoTDevice) -> Dict:
        """Convert IoTDevice to dictionary format."""
        additional_info = device.additional_info or {}
        
        # Get current readings from sensors
        current_readings = {}
        sensor_types = []
        for sensor in device.sensors:
            sensor_types.append(sensor.sensor_type)
        
        return {
            "id": str(device.id),
            "sensor_id": additional_info.get("sensor_id", device.device_db_id),
            "vault_id": additional_info.get("vault_id"),
            "vault_name": device.name,
            "vault_type": additional_info.get("vault_type", "active"),
            "status": device.status,
            "battery": device.battery_level,
            "signal": device.signal_strength,
            "sensors": sensor_types,
            "current_readings": current_readings,
            "last_reading": device.last_seen.isoformat() if device.last_seen else None,
            "installed_date": additional_info.get("installed_date"),
            "calibration_date": device.calibration_date.strftime("%Y-%m-%d") if device.calibration_date else None,
            "alerts_enabled": additional_info.get("alerts_enabled", True),
        }


# Global service instance (for backward compatibility, but prefer dependency injection)
vault_sensor_service = VaultSensorService()

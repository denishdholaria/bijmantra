"""
IoT Telemetry Service
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iot import IoTDevice, IoTSensor, IoTSensorType, IoTTelemetry
from app.schemas.iot.telemetry import TelemetryCreate


class TelemetryService:
    """Service for managing IoT Telemetry Data."""

    async def record_reading(
        self,
        db: AsyncSession,
        telemetry_in: TelemetryCreate
    ) -> IoTTelemetry:
        """Record a new sensor reading."""

        # Resolve device
        device_query = select(IoTDevice).where(IoTDevice.device_db_id == telemetry_in.device_db_id)
        result = await db.execute(device_query)
        device = result.scalar_one_or_none()

        if not device:
            raise ValueError(f"Device {telemetry_in.device_db_id} not found.")

        # Resolve sensor
        sensor_query = select(IoTSensor).where(
            and_(IoTSensor.device_id == device.id, IoTSensor.sensor_type == telemetry_in.sensor_code)
        )
        result = await db.execute(sensor_query)
        sensor = result.scalar_one_or_none()

        if not sensor:
            # Auto-create sensor if it doesn't exist?
            # Check if type exists
            type_query = select(IoTSensorType).where(IoTSensorType.code == telemetry_in.sensor_code)
            type_result = await db.execute(type_query)
            sensor_type = type_result.scalar_one_or_none()

            unit = sensor_type.unit if sensor_type else ""

            sensor = IoTSensor(
                sensor_db_id=f"{device.device_db_id}-{telemetry_in.sensor_code}-{uuid4().hex[:4]}",
                device_id=device.id,
                sensor_type=telemetry_in.sensor_code,
                sensor_type_id=sensor_type.id if sensor_type else None,
                name=f"{device.name} {telemetry_in.sensor_code}",
                unit=unit,
                is_active=True
            )
            db.add(sensor)
            await db.flush()

        # Create telemetry
        ts = telemetry_in.timestamp or datetime.now()

        telemetry = IoTTelemetry(
            timestamp=ts,
            device_id=device.id,
            sensor_id=sensor.id,
            value=telemetry_in.value,
            raw_value=telemetry_in.raw_value,
            quality=telemetry_in.quality,
            quality_code=telemetry_in.quality_code,
            additional_info=telemetry_in.additional_info
        )
        db.add(telemetry)

        # Update device last seen
        device.last_seen = ts
        if device.status == "offline":
             device.status = "online"

        await db.commit()
        await db.refresh(telemetry)

        return telemetry

    async def get_readings(
        self,
        db: AsyncSession,
        device_db_id: str | None = None,
        sensor_code: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100
    ) -> tuple[list[IoTTelemetry], int]:
        """Get sensor readings with filtering."""

        query = select(IoTTelemetry).join(IoTDevice).join(IoTSensor)

        conditions = []
        if device_db_id:
            conditions.append(IoTDevice.device_db_id == device_db_id)
        if sensor_code:
            conditions.append(IoTSensor.sensor_type == sensor_code)
        if start_time:
            conditions.append(IoTTelemetry.timestamp >= start_time)
        if end_time:
            conditions.append(IoTTelemetry.timestamp <= end_time)

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        # Fetch with limit and sort
        query = query.order_by(desc(IoTTelemetry.timestamp)).limit(limit)
        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

# Singleton
telemetry_service = TelemetryService()

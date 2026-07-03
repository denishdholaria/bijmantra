"""
IoT Device Registry Service
"""

from uuid import uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iot import IoTDevice, IoTSensor, IoTSensorType
from app.schemas.iot.device import IoTDeviceCreate, IoTDeviceUpdate


class DeviceRegistryService:
    """Service for managing IoT Device Registry."""

    async def create_device(
        self,
        db: AsyncSession,
        device_in: IoTDeviceCreate,
        organization_id: int
    ) -> IoTDevice:
        """Register a new IoT device."""

        # Check if device exists
        query = select(IoTDevice).where(IoTDevice.device_db_id == device_in.device_db_id)
        result = await db.execute(query)
        existing_device = result.scalar_one_or_none()

        if existing_device:
            raise ValueError(f"Device with ID {device_in.device_db_id} already exists.")

        # Create new device
        device_data = device_in.model_dump(exclude={"sensors"})
        device = IoTDevice(
            **device_data,
            organization_id=organization_id,
            status="offline",
            battery_level=None,
            signal_strength=None,
            installation_date=func.now()
        )
        db.add(device)
        await db.flush() # Get ID

        # Auto-register sensors if provided
        if device_in.sensors:
            # Fetch all sensor types at once
            st_query = select(IoTSensorType).where(IoTSensorType.code.in_(device_in.sensors))
            st_result = await db.execute(st_query)
            sensor_types_map = {st.code: st for st in st_result.scalars().all()}

            for sensor_type_code in device_in.sensors:
                sensor_type = sensor_types_map.get(sensor_type_code)
                unit = sensor_type.unit if sensor_type else ""

                new_sensor = IoTSensor(
                    sensor_db_id=f"{device.device_db_id}-{sensor_type_code}-{uuid4().hex[:4]}",
                    device_id=device.id,
                    sensor_type=sensor_type_code,
                    sensor_type_id=sensor_type.id if sensor_type else None,
                    name=f"{device.name} {sensor_type_code}",
                    unit=unit,
                    is_active=True
                )
                db.add(new_sensor)

        await db.commit()
        await db.refresh(device)
        return device

    async def get_device(self, db: AsyncSession, device_id: int) -> IoTDevice | None:
        """Get device by internal ID."""
        query = select(IoTDevice).where(IoTDevice.id == device_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_device_by_db_id(self, db: AsyncSession, device_db_id: str) -> IoTDevice | None:
        """Get device by unique DB ID."""
        query = select(IoTDevice).where(IoTDevice.device_db_id == device_db_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_devices(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        organization_id: int | None = None,
        device_type: str | None = None,
        status: str | None = None,
        field_id: int | None = None,
    ) -> tuple[list[IoTDevice], int]:
        """List devices with filtering and pagination."""
        query = select(IoTDevice)

        conditions = []
        if organization_id:
            conditions.append(IoTDevice.organization_id == organization_id)
        if device_type:
            conditions.append(IoTDevice.device_type == device_type)
        if status:
            conditions.append(IoTDevice.status == status)
        if field_id:
            conditions.append(IoTDevice.field_id == field_id)

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        # Paginate
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

    async def update_device(
        self,
        db: AsyncSession,
        device_id: int,
        device_in: IoTDeviceUpdate
    ) -> IoTDevice | None:
        """Update device details."""
        device = await self.get_device(db, device_id)
        if not device:
            return None

        update_data = device_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)

        await db.commit()
        await db.refresh(device)
        return device

    async def delete_device(self, db: AsyncSession, device_id: int) -> bool:
        """Delete a device."""
        device = await self.get_device(db, device_id)
        if not device:
            return False

        await db.delete(device)
        await db.commit()
        return True

# Singleton instance
device_registry_service = DeviceRegistryService()

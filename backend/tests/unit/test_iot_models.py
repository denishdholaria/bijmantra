import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from app.models.core import Organization
from app.models.iot import IoTDevice, IoTSensor, IoTTelemetry

@pytest.mark.asyncio
async def test_create_iot_telemetry(async_db_session):
    """
    Test creation and retrieval of IoTTelemetry records.
    Verifies relationships with IoTDevice and IoTSensor are working.
    """
    # 1. Create Organization (Required for IoTDevice)
    org = Organization(
        name="IoT Test Org",
        description="Test Organization for IoT"
    )
    async_db_session.add(org)
    await async_db_session.flush()
    await async_db_session.refresh(org)

    # 2. Create IoT Device
    device = IoTDevice(
        device_db_id="test-device-001",
        name="Test Sensor Hub",
        device_type="weather_station",
        organization_id=org.id,
        status="online"
    )
    async_db_session.add(device)
    await async_db_session.flush()
    await async_db_session.refresh(device)

    # 3. Create IoT Sensor
    sensor = IoTSensor(
        sensor_db_id="temp-sensor-001",
        device_id=device.id,
        sensor_type="temperature",
        unit="Celsius",
        is_active=True
    )
    async_db_session.add(sensor)
    await async_db_session.flush()
    await async_db_session.refresh(sensor)

    # 4. Create IoT Telemetry
    timestamp = datetime.now(timezone.utc)
    telemetry = IoTTelemetry(
        timestamp=timestamp,
        device_id=device.id,
        sensor_id=sensor.id,
        value=25.5,
        quality="good"
    )
    async_db_session.add(telemetry)
    await async_db_session.commit()

    # 5. Verify Retrieval
    stmt = select(IoTTelemetry).where(
        IoTTelemetry.device_id == device.id,
        IoTTelemetry.sensor_id == sensor.id
    )
    result = await async_db_session.execute(stmt)
    retrieved = result.scalars().first()

    assert retrieved is not None
    assert retrieved.value == 25.5
    assert retrieved.quality == "good"
    assert retrieved.timestamp == timestamp
    assert retrieved.device_id == device.id
    assert retrieved.sensor_id == sensor.id

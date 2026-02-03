import sys
import os
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Patching for SQLite & GeoAlchemy2
from unittest.mock import MagicMock
import sys
sys.modules["geoalchemy2"] = MagicMock()
sys.modules["geoalchemy2.types"] = MagicMock()
sys.modules["geoalchemy2.shape"] = MagicMock()

# Mock Geometry type
from sqlalchemy.types import TypeDecorator, TEXT
class MockGeometry(TypeDecorator):
    impl = TEXT
    def __init__(self, *args, **kwargs):
        super().__init__()

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(TEXT)

sys.modules["geoalchemy2"].Geometry = MockGeometry
sys.modules["geoalchemy2.types"].Geometry = MockGeometry

# Patch JSONB/ARRAY for SQLite
from sqlalchemy.dialects import postgresql
postgresql.JSONB = TEXT
postgresql.ARRAY = lambda x: TEXT

from app.main import app
from app.core.database import Base, get_db
from app.models.iot import IoTDevice, IoTSensor

# Setup Test DB
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Override get_current_user to return a mock user with organization_id
from app.api.deps import get_current_user
class MockUser:
    organization_id = 1
    email = "test@example.com"
    id = 1

app.dependency_overrides[get_current_user] = lambda: MockUser()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def verify_endpoints():
    await init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        print("1. Register Device...")
        device_data = {
            "device_id": "TEST-DEV-001",
            "name": "Test Device",
            "device_type": "weather",
            "location": "Test Lab",
            "sensors": ["temperature", "humidity"]
        }
        response = await ac.post("/api/v2/sensors/devices", json=device_data)
        assert response.status_code == 200, f"Failed to register device: {response.text}"
        print("   Success:", response.json())

        print("\n2. List Devices...")
        response = await ac.get("/api/v2/sensors/devices")
        assert response.status_code == 200
        data = response.json()
        assert len(data["devices"]) == 1
        print("   Success:", data)

        print("\n3. Record Reading...")
        reading_data = {
            "device_id": "TEST-DEV-001",
            "sensor": "temperature",
            "value": 25.5,
            "unit": "C"
        }
        response = await ac.post("/api/v2/sensors/readings", json=reading_data)
        assert response.status_code == 200, f"Failed to record reading: {response.text}"
        print("   Success:", response.json())

        print("\n4. Get Readings...")
        response = await ac.get("/api/v2/sensors/readings?device_id=TEST-DEV-001")
        assert response.status_code == 200
        data = response.json()
        assert len(data["readings"]) == 1
        print("   Success:", data)

        print("\n5. Create Alert Rule...")
        rule_data = {
            "name": "High Temp",
            "sensor": "temperature",
            "condition": "above",
            "threshold": 30.0,
            "unit": "C"
        }
        response = await ac.post("/api/v2/sensors/alerts/rules", json=rule_data)
        assert response.status_code == 200
        print("   Success:", response.json())

        print("\n6. Trigger Alert (Record high reading)...")
        reading_data["value"] = 35.0
        await ac.post("/api/v2/sensors/readings", json=reading_data)

        print("\n7. Check Alert Events...")
        response = await ac.get("/api/v2/sensors/alerts/events")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) >= 1
        print("   Success:", data["events"][0]["message"])

        print("\nVerification Complete: All IoT endpoints operational.")

if __name__ == "__main__":
    asyncio.run(verify_endpoints())

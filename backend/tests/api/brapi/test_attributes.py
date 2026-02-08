import pytest
import sys
from unittest.mock import MagicMock

# Mock modules that might hang during startup
sys.modules["app.core.redis"] = MagicMock()
sys.modules["app.core.meilisearch"] = MagicMock()
sys.modules["app.services.task_queue"] = MagicMock()
sys.modules["app.services.redis_security"] = MagicMock()
sys.modules["app.core.socketio"] = MagicMock()

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.api.deps import get_db
from app.models.base import Base
from app.models.core import User, Organization
from app.models.brapi_phenotyping import GermplasmAttributeDefinition # Register model
from app.core.security import create_access_token
from datetime import timedelta

# Use async sqlite
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=engine)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(setup_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def token():
    # We need to create user/org directly in DB
    async with TestingSessionLocal() as db:
        # Check if org exists
        from sqlalchemy import select
        result = await db.execute(select(Organization).where(Organization.name == "Test Organization"))
        org = result.scalar_one_or_none()

        if not org:
            org = Organization(name="Test Organization")
            db.add(org)
            await db.commit()
            await db.refresh(org)

        result = await db.execute(select(User).where(User.email == "test@example.com"))
        user = result.scalar_one_or_none()

        if not user:
            user = User(email="test@example.com", hashed_password="password", organization_id=org.id, is_active=True)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        return access_token

@pytest.mark.asyncio
async def test_germplasm_attributes_crud(client, token):
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create
    new_attr = {
        "attributeName": "Test Attribute 1",
        "attributeCategory": "Agronomic",
        "dataType": "Text",
        "commonCropName": "Wheat"
    }
    response = await client.post("/brapi/v2/attributes", json=[new_attr], headers=headers)
    assert response.status_code == 201, f"Create failed: {response.text}"
    data = response.json()["result"]["data"]
    assert len(data) == 1
    attr_id = data[0]["attributeDbId"]

    # 2. Get All
    response = await client.get("/brapi/v2/attributes", headers=headers)
    assert response.status_code == 200, f"Get All failed: {response.text}"
    data = response.json()["result"]["data"]
    assert any(a["attributeDbId"] == attr_id for a in data)

    # 3. Get One
    response = await client.get(f"/brapi/v2/attributes/{attr_id}", headers=headers)
    assert response.status_code == 200, f"Get One failed: {response.text}"
    assert response.json()["result"]["attributeDbId"] == attr_id

    # 4. Update
    update_data = {
        "attributeName": "Updated Name",
        "attributeCategory": "Agronomic"
    }
    response = await client.put(f"/brapi/v2/attributes/{attr_id}", json=update_data, headers=headers)
    assert response.status_code == 200, f"Update failed: {response.text}"
    assert response.json()["result"]["attributeName"] == "Updated Name"

    # 5. Categories
    response = await client.get("/brapi/v2/attributes/categories", headers=headers)
    assert response.status_code == 200, f"Get Categories failed: {response.text}"
    assert "Agronomic" in response.json()["result"]["data"]

    # 6. Delete
    response = await client.delete(f"/brapi/v2/attributes/{attr_id}", headers=headers)
    assert response.status_code == 200, f"Delete failed: {response.text}"

    # 7. Verify Delete
    response = await client.get(f"/brapi/v2/attributes/{attr_id}", headers=headers)
    assert response.status_code == 404, f"Verify Delete failed: {response.text}"

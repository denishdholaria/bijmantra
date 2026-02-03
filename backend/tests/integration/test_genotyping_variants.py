import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.base import Base
# Import models to register them
from app.models import core, genotyping
from app.middleware.tenant_context import get_tenant_db
from app.core.security import create_access_token

# Async SQLite
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

@pytest.fixture
async def override_get_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def _get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_tenant_db] = _get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client(override_get_db):
    # Need to create user for token
    async with TestingSessionLocal() as session:
        org = core.Organization(name="Test Org")
        session.add(org)
        await session.commit()
        await session.refresh(org)

        user = core.User(email="test@example.com", hashed_password="pw", organization_id=org.id, is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id
        org_id = org.id

    token = create_access_token(data={"sub": str(user_id), "organization_id": org_id})

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"}
    ) as client:
        yield client

@pytest.mark.asyncio
async def test_crud_variants(async_client):
    # 1. Create VariantSet
    vs_payload = {"variantSetName": "TestVS"}
    response = await async_client.post("/brapi/v2/variantsets", json=vs_payload)
    assert response.status_code == 200
    vs_data = response.json()["result"]
    vs_id = vs_data["variantSetDbId"]
    assert vs_data["variantSetName"] == "TestVS"

    # 2. Create Variant
    v_payload = {
        "variantName": "TestVariant",
        "variantType": "SNP",
        "referenceBases": "A",
        "alternateBases": ["G"],
        "start": 100,
        "end": 101,
        "variantSetDbId": vs_id,
        "referenceName": "Chr1"
    }
    response = await async_client.post("/brapi/v2/variants", json=v_payload)
    assert response.status_code == 200
    v_data = response.json()["result"]
    v_id = v_data["variantDbId"]
    assert v_data["variantName"] == "TestVariant"
    assert v_data["variantSetDbId"] == [vs_id]

    # 3. List Variants
    response = await async_client.get(f"/brapi/v2/variants?variantSetDbId={vs_id}")
    assert response.status_code == 200
    data = response.json()["result"]["data"]
    assert len(data) >= 1
    assert any(v["variantDbId"] == v_id for v in data)

    # 4. Update Variant
    update_payload = {"variantName": "UpdatedVariant"}
    response = await async_client.put(f"/brapi/v2/variants/{v_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["result"]["variantName"] == "UpdatedVariant"

    # 5. Delete Variant
    response = await async_client.delete(f"/brapi/v2/variants/{v_id}")
    assert response.status_code == 200

    # 6. Verify Deletion
    response = await async_client.get(f"/brapi/v2/variants/{v_id}")
    # get_variant returns null result if not found, usually 200 OK with empty result in BrAPI?
    # My implementation returns:
    # if not variant: return {"metadata": {"status": [{"message": "not found", "messageType": "ERROR"}]}, "result": None}
    assert response.status_code == 200
    assert response.json()["result"] is None

    # 7. Delete VariantSet
    response = await async_client.delete(f"/brapi/v2/variantsets/{vs_id}")
    assert response.status_code == 200

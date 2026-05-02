import pytest
import sys
from unittest.mock import MagicMock
from sqlalchemy import event, select

# Mock modules that might hang during startup
sys.modules["app.core.redis"] = MagicMock()
sys.modules["app.core.meilisearch"] = MagicMock()
sys.modules["app.services.task_queue"] = MagicMock()
sys.modules["app.services.redis_security"] = MagicMock()
sys.modules["app.core.socketio"] = MagicMock()
sys.modules["app.modules.core.services.audit_service"] = MagicMock()

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.api.deps import get_db, get_current_user
from app.models.base import Base
from app.models.core import User, Organization
from app.models.genotyping import Call, CallSet, Variant, VariantSet, Reference, ReferenceSet
from app.models.phenotyping import Sample

# Use async sqlite
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Mock SpatiaLite functions for SQLite
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

    # Mock SpatiaLite functions
    dbapi_connection.create_function("RecoverGeometryColumn", -1, lambda *args: None)
    dbapi_connection.create_function("CreateSpatialIndex", -1, lambda *args: None)
    dbapi_connection.create_function("DisableSpatialIndex", -1, lambda *args: None)
    dbapi_connection.create_function("CheckSpatialIndex", -1, lambda *args: None)
    dbapi_connection.create_function("GeomFromEWKT", -1, lambda *args: args[0] if args else None)
    dbapi_connection.create_function("AsEWKB", -1, lambda *args: args[0] if args else None)
    dbapi_connection.create_function("DiscardGeometryColumn", -1, lambda *args: None)

event.listen(engine.sync_engine, "connect", set_sqlite_pragma)

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
async def test_data():
    async with TestingSessionLocal() as db:
        # Create Organizations
        org1 = Organization(name="Org 1")
        org2 = Organization(name="Org 2")
        db.add_all([org1, org2])
        await db.commit()
        await db.refresh(org1)
        await db.refresh(org2)

        # Create Users
        user1 = User(email="user1@example.com", hashed_password="pw", organization_id=org1.id, is_active=True)
        user2 = User(email="user2@example.com", hashed_password="pw", organization_id=org2.id, is_active=True)
        db.add_all([user1, user2])
        await db.commit()
        await db.refresh(user1)
        await db.refresh(user2)

        # Create Genotyping Data for Org 1
        ref_set = ReferenceSet(
            reference_set_db_id="rs1", reference_set_name="Ref Set 1", organization_id=org1.id
        )
        db.add(ref_set)
        await db.commit()
        await db.refresh(ref_set)

        ref = Reference(
            reference_db_id="r1", reference_name="Ref 1", reference_set_id=ref_set.id, organization_id=org1.id
        )
        db.add(ref)
        await db.commit()
        await db.refresh(ref)

        var_set = VariantSet(
            variant_set_db_id="vs1", variant_set_name="Var Set 1", reference_set_id=ref_set.id, organization_id=org1.id
        )
        db.add(var_set)
        await db.commit()
        await db.refresh(var_set)

        variant = Variant(
            variant_db_id="v1", variant_name="Var 1", variant_set_id=var_set.id, reference_id=ref.id, organization_id=org1.id
        )
        db.add(variant)
        await db.commit()
        await db.refresh(variant)

        sample = Sample(
            sample_db_id="s1", sample_name="Sample 1", organization_id=org1.id
        )
        db.add(sample)
        await db.commit()
        await db.refresh(sample)

        call_set = CallSet(
            call_set_db_id="cs1", call_set_name="Call Set 1", sample_id=sample.id, organization_id=org1.id
        )
        db.add(call_set)
        await db.commit()
        await db.refresh(call_set)

        call = Call(
            call_db_id="c1", variant_id=variant.id, call_set_id=call_set.id, genotype_value="0/1", organization_id=org1.id
        )
        db.add(call)
        await db.commit()

        return {
            "org1": org1, "user1": user1,
            "org2": org2, "user2": user2,
            "call": call
        }

@pytest.mark.asyncio
async def test_calls_security(client, test_data):
    """
    Test security controls for /brapi/v2/calls endpoint.
    """
    user1 = test_data["user1"]
    user2 = test_data["user2"]

    # 1. Unauthenticated Access -> Should be 401
    # Ensure no current_user override is active, but keep get_db override
    # We can manually set the override dict
    app.dependency_overrides = {get_db: override_get_db}

    response = await client.get("/brapi/v2/calls")
    assert response.status_code == 401, "Unauthenticated access should be denied"

    # 2. Same Organization Access -> Should see data
    async def override_get_current_user_org1():
        return user1

    app.dependency_overrides[get_current_user] = override_get_current_user_org1

    response = await client.get("/brapi/v2/calls")
    assert response.status_code == 200, "Same org access should be allowed"
    data = response.json()["result"]["data"]
    assert len(data) == 1
    assert data[0]["genotypeValue"] == "0/1"

    # 3. Cross Organization Access -> Should NOT see data
    async def override_get_current_user_org2():
        return user2

    app.dependency_overrides[get_current_user] = override_get_current_user_org2

    response = await client.get("/brapi/v2/calls")
    assert response.status_code == 200, "Cross org access allowed but filtered"
    data = response.json()["result"]["data"]
    assert len(data) == 0, "Should not see calls from other organization"

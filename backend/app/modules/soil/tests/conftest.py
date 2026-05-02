from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.core import Organization, User


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    class_=AsyncSession, autocommit=False, autoflush=False, bind=engine
)

@event.listens_for(engine.sync_engine, "connect")
def do_connect(dbapi_connection, connection_record):
    # Mock GeoAlchemy2 spatial functions for SQLite
    try:
        # Mock functions called by GeoAlchemy2
        dbapi_connection.create_function("RecoverGeometryColumn", 5, lambda *args: 1)
        dbapi_connection.create_function("DiscardGeometryColumn", 2, lambda *args: 1)
        dbapi_connection.create_function("GeometryType", 1, lambda *args: "POINT")
        dbapi_connection.create_function("ST_AsText", 1, lambda *args: "POINT(0 0)")
        dbapi_connection.create_function("ST_GeomFromText", 1, lambda *args: b'\x00')
        dbapi_connection.create_function("CreateSpatialIndex", 2, lambda *args: 1)
        dbapi_connection.create_function("CheckSpatialIndex", 2, lambda *args: 1)
        dbapi_connection.create_function("DisableSpatialIndex", 2, lambda *args: 1)
        # Add mock for ST_Point to prevent "no such function: ST_Point" errors
        dbapi_connection.create_function("ST_Point", 2, lambda x, y: f"POINT({x} {y})")
        # For AddGeometryColumn
        dbapi_connection.create_function("AddGeometryColumn", 6, lambda *args: 1)
    except Exception:
        pass

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def db() -> AsyncGenerator[AsyncSession, None]:
    # Need to handle potential issues with unsupported types in SQLite (ARRAY)
    # We can try to modify the metadata for testing or just accept that some tables fail creation

    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            # We explicitly ignore compile errors for ARRAY types in SQLite
            # This allows testing non-array models even if some tables fail creation
            print(f"Warning: Table creation failed partially: {e}")

    async with TestingSessionLocal() as session:
        # Seed required data for tests
        try:
            org = Organization(id=1, name="Test Org")
            session.add(org)
            await session.commit()

            # Need a Field record for Soil models
            # But Field model might not exist or be importable if tables failed
            # Try to import Field
            from app.models.future.field import Field
            field = Field(id=1, name="Test Field", organization_id=1, area=10.0)
            session.add(field)
            await session.commit()
        except Exception as e:
            print(f"Warning: Could not seed initial data: {e}")

        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="module")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Override get_db dependency
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    # Mock authentication
    from app.api.deps import get_current_active_user, get_organization_id

    async def override_get_current_active_user():
        return User(id=1, email="test@example.com", is_active=True, organization_id=1)

    async def override_get_organization_id():
        return 1

    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    app.dependency_overrides[get_organization_id] = override_get_organization_id

    # Use ASGITransport for newer httpx versions
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()

@pytest.fixture
def normal_user_token_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-token"}

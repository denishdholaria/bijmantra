"""
Pytest configuration for BrAPI endpoint tests.
Simplified version for testing public endpoints.
"""

import pytest
import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from geoalchemy2 import Geometry
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.core import User, Organization
from app.models.base import Base
from app.core.security import create_access_token
from app.core.database import get_db
from datetime import timedelta
from sqlalchemy import select

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use a file-based SQLite database to allow sharing between sync and async engines
TEST_DB_FILE = "test.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"
ASYNC_TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

# SQLite compatibility patches
@compiles(Geometry, 'sqlite')
def compile_geometry(element, compiler, **kw):
    return "TEXT"

@compiles(ARRAY, 'sqlite')
def compile_array(element, compiler, **kw):
    return "JSON"

@compiles(JSONB, 'sqlite')
def compile_jsonb(element, compiler, **kw):
    return "JSON"

# Sync Engine (for legacy tests and fixtures)
sync_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Mock SpatiaLite functions for SQLite
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

    # Mock SpatiaLite functions to prevent errors with Geometry columns
    dbapi_connection.create_function("RecoverGeometryColumn", -1, lambda *args: None)
    dbapi_connection.create_function("CreateSpatialIndex", -1, lambda *args: None)
    dbapi_connection.create_function("DisableSpatialIndex", -1, lambda *args: None)
    dbapi_connection.create_function("CheckSpatialIndex", -1, lambda *args: None)
    dbapi_connection.create_function("GeomFromEWKT", -1, lambda *args: args[0] if args else None)
    dbapi_connection.create_function("AsEWKB", -1, lambda *args: args[0] if args else None)
    dbapi_connection.create_function("DiscardGeometryColumn", -1, lambda *args: None)

event.listen(sync_engine, "connect", set_sqlite_pragma)

SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Async Engine (for new tests and app override)
async_engine = create_async_engine(
    ASYNC_TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
AsyncTestingSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

event.listen(async_engine.sync_engine, "connect", set_sqlite_pragma)

@pytest.fixture(scope="session")
def setup_db():
    # Remove existing test DB if any
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

    # Only create tables needed for tests to avoid SQLite/GeoAlchemy2 issues with RecoverGeometryColumn
    tables = [
        "organizations",
        "users",
        "user_profiles",
        "collaboration_activities",
        "shared_items",
        "collaboration_workspaces",
        "workspace_members",
        "user_presence",
        "collaboration_tasks",
        "collaboration_comments",
        "roles",
        "user_roles",
        "user_dock_preferences",
        "conversations",
        "conversation_participants",
        "messages",
        # Add tables for other tests if needed
        "carbon_stocks",
        "plates",
        "studies",
        "trials",
        "programs",
        "samples",
        "observation_units",
        "crossing_projects",
        "crosses",
        "germplasm",
        "seasons",
        "people",
        "locations",
        "iot_devices",
        "iot_sensors",
        "iot_telemetry",
        "barcode_scans",
        "seedlots"
    ]

    tables_to_create = []
    for table_name in tables:
        if table_name in Base.metadata.tables:
            tables_to_create.append(Base.metadata.tables[table_name])

    Base.metadata.create_all(bind=sync_engine, tables=tables_to_create)

    yield

    # Cleanup
    Base.metadata.drop_all(bind=sync_engine)
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

@pytest.fixture
def db_session(setup_db) -> Session:
    """
    Creates a new synchronous database session for a test.
    Compatible with legacy tests.
    """
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
async def async_db_session(setup_db) -> AsyncSession:
    """
    Creates a new asynchronous database session for a test.
    For new async tests.
    """
    async with AsyncTestingSessionLocal() as session:
        yield session

@pytest.fixture
def test_user(db_session: Session) -> User:
    """
    Creates a test user and organization using sync session.
    Compatible with legacy tests.
    """
    org = db_session.query(Organization).filter_by(name="Test Organization").first()
    if not org:
        org = Organization(name="Test Organization")
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)

    user = db_session.query(User).filter_by(email="test@example.com").first()
    if not user:
        user = User(
            email="test@example.com",
            hashed_password="password",
            organization_id=org.id,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
async def authenticated_client(test_user: User) -> AsyncClient:
    """
    Creates an authenticated client.
    Overrides get_db to use the async session connected to the SAME test database.
    """
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(test_user.id)}, expires_delta=access_token_expires
    )

    # Override dependency to use our async session factory
    async def override_get_db():
        async with AsyncTestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {access_token}"},
    ) as client:
        yield client

    app.dependency_overrides.clear()

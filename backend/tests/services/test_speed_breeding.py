import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.core import Organization
from app.models.speed_breeding import SpeedBreedingProtocol
from app.services.speed_breeding import speed_breeding_service
from app.schemas.speed_breeding import SpeedBreedingProtocolCreate

# Use sqlite+aiosqlite for async sqlite
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="module")
async def async_engine():
    engine = create_async_engine(DATABASE_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        # Filter tables to create to avoid GeoAlchemy/SQLite issues
        tables = [
            t for t in Base.metadata.sorted_tables
            if t.name.startswith("speed_breeding_") or t.name == "organizations"
        ]
        await conn.run_sync(Base.metadata.create_all, tables=tables)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, tables=tables)
    await engine.dispose()

@pytest_asyncio.fixture
async def async_db_session(async_engine):
    AsyncSessionLocal = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_create_and_get_protocol(async_db_session):
    # Setup Organization
    org = Organization(name="Test Org", id=1)
    async_db_session.add(org)
    await async_db_session.commit()

    # Test Create
    protocol_in = SpeedBreedingProtocolCreate(
        name="Test Protocol",
        crop="Test Crop",
        photoperiod=16,
        temperature_day=25.0,
        temperature_night=20.0
    )

    created = await speed_breeding_service.create_protocol(async_db_session, 1, protocol_in)
    assert created.id is not None
    assert created.name == "Test Protocol"

    # Test Get
    fetched = await speed_breeding_service.get_protocol(async_db_session, 1, str(created.id))
    assert fetched is not None
    assert fetched.id == created.id

    # Test List
    protocols = await speed_breeding_service.get_protocols(async_db_session, 1)
    assert len(protocols) == 1
    assert protocols[0].name == "Test Protocol"

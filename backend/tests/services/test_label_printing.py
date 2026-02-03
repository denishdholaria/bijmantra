import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.core import Organization
from app.services.label_printing import label_printing_service
from app.models.label_printing import PrintJob, PrintJobStatus
from sqlalchemy import select
from datetime import datetime, timezone
from sqlalchemy.ext.compiler import compiles
from geoalchemy2 import Geometry
import app.models # Ensure models are registered

# SQLite compatibility patches
# This allows using SQLite for tests even if models use PostGIS Geometry types
# by compiling Geometry columns to TEXT type in SQLite.
@compiles(Geometry, 'sqlite')
def compile_geometry(element, compiler, **kw):
    return "TEXT"

# Use async sqlite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def async_db_engine():
    """Create async database engine for testing.

    This fixture:
    1. Creates an in-memory SQLite engine with async driver.
    2. Creates only the necessary tables (Organization, PrintJob) to avoid
       complex dependency issues with other models (especially those using
       GeoAlchemy2 features not fully supported by standard SQLite).
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Create tables
    async with engine.begin() as conn:
        # Only create tables needed for tests to avoid GeoAlchemy/Spatialite issues with other tables
        await conn.run_sync(Base.metadata.create_all, tables=[
            Organization.__table__,
            PrintJob.__table__
        ])

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, tables=[
            Organization.__table__,
            PrintJob.__table__
        ])

    await engine.dispose()

@pytest_asyncio.fixture
async def db(async_db_engine):
    """Create async database session for testing."""
    async_session = sessionmaker(
        async_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def test_organization(db):
    """Create a test organization."""
    org = Organization(name="Test Org Print", description="Test Description")
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org

@pytest.mark.asyncio
async def test_create_print_job(db, test_organization):
    """Test creating a new print job."""
    data = {
        "template_id": "plot-standard",
        "label_count": 10,
        "copies": 2,
        "items": [{"id": "1", "data": "test"}],
        "created_by": "test_user"
    }

    result = await label_printing_service.create_print_job(db, test_organization.id, data)

    assert result["template_id"] == "plot-standard"
    assert result["label_count"] == 10
    assert result["copies"] == 2
    assert result["status"] == "pending"
    assert result["created_by"] == "test_user"
    assert result["id"].startswith("job-")

    # Verify DB
    stmt = select(PrintJob).where(PrintJob.job_id == result["id"])
    db_result = await db.execute(stmt)
    job = db_result.scalar_one()

    assert job.organization_id == test_organization.id
    assert job.template_id == "plot-standard"
    assert job.label_count == 10
    assert job.copies == 2
    assert job.status == PrintJobStatus.PENDING

@pytest.mark.asyncio
async def test_get_print_jobs(db, test_organization):
    """Test retrieving print jobs."""
    # Create a job
    data = {
        "template_id": "plot-standard",
        "label_count": 5,
        "copies": 1,
    }
    job1 = await label_printing_service.create_print_job(db, test_organization.id, data)

    # Get jobs
    jobs = await label_printing_service.get_print_jobs(db, test_organization.id)
    assert len(jobs) >= 1
    ids = [j["id"] for j in jobs]
    assert job1["id"] in ids

    # Verify items are correctly retrieved (JSON serialization)
    retrieved_job = next(j for j in jobs if j["id"] == job1["id"])
    assert retrieved_job["items"] is not None
    assert len(retrieved_job["items"]) == 0 # Default empty list in create_print_job unless provided

    # Test filter by status
    # Manually update status for testing
    stmt = select(PrintJob).where(PrintJob.job_id == job1["id"])
    result = await db.execute(stmt)
    job_obj = result.scalar_one()
    job_obj.status = PrintJobStatus.COMPLETED
    job_obj.completed_at = datetime.now(timezone.utc)
    await db.commit()

    completed_jobs = await label_printing_service.get_print_jobs(db, test_organization.id, status=PrintJobStatus.COMPLETED)
    assert len(completed_jobs) >= 1
    assert job1["id"] in [j["id"] for j in completed_jobs]

    pending_jobs = await label_printing_service.get_print_jobs(db, test_organization.id, status=PrintJobStatus.PENDING)
    assert job1["id"] not in [j["id"] for j in pending_jobs]

@pytest.mark.asyncio
async def test_get_stats(db, test_organization):
    """Test retrieving label printing statistics."""
    # Create completed job
    data1 = {"template_id": "t1", "label_count": 10, "copies": 2}
    job1 = await label_printing_service.create_print_job(db, test_organization.id, data1)

    # Create pending job
    data2 = {"template_id": "t2", "label_count": 5, "copies": 1}
    job2 = await label_printing_service.create_print_job(db, test_organization.id, data2)

    # Mark job1 as completed
    stmt = select(PrintJob).where(PrintJob.job_id == job1["id"])
    result = await db.execute(stmt)
    job_obj = result.scalar_one()
    job_obj.status = PrintJobStatus.COMPLETED
    job_obj.completed_at = datetime.now(timezone.utc)
    await db.commit()

    stats = await label_printing_service.get_stats(db, test_organization.id)

    assert stats["total_jobs"] == 2
    assert stats["completed_jobs"] == 1
    assert stats["pending_jobs"] == 1
    assert stats["total_labels_printed"] == 20 # 10 * 2
    assert stats["last_print"] is not None

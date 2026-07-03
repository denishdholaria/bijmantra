import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.core import Organization
from app.modules.phenotyping.services.vision.datasets_service import (
    DatasetType,
    vision_dataset_service,
)
from app.modules.phenotyping.services.vision.training_service import (
    TrainingBackend,
    TrainingStatus,
    vision_training_service,
)


@pytest.fixture
async def vision_training_db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    tables = [
        Base.metadata.tables["organizations"],
        Base.metadata.tables["vision_datasets"],
        Base.metadata.tables["vision_dataset_images"],
        Base.metadata.tables["vision_training_jobs"],
        Base.metadata.tables["vision_training_logs"],
    ]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        org = Organization(name="Vision Training Test Org")
        session.add(org)
        await session.commit()
        await session.refresh(org)
        dataset = await vision_dataset_service.create_dataset(
            session,
            org.id,
            name="Training Dataset",
            description="Dataset for training tests",
            dataset_type=DatasetType.CLASSIFICATION,
            crop="rice",
            classes=["healthy", "blast"],
            train_split=0.7,
            val_split=0.15,
            test_split=0.15,
        )
        yield session, org.id, dataset

    await engine.dispose()


@pytest.mark.asyncio
async def test_training_job_is_persisted_and_listed(vision_training_db_session):
    db, org_id, dataset = vision_training_db_session

    job = await vision_training_service.create_job(
        db,
        org_id,
        name="MobileNet bootstrap",
        dataset_id=dataset["id"],
        base_model="mobilenetv2",
        backend=TrainingBackend.SERVER,
        hyperparameters={"epochs": 8},
        created_by="tester",
    )

    assert job["id"] is not None
    assert job["job_code"].startswith("vision-training-")
    assert job["dataset_id"] == dataset["id"]
    assert job["status"] == TrainingStatus.QUEUED
    assert job["hyperparameters"]["epochs"] == 8

    jobs = await vision_training_service.list_jobs(db, org_id, dataset_id=dataset["dataset_code"])
    assert [item["id"] for item in jobs] == [job["id"]]


@pytest.mark.asyncio
async def test_start_job_fails_closed_without_runner_and_records_log(vision_training_db_session):
    db, org_id, dataset = vision_training_db_session
    job = await vision_training_service.create_job(
        db,
        org_id,
        name="No runner job",
        dataset_id=dataset["id"],
        base_model="efficientnetb0",
        backend=TrainingBackend.SERVER,
        hyperparameters={},
    )

    started = await vision_training_service.start_job(db, org_id, job["id"])
    logs = await vision_training_service.get_logs(db, org_id, job["id"])

    assert started is not None
    assert started["status"] == TrainingStatus.FAILED
    assert "No training runner is configured" in started["error_message"]
    assert any(log["event_type"] == "runner_unavailable" for log in logs)


@pytest.mark.asyncio
async def test_cancel_queued_training_job(vision_training_db_session):
    db, org_id, dataset = vision_training_db_session
    job = await vision_training_service.create_job(
        db,
        org_id,
        name="Cancelable job",
        dataset_id=dataset["dataset_code"],
        base_model="resnet50",
        backend=TrainingBackend.CLOUD,
        hyperparameters={},
    )

    cancelled = await vision_training_service.cancel_job(db, org_id, job["job_code"])

    assert cancelled is not None
    assert cancelled["status"] == TrainingStatus.CANCELLED
    assert cancelled["progress"] == 0

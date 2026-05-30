import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.core import Organization
from app.modules.phenotyping.services.vision.datasets_service import (
    DatasetStatus,
    DatasetType,
    vision_dataset_service,
)


@pytest.fixture
async def vision_db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    tables = [
        Base.metadata.tables["organizations"],
        Base.metadata.tables["vision_datasets"],
        Base.metadata.tables["vision_dataset_images"],
    ]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        org = Organization(name="Vision Test Org")
        other_org = Organization(name="Other Vision Org")
        session.add_all([org, other_org])
        await session.commit()
        await session.refresh(org)
        await session.refresh(other_org)
        yield session, org.id, other_org.id

    await engine.dispose()


@pytest.mark.asyncio
async def test_dataset_crud_is_persisted_and_tenant_scoped(vision_db_session):
    db, org_id, other_org_id = vision_db_session

    dataset = await vision_dataset_service.create_dataset(
        db,
        org_id,
        name="Rice Leaf Disease v1",
        description="Public bootstrap set",
        dataset_type=DatasetType.CLASSIFICATION,
        crop="rice",
        classes=["healthy", "blast"],
        train_split=0.7,
        val_split=0.15,
        test_split=0.15,
        created_by="tester",
    )

    assert dataset["id"] is not None
    assert dataset["dataset_code"].startswith("vision-dataset-")
    assert dataset["organization_id"] == org_id
    assert dataset["image_count"] == 0

    own_datasets = await vision_dataset_service.list_datasets(db, org_id, crop="rice")
    other_datasets = await vision_dataset_service.list_datasets(db, other_org_id, crop="rice")

    assert [item["id"] for item in own_datasets] == [dataset["id"]]
    assert other_datasets == []

    updated = await vision_dataset_service.update_dataset(
        db,
        org_id,
        dataset["id"],
        {"status": DatasetStatus.COLLECTING, "classes": ["healthy", "blast", "brown_spot"]},
    )

    assert updated is not None
    assert updated["status"] == "collecting"
    assert updated["classes"] == ["healthy", "blast", "brown_spot"]

    deleted = await vision_dataset_service.delete_dataset(db, org_id, dataset["id"])
    assert deleted is True
    assert await vision_dataset_service.get_dataset(db, org_id, dataset["id"]) is None


@pytest.mark.asyncio
async def test_dataset_images_stats_and_export(vision_db_session):
    db, org_id, _other_org_id = vision_db_session
    dataset = await vision_dataset_service.create_dataset(
        db,
        org_id,
        name="Tomato Disease v1",
        description="Tomato labels",
        dataset_type=DatasetType.CLASSIFICATION,
        crop="tomato",
        classes=["healthy", "late_blight"],
        train_split=0.8,
        val_split=0.1,
        test_split=0.1,
    )

    result = await vision_dataset_service.add_images(
        db,
        org_id,
        dataset_id=dataset["dataset_code"],
        images=[
            {
                "filename": "../late-blight leaf.jpg",
                "url": "s3://bucket/a.jpg",
                "width": 1024,
                "height": 768,
                "size_bytes": 2048,
                "split": "train",
                "metadata": {"source": "public"},
                "annotation": {"label": "late_blight"},
            },
            {
                "filename": "healthy.png",
                "url": "s3://bucket/b.png",
                "width": 900,
                "height": 700,
                "size_bytes": 1024,
                "split": "test",
            },
        ],
    )

    assert result["added_count"] == 2
    assert result["total_images"] == 2
    assert result["images"][0]["filename"] == "late-blight leaf.jpg"

    train_images = await vision_dataset_service.get_dataset_images(
        db,
        org_id,
        dataset_id=dataset["id"],
        split="train",
    )
    annotated_images = await vision_dataset_service.get_dataset_images(
        db,
        org_id,
        dataset_id=dataset["id"],
        annotated_only=True,
    )
    stats = await vision_dataset_service.get_dataset_stats(db, org_id, dataset["id"])
    csv_export = await vision_dataset_service.export_annotations(db, org_id, dataset["id"], "csv")

    assert len(train_images) == 1
    assert len(annotated_images) == 1
    assert stats is not None
    assert stats["image_count"] == 2
    assert stats["annotated_count"] == 1
    assert stats["split_counts"] == {"train": 1, "val": 0, "test": 1}
    assert stats["class_distribution"] == {"late_blight": 1}
    assert csv_export is not None
    assert csv_export["format"] == "csv"
    assert csv_export["rows"][0]["label"] == "late_blight"


@pytest.mark.asyncio
async def test_dataset_service_rejects_invalid_splits(vision_db_session):
    db, org_id, _other_org_id = vision_db_session

    result = await vision_dataset_service.create_dataset(
        db,
        org_id,
        name="Invalid Splits",
        description="Bad ratios",
        dataset_type=DatasetType.CLASSIFICATION,
        crop="rice",
        classes=["healthy", "blast"],
        train_split=0.5,
        val_split=0.5,
        test_split=0.5,
    )

    assert result["error"] == "Train, val, and test splits must sum to 1.0"

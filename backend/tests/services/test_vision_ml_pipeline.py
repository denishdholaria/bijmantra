from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.core import Organization
from app.models.vision import VisionModel
from app.modules.phenotyping.services.vision.artifact_utils import write_artifact_manifest
from app.modules.phenotyping.services.vision.dataset_governance_service import (
    vision_dataset_governance_service,
)
from app.modules.phenotyping.services.vision.inference_service import vision_inference_service
from app.modules.phenotyping.services.vision.public_dataset_catalog import (
    PROJECT_USE_COMMERCIAL,
    PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
)
from app.modules.phenotyping.services.vision.registry_lifecycle_service import (
    vision_model_lifecycle_service,
)
from app.modules.phenotyping.services.vision.training_runner import vision_training_runner
from app.modules.phenotyping.services.vision.training_service import (
    TrainingBackend,
    vision_training_service,
)


def _write_fixture_dataset(root: Path) -> Path:
    colors = {
        "Tomato___healthy": [(35, 150, 55), (45, 160, 65), (30, 140, 50), (50, 155, 60)],
        "Tomato___late_blight": [
            (145, 90, 35),
            (130, 80, 45),
            (160, 95, 40),
            (150, 75, 30),
        ],
    }
    for label, samples in colors.items():
        label_dir = root / label
        label_dir.mkdir(parents=True, exist_ok=True)
        for index, color in enumerate(samples):
            image = Image.new("RGB", (96, 96), color)
            image.save(label_dir / f"{index}.png")
    return root


@pytest.fixture
async def vision_pipeline_db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    table_names = [
        "organizations",
        "vision_datasets",
        "vision_dataset_images",
        "vision_dataset_versions",
        "vision_dataset_audit_logs",
        "vision_training_jobs",
        "vision_training_logs",
        "vision_models",
        "vision_deployments",
    ]
    tables = [Base.metadata.tables[name] for name in table_names]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        org = Organization(name="Vision ML Pipeline Org")
        session.add(org)
        await session.commit()
        await session.refresh(org)
        yield session, org.id

    await engine.dispose()


@pytest.mark.asyncio
async def test_governed_ingestion_rejects_dataset_disallowed_for_project_use(
    vision_pipeline_db_session,
    tmp_path,
):
    db, org_id = vision_pipeline_db_session
    dataset_root = _write_fixture_dataset(tmp_path / "plant-pathology")

    result = await vision_dataset_governance_service.ingest_local_directory(
        db,
        org_id,
        dataset_root=dataset_root,
        source_slug="plant-pathology-fgvc",
        dataset_name="Apple field dataset",
        crop="apple",
        split_seed=11,
        preprocessing_version="vision-preprocess-v1",
        created_by="test",
    )

    assert result["error"] == "Dataset source terms are not approved for this project use"
    assert result["allowed_uses"] == ["academic_research", "competition"]


@pytest.mark.asyncio
async def test_governed_ingestion_requires_manual_terms_acceptance_for_kaggle_sources(
    vision_pipeline_db_session,
    tmp_path,
):
    db, org_id = vision_pipeline_db_session
    dataset_root = _write_fixture_dataset(tmp_path / "cassava-needs-acceptance")

    result = await vision_dataset_governance_service.ingest_local_directory(
        db,
        org_id,
        dataset_root=dataset_root,
        source_slug="cassava-leaf-disease",
        dataset_name="Cassava without terms record",
        crop="cassava",
        split_seed=42,
        preprocessing_version="vision-preprocess-v1",
        created_by="test",
        project_use=PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
    )

    assert (
        result["error"] == "Dataset source requires manual access terms acceptance before ingestion"
    )
    assert (
        "kaggle.com/competitions/cassava-leaf-disease-classification/rules" in result["license_url"]
    )


@pytest.mark.asyncio
async def test_train_register_promote_and_infer_with_approved_baseline_model(
    vision_pipeline_db_session,
    tmp_path,
):
    db, org_id = vision_pipeline_db_session
    dataset_root = _write_fixture_dataset(tmp_path / "plantdoc")

    ingested = await vision_dataset_governance_service.ingest_local_directory(
        db,
        org_id,
        dataset_root=dataset_root,
        source_slug="plantdoc",
        dataset_name="PlantDoc tomato governed subset",
        crop="tomato",
        split_seed=17,
        preprocessing_version="vision-preprocess-v1",
        created_by="test",
    )

    assert "error" not in ingested
    assert ingested["dataset"]["classes"] == ["healthy", "late_blight"]
    assert ingested["version"]["license_verified"] is True
    assert PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL in ingested["version"]["allowed_uses"]
    assert ingested["version"]["commercial_use_allowed"] is True
    assert ingested["version"]["manifest_checksum"]
    assert ingested["version"]["class_distribution"] == {"healthy": 4, "late_blight": 4}
    assert ingested["version"]["split_distribution"] == {"test": 2, "train": 4, "val": 2}

    audit_logs = await vision_dataset_governance_service.list_audit_logs(
        db,
        org_id,
        ingested["dataset"]["id"],
    )
    assert [log["event_type"] for log in audit_logs] == [
        "dataset_ingestion_started",
        "dataset_version_created",
    ]

    job = await vision_training_service.create_job(
        db,
        org_id,
        name="Deterministic tomato baseline",
        dataset_id=ingested["dataset"]["id"],
        base_model="sklearn-image-baseline",
        backend=TrainingBackend.SERVER,
        hyperparameters={
            "seed": 123,
            "epochs": 25,
            "confidence_threshold": 0.5,
            "preprocessing_version": "vision-preprocess-v1",
        },
        created_by="test",
    )

    trained = await vision_training_runner.run_job(
        db,
        org_id,
        job["id"],
        artifact_root=tmp_path / "artifacts",
    )

    assert "error" not in trained
    assert trained["status"] == "completed"
    assert trained["model_id"]
    assert trained["metrics"]["test_accuracy"] >= 0.5

    candidate = await vision_model_lifecycle_service.get_model(
        db,
        org_id,
        trained["model_id"],
    )
    assert candidate is not None
    assert candidate["lifecycle_state"] == "candidate"
    assert candidate["artifact_checksum"]
    assert PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL in candidate["allowed_uses"]
    assert candidate["runtime_available"] is False

    candidate_analysis = await vision_inference_service.analyze_image(
        filename="candidate.png",
        content_type="image/png",
        payload=(dataset_root / "Tomato___healthy" / "0.png").read_bytes(),
        organization_id=org_id,
        crop="tomato",
        model=candidate,
    )
    assert candidate_analysis["status"] == "runtime_unavailable"
    assert candidate_analysis["predictions"] == []

    blocked_promotion = await vision_model_lifecycle_service.promote_model(
        db,
        org_id,
        trained["model_id"],
        approved_by="lead",
    )
    assert blocked_promotion["error"] == "Only validated models can be promoted to production"

    validated = await vision_model_lifecycle_service.validate_model(
        db,
        org_id,
        trained["model_id"],
        approved_by="qa",
    )
    assert validated["lifecycle_state"] == "validated"
    assert validated["readiness_score"] > 0

    production = await vision_model_lifecycle_service.promote_model(
        db,
        org_id,
        trained["model_id"],
        approved_by="lead",
    )
    assert production["lifecycle_state"] == "production"
    assert production["runtime_available"] is True

    active = await vision_model_lifecycle_service.get_active_production_model(
        db,
        org_id,
        crop="tomato",
    )
    assert active is not None
    assert active["id"] == trained["model_id"]

    analysis = await vision_inference_service.analyze_image(
        filename="healthy.png",
        content_type="image/png",
        payload=(dataset_root / "Tomato___healthy" / "1.png").read_bytes(),
        organization_id=org_id,
        crop="tomato",
        model=active,
    )

    assert analysis["status"] == "success"
    assert analysis["model"]["id"] == trained["model_id"]
    assert analysis["latency_ms"] >= 0
    assert analysis["predictions"]
    assert analysis["predictions"][0]["label"] in {"healthy", "late_blight"}
    assert 0 <= analysis["predictions"][0]["confidence"] <= 1


@pytest.mark.asyncio
async def test_cassava_policy_allows_open_source_noncommercial_and_blocks_commercial_promotion(
    vision_pipeline_db_session,
    tmp_path,
):
    db, org_id = vision_pipeline_db_session
    dataset_root = _write_fixture_dataset(tmp_path / "cassava")

    ingested = await vision_dataset_governance_service.ingest_local_directory(
        db,
        org_id,
        dataset_root=dataset_root,
        source_slug="cassava-leaf-disease",
        dataset_name="Cassava governed research subset",
        crop="cassava",
        split_seed=23,
        preprocessing_version="vision-preprocess-v1",
        created_by="test",
        project_use=PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
        terms_accepted_by="test",
    )

    assert "error" not in ingested
    assert ingested["version"]["commercial_use_allowed"] is False
    assert ingested["version"]["terms_accepted_by"] == "test"
    assert ingested["version"]["allowed_uses"] == [
        PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
        "academic_research",
    ]

    job = await vision_training_service.create_job(
        db,
        org_id,
        name="Cassava non-commercial baseline",
        dataset_id=ingested["dataset"]["id"],
        base_model="sklearn-image-baseline",
        backend=TrainingBackend.SERVER,
        hyperparameters={
            "seed": 777,
            "epochs": 25,
            "confidence_threshold": 0.5,
        },
        created_by="test",
    )
    trained = await vision_training_runner.run_job(
        db,
        org_id,
        job["id"],
        artifact_root=tmp_path / "cassava-artifacts",
    )
    assert "error" not in trained

    validated = await vision_model_lifecycle_service.validate_model(
        db,
        org_id,
        trained["model_id"],
        approved_by="qa",
    )
    assert validated["commercial_use_allowed"] is False

    blocked_commercial = await vision_model_lifecycle_service.promote_model(
        db,
        org_id,
        trained["model_id"],
        approved_by="lead",
        deployment_mode=PROJECT_USE_COMMERCIAL,
    )
    assert blocked_commercial["error"] == "Model license policy does not allow this deployment mode"

    production = await vision_model_lifecycle_service.promote_model(
        db,
        org_id,
        trained["model_id"],
        approved_by="lead",
        deployment_mode=PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
    )
    assert production["lifecycle_state"] == "production"
    assert production["commercial_use_allowed"] is False


@pytest.mark.asyncio
async def test_registry_promotion_archives_previous_production_and_rolls_back(
    vision_pipeline_db_session,
    tmp_path,
):
    db, org_id = vision_pipeline_db_session
    artifact_dir = tmp_path / "artifact"
    artifact_dir.mkdir()
    (artifact_dir / "model.joblib").write_bytes(b"placeholder")
    manifest = write_artifact_manifest(artifact_dir)

    first = VisionModel(
        organization_id=org_id,
        name="First tomato model",
        description="first",
        version="1.0.0",
        format="sklearn_image_classifier",
        file_path=str(artifact_dir),
        metrics={"test_accuracy": 0.8},
        size_bytes=10,
        lifecycle_state="validated",
        artifact_checksum=manifest["artifact_checksum"],
        label_mapping={"0": "healthy", "1": "late_blight"},
        preprocessing_config={"crop": "tomato", "task": "classification"},
        training_provenance={
            "crop": "tomato",
            "task": "classification",
            "allowed_uses": [PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL],
            "project_use": PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
            "commercial_use_allowed": False,
        },
        readiness_score=80,
    )
    second = VisionModel(
        organization_id=org_id,
        name="Second tomato model",
        description="second",
        version="1.0.1",
        format="sklearn_image_classifier",
        file_path=str(artifact_dir),
        metrics={"test_accuracy": 0.85},
        size_bytes=10,
        lifecycle_state="validated",
        artifact_checksum=manifest["artifact_checksum"],
        label_mapping={"0": "healthy", "1": "late_blight"},
        preprocessing_config={"crop": "tomato", "task": "classification"},
        training_provenance={
            "crop": "tomato",
            "task": "classification",
            "allowed_uses": [PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL],
            "project_use": PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
            "commercial_use_allowed": False,
        },
        readiness_score=85,
    )
    db.add_all([first, second])
    await db.commit()
    await db.refresh(first)
    await db.refresh(second)

    promoted_first = await vision_model_lifecycle_service.promote_model(
        db, org_id, str(first.id), approved_by="lead"
    )
    promoted_second = await vision_model_lifecycle_service.promote_model(
        db, org_id, str(second.id), approved_by="lead"
    )
    rolled_back = await vision_model_lifecycle_service.rollback_to_model(
        db, org_id, str(first.id), approved_by="lead"
    )

    assert promoted_first["lifecycle_state"] == "production"
    assert promoted_second["lifecycle_state"] == "production"
    assert rolled_back["lifecycle_state"] == "production"

    second_after = await vision_model_lifecycle_service.get_model(db, org_id, str(second.id))
    active = await vision_model_lifecycle_service.get_active_production_model(
        db,
        org_id,
        crop="tomato",
    )
    assert second_after["lifecycle_state"] == "archived"
    assert active["id"] == str(first.id)

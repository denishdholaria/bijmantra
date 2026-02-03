import pytest
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.vision import VisionModel, VisionDeployment
from app.services.vision_deployment import vision_deployment_service, ExportFormat, DeploymentTarget
from app.models.base import Base

@pytest.fixture
async def my_db_session():
    # Use in-memory DB for isolation
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )

    # Create only relevant tables
    tables = [
        Base.metadata.tables["vision_models"],
        Base.metadata.tables["vision_deployments"]
    ]

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_factory() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_export_model(my_db_session):
    # Create a dummy source file
    source_path = "/tmp/test_model_source"
    with open(source_path, "w") as f:
        f.write("dummy content")

    # Create a test model
    model = VisionModel(
        organization_id=1,
        name="Test Model",
        version="1.0.0",
        format="savedmodel",
        file_path=source_path,
        metrics={"accuracy": 0.9},
        is_public=False
    )
    my_db_session.add(model)
    await my_db_session.commit()
    await my_db_session.refresh(model)

    # Call export
    result = await vision_deployment_service.export_model(
        my_db_session,
        organization_id=1,
        model_id=str(model.id),
        format=ExportFormat.TFLITE
    )

    assert "error" not in result
    assert result["format"] == ExportFormat.TFLITE
    assert result["model_id"] == str(model.id)
    assert result["download_url"] is not None
    assert "size_mb" in result

@pytest.mark.asyncio
async def test_deploy_model(my_db_session):
    # Create a test model
    model = VisionModel(
        organization_id=1,
        name="Test Model 2",
        version="1.0.0",
        format="savedmodel",
        file_path="/tmp/test_model_source_2",
    )
    my_db_session.add(model)
    await my_db_session.commit()
    await my_db_session.refresh(model)

    # Call deploy
    result = await vision_deployment_service.deploy_model(
        my_db_session,
        organization_id=1,
        model_id=str(model.id),
        target=DeploymentTarget.BROWSER,
        format=ExportFormat.TFJS
    )

    assert "error" not in result
    assert result["status"] == "active"
    assert result["target"] == DeploymentTarget.BROWSER

    # Verify DB
    deploy_id = result["id"]
    deployment = await vision_deployment_service.get_deployment(
        my_db_session,
        organization_id=1,
        deploy_id=str(deploy_id)
    )
    assert deployment is not None
    assert deployment["id"] == deploy_id

    # List deployments
    deployments = await vision_deployment_service.list_deployments(
        my_db_session,
        organization_id=1,
        model_id=str(model.id)
    )
    assert len(deployments) == 1
    assert deployments[0]["id"] == deploy_id

    # Undeploy
    success = await vision_deployment_service.undeploy(
        my_db_session,
        organization_id=1,
        deploy_id=str(deploy_id)
    )
    assert success is True

    deployment = await vision_deployment_service.get_deployment(
        my_db_session,
        organization_id=1,
        deploy_id=str(deploy_id)
    )
    assert deployment is None

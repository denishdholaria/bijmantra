import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC
from app.services.phenology import PhenologyService
from app.models.phenology import PhenologyRecord, PhenologyObservation

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock() # add is synchronous in SQLAlchemy AsyncSession
    return db

@pytest.fixture
def phenology_service():
    return PhenologyService()

@pytest.mark.asyncio
async def test_create_record(mock_db, phenology_service):
    # Setup
    organization_id = 1
    data = {
        "germplasm_id": "germplasm-uuid",
        "germplasm_name": "Test Germplasm",
        "study_id": "study-uuid",
        "plot_id": "plot-1",
        "sowing_date": "2023-01-01T00:00:00Z",
        "current_stage": 10,
        "expected_maturity": 120,
        "crop": "rice"
    }

    # Mock resolution of FKs: first call for germplasm, second for study
    mock_db.scalar.side_effect = [100, 200]

    # Act
    result = await phenology_service.create_record(mock_db, organization_id, data)

    # Assert
    assert result["germplasm_name"] == "Test Germplasm"
    assert result["current_stage"] == 10
    # days_from_sowing should be calculated
    assert result["days_from_sowing"] is not None
    assert "id" in result
    assert result["id"].startswith("phen-")

    # Verify DB calls
    assert mock_db.add.called
    assert mock_db.commit.called
    assert mock_db.refresh.called

    # Verify FK resolution queries were made
    # We expect 2 calls to scalar (one for germplasm query, one for study query)
    assert mock_db.scalar.call_count == 2

@pytest.mark.asyncio
async def test_get_record(mock_db, phenology_service):
    # Setup
    organization_id = 1
    record_id = "phen-1234"

    mock_record = PhenologyRecord(
        id=1,
        record_db_id=record_id,
        organization_id=organization_id,
        current_stage=20,
        current_stage_name="Tillering",
        created_at=datetime.now(UTC)
    )

    # Mock execute results
    # 1. get_record query
    mock_result_record = MagicMock()
    mock_result_record.scalar_one_or_none.return_value = mock_record

    # 2. get_observations query
    mock_obs = PhenologyObservation(
        observation_db_id="obs-1",
        stage=20,
        date="2023-02-01",
        notes="Growing well"
    )
    mock_result_obs = MagicMock()
    mock_result_obs.scalars.return_value.all.return_value = [mock_obs]

    mock_db.execute.side_effect = [mock_result_record, mock_result_obs]

    # Act
    result = await phenology_service.get_record(mock_db, organization_id, record_id)

    # Assert
    assert result is not None
    assert result["id"] == record_id
    assert result["current_stage"] == 20
    assert len(result["observations"]) == 1
    assert result["observations"][0]["id"] == "obs-1"

@pytest.mark.asyncio
async def test_update_record(mock_db, phenology_service):
    # Setup
    organization_id = 1
    record_id = "phen-1234"
    data = {"current_stage": 30}

    mock_record = PhenologyRecord(
        id=1,
        record_db_id=record_id,
        organization_id=organization_id,
        current_stage=20,
        created_at=datetime.now(UTC)
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_record
    mock_db.execute.return_value = mock_result

    # Act
    result = await phenology_service.update_record(mock_db, organization_id, record_id, data)

    # Assert
    assert result["current_stage"] == 30
    assert result["current_stage_name"] == "Stem Elongation" # 30 maps to Stem Elongation in GROWTH_STAGES
    assert mock_db.commit.called
    assert mock_db.refresh.called

@pytest.mark.asyncio
async def test_record_observation(mock_db, phenology_service):
    # Setup
    organization_id = 1
    record_id = "phen-1234"
    data = {"stage": 30, "notes": "New stage reached"}

    mock_record = PhenologyRecord(
        id=1,
        record_db_id=record_id,
        organization_id=organization_id,
        created_at=datetime.now(UTC)
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_record
    mock_db.execute.return_value = mock_result

    # Act
    result = await phenology_service.record_observation(mock_db, organization_id, record_id, data)

    # Assert
    assert result["stage"] == 30
    assert result["notes"] == "New stage reached"
    assert result["id"].startswith("obs-")
    assert mock_db.add.called
    assert mock_db.commit.called

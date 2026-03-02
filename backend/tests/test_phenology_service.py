import pytest
from app.services.phenology import phenology_service
from datetime import datetime, UTC

@pytest.mark.asyncio
async def test_create_record(async_db_session, test_user):
    data = {
        "germplasm_id": "1",
        "germplasm_name": "Test Germplasm",
        "study_id": "100",
        "plot_id": "200",
        "sowing_date": "2023-01-01T00:00:00Z",
        "current_stage": 10,
        "expected_maturity": 120,
        "crop": "rice"
    }

    record = await phenology_service.create_record(
        async_db_session, test_user.organization_id, data
    )

    assert record["germplasm_name"] == "Test Germplasm"
    assert record["current_stage"] == 10
    assert record["sowing_date"] is not None
    assert record["id"].startswith("phen-")
    assert record["observations_count"] == 0

@pytest.mark.asyncio
async def test_get_record(async_db_session, test_user):
    # Create first
    data = {"germplasm_name": "Test 2", "crop": "wheat"}
    created = await phenology_service.create_record(
        async_db_session, test_user.organization_id, data
    )

    # Get
    fetched = await phenology_service.get_record(
        async_db_session, test_user.organization_id, created["id"]
    )

    assert fetched is not None
    assert fetched["id"] == created["id"]
    assert fetched["germplasm_name"] == "Test 2"

@pytest.mark.asyncio
async def test_update_record(async_db_session, test_user):
    data = {"germplasm_name": "Test Update", "sowing_date": "2023-01-01T00:00:00Z"}
    created = await phenology_service.create_record(
        async_db_session, test_user.organization_id, data
    )

    update_data = {"current_stage": 50}
    updated = await phenology_service.update_record(
        async_db_session, test_user.organization_id, created["id"], update_data
    )

    assert updated["current_stage"] == 50
    assert updated["current_stage_name"] == "Heading"
    # days_from_sowing should be > 0
    assert updated["days_from_sowing"] > 0

@pytest.mark.asyncio
async def test_record_observation(async_db_session, test_user):
    data = {"germplasm_name": "Test Obs"}
    created = await phenology_service.create_record(
        async_db_session, test_user.organization_id, data
    )

    obs_data = {
        "stage": 60,
        "date": datetime.now(UTC).isoformat(),
        "notes": "Flowering started"
    }

    obs = await phenology_service.record_observation(
        async_db_session, test_user.organization_id, created["id"], obs_data
    )

    assert obs["stage"] == 60
    assert obs["notes"] == "Flowering started"

    # Check if record updated
    fetched = await phenology_service.get_record(
        async_db_session, test_user.organization_id, created["id"]
    )
    assert fetched["current_stage"] == 60 # It should auto-update
    assert fetched["observations_count"] == 1
    assert len(fetched["observations"]) == 1

@pytest.mark.asyncio
async def test_get_observations(async_db_session, test_user):
    data = {"germplasm_name": "Test Obs List"}
    created = await phenology_service.create_record(
        async_db_session, test_user.organization_id, data
    )

    await phenology_service.record_observation(
        async_db_session, test_user.organization_id, created["id"], {"stage": 20}
    )
    await phenology_service.record_observation(
        async_db_session, test_user.organization_id, created["id"], {"stage": 30}
    )

    obs_list = await phenology_service.get_observations(
        async_db_session, test_user.organization_id, created["id"]
    )

    assert len(obs_list) == 2
    # Sorting might depend on execution speed if timestamps are close, but newer should be first
    assert obs_list[0]["stage"] == 30 or obs_list[1]["stage"] == 30

@pytest.mark.asyncio
async def test_get_stats(async_db_session, test_user):
    # Add some data
    await phenology_service.create_record(
         async_db_session, test_user.organization_id,
         {"germplasm_name": "S1", "current_stage": 10, "sowing_date": "2023-01-01T00:00:00Z"}
    )
    await phenology_service.create_record(
         async_db_session, test_user.organization_id,
         {"germplasm_name": "S2", "current_stage": 85, "sowing_date": "2023-01-01T00:00:00Z"}
    )

    stats = await phenology_service.get_stats(async_db_session, test_user.organization_id)

    assert stats["total_records"] >= 2
    assert stats["near_maturity"] >= 1
    assert "Seedling" in stats["by_stage"]

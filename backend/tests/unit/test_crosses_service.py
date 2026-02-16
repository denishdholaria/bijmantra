import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.cross_service import CrossService
from app.schemas.germplasm import CrossCreate, CrossUpdate

@pytest.mark.asyncio
async def test_create_cross():
    # Mock DB session
    db = AsyncMock()
    # Mock execute result for lookups
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    cross_data = CrossCreate(
        crossName="Test Cross",
        crossType="BIPARENTAL",
        crossingYear=2024
    )

    cross = await CrossService.create_cross(db, cross_data, organization_id=1)

    assert cross.cross_name == "Test Cross"
    assert cross.cross_type == "BIPARENTAL"
    assert cross.organization_id == 1
    assert cross.cross_db_id.startswith("cross_")

    # Verify DB add and flush called
    assert db.add.called
    assert db.flush.called
    assert db.refresh.called

@pytest.mark.asyncio
async def test_get_stats():
    db = AsyncMock()

    # Mock execute results for 4 queries (Total, Season, Success, Pending)
    # execute returns a Result object, on which scalar() is called.

    # Create distinct result mocks for each call
    result_total = MagicMock()
    result_total.scalar.return_value = 10

    result_season = MagicMock()
    result_season.scalar.return_value = 5

    result_success = MagicMock()
    result_success.scalar.return_value = 3

    result_pending = MagicMock()
    result_pending.scalar.return_value = 2

    db.execute.side_effect = [result_total, result_season, result_success, result_pending]

    stats = await CrossService.get_stats(db, organization_id=1)

    assert stats.totalCount == 10
    assert stats.thisSeasonCount == 5
    assert stats.successfulCount == 3
    assert stats.pendingCount == 2

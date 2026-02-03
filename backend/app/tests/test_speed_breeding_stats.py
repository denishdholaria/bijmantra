from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.speed_breeding import SpeedBreedingChamber
from app.services.speed_breeding import SpeedBreedingService


@pytest.mark.asyncio
async def test_get_chamber_statistics():
    service = SpeedBreedingService()
    db = AsyncMock()
    organization_id = 1

    # Mock chambers
    chamber1 = SpeedBreedingChamber(id=1, organization_id=organization_id, status="active", capacity=100)
    chamber2 = SpeedBreedingChamber(id=2, organization_id=organization_id, status="maintenance", capacity=200)
    chamber3 = SpeedBreedingChamber(id=3, organization_id=organization_id, status="active", capacity=100)

    # Mock result for chambers query
    chambers_result = MagicMock()
    chambers_result.scalars.return_value.all.return_value = [chamber1, chamber2, chamber3]

    # Mock active batches entries
    # batch1: 50 entries, batch2: 30 entries
    entries_result = MagicMock()
    entries_result.scalars.return_value.all.return_value = [50, 30]

    # Configure db.execute side_effect to return different results for sequential calls
    db.execute.side_effect = [chambers_result, entries_result]

    stats = await service.get_chamber_statistics(db, organization_id)

    assert stats["total_chambers"] == 3
    assert stats["active_chambers"] == 2
    assert stats["maintenance_chambers"] == 1
    assert stats["offline_chambers"] == 0
    assert stats["total_capacity"] == 400 # 100 + 200 + 100
    assert stats["used_capacity"] == 80 # 50 + 30
    assert stats["utilization_percentage"] == 20.0 # (80/400)*100

@pytest.mark.asyncio
async def test_get_chamber_statistics_empty():
    service = SpeedBreedingService()
    db = AsyncMock()
    organization_id = 1

    # Mock empty chambers
    chambers_result = MagicMock()
    chambers_result.scalars.return_value.all.return_value = []

    # Mock empty batches
    entries_result = MagicMock()
    entries_result.scalars.return_value.all.return_value = []

    db.execute.side_effect = [chambers_result, entries_result]

    stats = await service.get_chamber_statistics(db, organization_id)

    assert stats["total_chambers"] == 0
    assert stats["total_capacity"] == 0
    assert stats["used_capacity"] == 0
    assert stats["utilization_percentage"] == 0.0

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(test_get_chamber_statistics())
        asyncio.run(test_get_chamber_statistics_empty())
        print("Tests passed")
    except Exception as e:
        print(f"Tests failed: {e}")

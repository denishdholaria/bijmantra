from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.speed_breeding import SpeedBreedingProtocol
from app.schemas.speed_breeding import SpeedBreedingProtocolCreate
from app.services.speed_breeding import SpeedBreedingService


@pytest.mark.asyncio
async def test_create_protocol():
    service = SpeedBreedingService()
    db = AsyncMock()

    protocol_in = SpeedBreedingProtocolCreate(
        name="Test Protocol",
        crop="Wheat",
        days_to_harvest=60,
        days_to_flower=30,
        generations_per_year=6
    )

    organization_id = 1

    # Mock db.add and db.commit
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    result = await service.create_protocol(db, organization_id, protocol_in)

    assert result.name == "Test Protocol"
    assert result.organization_id == organization_id
    db.add.assert_called_once()
    db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_calculate_timeline():
    service = SpeedBreedingService()
    db = AsyncMock()
    organization_id = 1

    # Mock get_protocol
    mock_protocol = SpeedBreedingProtocol(
        id=1,
        name="Test Protocol",
        crop="Wheat",
        days_to_harvest=60,
        days_to_flower=30,
        generations_per_year=6
    )
    service.get_protocol = AsyncMock(return_value=mock_protocol)

    result = await service.calculate_timeline(db, organization_id, "1", "F3", "2023-01-01")

    assert result["protocol"] == "Test Protocol"
    assert result["target_generation"] == "F3"
    assert len(result["timeline"]) == 3
    assert result["timeline"][0]["generation"] == "F1"
    assert result["timeline"][1]["generation"] == "F2"
    assert result["timeline"][2]["generation"] == "F3"

if __name__ == "__main__":
    # If run as script, use asyncio to run test functions
    import asyncio
    try:
        asyncio.run(test_create_protocol())
        asyncio.run(test_calculate_timeline())
        print("Tests passed")
    except Exception as e:
        print(f"Tests failed: {e}")

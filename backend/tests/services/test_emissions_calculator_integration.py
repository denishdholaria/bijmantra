import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.emissions_calculator_service import EmissionsCalculatorService
from app.models.climate import EmissionSource, EmissionCategory
from app.models.phenotyping import Observation, ObservationVariable

@pytest.mark.asyncio
async def test_calculate_variety_footprint_with_yield():
    """Test calculating variety footprint with actual yield data from observations"""

    # Mock dependencies
    service = EmissionsCalculatorService()
    db = AsyncMock(spec=AsyncSession)

    # Mock emissions data
    emission_sources = [
        EmissionSource(
            id=1,
            organization_id=1,
            co2e_emissions=100.0,
            category=EmissionCategory.FERTILIZER
        ),
        EmissionSource(
            id=2,
            organization_id=1,
            co2e_emissions=50.0,
            category=EmissionCategory.FUEL
        )
    ]

    # Mock get_emission_sources to return our mock emissions
    service.get_emission_sources = AsyncMock(return_value=emission_sources)

    # Mock observations query result
    # We expect query for yield values
    # Scenario: 2 yield observations: "5000", "6000" -> Average 5500
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = ["5000", "6000"]
    db.execute.return_value = mock_result

    # Run method
    footprint = await service.calculate_variety_footprint(
        db=db,
        organization_id=1,
        germplasm_id=101,
        trial_id=201,
        study_id=301,
        location_id=401
    )

    # Assertions
    assert footprint is not None
    assert footprint.total_emissions == 150.0  # 100 + 50
    assert footprint.total_yield == 5500.0  # Average of 5000 and 6000

    # CI = 150 / 5500 = 0.02727
    assert footprint.carbon_intensity == pytest.approx(0.02727, rel=0.001)

    # Verify DB interaction
    # 1. Called get_emission_sources
    service.get_emission_sources.assert_called_once_with(
        db, 1, trial_id=201, study_id=301
    )

    # 2. Called execute for observations
    # We can't easily verify the exact SQL string but we can verify it was called
    assert db.execute.called

@pytest.mark.asyncio
async def test_calculate_variety_footprint_no_yield():
    """Test calculating variety footprint when no yield data exists"""

    service = EmissionsCalculatorService()
    db = AsyncMock(spec=AsyncSession)

    # Mock emissions
    service.get_emission_sources = AsyncMock(return_value=[
        EmissionSource(co2e_emissions=100.0, category=EmissionCategory.FERTILIZER)
    ])

    # Mock empty observations
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    footprint = await service.calculate_variety_footprint(
        db=db,
        organization_id=1,
        germplasm_id=101,
        trial_id=201,
        study_id=301,
        location_id=401
    )

    assert footprint.total_yield == 0.0
    assert footprint.carbon_intensity == 0.0  # Should handle division by zero or return 0

@pytest.mark.asyncio
async def test_calculate_variety_footprint_invalid_yield_values():
    """Test handling of non-numeric yield values"""

    service = EmissionsCalculatorService()
    db = AsyncMock(spec=AsyncSession)

    # Mock emissions
    service.get_emission_sources = AsyncMock(return_value=[
        EmissionSource(co2e_emissions=100.0, category=EmissionCategory.FERTILIZER)
    ])

    # Mock invalid observations
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = ["5000", "invalid", "6000"]
    db.execute.return_value = mock_result

    footprint = await service.calculate_variety_footprint(
        db=db,
        organization_id=1,
        germplasm_id=101,
        trial_id=201,
        study_id=301,
        location_id=401
    )

    # Should ignore "invalid" and average 5000 and 6000
    assert footprint.total_yield == 5500.0
    assert footprint.carbon_intensity == pytest.approx(100.0 / 5500.0, rel=0.001)

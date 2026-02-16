"""
Unit tests for Soil Moisture API
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.api.v2.future.soil_moisture import (
    list_soil_moisture_readings,
    create_soil_moisture_reading,
    get_device_readings
)
from app.schemas.future.water_irrigation import SoilMoistureReadingCreate

class TestSoilMoistureApi:
    """Test suite for Soil Moisture API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.mock_db = AsyncMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.organization_id = 1
        self.mock_user.is_active = True

    @pytest.mark.asyncio
    async def test_list_readings(self):
        # Arrange
        mock_data = [
            MagicMock(
                id=1, device_id=1, reading_timestamp=datetime.now(),
                depth_cm=10, volumetric_water_content=0.3,
                organization_id=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]

        # Patch CRUD
        from app.crud.future import soil_moisture
        original_get_multi = soil_moisture.soil_moisture.get_multi
        soil_moisture.soil_moisture.get_multi = AsyncMock(return_value=(mock_data, 1))

        try:
            # Act
            result = await list_soil_moisture_readings(
                skip=0, limit=100, db=self.mock_db, org_id=1
            )

            # Assert
            assert len(result) == 1
            assert result[0].id == 1
        finally:
             soil_moisture.soil_moisture.get_multi = original_get_multi

    @pytest.mark.asyncio
    async def test_create_reading(self):
        # Arrange
        reading_in = SoilMoistureReadingCreate(
            device_id=1,
            reading_timestamp=datetime.now(),
            depth_cm=30,
            volumetric_water_content=0.25
        )

        mock_created = MagicMock(
            id=1,
            **reading_in.model_dump(),
            organization_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        from app.crud.future import soil_moisture
        original_create = soil_moisture.soil_moisture.create
        soil_moisture.soil_moisture.create = AsyncMock(return_value=mock_created)

        try:
            # Act
            result = await create_soil_moisture_reading(
                reading_in, db=self.mock_db, current_user=self.mock_user
            )

            # Assert
            assert result.id == 1
            assert result.volumetric_water_content == 0.25
        finally:
            soil_moisture.soil_moisture.create = original_create

    @pytest.mark.asyncio
    async def test_get_device_readings(self):
         # Arrange
        mock_data = [
            MagicMock(
                id=1, device_id=123, reading_timestamp=datetime.now(),
                depth_cm=10, volumetric_water_content=0.3,
                organization_id=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]

        from app.crud.future import soil_moisture
        original_get_by_device = soil_moisture.soil_moisture.get_by_device
        soil_moisture.soil_moisture.get_by_device = AsyncMock(return_value=mock_data)

        try:
            # Act
            result = await get_device_readings(
                device_id=123, db=self.mock_db, org_id=1
            )

            # Assert
            assert len(result) == 1
            assert result[0].device_id == 123
        finally:
            soil_moisture.soil_moisture.get_by_device = original_get_by_device

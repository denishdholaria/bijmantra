"""
Unit tests for Crop Calendar API
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
from app.api.v2.future.crop_calendar import list_crop_calendars

class TestCropCalendarApi:
    """Test suite for Crop Calendar API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for db and user dependencies for each test."""
        self.mock_db = AsyncMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.organization_id = 1
        self.mock_user.email = "test@example.com"
        
        self.mock_execute = self.mock_db.execute
        self.mock_scalar_one_or_none = MagicMock()
        self.mock_execute.return_value.scalar_one_or_none = self.mock_scalar_one_or_none

    @pytest.mark.asyncio
    async def test_list_crop_calendars_returns_empty_list(self):
        """Test that list_crop_calendars returns an empty list when no calendars exist."""
        # Arrange
        async def mock_get_multi(*args, **kwargs):
            return [], 0
        
        # Replace the original crud method with the mock
        from app.crud.future import crop_calendar
        crop_calendar.crop_calendar.get_multi = mock_get_multi

        # Act
        response = await list_crop_calendars(
            page=0, 
            page_size=10, 
            db=self.mock_db, 
            org_id=self.mock_user.organization_id
        )

        # Assert
        assert response.metadata.pagination.total_count == 0
        assert response.result['data'] == []

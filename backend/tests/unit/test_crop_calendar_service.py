import unittest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
# Add backend to path
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

# Import app.models to register all models and relationships
import app.models

from app.modules.crop_calendar.service import CropCalendarService
from app.modules.crop_calendar.schemas import (
    ActivityTypeCreate, ScheduleEventCreate, ResourceRequirementCreate, HarvestWindowCreate
)
from app.modules.crop_calendar.models import (
    ActivityType, ScheduleEvent, CropCalendar, ResourceRequirement, HarvestWindow
)
from datetime import date

class TestCropCalendarService(unittest.IsolatedAsyncioTestCase):
    async def test_create_activity_type(self):
        # Mock DB session
        mock_db = AsyncMock(spec=AsyncSession)
        service = CropCalendarService(mock_db)

        # Input data
        data = ActivityTypeCreate(name="Sowing", description="Planting seeds")
        organization_id = 1

        # Call method
        result = await service.create_activity_type(data, organization_id)

        # Assertions
        self.assertIsInstance(result, ActivityType)
        self.assertEqual(result.name, "Sowing")
        self.assertEqual(result.organization_id, organization_id)

        # Verify DB interactions
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    async def test_create_schedule_event(self):
        # Mock DB session
        mock_db = AsyncMock(spec=AsyncSession)
        service = CropCalendarService(mock_db)

        # Mock get_crop_calendar
        mock_calendar = CropCalendar(id=1, organization_id=1)
        service.get_crop_calendar = AsyncMock(return_value=mock_calendar)

        # Input data
        data = ScheduleEventCreate(
            calendar_id=1,
            activity_name="Sowing",
            scheduled_date=date(2025, 6, 1)
        )
        organization_id = 1

        # Call method
        result = await service.create_schedule_event(data, organization_id)

        # Assertions
        self.assertIsInstance(result, ScheduleEvent)
        self.assertEqual(result.activity_name, "Sowing")
        self.assertEqual(result.organization_id, organization_id)

        # Verify DB interactions
        self.assertTrue(mock_db.add.called)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    async def test_add_resource_requirement(self):
        # Mock DB session
        mock_db = AsyncMock(spec=AsyncSession)
        service = CropCalendarService(mock_db)

        # Mock get_schedule_event
        mock_event = ScheduleEvent(id=1, organization_id=1)
        service.get_schedule_event = AsyncMock(return_value=mock_event)

        # Input data
        data = ResourceRequirementCreate(
            resource_type="Fertilizer",
            resource_name="Urea",
            quantity=100.0,
            unit="kg"
        )
        organization_id = 1
        event_id = 1

        # Call method
        result = await service.add_resource_requirement(event_id, data, organization_id)

        # Assertions
        self.assertIsInstance(result, ResourceRequirement)
        self.assertEqual(result.resource_name, "Urea")
        self.assertEqual(result.organization_id, organization_id)

        # Verify DB interactions
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    async def test_add_harvest_window(self):
        # Mock DB session
        mock_db = AsyncMock(spec=AsyncSession)
        service = CropCalendarService(mock_db)

        # Mock get_crop_calendar
        mock_calendar = CropCalendar(id=1, organization_id=1)
        service.get_crop_calendar = AsyncMock(return_value=mock_calendar)

        # Input data
        data = HarvestWindowCreate(
            calendar_id=1,
            window_start=date(2025, 10, 1),
            window_end=date(2025, 10, 15),
            predicted_yield=5000.0
        )
        organization_id = 1

        # Call method
        result = await service.add_harvest_window(data, organization_id)

        # Assertions
        self.assertIsInstance(result, HarvestWindow)
        self.assertEqual(result.predicted_yield, 5000.0)
        self.assertEqual(result.organization_id, organization_id)

        # Verify DB interactions
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

if __name__ == '__main__':
    unittest.main()

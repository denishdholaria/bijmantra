"""
CRUD operations for Irrigation Schedule
"""

from typing import List
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.irrigation_schedule import IrrigationSchedule
from app.schemas.future.water_irrigation import IrrigationScheduleCreate, IrrigationScheduleUpdate


class CRUDIrrigationSchedule(CRUDBase[IrrigationSchedule, IrrigationScheduleCreate, IrrigationScheduleUpdate]):
    """CRUD operations for IrrigationSchedule"""

    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> List[IrrigationSchedule]:
        """Get all irrigation schedules for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.schedule_date.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_upcoming(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int,
        days_ahead: int = 7
    ) -> List[IrrigationSchedule]:
        """Get upcoming irrigation schedules for a field."""
        from datetime import timedelta
        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id,
            self.model.schedule_date >= today,
            self.model.schedule_date <= end_date
        ).order_by(self.model.schedule_date)

        result = await db.execute(query)
        return list(result.scalars().all())


irrigation_schedule = CRUDIrrigationSchedule(IrrigationSchedule)

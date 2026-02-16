"""
CRUD operations for Growing Degree Day Log
"""

from typing import List, Optional
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.gdd_log import GrowingDegreeDayLog
from app.schemas.future.crop_intelligence import GrowingDegreeDayLogCreate, GrowingDegreeDayLogUpdate


class CRUDGrowingDegreeDayLog(CRUDBase[GrowingDegreeDayLog, GrowingDegreeDayLogCreate, GrowingDegreeDayLogUpdate]):
    """CRUD operations for GrowingDegreeDayLog"""

    async def get_by_field_and_date_range(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        start_date: date,
        end_date: date,
        org_id: int
    ) -> List[GrowingDegreeDayLog]:
        """Get GDD logs for a field within a date range."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id,
            self.model.log_date >= start_date,
            self.model.log_date <= end_date
        ).order_by(self.model.log_date)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_cumulative_summary(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> dict:
        """Get cumulative GDD summary for a field."""
        query = select(
            func.max(self.model.cumulative_gdd).label("total_gdd"),
            func.min(self.model.log_date).label("start_date"),
            func.max(self.model.log_date).label("end_date"),
            func.count(self.model.id).label("days_logged")
        ).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        )

        result = await db.execute(query)
        row = result.one_or_none()

        if row:
            return {
                "total_gdd": row.total_gdd or 0,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "days_logged": row.days_logged
            }
        return {"total_gdd": 0, "start_date": None, "end_date": None, "days_logged": 0}


gdd_log = CRUDGrowingDegreeDayLog(GrowingDegreeDayLog)

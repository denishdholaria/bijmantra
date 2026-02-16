"""
CRUD operations for Soil Health Score
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.soil_health_score import SoilHealthScore
from app.schemas.future.soil_nutrients import SoilHealthScoreBase, SoilHealthScoreCreate


class CRUDSoilHealthScore(CRUDBase[SoilHealthScore, SoilHealthScoreCreate, SoilHealthScoreBase]):
    """CRUD operations for SoilHealthScore"""

    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> List[SoilHealthScore]:
        """Get all health scores for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.assessment_date.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_latest_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> Optional[SoilHealthScore]:
        """Get the most recent health score for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.assessment_date.desc()).limit(1)

        result = await db.execute(query)
        return result.scalar_one_or_none()


soil_health = CRUDSoilHealthScore(SoilHealthScore)

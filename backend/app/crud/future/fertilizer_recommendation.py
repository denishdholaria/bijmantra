"""
CRUD operations for Fertilizer Recommendation
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.fertilizer_recommendation import FertilizerRecommendation
from app.schemas.future.soil_nutrients import FertilizerRecommendationBase, FertilizerRecommendationCreate


class CRUDFertilizerRecommendation(CRUDBase[FertilizerRecommendation, FertilizerRecommendationCreate, FertilizerRecommendationBase]):
    """CRUD operations for FertilizerRecommendation"""

    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> List[FertilizerRecommendation]:
        """Get all recommendations for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_soil_test(
        self,
        db: AsyncSession,
        *,
        soil_test_id: int,
        org_id: int
    ) -> List[FertilizerRecommendation]:
        """Get recommendations based on a soil test."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.soil_test_id == soil_test_id
        )

        result = await db.execute(query)
        return list(result.scalars().all())


fertilizer_recommendation = CRUDFertilizerRecommendation(FertilizerRecommendation)

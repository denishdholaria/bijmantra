"""
CRUD operations for Yield Prediction
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.yield_prediction import YieldPrediction
from app.schemas.future.crop_intelligence import YieldPredictionBase, YieldPredictionCreate


class CRUDYieldPrediction(CRUDBase[YieldPrediction, YieldPredictionCreate, YieldPredictionBase]):
    """CRUD operations for YieldPrediction"""

    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> List[YieldPrediction]:
        """Get all predictions for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.prediction_date.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_trial(
        self,
        db: AsyncSession,
        *,
        trial_id: int,
        org_id: int
    ) -> List[YieldPrediction]:
        """Get all predictions for a trial."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.trial_id == trial_id
        ).order_by(self.model.prediction_date.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_latest_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> Optional[YieldPrediction]:
        """Get the most recent prediction for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.prediction_date.desc()).limit(1)

        result = await db.execute(query)
        return result.scalar_one_or_none()


yield_prediction = CRUDYieldPrediction(YieldPrediction)

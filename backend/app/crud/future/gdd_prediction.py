"""
CRUD operations for GDD Prediction
"""

from typing import List
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.gdd_prediction import GDDPrediction
from app.schemas.future.gdd_prediction import GDDPredictionCreate, GDDPredictionUpdate


class CRUDGDDPrediction(CRUDBase[GDDPrediction, GDDPredictionCreate, GDDPredictionUpdate]):
    """CRUD operations for GDDPrediction"""

    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[GDDPrediction]:
        """Get predictions for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.prediction_date.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())


gdd_prediction = CRUDGDDPrediction(GDDPrediction)

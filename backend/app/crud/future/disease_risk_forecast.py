"""
CRUD operations for Disease Risk Forecast
"""

from typing import List
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.disease_risk_forecast import DiseaseRiskForecast
from app.schemas.future.crop_protection import DiseaseRiskForecastBase, DiseaseRiskForecastCreate


class CRUDDiseaseRiskForecast(CRUDBase[DiseaseRiskForecast, DiseaseRiskForecastCreate, DiseaseRiskForecastBase]):
    """CRUD operations for DiseaseRiskForecast"""

    async def get_active_forecasts(
        self,
        db: AsyncSession,
        *,
        org_id: int
    ) -> List[DiseaseRiskForecast]:
        """Get all active (current) disease risk forecasts."""
        today = date.today()
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.forecast_date >= today
        ).order_by(self.model.risk_level.desc(), self.model.forecast_date)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> List[DiseaseRiskForecast]:
        """Get all forecasts for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.forecast_date.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_high_risk(
        self,
        db: AsyncSession,
        *,
        org_id: int
    ) -> List[DiseaseRiskForecast]:
        """Get high-risk forecasts."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.risk_level == "HIGH"
        ).order_by(self.model.forecast_date)

        result = await db.execute(query)
        return list(result.scalars().all())


disease_risk_forecast = CRUDDiseaseRiskForecast(DiseaseRiskForecast)

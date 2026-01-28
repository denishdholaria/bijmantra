"""
CRUD operations for Water Balance
"""

from typing import List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.water_balance import WaterBalance
from app.schemas.future.water_irrigation import WaterBalanceBase, WaterBalanceCreate


class CRUDWaterBalance(CRUDBase[WaterBalance, WaterBalanceCreate, WaterBalanceBase]):
    """CRUD operations for WaterBalance"""
    
    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> List[WaterBalance]:
        """Get all water balance records for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.calculation_date.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_field_summary(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> dict:
        """Get water balance summary for a field."""
        query = select(
            func.sum(self.model.precipitation_mm).label("total_precipitation"),
            func.sum(self.model.irrigation_mm).label("total_irrigation"),
            func.sum(self.model.evapotranspiration_mm).label("total_et"),
            func.avg(self.model.soil_moisture_percent).label("avg_soil_moisture"),
            func.count(self.model.id).label("record_count")
        ).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        )
        
        result = await db.execute(query)
        row = result.one_or_none()
        
        if row:
            return {
                "total_precipitation_mm": float(row.total_precipitation or 0),
                "total_irrigation_mm": float(row.total_irrigation or 0),
                "total_evapotranspiration_mm": float(row.total_et or 0),
                "average_soil_moisture_percent": float(row.avg_soil_moisture or 0),
                "record_count": row.record_count
            }
        return {
            "total_precipitation_mm": 0,
            "total_irrigation_mm": 0,
            "total_evapotranspiration_mm": 0,
            "average_soil_moisture_percent": 0,
            "record_count": 0
        }


water_balance = CRUDWaterBalance(WaterBalance)

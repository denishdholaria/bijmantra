"""
CRUD operations for Carbon Sequestration
"""

from typing import List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.carbon_sequestration import CarbonSequestration
from app.schemas.future.soil_nutrients import CarbonSequestrationBase, CarbonSequestrationCreate


class CRUDCarbonSequestration(CRUDBase[CarbonSequestration, CarbonSequestrationCreate, CarbonSequestrationBase]):
    """CRUD operations for CarbonSequestration"""
    
    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> List[CarbonSequestration]:
        """Get all carbon records for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.measurement_date.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_field_summary(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> dict:
        """Get carbon sequestration summary for a field."""
        query = select(
            func.sum(self.model.carbon_sequestered_tonnes).label("total_sequestered"),
            func.avg(self.model.soil_organic_carbon_percent).label("avg_soc"),
            func.count(self.model.id).label("measurement_count")
        ).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        )
        
        result = await db.execute(query)
        row = result.one_or_none()
        
        if row:
            return {
                "total_sequestered_tonnes": float(row.total_sequestered or 0),
                "average_soc_percent": float(row.avg_soc or 0),
                "measurement_count": row.measurement_count
            }
        return {"total_sequestered_tonnes": 0, "average_soc_percent": 0, "measurement_count": 0}


carbon_sequestration = CRUDCarbonSequestration(CarbonSequestration)

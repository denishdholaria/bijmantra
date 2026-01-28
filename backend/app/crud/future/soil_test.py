"""
CRUD operations for Soil Test
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.soil_test import SoilTest
from app.schemas.future.soil_nutrients import SoilTestCreate, SoilTestUpdate


class CRUDSoilTest(CRUDBase[SoilTest, SoilTestCreate, SoilTestUpdate]):
    """CRUD operations for SoilTest"""
    
    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> List[SoilTest]:
        """Get all soil tests for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.sample_date.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())


soil_test = CRUDSoilTest(SoilTest)

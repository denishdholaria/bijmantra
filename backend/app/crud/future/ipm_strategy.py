"""
CRUD operations for IPM Strategy
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.ipm_strategy import IPMStrategy
from app.schemas.future.crop_protection import IPMStrategyCreate, IPMStrategyUpdate


class CRUDIPMStrategy(CRUDBase[IPMStrategy, IPMStrategyCreate, IPMStrategyUpdate]):
    """CRUD operations for IPMStrategy"""

    async def get_by_crop(
        self,
        db: AsyncSession,
        *,
        crop_name: str,
        org_id: int
    ) -> List[IPMStrategy]:
        """Get all IPM strategies for a crop."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.crop_name == crop_name
        ).order_by(self.model.strategy_name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_pest(
        self,
        db: AsyncSession,
        *,
        pest_name: str,
        org_id: int
    ) -> List[IPMStrategy]:
        """Get all IPM strategies for a specific pest."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.target_pest == pest_name
        ).order_by(self.model.effectiveness_rating.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> List[IPMStrategy]:
        """Get all IPM strategies for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.strategy_name)

        result = await db.execute(query)
        return list(result.scalars().all())


ipm_strategy = CRUDIPMStrategy(IPMStrategy)

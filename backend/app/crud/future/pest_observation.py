"""
CRUD operations for Pest Observation
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.pest_observation import PestObservation
from app.schemas.future.crop_protection import PestObservationBase, PestObservationCreate


class CRUDPestObservation(CRUDBase[PestObservation, PestObservationCreate, PestObservationBase]):
    """CRUD operations for PestObservation"""
    
    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> List[PestObservation]:
        """Get all pest observations for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.observation_date.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_severity(
        self,
        db: AsyncSession,
        *,
        min_severity: int,
        org_id: int
    ) -> List[PestObservation]:
        """Get observations above a severity threshold."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.severity >= min_severity
        ).order_by(self.model.severity.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())


pest_observation = CRUDPestObservation(PestObservation)

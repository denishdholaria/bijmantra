"""
CRUD operations for Crop Suitability
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.crop_suitability import CropSuitability
from app.schemas.future.crop_intelligence import CropSuitabilityBase, CropSuitabilityCreate


class CRUDCropSuitability(CRUDBase[CropSuitability, CropSuitabilityCreate, CropSuitabilityBase]):
    """CRUD operations for CropSuitability"""

    async def get_by_location(
        self,
        db: AsyncSession,
        *,
        location_id: int,
        org_id: int
    ) -> List[CropSuitability]:
        """Get all suitability assessments for a location."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.location_id == location_id
        ).order_by(self.model.suitability_score.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_crop(
        self,
        db: AsyncSession,
        *,
        crop_name: str,
        org_id: int
    ) -> List[CropSuitability]:
        """Get all suitability assessments for a crop."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.crop_name == crop_name
        ).order_by(self.model.suitability_score.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_suitable_locations(
        self,
        db: AsyncSession,
        *,
        crop_name: str,
        min_score: float,
        org_id: int
    ) -> List[CropSuitability]:
        """Get locations suitable for a crop above minimum score."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.crop_name == crop_name,
            self.model.suitability_score >= min_score
        ).order_by(self.model.suitability_score.desc())

        result = await db.execute(query)
        return list(result.scalars().all())


crop_suitability = CRUDCropSuitability(CropSuitability)

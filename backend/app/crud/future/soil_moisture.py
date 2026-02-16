"""
CRUD operations for Soil Moisture Reading
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.soil_moisture_reading import SoilMoistureReading
from app.schemas.future.water_irrigation import SoilMoistureReadingBase, SoilMoistureReadingCreate


class CRUDSoilMoistureReading(CRUDBase[SoilMoistureReading, SoilMoistureReadingCreate, SoilMoistureReadingBase]):
    """CRUD operations for SoilMoistureReading"""

    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> List[SoilMoistureReading]:
        """Get all moisture readings for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.reading_timestamp.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_device(
        self,
        db: AsyncSession,
        *,
        device_id: int,
        org_id: int
    ) -> List[SoilMoistureReading]:
        """Get all readings from a specific device."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.device_id == device_id
        ).order_by(self.model.reading_timestamp.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_latest_by_device(
        self,
        db: AsyncSession,
        *,
        device_id: int,
        org_id: int
    ) -> Optional[SoilMoistureReading]:
        """Get the most recent reading from a device."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.device_id == device_id
        ).order_by(self.model.reading_timestamp.desc()).limit(1)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_timeseries(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int,
        hours: int = 24
    ) -> List[SoilMoistureReading]:
        """Get moisture readings for a field over a time period."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id,
            self.model.reading_timestamp >= cutoff
        ).order_by(self.model.reading_timestamp)

        result = await db.execute(query)
        return list(result.scalars().all())


soil_moisture = CRUDSoilMoistureReading(SoilMoistureReading)

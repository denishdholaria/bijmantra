"""
CRUD operations for Spray Application
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.future.spray_application import SprayApplication
from app.schemas.future.crop_protection import SprayApplicationCreate, SprayApplicationUpdate


class CRUDSprayApplication(CRUDBase[SprayApplication, SprayApplicationCreate, SprayApplicationUpdate]):
    """CRUD operations for SprayApplication"""

    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        org_id: int
    ) -> List[SprayApplication]:
        """Get all spray applications for a field."""
        query = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.field_id == field_id
        ).order_by(self.model.application_date.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_compliance_report(
        self,
        db: AsyncSession,
        *,
        org_id: int
    ) -> dict:
        """Get spray application compliance summary."""
        query = select(self.model).where(
            self.model.organization_id == org_id
        )

        result = await db.execute(query)
        applications = list(result.scalars().all())

        total = len(applications)
        compliant = sum(1 for a in applications if getattr(a, 'is_compliant', True))

        return {
            "total_applications": total,
            "compliant_applications": compliant,
            "compliance_rate": (compliant / total * 100) if total > 0 else 100.0
        }


spray_application = CRUDSprayApplication(SprayApplication)

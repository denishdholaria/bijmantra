"""
Water Balance Service
Business logic for water balance calculations and data management.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.future import water_balance as water_crud
from app.schemas.future.water_irrigation import WaterBalanceCreate
from app.models.future.water_balance import WaterBalance

class WaterBalanceService:
    """Service for managing water balance records and calculations."""

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, org_id: int
    ) -> List[WaterBalance]:
        """
        List all water balance records for the organization.
        """
        records, _ = await water_crud.water_balance.get_multi(
            db, skip=skip, limit=limit, org_id=org_id
        )
        return records

    async def get(
        self, db: AsyncSession, id: int, org_id: int
    ) -> Optional[WaterBalance]:
        """
        Get a single water balance record by ID.
        Ensures the record belongs to the organization.
        """
        record = await water_crud.water_balance.get(db, id=id)
        if record and record.organization_id == org_id:
            return record
        return None

    async def create(
        self, db: AsyncSession, *, obj_in: WaterBalanceCreate, org_id: int
    ) -> WaterBalance:
        """
        Create a new water balance record.

        The Water Balance Equation (ΔS = P + I - ET - R - D) is implicitly
        represented by the input values.
        """
        # Future business logic: validate the equation:
        # calculated_delta_s = (obj_in.precipitation_mm + obj_in.irrigation_mm -
        #                       obj_in.et_actual_mm - obj_in.runoff_mm -
        #                       obj_in.deep_percolation_mm)
        # We could compare this with change in soil_water_content_mm if we had the previous day's record.

        record = await water_crud.water_balance.create(
            db, obj_in=obj_in, org_id=org_id
        )
        await db.commit()
        await db.refresh(record)
        return record

    async def delete(
        self, db: AsyncSession, *, id: int, org_id: int
    ) -> Optional[int]:
        """
        Delete a water balance record.
        Returns the ID if deleted, None if not found/unauthorized.
        """
        record = await self.get(db, id=id, org_id=org_id)
        if not record:
            return None
        await water_crud.water_balance.delete(db, id=id)
        await db.commit()
        return id

    async def get_by_field(
        self, db: AsyncSession, *, field_id: int, org_id: int
    ) -> List[WaterBalance]:
        """
        Get all water balance records for a specific field.
        """
        return await water_crud.water_balance.get_by_field(
            db, field_id=field_id, org_id=org_id
        )

    async def get_field_summary(
        self, db: AsyncSession, *, field_id: int, org_id: int
    ) -> Dict[str, Any]:
        """
        Get summary statistics for a field's water balance.
        """
        return await water_crud.water_balance.get_field_summary(
            db, field_id=field_id, org_id=org_id
        )

water_balance_service = WaterBalanceService()

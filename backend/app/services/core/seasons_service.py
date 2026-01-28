from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
import uuid

from app.models.core import Season as SeasonModel
from app.schemas.core import SeasonCreate, SeasonUpdate

class SeasonService:
    @staticmethod
    async def list_seasons(
        db: AsyncSession,
        org_id: int,
        page: int,
        page_size: int,
        year: Optional[int] = None,
        season_db_id: Optional[str] = None
    ) -> tuple[List[SeasonModel], int]:
        """List seasons with pagination"""
        query = select(SeasonModel).where(SeasonModel.organization_id == org_id)

        if year:
            query = query.where(SeasonModel.year == year)

        if season_db_id:
            query = query.where(SeasonModel.season_db_id == season_db_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(SeasonModel.year.desc(), SeasonModel.season_name)
        query = query.offset(page * page_size).limit(page_size)

        result = await db.execute(query)
        seasons = result.scalars().all()

        return seasons, total_count

    @staticmethod
    async def get_season(
        db: AsyncSession,
        org_id: int,
        season_db_id: str
    ) -> Optional[SeasonModel]:
        """Get a single season by DbId"""
        query = select(SeasonModel).where(
            SeasonModel.season_db_id == season_db_id,
            SeasonModel.organization_id == org_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_season(
        db: AsyncSession,
        org_id: int,
        season_in: SeasonCreate
    ) -> SeasonModel:
        """Create a new season"""
        # Generate unique season_db_id
        season_db_id = f"season_{uuid.uuid4().hex[:12]}"

        season = SeasonModel(
            organization_id=org_id,
            season_db_id=season_db_id,
            season_name=season_in.season_name,
            year=season_in.year,
            additional_info=season_in.additional_info,
            external_references=season_in.external_references
        )

        db.add(season)
        await db.commit()
        await db.refresh(season)
        return season

    @staticmethod
    async def update_season(
        db: AsyncSession,
        org_id: int,
        season_db_id: str,
        season_in: SeasonUpdate
    ) -> Optional[SeasonModel]:
        """Update a season"""
        season = await SeasonService.get_season(db, org_id, season_db_id)
        if not season:
            return None

        # Update fields
        if season_in.season_name is not None:
            season.season_name = season_in.season_name
        if season_in.year is not None:
            season.year = season_in.year
        if season_in.additional_info is not None:
            season.additional_info = season_in.additional_info
        if season_in.external_references is not None:
            season.external_references = season_in.external_references

        await db.commit()
        await db.refresh(season)
        return season

    @staticmethod
    async def delete_season(
        db: AsyncSession,
        org_id: int,
        season_db_id: str
    ) -> bool:
        """Delete a season"""
        season = await SeasonService.get_season(db, org_id, season_db_id)
        if not season:
            return False

        await db.delete(season)
        await db.commit()
        return True

season_service = SeasonService()

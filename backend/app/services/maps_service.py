"""
BrAPI Maps Service
Business logic for Genome Maps, Linkage Groups, and Marker Positions.
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, update
from sqlalchemy.orm import selectinload
import uuid

from app.models.genotyping import GenomeMap, LinkageGroup, MarkerPosition
from app.schemas.genotyping import GenomeMapCreate, GenomeMapUpdate

class MapsService:
    """Service for managing Genome Maps and related data."""

    async def list_maps(
        self,
        db: AsyncSession,
        map_db_id: Optional[str] = None,
        map_pui: Optional[str] = None,
        common_crop_name: Optional[str] = None,
        scientific_name: Optional[str] = None,
        type: Optional[str] = None,
        page: int = 0,
        page_size: int = 1000
    ) -> Tuple[List[GenomeMap], int]:
        """List genome maps with filters."""
        query = select(GenomeMap)

        if map_db_id:
            query = query.where(GenomeMap.map_db_id == map_db_id)
        if map_pui:
            query = query.where(GenomeMap.map_pui == map_pui)
        if common_crop_name:
            query = query.where(GenomeMap.common_crop_name.ilike(f"%{common_crop_name}%"))
        if scientific_name:
            query = query.where(GenomeMap.scientific_name.ilike(f"%{scientific_name}%"))
        if type:
            query = query.where(GenomeMap.type == type)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.offset(page * page_size).limit(page_size)

        result = await db.execute(query)
        maps = result.scalars().all()

        return maps, total

    async def get_map(self, db: AsyncSession, map_db_id: str) -> Optional[GenomeMap]:
        """Get a single genome map by ID."""
        query = select(GenomeMap).where(GenomeMap.map_db_id == map_db_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_map(self, db: AsyncSession, map_data: GenomeMapCreate, organization_id: int) -> GenomeMap:
        """Create a new genome map."""
        # Generate ID if needed (though BrAPI usually implies server-generated)
        map_db_id = str(uuid.uuid4())

        db_map = GenomeMap(
            map_db_id=map_db_id,
            organization_id=organization_id,
            **map_data.model_dump()
        )

        db.add(db_map)
        await db.commit()
        await db.refresh(db_map)
        return db_map

    async def update_map(self, db: AsyncSession, map_db_id: str, map_data: GenomeMapUpdate) -> Optional[GenomeMap]:
        """Update an existing genome map."""
        db_map = await self.get_map(db, map_db_id)
        if not db_map:
            return None

        update_data = map_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_map, key, value)

        await db.commit()
        await db.refresh(db_map)
        return db_map

    async def delete_map(self, db: AsyncSession, map_db_id: str) -> bool:
        """Delete a genome map."""
        db_map = await self.get_map(db, map_db_id)
        if not db_map:
            return False

        await db.delete(db_map)
        await db.commit()
        return True

    async def list_linkage_groups(
        self,
        db: AsyncSession,
        map_db_id: str,
        page: int = 0,
        page_size: int = 1000
    ) -> Tuple[List[LinkageGroup], int]:
        """List linkage groups for a map."""
        # Check map exists first
        db_map = await self.get_map(db, map_db_id)
        if not db_map:
            return [], 0

        query = select(LinkageGroup).where(LinkageGroup.map_id == db_map.id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset(page * page_size).limit(page_size)

        result = await db.execute(query)
        linkage_groups = result.scalars().all()

        return linkage_groups, total

    async def list_marker_positions(
        self,
        db: AsyncSession,
        map_db_id: Optional[str] = None,
        linkage_group_name: Optional[str] = None,
        min_position: Optional[float] = None,
        max_position: Optional[float] = None,
        page: int = 0,
        page_size: int = 1000
    ) -> Tuple[List[MarkerPosition], int]:
        """List marker positions."""
        query = select(MarkerPosition)

        if map_db_id:
            # Need to join with GenomeMap to filter by mapDbId if MarkerPosition stores foreign key ID
            # Assuming MarkerPosition has map_id relation
            query = query.join(GenomeMap).where(GenomeMap.map_db_id == map_db_id)

        if linkage_group_name:
            query = query.where(MarkerPosition.linkage_group_name == linkage_group_name)
        if min_position is not None:
            query = query.where(MarkerPosition.position >= min_position)
        if max_position is not None:
            query = query.where(MarkerPosition.position <= max_position)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset(page * page_size).limit(page_size)

        result = await db.execute(query)
        positions = result.scalars().all()

        return positions, total

# Singleton instance
maps_service = MapsService()

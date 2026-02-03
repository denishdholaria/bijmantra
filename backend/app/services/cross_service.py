from typing import List, Optional, Tuple, Dict, Any
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.germplasm import Cross, CrossingProject, Germplasm
from app.schemas.germplasm import CrossCreate, CrossUpdate, CrossStats, Cross as CrossSchema

class CrossService:
    @staticmethod
    async def list_crosses(
        db: AsyncSession,
        page: int = 0,
        page_size: int = 20,
        crossing_project_db_id: Optional[str] = None,
        cross_type: Optional[str] = None,
        cross_db_id: Optional[str] = None,
        cross_name: Optional[str] = None,
        organization_id: Optional[int] = None
    ) -> Tuple[List[Cross], int]:
        # Build base statement with eager loading
        stmt = select(Cross).options(
            selectinload(Cross.crossing_project),
            selectinload(Cross.parent1),
            selectinload(Cross.parent2),
        )

        # Filter by organization
        if organization_id:
            stmt = stmt.where(Cross.organization_id == organization_id)

        # Apply filters
        if crossing_project_db_id:
            stmt = stmt.join(Cross.crossing_project).where(
                CrossingProject.crossing_project_db_id == crossing_project_db_id
            )
        if cross_type:
            stmt = stmt.where(Cross.cross_type == cross_type)
        if cross_db_id:
            stmt = stmt.where(Cross.cross_db_id == cross_db_id)
        if cross_name:
            stmt = stmt.where(Cross.cross_name.ilike(f"%{cross_name}%"))

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        stmt = stmt.offset(page * page_size).limit(page_size)

        # Execute query
        result = await db.execute(stmt)
        crosses = result.scalars().all()

        return crosses, total

    @staticmethod
    async def create_cross(
        db: AsyncSession,
        cross_data: CrossCreate,
        organization_id: int
    ) -> Cross:
        cross_db_id = f"cross_{uuid.uuid4().hex[:12]}"

        # Look up crossing project
        project_id = None
        if cross_data.crossingProjectDbId:
            stmt = select(CrossingProject).where(
                CrossingProject.crossing_project_db_id == cross_data.crossingProjectDbId
            )
            result = await db.execute(stmt)
            project = result.scalar_one_or_none()
            if project:
                project_id = project.id

        # Look up parents
        parent1_id = None
        parent2_id = None
        if cross_data.parent1DbId:
            stmt = select(Germplasm).where(Germplasm.germplasm_db_id == cross_data.parent1DbId)
            result = await db.execute(stmt)
            p1 = result.scalar_one_or_none()
            if p1:
                parent1_id = p1.id
        if cross_data.parent2DbId:
            stmt = select(Germplasm).where(Germplasm.germplasm_db_id == cross_data.parent2DbId)
            result = await db.execute(stmt)
            p2 = result.scalar_one_or_none()
            if p2:
                parent2_id = p2.id

        new_cross = Cross(
            organization_id=organization_id,
            cross_db_id=cross_db_id,
            cross_name=cross_data.crossName,
            cross_type=cross_data.crossType,
            crossing_project_id=project_id,
            parent1_db_id=parent1_id,
            parent1_type=cross_data.parent1Type,
            parent2_db_id=parent2_id,
            parent2_type=cross_data.parent2Type,
            pollination_time_stamp=cross_data.pollinationTimeStamp,
            crossing_year=cross_data.crossingYear,
            cross_status=cross_data.crossStatus or "PLANNED",
            additional_info=cross_data.additionalInfo,
            external_references=cross_data.externalReferences
        )

        db.add(new_cross)
        await db.flush()
        await db.refresh(new_cross, attribute_names=["crossing_project", "parent1", "parent2"])

        return new_cross

    @staticmethod
    async def get_cross(
        db: AsyncSession,
        cross_db_id: str,
        organization_id: Optional[int] = None
    ) -> Optional[Cross]:
        stmt = select(Cross).options(
            selectinload(Cross.crossing_project),
            selectinload(Cross.parent1),
            selectinload(Cross.parent2),
        ).where(Cross.cross_db_id == cross_db_id)

        if organization_id:
            stmt = stmt.where(Cross.organization_id == organization_id)

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_crosses(
        db: AsyncSession,
        crosses_update: List[CrossUpdate],
        organization_id: Optional[int] = None
    ) -> List[Cross]:
        updated = []

        for cross_data in crosses_update:
            stmt = select(Cross).options(
                selectinload(Cross.crossing_project),
                selectinload(Cross.parent1),
                selectinload(Cross.parent2),
            ).where(Cross.cross_db_id == cross_data.crossDbId)

            if organization_id:
                stmt = stmt.where(Cross.organization_id == organization_id)

            result = await db.execute(stmt)
            cross = result.scalar_one_or_none()

            if cross:
                if cross_data.crossName is not None:
                    cross.cross_name = cross_data.crossName
                if cross_data.crossType is not None:
                    cross.cross_type = cross_data.crossType
                if cross_data.pollinationTimeStamp is not None:
                    cross.pollination_time_stamp = cross_data.pollinationTimeStamp
                if cross_data.crossingYear is not None:
                    cross.crossing_year = cross_data.crossingYear
                if cross_data.crossStatus is not None:
                    cross.cross_status = cross_data.crossStatus
                if cross_data.additionalInfo is not None:
                    cross.additional_info = cross_data.additionalInfo
                if cross_data.externalReferences is not None:
                    cross.external_references = cross_data.externalReferences

                # Note: Updating parents or project is not implemented here based on original code,
                # but could be added if needed. For now sticking to minimal changes.

                updated.append(cross)

        await db.flush()
        return updated

    @staticmethod
    async def get_stats(
        db: AsyncSession,
        organization_id: Optional[int] = None
    ) -> CrossStats:
        base_query = select(func.count(Cross.id))
        if organization_id:
            base_query = base_query.where(Cross.organization_id == organization_id)

        # Total
        total_result = await db.execute(base_query)
        total_count = total_result.scalar() or 0

        # This Season (Current Year)
        current_year = datetime.now().year
        season_query = base_query.where(Cross.crossing_year == current_year)
        season_result = await db.execute(season_query)
        season_count = season_result.scalar() or 0

        # Successful (COMPLETED)
        success_query = base_query.where(Cross.cross_status == 'COMPLETED')
        success_result = await db.execute(success_query)
        success_count = success_result.scalar() or 0

        # Pending (PLANNED)
        pending_query = base_query.where(Cross.cross_status == 'PLANNED')
        pending_result = await db.execute(pending_query)
        pending_count = pending_result.scalar() or 0

        return CrossStats(
            totalCount=total_count,
            thisSeasonCount=season_count,
            successfulCount=success_count,
            pendingCount=pending_count
        )

    @staticmethod
    def model_to_schema(cross: Cross) -> CrossSchema:
        """Convert a Cross SQLAlchemy model to Pydantic schema."""
        return CrossSchema(
            crossDbId=cross.cross_db_id,
            crossName=cross.cross_name,
            crossType=cross.cross_type,
            crossingProjectDbId=cross.crossing_project.crossing_project_db_id if cross.crossing_project else None,
            crossingProjectName=cross.crossing_project.crossing_project_name if cross.crossing_project else None,
            parent1DbId=cross.parent1.germplasm_db_id if cross.parent1 else None,
            parent1Name=cross.parent1.germplasm_name if cross.parent1 else None,
            parent1Type=cross.parent1_type,
            parent2DbId=cross.parent2.germplasm_db_id if cross.parent2 else None,
            parent2Name=cross.parent2.germplasm_name if cross.parent2 else None,
            parent2Type=cross.parent2_type,
            pollinationTimeStamp=cross.pollination_time_stamp,
            crossingYear=cross.crossing_year,
            crossStatus=cross.cross_status,
            additionalInfo=cross.additional_info,
            externalReferences=cross.external_references,
        )

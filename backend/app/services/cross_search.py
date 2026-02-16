"""
Cross Search Service

Advanced cross/planned cross search and discovery.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload


class CrossSearchService:
    """Service for advanced cross search.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def search(
        self,
        db: AsyncSession,
        organization_id: int,
        query: Optional[str] = None,
        parent_id: Optional[int] = None,
        status: Optional[str] = None,
        cross_type: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search crosses with filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            query: Text search query (cross name, parent names)
            parent_id: Filter by parent germplasm ID
            status: Filter by cross status
            cross_type: Filter by cross type (BIPARENTAL, SELF, etc.)
            year: Filter by crossing year
            limit: Maximum results to return
            
        Returns:
            List of cross dictionaries, empty if no data
        """
        from app.models.germplasm import Cross, Germplasm

        stmt = (
            select(Cross)
            .options(
                selectinload(Cross.parent1),
                selectinload(Cross.parent2),
                selectinload(Cross.crossing_project)
            )
            .where(Cross.organization_id == organization_id)
            .order_by(Cross.created_at.desc())
            .limit(limit)
        )

        if query:
            q = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Cross.cross_name).like(q),
                    func.lower(Cross.cross_db_id).like(q),
                )
            )

        if status:
            stmt = stmt.where(func.lower(Cross.cross_status) == status.lower())

        if cross_type:
            stmt = stmt.where(func.lower(Cross.cross_type) == cross_type.lower())

        if year:
            stmt = stmt.where(Cross.crossing_year == year)

        if parent_id:
            stmt = stmt.where(
                or_(
                    Cross.parent1_db_id == parent_id,
                    Cross.parent2_db_id == parent_id
                )
            )

        result = await db.execute(stmt)
        crosses = result.scalars().all()

        results = []
        for c in crosses:
            results.append({
                "id": str(c.id),
                "cross_db_id": c.cross_db_id,
                "name": c.cross_name,
                "type": c.cross_type or "BIPARENTAL",
                "status": c.cross_status or "PLANNED",
                "year": c.crossing_year,
                "parent1": {
                    "id": str(c.parent1.id),
                    "name": c.parent1.germplasm_name,
                    "type": c.parent1_type,
                } if c.parent1 else None,
                "parent2": {
                    "id": str(c.parent2.id),
                    "name": c.parent2.germplasm_name,
                    "type": c.parent2_type,
                } if c.parent2 else None,
                "project": c.crossing_project.crossing_project_name if c.crossing_project else None,
                "pollination_date": c.pollination_time_stamp,
            })

        return results

    async def search_planned(
        self,
        db: AsyncSession,
        organization_id: int,
        query: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search planned crosses.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            query: Text search query
            status: Filter by status (PLANNED, IN_PROGRESS, COMPLETED)
            limit: Maximum results to return
            
        Returns:
            List of planned cross dictionaries
        """
        from app.models.germplasm import PlannedCross

        stmt = (
            select(PlannedCross)
            .options(
                selectinload(PlannedCross.parent1),
                selectinload(PlannedCross.parent2),
                selectinload(PlannedCross.crossing_project)
            )
            .where(PlannedCross.organization_id == organization_id)
            .order_by(PlannedCross.created_at.desc())
            .limit(limit)
        )

        if query:
            q = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(PlannedCross.planned_cross_name).like(q),
                    func.lower(PlannedCross.planned_cross_db_id).like(q),
                )
            )

        if status:
            stmt = stmt.where(func.lower(PlannedCross.status) == status.lower())

        result = await db.execute(stmt)
        planned = result.scalars().all()

        results = []
        for p in planned:
            results.append({
                "id": str(p.id),
                "planned_cross_db_id": p.planned_cross_db_id,
                "name": p.planned_cross_name,
                "type": p.cross_type or "BIPARENTAL",
                "status": p.status or "PLANNED",
                "progeny_count": p.number_of_progeny,
                "parent1": {
                    "id": str(p.parent1.id),
                    "name": p.parent1.germplasm_name,
                    "type": p.parent1_type,
                } if p.parent1 else None,
                "parent2": {
                    "id": str(p.parent2.id),
                    "name": p.parent2.germplasm_name,
                    "type": p.parent2_type,
                } if p.parent2 else None,
                "project": p.crossing_project.crossing_project_name if p.crossing_project else None,
            })

        return results

    async def get_by_id(
        self,
        db: AsyncSession,
        organization_id: int,
        cross_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cross by ID with full details.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            cross_id: Cross ID
            
        Returns:
            Cross dictionary or None if not found
        """
        from app.models.germplasm import Cross

        stmt = (
            select(Cross)
            .options(
                selectinload(Cross.parent1),
                selectinload(Cross.parent2),
                selectinload(Cross.crossing_project),
            )
            .where(Cross.organization_id == organization_id)
            .where(Cross.id == int(cross_id))
        )

        result = await db.execute(stmt)
        c = result.scalar_one_or_none()

        if not c:
            return None

        return {
            "id": str(c.id),
            "cross_db_id": c.cross_db_id,
            "name": c.cross_name,
            "type": c.cross_type,
            "status": c.cross_status,
            "year": c.crossing_year,
            "pollination_date": c.pollination_time_stamp,
            "parent1": {
                "id": str(c.parent1.id),
                "name": c.parent1.germplasm_name,
                "accession": c.parent1.accession_number,
                "species": c.parent1.species,
                "type": c.parent1_type,
            } if c.parent1 else None,
            "parent2": {
                "id": str(c.parent2.id),
                "name": c.parent2.germplasm_name,
                "accession": c.parent2.accession_number,
                "species": c.parent2.species,
                "type": c.parent2_type,
            } if c.parent2 else None,
            "project": {
                "id": str(c.crossing_project.id),
                "name": c.crossing_project.crossing_project_name,
            } if c.crossing_project else None,
            "additional_info": c.additional_info or {},
        }

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> Dict[str, int]:
        """Get cross statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Statistics dictionary with counts
        """
        from app.models.germplasm import Cross, PlannedCross

        # Total crosses
        cross_stmt = (
            select(func.count(Cross.id))
            .where(Cross.organization_id == organization_id)
        )
        cross_result = await db.execute(cross_stmt)
        total_crosses = cross_result.scalar() or 0

        # Completed crosses
        completed_stmt = (
            select(func.count(Cross.id))
            .where(Cross.organization_id == organization_id)
            .where(func.lower(Cross.cross_status) == 'completed')
        )
        completed_result = await db.execute(completed_stmt)
        completed = completed_result.scalar() or 0

        # Planned crosses
        planned_stmt = (
            select(func.count(PlannedCross.id))
            .where(PlannedCross.organization_id == organization_id)
        )
        planned_result = await db.execute(planned_stmt)
        planned = planned_result.scalar() or 0

        return {
            "total_crosses": total_crosses,
            "completed_crosses": completed,
            "planned_crosses": planned,
        }


# Singleton instance
cross_search_service = CrossSearchService()

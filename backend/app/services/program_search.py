"""
Program Search Service

Advanced breeding program search and discovery.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload


class ProgramSearchService:
    """Service for advanced program search.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def search(
        self,
        db: AsyncSession,
        organization_id: int,
        query: Optional[str] = None,
        crop: Optional[str] = None,
        is_research: Optional[bool] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search programs with filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            query: Text search query (name, objective, abbreviation)
            crop: Filter by common crop name (via trials)
            is_research: Filter by research project flag
            limit: Maximum results to return
            
        Returns:
            List of program dictionaries, empty if no data
        """
        from app.models.core import Program

        stmt = (
            select(Program)
            .options(
                selectinload(Program.lead_person),
                selectinload(Program.trials)
            )
            .where(Program.organization_id == organization_id)
            .limit(limit)
        )

        if query:
            q = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Program.program_name).like(q),
                    func.lower(Program.program_db_id).like(q),
                    func.lower(Program.abbreviation).like(q),
                    func.lower(Program.objective).like(q),
                )
            )

        if is_research is not None:
            stmt = stmt.where(Program.is_research_project == is_research)

        result = await db.execute(stmt)
        programs = result.scalars().all()

        results = []
        for p in programs:
            # Filter by crop if specified (check trials)
            if crop:
                trial_crops = [t.common_crop_name for t in (p.trials or []) if t.common_crop_name]
                if not any(crop.lower() in c.lower() for c in trial_crops):
                    continue

            results.append({
                "id": str(p.id),
                "program_db_id": p.program_db_id,
                "name": p.program_name,
                "abbreviation": p.abbreviation,
                "objective": p.objective or "",
                "is_research_project": p.is_research_project,
                "trial_count": len(p.trials) if p.trials else 0,
                "lead_person": {
                    "id": str(p.lead_person.id),
                    "name": p.lead_person.first_name + " " + (p.lead_person.last_name or ""),
                } if p.lead_person else None,
                "crops": list(set(t.common_crop_name for t in (p.trials or []) if t.common_crop_name)),
            })

        return results

    async def get_by_id(
        self,
        db: AsyncSession,
        organization_id: int,
        program_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get program by ID with full details.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            program_id: Program ID
            
        Returns:
            Program dictionary or None if not found
        """
        from app.models.core import Program

        stmt = (
            select(Program)
            .options(
                selectinload(Program.lead_person),
                selectinload(Program.trials)
            )
            .where(Program.organization_id == organization_id)
            .where(Program.id == int(program_id))
        )

        result = await db.execute(stmt)
        p = result.scalar_one_or_none()

        if not p:
            return None

        return {
            "id": str(p.id),
            "program_db_id": p.program_db_id,
            "name": p.program_name,
            "abbreviation": p.abbreviation,
            "objective": p.objective or "",
            "is_research_project": p.is_research_project,
            "research_context": p.research_context or {},
            "lead_person": {
                "id": str(p.lead_person.id),
                "name": p.lead_person.first_name + " " + (p.lead_person.last_name or ""),
                "email": p.lead_person.email_address,
            } if p.lead_person else None,
            "trials": [
                {
                    "id": str(t.id),
                    "name": t.trial_name,
                    "crop": t.common_crop_name,
                    "active": t.active,
                }
                for t in (p.trials or [])
            ],
            "trial_count": len(p.trials) if p.trials else 0,
            "crops": list(set(t.common_crop_name for t in (p.trials or []) if t.common_crop_name)),
            "additional_info": p.additional_info or {},
        }

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> Dict[str, int]:
        """Get program statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Statistics dictionary with counts
        """
        from app.models.core import Program

        # Total programs
        total_stmt = (
            select(func.count(Program.id))
            .where(Program.organization_id == organization_id)
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0

        # Research projects
        research_stmt = (
            select(func.count(Program.id))
            .where(Program.organization_id == organization_id)
            .where(Program.is_research_project == True)
        )
        research_result = await db.execute(research_stmt)
        research_count = research_result.scalar() or 0

        # Breeding programs (non-research)
        breeding_count = total - research_count

        return {
            "total_programs": total,
            "breeding_programs": breeding_count,
            "research_projects": research_count,
        }


# Singleton instance
program_search_service = ProgramSearchService()

"""
Trial Search Service

Advanced trial search and discovery.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload


class TrialSearchService:
    """Service for advanced trial search.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def search(
        self, 
        db: AsyncSession,
        organization_id: int,
        query: Optional[str] = None, 
        crop: Optional[str] = None,
        season: Optional[str] = None,
        location: Optional[str] = None,
        program: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search trials with filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            query: Text search query (name, description)
            crop: Filter by common crop name
            season: Filter by season/year
            location: Filter by location name
            program: Filter by program name
            status: Filter by active status
            limit: Maximum results to return
            
        Returns:
            List of trial dictionaries, empty if no data
        """
        from app.models.core import Trial, Program, Location, Study
        
        stmt = (
            select(Trial)
            .options(
                selectinload(Trial.program),
                selectinload(Trial.location),
                selectinload(Trial.studies)
            )
            .where(Trial.organization_id == organization_id)
            .limit(limit)
        )
        
        if query:
            q = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Trial.trial_name).like(q),
                    func.lower(Trial.trial_description).like(q),
                    func.lower(Trial.trial_db_id).like(q),
                    func.lower(Trial.common_crop_name).like(q),
                )
            )
        
        if crop:
            stmt = stmt.where(func.lower(Trial.common_crop_name) == crop.lower())
        
        if status:
            is_active = status.lower() in ['active', 'true', '1']
            stmt = stmt.where(Trial.active == is_active)
        
        result = await db.execute(stmt)
        trials = result.scalars().all()
        
        results = []
        for t in trials:
            # Filter by location if specified
            if location and t.location:
                if location.lower() not in t.location.location_name.lower():
                    continue
            
            # Filter by program if specified
            if program and t.program:
                if program.lower() not in t.program.program_name.lower():
                    continue
            
            results.append({
                "id": str(t.id),
                "trial_db_id": t.trial_db_id,
                "name": t.trial_name,
                "description": t.trial_description or "",
                "crop": t.common_crop_name or "Unknown",
                "program": t.program.program_name if t.program else None,
                "location": t.location.location_name if t.location else None,
                "start_date": t.start_date,
                "end_date": t.end_date,
                "active": t.active,
                "study_count": len(t.studies) if t.studies else 0,
                "type": t.trial_type or "Standard",
            })
        
        return results
    
    async def get_by_id(
        self, 
        db: AsyncSession,
        organization_id: int,
        trial_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get trial by ID with full details.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            trial_id: Trial ID
            
        Returns:
            Trial dictionary or None if not found
        """
        from app.models.core import Trial
        
        stmt = (
            select(Trial)
            .options(
                selectinload(Trial.program),
                selectinload(Trial.location),
                selectinload(Trial.studies)
            )
            .where(Trial.organization_id == organization_id)
            .where(Trial.id == int(trial_id))
        )
        
        result = await db.execute(stmt)
        t = result.scalar_one_or_none()
        
        if not t:
            return None
        
        return {
            "id": str(t.id),
            "trial_db_id": t.trial_db_id,
            "name": t.trial_name,
            "description": t.trial_description or "",
            "crop": t.common_crop_name or "Unknown",
            "program": {
                "id": str(t.program.id),
                "name": t.program.program_name
            } if t.program else None,
            "location": {
                "id": str(t.location.id),
                "name": t.location.location_name,
                "country": t.location.country_name
            } if t.location else None,
            "start_date": t.start_date,
            "end_date": t.end_date,
            "active": t.active,
            "type": t.trial_type,
            "studies": [
                {
                    "id": str(s.id),
                    "name": s.study_name,
                    "type": s.study_type
                }
                for s in (t.studies or [])
            ],
            "additional_info": t.additional_info or {},
        }
    
    async def get_statistics(
        self, 
        db: AsyncSession,
        organization_id: int
    ) -> Dict[str, int]:
        """Get trial statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Statistics dictionary with counts
        """
        from app.models.core import Trial
        
        # Total count
        total_stmt = (
            select(func.count(Trial.id))
            .where(Trial.organization_id == organization_id)
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        # Active count
        active_stmt = (
            select(func.count(Trial.id))
            .where(Trial.organization_id == organization_id)
            .where(Trial.active == True)
        )
        active_result = await db.execute(active_stmt)
        active = active_result.scalar() or 0
        
        # Crop count
        crop_stmt = (
            select(func.count(func.distinct(Trial.common_crop_name)))
            .where(Trial.organization_id == organization_id)
        )
        crop_result = await db.execute(crop_stmt)
        crop_count = crop_result.scalar() or 0
        
        return {
            "total_trials": total,
            "active_trials": active,
            "crop_count": crop_count,
        }


# Singleton instance
trial_search_service = TrialSearchService()

"""
Performance Ranking Service
Rank breeding entries by performance metrics.
Queries real data from database - no demo/mock data.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload


class PerformanceRankingService:
    """Service for ranking breeding entries by performance.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def get_rankings(
        self,
        db: AsyncSession,
        organization_id: int,
        program_id: Optional[str] = None,
        trial_id: Optional[str] = None,
        sort_by: str = "score",
        limit: int = 50,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get ranked entries from database with optional filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            program_id: Filter by program ID
            trial_id: Filter by trial ID
            sort_by: Sort field (score, yield, gebv, name)
            limit: Maximum results to return
            search: Search query for name/traits
            
        Returns:
            List of ranked entry dictionaries, empty if no data
        """
        from app.models.core import ObservationUnit, Study, Trial, Program
        from app.models.germplasm import Germplasm
        
        # Query observation units with germplasm and study info
        stmt = (
            select(ObservationUnit)
            .where(ObservationUnit.organization_id == organization_id)
            .options(
                selectinload(ObservationUnit.germplasm),
                selectinload(ObservationUnit.study),
            )
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        units = result.scalars().all()
        
        if not units:
            return []
        
        # Build ranking entries from observation units
        entries = []
        for unit in units:
            if not unit.germplasm:
                continue
            
            # Extract traits from additional_info
            traits = []
            if unit.germplasm.additional_info and isinstance(unit.germplasm.additional_info, dict):
                traits = unit.germplasm.additional_info.get("traits", [])
            
            # Apply search filter
            if search:
                search_lower = search.lower()
                name = unit.germplasm.germplasm_name or ""
                if not (
                    search_lower in name.lower() or
                    any(search_lower in t.lower() for t in traits)
                ):
                    continue
            
            entry = {
                "id": str(unit.id),
                "entry_id": unit.observation_unit_db_id or str(unit.id),
                "name": unit.germplasm.germplasm_name or "Unknown",
                "program_id": str(unit.study.program_id) if unit.study and unit.study.program_id else None,
                "program_name": None,  # Would need join to Program
                "trial_id": str(unit.study.trial_id) if unit.study and unit.study.trial_id else None,
                "trial_name": None,  # Would need join to Trial
                "generation": unit.germplasm.additional_info.get("generation") if unit.germplasm.additional_info else None,
                "yield": None,  # Would need to aggregate from observations
                "yield_rank": None,
                "gebv": None,  # Would need from genomic predictions
                "gebv_rank": None,
                "traits": traits,
                "score": 0,  # Would need to calculate from observations
                "previous_score": None,
                "previous_rank": None,
                "observations": {},
            }
            
            # Apply program/trial filters
            if program_id and entry["program_id"] != program_id:
                continue
            if trial_id and entry["trial_id"] != trial_id:
                continue
            
            entries.append(entry)
        
        # Sort entries
        sort_key = {
            "score": lambda x: x.get("score", 0),
            "yield": lambda x: x.get("yield") or 0,
            "gebv": lambda x: x.get("gebv") or 0,
            "name": lambda x: x.get("name", ""),
        }.get(sort_by, lambda x: x.get("score", 0))
        
        entries.sort(key=sort_key, reverse=(sort_by != "name"))
        
        # Assign ranks
        for i, entry in enumerate(entries):
            entry["rank"] = i + 1
        
        return entries[:limit]

    async def get_entry(
        self,
        db: AsyncSession,
        organization_id: int,
        entry_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a single entry by ID.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            entry_id: Entry/observation unit ID
            
        Returns:
            Entry dictionary or None if not found
        """
        from app.models.core import ObservationUnit
        
        stmt = (
            select(ObservationUnit)
            .where(ObservationUnit.organization_id == organization_id)
            .where(ObservationUnit.id == int(entry_id))
            .options(selectinload(ObservationUnit.germplasm))
        )
        
        result = await db.execute(stmt)
        unit = result.scalar_one_or_none()
        
        if not unit or not unit.germplasm:
            return None
        
        traits = []
        if unit.germplasm.additional_info and isinstance(unit.germplasm.additional_info, dict):
            traits = unit.germplasm.additional_info.get("traits", [])
        
        return {
            "id": str(unit.id),
            "entry_id": unit.observation_unit_db_id or str(unit.id),
            "name": unit.germplasm.germplasm_name or "Unknown",
            "traits": traits,
            "score": 0,
            "yield": None,
            "gebv": None,
        }

    async def get_top_performers(
        self,
        db: AsyncSession,
        organization_id: int,
        program_id: Optional[str] = None,
        trial_id: Optional[str] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get top performing entries (podium).
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            program_id: Filter by program ID
            trial_id: Filter by trial ID
            limit: Number of top performers to return
            
        Returns:
            List of top performer dictionaries
        """
        return await self.get_rankings(
            db, organization_id,
            program_id=program_id,
            trial_id=trial_id,
            sort_by="score",
            limit=limit,
        )

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
        program_id: Optional[str] = None,
        trial_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get ranking statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            program_id: Filter by program ID
            trial_id: Filter by trial ID
            
        Returns:
            Statistics dictionary
        """
        entries = await self.get_rankings(
            db, organization_id,
            program_id=program_id,
            trial_id=trial_id,
            limit=1000,
        )
        
        if not entries:
            return {
                "total_entries": 0,
                "avg_score": 0,
                "avg_yield": None,
                "avg_gebv": None,
                "top_performer": None,
                "most_improved": None,
            }
        
        # Calculate averages
        scores = [e["score"] for e in entries if e.get("score") is not None]
        yields = [e["yield"] for e in entries if e.get("yield") is not None]
        gebvs = [e["gebv"] for e in entries if e.get("gebv") is not None]
        
        return {
            "total_entries": len(entries),
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "avg_yield": round(sum(yields) / len(yields), 2) if yields else None,
            "avg_gebv": round(sum(gebvs) / len(gebvs), 2) if gebvs else None,
            "top_performer": entries[0]["name"] if entries else None,
            "most_improved": None,  # Would need historical data
        }

    async def get_programs(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> List[Dict[str, str]]:
        """Get unique programs from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            List of program dictionaries
        """
        from app.models.core import Program
        
        stmt = (
            select(Program)
            .where(Program.organization_id == organization_id)
        )
        
        result = await db.execute(stmt)
        programs = result.scalars().all()
        
        return [
            {"id": str(p.id), "name": p.program_name or str(p.id)}
            for p in programs
        ]

    async def get_trials(
        self,
        db: AsyncSession,
        organization_id: int,
        program_id: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Get unique trials from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            program_id: Filter by program ID
            
        Returns:
            List of trial dictionaries
        """
        from app.models.core import Trial
        
        stmt = (
            select(Trial)
            .where(Trial.organization_id == organization_id)
        )
        
        if program_id:
            stmt = stmt.where(Trial.program_id == int(program_id))
        
        result = await db.execute(stmt)
        trials = result.scalars().all()
        
        return [
            {
                "id": str(t.id),
                "name": t.trial_name or str(t.id),
                "program_id": str(t.program_id) if t.program_id else None,
            }
            for t in trials
        ]

    async def compare_entries(
        self,
        db: AsyncSession,
        organization_id: int,
        entry_ids: List[str],
    ) -> Dict[str, Any]:
        """Compare multiple entries side by side.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            entry_ids: List of entry IDs to compare
            
        Returns:
            Comparison dictionary
        """
        if len(entry_ids) < 2:
            return {"error": "Need at least 2 entries to compare"}
        
        entries = []
        for eid in entry_ids:
            entry = await self.get_entry(db, organization_id, eid)
            if entry:
                entries.append(entry)
        
        if len(entries) < 2:
            return {"error": "Could not find enough entries to compare"}
        
        # Find best values
        yields = [e.get("yield") for e in entries if e.get("yield") is not None]
        gebvs = [e.get("gebv") for e in entries if e.get("gebv") is not None]
        scores = [e.get("score") for e in entries if e.get("score") is not None]
        
        best_yield = max(yields) if yields else None
        best_gebv = max(gebvs) if gebvs else None
        best_score = max(scores) if scores else None
        
        comparison = []
        for entry in entries:
            comparison.append({
                "id": entry["id"],
                "entry_id": entry["entry_id"],
                "name": entry["name"],
                "yield": entry.get("yield"),
                "yield_is_best": entry.get("yield") == best_yield if best_yield else False,
                "gebv": entry.get("gebv"),
                "gebv_is_best": entry.get("gebv") == best_gebv if best_gebv else False,
                "score": entry.get("score"),
                "score_is_best": entry.get("score") == best_score if best_score else False,
                "traits": entry.get("traits", []),
            })
        
        return {
            "entries": comparison,
            "best_yield": best_yield,
            "best_gebv": best_gebv,
            "best_score": best_score,
        }


# Singleton instance
performance_ranking_service = PerformanceRankingService()

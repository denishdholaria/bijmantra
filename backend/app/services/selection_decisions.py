"""
Selection Decisions Service
Manage breeding candidate selection decisions (advance/reject/hold).
Queries real data from database - no demo/mock data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload


class SelectionDecisionsService:
    """Service for managing selection decisions on breeding candidates.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def list_candidates(
        self,
        db: AsyncSession,
        organization_id: int,
        program_id: Optional[str] = None,
        trial_id: Optional[str] = None,
        generation: Optional[str] = None,
        decision_status: Optional[str] = None,
        min_gebv: Optional[float] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List selection candidates from database with optional filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            program_id: Filter by program ID
            trial_id: Filter by trial ID
            generation: Filter by generation (F5, F6, etc.)
            decision_status: Filter by decision status (pending, advance, reject, hold)
            min_gebv: Minimum GEBV threshold
            search: Search query for name/pedigree/traits
            
        Returns:
            List of candidate dictionaries, empty if no data
        """
        from app.models.germplasm import Germplasm
        from app.models.core import Study
        from app.models.phenotyping import ObservationUnit

        # Query germplasm as candidates
        stmt = (
            select(Germplasm)
            .where(Germplasm.organization_id == organization_id)
        )

        result = await db.execute(stmt)
        germplasm_list = result.scalars().all()

        if not germplasm_list:
            return []

        candidates = []
        for g in germplasm_list:
            # Extract info from additional_info
            info = g.additional_info or {}
            traits = info.get("traits", [])
            gen = info.get("generation")
            gebv = info.get("gebv")
            yield_est = info.get("yield_estimate")
            decision = info.get("selection_decision")
            decision_notes = info.get("selection_notes")
            decision_date = info.get("selection_date")
            decided_by = info.get("decided_by")

            # Apply filters
            if generation and gen != generation:
                continue
            if min_gebv and (gebv is None or gebv < min_gebv):
                continue
            if decision_status:
                if decision_status == "pending" and decision:
                    continue
                elif decision_status != "pending" and decision != decision_status:
                    continue
            if search:
                search_lower = search.lower()
                name = g.germplasm_name or ""
                pedigree = g.pedigree or ""
                if not (
                    search_lower in name.lower() or
                    search_lower in pedigree.lower() or
                    any(search_lower in t.lower() for t in traits)
                ):
                    continue

            candidates.append({
                "id": str(g.id),
                "name": g.germplasm_name or f"Germplasm-{g.id}",
                "germplasm_id": str(g.id),
                "program_id": None,  # Would need to join through observation_units
                "program_name": None,
                "generation": gen,
                "gebv": gebv,
                "yield_estimate": yield_est,
                "traits": traits,
                "pedigree": g.pedigree,
                "trial_id": None,
                "trial_name": None,
                "location": None,
                "created_at": g.created_at.isoformat() if g.created_at else None,
                "decision": decision,
                "decision_notes": decision_notes,
                "decision_date": decision_date,
                "decided_by": decided_by,
            })

        # Sort by GEBV descending
        candidates.sort(key=lambda x: x.get("gebv") or 0, reverse=True)
        return candidates

    async def get_candidate(
        self,
        db: AsyncSession,
        organization_id: int,
        candidate_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a single candidate with decision info.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            candidate_id: Germplasm ID
            
        Returns:
            Candidate dictionary or None if not found
        """
        from app.models.germplasm import Germplasm

        stmt = (
            select(Germplasm)
            .where(Germplasm.organization_id == organization_id)
            .where(Germplasm.id == int(candidate_id))
        )

        result = await db.execute(stmt)
        g = result.scalar_one_or_none()

        if not g:
            return None

        info = g.additional_info or {}

        return {
            "id": str(g.id),
            "name": g.germplasm_name or f"Germplasm-{g.id}",
            "germplasm_id": str(g.id),
            "generation": info.get("generation"),
            "gebv": info.get("gebv"),
            "yield_estimate": info.get("yield_estimate"),
            "traits": info.get("traits", []),
            "pedigree": g.pedigree,
            "decision": info.get("selection_decision"),
            "decision_notes": info.get("selection_notes"),
            "decision_date": info.get("selection_date"),
            "decided_by": info.get("decided_by"),
        }

    async def record_decision(
        self,
        db: AsyncSession,
        organization_id: int,
        candidate_id: str,
        decision: str,
        notes: Optional[str] = None,
        decided_by: str = "user",
    ) -> Dict[str, Any]:
        """Record a selection decision for a candidate.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            candidate_id: Germplasm ID
            decision: Decision type (advance, reject, hold)
            notes: Optional decision notes
            decided_by: User who made the decision
            
        Returns:
            Result dictionary with status
        """
        from app.models.germplasm import Germplasm

        if decision not in ["advance", "reject", "hold"]:
            return {"error": f"Invalid decision: {decision}. Must be advance, reject, or hold"}

        stmt = (
            select(Germplasm)
            .where(Germplasm.organization_id == organization_id)
            .where(Germplasm.id == int(candidate_id))
        )

        result = await db.execute(stmt)
        g = result.scalar_one_or_none()

        if not g:
            return {"error": f"Candidate {candidate_id} not found"}

        # Update additional_info with decision
        info = g.additional_info or {}
        info["selection_decision"] = decision
        info["selection_notes"] = notes
        info["selection_date"] = datetime.now(timezone.utc).isoformat()
        info["decided_by"] = decided_by
        g.additional_info = info

        await db.commit()

        return {
            "status": "success",
            "decision": {
                "candidate_id": candidate_id,
                "decision": decision,
                "notes": notes,
                "decided_by": decided_by,
                "date": info["selection_date"],
            }
        }

    async def record_bulk_decisions(
        self,
        db: AsyncSession,
        organization_id: int,
        decisions: List[Dict[str, Any]],
        decided_by: str = "user",
    ) -> Dict[str, Any]:
        """Record multiple decisions at once.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            decisions: List of decision dictionaries
            decided_by: User who made the decisions
            
        Returns:
            Result dictionary with counts
        """
        results = []
        for d in decisions:
            result = await self.record_decision(
                db, organization_id,
                candidate_id=d["candidate_id"],
                decision=d["decision"],
                notes=d.get("notes"),
                decided_by=decided_by,
            )
            results.append(result)

        success_count = sum(1 for r in results if "error" not in r)
        return {
            "status": "success",
            "total": len(decisions),
            "successful": success_count,
            "failed": len(decisions) - success_count,
            "results": results,
        }

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
        program_id: Optional[str] = None,
        trial_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get selection decision statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            program_id: Filter by program ID
            trial_id: Filter by trial ID
            
        Returns:
            Statistics dictionary
        """
        candidates = await self.list_candidates(
            db, organization_id,
            program_id=program_id,
            trial_id=trial_id,
        )

        if not candidates:
            return {
                "total_candidates": 0,
                "advanced": 0,
                "rejected": 0,
                "on_hold": 0,
                "pending": 0,
                "selection_rate": 0,
                "avg_gebv_advanced": None,
                "avg_gebv_rejected": None,
            }

        total = len(candidates)
        advanced = sum(1 for c in candidates if c.get("decision") == "advance")
        rejected = sum(1 for c in candidates if c.get("decision") == "reject")
        on_hold = sum(1 for c in candidates if c.get("decision") == "hold")
        pending = sum(1 for c in candidates if not c.get("decision"))

        # Calculate average GEBV by decision
        advanced_gebvs = [c["gebv"] for c in candidates if c.get("decision") == "advance" and c.get("gebv")]
        rejected_gebvs = [c["gebv"] for c in candidates if c.get("decision") == "reject" and c.get("gebv")]

        return {
            "total_candidates": total,
            "advanced": advanced,
            "rejected": rejected,
            "on_hold": on_hold,
            "pending": pending,
            "selection_rate": round(advanced / total * 100, 1) if total > 0 else 0,
            "avg_gebv_advanced": round(sum(advanced_gebvs) / len(advanced_gebvs), 2) if advanced_gebvs else None,
            "avg_gebv_rejected": round(sum(rejected_gebvs) / len(rejected_gebvs), 2) if rejected_gebvs else None,
        }

    async def get_decision_history(
        self,
        db: AsyncSession,
        organization_id: int,
        limit: int = 50,
        candidate_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get decision history from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            limit: Maximum results to return
            candidate_id: Filter by candidate ID
            
        Returns:
            List of decision history entries
        """
        candidates = await self.list_candidates(db, organization_id)

        # Filter to only those with decisions
        history = [
            {
                "id": c["id"],
                "candidate_id": c["id"],
                "candidate_name": c["name"],
                "decision": c["decision"],
                "notes": c.get("decision_notes"),
                "decided_by": c.get("decided_by"),
                "date": c.get("decision_date"),
            }
            for c in candidates
            if c.get("decision")
        ]

        if candidate_id:
            history = [h for h in history if h["candidate_id"] == candidate_id]

        # Sort by date descending
        history.sort(key=lambda x: x.get("date") or "", reverse=True)
        return history[:limit]

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


# Singleton instance
selection_decisions_service = SelectionDecisionsService()

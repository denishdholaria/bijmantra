"""
Trial Planning Service
Manages trial planning, scheduling, and resource allocation.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timezone
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload


class TrialStatus(str, Enum):
    PLANNING = "planning"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TrialType(str, Enum):
    OYT = "OYT"  # Observation Yield Trial
    PYT = "PYT"  # Preliminary Yield Trial
    AYT = "AYT"  # Advanced Yield Trial
    MLT = "MLT"  # Multi-Location Trial
    DST = "DST"  # Disease Screening Trial
    QT = "QT"    # Quality Trial
    DUS = "DUS"  # DUS Trial


class TrialPlanningService:
    """Service for trial planning and scheduling.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def list_trials(
        self,
        db: AsyncSession,
        organization_id: int,
        status: Optional[str] = None,
        trial_type: Optional[str] = None,
        season: Optional[str] = None,
        year: Optional[int] = None,
        crop: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List trials from database with optional filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            status: Filter by status
            trial_type: Filter by trial type
            season: Filter by season
            year: Filter by year
            crop: Filter by crop
            search: Search query
            
        Returns:
            List of trial dictionaries, empty if no data
        """
        from app.models.core import Trial, Program

        stmt = (
            select(Trial)
            .where(Trial.organization_id == organization_id)
            .options(selectinload(Trial.program))
        )

        if status:
            stmt = stmt.where(Trial.additional_info["status"].astext == status)

        result = await db.execute(stmt)
        trials = result.scalars().all()

        if not trials:
            return []

        trial_list = []
        for t in trials:
            info = t.additional_info or {}

            # Apply filters
            t_type = info.get("trial_type")
            t_season = info.get("season")
            t_year = info.get("year")
            t_crop = info.get("crop")
            t_status = info.get("status", "planning")

            if trial_type and t_type != trial_type:
                continue
            if season and t_season != season:
                continue
            if year and t_year != year:
                continue
            if crop and t_crop and t_crop.lower() != crop.lower():
                continue
            if search:
                search_lower = search.lower()
                name = t.trial_name or ""
                objectives = info.get("objectives", "")
                if not (search_lower in name.lower() or search_lower in objectives.lower()):
                    continue

            locations = info.get("locations", [])
            entries = info.get("entries", 0)
            reps = info.get("reps", 1)

            trial_list.append({
                "id": str(t.id),
                "name": t.trial_name,
                "type": t_type,
                "season": t_season,
                "year": t_year,
                "locations": locations,
                "entries": entries,
                "reps": reps,
                "design": info.get("design", "RCBD"),
                "status": t_status,
                "progress": info.get("progress", 0),
                "startDate": info.get("start_date"),
                "endDate": info.get("end_date"),
                "programId": str(t.program_id) if t.program_id else None,
                "programName": t.program.program_name if t.program else None,
                "crop": t_crop,
                "objectives": info.get("objectives"),
                "totalPlots": entries * reps * len(locations) if locations else 0,
                "createdBy": info.get("created_by"),
                "approvedBy": info.get("approved_by"),
                "approvedDate": info.get("approved_date"),
                "createdAt": t.created_at.isoformat() if t.created_at else None,
                "updatedAt": t.updated_at.isoformat() if t.updated_at else None,
            })

        # Sort by start date descending
        trial_list.sort(key=lambda x: x.get("startDate") or "", reverse=True)
        return trial_list

    async def get_trial(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get trial by ID.
        
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
            .where(Trial.organization_id == organization_id)
            .where(Trial.id == int(trial_id))
            .options(selectinload(Trial.program))
        )

        result = await db.execute(stmt)
        t = result.scalar_one_or_none()

        if not t:
            return None

        info = t.additional_info or {}
        locations = info.get("locations", [])
        entries = info.get("entries", 0)
        reps = info.get("reps", 1)

        return {
            "id": str(t.id),
            "name": t.trial_name,
            "type": info.get("trial_type"),
            "season": info.get("season"),
            "year": info.get("year"),
            "locations": locations,
            "entries": entries,
            "reps": reps,
            "design": info.get("design", "RCBD"),
            "status": info.get("status", "planning"),
            "progress": info.get("progress", 0),
            "startDate": info.get("start_date"),
            "endDate": info.get("end_date"),
            "programId": str(t.program_id) if t.program_id else None,
            "programName": t.program.program_name if t.program else None,
            "crop": info.get("crop"),
            "objectives": info.get("objectives"),
            "totalPlots": entries * reps * len(locations) if locations else 0,
            "createdBy": info.get("created_by"),
            "approvedBy": info.get("approved_by"),
            "approvedDate": info.get("approved_date"),
            "createdAt": t.created_at.isoformat() if t.created_at else None,
            "updatedAt": t.updated_at.isoformat() if t.updated_at else None,
            "resources": info.get("resources", []),
        }

    async def create_trial(
        self,
        db: AsyncSession,
        organization_id: int,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new planned trial.
        
        Args:
            db: Database session
            organization_id: Organization ID
            data: Trial data
            
        Returns:
            Created trial dictionary
        """
        from app.models.core import Trial

        trial = Trial(
            organization_id=organization_id,
            trial_name=data["name"],
            program_id=int(data["programId"]) if data.get("programId") else None,
            active=True,
            additional_info={
                "trial_type": data.get("type"),
                "season": data.get("season"),
                "year": data.get("year", date.today().year),
                "locations": data.get("locations", []),
                "entries": data.get("entries", 0),
                "reps": data.get("reps", 1),
                "design": data.get("design", "RCBD"),
                "status": "planning",
                "progress": 0,
                "start_date": data.get("startDate"),
                "end_date": data.get("endDate"),
                "crop": data.get("crop"),
                "objectives": data.get("objectives"),
                "created_by": data.get("createdBy"),
                "resources": [],
            },
        )

        db.add(trial)
        await db.commit()
        await db.refresh(trial)

        return await self.get_trial(db, organization_id, str(trial.id))

    async def update_trial(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: str,
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update a trial.
        
        Args:
            db: Database session
            organization_id: Organization ID
            trial_id: Trial ID
            data: Update data
            
        Returns:
            Updated trial dictionary or None if not found
        """
        from app.models.core import Trial

        stmt = (
            select(Trial)
            .where(Trial.organization_id == organization_id)
            .where(Trial.id == int(trial_id))
        )

        result = await db.execute(stmt)
        trial = result.scalar_one_or_none()

        if not trial:
            return None

        if "name" in data:
            trial.trial_name = data["name"]

        info = trial.additional_info or {}

        for key in ["type", "season", "year", "locations", "entries", "reps",
                    "design", "status", "progress", "objectives", "crop"]:
            if key in data:
                info_key = "trial_type" if key == "type" else key
                info[info_key] = data[key]

        if "startDate" in data:
            info["start_date"] = data["startDate"]
        if "endDate" in data:
            info["end_date"] = data["endDate"]

        trial.additional_info = info
        await db.commit()

        return await self.get_trial(db, organization_id, trial_id)

    async def delete_trial(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: str,
    ) -> bool:
        """Delete a trial.
        
        Args:
            db: Database session
            organization_id: Organization ID
            trial_id: Trial ID
            
        Returns:
            True if deleted, False if not found
        """
        from app.models.core import Trial

        stmt = (
            select(Trial)
            .where(Trial.organization_id == organization_id)
            .where(Trial.id == int(trial_id))
        )

        result = await db.execute(stmt)
        trial = result.scalar_one_or_none()

        if not trial:
            return False

        await db.delete(trial)
        await db.commit()
        return True

    async def approve_trial(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: str,
        approved_by: str,
    ) -> Optional[Dict[str, Any]]:
        """Approve a trial.
        
        Args:
            db: Database session
            organization_id: Organization ID
            trial_id: Trial ID
            approved_by: Approver name
            
        Returns:
            Updated trial dictionary or None
        """
        return await self.update_trial(db, organization_id, trial_id, {
            "status": "approved",
            "approvedBy": approved_by,
            "approvedDate": date.today().isoformat(),
            "progress": 50,
        })

    async def start_trial(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Start a trial (move to active).
        
        Args:
            db: Database session
            organization_id: Organization ID
            trial_id: Trial ID
            
        Returns:
            Updated trial dictionary or None
        """
        return await self.update_trial(db, organization_id, trial_id, {
            "status": "active",
            "progress": 60,
        })

    async def complete_trial(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Complete a trial.
        
        Args:
            db: Database session
            organization_id: Organization ID
            trial_id: Trial ID
            
        Returns:
            Updated trial dictionary or None
        """
        return await self.update_trial(db, organization_id, trial_id, {
            "status": "completed",
            "progress": 100,
            "endDate": date.today().isoformat(),
        })

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict[str, Any]:
        """Get trial planning statistics.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            Statistics dictionary
        """
        trials = await self.list_trials(db, organization_id)

        if not trials:
            return {
                "totalTrials": 0,
                "byStatus": {},
                "byType": {},
                "totalPlots": 0,
                "totalEntries": 0,
                "totalEstimatedCost": 0,
                "planning": 0,
                "active": 0,
                "completed": 0,
            }

        status_counts = {}
        type_counts = {}
        total_plots = 0
        total_entries = 0

        for t in trials:
            status = t.get("status", "planning")
            status_counts[status] = status_counts.get(status, 0) + 1

            t_type = t.get("type")
            if t_type:
                type_counts[t_type] = type_counts.get(t_type, 0) + 1

            total_plots += t.get("totalPlots", 0)
            total_entries += t.get("entries", 0)

        return {
            "totalTrials": len(trials),
            "byStatus": status_counts,
            "byType": type_counts,
            "totalPlots": total_plots,
            "totalEntries": total_entries,
            "totalEstimatedCost": 0,  # Would need resource data
            "planning": status_counts.get("planning", 0),
            "active": status_counts.get("active", 0),
            "completed": status_counts.get("completed", 0),
        }

    async def get_timeline(
        self,
        db: AsyncSession,
        organization_id: int,
        year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get trial timeline for visualization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            year: Filter by year
            
        Returns:
            List of timeline entries
        """
        trials = await self.list_trials(db, organization_id, year=year)

        return [{
            "id": t["id"],
            "name": t["name"],
            "type": t.get("type"),
            "status": t.get("status"),
            "startDate": t.get("startDate"),
            "endDate": t.get("endDate"),
            "locations": len(t.get("locations", [])),
            "progress": t.get("progress", 0),
        } for t in trials]

    def get_trial_types(self) -> List[Dict[str, str]]:
        """Get list of trial types (reference data)."""
        return [
            {"value": "OYT", "label": "Observation Yield Trial"},
            {"value": "PYT", "label": "Preliminary Yield Trial"},
            {"value": "AYT", "label": "Advanced Yield Trial"},
            {"value": "MLT", "label": "Multi-Location Trial"},
            {"value": "DST", "label": "Disease Screening Trial"},
            {"value": "QT", "label": "Quality Trial"},
            {"value": "DUS", "label": "DUS Trial"},
        ]

    async def get_seasons(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> List[str]:
        """Get list of seasons from database.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            List of season names
        """
        trials = await self.list_trials(db, organization_id)
        return list(set(t.get("season") for t in trials if t.get("season")))

    def get_designs(self) -> List[Dict[str, str]]:
        """Get list of trial designs (reference data)."""
        return [
            {"value": "RCBD", "label": "Randomized Complete Block Design"},
            {"value": "Alpha-Lattice", "label": "Alpha-Lattice Design"},
            {"value": "Augmented", "label": "Augmented Design"},
            {"value": "Split-Plot", "label": "Split-Plot Design"},
            {"value": "CRD", "label": "Completely Randomized Design"},
        ]


# Factory function
def get_trial_planning_service() -> TrialPlanningService:
    """Get trial planning service instance."""
    return TrialPlanningService()

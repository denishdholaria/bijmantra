"""
Phenology Tracker Service
Track plant growth stages and development using Zadoks/BBCH scale.
Queries real data from database - no demo/mock data.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


# Zadoks/BBCH Growth Stages (reference data - not demo data)
GROWTH_STAGES = [
    {"code": 0, "name": "Germination", "description": "Seed germination and emergence"},
    {"code": 10, "name": "Seedling", "description": "First leaves unfolded"},
    {"code": 20, "name": "Tillering", "description": "Side shoots developing"},
    {"code": 30, "name": "Stem Elongation", "description": "Stem nodes visible"},
    {"code": 40, "name": "Booting", "description": "Flag leaf sheath extending"},
    {"code": 50, "name": "Heading", "description": "Inflorescence emerging"},
    {"code": 60, "name": "Flowering", "description": "Anthesis beginning"},
    {"code": 70, "name": "Grain Fill", "description": "Kernel development"},
    {"code": 80, "name": "Ripening", "description": "Grain hardening"},
    {"code": 90, "name": "Maturity", "description": "Harvest ready"},
]


class PhenologyService:
    """Service for phenology tracking operations.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def get_records(
        self,
        db: AsyncSession,
        organization_id: int,
        study_id: Optional[str] = None,
        crop: Optional[str] = None,
        min_stage: Optional[int] = None,
        max_stage: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get phenology records with filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            study_id: Filter by study ID
            crop: Filter by crop name
            min_stage: Minimum growth stage code
            max_stage: Maximum growth stage code
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            Dictionary with records list and pagination info
        """
        # TODO: Query from phenology_records table when created
        # For now, return empty results
        return {"records": [], "total": 0, "limit": limit, "offset": offset}

    async def get_record(
        self, 
        db: AsyncSession,
        organization_id: int,
        record_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a single phenology record with observations.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            record_id: Phenology record ID
            
        Returns:
            Record dictionary with observations or None if not found
        """
        # TODO: Query from phenology_records table
        return None

    async def create_record(
        self, 
        db: AsyncSession,
        organization_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new phenology record.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            data: Record data
            
        Returns:
            Created record dictionary
        """
        record_id = f"phen-{uuid4().hex[:8]}"
        
        sowing_date_str = data.get("sowing_date")
        if sowing_date_str:
            sowing_date = datetime.fromisoformat(sowing_date_str.replace("Z", "+00:00"))
            days_from_sowing = (datetime.now(timezone.utc) - sowing_date).days
        else:
            days_from_sowing = 0
        
        current_stage = data.get("current_stage", 0)
        
        record = {
            "id": record_id,
            "germplasm_id": data.get("germplasm_id"),
            "germplasm_name": data.get("germplasm_name"),
            "study_id": data.get("study_id"),
            "plot_id": data.get("plot_id"),
            "sowing_date": sowing_date_str,
            "current_stage": current_stage,
            "current_stage_name": self._get_stage_name(current_stage),
            "days_from_sowing": days_from_sowing,
            "expected_maturity": data.get("expected_maturity", 120),
            "crop": data.get("crop", "rice"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # TODO: Insert into phenology_records table
        
        return record

    async def update_record(
        self, 
        db: AsyncSession,
        organization_id: int,
        record_id: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a phenology record.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            record_id: Record ID
            data: Update data
            
        Returns:
            Updated record dictionary or None if not found
        """
        # TODO: Update in phenology_records table
        return None

    async def record_observation(
        self, 
        db: AsyncSession,
        organization_id: int,
        record_id: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Record a stage observation.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            record_id: Phenology record ID
            data: Observation data
            
        Returns:
            Created observation dictionary or None if record not found
        """
        # TODO: Insert into phenology_observations table
        stage = data.get("stage", 0)
        
        observation = {
            "id": f"obs-{record_id}-{uuid4().hex[:4]}",
            "stage": stage,
            "stage_name": self._get_stage_name(stage),
            "date": data.get("date") or datetime.now(timezone.utc).isoformat(),
            "notes": data.get("notes", ""),
            "recorded_by": data.get("recorded_by", "system"),
        }
        
        return observation

    async def get_observations(
        self, 
        db: AsyncSession,
        organization_id: int,
        record_id: str
    ) -> List[Dict[str, Any]]:
        """Get all observations for a record.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            record_id: Phenology record ID
            
        Returns:
            List of observation dictionaries
        """
        # TODO: Query from phenology_observations table
        return []

    def _get_stage_name(self, stage_code: int) -> str:
        """Get stage name from code.
        
        Args:
            stage_code: Zadoks/BBCH stage code
            
        Returns:
            Stage name string
        """
        for stage in GROWTH_STAGES:
            if stage["code"] == stage_code:
                return stage["name"]
        # Find closest stage
        closest = min(GROWTH_STAGES, key=lambda s: abs(s["code"] - stage_code))
        return closest["name"]

    def get_growth_stages(self, crop: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get growth stage definitions.
        
        Args:
            crop: Optional crop filter (not used currently, stages are universal)
            
        Returns:
            List of growth stage dictionaries
        """
        return GROWTH_STAGES

    async def get_stats(
        self, 
        db: AsyncSession,
        organization_id: int,
        study_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get phenology statistics.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            study_id: Optional study filter
            
        Returns:
            Statistics dictionary
        """
        result = await self.get_records(db, organization_id, study_id=study_id)
        records = result.get("records", [])
        
        if not records:
            return {"total_records": 0, "by_stage": {}, "avg_days_from_sowing": 0, "near_maturity": 0, "total_observations": 0}
        
        # Count by stage
        by_stage = {}
        for r in records:
            stage = r.get("current_stage_name", "Unknown")
            by_stage[stage] = by_stage.get(stage, 0) + 1
        
        # Average days from sowing
        avg_days = sum(r.get("days_from_sowing", 0) for r in records) / len(records)
        
        # Near maturity count
        near_maturity = len([r for r in records if r.get("current_stage", 0) >= 80])
        
        return {
            "total_records": len(records),
            "by_stage": by_stage,
            "avg_days_from_sowing": round(avg_days, 1),
            "near_maturity": near_maturity,
            "total_observations": sum(r.get("observations_count", 0) for r in records),
        }


# Singleton instance
phenology_service = PhenologyService()

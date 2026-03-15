"""
Phenology Tracker Service
Track plant growth stages and development using Zadoks/BBCH scale.
Queries real data from database - no demo/mock data.
"""
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select, desc, func, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.phenology import PhenologyRecord, PhenologyObservation


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
        study_id: str | None = None,
        crop: str | None = None,
        min_stage: int | None = None,
        max_stage: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
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
        query = select(PhenologyRecord).where(
            PhenologyRecord.organization_id == organization_id
        )

        if study_id:
            query = query.where(PhenologyRecord.study_id == study_id)
        if crop:
            query = query.where(PhenologyRecord.crop == crop)
        if min_stage is not None:
            query = query.where(PhenologyRecord.current_stage >= min_stage)
        if max_stage is not None:
            query = query.where(PhenologyRecord.current_stage <= max_stage)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        # Get records with observations loaded (for count)
        query = query.options(selectinload(PhenologyRecord.observations))
        query = query.order_by(desc(PhenologyRecord.created_at)).limit(limit).offset(offset)

        result = await db.execute(query)
        records = result.scalars().all()

        return {
            "records": [self._record_to_dict(r) for r in records],
            "total": total,
            "limit": limit,
            "offset": offset
        }

    async def get_record(
        self,
        db: AsyncSession,
        organization_id: int,
        record_id: str
    ) -> dict[str, Any] | None:
        """Get a single phenology record with observations.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            record_id: Phenology record ID

        Returns:
            Record dictionary with observations or None if not found
        """
        query = select(PhenologyRecord).where(
            PhenologyRecord.organization_id == organization_id,
            PhenologyRecord.record_id == record_id
        ).options(selectinload(PhenologyRecord.observations))

        result = await db.execute(query)
        record = result.scalars().first()

        if not record:
            return None

        return self._record_to_dict(record, include_observations=True)

    async def create_record(
        self,
        db: AsyncSession,
        organization_id: int,
        data: dict[str, Any]
    ) -> dict[str, Any]:
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
        sowing_date = None
        days_from_sowing = 0

        if sowing_date_str:
            try:
                sowing_date = datetime.fromisoformat(sowing_date_str.replace("Z", "+00:00"))
                days_from_sowing = (datetime.now(UTC) - sowing_date).days
            except ValueError:
                pass

        current_stage = data.get("current_stage", 0)
        current_stage_name = self._get_stage_name(current_stage)

        new_record = PhenologyRecord(
            organization_id=organization_id,
            record_id=record_id,
            germplasm_id=data.get("germplasm_id"),
            germplasm_name=data.get("germplasm_name"),
            study_id=data.get("study_id"),
            plot_id=data.get("plot_id"),
            sowing_date=sowing_date,
            current_stage=current_stage,
            current_stage_name=current_stage_name,
            days_from_sowing=days_from_sowing,
            expected_maturity=data.get("expected_maturity", 120),
            crop=data.get("crop", "rice")
        )

        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)

        return self._record_to_dict(new_record)

    async def update_record(
        self,
        db: AsyncSession,
        organization_id: int,
        record_id: str,
        data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a phenology record.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            record_id: Record ID
            data: Update data

        Returns:
            Updated record dictionary or None if not found
        """
        query = select(PhenologyRecord).where(
            PhenologyRecord.organization_id == organization_id,
            PhenologyRecord.record_id == record_id
        ).options(selectinload(PhenologyRecord.observations))

        result = await db.execute(query)
        record = result.scalars().first()

        if not record:
            return None

        if "current_stage" in data:
            record.current_stage = data["current_stage"]
            record.current_stage_name = self._get_stage_name(record.current_stage)

        if "expected_maturity" in data:
            record.expected_maturity = data["expected_maturity"]

        # Update days_from_sowing if sowing_date exists
        if record.sowing_date:
            sowing_date = record.sowing_date
            if sowing_date.tzinfo is None:
                sowing_date = sowing_date.replace(tzinfo=UTC)
            record.days_from_sowing = (datetime.now(UTC) - sowing_date).days

        await db.commit()
        await db.refresh(record)

        return self._record_to_dict(record)

    async def record_observation(
        self,
        db: AsyncSession,
        organization_id: int,
        record_id: str,
        data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Record a stage observation.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            record_id: Phenology record ID
            data: Observation data

        Returns:
            Created observation dictionary or None if record not found
        """
        query = select(PhenologyRecord).where(
            PhenologyRecord.organization_id == organization_id,
            PhenologyRecord.record_id == record_id
        )
        result = await db.execute(query)
        record = result.scalars().first()

        if not record:
            return None

        stage = data.get("stage", 0)
        observation_id = f"obs-{record_id}-{uuid4().hex[:4]}"

        date_str = data.get("date")
        obs_date = datetime.now(UTC)
        if date_str:
            try:
                obs_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        new_observation = PhenologyObservation(
            organization_id=organization_id,
            observation_id=observation_id,
            record_id=record.id, # Link to internal ID
            stage=stage,
            stage_name=self._get_stage_name(stage),
            date=obs_date,
            notes=data.get("notes", ""),
            recorded_by=data.get("recorded_by", "system")
        )

        db.add(new_observation)

        # Also update the record's current stage if this observation is newer or higher stage
        if stage > record.current_stage:
            record.current_stage = stage
            record.current_stage_name = self._get_stage_name(stage)

        await db.commit()
        await db.refresh(new_observation)

        return self._observation_to_dict(new_observation)

    async def get_observations(
        self,
        db: AsyncSession,
        organization_id: int,
        record_id: str
    ) -> list[dict[str, Any]]:
        """Get all observations for a record.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            record_id: Phenology record ID

        Returns:
            List of observation dictionaries
        """
        # First check if record exists and belongs to org
        record_query = select(PhenologyRecord).where(
            PhenologyRecord.organization_id == organization_id,
            PhenologyRecord.record_id == record_id
        )
        record_result = await db.execute(record_query)
        record = record_result.scalars().first()

        if not record:
            return []

        # Query observations
        query = select(PhenologyObservation).where(
            PhenologyObservation.record_id == record.id
        ).order_by(desc(PhenologyObservation.date))

        result = await db.execute(query)
        observations = result.scalars().all()

        return [self._observation_to_dict(obs) for obs in observations]

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
        if not GROWTH_STAGES:
            return "Unknown"
        closest = min(GROWTH_STAGES, key=lambda s: abs(s["code"] - stage_code))
        return closest["name"]

    def get_growth_stages(self, crop: str | None = None) -> list[dict[str, Any]]:
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
        study_id: str | None = None
    ) -> dict[str, Any]:
        """Get phenology statistics.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            study_id: Optional study filter

        Returns:
            Statistics dictionary
        """
        # Base filters
        filters = [PhenologyRecord.organization_id == organization_id]
        if study_id:
            filters.append(PhenologyRecord.study_id == study_id)

        # Total records
        total_query = select(func.count()).where(*filters)
        total_records = await db.scalar(total_query) or 0

        if total_records == 0:
             return {"total_records": 0, "by_stage": {}, "avg_days_from_sowing": 0, "near_maturity": 0, "total_observations": 0}

        # Count by stage
        stage_query = select(
            PhenologyRecord.current_stage_name,
            func.count(PhenologyRecord.id)
        ).where(*filters).group_by(PhenologyRecord.current_stage_name)

        stage_result = await db.execute(stage_query)
        by_stage = {row[0]: row[1] for row in stage_result}

        # Average days from sowing
        avg_query = select(func.avg(PhenologyRecord.days_from_sowing)).where(*filters)
        avg_days = await db.scalar(avg_query) or 0

        # Near maturity (>= 80)
        maturity_query = select(func.count()).where(*filters, PhenologyRecord.current_stage >= 80)
        near_maturity = await db.scalar(maturity_query) or 0

        # Total observations (need join)
        obs_query = select(func.count(PhenologyObservation.id)).join(
            PhenologyRecord, PhenologyObservation.record_id == PhenologyRecord.id
        ).where(*filters)
        total_observations = await db.scalar(obs_query) or 0

        return {
            "total_records": total_records,
            "by_stage": by_stage,
            "avg_days_from_sowing": round(float(avg_days), 1),
            "near_maturity": near_maturity,
            "total_observations": total_observations,
        }

    def _record_to_dict(self, record: PhenologyRecord, include_observations: bool = False) -> dict[str, Any]:
        """Convert record model to dictionary."""
        observations_count = 0
        ins = inspect(record)
        if "observations" not in ins.unloaded:
            observations_count = len(record.observations)

        data = {
            "id": record.record_id,
            "germplasm_id": record.germplasm_id,
            "germplasm_name": record.germplasm_name,
            "study_id": record.study_id,
            "plot_id": record.plot_id,
            "sowing_date": record.sowing_date.isoformat() if record.sowing_date else None,
            "current_stage": record.current_stage,
            "current_stage_name": record.current_stage_name,
            "days_from_sowing": record.days_from_sowing,
            "expected_maturity": record.expected_maturity,
            "crop": record.crop,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "observations_count": observations_count
        }

        if include_observations:
            # Must ensure loaded before calling this if True
            if "observations" not in ins.unloaded and record.observations:
                data["observations"] = [self._observation_to_dict(o) for o in sorted(record.observations, key=lambda x: x.date, reverse=True)]
            else:
                data["observations"] = []

        return data

    def _observation_to_dict(self, obs: PhenologyObservation) -> dict[str, Any]:
        """Convert observation model to dictionary."""
        return {
            "id": obs.observation_id,
            "stage": obs.stage,
            "stage_name": obs.stage_name,
            "date": obs.date.isoformat() if obs.date else None,
            "notes": obs.notes,
            "recorded_by": obs.recorded_by
        }


# Singleton instance
phenology_service = PhenologyService()

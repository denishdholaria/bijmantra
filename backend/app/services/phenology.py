"""
Phenology Tracker Service
Track plant growth stages and development using Zadoks/BBCH scale
"""
from datetime import datetime, UTC, timedelta
from typing import Optional
from uuid import uuid4


# Zadoks/BBCH Growth Stages
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
    """Service for phenology tracking operations."""

    def __init__(self):
        self._records: dict[str, dict] = {}
        self._observations: dict[str, list] = {}
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize demo phenology records."""
        base_date = datetime.now(UTC) - timedelta(days=75)
        
        demo_records = [
            {
                "id": "phen-001",
                "germplasm_id": "germ-001",
                "germplasm_name": "IR64",
                "study_id": "study-2024",
                "plot_id": "A-01",
                "sowing_date": (base_date).isoformat(),
                "current_stage": 50,
                "current_stage_name": "Heading",
                "days_from_sowing": 75,
                "expected_maturity": 120,
                "crop": "rice",
            },
            {
                "id": "phen-002",
                "germplasm_id": "germ-002",
                "germplasm_name": "Nipponbare",
                "study_id": "study-2024",
                "plot_id": "A-02",
                "sowing_date": (base_date - timedelta(days=5)).isoformat(),
                "current_stage": 60,
                "current_stage_name": "Flowering",
                "days_from_sowing": 80,
                "expected_maturity": 115,
                "crop": "rice",
            },
            {
                "id": "phen-003",
                "germplasm_id": "germ-003",
                "germplasm_name": "Kasalath",
                "study_id": "study-2024",
                "plot_id": "A-03",
                "sowing_date": (base_date + timedelta(days=5)).isoformat(),
                "current_stage": 40,
                "current_stage_name": "Booting",
                "days_from_sowing": 70,
                "expected_maturity": 125,
                "crop": "rice",
            },
            {
                "id": "phen-004",
                "germplasm_id": "germ-004",
                "germplasm_name": "N22",
                "study_id": "study-2024",
                "plot_id": "B-01",
                "sowing_date": (base_date - timedelta(days=10)).isoformat(),
                "current_stage": 70,
                "current_stage_name": "Grain Fill",
                "days_from_sowing": 85,
                "expected_maturity": 105,
                "crop": "rice",
            },
            {
                "id": "phen-005",
                "germplasm_id": "germ-005",
                "germplasm_name": "Moroberekan",
                "study_id": "study-2024",
                "plot_id": "B-02",
                "sowing_date": (base_date + timedelta(days=30)).isoformat(),
                "current_stage": 20,
                "current_stage_name": "Tillering",
                "days_from_sowing": 45,
                "expected_maturity": 140,
                "crop": "rice",
            },
        ]
        
        for record in demo_records:
            self._records[record["id"]] = record
            self._observations[record["id"]] = [
                {
                    "id": f"obs-{record['id']}-1",
                    "stage": 0,
                    "stage_name": "Germination",
                    "date": record["sowing_date"],
                    "notes": "Good emergence",
                    "recorded_by": "demo@bijmantra.org",
                },
            ]

    def get_records(
        self,
        study_id: Optional[str] = None,
        crop: Optional[str] = None,
        min_stage: Optional[int] = None,
        max_stage: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get phenology records with filters."""
        records = list(self._records.values())
        
        if study_id:
            records = [r for r in records if r.get("study_id") == study_id]
        if crop:
            records = [r for r in records if r.get("crop", "").lower() == crop.lower()]
        if min_stage is not None:
            records = [r for r in records if r.get("current_stage", 0) >= min_stage]
        if max_stage is not None:
            records = [r for r in records if r.get("current_stage", 0) <= max_stage]
        
        records.sort(key=lambda x: x.get("plot_id", ""))
        total = len(records)
        records = records[offset:offset + limit]
        
        # Add observations count
        for r in records:
            r["observations_count"] = len(self._observations.get(r["id"], []))
            r["days_remaining"] = r.get("expected_maturity", 0) - r.get("days_from_sowing", 0)
        
        return {"records": records, "total": total, "limit": limit, "offset": offset}

    def get_record(self, record_id: str) -> Optional[dict]:
        """Get a single phenology record with observations."""
        record = self._records.get(record_id)
        if record:
            record = record.copy()
            record["observations"] = self._observations.get(record_id, [])
        return record

    def create_record(self, data: dict) -> dict:
        """Create a new phenology record."""
        record_id = f"phen-{uuid4().hex[:8]}"
        
        # Calculate days from sowing
        sowing_date = datetime.fromisoformat(data.get("sowing_date", datetime.now(UTC).isoformat()))
        days_from_sowing = (datetime.now(UTC) - sowing_date).days
        
        record = {
            "id": record_id,
            "germplasm_id": data.get("germplasm_id"),
            "germplasm_name": data.get("germplasm_name"),
            "study_id": data.get("study_id"),
            "plot_id": data.get("plot_id"),
            "sowing_date": data.get("sowing_date"),
            "current_stage": data.get("current_stage", 0),
            "current_stage_name": self._get_stage_name(data.get("current_stage", 0)),
            "days_from_sowing": days_from_sowing,
            "expected_maturity": data.get("expected_maturity", 120),
            "crop": data.get("crop", "rice"),
            "created_at": datetime.now(UTC).isoformat(),
        }
        
        self._records[record_id] = record
        self._observations[record_id] = []
        
        return record

    def update_record(self, record_id: str, data: dict) -> Optional[dict]:
        """Update a phenology record."""
        if record_id not in self._records:
            return None
        
        record = self._records[record_id]
        
        if "current_stage" in data:
            record["current_stage"] = data["current_stage"]
            record["current_stage_name"] = self._get_stage_name(data["current_stage"])
        if "expected_maturity" in data:
            record["expected_maturity"] = data["expected_maturity"]
        
        # Recalculate days
        if record.get("sowing_date"):
            sowing_date = datetime.fromisoformat(record["sowing_date"])
            record["days_from_sowing"] = (datetime.now(UTC) - sowing_date).days
        
        return record

    def record_observation(self, record_id: str, data: dict) -> Optional[dict]:
        """Record a stage observation."""
        if record_id not in self._records:
            return None
        
        obs_id = f"obs-{record_id}-{len(self._observations.get(record_id, [])) + 1}"
        stage = data.get("stage", 0)
        
        observation = {
            "id": obs_id,
            "stage": stage,
            "stage_name": self._get_stage_name(stage),
            "date": data.get("date") or datetime.now(UTC).isoformat(),
            "notes": data.get("notes", ""),
            "recorded_by": data.get("recorded_by", "system"),
        }
        
        if record_id not in self._observations:
            self._observations[record_id] = []
        self._observations[record_id].append(observation)
        
        # Update current stage if this is the latest
        record = self._records[record_id]
        if stage > record.get("current_stage", 0):
            record["current_stage"] = stage
            record["current_stage_name"] = self._get_stage_name(stage)
        
        return observation

    def get_observations(self, record_id: str) -> list[dict]:
        """Get all observations for a record."""
        return self._observations.get(record_id, [])

    def _get_stage_name(self, stage_code: int) -> str:
        """Get stage name from code."""
        for stage in GROWTH_STAGES:
            if stage["code"] == stage_code:
                return stage["name"]
        # Find closest stage
        closest = min(GROWTH_STAGES, key=lambda s: abs(s["code"] - stage_code))
        return closest["name"]

    def get_growth_stages(self, crop: Optional[str] = None) -> list[dict]:
        """Get growth stage definitions."""
        return GROWTH_STAGES

    def get_stats(self, study_id: Optional[str] = None) -> dict:
        """Get phenology statistics."""
        records = list(self._records.values())
        
        if study_id:
            records = [r for r in records if r.get("study_id") == study_id]
        
        if not records:
            return {"total_records": 0, "by_stage": {}, "avg_days": 0}
        
        # Count by stage
        by_stage = {}
        for r in records:
            stage = r.get("current_stage_name", "Unknown")
            by_stage[stage] = by_stage.get(stage, 0) + 1
        
        # Average days from sowing
        avg_days = sum(r.get("days_from_sowing", 0) for r in records) / len(records)
        
        # Maturity forecast
        near_maturity = len([r for r in records if r.get("current_stage", 0) >= 80])
        
        return {
            "total_records": len(records),
            "by_stage": by_stage,
            "avg_days_from_sowing": round(avg_days, 1),
            "near_maturity": near_maturity,
            "total_observations": sum(len(self._observations.get(r["id"], [])) for r in records),
        }


# Singleton instance
phenology_service = PhenologyService()

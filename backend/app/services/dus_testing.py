"""
DUS Testing Service (Distinctness, Uniformity, Stability)

UPOV-compliant variety testing for Plant Variety Protection (PVP).
Converted to use real database queries per Zero Mock Data Policy.
"""

from datetime import datetime, UTC
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import math

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dus import DUSTrial as DUSTrialModel, DUSEntry as DUSEntryModel, DUSScore as DUSScoreModel


# ============ Enums ============

class CharacterType(str, Enum):
    VG = "VG"  # Visual assessment - Grouping
    MG = "MG"  # Measurement - Grouping
    VS = "VS"  # Visual assessment - Single
    MS = "MS"  # Measurement - Single
    PQ = "PQ"  # Pseudo-qualitative
    QN = "QN"  # Quantitative
    QL = "QL"  # Qualitative


class TrialStatus(str, Enum):
    PLANNED = "planned"
    YEAR_1 = "year_1"
    YEAR_2 = "year_2"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DUSResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"


# ============ Schemas ============

class DUSCharacter(BaseModel):
    """UPOV DUS character definition"""
    id: str
    number: int
    name: str
    type: CharacterType
    states: List[Dict[str, Any]]
    grouping: bool = False
    asterisk: bool = False
    notes: Optional[str] = None


class CropTemplate(BaseModel):
    """Crop-specific DUS template based on UPOV Test Guidelines"""
    crop_code: str
    crop_name: str
    scientific_name: str
    upov_code: str
    test_guideline: str
    characters: List[DUSCharacter]
    uniformity_threshold: float = 1.0
    min_sample_size: int = 100
    test_years: int = 2


# ============ Crop Templates (UPOV Test Guidelines) ============
# These are static reference data from UPOV and remain as code constants

RICE_CHARACTERS = [
    DUSCharacter(id="rice_1", number=1, name="Coleoptile: color", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Colorless"}, {"code": 2, "description": "Green"}, {"code": 3, "description": "Purple"}]),
    DUSCharacter(id="rice_2", number=2, name="Leaf: intensity of green color", type=CharacterType.VG, grouping=True,
                 states=[{"code": 1, "description": "Light"}, {"code": 3, "description": "Medium"}, {"code": 5, "description": "Dark"}]),
    DUSCharacter(id="rice_3", number=3, name="Leaf: anthocyanin coloration", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 9, "description": "Present"}]),
    DUSCharacter(id="rice_11", number=11, name="Time of heading (50% panicle emergence)", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very early"}, {"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}, {"code": 9, "description": "Very late"}]),
    DUSCharacter(id="rice_16", number=16, name="Grain: length", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very short"}, {"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Long"}, {"code": 9, "description": "Very long"}]),
    DUSCharacter(id="rice_17", number=17, name="Grain: width", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very narrow"}, {"code": 3, "description": "Narrow"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Broad"}, {"code": 9, "description": "Very broad"}]),
    DUSCharacter(id="rice_20", number=20, name="Grain: aroma", type=CharacterType.QL, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 9, "description": "Present"}]),
]

RICE_TEMPLATE = CropTemplate(
    crop_code="rice", crop_name="Rice", scientific_name="Oryza sativa L.",
    upov_code="ORYZA_SAT", test_guideline="TG/16/8", characters=RICE_CHARACTERS,
    uniformity_threshold=1.0, min_sample_size=100, test_years=2,
)


WHEAT_CHARACTERS = [
    DUSCharacter(id="wheat_1", number=1, name="Coleoptile: anthocyanin coloration", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}, {"code": 9, "description": "Very strong"}]),
    DUSCharacter(id="wheat_2", number=2, name="Plant: growth habit", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Erect"}, {"code": 3, "description": "Semi-erect"}, {"code": 5, "description": "Intermediate"}, {"code": 7, "description": "Semi-prostrate"}, {"code": 9, "description": "Prostrate"}]),
    DUSCharacter(id="wheat_4", number=4, name="Time of ear emergence", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very early"}, {"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}, {"code": 9, "description": "Very late"}]),
    DUSCharacter(id="wheat_8", number=8, name="Plant: height", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very short"}, {"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Tall"}, {"code": 9, "description": "Very tall"}]),
    DUSCharacter(id="wheat_13", number=13, name="Grain: color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Red"}]),
    DUSCharacter(id="wheat_15", number=15, name="Seasonal type", type=CharacterType.QL, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Winter type"}, {"code": 2, "description": "Spring type"}]),
]

WHEAT_TEMPLATE = CropTemplate(
    crop_code="wheat", crop_name="Wheat", scientific_name="Triticum aestivum L.",
    upov_code="TRITI_AES", test_guideline="TG/3/12", characters=WHEAT_CHARACTERS,
    uniformity_threshold=1.0, min_sample_size=100, test_years=2,
)


MAIZE_CHARACTERS = [
    DUSCharacter(id="maize_1", number=1, name="First leaf: anthocyanin coloration of sheath", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}, {"code": 9, "description": "Very strong"}]),
    DUSCharacter(id="maize_5", number=5, name="Tassel: time of anthesis", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very early"}, {"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}, {"code": 9, "description": "Very late"}]),
    DUSCharacter(id="maize_11", number=11, name="Plant: height", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very short"}, {"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Tall"}, {"code": 9, "description": "Very tall"}]),
    DUSCharacter(id="maize_17", number=17, name="Grain: type", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Flint"}, {"code": 2, "description": "Flint-like"}, {"code": 3, "description": "Intermediate"}, {"code": 4, "description": "Dent-like"}, {"code": 5, "description": "Dent"}, {"code": 6, "description": "Sweet"}, {"code": 7, "description": "Pop"}]),
    DUSCharacter(id="maize_18", number=18, name="Grain: color of top of grain", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Whitish yellow"}, {"code": 3, "description": "Yellow"}, {"code": 4, "description": "Orange"}, {"code": 5, "description": "Red"}, {"code": 6, "description": "Purple"}]),
]

MAIZE_TEMPLATE = CropTemplate(
    crop_code="maize", crop_name="Maize", scientific_name="Zea mays L.",
    upov_code="ZEA_MAY", test_guideline="TG/2/7", characters=MAIZE_CHARACTERS,
    uniformity_threshold=1.0, min_sample_size=100, test_years=2,
)

CROP_TEMPLATES: Dict[str, CropTemplate] = {
    "rice": RICE_TEMPLATE,
    "wheat": WHEAT_TEMPLATE,
    "maize": MAIZE_TEMPLATE,
}

try:
    from app.services.dus_crops import ADDITIONAL_CROP_TEMPLATES
    CROP_TEMPLATES.update(ADDITIONAL_CROP_TEMPLATES)
except ImportError:
    pass


# ============ DUS Testing Service ============

class DUSTestingService:
    """
    Service for DUS (Distinctness, Uniformity, Stability) testing.
    
    All methods are async and require AsyncSession and organization_id
    for multi-tenant isolation per GOVERNANCE.md §4.3.1.
    """

    async def _generate_trial_code(self, db: AsyncSession, organization_id: int, year: int) -> str:
        """Generate unique trial code."""
        stmt = select(func.count(DUSTrialModel.id)).where(
            and_(
                DUSTrialModel.organization_id == organization_id,
                DUSTrialModel.trial_code.like(f"DUS-{year}-%")
            )
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0
        return f"DUS-{year}-{count + 1:03d}"

    # ============ Crop Templates (Static UPOV Data) ============

    def get_crop_templates(self) -> List[Dict[str, Any]]:
        """Get list of available crop templates."""
        return [
            {
                "crop_code": t.crop_code,
                "crop_name": t.crop_name,
                "scientific_name": t.scientific_name,
                "upov_code": t.upov_code,
                "test_guideline": t.test_guideline,
                "character_count": len(t.characters),
                "uniformity_threshold": t.uniformity_threshold,
                "test_years": t.test_years,
            }
            for t in CROP_TEMPLATES.values()
        ]

    def get_crop_template(self, crop_code: str) -> Optional[CropTemplate]:
        """Get crop template by code."""
        return CROP_TEMPLATES.get(crop_code.lower())

    def get_crop_characters(self, crop_code: str) -> List[Dict[str, Any]]:
        """Get characters for a crop."""
        template = self.get_crop_template(crop_code)
        if not template:
            return []
        return [c.model_dump() for c in template.characters]

    def get_grouping_characters(self, crop_code: str) -> List[Dict[str, Any]]:
        """Get grouping characters for initial screening."""
        template = self.get_crop_template(crop_code)
        if not template:
            return []
        return [c.model_dump() for c in template.characters if c.grouping]

    def get_asterisk_characters(self, crop_code: str) -> List[Dict[str, Any]]:
        """Get asterisk (important) characters for distinctness."""
        template = self.get_crop_template(crop_code)
        if not template:
            return []
        return [c.model_dump() for c in template.characters if c.asterisk]


    # ============ Trial Management ============

    async def create_trial(
        self,
        db: AsyncSession,
        organization_id: int,
        crop_code: str,
        trial_name: str,
        year: int,
        location: str,
        sample_size: int = 100,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new DUS trial."""
        trial_code = await self._generate_trial_code(db, organization_id, year)
        
        trial = DUSTrialModel(
            trial_code=trial_code,
            trial_name=trial_name,
            crop_code=crop_code.lower(),
            year=year,
            location=location,
            sample_size=sample_size,
            status=TrialStatus.PLANNED.value,
            notes=notes,
            organization_id=organization_id,
        )
        db.add(trial)
        await db.commit()
        await db.refresh(trial)
        
        return self._trial_to_dict(trial)

    async def get_trial(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Get trial by ID with entries and scores."""
        stmt = select(DUSTrialModel).options(
            selectinload(DUSTrialModel.entries).selectinload(DUSEntryModel.scores)
        ).where(
            and_(
                DUSTrialModel.organization_id == organization_id,
                DUSTrialModel.id == trial_id
            )
        )
        result = await db.execute(stmt)
        trial = result.scalar_one_or_none()
        
        return self._trial_to_dict(trial) if trial else None

    async def list_trials(
        self,
        db: AsyncSession,
        organization_id: int,
        crop_code: Optional[str] = None,
        year: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List trials with optional filters."""
        stmt = select(DUSTrialModel).options(
            selectinload(DUSTrialModel.entries)
        ).where(
            DUSTrialModel.organization_id == organization_id
        )
        
        if crop_code:
            stmt = stmt.where(DUSTrialModel.crop_code == crop_code.lower())
        if year:
            stmt = stmt.where(DUSTrialModel.year == year)
        if status:
            stmt = stmt.where(DUSTrialModel.status == status)
        
        stmt = stmt.order_by(DUSTrialModel.created_at.desc()).limit(limit)
        
        result = await db.execute(stmt)
        trials = result.scalars().all()
        
        return [self._trial_to_dict(t) for t in trials]

    async def update_trial_status(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: int,
        status: str,
    ) -> Optional[Dict[str, Any]]:
        """Update trial status."""
        stmt = select(DUSTrialModel).where(
            and_(
                DUSTrialModel.organization_id == organization_id,
                DUSTrialModel.id == trial_id
            )
        )
        result = await db.execute(stmt)
        trial = result.scalar_one_or_none()
        
        if not trial:
            return None
        
        trial.status = status
        await db.commit()
        await db.refresh(trial)
        
        return self._trial_to_dict(trial)


    # ============ Entry Management ============

    async def add_entry(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: int,
        variety_name: str,
        is_candidate: bool = False,
        is_reference: bool = False,
        breeder: Optional[str] = None,
        origin: Optional[str] = None,
        germplasm_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Add entry to trial."""
        # Verify trial exists and belongs to org
        trial_stmt = select(DUSTrialModel).where(
            and_(
                DUSTrialModel.organization_id == organization_id,
                DUSTrialModel.id == trial_id
            )
        )
        trial_result = await db.execute(trial_stmt)
        trial = trial_result.scalar_one_or_none()
        
        if not trial:
            return None
        
        # Count existing entries for entry_code
        count_stmt = select(func.count(DUSEntryModel.id)).where(
            DUSEntryModel.trial_id == trial_id
        )
        count_result = await db.execute(count_stmt)
        count = count_result.scalar() or 0
        
        entry = DUSEntryModel(
            trial_id=trial_id,
            entry_code=f"E{count + 1}",
            variety_name=variety_name,
            is_candidate=is_candidate,
            is_reference=is_reference,
            breeder=breeder,
            origin=origin,
            germplasm_id=germplasm_id,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        
        return self._entry_to_dict(entry)

    async def get_entries(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: int,
    ) -> List[Dict[str, Any]]:
        """Get all entries for a trial."""
        # Verify trial belongs to org
        trial_stmt = select(DUSTrialModel.id).where(
            and_(
                DUSTrialModel.organization_id == organization_id,
                DUSTrialModel.id == trial_id
            )
        )
        trial_result = await db.execute(trial_stmt)
        if not trial_result.scalar_one_or_none():
            return []
        
        stmt = select(DUSEntryModel).options(
            selectinload(DUSEntryModel.scores)
        ).where(
            DUSEntryModel.trial_id == trial_id
        ).order_by(DUSEntryModel.entry_code)
        
        result = await db.execute(stmt)
        entries = result.scalars().all()
        
        return [self._entry_to_dict(e) for e in entries]


    # ============ Scoring ============

    async def record_score(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: int,
        entry_id: int,
        character_id: str,
        value: float,
        observation_year: int = 1,
        notes: Optional[str] = None,
        scored_by: Optional[str] = None,
    ) -> bool:
        """Record character score for an entry."""
        # Verify entry belongs to trial in org
        stmt = select(DUSEntryModel).join(DUSTrialModel).where(
            and_(
                DUSTrialModel.organization_id == organization_id,
                DUSTrialModel.id == trial_id,
                DUSEntryModel.id == entry_id
            )
        )
        result = await db.execute(stmt)
        entry = result.scalar_one_or_none()
        
        if not entry:
            return False
        
        # Check for existing score
        existing_stmt = select(DUSScoreModel).where(
            and_(
                DUSScoreModel.entry_id == entry_id,
                DUSScoreModel.character_id == character_id,
                DUSScoreModel.observation_year == observation_year
            )
        )
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            existing.value = value
            existing.notes = notes
            existing.scored_by = scored_by
            existing.scored_at = datetime.now(UTC)
        else:
            score = DUSScoreModel(
                entry_id=entry_id,
                character_id=character_id,
                value=value,
                observation_year=observation_year,
                notes=notes,
                scored_by=scored_by,
                scored_at=datetime.now(UTC),
            )
            db.add(score)
        
        await db.commit()
        return True

    async def bulk_record_scores(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: int,
        entry_id: int,
        scores: List[Dict[str, Any]],
        observation_year: int = 1,
        scored_by: Optional[str] = None,
    ) -> int:
        """Record multiple scores at once."""
        count = 0
        for score in scores:
            if await self.record_score(
                db=db,
                organization_id=organization_id,
                trial_id=trial_id,
                entry_id=entry_id,
                character_id=score["character_id"],
                value=score["value"],
                observation_year=observation_year,
                notes=score.get("notes"),
                scored_by=scored_by,
            ):
                count += 1
        return count


    # ============ DUS Analysis ============

    async def analyze_distinctness(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: int,
        candidate_entry_id: int,
    ) -> Dict[str, Any]:
        """Analyze distinctness of candidate variety against reference varieties."""
        trial = await self.get_trial(db, organization_id, trial_id)
        if not trial:
            return {"error": "Trial not found"}
        
        template = self.get_crop_template(trial["crop_code"])
        if not template:
            return {"error": "Crop template not found"}
        
        # Find candidate and references
        candidate = None
        references = []
        for entry in trial.get("entries", []):
            if entry["entry_id"] == candidate_entry_id:
                candidate = entry
            elif entry["is_reference"]:
                references.append(entry)
        
        if not candidate:
            return {"error": "Candidate entry not found"}
        if not references:
            return {"error": "No reference varieties in trial"}
        
        # Get candidate scores as dict
        candidate_scores = {s["character_id"]: s["value"] for s in candidate.get("scores", [])}
        
        comparisons = []
        for ref in references:
            ref_scores = {s["character_id"]: s["value"] for s in ref.get("scores", [])}
            
            differences = []
            for char in template.characters:
                cand_val = candidate_scores.get(char.id)
                ref_val = ref_scores.get(char.id)
                
                if cand_val is not None and ref_val is not None and cand_val != ref_val:
                    differences.append({
                        "character_id": char.id,
                        "character_name": char.name,
                        "candidate_value": cand_val,
                        "reference_value": ref_val,
                        "is_asterisk": char.asterisk,
                    })
            
            is_distinct = len(differences) > 0
            comparisons.append({
                "reference_variety": ref["variety_name"],
                "reference_entry_id": ref["entry_id"],
                "is_distinct": is_distinct,
                "difference_count": len(differences),
                "differences": differences,
            })
        
        all_distinct = all(c["is_distinct"] for c in comparisons)
        
        return {
            "trial_id": trial_id,
            "candidate_variety": candidate["variety_name"],
            "candidate_entry_id": candidate_entry_id,
            "result": DUSResult.PASS.value if all_distinct else DUSResult.FAIL.value,
            "is_distinct": all_distinct,
            "comparisons": comparisons,
            "summary": f"Distinct from {sum(1 for c in comparisons if c['is_distinct'])}/{len(comparisons)} reference varieties",
        }


    def calculate_uniformity(
        self,
        off_type_count: int,
        sample_size: int,
        threshold_percentage: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Calculate uniformity based on off-type count.
        Uses UPOV standard for self-pollinated crops.
        """
        threshold = threshold_percentage / 100
        max_off_types = self._get_max_off_types(sample_size, threshold)
        
        off_type_percentage = (off_type_count / sample_size) * 100
        is_uniform = off_type_count <= max_off_types
        
        return {
            "sample_size": sample_size,
            "off_type_count": off_type_count,
            "off_type_percentage": round(off_type_percentage, 2),
            "threshold_percentage": threshold_percentage,
            "max_allowed_off_types": max_off_types,
            "result": DUSResult.PASS.value if is_uniform else DUSResult.FAIL.value,
            "is_uniform": is_uniform,
        }

    def _get_max_off_types(self, sample_size: int, threshold: float) -> int:
        """Get maximum allowed off-types based on sample size and threshold."""
        upov_table = {20: 1, 50: 2, 100: 3, 200: 5, 300: 7, 500: 9, 1000: 15}
        
        sizes = sorted(upov_table.keys())
        for size in sizes:
            if sample_size <= size:
                base = upov_table[size]
                if threshold > 0.01:
                    return int(base * (threshold / 0.01))
                return base
        
        return int(sample_size * threshold * 1.5)

    async def assess_stability(
        self,
        db: AsyncSession,
        organization_id: int,
        trial_id: int,
        entry_id: int,
    ) -> Dict[str, Any]:
        """Assess stability by comparing scores across two years."""
        trial = await self.get_trial(db, organization_id, trial_id)
        if not trial:
            return {"error": "Trial not found"}
        
        template = self.get_crop_template(trial["crop_code"])
        if not template:
            return {"error": "Crop template not found"}
        
        # Find entry
        entry = None
        for e in trial.get("entries", []):
            if e["entry_id"] == entry_id:
                entry = e
                break
        
        if not entry:
            return {"error": "Entry not found"}
        
        # Separate scores by year
        year1_scores = {s["character_id"]: s["value"] for s in entry.get("scores", []) if s.get("observation_year") == 1}
        year2_scores = {s["character_id"]: s["value"] for s in entry.get("scores", []) if s.get("observation_year") == 2}
        
        if not year1_scores or not year2_scores:
            return {"error": "Requires scores from both years", "status": "pending"}
        
        changes = []
        for char in template.characters:
            y1_val = year1_scores.get(char.id)
            y2_val = year2_scores.get(char.id)
            
            if y1_val is not None and y2_val is not None and y1_val != y2_val:
                changes.append({
                    "character_id": char.id,
                    "character_name": char.name,
                    "year1_value": y1_val,
                    "year2_value": y2_val,
                    "is_asterisk": char.asterisk,
                })
        
        asterisk_changes = [c for c in changes if c["is_asterisk"]]
        is_stable = len(asterisk_changes) == 0
        
        return {
            "trial_id": trial_id,
            "entry_id": entry_id,
            "result": DUSResult.PASS.value if is_stable else DUSResult.FAIL.value,
            "is_stable": is_stable,
            "total_changes": len(changes),
            "asterisk_changes": len(asterisk_changes),
            "changes": changes,
            "summary": f"{len(changes)} character(s) changed, {len(asterisk_changes)} asterisk character(s)",
        }


    # ============ Helper Methods ============

    def _trial_to_dict(self, trial: DUSTrialModel) -> Dict[str, Any]:
        """Convert DUSTrial model to dictionary."""
        return {
            "trial_id": trial.id,
            "trial_code": trial.trial_code,
            "trial_name": trial.trial_name,
            "crop_code": trial.crop_code,
            "year": trial.year,
            "location": trial.location,
            "sample_size": trial.sample_size,
            "status": trial.status,
            "distinctness_result": trial.distinctness_result,
            "uniformity_result": trial.uniformity_result,
            "stability_result": trial.stability_result,
            "overall_result": trial.overall_result,
            "notes": trial.notes,
            "created_at": trial.created_at.isoformat() if trial.created_at else None,
            "entries": [self._entry_to_dict(e) for e in trial.entries] if trial.entries else [],
        }

    def _entry_to_dict(self, entry: DUSEntryModel) -> Dict[str, Any]:
        """Convert DUSEntry model to dictionary."""
        return {
            "entry_id": entry.id,
            "entry_code": entry.entry_code,
            "variety_name": entry.variety_name,
            "is_candidate": entry.is_candidate,
            "is_reference": entry.is_reference,
            "breeder": entry.breeder,
            "origin": entry.origin,
            "germplasm_id": entry.germplasm_id,
            "off_type_count": entry.off_type_count,
            "uniformity_passed": entry.uniformity_passed,
            "notes": entry.notes,
            "scores": [self._score_to_dict(s) for s in entry.scores] if entry.scores else [],
        }

    def _score_to_dict(self, score: DUSScoreModel) -> Dict[str, Any]:
        """Convert DUSScore model to dictionary."""
        return {
            "score_id": score.id,
            "character_id": score.character_id,
            "value": score.value,
            "value_text": score.value_text,
            "observation_year": score.observation_year,
            "scored_by": score.scored_by,
            "scored_at": score.scored_at.isoformat() if score.scored_at else None,
            "notes": score.notes,
        }


# Service instance
dus_service = DUSTestingService()


def get_dus_service() -> DUSTestingService:
    return dus_service

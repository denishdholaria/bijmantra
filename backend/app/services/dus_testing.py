"""
DUS Testing Service (Distinctness, Uniformity, Stability)

UPOV-compliant variety testing for Plant Variety Protection (PVP).
"""

from datetime import datetime, UTC, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import math


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
    states: List[Dict[str, Any]]  # [{code: 1, description: "Light"}, ...]
    grouping: bool = False
    asterisk: bool = False  # UPOV asterisk (important for distinctness)
    notes: Optional[str] = None


class CropTemplate(BaseModel):
    """Crop-specific DUS template based on UPOV Test Guidelines"""
    crop_code: str
    crop_name: str
    scientific_name: str
    upov_code: str
    test_guideline: str
    characters: List[DUSCharacter]
    uniformity_threshold: float = 1.0  # Percentage
    min_sample_size: int = 100
    test_years: int = 2


class CharacterScore(BaseModel):
    """Score for a single character observation"""
    character_id: str
    value: Any  # Can be int (state code) or float (measurement)
    notes: Optional[str] = None
    scored_by: Optional[str] = None
    scored_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TrialEntry(BaseModel):
    """Entry (variety) in a DUS trial"""
    entry_id: str
    variety_name: str
    is_candidate: bool = False
    is_reference: bool = False
    breeder: Optional[str] = None
    origin: Optional[str] = None
    scores: List[CharacterScore] = []


class DUSTrial(BaseModel):
    """DUS trial for variety testing"""
    id: str
    crop_code: str
    trial_name: str
    year: int
    location: str
    status: TrialStatus = TrialStatus.PLANNED
    entries: List[TrialEntry] = []
    sample_size: int = 100
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    notes: Optional[str] = None



# ============ Crop Templates (UPOV Test Guidelines) ============

# Rice (Oryza sativa) - UPOV TG/16/8
RICE_CHARACTERS = [
    DUSCharacter(id="rice_1", number=1, name="Coleoptile: color", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Colorless"}, {"code": 2, "description": "Green"}, {"code": 3, "description": "Purple"}]),
    DUSCharacter(id="rice_2", number=2, name="Leaf: intensity of green color", type=CharacterType.VG, grouping=True,
                 states=[{"code": 1, "description": "Light"}, {"code": 3, "description": "Medium"}, {"code": 5, "description": "Dark"}]),
    DUSCharacter(id="rice_3", number=3, name="Leaf: anthocyanin coloration", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 9, "description": "Present"}]),
    DUSCharacter(id="rice_4", number=4, name="Leaf: pubescence of blade surface", type=CharacterType.VG,
                 states=[{"code": 1, "description": "Absent"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}]),
    DUSCharacter(id="rice_5", number=5, name="Leaf: auricles", type=CharacterType.QL, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 9, "description": "Present"}]),
    DUSCharacter(id="rice_6", number=6, name="Leaf: color of auricles", type=CharacterType.PQ,
                 states=[{"code": 1, "description": "Light green"}, {"code": 2, "description": "Purple"}]),
    DUSCharacter(id="rice_7", number=7, name="Leaf: color of ligule", type=CharacterType.PQ,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Light purple"}, {"code": 3, "description": "Purple"}]),
    DUSCharacter(id="rice_8", number=8, name="Leaf: length of blade", type=CharacterType.QN, grouping=True,
                 states=[{"code": 1, "description": "Very short"}, {"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Long"}, {"code": 9, "description": "Very long"}]),
    DUSCharacter(id="rice_9", number=9, name="Leaf: width of blade", type=CharacterType.QN, grouping=True,
                 states=[{"code": 1, "description": "Very narrow"}, {"code": 3, "description": "Narrow"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Broad"}, {"code": 9, "description": "Very broad"}]),
    DUSCharacter(id="rice_10", number=10, name="Culm: attitude", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Erect"}, {"code": 3, "description": "Semi-erect"}, {"code": 5, "description": "Open"}, {"code": 7, "description": "Spreading"}]),
    DUSCharacter(id="rice_11", number=11, name="Time of heading (50% panicle emergence)", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very early"}, {"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}, {"code": 9, "description": "Very late"}]),
    DUSCharacter(id="rice_12", number=12, name="Panicle: length", type=CharacterType.QN, asterisk=True,
                 states=[{"code": 1, "description": "Very short"}, {"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Long"}, {"code": 9, "description": "Very long"}]),
    DUSCharacter(id="rice_13", number=13, name="Panicle: attitude of branches", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Erect"}, {"code": 3, "description": "Semi-erect"}, {"code": 5, "description": "Spreading"}, {"code": 7, "description": "Drooping"}]),
    DUSCharacter(id="rice_14", number=14, name="Panicle: exsertion", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Enclosed"}, {"code": 3, "description": "Partly exserted"}, {"code": 5, "description": "Just exserted"}, {"code": 7, "description": "Moderately exserted"}, {"code": 9, "description": "Well exserted"}]),
    DUSCharacter(id="rice_15", number=15, name="Spikelet: color of stigma", type=CharacterType.PQ,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Light green"}, {"code": 3, "description": "Yellow"}, {"code": 4, "description": "Light purple"}, {"code": 5, "description": "Purple"}]),
    DUSCharacter(id="rice_16", number=16, name="Grain: length", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very short"}, {"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Long"}, {"code": 9, "description": "Very long"}]),
    DUSCharacter(id="rice_17", number=17, name="Grain: width", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very narrow"}, {"code": 3, "description": "Narrow"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Broad"}, {"code": 9, "description": "Very broad"}]),
    DUSCharacter(id="rice_18", number=18, name="Grain: shape (length/width ratio)", type=CharacterType.MG, grouping=True,
                 states=[{"code": 1, "description": "Round"}, {"code": 3, "description": "Semi-round"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Long"}, {"code": 9, "description": "Very long"}]),
    DUSCharacter(id="rice_19", number=19, name="Grain: color of pericarp", type=CharacterType.PQ, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Light brown"}, {"code": 3, "description": "Brown"}, {"code": 4, "description": "Red"}, {"code": 5, "description": "Purple"}]),
    DUSCharacter(id="rice_20", number=20, name="Grain: aroma", type=CharacterType.QL, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 9, "description": "Present"}]),
]

RICE_TEMPLATE = CropTemplate(
    crop_code="rice",
    crop_name="Rice",
    scientific_name="Oryza sativa L.",
    upov_code="ORYZA_SAT",
    test_guideline="TG/16/8",
    characters=RICE_CHARACTERS,
    uniformity_threshold=1.0,
    min_sample_size=100,
    test_years=2,
)


# Wheat (Triticum aestivum) - UPOV TG/3/12
WHEAT_CHARACTERS = [
    DUSCharacter(id="wheat_1", number=1, name="Coleoptile: anthocyanin coloration", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}, {"code": 9, "description": "Very strong"}]),
    DUSCharacter(id="wheat_2", number=2, name="Plant: growth habit", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Erect"}, {"code": 3, "description": "Semi-erect"}, {"code": 5, "description": "Intermediate"}, {"code": 7, "description": "Semi-prostrate"}, {"code": 9, "description": "Prostrate"}]),
    DUSCharacter(id="wheat_3", number=3, name="Flag leaf: anthocyanin coloration of auricles", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}, {"code": 9, "description": "Very strong"}]),
    DUSCharacter(id="wheat_4", number=4, name="Time of ear emergence", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very early"}, {"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}, {"code": 9, "description": "Very late"}]),
    DUSCharacter(id="wheat_5", number=5, name="Flag leaf: glaucosity of sheath", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}, {"code": 9, "description": "Very strong"}]),
    DUSCharacter(id="wheat_6", number=6, name="Culm: glaucosity of neck", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}, {"code": 9, "description": "Very strong"}]),
    DUSCharacter(id="wheat_7", number=7, name="Ear: glaucosity", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}, {"code": 9, "description": "Very strong"}]),
    DUSCharacter(id="wheat_8", number=8, name="Plant: height", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very short"}, {"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Tall"}, {"code": 9, "description": "Very tall"}]),
    DUSCharacter(id="wheat_9", number=9, name="Ear: shape in profile", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Tapering"}, {"code": 2, "description": "Parallel-sided"}, {"code": 3, "description": "Semi-clavate"}, {"code": 4, "description": "Clavate"}, {"code": 5, "description": "Fusiform"}]),
    DUSCharacter(id="wheat_10", number=10, name="Ear: density", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very lax"}, {"code": 3, "description": "Lax"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Dense"}, {"code": 9, "description": "Very dense"}]),
    DUSCharacter(id="wheat_11", number=11, name="Ear: length", type=CharacterType.MG, asterisk=True,
                 states=[{"code": 1, "description": "Very short"}, {"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Long"}, {"code": 9, "description": "Very long"}]),
    DUSCharacter(id="wheat_12", number=12, name="Awns or scurs: presence", type=CharacterType.QL, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Both absent"}, {"code": 2, "description": "Scurs only"}, {"code": 3, "description": "Awns present"}]),
    DUSCharacter(id="wheat_13", number=13, name="Grain: color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Red"}]),
    DUSCharacter(id="wheat_14", number=14, name="Grain: shape", type=CharacterType.VG,
                 states=[{"code": 1, "description": "Elliptical"}, {"code": 2, "description": "Ovate"}, {"code": 3, "description": "Semi-elongated"}, {"code": 4, "description": "Elongated"}]),
    DUSCharacter(id="wheat_15", number=15, name="Seasonal type", type=CharacterType.QL, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Winter type"}, {"code": 2, "description": "Spring type"}]),
]

WHEAT_TEMPLATE = CropTemplate(
    crop_code="wheat",
    crop_name="Wheat",
    scientific_name="Triticum aestivum L.",
    upov_code="TRITI_AES",
    test_guideline="TG/3/12",
    characters=WHEAT_CHARACTERS,
    uniformity_threshold=1.0,
    min_sample_size=100,
    test_years=2,
)


# Maize (Zea mays) - UPOV TG/2/7
MAIZE_CHARACTERS = [
    DUSCharacter(id="maize_1", number=1, name="First leaf: anthocyanin coloration of sheath", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}, {"code": 9, "description": "Very strong"}]),
    DUSCharacter(id="maize_2", number=2, name="Leaf: angle between blade and stem", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Very small"}, {"code": 3, "description": "Small"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Large"}, {"code": 9, "description": "Very large"}]),
    DUSCharacter(id="maize_3", number=3, name="Leaf: attitude of blade", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Straight"}, {"code": 3, "description": "Slightly curved"}, {"code": 5, "description": "Curved"}, {"code": 7, "description": "Strongly curved"}]),
    DUSCharacter(id="maize_4", number=4, name="Leaf: width of blade", type=CharacterType.MG, grouping=True,
                 states=[{"code": 1, "description": "Very narrow"}, {"code": 3, "description": "Narrow"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Broad"}, {"code": 9, "description": "Very broad"}]),
    DUSCharacter(id="maize_5", number=5, name="Tassel: time of anthesis", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very early"}, {"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}, {"code": 9, "description": "Very late"}]),
    DUSCharacter(id="maize_6", number=6, name="Tassel: anthocyanin coloration of base of glume", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}, {"code": 9, "description": "Very strong"}]),
    DUSCharacter(id="maize_7", number=7, name="Tassel: anthocyanin coloration of glumes", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}, {"code": 9, "description": "Very strong"}]),
    DUSCharacter(id="maize_8", number=8, name="Tassel: anthocyanin coloration of anthers", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}, {"code": 9, "description": "Very strong"}]),
    DUSCharacter(id="maize_9", number=9, name="Tassel: angle between main axis and lateral branches", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Very small"}, {"code": 3, "description": "Small"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Large"}, {"code": 9, "description": "Very large"}]),
    DUSCharacter(id="maize_10", number=10, name="Tassel: attitude of lateral branches", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Straight"}, {"code": 3, "description": "Slightly curved"}, {"code": 5, "description": "Curved"}, {"code": 7, "description": "Strongly curved"}]),
    DUSCharacter(id="maize_11", number=11, name="Plant: height", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very short"}, {"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Tall"}, {"code": 9, "description": "Very tall"}]),
    DUSCharacter(id="maize_12", number=12, name="Ear: time of silk emergence", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very early"}, {"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}, {"code": 9, "description": "Very late"}]),
    DUSCharacter(id="maize_13", number=13, name="Ear: anthocyanin coloration of silks", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}, {"code": 9, "description": "Very strong"}]),
    DUSCharacter(id="maize_14", number=14, name="Ear: length", type=CharacterType.MG, asterisk=True,
                 states=[{"code": 1, "description": "Very short"}, {"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Long"}, {"code": 9, "description": "Very long"}]),
    DUSCharacter(id="maize_15", number=15, name="Ear: shape", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Conical"}, {"code": 2, "description": "Conico-cylindrical"}, {"code": 3, "description": "Cylindrical"}]),
    DUSCharacter(id="maize_16", number=16, name="Ear: number of rows of grain", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Very few"}, {"code": 3, "description": "Few"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Many"}, {"code": 9, "description": "Very many"}]),
    DUSCharacter(id="maize_17", number=17, name="Grain: type", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Flint"}, {"code": 2, "description": "Flint-like"}, {"code": 3, "description": "Intermediate"}, {"code": 4, "description": "Dent-like"}, {"code": 5, "description": "Dent"}, {"code": 6, "description": "Sweet"}, {"code": 7, "description": "Pop"}]),
    DUSCharacter(id="maize_18", number=18, name="Grain: color of top of grain", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Whitish yellow"}, {"code": 3, "description": "Yellow"}, {"code": 4, "description": "Orange"}, {"code": 5, "description": "Red"}, {"code": 6, "description": "Purple"}]),
]

MAIZE_TEMPLATE = CropTemplate(
    crop_code="maize",
    crop_name="Maize",
    scientific_name="Zea mays L.",
    upov_code="ZEA_MAY",
    test_guideline="TG/2/7",
    characters=MAIZE_CHARACTERS,
    uniformity_threshold=1.0,
    min_sample_size=100,
    test_years=2,
)

# All crop templates (base crops)
CROP_TEMPLATES: Dict[str, CropTemplate] = {
    "rice": RICE_TEMPLATE,
    "wheat": WHEAT_TEMPLATE,
    "maize": MAIZE_TEMPLATE,
}

# Import and add additional crop templates
try:
    from app.services.dus_crops import ADDITIONAL_CROP_TEMPLATES
    CROP_TEMPLATES.update(ADDITIONAL_CROP_TEMPLATES)
except ImportError:
    pass  # Additional crops not available



# ============ DUS Testing Service ============

class DUSTestingService:
    """Service for DUS (Distinctness, Uniformity, Stability) testing"""
    
    def __init__(self):
        self.trials: Dict[str, DUSTrial] = {}
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize demo trial data"""
        demo_trial = DUSTrial(
            id="DUS-2024-001",
            crop_code="rice",
            trial_name="Rice DUS Trial 2024 - Kharif",
            year=2024,
            location="IARI, New Delhi",
            status=TrialStatus.YEAR_1,
            sample_size=100,
            entries=[
                TrialEntry(entry_id="E1", variety_name="BIJ-R-001", is_candidate=True, breeder="Bijmantra"),
                TrialEntry(entry_id="E2", variety_name="IR64", is_reference=True, origin="IRRI"),
                TrialEntry(entry_id="E3", variety_name="Pusa Basmati 1", is_reference=True, origin="IARI"),
                TrialEntry(entry_id="E4", variety_name="Swarna", is_reference=True, origin="CRRI"),
            ],
        )
        self.trials[demo_trial.id] = demo_trial
    
    # ============ Crop Templates ============
    
    def get_crop_templates(self) -> List[Dict[str, Any]]:
        """Get list of available crop templates"""
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
        """Get crop template by code"""
        return CROP_TEMPLATES.get(crop_code.lower())
    
    def get_crop_characters(self, crop_code: str) -> List[Dict[str, Any]]:
        """Get characters for a crop"""
        template = self.get_crop_template(crop_code)
        if not template:
            return []
        return [c.model_dump() for c in template.characters]
    
    def get_grouping_characters(self, crop_code: str) -> List[Dict[str, Any]]:
        """Get grouping characters for initial screening"""
        template = self.get_crop_template(crop_code)
        if not template:
            return []
        return [c.model_dump() for c in template.characters if c.grouping]
    
    def get_asterisk_characters(self, crop_code: str) -> List[Dict[str, Any]]:
        """Get asterisk (important) characters for distinctness"""
        template = self.get_crop_template(crop_code)
        if not template:
            return []
        return [c.model_dump() for c in template.characters if c.asterisk]
    
    # ============ Trial Management ============
    
    def create_trial(
        self,
        crop_code: str,
        trial_name: str,
        year: int,
        location: str,
        sample_size: int = 100,
        notes: Optional[str] = None,
    ) -> DUSTrial:
        """Create a new DUS trial"""
        trial_id = f"DUS-{year}-{str(len(self.trials) + 1).zfill(3)}"
        trial = DUSTrial(
            id=trial_id,
            crop_code=crop_code,
            trial_name=trial_name,
            year=year,
            location=location,
            sample_size=sample_size,
            notes=notes,
        )
        self.trials[trial_id] = trial
        return trial
    
    def get_trial(self, trial_id: str) -> Optional[DUSTrial]:
        """Get trial by ID"""
        return self.trials.get(trial_id)
    
    def list_trials(
        self,
        crop_code: Optional[str] = None,
        year: Optional[int] = None,
        status: Optional[TrialStatus] = None,
    ) -> List[DUSTrial]:
        """List trials with optional filters"""
        trials = list(self.trials.values())
        if crop_code:
            trials = [t for t in trials if t.crop_code == crop_code]
        if year:
            trials = [t for t in trials if t.year == year]
        if status:
            trials = [t for t in trials if t.status == status]
        return trials
    
    def add_entry(
        self,
        trial_id: str,
        variety_name: str,
        is_candidate: bool = False,
        is_reference: bool = False,
        breeder: Optional[str] = None,
        origin: Optional[str] = None,
    ) -> Optional[TrialEntry]:
        """Add entry to trial"""
        trial = self.get_trial(trial_id)
        if not trial:
            return None
        
        entry_id = f"E{len(trial.entries) + 1}"
        entry = TrialEntry(
            entry_id=entry_id,
            variety_name=variety_name,
            is_candidate=is_candidate,
            is_reference=is_reference,
            breeder=breeder,
            origin=origin,
        )
        trial.entries.append(entry)
        return entry
    
    def record_score(
        self,
        trial_id: str,
        entry_id: str,
        character_id: str,
        value: Any,
        notes: Optional[str] = None,
        scored_by: Optional[str] = None,
    ) -> bool:
        """Record character score for an entry"""
        trial = self.get_trial(trial_id)
        if not trial:
            return False
        
        entry = next((e for e in trial.entries if e.entry_id == entry_id), None)
        if not entry:
            return False
        
        # Update or add score
        existing = next((s for s in entry.scores if s.character_id == character_id), None)
        if existing:
            existing.value = value
            existing.notes = notes
            existing.scored_by = scored_by
            existing.scored_at = datetime.now(UTC)
        else:
            entry.scores.append(CharacterScore(
                character_id=character_id,
                value=value,
                notes=notes,
                scored_by=scored_by,
            ))
        return True
    
    def bulk_record_scores(
        self,
        trial_id: str,
        entry_id: str,
        scores: List[Dict[str, Any]],
        scored_by: Optional[str] = None,
    ) -> int:
        """Record multiple scores at once"""
        count = 0
        for score in scores:
            if self.record_score(
                trial_id=trial_id,
                entry_id=entry_id,
                character_id=score["character_id"],
                value=score["value"],
                notes=score.get("notes"),
                scored_by=scored_by,
            ):
                count += 1
        return count

    
    # ============ DUS Analysis ============
    
    def analyze_distinctness(self, trial_id: str, candidate_entry_id: str) -> Dict[str, Any]:
        """
        Analyze distinctness of candidate variety against reference varieties.
        A variety is distinct if it differs in at least one character.
        """
        trial = self.get_trial(trial_id)
        if not trial:
            return {"error": "Trial not found"}
        
        candidate = next((e for e in trial.entries if e.entry_id == candidate_entry_id), None)
        if not candidate:
            return {"error": "Candidate entry not found"}
        
        references = [e for e in trial.entries if e.is_reference]
        if not references:
            return {"error": "No reference varieties in trial"}
        
        template = self.get_crop_template(trial.crop_code)
        if not template:
            return {"error": "Crop template not found"}
        
        # Get candidate scores as dict
        candidate_scores = {s.character_id: s.value for s in candidate.scores}
        
        comparisons = []
        for ref in references:
            ref_scores = {s.character_id: s.value for s in ref.scores}
            
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
                "reference_variety": ref.variety_name,
                "reference_entry_id": ref.entry_id,
                "is_distinct": is_distinct,
                "difference_count": len(differences),
                "differences": differences,
            })
        
        # Overall distinctness: must be distinct from ALL reference varieties
        all_distinct = all(c["is_distinct"] for c in comparisons)
        
        return {
            "trial_id": trial_id,
            "candidate_variety": candidate.variety_name,
            "candidate_entry_id": candidate_entry_id,
            "result": DUSResult.PASS if all_distinct else DUSResult.FAIL,
            "is_distinct": all_distinct,
            "comparisons": comparisons,
            "summary": f"Distinct from {sum(1 for c in comparisons if c['is_distinct'])}/{len(comparisons)} reference varieties",
        }
    
    def calculate_uniformity(
        self,
        trial_id: str,
        entry_id: str,
        off_type_count: int,
        sample_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculate uniformity based on off-type count.
        Uses UPOV standard for self-pollinated crops.
        """
        trial = self.get_trial(trial_id)
        if not trial:
            return {"error": "Trial not found"}
        
        template = self.get_crop_template(trial.crop_code)
        if not template:
            return {"error": "Crop template not found"}
        
        sample = sample_size or trial.sample_size
        threshold = template.uniformity_threshold / 100  # Convert percentage
        
        # Calculate maximum allowed off-types (binomial distribution)
        # Using simplified UPOV table approach
        max_off_types = self._get_max_off_types(sample, threshold)
        
        off_type_percentage = (off_type_count / sample) * 100
        is_uniform = off_type_count <= max_off_types
        
        return {
            "trial_id": trial_id,
            "entry_id": entry_id,
            "sample_size": sample,
            "off_type_count": off_type_count,
            "off_type_percentage": round(off_type_percentage, 2),
            "threshold_percentage": template.uniformity_threshold,
            "max_allowed_off_types": max_off_types,
            "result": DUSResult.PASS if is_uniform else DUSResult.FAIL,
            "is_uniform": is_uniform,
        }
    
    def _get_max_off_types(self, sample_size: int, threshold: float) -> int:
        """Get maximum allowed off-types based on sample size and threshold"""
        # UPOV standard table for 1% threshold (probability 0.95)
        upov_table = {
            20: 1, 50: 2, 100: 3, 200: 5, 300: 7, 500: 9, 1000: 15,
        }
        
        # Find closest sample size
        sizes = sorted(upov_table.keys())
        for size in sizes:
            if sample_size <= size:
                base = upov_table[size]
                # Adjust for different thresholds
                if threshold > 0.01:
                    return int(base * (threshold / 0.01))
                return base
        
        # For larger samples, use approximation
        return int(sample_size * threshold * 1.5)
    
    def assess_stability(
        self,
        trial_id: str,
        entry_id: str,
        year1_scores: Dict[str, Any],
        year2_scores: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Assess stability by comparing scores across two years.
        Characters should remain consistent.
        """
        trial = self.get_trial(trial_id)
        if not trial:
            return {"error": "Trial not found"}
        
        template = self.get_crop_template(trial.crop_code)
        if not template:
            return {"error": "Crop template not found"}
        
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
        
        # Stability: no changes in asterisk characters, minimal changes in others
        asterisk_changes = [c for c in changes if c["is_asterisk"]]
        is_stable = len(asterisk_changes) == 0
        
        return {
            "trial_id": trial_id,
            "entry_id": entry_id,
            "result": DUSResult.PASS if is_stable else DUSResult.FAIL,
            "is_stable": is_stable,
            "total_changes": len(changes),
            "asterisk_changes": len(asterisk_changes),
            "changes": changes,
            "summary": f"{len(changes)} character(s) changed, {len(asterisk_changes)} asterisk character(s)",
        }
    
    def generate_dus_report(self, trial_id: str, candidate_entry_id: str) -> Dict[str, Any]:
        """Generate comprehensive DUS report for a candidate variety"""
        trial = self.get_trial(trial_id)
        if not trial:
            return {"error": "Trial not found"}
        
        candidate = next((e for e in trial.entries if e.entry_id == candidate_entry_id), None)
        if not candidate:
            return {"error": "Candidate entry not found"}
        
        template = self.get_crop_template(trial.crop_code)
        if not template:
            return {"error": "Crop template not found"}
        
        # Get distinctness analysis
        distinctness = self.analyze_distinctness(trial_id, candidate_entry_id)
        
        # Build character table
        candidate_scores = {s.character_id: s for s in candidate.scores}
        character_table = []
        for char in template.characters:
            score = candidate_scores.get(char.id)
            state_desc = None
            if score:
                state = next((s for s in char.states if s["code"] == score.value), None)
                state_desc = state["description"] if state else str(score.value)
            
            character_table.append({
                "number": char.number,
                "name": char.name,
                "type": char.type.value,
                "grouping": char.grouping,
                "asterisk": char.asterisk,
                "value": score.value if score else None,
                "state_description": state_desc,
            })
        
        return {
            "report_type": "DUS Testing Report",
            "generated_at": datetime.now(UTC).isoformat(),
            "trial": {
                "id": trial.id,
                "name": trial.trial_name,
                "crop": template.crop_name,
                "scientific_name": template.scientific_name,
                "year": trial.year,
                "location": trial.location,
                "status": trial.status.value,
                "test_guideline": template.test_guideline,
            },
            "candidate": {
                "entry_id": candidate.entry_id,
                "variety_name": candidate.variety_name,
                "breeder": candidate.breeder,
            },
            "reference_varieties": [
                {"entry_id": e.entry_id, "variety_name": e.variety_name, "origin": e.origin}
                for e in trial.entries if e.is_reference
            ],
            "character_observations": character_table,
            "distinctness": distinctness,
            "uniformity": {"status": "pending", "note": "Requires off-type count data"},
            "stability": {"status": "pending", "note": "Requires Year 2 data"},
            "overall_result": distinctness.get("result", DUSResult.PENDING),
        }


# Singleton instance
dus_service = DUSTestingService()

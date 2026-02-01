"""
DUS Testing API (Distinctness, Uniformity, Stability)

UPOV-compliant variety testing endpoints for Plant Variety Protection.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dus_testing import (
    dus_service, TrialStatus, DUSResult,
)
from app.api.deps import get_db, get_current_user
from app.models.core import User

router = APIRouter(prefix="/dus", tags=["DUS Testing"])


# ============ Request/Response Schemas ============

class CreateTrialRequest(BaseModel):
    crop_code: str = Field(..., description="Crop code (rice, wheat, maize)")
    trial_name: str = Field(..., description="Trial name")
    year: int = Field(..., description="Trial year")
    location: str = Field(..., description="Trial location")
    sample_size: int = Field(100, description="Sample size per entry")
    notes: Optional[str] = None


class AddEntryRequest(BaseModel):
    variety_name: str = Field(..., description="Variety name")
    is_candidate: bool = Field(False, description="Is this a candidate variety?")
    is_reference: bool = Field(False, description="Is this a reference variety?")
    breeder: Optional[str] = None
    origin: Optional[str] = None


class RecordScoreRequest(BaseModel):
    character_id: str = Field(..., description="Character ID")
    value: Any = Field(..., description="Score value (state code or measurement)")
    notes: Optional[str] = None


class BulkScoreRequest(BaseModel):
    scores: List[Dict[str, Any]] = Field(..., description="List of scores")


class UniformityRequest(BaseModel):
    off_type_count: int = Field(..., ge=0, description="Number of off-type plants")
    sample_size: Optional[int] = Field(None, description="Sample size (uses trial default if not provided)")


class StabilityRequest(BaseModel):
    year1_scores: Dict[str, Any] = Field(..., description="Year 1 character scores")
    year2_scores: Dict[str, Any] = Field(..., description="Year 2 character scores")


# ============ Crop Templates ============

@router.get("/crops")
async def list_crop_templates():
    """
    List available crop templates with DUS characters.
    
    Each crop has UPOV-defined characters for DUS testing.
    """
    return {
        "crops": dus_service.get_crop_templates(),
        "total": len(dus_service.get_crop_templates()),
    }


@router.get("/crops/{crop_code}")
async def get_crop_template(crop_code: str):
    """Get detailed crop template including all characters"""
    template = dus_service.get_crop_template(crop_code)
    if not template:
        raise HTTPException(status_code=404, detail=f"Crop template not found: {crop_code}")
    return template.model_dump()


@router.get("/crops/{crop_code}/characters")
async def get_crop_characters(
    crop_code: str,
    grouping_only: bool = Query(False, description="Return only grouping characters"),
    asterisk_only: bool = Query(False, description="Return only asterisk (important) characters"),
):
    """
    Get DUS characters for a crop.
    
    - **Grouping characters**: Used for initial screening
    - **Asterisk characters**: Important for distinctness (marked with * in UPOV guidelines)
    """
    if grouping_only:
        chars = dus_service.get_grouping_characters(crop_code)
    elif asterisk_only:
        chars = dus_service.get_asterisk_characters(crop_code)
    else:
        chars = dus_service.get_crop_characters(crop_code)
    
    if not chars:
        raise HTTPException(status_code=404, detail=f"Crop template not found: {crop_code}")
    
    return {
        "crop_code": crop_code,
        "characters": chars,
        "total": len(chars),
    }



# ============ Trial Management ============

@router.post("/trials")
async def create_trial(
    request: CreateTrialRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new DUS trial.
    
    A DUS trial typically runs for 2 years with candidate and reference varieties.
    """
    # Validate crop code
    template = dus_service.get_crop_template(request.crop_code)
    if not template:
        raise HTTPException(status_code=400, detail=f"Invalid crop code: {request.crop_code}")
    
    trial = await dus_service.create_trial(
        db=db,
        organization_id=current_user.organization_id,
        crop_code=request.crop_code,
        trial_name=request.trial_name,
        year=request.year,
        location=request.location,
        sample_size=request.sample_size,
        notes=request.notes,
    )
    
    return {
        "message": "Trial created successfully",
        "trial": trial,
    }


@router.get("/trials")
async def list_trials(
    crop_code: Optional[str] = Query(None, description="Filter by crop"),
    year: Optional[int] = Query(None, description="Filter by year"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List DUS trials with optional filters"""
    status_enum = TrialStatus(status) if status else None
    trials = await dus_service.list_trials(
        db=db,
        organization_id=current_user.organization_id,
        crop_code=crop_code, 
        year=year, 
        status=status_enum
    )
    
    return {
        "trials": trials,
        "total": len(trials),
    }


@router.get("/trials/{trial_id}")
async def get_trial(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trial details including entries and scores"""
    try:
        t_id = int(trial_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trial ID format")

    trial = await dus_service.get_trial(db=db, organization_id=current_user.organization_id, trial_id=t_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return trial


@router.post("/trials/{trial_id}/entries")
async def add_trial_entry(
    trial_id: str, 
    request: AddEntryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a variety entry to a trial.
    
    Mark as `is_candidate=true` for the variety being tested,
    or `is_reference=true` for comparison varieties.
    """
    try:
        t_id = int(trial_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trial ID format")

    entry = await dus_service.add_entry(
        db=db,
        organization_id=current_user.organization_id,
        trial_id=t_id,
        variety_name=request.variety_name,
        is_candidate=request.is_candidate,
        is_reference=request.is_reference,
        breeder=request.breeder,
        origin=request.origin,
    )
    
    if not entry:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    return {
        "message": "Entry added successfully",
        "entry": entry,
    }


@router.get("/trials/{trial_id}/entries")
async def list_trial_entries(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all entries in a trial"""
    try:
        t_id = int(trial_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trial ID format")

    trial = await dus_service.get_trial(db=db, organization_id=current_user.organization_id, trial_id=t_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    entries = await dus_service.get_entries(db=db, organization_id=current_user.organization_id, trial_id=t_id)

    return {
        "trial_id": trial_id,
        "entries": entries,
        "candidate_count": sum(1 for e in entries if e["is_candidate"]),
        "reference_count": sum(1 for e in entries if e["is_reference"]),
    }


# ============ Character Scoring ============

@router.post("/trials/{trial_id}/entries/{entry_id}/scores")
async def record_character_score(
    trial_id: str,
    entry_id: str,
    request: RecordScoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a character score for an entry"""
    try:
        t_id = int(trial_id)
        e_id = int(entry_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    success = await dus_service.record_score(
        db=db,
        organization_id=current_user.organization_id,
        trial_id=t_id,
        entry_id=e_id,
        character_id=request.character_id,
        value=request.value,
        notes=request.notes,
        scored_by=current_user.full_name or current_user.email
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Trial or entry not found")
    
    return {"message": "Score recorded successfully"}


@router.post("/trials/{trial_id}/entries/{entry_id}/scores/bulk")
async def bulk_record_scores(
    trial_id: str,
    entry_id: str,
    request: BulkScoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record multiple character scores at once"""
    try:
        t_id = int(trial_id)
        e_id = int(entry_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    count = await dus_service.bulk_record_scores(
        db=db,
        organization_id=current_user.organization_id,
        trial_id=t_id,
        entry_id=e_id,
        scores=request.scores,
        scored_by=current_user.full_name or current_user.email
    )
    
    if count == 0:
        raise HTTPException(status_code=404, detail="Trial or entry not found")
    
    return {
        "message": f"Recorded {count} scores successfully",
        "recorded_count": count,
    }


@router.get("/trials/{trial_id}/entries/{entry_id}/scores")
async def get_entry_scores(
    trial_id: str, 
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all scores for an entry"""
    try:
        t_id = int(trial_id)
        e_id = int(entry_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    trial = await dus_service.get_trial(db=db, organization_id=current_user.organization_id, trial_id=t_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    entries = await dus_service.get_entries(db=db, organization_id=current_user.organization_id, trial_id=t_id)
    entry = next((e for e in entries if e["entry_id"] == e_id), None)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    return {
        "trial_id": trial_id,
        "entry_id": entry_id,
        "variety_name": entry["variety_name"],
        "scores": entry["scores"],
        "score_count": len(entry["scores"]),
    }


# ============ DUS Analysis ============

@router.get("/trials/{trial_id}/distinctness/{entry_id}")
async def analyze_distinctness(
    trial_id: str, 
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze distinctness of a candidate variety.
    
    Compares the candidate against all reference varieties.
    A variety is distinct if it differs in at least one character from each reference.
    """
    try:
        t_id = int(trial_id)
        e_id = int(entry_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    result = await dus_service.analyze_distinctness(
        db=db,
        organization_id=current_user.organization_id,
        trial_id=t_id,
        candidate_entry_id=e_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/trials/{trial_id}/uniformity/{entry_id}")
async def calculate_uniformity(
    trial_id: str,
    entry_id: str,
    request: UniformityRequest,
):
    """
    Calculate uniformity based on off-type count.
    
    Uses UPOV standard for self-pollinated crops.
    The variety passes if off-types are below the threshold.
    """
    # Service method is synchronous and math-only, so we don't need DB here
    result = dus_service.calculate_uniformity(
        off_type_count=request.off_type_count,
        sample_size=request.sample_size or 100, # Default if not provided
        threshold_percentage=1.0 # Default
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # Enrich result with IDs
    result["trial_id"] = trial_id
    result["entry_id"] = entry_id
    
    return result


@router.post("/trials/{trial_id}/stability/{entry_id}")
async def assess_stability(
    trial_id: str,
    entry_id: str,
    request: StabilityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assess stability by comparing Year 1 and Year 2 scores.
    
    Characters should remain consistent across years.
    Asterisk characters must not change.
    """
    try:
        t_id = int(trial_id)
        e_id = int(entry_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    result = await dus_service.assess_stability(
        db=db,
        organization_id=current_user.organization_id,
        trial_id=t_id,
        entry_id=e_id,
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


# @router.get("/trials/{trial_id}/report/{entry_id}")
# async def generate_dus_report(trial_id: str, entry_id: str):
#     """
#     Generate comprehensive DUS report for a candidate variety.
#     
#     Includes character observations, distinctness analysis,
#     and overall DUS result.
#     """
#     report = dus_service.generate_dus_report(trial_id, entry_id)
#     
#     if "error" in report:
#         raise HTTPException(status_code=404, detail=report["error"])
#     
#     return report


# ============ Reference Data ============

@router.get("/reference/trial-statuses")
async def get_trial_statuses():
    """Get available trial status values"""
    return {
        "statuses": [
            {"value": s.value, "description": s.name.replace("_", " ").title()}
            for s in TrialStatus
        ]
    }


@router.get("/reference/character-types")
async def get_character_types():
    """Get DUS character type codes"""
    return {
        "types": [
            {"code": "VG", "description": "Visual assessment - Grouping character"},
            {"code": "MG", "description": "Measurement - Grouping character"},
            {"code": "VS", "description": "Visual assessment - Single observation"},
            {"code": "MS", "description": "Measurement - Single observation"},
            {"code": "PQ", "description": "Pseudo-qualitative"},
            {"code": "QN", "description": "Quantitative"},
            {"code": "QL", "description": "Qualitative"},
        ]
    }

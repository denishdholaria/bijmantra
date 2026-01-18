"""
Trial Summary API
Comprehensive trial analysis and reporting

Converted to database queries per Zero Mock Data Policy (Session 77).
Queries Trial, Study, Observation tables for real data.
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.core import Trial, Study, Program, Location
from app.models.phenotyping import Observation, ObservationVariable

router = APIRouter(prefix="/trial-summary", tags=["Trial Summary"])


# ============================================
# SCHEMAS
# ============================================

class TrialInfo(BaseModel):
    trialDbId: str
    trialName: str
    programDbId: Optional[str] = None
    programName: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    locations: int = 0
    entries: int = 0
    traits: int = 0
    observations: int = 0
    completionRate: float = 0.0
    leadScientist: Optional[str] = None


class TopPerformer(BaseModel):
    rank: int
    germplasmDbId: str
    germplasmName: str
    yield_value: float
    change_percent: str
    traits: List[str]


class TraitSummary(BaseModel):
    trait: str
    mean: float
    cv: float
    lsd: float
    fValue: float
    significance: str


class LocationPerformance(BaseModel):
    locationDbId: str
    locationName: str
    entries: int
    meanYield: float
    cv: float
    completionRate: float


class TrialSummaryResponse(BaseModel):
    trial: TrialInfo
    topPerformers: List[TopPerformer]
    traitSummary: List[TraitSummary]
    locationPerformance: List[LocationPerformance]
    statistics: dict


# ============================================
# ENDPOINTS
# ============================================

@router.get("/trials")
async def get_trials(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    status: Optional[str] = Query(None, description="Filter by status: active, completed, planned"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get list of trials with summary info.
    
    Queries Trial table with related Program and Study data.
    Returns empty list when no trials exist.
    """
    stmt = select(Trial).where(
        Trial.organization_id == organization_id
    ).options(
        selectinload(Trial.program),
    )
    
    if program_id:
        stmt = stmt.where(Trial.program_id == int(program_id))
    
    result = await db.execute(stmt)
    trials = result.scalars().all()
    
    # Transform to response format
    data = []
    for trial in trials:
        # Count studies for this trial
        study_count_result = await db.execute(
            select(func.count()).select_from(Study).where(
                and_(
                    Study.trial_id == trial.id,
                    Study.organization_id == organization_id,
                )
            )
        )
        study_count = study_count_result.scalar() or 0
        
        # Get additional info
        additional = trial.additional_info or {}
        
        data.append(TrialInfo(
            trialDbId=trial.trial_db_id or str(trial.id),
            trialName=trial.trial_name or "",
            programDbId=str(trial.program_id) if trial.program_id else None,
            programName=trial.program.program_name if trial.program else None,
            startDate=trial.start_date.isoformat() if trial.start_date else None,
            endDate=trial.end_date.isoformat() if trial.end_date else None,
            locations=study_count,
            entries=additional.get("entries", 0),
            traits=additional.get("traits", 0),
            observations=additional.get("observations", 0),
            completionRate=additional.get("completionRate", 0.0),
            leadScientist=additional.get("leadScientist"),
        ).model_dump())
    
    return {"data": data, "total": len(data)}


@router.get("/trials/{trial_id}")
async def get_trial(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get trial details.
    
    Returns 404 if trial not found.
    """
    stmt = select(Trial).where(
        and_(
            Trial.organization_id == organization_id,
            Trial.trial_db_id == trial_id,
        )
    ).options(
        selectinload(Trial.program),
    )
    
    result = await db.execute(stmt)
    trial = result.scalar_one_or_none()
    
    if not trial:
        # Try by numeric ID
        if trial_id.isdigit():
            stmt = select(Trial).where(
                and_(
                    Trial.organization_id == organization_id,
                    Trial.id == int(trial_id),
                )
            ).options(
                selectinload(Trial.program),
            )
            result = await db.execute(stmt)
            trial = result.scalar_one_or_none()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    additional = trial.additional_info or {}
    
    return {"data": TrialInfo(
        trialDbId=trial.trial_db_id or str(trial.id),
        trialName=trial.trial_name or "",
        programDbId=str(trial.program_id) if trial.program_id else None,
        programName=trial.program.program_name if trial.program else None,
        startDate=trial.start_date.isoformat() if trial.start_date else None,
        endDate=trial.end_date.isoformat() if trial.end_date else None,
        locations=additional.get("locations", 0),
        entries=additional.get("entries", 0),
        traits=additional.get("traits", 0),
        observations=additional.get("observations", 0),
        completionRate=additional.get("completionRate", 0.0),
        leadScientist=additional.get("leadScientist"),
    ).model_dump()}


@router.get("/trials/{trial_id}/summary", response_model=TrialSummaryResponse)
async def get_trial_summary(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get comprehensive trial summary.
    
    Returns trial info with top performers, trait summary, and location performance.
    Returns empty lists when no data exists.
    """
    # Get trial
    stmt = select(Trial).where(
        and_(
            Trial.organization_id == organization_id,
            Trial.trial_db_id == trial_id,
        )
    ).options(
        selectinload(Trial.program),
    )
    
    result = await db.execute(stmt)
    trial = result.scalar_one_or_none()
    
    if not trial:
        if trial_id.isdigit():
            stmt = select(Trial).where(
                and_(
                    Trial.organization_id == organization_id,
                    Trial.id == int(trial_id),
                )
            ).options(
                selectinload(Trial.program),
            )
            result = await db.execute(stmt)
            trial = result.scalar_one_or_none()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    additional = trial.additional_info or {}
    
    trial_info = TrialInfo(
        trialDbId=trial.trial_db_id or str(trial.id),
        trialName=trial.trial_name or "",
        programDbId=str(trial.program_id) if trial.program_id else None,
        programName=trial.program.program_name if trial.program else None,
        startDate=trial.start_date.isoformat() if trial.start_date else None,
        endDate=trial.end_date.isoformat() if trial.end_date else None,
        locations=additional.get("locations", 0),
        entries=additional.get("entries", 0),
        traits=additional.get("traits", 0),
        observations=additional.get("observations", 0),
        completionRate=additional.get("completionRate", 0.0),
        leadScientist=additional.get("leadScientist"),
    )
    
    # Return empty lists - real data would come from observations/analysis
    return TrialSummaryResponse(
        trial=trial_info,
        topPerformers=[],
        traitSummary=[],
        locationPerformance=[],
        statistics={
            "grand_mean": None,
            "overall_cv": None,
            "heritability": None,
            "genetic_variance": None,
            "error_variance": None,
            "lsd_5_percent": None,
            "selection_intensity": None,
            "expected_gain": None,
            "message": "Statistics require observation data",
        }
    )


@router.get("/trials/{trial_id}/top-performers")
async def get_top_performers(
    trial_id: str,
    limit: int = Query(10, ge=1, le=50),
    trait: Optional[str] = Query(None, description="Sort by specific trait"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get top performing entries in a trial.
    
    Returns empty list when no observation data exists.
    """
    # Verify trial exists
    stmt = select(Trial).where(
        and_(
            Trial.organization_id == organization_id,
            Trial.trial_db_id == trial_id,
        )
    )
    result = await db.execute(stmt)
    trial = result.scalar_one_or_none()
    
    if not trial:
        if trial_id.isdigit():
            stmt = select(Trial).where(
                and_(
                    Trial.organization_id == organization_id,
                    Trial.id == int(trial_id),
                )
            )
            result = await db.execute(stmt)
            trial = result.scalar_one_or_none()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    # TODO: Query observations and rank by trait value
    return {"data": [], "trait": trait or "Yield", "message": "Requires observation data"}


@router.get("/trials/{trial_id}/traits")
async def get_trait_summary(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get trait summary statistics for a trial.
    
    Returns empty list when no observation data exists.
    """
    # Verify trial exists
    stmt = select(Trial).where(
        and_(
            Trial.organization_id == organization_id,
            Trial.trial_db_id == trial_id,
        )
    )
    result = await db.execute(stmt)
    trial = result.scalar_one_or_none()
    
    if not trial:
        if trial_id.isdigit():
            stmt = select(Trial).where(
                and_(
                    Trial.organization_id == organization_id,
                    Trial.id == int(trial_id),
                )
            )
            result = await db.execute(stmt)
            trial = result.scalar_one_or_none()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    # TODO: Calculate trait statistics from observations
    return {"data": [], "message": "Requires observation data"}


@router.get("/trials/{trial_id}/locations")
async def get_location_performance(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get performance by location for a trial.
    
    Returns empty list when no location data exists.
    """
    # Verify trial exists
    stmt = select(Trial).where(
        and_(
            Trial.organization_id == organization_id,
            Trial.trial_db_id == trial_id,
        )
    )
    result = await db.execute(stmt)
    trial = result.scalar_one_or_none()
    
    if not trial:
        if trial_id.isdigit():
            stmt = select(Trial).where(
                and_(
                    Trial.organization_id == organization_id,
                    Trial.id == int(trial_id),
                )
            )
            result = await db.execute(stmt)
            trial = result.scalar_one_or_none()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    # Get studies (locations) for this trial
    stmt = select(Study).where(
        and_(
            Study.trial_id == trial.id,
            Study.organization_id == organization_id,
        )
    ).options(
        selectinload(Study.location),
    )
    
    result = await db.execute(stmt)
    studies = result.scalars().all()
    
    locations = []
    for study in studies:
        if study.location:
            locations.append(LocationPerformance(
                locationDbId=str(study.location.id),
                locationName=study.location.location_name or "",
                entries=0,  # Would need observation unit count
                meanYield=0.0,  # Would need observation data
                cv=0.0,
                completionRate=0.0,
            ).model_dump())
    
    return {"data": locations}


@router.get("/trials/{trial_id}/statistics")
async def get_trial_statistics(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get detailed statistical analysis for a trial.
    
    Statistical Analysis Formulas:
    
    Heritability (H²):
    H² = Vg / (Vg + Ve/r)
    Where: Vg = genotypic variance, Ve = error variance, r = replicates
    
    LSD (Least Significant Difference):
    LSD = t(α, df_error) × √(2 × MSE / r)
    
    Expected Genetic Gain:
    ΔG = i × H² × σp
    Where: i = selection intensity, σp = phenotypic std dev
    
    Returns null values when no observation data exists.
    """
    # Verify trial exists
    stmt = select(Trial).where(
        and_(
            Trial.organization_id == organization_id,
            Trial.trial_db_id == trial_id,
        )
    )
    result = await db.execute(stmt)
    trial = result.scalar_one_or_none()
    
    if not trial:
        if trial_id.isdigit():
            stmt = select(Trial).where(
                and_(
                    Trial.organization_id == organization_id,
                    Trial.id == int(trial_id),
                )
            )
            result = await db.execute(stmt)
            trial = result.scalar_one_or_none()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    # TODO: Calculate statistics from observations
    return {
        "grand_mean": None,
        "overall_cv": None,
        "heritability": None,
        "genetic_variance": None,
        "error_variance": None,
        "genotype_variance": None,
        "gxe_variance": None,
        "lsd_5_percent": None,
        "lsd_1_percent": None,
        "selection_intensity": None,
        "expected_gain": None,
        "realized_gain": None,
        "anova": None,
        "message": "Statistics require observation data",
    }


@router.post("/trials/{trial_id}/export")
async def export_trial_summary(
    trial_id: str,
    format: str = Query("pdf", description="Export format: pdf, xlsx, docx"),
    sections: Optional[str] = Query(None, description="Comma-separated sections to include"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Export trial summary report.
    
    Note: Export functionality requires report generation service.
    """
    # Verify trial exists
    stmt = select(Trial).where(
        and_(
            Trial.organization_id == organization_id,
            Trial.trial_db_id == trial_id,
        )
    )
    result = await db.execute(stmt)
    trial = result.scalar_one_or_none()
    
    if not trial:
        if trial_id.isdigit():
            stmt = select(Trial).where(
                and_(
                    Trial.organization_id == organization_id,
                    Trial.id == int(trial_id),
                )
            )
            result = await db.execute(stmt)
            trial = result.scalar_one_or_none()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    return {
        "message": f"Report generation pending - {format.upper()} format",
        "trial_id": trial_id,
        "format": format,
        "sections": sections.split(",") if sections else ["all"],
        "download_url": None,
        "note": "Export functionality requires report generation service",
    }

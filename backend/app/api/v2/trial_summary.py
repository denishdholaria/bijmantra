"""
Trial Summary API
Comprehensive trial analysis and reporting
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/trial-summary", tags=["Trial Summary"])


# ============================================
# SCHEMAS
# ============================================

class TrialInfo(BaseModel):
    trialDbId: str
    trialName: str
    programDbId: str
    programName: str
    startDate: str
    endDate: str
    locations: int
    entries: int
    traits: int
    observations: int
    completionRate: float
    leadScientist: str


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
# DEMO DATA
# ============================================

DEMO_TRIALS = [
    TrialInfo(
        trialDbId="trial-1",
        trialName="Yield Trial Spring 2025",
        programDbId="prog-001",
        programName="Rice Improvement Program",
        startDate="2025-01-15",
        endDate="2025-06-30",
        locations=4,
        entries=256,
        traits=12,
        observations=12288,
        completionRate=87,
        leadScientist="Dr. Sarah Johnson"
    ),
    TrialInfo(
        trialDbId="trial-2",
        trialName="Disease Screening 2025",
        programDbId="prog-002",
        programName="Wheat Breeding Program",
        startDate="2025-02-01",
        endDate="2025-07-15",
        locations=3,
        entries=180,
        traits=8,
        observations=4320,
        completionRate=72,
        leadScientist="Dr. Michael Chen"
    ),
    TrialInfo(
        trialDbId="trial-3",
        trialName="Multi-location Trial 2024",
        programDbId="prog-001",
        programName="Rice Improvement Program",
        startDate="2024-06-01",
        endDate="2024-12-15",
        locations=8,
        entries=320,
        traits=15,
        observations=38400,
        completionRate=100,
        leadScientist="Dr. Priya Patel"
    ),
]


def generate_top_performers(trial_id: str) -> List[TopPerformer]:
    """Generate top performers for a trial."""
    base_yield = 5.5 + random.uniform(0, 1)
    performers = []
    for i in range(1, 11):
        yield_val = round(base_yield + (10 - i) * 0.15 + random.uniform(-0.1, 0.1), 2)
        change = round((yield_val - base_yield) / base_yield * 100, 1)
        traits = random.sample(
            ["High yield", "Disease resistant", "Drought tolerant", "Early maturity", "Quality", "Lodging resistant"],
            k=random.randint(1, 3)
        )
        performers.append(TopPerformer(
            rank=i,
            germplasmDbId=f"grm-2025-{i:03d}",
            germplasmName=f"BM-2025-{random.randint(1, 100):03d}",
            yield_value=yield_val,
            change_percent=f"+{change}%" if change > 0 else f"{change}%",
            traits=traits
        ))
    return performers


def generate_trait_summary() -> List[TraitSummary]:
    """Generate trait summary statistics."""
    return [
        TraitSummary(trait="Grain Yield", mean=5.8, cv=12.4, lsd=0.45, fValue=8.7, significance="**"),
        TraitSummary(trait="Plant Height", mean=98, cv=8.2, lsd=5.2, fValue=15.3, significance="***"),
        TraitSummary(trait="Days to Maturity", mean=122, cv=4.5, lsd=3.1, fValue=22.1, significance="***"),
        TraitSummary(trait="Disease Score", mean=3.2, cv=28.6, lsd=0.8, fValue=5.4, significance="**"),
        TraitSummary(trait="1000 Grain Weight", mean=28.5, cv=6.8, lsd=1.2, fValue=12.8, significance="***"),
        TraitSummary(trait="Protein Content", mean=8.2, cv=9.4, lsd=0.5, fValue=7.2, significance="**"),
    ]


def generate_location_performance() -> List[LocationPerformance]:
    """Generate location performance data."""
    locations = [
        ("loc-1", "IRRI Los Baños"),
        ("loc-2", "CIMMYT El Batán"),
        ("loc-3", "ICRISAT Patancheru"),
        ("loc-4", "AfricaRice Ibadan"),
    ]
    return [
        LocationPerformance(
            locationDbId=loc_id,
            locationName=loc_name,
            entries=64,
            meanYield=round(5.2 + i * 0.3 + random.uniform(-0.2, 0.2), 2),
            cv=round(12 - i + random.uniform(-1, 1), 1),
            completionRate=round(85 + i * 3 + random.uniform(-2, 2), 0)
        )
        for i, (loc_id, loc_name) in enumerate(locations)
    ]


# ============================================
# ENDPOINTS
# ============================================

@router.get("/trials")
async def get_trials(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    status: Optional[str] = Query(None, description="Filter by status: active, completed, planned"),
):
    """Get list of trials with summary info."""
    trials = DEMO_TRIALS
    
    if program_id:
        trials = [t for t in trials if t.programDbId == program_id]
    
    if status:
        if status == "completed":
            trials = [t for t in trials if t.completionRate == 100]
        elif status == "active":
            trials = [t for t in trials if 0 < t.completionRate < 100]
    
    return {"data": [t.model_dump() for t in trials], "total": len(trials)}


@router.get("/trials/{trial_id}")
async def get_trial(trial_id: str):
    """Get trial details."""
    trial = next((t for t in DEMO_TRIALS if t.trialDbId == trial_id), None)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return {"data": trial.model_dump()}


@router.get("/trials/{trial_id}/summary", response_model=TrialSummaryResponse)
async def get_trial_summary(trial_id: str):
    """Get comprehensive trial summary."""
    trial = next((t for t in DEMO_TRIALS if t.trialDbId == trial_id), None)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    top_performers = generate_top_performers(trial_id)
    trait_summary = generate_trait_summary()
    location_performance = generate_location_performance()
    
    statistics = {
        "grand_mean": 5.8,
        "overall_cv": 12.4,
        "heritability": 0.72,
        "genetic_variance": 0.45,
        "error_variance": 0.18,
        "lsd_5_percent": 0.45,
        "selection_intensity": 1.4,
        "expected_gain": 2.3
    }
    
    return TrialSummaryResponse(
        trial=trial,
        topPerformers=top_performers,
        traitSummary=trait_summary,
        locationPerformance=location_performance,
        statistics=statistics
    )


@router.get("/trials/{trial_id}/top-performers")
async def get_top_performers(
    trial_id: str,
    limit: int = Query(10, ge=1, le=50),
    trait: Optional[str] = Query(None, description="Sort by specific trait"),
):
    """Get top performing entries in a trial."""
    trial = next((t for t in DEMO_TRIALS if t.trialDbId == trial_id), None)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    performers = generate_top_performers(trial_id)[:limit]
    return {"data": [p.model_dump() for p in performers], "trait": trait or "Yield"}


@router.get("/trials/{trial_id}/traits")
async def get_trait_summary(trial_id: str):
    """Get trait summary statistics for a trial."""
    trial = next((t for t in DEMO_TRIALS if t.trialDbId == trial_id), None)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    traits = generate_trait_summary()
    return {"data": [t.model_dump() for t in traits]}


@router.get("/trials/{trial_id}/locations")
async def get_location_performance(trial_id: str):
    """Get performance by location for a trial."""
    trial = next((t for t in DEMO_TRIALS if t.trialDbId == trial_id), None)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    locations = generate_location_performance()
    return {"data": [loc.model_dump() for loc in locations]}


@router.get("/trials/{trial_id}/statistics")
async def get_trial_statistics(trial_id: str):
    """Get detailed statistical analysis for a trial."""
    trial = next((t for t in DEMO_TRIALS if t.trialDbId == trial_id), None)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    return {
        "grand_mean": 5.8,
        "overall_cv": 12.4,
        "heritability": 0.72,
        "genetic_variance": 0.45,
        "error_variance": 0.18,
        "genotype_variance": 0.32,
        "gxe_variance": 0.15,
        "lsd_5_percent": 0.45,
        "lsd_1_percent": 0.62,
        "selection_intensity": 1.4,
        "expected_gain": 2.3,
        "realized_gain": 2.1,
        "anova": {
            "genotype": {"df": 255, "ss": 125.4, "ms": 0.49, "f": 8.7, "p": 0.001},
            "location": {"df": 3, "ss": 45.2, "ms": 15.07, "f": 267.3, "p": 0.001},
            "gxe": {"df": 765, "ss": 89.3, "ms": 0.12, "f": 2.1, "p": 0.001},
            "error": {"df": 1024, "ss": 57.8, "ms": 0.056, "f": None, "p": None}
        }
    }


@router.post("/trials/{trial_id}/export")
async def export_trial_summary(
    trial_id: str,
    format: str = Query("pdf", description="Export format: pdf, xlsx, docx"),
    sections: Optional[str] = Query(None, description="Comma-separated sections to include"),
):
    """Export trial summary report."""
    trial = next((t for t in DEMO_TRIALS if t.trialDbId == trial_id), None)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    return {
        "message": f"Report generated as {format.upper()}",
        "trial_id": trial_id,
        "format": format,
        "sections": sections.split(",") if sections else ["all"],
        "download_url": f"/api/v2/trial-summary/download/{trial_id}.{format}"
    }

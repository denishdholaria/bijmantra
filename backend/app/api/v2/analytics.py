"""
Apex Analytics API
Comprehensive breeding analytics with AI insights
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ============================================
# SCHEMAS
# ============================================

class GeneticGainData(BaseModel):
    year: int
    gain: float
    cumulative: float
    target: float


class HeritabilityData(BaseModel):
    trait: str
    value: float
    se: Optional[float] = None


class SelectionResponseData(BaseModel):
    generation: int
    mean: float
    variance: float
    selected: float


class CorrelationMatrix(BaseModel):
    traits: list[str]
    matrix: list[list[float]]


class AnalyticsSummary(BaseModel):
    total_trials: int
    active_studies: int
    germplasm_entries: int
    observations_this_month: int
    genetic_gain_rate: float
    data_quality_score: float
    selection_intensity: float
    breeding_cycle_days: int


class QuickInsight(BaseModel):
    id: str
    type: str  # success, warning, info
    title: str
    description: str
    action_label: Optional[str] = None
    action_route: Optional[str] = None
    created_at: datetime


class ComputeJob(BaseModel):
    id: str
    name: str
    status: str  # pending, running, completed, failed
    progress: int
    engine: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_url: Optional[str] = None


class AnalyticsResponse(BaseModel):
    genetic_gain: list[GeneticGainData]
    heritabilities: list[HeritabilityData]
    selection_response: list[SelectionResponseData]
    correlations: CorrelationMatrix
    summary: AnalyticsSummary
    insights: list[QuickInsight]


# ============================================
# ENDPOINTS
# ============================================

@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
    year_start: Optional[int] = Query(None, description="Start year"),
    year_end: Optional[int] = Query(None, description="End year"),
):
    """Get comprehensive breeding analytics data."""
    
    # Generate realistic demo data
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 1))
    
    genetic_gain = []
    cumulative = 0
    for i, year in enumerate(years):
        gain = round(1.8 + random.uniform(0, 0.8), 2)
        cumulative += gain
        genetic_gain.append(GeneticGainData(
            year=year,
            gain=gain,
            cumulative=round(cumulative, 2),
            target=2.0 * (i + 1)
        ))
    
    heritabilities = [
        HeritabilityData(trait="Yield", value=0.72, se=0.05),
        HeritabilityData(trait="Plant Height", value=0.85, se=0.03),
        HeritabilityData(trait="Days to Flowering", value=0.78, se=0.04),
        HeritabilityData(trait="Disease Resistance", value=0.45, se=0.08),
        HeritabilityData(trait="Grain Quality", value=0.65, se=0.06),
        HeritabilityData(trait="Drought Tolerance", value=0.52, se=0.07),
    ]
    
    selection_response = [
        SelectionResponseData(generation=i, mean=100 + i*5, variance=15-i, selected=108 + i*4)
        for i in range(6)
    ]
    
    correlations = CorrelationMatrix(
        traits=["Yield", "Height", "Flowering", "Quality", "Disease Res."],
        matrix=[
            [1.00, 0.35, -0.22, 0.45, 0.28],
            [0.35, 1.00, 0.18, 0.12, -0.15],
            [-0.22, 0.18, 1.00, -0.08, 0.05],
            [0.45, 0.12, -0.08, 1.00, 0.32],
            [0.28, -0.15, 0.05, 0.32, 1.00],
        ]
    )
    
    summary = AnalyticsSummary(
        total_trials=24,
        active_studies=156,
        germplasm_entries=12847,
        observations_this_month=45623,
        genetic_gain_rate=2.6,
        data_quality_score=94,
        selection_intensity=1.4,
        breeding_cycle_days=365
    )
    
    insights = [
        QuickInsight(
            id="insight-1",
            type="success",
            title="Genetic Gain Above Target",
            description="Your program is exceeding the 2% annual target by 0.6%",
            created_at=datetime.now()
        ),
        QuickInsight(
            id="insight-2",
            type="warning",
            title="Data Quality Alert",
            description="3 studies have missing observations that need attention",
            action_label="Review Studies",
            action_route="/studies?filter=incomplete",
            created_at=datetime.now()
        ),
        QuickInsight(
            id="insight-3",
            type="info",
            title="Crossing Recommendation",
            description="Veena identified 5 optimal crosses for disease resistance",
            action_label="View Crosses",
            action_route="/crossingplanner",
            created_at=datetime.now()
        ),
    ]
    
    return AnalyticsResponse(
        genetic_gain=genetic_gain,
        heritabilities=heritabilities,
        selection_response=selection_response,
        correlations=correlations,
        summary=summary,
        insights=insights
    )


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    program_id: Optional[str] = Query(None),
):
    """Get analytics summary statistics."""
    return AnalyticsSummary(
        total_trials=24,
        active_studies=156,
        germplasm_entries=12847,
        observations_this_month=45623,
        genetic_gain_rate=2.6,
        data_quality_score=94,
        selection_intensity=1.4,
        breeding_cycle_days=365
    )


@router.get("/genetic-gain")
async def get_genetic_gain(
    program_id: Optional[str] = Query(None),
    trait: Optional[str] = Query(None),
    years: int = Query(6, ge=1, le=20),
):
    """Get genetic gain trend data."""
    current_year = datetime.now().year
    year_list = list(range(current_year - years + 1, current_year + 1))
    
    data = []
    cumulative = 0
    for i, year in enumerate(year_list):
        gain = round(1.8 + random.uniform(0, 0.8), 2)
        cumulative += gain
        data.append({
            "year": year,
            "gain": gain,
            "cumulative": round(cumulative, 2),
            "target": 2.0 * (i + 1)
        })
    
    return {"data": data, "trait": trait or "Yield", "unit": "%"}


@router.get("/heritabilities")
async def get_heritabilities(
    program_id: Optional[str] = Query(None),
    study_id: Optional[str] = Query(None),
):
    """Get heritability estimates for traits."""
    return {
        "data": [
            {"trait": "Yield", "value": 0.72, "se": 0.05, "method": "REML"},
            {"trait": "Plant Height", "value": 0.85, "se": 0.03, "method": "REML"},
            {"trait": "Days to Flowering", "value": 0.78, "se": 0.04, "method": "REML"},
            {"trait": "Disease Resistance", "value": 0.45, "se": 0.08, "method": "REML"},
            {"trait": "Grain Quality", "value": 0.65, "se": 0.06, "method": "REML"},
            {"trait": "Drought Tolerance", "value": 0.52, "se": 0.07, "method": "REML"},
        ]
    }


@router.get("/correlations")
async def get_trait_correlations(
    program_id: Optional[str] = Query(None),
    traits: Optional[str] = Query(None, description="Comma-separated trait names"),
):
    """Get genetic correlation matrix between traits."""
    trait_list = ["Yield", "Height", "Flowering", "Quality", "Disease Res."]
    if traits:
        trait_list = [t.strip() for t in traits.split(",")]
    
    n = len(trait_list)
    matrix = [[1.0 if i == j else round(random.uniform(-0.3, 0.5), 2) for j in range(n)] for i in range(n)]
    # Make symmetric
    for i in range(n):
        for j in range(i+1, n):
            matrix[j][i] = matrix[i][j]
    
    return {"traits": trait_list, "matrix": matrix, "method": "Genetic Correlation"}


@router.get("/selection-response")
async def get_selection_response(
    program_id: Optional[str] = Query(None),
    generations: int = Query(5, ge=1, le=20),
):
    """Get selection response over generations."""
    data = []
    for i in range(generations + 1):
        data.append({
            "generation": i,
            "mean": round(100 + i * 5 + random.uniform(-1, 1), 2),
            "variance": round(15 - i * 0.5 + random.uniform(-0.5, 0.5), 2),
            "selected": round(108 + i * 4 + random.uniform(-1, 1), 2),
            "selection_differential": round(8 - i * 0.3, 2)
        })
    return {"data": data, "trait": "Yield", "unit": "kg/ha"}


@router.get("/insights")
async def get_ai_insights(
    program_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    """Get AI-generated insights from Veena."""
    insights = [
        {
            "id": "insight-1",
            "type": "success",
            "title": "Genetic Gain Above Target",
            "description": "Your program is exceeding the 2% annual target by 0.6%",
            "priority": 1,
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "insight-2",
            "type": "warning",
            "title": "Data Quality Alert",
            "description": "3 studies have missing observations that need attention",
            "action_label": "Review Studies",
            "action_route": "/studies?filter=incomplete",
            "priority": 2,
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "insight-3",
            "type": "info",
            "title": "Crossing Recommendation",
            "description": "Veena identified 5 optimal crosses for disease resistance improvement",
            "action_label": "View Crosses",
            "action_route": "/crossingplanner",
            "priority": 3,
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "insight-4",
            "type": "info",
            "title": "Trial Completion",
            "description": "Multi-location trial MLT-2025-001 is 95% complete",
            "action_label": "View Trial",
            "action_route": "/trials/MLT-2025-001",
            "priority": 4,
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "insight-5",
            "type": "success",
            "title": "New Variety Candidate",
            "description": "Entry GRM-2024-156 shows consistent performance across 8 locations",
            "action_label": "View Entry",
            "action_route": "/germplasm/GRM-2024-156",
            "priority": 5,
            "created_at": datetime.now().isoformat()
        },
    ]
    return {"insights": insights[:limit], "total": len(insights)}


@router.post("/compute/gblup")
async def run_gblup_analysis(
    program_id: Optional[str] = Query(None),
    trait: str = Query(..., description="Trait to analyze"),
):
    """Submit GBLUP analysis job."""
    job_id = f"gblup-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return ComputeJob(
        id=job_id,
        name=f"GBLUP Analysis - {trait}",
        status="pending",
        progress=0,
        engine="Fortran HPC",
        started_at=datetime.now()
    )


@router.get("/compute/{job_id}")
async def get_compute_job_status(job_id: str):
    """Get status of a compute job."""
    # Simulate job progress
    progress = min(100, random.randint(50, 100))
    status = "completed" if progress == 100 else "running"
    
    return ComputeJob(
        id=job_id,
        name="GBLUP Analysis",
        status=status,
        progress=progress,
        engine="Fortran HPC",
        started_at=datetime.now() - timedelta(minutes=5),
        completed_at=datetime.now() if status == "completed" else None,
        result_url=f"/api/v2/analytics/compute/{job_id}/results" if status == "completed" else None
    )


@router.get("/veena-summary")
async def get_veena_summary(
    program_id: Optional[str] = Query(None),
):
    """Get Veena AI natural language summary of analytics."""
    return {
        "summary": (
            "Namaste! 🙏 Your breeding program is performing exceptionally well this season. "
            "The genetic gain of 2.6% per year exceeds your target by 30%, driven primarily by "
            "improved selection accuracy from genomic predictions. I've noticed that yield and "
            "quality traits show a positive correlation (r=0.45), which is excellent for simultaneous "
            "improvement. However, the slight decrease in data quality score warrants attention - "
            "I recommend reviewing the 3 flagged studies before your next analysis cycle. "
            "Would you like me to generate a detailed report or prioritize the crossing recommendations?"
        ),
        "generated_at": datetime.now().isoformat(),
        "confidence": 0.92,
        "key_metrics": {
            "genetic_gain": "2.6% (above target)",
            "data_quality": "94% (slight decrease)",
            "active_trials": 24,
            "pending_actions": 3
        }
    }

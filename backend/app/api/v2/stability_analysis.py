"""
Stability Analysis API
Multi-environment trial stability analysis for variety evaluation

Endpoints:
- GET /api/v2/stability/varieties - List varieties with stability metrics
- GET /api/v2/stability/varieties/{id} - Get variety stability details
- POST /api/v2/stability/analyze - Run stability analysis
- GET /api/v2/stability/methods - List stability methods
- GET /api/v2/stability/recommendations - Get variety recommendations
- GET /api/v2/stability/comparison - Compare stability methods
- GET /api/v2/stability/statistics - Get overall statistics

Stability Methods:
    Eberhart & Russell (1966):
        bi = Σ(Yij × Ij) / Σ(Ij²)
        S²di = [Σ(Yij - Ȳi - bi×Ij)²] / (n-2) - MSe/r
        
    Shukla (1972):
        σ²i = [g(g-1)Σ(Yij - Ȳi - Ȳj + Ȳ..)²] / [(g-1)(g-2)(n-1)]
        
    Wricke (1962):
        Wi = Σ(Yij - Ȳi - Ȳj + Ȳ..)²
        
    Lin & Binns (1988):
        Pi = Σ(Yij - Mj)² / (2n)
        
    AMMI:
        ASV = √[(SSIPCA1/SSIPCA2)(IPCA1)² + (IPCA2)²]

Interpretation:
    bi ≈ 1: Average response to environments
    bi > 1: Responsive to favorable environments  
    bi < 1: Adapted to unfavorable environments
    Low S²di: High predictability
    Low σ²i, Wi: High stability
    Low Pi: Superior performance
    Low ASV: High stability
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.services.stability_analysis import stability_analysis_service

from app.api.deps import get_current_user

router = APIRouter(prefix="/stability", tags=["Stability Analysis"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class StabilityAnalysisRequest(BaseModel):
    """Request to run stability analysis"""
    variety_ids: List[str] = Field(..., description="Variety IDs to analyze")
    methods: List[str] = Field(
        default=["eberhart", "shukla", "wricke", "linbinns"], 
        description="Methods to use"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "variety_ids": ["1", "2", "3"],
            "methods": ["eberhart", "shukla", "wricke"],
        }
    })


# ============================================
# ENDPOINTS
# ============================================

@router.get("/varieties")
async def list_varieties(
    recommendation: Optional[str] = Query(
        None, 
        description="Filter by recommendation: wide, favorable, unfavorable"
    ),
    min_yield: Optional[float] = Query(None, description="Minimum mean yield"),
    sort_by: Optional[str] = Query(
        "stability_rank", 
        description="Sort by: stability_rank, mean_yield, bi, pi"
    ),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    List varieties with stability metrics
    
    Returns all varieties with their stability parameters from multiple methods.
    Queries real data from database - returns empty list if no MET data exists.
    """
    varieties = await stability_analysis_service.get_varieties(
        db, organization_id, recommendation, min_yield, sort_by or "stability_rank"
    )
    
    return {
        "success": True,
        "count": len(varieties),
        "varieties": varieties,
    }


@router.get("/varieties/{variety_id}")
async def get_variety_stability(
    variety_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Get detailed stability metrics for a variety
    
    Returns stability parameters and interpretation for a single variety.
    """
    variety = await stability_analysis_service.get_variety(db, organization_id, variety_id)
    
    if not variety:
        raise HTTPException(404, f"Variety {variety_id} not found")
    
    return {
        "success": True,
        **variety,
    }


@router.post("/analyze")
async def run_stability_analysis(
    request: StabilityAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Run stability analysis on selected varieties
    
    Calculates stability metrics using specified methods.
    Requires multi-environment trial data for meaningful results.
    
    Stability Formulas:
        bi = Σ(Yij × Ij) / Σ(Ij²)
        S²di = [Σ(Yij - Ȳi - bi×Ij)²] / (n-2) - MSe/r
        σ²i = [g(g-1)Σ(Yij - Ȳi - Ȳj + Ȳ..)²] / [(g-1)(g-2)(n-1)]
        Wi = Σ(Yij - Ȳi - Ȳj + Ȳ..)²
        Pi = Σ(Yij - Mj)² / (2n)
        ASV = √[(SSIPCA1/SSIPCA2)(IPCA1)² + (IPCA2)²]
    """
    if not request.variety_ids:
        raise HTTPException(400, "No variety IDs provided")
    
    results = await stability_analysis_service.analyze(
        db, organization_id, request.variety_ids, request.methods
    )
    
    return {
        "success": True,
        **results,
    }


@router.get("/methods")
async def list_stability_methods():
    """
    List available stability analysis methods
    
    Returns reference data for stability methods (Eberhart & Russell, Shukla, 
    Wricke, Lin & Binns, AMMI) with interpretation guidelines.
    """
    methods = stability_analysis_service.get_methods()
    
    return {
        "success": True,
        "methods": methods,
    }


@router.get("/recommendations")
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Get variety recommendations based on stability analysis
    
    Groups varieties by adaptation type:
    - Wide adaptation: bi ≈ 1, low S²di, low σ²i
    - Favorable environments: bi > 1, responsive to inputs
    - Unfavorable environments: bi < 1, consistent performance
    """
    recommendations = await stability_analysis_service.get_recommendations(
        db, organization_id
    )
    
    return {
        "success": True,
        "recommendations": recommendations,
    }


@router.get("/comparison")
async def compare_methods(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Compare stability rankings across methods
    
    Shows rank correlation between different stability measures.
    Useful for understanding method agreement and selecting appropriate metrics.
    """
    comparison = await stability_analysis_service.get_comparison(db, organization_id)
    
    return {
        "success": True,
        **comparison,
    }


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Get overall stability analysis statistics
    
    Returns summary statistics including variety counts by adaptation type,
    yield statistics, and analysis coverage.
    """
    statistics = await stability_analysis_service.get_statistics(db, organization_id)
    
    return {
        "success": True,
        "statistics": statistics,
    }

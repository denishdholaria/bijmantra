"""
Yield Map API
Spatial visualization of yield data across field plots
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import random

router = APIRouter(prefix="/yield-map", tags=["Yield Map"])


class PlotData(BaseModel):
    """Plot data for yield map"""
    row: int
    col: int
    plot_id: str
    germplasm: str
    yield_value: float
    rep: str
    observations: Optional[Dict[str, float]] = None


class StudyInfo(BaseModel):
    """Study information"""
    study_db_id: str
    study_name: str
    trial_name: Optional[str] = None
    location_name: Optional[str] = None
    season: Optional[str] = None


class YieldMapStats(BaseModel):
    """Yield map statistics"""
    total_plots: int
    min_yield: float
    max_yield: float
    avg_yield: float
    std_yield: float
    cv_percent: float


@router.get("/studies")
async def get_studies(
    program_id: Optional[str] = None,
    season: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    """
    Get studies available for yield mapping
    """
    # Demo studies
    studies = [
        {
            "studyDbId": "study-001",
            "studyName": "Rice Yield Trial 2024",
            "trialName": "Multi-Location Yield Trial",
            "locationName": "Field Station A",
            "season": "2024 Wet Season",
        },
        {
            "studyDbId": "study-002",
            "studyName": "Wheat Performance Trial",
            "trialName": "Advanced Yield Trial",
            "locationName": "Research Farm B",
            "season": "2024 Rabi",
        },
        {
            "studyDbId": "study-003",
            "studyName": "Maize Hybrid Evaluation",
            "trialName": "Hybrid Yield Trial",
            "locationName": "Experimental Station C",
            "season": "2024 Kharif",
        },
    ]
    
    return {
        "result": {
            "data": studies[:limit]
        },
        "metadata": {
            "pagination": {
                "currentPage": 0,
                "pageSize": limit,
                "totalCount": len(studies),
                "totalPages": 1,
            }
        }
    }


@router.get("/studies/{study_id}/plots")
async def get_field_plot_data(
    study_id: str,
    trait: str = Query(default="yield", description="Trait to visualize"),
):
    """
    Get plot data for yield map visualization
    """
    # Generate realistic plot data based on study
    random.seed(hash(study_id) % 1000)
    
    germplasms = [
        "IR64", "Nipponbare", "Kasalath", "N22", "Swarna",
        "MTU1010", "BPT5204", "Samba Mahsuri", "Check-1", "Check-2"
    ]
    
    plots = []
    rows = 8
    cols = 10
    
    for row in range(1, rows + 1):
        for col in range(1, cols + 1):
            # Simulate spatial variation
            base_yield = 4.5
            row_effect = (row - rows/2) * 0.1
            col_effect = (col - cols/2) * 0.05
            random_effect = random.gauss(0, 0.3)
            
            yield_value = max(2.0, base_yield + row_effect + col_effect + random_effect)
            
            plots.append({
                "observationUnitDbId": f"plot-{study_id}-{row}-{col}",
                "observationUnitName": f"R{row}C{col}",
                "germplasmDbId": f"germ-{(row + col) % len(germplasms)}",
                "germplasmName": germplasms[(row + col) % len(germplasms)],
                "observationUnitPosition": {
                    "positionCoordinateX": str(col),
                    "positionCoordinateY": str(row),
                    "positionCoordinateXType": "GRID_COL",
                    "positionCoordinateYType": "GRID_ROW",
                },
                "observations": [
                    {
                        "observationVariableName": "Grain Yield",
                        "observationVariableDbId": "var-yield",
                        "value": str(round(yield_value, 2)),
                        "observationTimeStamp": datetime.now().isoformat(),
                    },
                    {
                        "observationVariableName": "Plant Height",
                        "observationVariableDbId": "var-height",
                        "value": str(round(80 + random.gauss(0, 10), 1)),
                        "observationTimeStamp": datetime.now().isoformat(),
                    },
                ],
            })
    
    return {
        "result": {
            "data": plots
        },
        "metadata": {
            "pagination": {
                "currentPage": 0,
                "pageSize": len(plots),
                "totalCount": len(plots),
                "totalPages": 1,
            }
        }
    }


@router.get("/studies/{study_id}/stats")
async def get_yield_stats(study_id: str):
    """
    Get yield statistics for a study
    """
    random.seed(hash(study_id) % 1000)
    
    # Generate stats
    yields = [4.5 + random.gauss(0, 0.5) for _ in range(80)]
    avg_yield = sum(yields) / len(yields)
    variance = sum((y - avg_yield) ** 2 for y in yields) / len(yields)
    std_yield = variance ** 0.5
    
    return {
        "study_id": study_id,
        "total_plots": len(yields),
        "min_yield": round(min(yields), 2),
        "max_yield": round(max(yields), 2),
        "avg_yield": round(avg_yield, 2),
        "std_yield": round(std_yield, 2),
        "cv_percent": round((std_yield / avg_yield) * 100, 1) if avg_yield > 0 else 0,
    }


@router.get("/studies/{study_id}/traits")
async def get_available_traits(study_id: str):
    """
    Get available traits for a study
    """
    return {
        "data": [
            {"id": "yield", "name": "Grain Yield", "unit": "t/ha"},
            {"id": "height", "name": "Plant Height", "unit": "cm"},
            {"id": "maturity", "name": "Days to Maturity", "unit": "days"},
            {"id": "disease", "name": "Disease Score", "unit": "1-9"},
        ]
    }


@router.get("/studies/{study_id}/spatial-analysis")
async def get_spatial_analysis(study_id: str):
    """
    Get spatial analysis results for yield data
    """
    random.seed(hash(study_id) % 1000)
    
    return {
        "study_id": study_id,
        "spatial_autocorrelation": {
            "morans_i": round(random.uniform(0.1, 0.4), 3),
            "p_value": round(random.uniform(0.001, 0.05), 4),
            "significant": True,
        },
        "row_effect": {
            "variance": round(random.uniform(0.05, 0.15), 3),
            "percent_total": round(random.uniform(5, 15), 1),
        },
        "column_effect": {
            "variance": round(random.uniform(0.03, 0.10), 3),
            "percent_total": round(random.uniform(3, 10), 1),
        },
        "recommendations": [
            "Consider spatial adjustment in analysis",
            "Row blocking may improve precision",
        ],
    }

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
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
import random
import math

router = APIRouter(prefix="/stability", tags=["Stability Analysis"])


# ============================================
# DEMO DATA
# ============================================

DEMO_VARIETIES = [
    {
        "id": "v1",
        "name": "Elite-001",
        "mean_yield": 5.8,
        "rank": 2,
        "bi": 1.02,
        "s2di": 0.015,
        "sigma2i": 0.12,
        "wi": 2.5,
        "pi": 0.85,
        "asv": 0.42,
        "stability_rank": 1,
        "recommendation": "wide",
        "environments_tested": 12,
        "years_tested": 3,
    },
    {
        "id": "v2",
        "name": "Elite-002",
        "mean_yield": 5.5,
        "rank": 4,
        "bi": 0.95,
        "s2di": 0.022,
        "sigma2i": 0.18,
        "wi": 3.2,
        "pi": 1.25,
        "asv": 0.58,
        "stability_rank": 3,
        "recommendation": "wide",
        "environments_tested": 12,
        "years_tested": 3,
    },
    {
        "id": "v3",
        "name": "Elite-003",
        "mean_yield": 6.2,
        "rank": 1,
        "bi": 1.35,
        "s2di": 0.085,
        "sigma2i": 0.45,
        "wi": 8.5,
        "pi": 0.42,
        "asv": 1.25,
        "stability_rank": 5,
        "recommendation": "favorable",
        "environments_tested": 12,
        "years_tested": 3,
    },
    {
        "id": "v4",
        "name": "Elite-004",
        "mean_yield": 5.2,
        "rank": 5,
        "bi": 0.98,
        "s2di": 0.008,
        "sigma2i": 0.08,
        "wi": 1.8,
        "pi": 1.85,
        "asv": 0.28,
        "stability_rank": 2,
        "recommendation": "wide",
        "environments_tested": 12,
        "years_tested": 3,
    },
    {
        "id": "v5",
        "name": "Elite-005",
        "mean_yield": 5.9,
        "rank": 3,
        "bi": 1.18,
        "s2di": 0.052,
        "sigma2i": 0.32,
        "wi": 5.8,
        "pi": 0.68,
        "asv": 0.85,
        "stability_rank": 4,
        "recommendation": "favorable",
        "environments_tested": 12,
        "years_tested": 3,
    },
    {
        "id": "v6",
        "name": "Check-001",
        "mean_yield": 5.0,
        "rank": 6,
        "bi": 0.85,
        "s2di": 0.035,
        "sigma2i": 0.22,
        "wi": 4.2,
        "pi": 2.15,
        "asv": 0.65,
        "stability_rank": 6,
        "recommendation": "unfavorable",
        "environments_tested": 12,
        "years_tested": 3,
    },
]

STABILITY_METHODS = [
    {
        "id": "eberhart",
        "name": "Eberhart & Russell",
        "year": 1966,
        "type": "parametric",
        "description": "Regression-based stability using regression coefficient (bi) and deviation from regression (S²di)",
        "interpretation": {
            "bi_equal_1": "Average response to environments",
            "bi_greater_1": "Responsive to favorable environments",
            "bi_less_1": "Adapted to unfavorable environments",
            "s2di_near_0": "High predictability",
            "s2di_greater_0": "Low predictability",
        },
    },
    {
        "id": "shukla",
        "name": "Shukla's Stability Variance",
        "year": 1972,
        "type": "parametric",
        "description": "Stability variance (σ²i) for each genotype",
        "interpretation": {
            "low_sigma2i": "High stability",
            "high_sigma2i": "Low stability",
        },
    },
    {
        "id": "wricke",
        "name": "Wricke's Ecovalence",
        "year": 1962,
        "type": "parametric",
        "description": "Contribution to G×E interaction sum of squares",
        "interpretation": {
            "low_wi": "High stability (low G×E contribution)",
            "high_wi": "Low stability (high G×E contribution)",
        },
    },
    {
        "id": "linbinns",
        "name": "Lin & Binns Superiority",
        "year": 1988,
        "type": "parametric",
        "description": "Deviation from maximum response in each environment",
        "interpretation": {
            "low_pi": "Superior performance (close to best in each environment)",
            "high_pi": "Poor performance",
        },
    },
    {
        "id": "ammi",
        "name": "AMMI Stability Value",
        "year": 1992,
        "type": "multivariate",
        "description": "AMMI Stability Value (ASV) from AMMI analysis",
        "interpretation": {
            "low_asv": "High stability",
            "high_asv": "Low stability",
        },
    },
]


# ============================================
# SCHEMAS
# ============================================

class StabilityAnalysisRequest(BaseModel):
    """Request to run stability analysis"""
    variety_ids: List[str] = Field(..., description="Variety IDs to analyze")
    methods: List[str] = Field(default=["eberhart", "shukla", "wricke", "linbinns"], description="Methods to use")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "variety_ids": ["v1", "v2", "v3"],
            "methods": ["eberhart", "shukla", "wricke"],
        }
    })


# ============================================
# ENDPOINTS
# ============================================

@router.get("/varieties")
async def list_varieties(
    recommendation: Optional[str] = Query(None, description="Filter by recommendation: wide, favorable, unfavorable"),
    min_yield: Optional[float] = Query(None, description="Minimum mean yield"),
    sort_by: Optional[str] = Query("stability_rank", description="Sort by: stability_rank, mean_yield, bi, pi"),
):
    """
    List varieties with stability metrics
    
    Returns all varieties with their stability parameters from multiple methods.
    """
    varieties = DEMO_VARIETIES.copy()
    
    # Apply filters
    if recommendation:
        varieties = [v for v in varieties if v["recommendation"] == recommendation]
    
    if min_yield is not None:
        varieties = [v for v in varieties if v["mean_yield"] >= min_yield]
    
    # Sort
    if sort_by == "mean_yield":
        varieties.sort(key=lambda x: x["mean_yield"], reverse=True)
    elif sort_by == "bi":
        varieties.sort(key=lambda x: abs(x["bi"] - 1))  # Closest to 1
    elif sort_by == "pi":
        varieties.sort(key=lambda x: x["pi"])  # Lower is better
    else:
        varieties.sort(key=lambda x: x["stability_rank"])
    
    return {
        "success": True,
        "count": len(varieties),
        "varieties": varieties,
    }


@router.get("/varieties/{variety_id}")
async def get_variety_stability(variety_id: str):
    """Get detailed stability metrics for a variety"""
    variety = next((v for v in DEMO_VARIETIES if v["id"] == variety_id), None)
    
    if not variety:
        raise HTTPException(404, f"Variety {variety_id} not found")
    
    # Add detailed interpretation
    bi_interp = "average"
    if variety["bi"] > 1.1:
        bi_interp = "responsive"
    elif variety["bi"] < 0.9:
        bi_interp = "stable"
    
    predictability = "high" if variety["s2di"] < 0.03 else "low"
    
    return {
        "success": True,
        **variety,
        "interpretation": {
            "bi_category": bi_interp,
            "predictability": predictability,
            "shukla_category": "stable" if variety["sigma2i"] < 0.2 else "moderate" if variety["sigma2i"] < 0.35 else "unstable",
            "wricke_category": "stable" if variety["wi"] < 3 else "moderate" if variety["wi"] < 6 else "unstable",
            "linbinns_category": "superior" if variety["pi"] < 1 else "good" if variety["pi"] < 1.5 else "poor",
        },
    }


@router.post("/analyze")
async def run_stability_analysis(request: StabilityAnalysisRequest):
    """
    Run stability analysis on selected varieties
    
    Calculates stability metrics using specified methods.
    """
    varieties = [v for v in DEMO_VARIETIES if v["id"] in request.variety_ids]
    
    if not varieties:
        raise HTTPException(400, "No valid variety IDs provided")
    
    results = []
    for v in varieties:
        result = {
            "variety_id": v["id"],
            "variety_name": v["name"],
            "mean_yield": v["mean_yield"],
            "metrics": {},
        }
        
        if "eberhart" in request.methods:
            result["metrics"]["eberhart"] = {
                "bi": v["bi"],
                "s2di": v["s2di"],
                "response": "responsive" if v["bi"] > 1.1 else "stable" if v["bi"] < 0.9 else "average",
            }
        
        if "shukla" in request.methods:
            result["metrics"]["shukla"] = {
                "sigma2i": v["sigma2i"],
                "category": "stable" if v["sigma2i"] < 0.2 else "moderate" if v["sigma2i"] < 0.35 else "unstable",
            }
        
        if "wricke" in request.methods:
            result["metrics"]["wricke"] = {
                "wi": v["wi"],
                "category": "stable" if v["wi"] < 3 else "moderate" if v["wi"] < 6 else "unstable",
            }
        
        if "linbinns" in request.methods:
            result["metrics"]["linbinns"] = {
                "pi": v["pi"],
                "category": "superior" if v["pi"] < 1 else "good" if v["pi"] < 1.5 else "poor",
            }
        
        if "ammi" in request.methods:
            result["metrics"]["ammi"] = {
                "asv": v["asv"],
                "category": "stable" if v["asv"] < 0.5 else "moderate" if v["asv"] < 1 else "unstable",
            }
        
        results.append(result)
    
    return {
        "success": True,
        "methods_used": request.methods,
        "variety_count": len(results),
        "results": results,
    }


@router.get("/methods")
async def list_stability_methods():
    """List available stability analysis methods"""
    return {
        "success": True,
        "methods": STABILITY_METHODS,
    }


@router.get("/recommendations")
async def get_recommendations():
    """
    Get variety recommendations based on stability analysis
    
    Groups varieties by adaptation type.
    """
    wide = [v for v in DEMO_VARIETIES if v["recommendation"] == "wide"]
    favorable = [v for v in DEMO_VARIETIES if v["recommendation"] == "favorable"]
    unfavorable = [v for v in DEMO_VARIETIES if v["recommendation"] == "unfavorable"]
    
    return {
        "success": True,
        "recommendations": {
            "wide_adaptation": {
                "description": "Suitable for diverse environments",
                "criteria": "bi ≈ 1, low S²di, low σ²i",
                "varieties": [{"id": v["id"], "name": v["name"], "mean_yield": v["mean_yield"]} for v in wide],
            },
            "favorable_environments": {
                "description": "High yield potential under good conditions",
                "criteria": "bi > 1, responsive to inputs",
                "varieties": [{"id": v["id"], "name": v["name"], "mean_yield": v["mean_yield"]} for v in favorable],
            },
            "unfavorable_environments": {
                "description": "Stable under stress conditions",
                "criteria": "bi < 1, consistent performance",
                "varieties": [{"id": v["id"], "name": v["name"], "mean_yield": v["mean_yield"]} for v in unfavorable],
            },
        },
    }


@router.get("/comparison")
async def compare_methods():
    """
    Compare stability rankings across methods
    
    Shows rank correlation between different stability measures.
    """
    # Calculate ranks for each method
    varieties = DEMO_VARIETIES.copy()
    
    # Eberhart rank (by |bi - 1| + s2di)
    for v in varieties:
        v["er_score"] = abs(v["bi"] - 1) + v["s2di"] * 10
    varieties_er = sorted(varieties, key=lambda x: x["er_score"])
    er_ranks = {v["id"]: i + 1 for i, v in enumerate(varieties_er)}
    
    # Shukla rank
    varieties_sh = sorted(varieties, key=lambda x: x["sigma2i"])
    sh_ranks = {v["id"]: i + 1 for i, v in enumerate(varieties_sh)}
    
    # Wricke rank
    varieties_wr = sorted(varieties, key=lambda x: x["wi"])
    wr_ranks = {v["id"]: i + 1 for i, v in enumerate(varieties_wr)}
    
    # Lin & Binns rank
    varieties_lb = sorted(varieties, key=lambda x: x["pi"])
    lb_ranks = {v["id"]: i + 1 for i, v in enumerate(varieties_lb)}
    
    # AMMI rank
    varieties_am = sorted(varieties, key=lambda x: x["asv"])
    am_ranks = {v["id"]: i + 1 for i, v in enumerate(varieties_am)}
    
    comparison = []
    for v in DEMO_VARIETIES:
        ranks = [er_ranks[v["id"]], sh_ranks[v["id"]], wr_ranks[v["id"]], lb_ranks[v["id"]], am_ranks[v["id"]]]
        comparison.append({
            "variety_id": v["id"],
            "variety_name": v["name"],
            "eberhart_rank": er_ranks[v["id"]],
            "shukla_rank": sh_ranks[v["id"]],
            "wricke_rank": wr_ranks[v["id"]],
            "linbinns_rank": lb_ranks[v["id"]],
            "ammi_rank": am_ranks[v["id"]],
            "mean_rank": sum(ranks) / len(ranks),
        })
    
    comparison.sort(key=lambda x: x["mean_rank"])
    
    # Simple correlation matrix (demo values)
    correlation_matrix = {
        "eberhart": {"eberhart": 1.0, "shukla": 0.85, "wricke": 0.82, "linbinns": 0.78, "ammi": 0.88},
        "shukla": {"eberhart": 0.85, "shukla": 1.0, "wricke": 0.92, "linbinns": 0.75, "ammi": 0.90},
        "wricke": {"eberhart": 0.82, "shukla": 0.92, "wricke": 1.0, "linbinns": 0.72, "ammi": 0.87},
        "linbinns": {"eberhart": 0.78, "shukla": 0.75, "wricke": 0.72, "linbinns": 1.0, "ammi": 0.80},
        "ammi": {"eberhart": 0.88, "shukla": 0.90, "wricke": 0.87, "linbinns": 0.80, "ammi": 1.0},
    }
    
    return {
        "success": True,
        "comparison": comparison,
        "correlation_matrix": correlation_matrix,
    }


@router.get("/statistics")
async def get_statistics():
    """Get overall stability analysis statistics"""
    varieties = DEMO_VARIETIES
    
    return {
        "success": True,
        "statistics": {
            "total_varieties": len(varieties),
            "wide_adaptation": len([v for v in varieties if v["recommendation"] == "wide"]),
            "favorable_adaptation": len([v for v in varieties if v["recommendation"] == "favorable"]),
            "unfavorable_adaptation": len([v for v in varieties if v["recommendation"] == "unfavorable"]),
            "avg_yield": sum(v["mean_yield"] for v in varieties) / len(varieties),
            "max_yield": max(v["mean_yield"] for v in varieties),
            "min_yield": min(v["mean_yield"] for v in varieties),
            "avg_bi": sum(v["bi"] for v in varieties) / len(varieties),
            "environments_tested": 12,
            "years_tested": 3,
        },
    }

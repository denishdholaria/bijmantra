"""
Mixed Model API

Endpoints for formula-driven mixed model analysis and multi-environment heritability.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional, Dict, Any, Union
import json
import pandas as pd

from app.api import deps
from app.services.mixed_model import mixed_model_service
from app.services.phenotype_analysis import get_phenotype_service

router = APIRouter()

@router.post("/solve", response_model=Dict[str, Any])
async def solve_formula(
    formula: str = Body(..., description="R-style formula: y ~ Fixed + (1|Random)"),
    data: List[Dict[str, Any]] = Body(..., description="List of dictionaries (rows)"),
    current_user: Any = Depends(deps.get_current_active_user),
):
    """
    Solve a generic mixed model using a formula string.
    """
    if not data:
        raise HTTPException(status_code=400, detail="Data cannot be empty")
        
    try:
        y, X, Z = mixed_model_service.parse_formula(formula, data)
        result = mixed_model_service.solve_mme(y, X, Z)
        
        # Convert DataFrames to dicts for JSON serialization
        result["fixed_effects"] = result["fixed_effects"].to_dict(orient="records")
        result["random_effects"] = result["random_effects"].to_dict(orient="records")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mixed model analysis failed: {str(e)}")


@router.post("/analyze/rcbd", response_model=Dict[str, Any])
async def analyze_rcbd(
    data: List[Dict[str, Any]] = Body(..., description="List of dictionaries"),
    trait: str = Body(..., description="Response variable name"),
    genotype_col: str = Body("genotype"),
    block_col: str = Body("block"),
    current_user: Any = Depends(deps.get_current_active_user),
):
    """
    Run RCBD Analysis: Trait ~ Genotype + (1|Block)
    """
    try:
        result = mixed_model_service.analyze_rcbd(
            data, trait, genotype_col, block_col
        )
        
        # Serialization
        if "fixed_effects" in result:
             result["fixed_effects"] = result["fixed_effects"].to_dict(orient="records")
        if "random_effects" in result:
             result["random_effects"] = result["random_effects"].to_dict(orient="records")
             
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RCBD analysis failed: {str(e)}")


@router.post("/analyze/alpha-lattice", response_model=Dict[str, Any])
async def analyze_alpha(
    data: List[Dict[str, Any]] = Body(..., description="List of dictionaries"),
    trait: str = Body(..., description="Response variable name"),
    genotype_col: str = Body("genotype"),
    rep_col: str = Body("rep"),
    block_col: str = Body("block"),
    current_user: Any = Depends(deps.get_current_active_user),
):
    """
    Run Alpha-Lattice Analysis: Trait ~ Genotype + Rep + (1|Rep:Block)
    """
    try:
        result = mixed_model_service.analyze_alpha_lattice(
            data, trait, genotype_col, rep_col, block_col
        )
        
        # Serialization
        if "fixed_effects" in result:
             result["fixed_effects"] = result["fixed_effects"].to_dict(orient="records")
        if "random_effects" in result:
             result["random_effects"] = result["random_effects"].to_dict(orient="records")
             
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alpha-Lattice analysis failed: {str(e)}")


@router.post("/analyze/multi-env-heritability", response_model=Dict[str, Any])
async def analyze_multi_env_h2(
    data: List[Dict[str, Any]] = Body(..., description="List of dictionaries"),
    trait: str = Body(..., description="Response variable name"),
    genotype_col: str = Body("genotype"),
    env_col: str = Body("environment"),
    rep_col: str = Body("rep"),
    current_user: Any = Depends(deps.get_current_active_user),
):
    """
    Estimate Heritability from Multi-Environment Data.
    Partition variances into Vg, Vge, Ve.
    """
    service = get_phenotype_service()
    try:
        result = service.estimate_heritability_multi_env(
            data, trait, genotype_col, env_col, rep_col
        )
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-environment analysis failed: {str(e)}")

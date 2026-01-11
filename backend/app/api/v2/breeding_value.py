"""
Breeding Value Estimation API
BLUP, GBLUP, and genomic prediction
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.breeding_value import breeding_value_service

router = APIRouter(prefix="/breeding-value", tags=["Breeding Value"])


class BLUPRequest(BaseModel):
    phenotypes: List[Dict[str, Any]]
    pedigree: Optional[List[Dict[str, str]]] = None
    fixed_effects: Optional[List[str]] = None
    trait: str = "value"
    heritability: float = 0.3


class GBLUPRequest(BaseModel):
    phenotypes: List[Dict[str, Any]]
    markers: List[Dict[str, Any]]
    trait: str = "value"
    heritability: float = 0.3


class CrossPredictionRequest(BaseModel):
    parent1_ebv: float
    parent2_ebv: float
    trait_mean: float
    heritability: float = 0.3


class AccuracyRequest(BaseModel):
    predicted: List[float]
    observed: List[float]


class RankCandidatesRequest(BaseModel):
    breeding_values: List[Dict[str, Any]]
    selection_intensity: float = 0.1
    ebv_key: str = "ebv"


@router.post("/blup")
async def estimate_blup(data: BLUPRequest):
    """
    Estimate breeding values using BLUP
    Best Linear Unbiased Prediction using pedigree information
    """
    result = breeding_value_service.estimate_blup(
        phenotypes=data.phenotypes,
        pedigree=data.pedigree,
        fixed_effects=data.fixed_effects,
        trait=data.trait,
        heritability=data.heritability,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.post("/gblup")
async def estimate_gblup(data: GBLUPRequest):
    """
    Estimate genomic breeding values using GBLUP
    Uses genomic relationship matrix from marker data
    """
    result = breeding_value_service.estimate_gblup(
        phenotypes=data.phenotypes,
        markers=data.markers,
        trait=data.trait,
        heritability=data.heritability,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.post("/predict-cross")
async def predict_cross(data: CrossPredictionRequest):
    """Predict offspring performance from cross"""
    result = breeding_value_service.predict_cross(
        parent1_ebv=data.parent1_ebv,
        parent2_ebv=data.parent2_ebv,
        trait_mean=data.trait_mean,
        heritability=data.heritability,
    )
    return {"status": "success", "data": result}


@router.post("/accuracy")
async def calculate_accuracy(data: AccuracyRequest):
    """Calculate prediction accuracy"""
    result = breeding_value_service.calculate_accuracy(
        predicted=data.predicted,
        observed=data.observed,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.post("/rank-candidates")
async def rank_candidates(data: RankCandidatesRequest):
    """Rank and select breeding candidates"""
    result = breeding_value_service.rank_candidates(
        breeding_values=data.breeding_values,
        selection_intensity=data.selection_intensity,
        ebv_key=data.ebv_key,
    )
    return {"status": "success", "data": result}


@router.get("/analyses")
async def list_analyses():
    """List all breeding value analyses"""
    analyses = breeding_value_service.list_analyses()
    return {"status": "success", "data": analyses, "count": len(analyses)}


@router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get analysis results"""
    analysis = breeding_value_service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
    return {"status": "success", "data": analysis}


@router.get("/methods")
async def get_methods():
    """Get available breeding value estimation methods"""
    methods = breeding_value_service.get_methods()
    return {"status": "success", "data": methods}

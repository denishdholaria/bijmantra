"""
Selection Index API
Multi-trait selection indices for plant breeding
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.selection_index import selection_index_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/selection", tags=["Selection Index"], dependencies=[Depends(get_current_user)])


class SmithHazelRequest(BaseModel):
    phenotypic_values: List[Dict[str, Any]]
    trait_names: List[str]
    economic_weights: List[float]
    heritabilities: List[float]
    genetic_correlations: Optional[List[List[float]]] = None
    phenotypic_correlations: Optional[List[List[float]]] = None


class DesiredGainsRequest(BaseModel):
    phenotypic_values: List[Dict[str, Any]]
    trait_names: List[str]
    desired_gains: List[float]
    heritabilities: List[float]
    current_means: Optional[List[float]] = None


class BaseIndexRequest(BaseModel):
    phenotypic_values: List[Dict[str, Any]]
    trait_names: List[str]
    weights: List[float]


class IndependentCullingRequest(BaseModel):
    phenotypic_values: List[Dict[str, Any]]
    trait_names: List[str]
    thresholds: List[float]
    threshold_types: List[str]  # "min" or "max"


class TandemSelectionRequest(BaseModel):
    phenotypic_values: List[Dict[str, Any]]
    trait_sequence: List[str]
    selection_intensities: List[float]


class SelectionDifferentialRequest(BaseModel):
    all_values: List[float]
    selected_values: List[float]


class ResponsePredictionRequest(BaseModel):
    selection_intensity: float
    heritability: float
    phenotypic_std: float


@router.post("/smith-hazel")
async def calculate_smith_hazel(data: SmithHazelRequest):
    """
    Calculate Smith-Hazel selection index
    Optimal index using genetic parameters
    """
    try:
        result = selection_index_service.smith_hazel_index(
            phenotypic_values=data.phenotypic_values,
            trait_names=data.trait_names,
            economic_weights=data.economic_weights,
            heritabilities=data.heritabilities,
            genetic_correlations=data.genetic_correlations,
            phenotypic_correlations=data.phenotypic_correlations,
        )
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/desired-gains")
async def calculate_desired_gains(data: DesiredGainsRequest):
    """
    Calculate Desired Gains (Pesek-Baker) selection index
    Index to achieve specified genetic gains
    """
    try:
        result = selection_index_service.desired_gains_index(
            phenotypic_values=data.phenotypic_values,
            trait_names=data.trait_names,
            desired_gains=data.desired_gains,
            heritabilities=data.heritabilities,
            current_means=data.current_means,
        )
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/base-index")
async def calculate_base_index(data: BaseIndexRequest):
    """
    Calculate simple base index (weighted sum)
    I = w1*P1 + w2*P2 + ... + wn*Pn
    """
    result = selection_index_service.base_index(
        phenotypic_values=data.phenotypic_values,
        trait_names=data.trait_names,
        weights=data.weights,
    )
    return {"status": "success", "data": result}


@router.post("/independent-culling")
async def calculate_independent_culling(data: IndependentCullingRequest):
    """
    Independent culling levels selection
    Select individuals that meet ALL threshold criteria
    """
    result = selection_index_service.independent_culling(
        phenotypic_values=data.phenotypic_values,
        trait_names=data.trait_names,
        thresholds=data.thresholds,
        threshold_types=data.threshold_types,
    )
    return {"status": "success", "data": result}


@router.post("/tandem")
async def calculate_tandem_selection(data: TandemSelectionRequest):
    """
    Tandem selection - select for one trait at a time in sequence
    """
    result = selection_index_service.tandem_selection(
        phenotypic_values=data.phenotypic_values,
        trait_sequence=data.trait_sequence,
        selection_intensities=data.selection_intensities,
    )
    return {"status": "success", "data": result}


@router.post("/differential")
async def calculate_selection_differential(data: SelectionDifferentialRequest):
    """Calculate selection differential and intensity"""
    result = selection_index_service.calculate_selection_differential(
        all_values=data.all_values,
        selected_values=data.selected_values,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.post("/predict-response")
async def predict_response(data: ResponsePredictionRequest):
    """
    Predict response to selection using breeder's equation
    R = i × h² × σp
    """
    result = selection_index_service.predict_response(
        selection_intensity=data.selection_intensity,
        heritability=data.heritability,
        phenotypic_std=data.phenotypic_std,
    )
    return {"status": "success", "data": result}


@router.get("/methods")
async def get_selection_methods():
    """Get available selection methods"""
    methods = selection_index_service.get_selection_methods()
    return {"status": "success", "data": methods}


@router.get("/default-weights")
async def get_default_weights():
    """Get default economic weights for common traits"""
    weights = selection_index_service.get_default_weights()
    return {"status": "success", "data": weights}

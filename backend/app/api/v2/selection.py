"""
Selection Index API
Multi-trait selection indices for plant breeding
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator, model_validator

from app.api.deps import get_current_user
from app.modules.breeding.services.selection_index_service import selection_index_service


router = APIRouter(
    prefix="/selection", tags=["Selection Index"], dependencies=[Depends(get_current_user)]
)


class SmithHazelRequest(BaseModel):
    phenotypic_values: list[dict[str, Any]]
    trait_names: list[str]
    economic_weights: list[float]
    heritabilities: list[float]
    genetic_correlations: list[list[float]] | None = None
    phenotypic_correlations: list[list[float]] | None = None

    @field_validator("heritabilities")
    @classmethod
    def validate_heritabilities(cls, v: list[float]) -> list[float]:
        if any(h < 0 or h > 1 for h in v):
            raise ValueError("Heritability values must be between 0 and 1")
        return v

    @model_validator(mode="after")
    def validate_lengths(self) -> "SmithHazelRequest":
        n_traits = len(self.trait_names)
        if len(self.economic_weights) != n_traits:
            raise ValueError(f"Number of economic weights ({len(self.economic_weights)}) does not match number of traits ({n_traits})")
        if len(self.heritabilities) != n_traits:
            raise ValueError(f"Number of heritability values ({len(self.heritabilities)}) does not match number of traits ({n_traits})")
        return self


class DesiredGainsRequest(BaseModel):
    phenotypic_values: list[dict[str, Any]]
    trait_names: list[str]
    desired_gains: list[float]
    heritabilities: list[float]
    current_means: list[float] | None = None

    @field_validator("heritabilities")
    @classmethod
    def validate_heritabilities(cls, v: list[float]) -> list[float]:
        if any(h < 0 or h > 1 for h in v):
            raise ValueError("Heritability values must be between 0 and 1")
        return v

    @model_validator(mode="after")
    def validate_lengths(self) -> "DesiredGainsRequest":
        n_traits = len(self.trait_names)
        if len(self.desired_gains) != n_traits:
            raise ValueError(f"Number of desired gains ({len(self.desired_gains)}) does not match number of traits ({n_traits})")
        if len(self.heritabilities) != n_traits:
            raise ValueError(f"Number of heritability values ({len(self.heritabilities)}) does not match number of traits ({n_traits})")
        if self.current_means is not None and len(self.current_means) != n_traits:
            raise ValueError(f"Number of current means ({len(self.current_means)}) does not match number of traits ({n_traits})")
        return self


class BaseIndexRequest(BaseModel):
    phenotypic_values: list[dict[str, Any]]
    trait_names: list[str]
    weights: list[float]

    @model_validator(mode="after")
    def validate_lengths(self) -> "BaseIndexRequest":
        n_traits = len(self.trait_names)
        if len(self.weights) != n_traits:
            raise ValueError(f"Number of weights ({len(self.weights)}) does not match number of traits ({n_traits})")
        return self


class IndependentCullingRequest(BaseModel):
    phenotypic_values: list[dict[str, Any]]
    trait_names: list[str]
    thresholds: list[float]
    threshold_types: list[str]  # "min" or "max"

    @field_validator("threshold_types")
    @classmethod
    def validate_types(cls, v: list[str]) -> list[str]:
        valid_types = {"min", "max"}
        if any(t not in valid_types for t in v):
            raise ValueError("Threshold types must be 'min' or 'max'")
        return v

    @model_validator(mode="after")
    def validate_lengths(self) -> "IndependentCullingRequest":
        n_traits = len(self.trait_names)
        if len(self.thresholds) != n_traits:
            raise ValueError(f"Number of thresholds ({len(self.thresholds)}) does not match number of traits ({n_traits})")
        if len(self.threshold_types) != n_traits:
            raise ValueError(f"Number of threshold types ({len(self.threshold_types)}) does not match number of traits ({n_traits})")
        return self


class TandemSelectionRequest(BaseModel):
    phenotypic_values: list[dict[str, Any]]
    trait_sequence: list[str]
    selection_intensities: list[float]


class SelectionDifferentialRequest(BaseModel):
    all_values: list[float]
    selected_values: list[float]


class ResponsePredictionRequest(BaseModel):
    selection_intensity: float
    heritability: float
    phenotypic_std: float
    generation_interval: float = 1.0
    accuracy: float | None = None

    @field_validator("heritability")
    @classmethod
    def validate_heritability(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError("Heritability must be between 0 and 1")
        return v

    @field_validator("accuracy")
    @classmethod
    def validate_accuracy(cls, v: float | None) -> float | None:
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Accuracy must be between 0 and 1")
        return v

    @field_validator("selection_intensity", "phenotypic_std", "generation_interval")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Value must be positive")
        return v


class SelectionIndexCreate(BaseModel):
    name: str
    method: str
    trait_weights: dict[str, float]
    description: str | None = None
    config: dict[str, Any] | None = None


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
        generation_interval=data.generation_interval,
        accuracy=data.accuracy,
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


@router.post("/save")
async def save_index(data: SelectionIndexCreate):
    """Save a selection index configuration"""
    result = selection_index_service.save_index(data.model_dump())
    return {"status": "success", "data": result}


@router.get("/list")
async def list_indices():
    """List stored selection indices"""
    indices = selection_index_service.list_indices()
    return {"status": "success", "data": indices}


@router.get("/{index_id}")
async def get_index(index_id: str):
    """Get a specific selection index"""
    index = selection_index_service.get_index(index_id)
    if not index:
        raise HTTPException(status_code=404, detail="Index not found")
    return {"status": "success", "data": index}

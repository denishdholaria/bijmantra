"""
Genomic Selection API

Endpoints for GS model management, GEBV prediction, and selection tools.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ...services.genomic_selection import get_genomic_selection_service

router = APIRouter(prefix="/genomic-selection", tags=["Genomic Selection"])


@router.get("/models")
async def list_models(
    trait: Optional[str] = Query(None, description="Filter by trait"),
    method: Optional[str] = Query(None, description="Filter by method"),
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """List GS models with optional filters."""
    service = get_genomic_selection_service()
    models = service.list_models(trait=trait, method=method, status=status)
    return {"models": models, "total": len(models)}


@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """Get details for a specific model."""
    service = get_genomic_selection_service()
    model = service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.get("/models/{model_id}/predictions")
async def get_predictions(
    model_id: str,
    min_gebv: Optional[float] = Query(None, description="Minimum GEBV"),
    min_reliability: Optional[float] = Query(None, description="Minimum reliability"),
    selected_only: bool = Query(False, description="Only selected candidates"),
):
    """Get GEBV predictions for a model."""
    service = get_genomic_selection_service()
    predictions = service.get_predictions(
        model_id=model_id, min_gebv=min_gebv, min_reliability=min_reliability, selected_only=selected_only
    )
    return {"predictions": predictions, "total": len(predictions)}


@router.get("/models/{model_id}/selection-response")
async def get_selection_response(
    model_id: str,
    selection_intensity: float = Query(0.1, description="Selection intensity (proportion selected)"),
):
    """Calculate expected selection response."""
    service = get_genomic_selection_service()
    return service.get_selection_response(model_id=model_id, selection_intensity=selection_intensity)


@router.get("/yield-predictions")
async def get_yield_predictions(
    environment: Optional[str] = Query(None, description="Filter by environment"),
):
    """Get yield predictions."""
    service = get_genomic_selection_service()
    predictions = service.get_yield_predictions(environment=environment)
    return {"predictions": predictions, "total": len(predictions)}


@router.get("/cross-prediction")
async def get_cross_prediction(
    parent1_id: str = Query(..., description="First parent ID"),
    parent2_id: str = Query(..., description="Second parent ID"),
):
    """Predict progeny performance from cross."""
    service = get_genomic_selection_service()
    return service.get_cross_predictions(parent1_id=parent1_id, parent2_id=parent2_id)


@router.get("/comparison")
async def get_model_comparison():
    """Compare accuracy across models."""
    service = get_genomic_selection_service()
    return {"comparison": service.get_model_comparison()}


@router.get("/summary")
async def get_summary():
    """Get summary statistics."""
    service = get_genomic_selection_service()
    return service.get_summary()


@router.get("/methods")
async def get_methods():
    """Get available GS methods."""
    service = get_genomic_selection_service()
    return {"methods": service.get_methods()}


@router.get("/traits")
async def get_traits():
    """Get available traits."""
    service = get_genomic_selection_service()
    return {"traits": service.get_traits()}

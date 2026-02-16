"""
Genomic Selection API

Endpoints for GS model management, GEBV prediction, and selection tools.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict
import uuid

from ...services.genomic_selection import get_genomic_selection_service
from app.core.database import get_db
from app.api.deps import get_current_user
from ...schemas.genomic_selection import (
    GMatrixRequest, GMatrixResponse,
    GBLUPRequest, GBLUPResponse
)

router = APIRouter(prefix="/genomic-selection", tags=["Genomic Selection"])

# Simple in-memory cache for analysis results (since DB tables not ready)
_analysis_results: Dict[str, GBLUPResponse] = {}


@router.post("/g-matrix", response_model=GMatrixResponse)
async def calculate_g_matrix(request: GMatrixRequest):
    """Calculate Genomic Relationship Matrix."""
    service = get_genomic_selection_service()
    return service.calculate_g_matrix(markers=request.markers, ploidy=request.ploidy)


@router.post("/gblup", response_model=GBLUPResponse)
async def run_gblup(request: GBLUPRequest):
    """
    Run GBLUP analysis.

    Returns results immediately.
    """
    service = get_genomic_selection_service()
    result = service.run_gblup(
        phenotypes=request.phenotypes,
        g_matrix=request.g_matrix,
        heritability=request.heritability
    )

    # Store result with a new ID for retrieval
    analysis_id = str(uuid.uuid4())
    # Convert dict to Pydantic model
    response = GBLUPResponse(**result)
    _analysis_results[analysis_id] = response

    # Add analysis_id to response headers or wrap response?
    # For now, just return the response as per schema
    return response


@router.get("/gebvs/{analysis_id}", response_model=GBLUPResponse)
async def get_gebvs(analysis_id: str):
    """Get GEBVs for a specific analysis."""
    if analysis_id not in _analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _analysis_results[analysis_id]


@router.get("/models")
async def list_models(
    trait: Optional[str] = Query(None, description="Filter by trait"),
    method: Optional[str] = Query(None, description="Filter by method"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List GS models with optional filters."""
    service = get_genomic_selection_service()
    models = await service.list_models(db, current_user.organization_id, trait=trait, method=method, status=status)
    return {"models": models, "total": len(models)}


@router.get("/models/{model_id}")
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get details for a specific model."""
    service = get_genomic_selection_service()
    model = await service.get_model(db, current_user.organization_id, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.get("/models/{model_id}/predictions")
async def get_predictions(
    model_id: str,
    min_gebv: Optional[float] = Query(None, description="Minimum GEBV"),
    min_reliability: Optional[float] = Query(None, description="Minimum reliability"),
    selected_only: bool = Query(False, description="Only selected candidates"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get GEBV predictions for a model."""
    service = get_genomic_selection_service()
    predictions = await service.get_predictions(
        db, current_user.organization_id,
        model_id=model_id, min_gebv=min_gebv, min_reliability=min_reliability, selected_only=selected_only
    )
    return {"predictions": predictions, "total": len(predictions)}


@router.get("/models/{model_id}/selection-response")
async def get_selection_response(
    model_id: str,
    selection_intensity: float = Query(0.1, description="Selection intensity (proportion selected)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Calculate expected selection response."""
    service = get_genomic_selection_service()
    return await service.get_selection_response(db, current_user.organization_id, model_id=model_id, selection_intensity=selection_intensity)


@router.get("/yield-predictions")
async def get_yield_predictions(
    environment: Optional[str] = Query(None, description="Filter by environment"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get yield predictions."""
    service = get_genomic_selection_service()
    predictions = await service.get_yield_predictions(db, current_user.organization_id, environment=environment)
    return {"predictions": predictions, "total": len(predictions)}


@router.get("/cross-prediction")
async def get_cross_prediction(
    parent1_id: str = Query(..., description="First parent ID"),
    parent2_id: str = Query(..., description="Second parent ID"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Predict progeny performance from cross."""
    service = get_genomic_selection_service()
    return await service.get_cross_predictions(db, current_user.organization_id, parent1_id=parent1_id, parent2_id=parent2_id)


@router.get("/comparison")
async def get_model_comparison(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Compare accuracy across models."""
    service = get_genomic_selection_service()
    return {"comparison": await service.get_model_comparison(db, current_user.organization_id)}


@router.get("/summary")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get summary statistics."""
    service = get_genomic_selection_service()
    return await service.get_summary(db, current_user.organization_id)


@router.get("/methods")
async def get_methods(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get available GS methods."""
    service = get_genomic_selection_service()
    return {"methods": service.get_methods()}


@router.get("/traits")
async def get_traits(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get available traits."""
    service = get_genomic_selection_service()
    return {"traits": await service.get_traits(db, current_user.organization_id)}

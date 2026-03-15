"""
Genomic Selection API

Endpoints for GS model management, GEBV prediction, and selection tools.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db

from ...schemas.genomic_selection import (
    GBLUPRequest,
    GBLUPResponse,
    GMatrixRequest,
    GMatrixResponse,
)
from app.modules.genomics.services.genomic_selection_service import get_genomic_selection_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/genomic-selection", tags=["Genomic Selection"])

# ADR-002: Analysis results stored in Redis (restart-safe, multi-instance-safe).
# Falls back to a local dict only when Redis is unavailable (development only).
_GS_RESULT_PREFIX = "gs:result:"
_GS_RESULT_TTL = 86400  # 24 hours
_local_fallback: dict[str, dict] = {}  # dev-only fallback


def _local_fallback_enabled() -> bool:
    return settings.ENVIRONMENT != "production"


def _fallback_disabled_detail() -> str:
    return "Redis-backed genomic selection result storage is unavailable"


def _get_redis_client():
    from app.core.redis import redis_client

    return redis_client


async def _store_result(analysis_id: str, data: dict) -> None:
    """Persist a GBLUP result to Redis, falling back to local dict in development."""
    try:
        redis_client = _get_redis_client()
        if redis_client.is_available:
            await redis_client.set(f"{_GS_RESULT_PREFIX}{analysis_id}", data, ttl_seconds=_GS_RESULT_TTL)
            return
    except Exception as exc:
        logger.warning("Redis unavailable for GS result storage: %s", exc)
    if not _local_fallback_enabled():
        raise RuntimeError(_fallback_disabled_detail())
    _local_fallback[analysis_id] = data


async def _load_result(analysis_id: str) -> dict | None:
    """Load a GBLUP result from Redis, falling back to local dict in development."""
    try:
        redis_client = _get_redis_client()
        if redis_client.is_available:
            return await redis_client.get(f"{_GS_RESULT_PREFIX}{analysis_id}")
    except Exception as exc:
        logger.warning("Redis unavailable for GS result retrieval: %s", exc)
    if not _local_fallback_enabled():
        raise RuntimeError(_fallback_disabled_detail())
    return _local_fallback.get(analysis_id)


def _is_missing_table_error(error: ProgrammingError, table_name: str) -> bool:
    message = str(error).lower()
    return table_name in message and "does not exist" in message


@router.post("/g-matrix", response_model=GMatrixResponse)
async def calculate_g_matrix(request: GMatrixRequest):
    """Calculate Genomic Relationship Matrix."""
    service = get_genomic_selection_service()
    return service.calculate_g_matrix(markers=request.markers, ploidy=request.ploidy)


@router.post("/gblup", response_model=GBLUPResponse)
async def run_gblup(request: GBLUPRequest):
    """
    Run GBLUP analysis.

    Returns results immediately.  Results are persisted to Redis so they
    survive restarts and are accessible from any instance (ADR-002).
    """
    service = get_genomic_selection_service()
    result = service.run_gblup(
        phenotypes=request.phenotypes,
        g_matrix=request.g_matrix,
        heritability=request.heritability
    )

    analysis_id = str(uuid.uuid4())
    response = GBLUPResponse(**result)

    # Persist to Redis (ADR-002)
    try:
        await _store_result(analysis_id, response.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return response


@router.get("/gebvs/{analysis_id}", response_model=GBLUPResponse)
async def get_gebvs(analysis_id: str):
    """Get GEBVs for a specific analysis."""
    try:
        data = await _load_result(analysis_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if data is None:
        raise HTTPException(status_code=404, detail="Analysis not found or expired")
    return GBLUPResponse(**data) if isinstance(data, dict) else data


@router.get("/models")
async def list_models(
    trait: str | None = Query(None, description="Filter by trait"),
    method: str | None = Query(None, description="Filter by method"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List GS models with optional filters."""
    service = get_genomic_selection_service()
    try:
        models = await service.list_models(db, current_user.organization_id, trait=trait, method=method, status=status)
    except ProgrammingError as error:
        if not _is_missing_table_error(error, "gs_models"):
            raise
        await db.rollback()
        models = []
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
    min_gebv: float | None = Query(None, description="Minimum GEBV"),
    min_reliability: float | None = Query(None, description="Minimum reliability"),
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
    environment: str | None = Query(None, description="Filter by environment"),
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

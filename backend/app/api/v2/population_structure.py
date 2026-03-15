"""
Population Structure API

Endpoints for PCA, UMAP, t-SNE, and distance matrix calculations.
"""

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException

from app.api import deps
from app.modules.ai.services.dimensionality_reduction_service import dimensionality_reduction


router = APIRouter()

@router.post("/pca", response_model=dict[str, Any])
async def compute_pca(
    data: list[list[float]] = Body(..., description="Input matrix (n_samples x n_features)"),
    n_components: int = Body(10, ge=2, le=50),
    scale: bool = Body(True),
    current_user: Any = Depends(deps.get_current_active_user),
):
    """
    Run Principal Component Analysis (PCA) on provided data.
    """
    if not data:
        raise HTTPException(status_code=400, detail="Data matrix cannot be empty")

    result = dimensionality_reduction.run_pca(data, n_components=n_components, scale=scale)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result

@router.post("/umap", response_model=dict[str, Any])
async def compute_umap(
    data: list[list[float]] = Body(..., description="Input matrix (n_samples x n_features)"),
    n_components: int = Body(2, ge=2, le=10),
    n_neighbors: int = Body(15, ge=2),
    min_dist: float = Body(0.1, ge=0.0),
    metric: str = Body("euclidean"),
    scale: bool = Body(True),
    current_user: Any = Depends(deps.get_current_active_user),
):
    """
    Run Uniform Manifold Approximation and Projection (UMAP).
    """
    if not data:
        raise HTTPException(status_code=400, detail="Data matrix cannot be empty")

    result = dimensionality_reduction.run_umap(
        data,
        n_components=n_components,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric=metric,
        scale=scale
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result

@router.post("/distance-matrix", response_model=dict[str, Any])
async def compute_distance_matrix_endpoint(
    genotypes: list[list[int]] = Body(..., description="Genotype matrix (n_inds x n_markers)"),
    method: str = Body("modified_rogers", regex="^(euclidean|modified_rogers|nei|identity_by_state)$"),
    ploidy: int = Body(2, ge=1),
    current_user: Any = Depends(deps.get_current_active_user),
):
    """
    Compute genetic distance matrix between individuals.
    """
    if not genotypes:
        raise HTTPException(status_code=400, detail="Genotype matrix cannot be empty")

    result = dimensionality_reduction.compute_distance_matrix(
        genotypes,
        method=method,
        ploidy=ploidy
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result

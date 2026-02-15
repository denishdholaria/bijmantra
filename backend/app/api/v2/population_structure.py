"""
Population Structure API

Endpoints for PCA, UMAP, t-SNE, and distance matrix calculations.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.api import deps
from app.services.dimensionality_reduction import dimensionality_reduction
from app.models.genotyping import CallSet, Call, Variant

router = APIRouter()

@router.post("/pca", response_model=Dict[str, Any])
async def compute_pca(
    data: List[List[float]] = Body(..., description="Input matrix (n_samples x n_features)"),
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

@router.post("/umap", response_model=Dict[str, Any])
async def compute_umap(
    data: List[List[float]] = Body(..., description="Input matrix (n_samples x n_features)"),
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

@router.post("/distance-matrix", response_model=Dict[str, Any])
async def compute_distance_matrix_endpoint(
    genotypes: List[List[int]] = Body(..., description="Genotype matrix (n_inds x n_markers)"),
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

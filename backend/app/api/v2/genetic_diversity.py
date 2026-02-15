"""
Genetic Diversity Analysis API

Endpoints for population genetics analysis including diversity metrics,
genetic distances, and population structure.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...services.genetic_diversity import get_genetic_diversity_service
from app.core.database import get_db
from app.api.deps import get_current_user


router = APIRouter(prefix="/genetic-diversity", tags=["Genetic Diversity"])


@router.get("/populations")
async def list_populations(
    crop: Optional[str] = Query(None, description="Filter by crop"),
    program_id: Optional[str] = Query(None, description="Filter by program ID"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """List available populations for diversity analysis."""
    service = get_genetic_diversity_service()
    populations = await service.list_populations(db, current_user.organization_id, crop=crop, program_id=program_id)
    return {"data": populations}


@router.get("/populations/{population_id}")
async def get_population(
    population_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single population by ID."""
    service = get_genetic_diversity_service()
    population = await service.get_population(db, current_user.organization_id, population_id)
    if not population:
        raise HTTPException(status_code=404, detail="Population not found")
    return {"data": population}


@router.get("/populations/{population_id}/metrics")
async def get_diversity_metrics(
    population_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get diversity metrics for a population."""
    service = get_genetic_diversity_service()
    metrics = await service.get_diversity_metrics(db, current_user.organization_id, population_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Population not found")
    return {"data": metrics}


@router.get("/distances")
async def get_genetic_distances(
    population_ids: Optional[str] = Query(None, description="Comma-separated population IDs"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """Get pairwise genetic distances between populations."""
    service = get_genetic_diversity_service()
    
    pop_ids = None
    if population_ids:
        pop_ids = [p.strip() for p in population_ids.split(",")]
    
    distances = await service.get_genetic_distances(db, current_user.organization_id, population_ids=pop_ids)
    return {"data": distances}


@router.get("/amova")
async def get_amova_results(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get AMOVA (Analysis of Molecular Variance) results."""
    service = get_genetic_diversity_service()
    return {"data": await service.get_amova_results(db, current_user.organization_id)}


@router.get("/admixture")
async def get_admixture_proportions(
    k: int = Query(3, ge=2, le=10, description="Number of clusters"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """Get admixture proportions for population structure analysis."""
    service = get_genetic_diversity_service()
    return {"data": await service.get_admixture_proportions(db, current_user.organization_id, k=k)}


@router.get("/pca")
async def get_pca_data(
    population_ids: Optional[str] = Query(None, description="Comma-separated population IDs"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """Get PCA data for visualization."""
    service = get_genetic_diversity_service()
    
    pop_ids = None
    if population_ids:
        pop_ids = [p.strip() for p in population_ids.split(",")]
    
    return {"data": await service.get_pca_data(db, current_user.organization_id, population_ids=pop_ids)}


@router.get("/summary")
async def get_summary_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get summary statistics across all populations."""
    service = get_genetic_diversity_service()
    return {"data": await service.get_summary_statistics(db, current_user.organization_id)}

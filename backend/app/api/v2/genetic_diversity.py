"""
Genetic Diversity Analysis API

Endpoints for population genetics analysis including diversity metrics,
genetic distances, and population structure.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ...services.genetic_diversity import get_genetic_diversity_service


router = APIRouter(prefix="/genetic-diversity", tags=["Genetic Diversity"])


@router.get("/populations")
async def list_populations(
    crop: Optional[str] = Query(None, description="Filter by crop"),
    program_id: Optional[str] = Query(None, description="Filter by program ID"),
):
    """List available populations for diversity analysis."""
    service = get_genetic_diversity_service()
    populations = service.list_populations(crop=crop, program_id=program_id)
    return {"data": populations}


@router.get("/populations/{population_id}")
async def get_population(population_id: str):
    """Get a single population by ID."""
    service = get_genetic_diversity_service()
    population = service.get_population(population_id)
    if not population:
        raise HTTPException(status_code=404, detail="Population not found")
    return {"data": population}


@router.get("/populations/{population_id}/metrics")
async def get_diversity_metrics(population_id: str):
    """Get diversity metrics for a population."""
    service = get_genetic_diversity_service()
    metrics = service.get_diversity_metrics(population_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Population not found")
    return {"data": metrics}


@router.get("/distances")
async def get_genetic_distances(
    population_ids: Optional[str] = Query(None, description="Comma-separated population IDs"),
):
    """Get pairwise genetic distances between populations."""
    service = get_genetic_diversity_service()
    
    pop_ids = None
    if population_ids:
        pop_ids = [p.strip() for p in population_ids.split(",")]
    
    distances = service.get_genetic_distances(population_ids=pop_ids)
    return {"data": distances}


@router.get("/amova")
async def get_amova_results():
    """Get AMOVA (Analysis of Molecular Variance) results."""
    service = get_genetic_diversity_service()
    return {"data": service.get_amova_results()}


@router.get("/admixture")
async def get_admixture_proportions(
    k: int = Query(3, ge=2, le=10, description="Number of clusters"),
):
    """Get admixture proportions for population structure analysis."""
    service = get_genetic_diversity_service()
    return {"data": service.get_admixture_proportions(k=k)}


@router.get("/pca")
async def get_pca_data(
    population_ids: Optional[str] = Query(None, description="Comma-separated population IDs"),
):
    """Get PCA data for visualization."""
    service = get_genetic_diversity_service()
    
    pop_ids = None
    if population_ids:
        pop_ids = [p.strip() for p in population_ids.split(",")]
    
    return {"data": service.get_pca_data(population_ids=pop_ids)}


@router.get("/summary")
async def get_summary_statistics():
    """Get summary statistics across all populations."""
    service = get_genetic_diversity_service()
    return {"data": service.get_summary_statistics()}

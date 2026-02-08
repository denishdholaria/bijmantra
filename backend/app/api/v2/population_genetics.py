"""
Population Genetics API

Endpoints for population structure analysis, PCA, Fst calculations,
Hardy-Weinberg equilibrium tests, and migration rate estimation.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...services.population_genetics import get_population_genetics_service
from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter(prefix="/population-genetics", tags=["Population Genetics"])


@router.get("/populations")
async def list_populations(
    crop: Optional[str] = Query(None, description="Filter by crop"),
    region: Optional[str] = Query(None, description="Filter by region"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """List available populations for analysis."""
    service = get_population_genetics_service()
    populations = await service.list_populations(db, current_user.organization_id, crop=crop, region=region)
    return {
        "populations": populations,
        "total": len(populations),
    }


@router.get("/populations/{population_id}")
async def get_population(
    population_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get details for a specific population."""
    service = get_population_genetics_service()
    population = await service.get_population(db, current_user.organization_id, population_id)
    if not population:
        raise HTTPException(status_code=404, detail="Population not found")
    return population


@router.get("/populations/{population_id}/statistics")
async def get_population_statistics(
    population_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get detailed statistics for a population."""
    service = get_population_genetics_service()
    stats = await service.get_population_statistics(db, current_user.organization_id, population_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Population not found")
    return stats


@router.get("/structure")
async def get_structure_analysis(
    k: int = Query(3, ge=2, le=10, description="Number of clusters"),
    population_ids: Optional[str] = Query(None, description="Comma-separated population IDs"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """Get STRUCTURE/ADMIXTURE analysis results."""
    service = get_population_genetics_service()
    pop_ids = population_ids.split(",") if population_ids else None
    return await service.get_structure_analysis(db, current_user.organization_id, k=k, population_ids=pop_ids)


@router.get("/pca")
async def get_pca_results(
    population_ids: Optional[str] = Query(None, description="Comma-separated population IDs"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """Get PCA results for population structure visualization."""
    service = get_population_genetics_service()
    pop_ids = population_ids.split(",") if population_ids else None
    return await service.get_pca_results(db, current_user.organization_id, population_ids=pop_ids)


@router.get("/fst")
async def get_fst_analysis(
    population_ids: Optional[str] = Query(None, description="Comma-separated population IDs"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """Get pairwise Fst analysis between populations."""
    service = get_population_genetics_service()
    pop_ids = population_ids.split(",") if population_ids else None
    return await service.get_fst_analysis(db, current_user.organization_id, population_ids=pop_ids)


@router.get("/hardy-weinberg/{population_id}")
async def get_hardy_weinberg_test(
    population_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get Hardy-Weinberg equilibrium test results for a population."""
    service = get_population_genetics_service()
    result = await service.get_hardy_weinberg_test(db, current_user.organization_id, population_id)
    if not result:
        raise HTTPException(status_code=404, detail="Population not found")
    return result


@router.get("/migration")
async def get_migration_rates(
    population_ids: Optional[str] = Query(None, description="Comma-separated population IDs"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """Calculate migration rates (Nm) between populations."""
    service = get_population_genetics_service()
    pop_ids = population_ids.split(",") if population_ids else None
    return await service.get_migration_rates(db, current_user.organization_id, population_ids=pop_ids)


@router.get("/summary")
async def get_summary_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get summary statistics across all populations."""
    service = get_population_genetics_service()
    return await service.get_summary_statistics(db, current_user.organization_id)

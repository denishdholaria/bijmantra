"""
QTL Mapping API

Endpoints for QTL detection, GWAS analysis, and candidate gene identification.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...services.qtl_mapping import get_qtl_mapping_service
from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter(prefix="/qtl-mapping", tags=["QTL Mapping"])


@router.get("/qtls")
async def list_qtls(
    trait: Optional[str] = Query(None, description="Filter by trait"),
    chromosome: Optional[str] = Query(None, description="Filter by chromosome"),
    min_lod: float = Query(0, description="Minimum LOD score"),
    population: Optional[str] = Query(None, description="Filter by mapping population"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """List detected QTLs with optional filters."""
    service = get_qtl_mapping_service()
    qtls = await service.list_qtls(db, current_user.organization_id, trait=trait, chromosome=chromosome, min_lod=min_lod, population=population)
    return {
        "qtls": qtls,
        "total": len(qtls),
    }


@router.get("/qtls/{qtl_id}")
async def get_qtl(
    qtl_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get details for a specific QTL."""
    service = get_qtl_mapping_service()
    qtl = await service.get_qtl(db, current_user.organization_id, qtl_id)
    if not qtl:
        raise HTTPException(status_code=404, detail="QTL not found")
    return qtl


@router.get("/qtls/{qtl_id}/candidates")
async def get_candidate_genes(
    qtl_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get candidate genes within a QTL confidence interval."""
    service = get_qtl_mapping_service()
    qtl = await service.get_qtl(db, current_user.organization_id, qtl_id)
    if not qtl:
        raise HTTPException(status_code=404, detail="QTL not found")

    candidates = await service.get_candidate_genes(db, current_user.organization_id, qtl_id)
    return {
        "qtl_id": qtl_id,
        "qtl_name": qtl["name"],
        "confidence_interval": qtl["confidence_interval"],
        "candidates": candidates,
        "total": len(candidates),
    }


@router.get("/gwas")
async def get_gwas_results(
    trait: Optional[str] = Query(None, description="Filter by trait"),
    chromosome: Optional[str] = Query(None, description="Filter by chromosome"),
    min_log_p: float = Query(0, description="Minimum -log10(p-value)"),
    max_p_value: Optional[float] = Query(None, description="Maximum p-value"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """Get GWAS marker-trait associations."""
    service = get_qtl_mapping_service()
    results = await service.get_gwas_results(db, current_user.organization_id, trait=trait, chromosome=chromosome, min_log_p=min_log_p, max_p_value=max_p_value)
    return {
        "associations": results,
        "total": len(results),
    }


@router.get("/manhattan")
async def get_manhattan_data(
    trait: Optional[str] = Query(None, description="Filter by trait"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """Get data for Manhattan plot visualization."""
    service = get_qtl_mapping_service()
    return await service.get_manhattan_data(db, current_user.organization_id, trait=trait)


@router.get("/lod-profile/{chromosome}")
async def get_lod_profile(
    chromosome: str,
    trait: Optional[str] = Query(None, description="Filter by trait"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """Get LOD score profile for a chromosome."""
    service = get_qtl_mapping_service()
    return await service.get_lod_profile(db, current_user.organization_id, chromosome=chromosome, trait=trait)


@router.get("/go-enrichment")
async def get_go_enrichment(
    qtl_ids: Optional[str] = Query(None, description="Comma-separated QTL IDs"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """Get GO enrichment analysis for candidate genes."""
    service = get_qtl_mapping_service()
    ids = qtl_ids.split(",") if qtl_ids else None
    return {
        "enrichment": await service.get_go_enrichment(db, current_user.organization_id, qtl_ids=ids),
    }


@router.get("/summary/qtl")
async def get_qtl_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get summary statistics for QTL analysis."""
    service = get_qtl_mapping_service()
    return await service.get_qtl_summary(db, current_user.organization_id)


@router.get("/summary/gwas")
async def get_gwas_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get summary statistics for GWAS analysis."""
    service = get_qtl_mapping_service()
    return await service.get_gwas_summary(db, current_user.organization_id)


@router.get("/traits")
async def get_traits(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of available traits."""
    service = get_qtl_mapping_service()
    return {"traits": await service.get_traits(db, current_user.organization_id)}


@router.get("/populations")
async def get_populations(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of available mapping populations."""
    service = get_qtl_mapping_service()
    return {"populations": await service.get_populations(db, current_user.organization_id)}

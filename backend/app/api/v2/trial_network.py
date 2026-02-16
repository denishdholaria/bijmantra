"""
Trial Network API

Endpoints for multi-environment trial coordination.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.trial_network import trial_network_service


router = APIRouter(prefix="/trial-network", tags=["Trial Network"])


@router.get("/sites", summary="List trial sites")
async def list_sites(
    season: Optional[str] = Query(None, description="Filter by season"),
    status: Optional[str] = Query(None, description="Filter by status"),
    country: Optional[str] = Query(None, description="Filter by country"),
    region: Optional[str] = Query(None, description="Filter by region"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of trial sites in the network."""
    sites = await trial_network_service.get_sites(
        db, current_user.organization_id,
        season=season, status=status, country=country, region=region
    )
    return {"success": True, "count": len(sites), "sites": sites}


@router.get("/sites/{site_id}", summary="Get trial site")
async def get_site(
    site_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get details of a specific trial site."""
    site = await trial_network_service.get_site(db, current_user.organization_id, site_id)
    if not site:
        raise HTTPException(404, f"Site {site_id} not found")
    return {"success": True, "data": site}


@router.get("/statistics", summary="Get network statistics")
async def get_statistics(
    season: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get network-wide statistics."""
    stats = await trial_network_service.get_statistics(db, current_user.organization_id, season=season)
    return {"success": True, "data": stats}


@router.get("/germplasm", summary="Get shared germplasm")
async def get_shared_germplasm(
    min_sites: int = Query(1, description="Minimum sites"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get germplasm shared across multiple sites."""
    germplasm = await trial_network_service.get_shared_germplasm(
        db, current_user.organization_id, min_sites=min_sites, crop=crop
    )
    return {"success": True, "count": len(germplasm), "germplasm": germplasm}


@router.get("/performance", summary="Get network performance")
async def get_network_performance(
    trait: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get network-wide performance metrics."""
    performance = await trial_network_service.get_network_performance(
        db, current_user.organization_id, trait=trait
    )
    return {"success": True, "count": len(performance), "performance": performance}


@router.post("/compare", summary="Compare sites")
async def compare_sites(
    site_ids: List[str],
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Compare performance across selected sites."""
    if len(site_ids) < 2:
        raise HTTPException(400, "At least 2 sites required for comparison")
    comparison = await trial_network_service.get_site_comparison(
        db, current_user.organization_id, site_ids
    )
    return {"success": True, "data": comparison}


@router.get("/countries", summary="Get countries")
async def get_countries(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of countries with trial sites."""
    countries = await trial_network_service.get_countries(db, current_user.organization_id)
    return {"success": True, "count": len(countries), "countries": countries}


@router.get("/seasons", summary="Get seasons")
async def get_seasons(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get available seasons."""
    seasons = await trial_network_service.get_seasons(db, current_user.organization_id)
    return {"success": True, "seasons": seasons}

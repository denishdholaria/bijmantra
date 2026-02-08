"""
Germplasm Search API

Advanced germplasm search and discovery endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from app.services.germplasm_search import germplasm_search_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user


router = APIRouter(prefix="/germplasm-search", tags=["Germplasm Search"])


@router.get("/search", summary="Search germplasm")
async def search_germplasm(
    query: Optional[str] = Query(None, description="Search query"),
    species: Optional[str] = Query(None, description="Filter by species"),
    origin: Optional[str] = Query(None, description="Filter by country of origin"),
    collection: Optional[str] = Query(None, description="Filter by collection"),
    trait: Optional[str] = Query(None, description="Filter by trait"),
    limit: int = Query(50, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Search germplasm with advanced filters."""
    results =  await germplasm_search_service.search(db, current_user.organization_id, 
        query=query, species=species, origin=origin, 
        collection=collection, trait=trait, limit=limit
    )
    return {"success": True, "count": len(results), "results": results}


@router.get("/filters", summary="Get filter options")
async def get_filters(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get available filter options for search."""
    filters =  await germplasm_search_service.get_filters(db, current_user.organization_id)
    return {"success": True, "data": filters}


@router.get("/statistics", summary="Get statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get germplasm search statistics."""
    stats =  await germplasm_search_service.get_statistics(db, current_user.organization_id)
    return {"success": True, "data": stats}


@router.get("/{germplasm_id}", summary="Get germplasm")
async def get_germplasm(
    germplasm_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get germplasm by ID."""
    germplasm =  await germplasm_search_service.get_by_id(db, current_user.organization_id, germplasm_id)
    if not germplasm:
        raise HTTPException(404, f"Germplasm {germplasm_id} not found")
    return {"success": True, "data": germplasm}

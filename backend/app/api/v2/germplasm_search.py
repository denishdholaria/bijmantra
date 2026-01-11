"""
Germplasm Search API

Advanced germplasm search and discovery endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.services.germplasm_search import germplasm_search_service


router = APIRouter(prefix="/germplasm-search", tags=["Germplasm Search"])


@router.get("/search", summary="Search germplasm")
async def search_germplasm(
    query: Optional[str] = Query(None, description="Search query"),
    species: Optional[str] = Query(None, description="Filter by species"),
    origin: Optional[str] = Query(None, description="Filter by country of origin"),
    collection: Optional[str] = Query(None, description="Filter by collection"),
    trait: Optional[str] = Query(None, description="Filter by trait"),
    limit: int = Query(50, description="Maximum results"),
):
    """Search germplasm with advanced filters."""
    results = germplasm_search_service.search(
        query=query, species=species, origin=origin, 
        collection=collection, trait=trait, limit=limit
    )
    return {"success": True, "count": len(results), "results": results}


@router.get("/filters", summary="Get filter options")
async def get_filters():
    """Get available filter options for search."""
    filters = germplasm_search_service.get_filters()
    return {"success": True, "data": filters}


@router.get("/statistics", summary="Get statistics")
async def get_statistics():
    """Get germplasm search statistics."""
    stats = germplasm_search_service.get_statistics()
    return {"success": True, "data": stats}


@router.get("/{germplasm_id}", summary="Get germplasm")
async def get_germplasm(germplasm_id: str):
    """Get germplasm by ID."""
    germplasm = germplasm_search_service.get_by_id(germplasm_id)
    if not germplasm:
        raise HTTPException(404, f"Germplasm {germplasm_id} not found")
    return {"success": True, "data": germplasm}

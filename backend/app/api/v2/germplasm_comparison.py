"""
Germplasm Comparison API

Compare multiple germplasm entries side-by-side for selection decisions.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.services.germplasm_comparison import get_germplasm_comparison_service

router = APIRouter(prefix="/germplasm-comparison", tags=["Germplasm Comparison"])


class CompareRequest(BaseModel):
    """Request body for comparison."""
    ids: List[str]


@router.get("")
async def list_germplasm(
    search: Optional[str] = Query(None, description="Search by name, accession, or pedigree"),
    species: Optional[str] = Query(None, description="Filter by species"),
    status: Optional[str] = Query(None, description="Filter by status (active, archived, candidate)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    List germplasm entries available for comparison.
    
    Returns paginated list with traits and markers.
    """
    service = get_germplasm_comparison_service()
    return service.list_germplasm(
        search=search,
        species=species,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.get("/entry/{germplasm_id}")
async def get_germplasm(germplasm_id: str):
    """Get a single germplasm entry by ID."""
    service = get_germplasm_comparison_service()
    entry = service.get_germplasm(germplasm_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Germplasm not found")
    return entry


@router.post("/compare")
async def compare_germplasm(request: CompareRequest):
    """
    Compare multiple germplasm entries.
    
    Returns detailed comparison with:
    - Trait values for each entry
    - Best values highlighted
    - Marker presence/absence
    - Selection recommendations
    """
    if len(request.ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 entries required for comparison")
    if len(request.ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 entries allowed for comparison")
    
    service = get_germplasm_comparison_service()
    return service.compare(request.ids)


@router.get("/traits")
async def get_traits():
    """Get all trait definitions used in comparison."""
    service = get_germplasm_comparison_service()
    return service.get_traits()


@router.get("/markers")
async def get_markers(crop: Optional[str] = Query(None, description="Filter by crop")):
    """Get marker definitions, optionally filtered by crop."""
    service = get_germplasm_comparison_service()
    return service.get_markers(crop=crop)


@router.get("/statistics")
async def get_statistics():
    """Get overall statistics for germplasm comparison."""
    service = get_germplasm_comparison_service()
    return service.get_statistics()

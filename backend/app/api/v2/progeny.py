"""
Progeny API
Manage offspring and descendants of germplasm entries
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.progeny import progeny_service

router = APIRouter(prefix="/progeny", tags=["Progeny"])


@router.get("/parents")
async def list_parents(
    parent_type: Optional[str] = Query(None, description="Filter by parent type: FEMALE, MALE, SELF, POPULATION"),
    species: Optional[str] = Query(None, description="Filter by species"),
    search: Optional[str] = Query(None, description="Search by parent or progeny name"),
):
    """
    List parents with their progeny
    Returns parents sorted by number of offspring
    """
    parents = progeny_service.list_parents(
        parent_type=parent_type,
        species=species,
        search=search,
    )
    return {
        "status": "success",
        "data": parents,
        "count": len(parents),
    }


@router.get("/parents/{parent_id}")
async def get_parent(parent_id: str):
    """Get a single parent with all progeny"""
    parent = progeny_service.get_parent(parent_id)
    if not parent:
        raise HTTPException(status_code=404, detail=f"Parent {parent_id} not found")
    return {"status": "success", "data": parent}


@router.get("/germplasm/{germplasm_id}")
async def get_progeny_by_germplasm(germplasm_id: str):
    """Get progeny for a specific germplasm ID"""
    parent = progeny_service.get_progeny_by_germplasm(germplasm_id)
    if not parent:
        raise HTTPException(status_code=404, detail=f"No progeny data for germplasm {germplasm_id}")
    return {"status": "success", "data": parent}


@router.get("/statistics")
async def get_statistics():
    """Get progeny statistics"""
    stats = progeny_service.get_statistics()
    return {"status": "success", "data": stats}


@router.get("/types")
async def get_parent_types():
    """Get available parent types"""
    types = progeny_service.get_parent_types()
    return {"status": "success", "data": types}


@router.get("/lineage/{germplasm_id}")
async def get_lineage_tree(
    germplasm_id: str,
    depth: int = Query(3, description="Depth of lineage tree"),
):
    """Get lineage tree for a germplasm"""
    tree = progeny_service.get_lineage_tree(germplasm_id, depth)
    if "error" in tree:
        raise HTTPException(status_code=404, detail=tree["error"])
    return {"status": "success", "data": tree}

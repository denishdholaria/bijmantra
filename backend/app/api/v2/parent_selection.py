"""
Parent Selection API
Manage potential parents for crossing and provide recommendations
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.parent_selection import parent_selection_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter(prefix="/parent-selection", tags=["Parent Selection"])


class BreedingObjective(BaseModel):
    trait: str
    weight: float = Field(..., ge=0, le=100)
    direction: str = "maximize"


class SetObjectivesRequest(BaseModel):
    objectives: List[BreedingObjective]


@router.get("/parents")
async def list_parents(
    parent_type: Optional[str] = Query(None, description="Filter by type: elite, donor, landrace"),
    trait: Optional[str] = Query(None, description="Filter by trait"),
    min_gebv: Optional[float] = Query(None, description="Minimum GEBV threshold"),
    search: Optional[str] = Query(None, description="Search by name, pedigree, or traits"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    List available parents for crossing
    Returns parents sorted by GEBV (highest first)
    """
    parents =  await parent_selection_service.list_parents(db, current_user.organization_id, 
        parent_type=parent_type,
        trait=trait,
        min_gebv=min_gebv,
        search=search,
    )
    return {
        "status": "success",
        "data": parents,
        "count": len(parents),
    }


@router.get("/parents/{parent_id}")
async def get_parent(
    parent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get detailed information about a parent"""
    parent =  await parent_selection_service.get_parent(db, current_user.organization_id, parent_id)
    if not parent:
        raise HTTPException(status_code=404, detail=f"Parent {parent_id} not found")
    return {"status": "success", "data": parent}


@router.get("/predict-cross")
async def predict_cross(
    parent1_id: str = Query(..., description="First parent ID"),
    parent2_id: str = Query(..., description="Second parent ID"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Predict cross performance between two parents
    Returns expected GEBV, heterosis, genetic distance, and success probability
    """
    result =  await parent_selection_service.predict_cross(db, current_user.organization_id, parent1_id, parent2_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.get("/recommendations")
async def get_recommendations(
    target_traits: Optional[str] = Query(None, description="Comma-separated target traits"),
    limit: int = Query(5, description="Number of recommendations"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get AI-powered cross recommendations
    Optionally filter by target traits
    """
    traits = target_traits.split(",") if target_traits else None
    recommendations =  await parent_selection_service.get_recommendations(db, current_user.organization_id, 
        target_traits=traits,
        limit=limit,
    )
    return {
        "status": "success",
        "data": recommendations,
        "count": len(recommendations),
    }


@router.get("/objectives")
async def get_breeding_objectives(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get current breeding objectives"""
    objectives = parent_selection_service.get_breeding_objectives()
    return {"status": "success", "data": objectives}


@router.put("/objectives")
async def set_breeding_objectives(
    data: SetObjectivesRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Set breeding objectives with weights"""
    result =  await parent_selection_service.set_breeding_objectives(db, current_user.organization_id, 
        [obj.model_dump() for obj in data.objectives]
    )
    return result


@router.get("/types")
async def get_parent_types(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get available parent types"""
    types = parent_selection_service.get_parent_types()
    return {"status": "success", "data": types}


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get parent selection statistics"""
    stats =  await parent_selection_service.get_statistics(db, current_user.organization_id)
    return {"status": "success", "data": stats}

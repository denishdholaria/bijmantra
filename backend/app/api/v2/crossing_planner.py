"""
Crossing Planner API
Manage planned crosses between germplasm
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from app.services.crossing_planner import crossing_planner_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter(prefix="/crossing-planner", tags=["Crossing Planner"], dependencies=[Depends(get_current_user)])


class CrossCreate(BaseModel):
    femaleParentId: str
    maleParentId: str
    femaleParentName: Optional[str] = None
    maleParentName: Optional[str] = None
    crossName: Optional[str] = None
    objective: Optional[str] = None
    priority: str = "medium"
    targetDate: Optional[str] = None
    expectedProgeny: int = 50
    crossType: str = "single"
    season: Optional[str] = None
    location: Optional[str] = None
    breeder: Optional[str] = None
    notes: Optional[str] = None


class CrossUpdate(BaseModel):
    objective: Optional[str] = None
    priority: Optional[str] = None
    targetDate: Optional[str] = None
    expectedProgeny: Optional[int] = None
    crossType: Optional[str] = None
    season: Optional[str] = None
    location: Optional[str] = None
    breeder: Optional[str] = None
    notes: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str
    actualProgeny: Optional[int] = None


@router.get("")
async def list_crosses(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    season: Optional[str] = None,
    breeder: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List planned crosses with optional filters"""
    result =  await crossing_planner_service.list_crosses(db, current_user.organization_id, 
        status=status,
        priority=priority,
        season=season,
        breeder=breeder,
        page=page,
        page_size=pageSize,
    )
    return {"metadata": {"pagination": result["pagination"]}, "result": {"data": result["data"]}}


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get crossing statistics"""
    stats =  await crossing_planner_service.get_statistics(db, current_user.organization_id)
    return {"metadata": {}, "result": stats}


@router.get("/germplasm")
async def list_germplasm(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List available germplasm for crossing"""
    germplasm =  await crossing_planner_service.list_germplasm(db, current_user.organization_id, search=search)
    return {"metadata": {}, "result": {"data": germplasm}}


@router.get("/{crossId}")
async def get_cross(
    crossId: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single cross by ID"""
    cross =  await crossing_planner_service.get_cross(db, current_user.organization_id, crossId)
    if not cross:
        raise HTTPException(status_code=404, detail="Cross not found")
    return {"metadata": {}, "result": cross}


@router.post("")
async def create_cross(
    data: CrossCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new planned cross"""
    cross =  await crossing_planner_service.create_cross(db, current_user.organization_id, data.model_dump())
    return {"metadata": {}, "result": cross}


@router.put("/{crossId}")
async def update_cross(
    crossId: str, data: CrossUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a cross"""
    cross =  await crossing_planner_service.update_cross(db, current_user.organization_id, crossId, data.model_dump(exclude_none=True))
    if not cross:
        raise HTTPException(status_code=404, detail="Cross not found")
    return {"metadata": {}, "result": cross}


@router.put("/{crossId}/status")
async def update_status(
    crossId: str, data: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update cross status"""
    cross =  await crossing_planner_service.update_status(db, current_user.organization_id, crossId, data.status, data.actualProgeny)
    if not cross:
        raise HTTPException(status_code=404, detail="Cross not found")
    return {"metadata": {}, "result": cross}


@router.delete("/{crossId}")
async def delete_cross(
    crossId: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a cross"""
    success =  await crossing_planner_service.delete_cross(db, current_user.organization_id, crossId)
    if not success:
        raise HTTPException(status_code=404, detail="Cross not found")
    return {"metadata": {}, "result": {"deleted": True}}


@router.get("/reference/statuses")
async def get_statuses():
    """Get available cross statuses"""
    return {
        "metadata": {},
        "result": [
            {"id": "planned", "name": "Planned", "description": "Cross is planned but not yet scheduled"},
            {"id": "scheduled", "name": "Scheduled", "description": "Cross is scheduled for execution"},
            {"id": "in_progress", "name": "In Progress", "description": "Cross is being executed"},
            {"id": "completed", "name": "Completed", "description": "Cross completed successfully"},
            {"id": "failed", "name": "Failed", "description": "Cross failed"},
        ],
    }


@router.get("/reference/priorities")
async def get_priorities():
    """Get available priority levels"""
    return {
        "metadata": {},
        "result": [
            {"id": "high", "name": "High", "color": "red"},
            {"id": "medium", "name": "Medium", "color": "yellow"},
            {"id": "low", "name": "Low", "color": "green"},
        ],
    }


@router.get("/reference/cross-types")
async def get_cross_types():
    """Get available cross types"""
    return {
        "metadata": {},
        "result": [
            {"id": "single", "name": "Single Cross", "description": "A × B"},
            {"id": "three_way", "name": "Three-Way Cross", "description": "(A × B) × C"},
            {"id": "double", "name": "Double Cross", "description": "(A × B) × (C × D)"},
            {"id": "backcross", "name": "Backcross", "description": "F1 × Recurrent Parent"},
            {"id": "wide", "name": "Wide Cross", "description": "Interspecific cross"},
            {"id": "topcross", "name": "Topcross", "description": "Line × Tester"},
        ],
    }

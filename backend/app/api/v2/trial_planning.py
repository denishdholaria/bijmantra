"""
Trial Planning API
Endpoints for trial planning and scheduling
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from ...services.trial_planning import get_trial_planning_service
from app.core.database import get_db
from app.api.deps import get_current_user


router = APIRouter(prefix="/trial-planning", tags=["Trial Planning"])


# Request/Response Models
class TrialCreate(BaseModel):
    name: str
    type: str
    season: str
    year: Optional[int] = None
    locations: List[str]
    entries: int
    reps: int
    design: Optional[str] = "RCBD"
    startDate: str
    endDate: Optional[str] = None
    programId: Optional[str] = None
    programName: Optional[str] = None
    crop: Optional[str] = "Rice"
    objectives: Optional[str] = None
    createdBy: Optional[str] = None


class TrialUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    season: Optional[str] = None
    year: Optional[int] = None
    locations: Optional[List[str]] = None
    entries: Optional[int] = None
    reps: Optional[int] = None
    design: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    objectives: Optional[str] = None


class ResourceCreate(BaseModel):
    resourceType: str
    resourceName: str
    quantity: float
    unit: str
    estimatedCost: Optional[float] = 0
    status: Optional[str] = "planned"


# Trial endpoints
@router.get("")
async def list_trials(
    status: Optional[str] = Query(None, description="Filter by status"),
    type: Optional[str] = Query(None, description="Filter by trial type"),
    season: Optional[str] = Query(None, description="Filter by season"),
    year: Optional[int] = Query(None, description="Filter by year"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
    search: Optional[str] = Query(None, description="Search by name or objectives"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """List all planned trials with optional filters"""
    service = get_trial_planning_service()
    return await service.list_trials(db, current_user.organization_id, status=status,
        trial_type=type,
        season=season,
        year=year,
        crop=crop,
        search=search,)


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get trial planning statistics"""
    service = get_trial_planning_service()
    return await service.get_statistics(db, current_user.organization_id)


@router.get("/timeline")
async def get_timeline(
    year: Optional[int] = Query(None, description="Filter by year"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get trial timeline for visualization"""
    service = get_trial_planning_service()
    return await service.get_timeline(db, current_user.organization_id, year=year)


@router.get("/types")
async def get_trial_types(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of trial types"""
    service = get_trial_planning_service()
    return service.get_trial_types()


@router.get("/seasons")
async def get_seasons(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of seasons"""
    service = get_trial_planning_service()
    return await service.get_seasons(db, current_user.organization_id)


@router.get("/designs")
async def get_designs(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of trial designs"""
    service = get_trial_planning_service()
    return service.get_designs()


@router.post("")
async def create_trial(
    data: TrialCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new planned trial"""
    service = get_trial_planning_service()
    return await service.create_trial(db, current_user.organization_id, data.model_dump())


@router.get("/{trial_id}")
async def get_trial(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get trial by ID"""
    service = get_trial_planning_service()
    trial = await service.get_trial(db, current_user.organization_id, trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return trial


@router.put("/{trial_id}")
async def update_trial(
    trial_id: str, data: TrialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a trial"""
    service = get_trial_planning_service()
    trial = await service.update_trial(db, current_user.organization_id, trial_id, data.model_dump(exclude_none=True))
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return trial


@router.delete("/{trial_id}")
async def delete_trial(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a trial"""
    service = get_trial_planning_service()
    if not await service.delete_trial(db, current_user.organization_id, trial_id):
        raise HTTPException(status_code=404, detail="Trial not found")
    return {"message": "Trial deleted successfully"}


# Status transitions
@router.post("/{trial_id}/approve")
async def approve_trial(
    trial_id: str, approved_by: str = Query(..., description="Name of approver"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve a trial"""
    service = get_trial_planning_service()
    trial = await service.approve_trial(db, current_user.organization_id, trial_id, approved_by)
    if not trial:
        raise HTTPException(status_code=400, detail="Cannot approve trial (invalid status or not found)")
    return trial


@router.post("/{trial_id}/start")
async def start_trial(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Start a trial (move to active)"""
    service = get_trial_planning_service()
    trial = await service.start_trial(db, current_user.organization_id, trial_id)
    if not trial:
        raise HTTPException(status_code=400, detail="Cannot start trial (must be approved first)")
    return trial


@router.post("/{trial_id}/complete")
async def complete_trial(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Complete a trial"""
    service = get_trial_planning_service()
    trial = await service.complete_trial(db, current_user.organization_id, trial_id)
    if not trial:
        raise HTTPException(status_code=400, detail="Cannot complete trial (must be active first)")
    return trial


@router.post("/{trial_id}/cancel")
async def cancel_trial(
    trial_id: str, reason: str = Query(..., description="Cancellation reason"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cancel a trial"""
    service = get_trial_planning_service()
    trial = await service.cancel_trial(db, current_user.organization_id, trial_id, reason)
    if not trial:
        raise HTTPException(status_code=400, detail="Cannot cancel trial (already completed or not found)")
    return trial


# Resource endpoints
@router.get("/{trial_id}/resources")
async def get_resources(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get resources for a trial"""
    service = get_trial_planning_service()
    return await service.get_resources(db, current_user.organization_id, trial_id)


@router.post("/{trial_id}/resources")
async def add_resource(
    trial_id: str, data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a resource to a trial"""
    service = get_trial_planning_service()
    resource = await service.add_resource(db, current_user.organization_id, trial_id, data.model_dump())
    if not resource:
        raise HTTPException(status_code=404, detail="Trial not found")
    return resource

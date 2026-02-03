"""
Breeding Pipeline API

Endpoints for tracking germplasm through breeding stages.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.core import User
from ...services.breeding_pipeline import BreedingPipelineService


router = APIRouter(prefix="/breeding-pipeline", tags=["Breeding Pipeline"])


class CreateEntryRequest(BaseModel):
    """Request to create a new pipeline entry."""
    name: str
    pedigree: str
    crop: str
    current_stage: Optional[str] = "F1"
    program_id: Optional[str] = None
    program_name: Optional[str] = None
    year: Optional[int] = None
    traits: Optional[list[str]] = []
    notes: Optional[str] = ""


class AdvanceStageRequest(BaseModel):
    """Request to advance an entry to the next stage."""
    decision: str  # "Advanced", "Dropped", "Hold"
    notes: Optional[str] = ""


@router.get("/stages")
async def get_stages(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all pipeline stages."""
    service = BreedingPipelineService(db, current_user.organization_id)
    return {"data": service.get_stages()}


@router.get("")
async def list_entries(
    stage: Optional[str] = Query(None, description="Filter by current stage"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
    program_id: Optional[str] = Query(None, description="Filter by program ID"),
    status: Optional[str] = Query(None, description="Filter by status (active, released, dropped)"),
    year: Optional[int] = Query(None, description="Filter by year"),
    search: Optional[str] = Query(None, description="Search by name, pedigree, or ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List pipeline entries with filters."""
    service = BreedingPipelineService(db, current_user.organization_id)
    return await service.list_entries(
        stage=stage,
        crop=crop,
        program_id=program_id,
        status=status,
        year=year,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/statistics")
async def get_statistics(
    program_id: Optional[str] = Query(None, description="Filter by program ID"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pipeline statistics."""
    service = BreedingPipelineService(db, current_user.organization_id)
    result = await service.get_statistics(program_id=program_id, crop=crop)
    return {"data": result}


@router.get("/stage-summary")
async def get_stage_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary of entries at each stage."""
    service = BreedingPipelineService(db, current_user.organization_id)
    result = await service.get_stage_summary()
    return {"data": result}


@router.get("/crops")
async def get_crops(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of unique crops in the pipeline."""
    service = BreedingPipelineService(db, current_user.organization_id)
    result = await service.get_crops()
    return {"data": result}


@router.get("/programs")
async def get_programs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of breeding programs."""
    service = BreedingPipelineService(db, current_user.organization_id)
    result = await service.get_programs()
    return {"data": result}


@router.post("")
async def create_entry(
    request: CreateEntryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new pipeline entry."""
    service = BreedingPipelineService(db, current_user.organization_id)
    entry = await service.create_entry(request.model_dump())
    return {"data": entry, "message": "Entry created successfully"}


@router.get("/{entry_id}")
async def get_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single pipeline entry by ID."""
    service = BreedingPipelineService(db, current_user.organization_id)
    entry = await service.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"data": entry}


@router.post("/{entry_id}/advance")
async def advance_stage(
    entry_id: str,
    request: AdvanceStageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Advance an entry to the next stage or drop it."""
    service = BreedingPipelineService(db, current_user.organization_id)
    entry = await service.advance_stage(entry_id, request.decision, request.notes)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found or cannot be advanced")
    return {"data": entry, "message": f"Entry {request.decision.lower()} successfully"}

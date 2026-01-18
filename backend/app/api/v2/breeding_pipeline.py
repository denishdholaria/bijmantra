"""
Breeding Pipeline API

Endpoints for tracking germplasm through breeding stages.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from ...services.breeding_pipeline import get_breeding_pipeline_service


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
async def get_stages():
    """Get all pipeline stages."""
    service = get_breeding_pipeline_service()
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
):
    """List pipeline entries with filters."""
    service = get_breeding_pipeline_service()
    return service.list_entries(
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
):
    """Get pipeline statistics."""
    service = get_breeding_pipeline_service()
    return {"data": service.get_statistics(program_id=program_id, crop=crop)}


@router.get("/stage-summary")
async def get_stage_summary():
    """Get summary of entries at each stage."""
    service = get_breeding_pipeline_service()
    return {"data": service.get_stage_summary()}


@router.get("/crops")
async def get_crops():
    """Get list of unique crops in the pipeline."""
    service = get_breeding_pipeline_service()
    return {"data": service.get_crops()}


@router.get("/programs")
async def get_programs():
    """Get list of breeding programs."""
    service = get_breeding_pipeline_service()
    return {"data": service.get_programs()}


@router.post("")
async def create_entry(request: CreateEntryRequest):
    """Create a new pipeline entry."""
    service = get_breeding_pipeline_service()
    entry = service.create_entry(request.model_dump())
    return {"data": entry, "message": "Entry created successfully"}


@router.get("/{entry_id}")
async def get_entry(entry_id: str):
    """Get a single pipeline entry by ID."""
    service = get_breeding_pipeline_service()
    entry = service.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"data": entry}


@router.post("/{entry_id}/advance")
async def advance_stage(entry_id: str, request: AdvanceStageRequest):
    """Advance an entry to the next stage or drop it."""
    service = get_breeding_pipeline_service()
    entry = service.advance_stage(entry_id, request.decision, request.notes)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found or cannot be advanced")
    return {"data": entry, "message": f"Entry {request.decision.lower()} successfully"}

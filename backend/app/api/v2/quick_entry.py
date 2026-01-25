"""
Quick Entry API
Endpoints for rapid data entry operations
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.quick_entry import quick_entry_service


router = APIRouter(prefix="/quick-entry", tags=["Quick Entry"])


class GermplasmEntryRequest(BaseModel):
    germplasm_name: str
    accession_number: Optional[str] = None
    species: Optional[str] = None
    country_of_origin: Optional[str] = None
    pedigree: Optional[str] = None
    notes: Optional[str] = None


class ObservationEntryRequest(BaseModel):
    study_id: str
    observation_unit_id: str
    trait: str
    value: float
    unit: Optional[str] = None
    notes: Optional[str] = None


class CrossEntryRequest(BaseModel):
    female_parent: str
    male_parent: str
    cross_date: Optional[str] = None
    seeds_obtained: Optional[int] = None
    notes: Optional[str] = None


class TrialEntryRequest(BaseModel):
    trial_name: str
    program_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


@router.get("/stats")
async def get_session_stats():
    """Get session statistics for quick entry."""
    return quick_entry_service.get_session_stats()


@router.get("/recent")
async def get_recent_activity():
    """Get recent activity summary."""
    activity = quick_entry_service.get_recent_activity()
    return {"activity": activity}


@router.get("/options/{option_type}")
async def get_dropdown_options(option_type: str):
    """Get dropdown options for forms."""
    options = quick_entry_service.get_dropdown_options(option_type)
    return {"options": options, "type": option_type}


@router.get("/entries")
async def get_entries(
    entry_type: Optional[str] = Query(None, description="Filter by entry type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get quick entries."""
    return quick_entry_service.get_entries(
        entry_type=entry_type,
        limit=limit,
        offset=offset,
    )


@router.get("/entries/{entry_id}")
async def get_entry(entry_id: str):
    """Get a single entry."""
    entry = quick_entry_service.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str):
    """Delete an entry."""
    success = quick_entry_service.delete_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True, "message": "Entry deleted"}


@router.post("/germplasm")
async def create_germplasm_entry(request: GermplasmEntryRequest):
    """Create a quick germplasm entry."""
    entry = quick_entry_service.create_entry("germplasm", request.model_dump())
    return entry


@router.post("/observation")
async def create_observation_entry(request: ObservationEntryRequest):
    """Create a quick observation entry."""
    entry = quick_entry_service.create_entry("observation", request.model_dump())
    return entry


@router.post("/cross")
async def create_cross_entry(request: CrossEntryRequest):
    """Create a quick cross entry."""
    entry = quick_entry_service.create_entry("cross", request.model_dump())
    return entry


@router.post("/trial")
async def create_trial_entry(request: TrialEntryRequest):
    """Create a quick trial entry."""
    entry = quick_entry_service.create_entry("trial", request.model_dump())
    return entry

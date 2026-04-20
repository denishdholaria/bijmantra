"""
Quick Entry API
Endpoints for rapid data entry operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.modules.breeding.services.quick_entry_service import quick_entry_service


router = APIRouter(prefix="/quick-entry", tags=["Quick Entry"])


class GermplasmEntryRequest(BaseModel):
    germplasm_name: str
    accession_number: str | None = None
    species: str | None = None
    country_of_origin: str | None = None
    pedigree: str | None = None
    notes: str | None = None


class ObservationEntryRequest(BaseModel):
    study_id: str
    observation_unit_id: str
    trait: str
    value: float
    unit: str | None = None
    notes: str | None = None


class CrossEntryRequest(BaseModel):
    female_parent: str
    male_parent: str
    cross_date: str | None = None
    seeds_obtained: int | None = None
    notes: str | None = None


class TrialEntryRequest(BaseModel):
    trial_name: str
    program_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    notes: str | None = None


@router.get("/stats")
async def get_session_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get session statistics for quick entry."""
    return await quick_entry_service.get_session_stats(db, current_user.organization_id)


@router.get("/recent")
async def get_recent_activity(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get recent activity summary."""
    activity = await quick_entry_service.get_recent_activity(db, current_user.organization_id)
    return {"activity": activity}


@router.get("/options/{option_type}")
async def get_dropdown_options(
    option_type: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get dropdown options for forms."""
    options = await quick_entry_service.get_dropdown_options(
        db, current_user.organization_id, option_type
    )
    return {"options": options, "type": option_type}


@router.get("/entries")
async def get_entries(
    entry_type: str | None = Query(None, description="Filter by entry type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get quick entries."""
    return await quick_entry_service.get_entries(
        db,
        current_user.organization_id,
        entry_type=entry_type,
        limit=limit,
        offset=offset,
    )


@router.get("/entries/{entry_id}")
async def get_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single entry."""
    entry = await quick_entry_service.get_entry(db, current_user.organization_id, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.delete("/entries/{entry_id}")
async def delete_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an entry."""
    success = await quick_entry_service.delete_entry(db, current_user.organization_id, entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True, "message": "Entry deleted"}


@router.post("/germplasm")
async def create_germplasm_entry(
    request: GermplasmEntryRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a quick germplasm entry."""
    entry = await quick_entry_service.create_entry(
        db, current_user.organization_id, "germplasm", request.model_dump()
    )
    return entry


@router.post("/observation")
async def create_observation_entry(
    request: ObservationEntryRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a quick observation entry."""
    entry = await quick_entry_service.create_entry(
        db, current_user.organization_id, "observation", request.model_dump()
    )
    return entry


@router.post("/cross")
async def create_cross_entry(
    request: CrossEntryRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a quick cross entry."""
    entry = await quick_entry_service.create_entry(
        db, current_user.organization_id, "cross", request.model_dump()
    )
    return entry


@router.post("/trial")
async def create_trial_entry(
    request: TrialEntryRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a quick trial entry."""
    entry = await quick_entry_service.create_entry(
        db, current_user.organization_id, "trial", request.model_dump()
    )
    return entry

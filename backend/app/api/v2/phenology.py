"""
Phenology Tracker API
Endpoints for tracking plant growth stages and development
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.modules.phenotyping.services.phenology_service import phenology_service


router = APIRouter(prefix="/phenology", tags=["Phenology Tracker"])


class CreateRecordRequest(BaseModel):
    germplasm_id: str | None = None
    germplasm_name: str
    study_id: str
    plot_id: str
    sowing_date: str
    current_stage: int = 0
    expected_maturity: int = 120
    crop: str = "rice"


class UpdateRecordRequest(BaseModel):
    current_stage: int | None = None
    expected_maturity: int | None = None


class RecordObservationRequest(BaseModel):
    stage: int
    date: str | None = None
    notes: str | None = None


@router.get("/stages")
async def get_growth_stages(
    crop: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get growth stage definitions."""
    stages = phenology_service.get_growth_stages(crop=crop)
    return {"stages": stages}


@router.get("/stats")
async def get_stats(
    study_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get phenology statistics."""
    return await phenology_service.get_stats(db, current_user.organization_id, study_id=study_id)


@router.get("/records")
async def get_records(
    study_id: str | None = Query(None),
    crop: str | None = Query(None),
    min_stage: int | None = Query(None, ge=0, le=90),
    max_stage: int | None = Query(None, ge=0, le=90),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get phenology records with filters."""
    return await phenology_service.get_records(
        db,
        current_user.organization_id,
        study_id=study_id,
        crop=crop,
        min_stage=min_stage,
        max_stage=max_stage,
        limit=limit,
        offset=offset,
    )


@router.get("/records/{record_id}")
async def get_record(
    record_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single phenology record with observations."""
    record = await phenology_service.get_record(db, current_user.organization_id, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.post("/records")
async def create_record(
    request: CreateRecordRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new phenology record."""
    record = await phenology_service.create_record(
        db, current_user.organization_id, request.model_dump()
    )
    return record


@router.patch("/records/{record_id}")
async def update_record(
    record_id: str,
    request: UpdateRecordRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a phenology record."""
    data = {k: v for k, v in request.model_dump().items() if v is not None}
    record = await phenology_service.update_record(
        db, current_user.organization_id, record_id, data
    )
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.post("/records/{record_id}/observations")
async def record_observation(
    record_id: str,
    request: RecordObservationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Record a stage observation."""
    observation = await phenology_service.record_observation(
        db, current_user.organization_id, record_id, request.model_dump()
    )
    if not observation:
        raise HTTPException(status_code=404, detail="Record not found")
    return observation


@router.get("/records/{record_id}/observations")
async def get_observations(
    record_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get all observations for a record."""
    observations = await phenology_service.get_observations(
        db, current_user.organization_id, record_id
    )
    return {"observations": observations, "total": len(observations)}

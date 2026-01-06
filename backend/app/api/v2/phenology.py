"""
Phenology Tracker API
Endpoints for tracking plant growth stages and development
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.phenology import phenology_service


router = APIRouter(prefix="/phenology", tags=["Phenology Tracker"])


class CreateRecordRequest(BaseModel):
    germplasm_id: Optional[str] = None
    germplasm_name: str
    study_id: str
    plot_id: str
    sowing_date: str
    current_stage: int = 0
    expected_maturity: int = 120
    crop: str = "rice"


class UpdateRecordRequest(BaseModel):
    current_stage: Optional[int] = None
    expected_maturity: Optional[int] = None


class RecordObservationRequest(BaseModel):
    stage: int
    date: Optional[str] = None
    notes: Optional[str] = None


@router.get("/stages")
async def get_growth_stages(crop: Optional[str] = Query(None)):
    """Get growth stage definitions."""
    stages = phenology_service.get_growth_stages(crop=crop)
    return {"stages": stages}


@router.get("/stats")
async def get_stats(study_id: Optional[str] = Query(None)):
    """Get phenology statistics."""
    return phenology_service.get_stats(study_id=study_id)


@router.get("/records")
async def get_records(
    study_id: Optional[str] = Query(None),
    crop: Optional[str] = Query(None),
    min_stage: Optional[int] = Query(None, ge=0, le=90),
    max_stage: Optional[int] = Query(None, ge=0, le=90),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get phenology records with filters."""
    return phenology_service.get_records(
        study_id=study_id,
        crop=crop,
        min_stage=min_stage,
        max_stage=max_stage,
        limit=limit,
        offset=offset,
    )


@router.get("/records/{record_id}")
async def get_record(record_id: str):
    """Get a single phenology record with observations."""
    record = phenology_service.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.post("/records")
async def create_record(request: CreateRecordRequest):
    """Create a new phenology record."""
    record = phenology_service.create_record(request.model_dump())
    return record


@router.patch("/records/{record_id}")
async def update_record(record_id: str, request: UpdateRecordRequest):
    """Update a phenology record."""
    data = {k: v for k, v in request.model_dump().items() if v is not None}
    record = phenology_service.update_record(record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.post("/records/{record_id}/observations")
async def record_observation(record_id: str, request: RecordObservationRequest):
    """Record a stage observation."""
    observation = phenology_service.record_observation(record_id, request.model_dump())
    if not observation:
        raise HTTPException(status_code=404, detail="Record not found")
    return observation


@router.get("/records/{record_id}/observations")
async def get_observations(record_id: str):
    """Get all observations for a record."""
    observations = phenology_service.get_observations(record_id)
    return {"observations": observations, "total": len(observations)}

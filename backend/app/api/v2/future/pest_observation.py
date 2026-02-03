"""
Pest Observation API

Endpoints for recording and managing pest scouting observations.

Scientific Framework (preserved per scientific-documentation.md):
    Pest Severity Scale (0-10):
        - 0: No presence
        - 1-3: Low (below economic threshold)
        - 4-6: Moderate (approaching threshold)
        - 7-9: High (above threshold, action needed)
        - 10: Severe (crop loss imminent)
    
    Economic Threshold (ET):
        The pest density at which control measures should be applied
        to prevent economic damage. Varies by:
        - Crop value
        - Pest species
        - Growth stage
        - Market conditions
    
    Incidence vs Severity:
        - Incidence: % of plants/units affected
        - Severity: Intensity of damage on affected units
        - Both needed for accurate assessment
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import pest_observation as pest_crud
from app.schemas.future.crop_protection import (
    PestObservation,
    PestObservationCreate,
)
from app.models.core import User

router = APIRouter(prefix="/pest-observations", tags=["Pest Observations"])


@router.get("/", response_model=List[PestObservation])
async def list_pest_observations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all pest observations for the organization."""
    records, _ = await pest_crud.pest_observation.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )
    return records


@router.get("/{id}", response_model=PestObservation)
async def get_pest_observation(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single pest observation by ID."""
    record = await pest_crud.pest_observation.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Pest observation not found")
    return record


@router.post("/", response_model=PestObservation, status_code=201)
async def create_pest_observation(
    record_in: PestObservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new pest observation record.
    
    Severity Scale (0-10):
        - 0: No presence
        - 1-3: Low (below economic threshold)
        - 4-6: Moderate (approaching threshold)
        - 7-9: High (above threshold)
        - 10: Severe (crop loss imminent)
    """
    record = await pest_crud.pest_observation.create(
        db, obj_in=record_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{id}", status_code=204)
async def delete_pest_observation(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a pest observation record."""
    record = await pest_crud.pest_observation.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Pest observation not found")
    
    await pest_crud.pest_observation.delete(db, id=id)
    await db.commit()
    return None


@router.get("/field/{field_id}", response_model=List[PestObservation])
async def get_field_pest_observations(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all pest observations for a field."""
    records = await pest_crud.pest_observation.get_by_field(
        db, field_id=field_id, org_id=org_id
    )
    return records


@router.get("/severity/{min_severity}", response_model=List[PestObservation])
async def get_high_severity_observations(
    min_severity: int = Path(..., ge=0, le=10),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get pest observations above a severity threshold.
    
    Use this to identify fields requiring immediate attention.
    Recommended thresholds:
        - 4+: Approaching economic threshold
        - 7+: Above threshold, action needed
    """
    records = await pest_crud.pest_observation.get_by_severity(
        db, min_severity=min_severity, org_id=org_id
    )
    return records

"""
Crop Suitability Analysis API

Endpoints for assessing crop suitability based on FAO Land Evaluation Framework.

Scientific Framework (preserved per scientific-documentation.md):
    FAO Land Evaluation Classes:
    - S1 (Highly Suitable): 80-100% - No significant limitations
    - S2 (Moderately Suitable): 60-80% - Moderate limitations
    - S3 (Marginally Suitable): 40-60% - Severe limitations
    - N1 (Currently Not Suitable): 20-40% - Can be improved
    - N2 (Permanently Not Suitable): 0-20% - Cannot be improved

    Suitability factors:
    - Climate: temperature, rainfall, growing season
    - Soil: texture, depth, drainage, pH, fertility
    - Terrain: slope, aspect, elevation
    - Water: availability, quality, irrigation potential
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import crop_suitability as suitability_crud
from app.schemas.future.crop_intelligence import (
    CropSuitability,
    CropSuitabilityCreate,
)
from app.models.core import User

router = APIRouter(prefix="/crop-suitability", tags=["Crop Suitability"])


@router.get("/", response_model=List[CropSuitability])
async def list_crop_suitability(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all crop suitability assessments for the organization."""
    assessments, _ = await suitability_crud.crop_suitability.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )
    return assessments


@router.get("/{id}", response_model=CropSuitability)
async def get_crop_suitability(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single crop suitability assessment by ID."""
    assessment = await suitability_crud.crop_suitability.get(db, id=id)
    if not assessment or assessment.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Crop suitability assessment not found")
    return assessment


@router.post("/", response_model=CropSuitability, status_code=201)
async def create_crop_suitability(
    assessment_in: CropSuitabilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new crop suitability assessment.
    
    FAO Suitability Classes:
    - S1: 80-100% (Highly Suitable)
    - S2: 60-80% (Moderately Suitable)
    - S3: 40-60% (Marginally Suitable)
    - N1: 20-40% (Currently Not Suitable)
    - N2: 0-20% (Permanently Not Suitable)
    """
    assessment = await suitability_crud.crop_suitability.create(
        db, obj_in=assessment_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(assessment)
    return assessment


@router.delete("/{id}", status_code=204)
async def delete_crop_suitability(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a crop suitability assessment."""
    assessment = await suitability_crud.crop_suitability.get(db, id=id)
    if not assessment or assessment.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Crop suitability assessment not found")
    
    await suitability_crud.crop_suitability.delete(db, id=id)
    await db.commit()
    return None


@router.get("/location/{location_id}", response_model=List[CropSuitability])
async def get_suitability_by_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all suitability assessments for a location, ranked by score."""
    assessments = await suitability_crud.crop_suitability.get_by_location(
        db, location_id=location_id, org_id=org_id
    )
    return assessments


@router.get("/crop/{crop_name}", response_model=List[CropSuitability])
async def get_suitability_by_crop(
    crop_name: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all suitability assessments for a specific crop."""
    assessments = await suitability_crud.crop_suitability.get_by_crop(
        db, crop_name=crop_name, org_id=org_id
    )
    return assessments


@router.get("/suitable-locations/{crop_name}", response_model=List[CropSuitability])
async def get_suitable_locations(
    crop_name: str,
    min_score: float = Query(60.0, ge=0, le=100, description="Minimum suitability score"),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Find locations suitable for a crop above a minimum score threshold.
    
    Default threshold (60%) corresponds to S2 (Moderately Suitable) or better.
    """
    assessments = await suitability_crud.crop_suitability.get_suitable_locations(
        db, crop_name=crop_name, min_score=min_score, org_id=org_id
    )
    return assessments

"""
Soil Health Score API

Endpoints for soil health assessment and monitoring.

Scientific Framework (preserved per scientific-documentation.md):
    Soil Health Indicators:
    
    Physical:
    - Aggregate stability: Resistance to erosion
    - Water infiltration: Drainage capacity
    - Bulk density: Compaction indicator
    - Available water capacity: Water storage
    
    Chemical:
    - pH: Nutrient availability
    - CEC: Nutrient holding capacity
    - Base saturation: Ca, Mg, K balance
    - Organic carbon: Long-term fertility
    
    Biological:
    - Microbial biomass: Living soil organisms
    - Respiration rate: Microbial activity
    - Enzyme activity: Nutrient cycling
    - Earthworm count: Soil fauna
    
    Scoring:
    - 0-40: Poor (degraded)
    - 40-60: Fair (needs improvement)
    - 60-80: Good (sustainable)
    - 80-100: Excellent (regenerative)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import soil_health as health_crud
from app.schemas.future.soil_nutrients import (
    SoilHealthScore,
    SoilHealthScoreCreate,
)
from app.models.core import User

router = APIRouter(prefix="/soil-health", tags=["Soil Health"])


@router.get("/", response_model=List[SoilHealthScore])
async def list_soil_health_scores(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all soil health scores for the organization."""
    scores, _ = await health_crud.soil_health.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )
    return scores


@router.get("/{id}", response_model=SoilHealthScore)
async def get_soil_health_score(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single soil health score by ID."""
    score = await health_crud.soil_health.get(db, id=id)
    if not score or score.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Soil health score not found")
    return score


@router.post("/", response_model=SoilHealthScore, status_code=201)
async def create_soil_health_score(
    score_in: SoilHealthScoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new soil health assessment.
    
    Score interpretation:
    - 0-40: Poor (degraded soil)
    - 40-60: Fair (needs improvement)
    - 60-80: Good (sustainable)
    - 80-100: Excellent (regenerative)
    """
    score = await health_crud.soil_health.create(
        db, obj_in=score_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(score)
    return score


@router.delete("/{id}", status_code=204)
async def delete_soil_health_score(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a soil health score."""
    score = await health_crud.soil_health.get(db, id=id)
    if not score or score.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Soil health score not found")
    
    await health_crud.soil_health.delete(db, id=id)
    await db.commit()
    return None


@router.get("/field/{field_id}/trend", response_model=List[SoilHealthScore])
async def get_field_health_trend(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get soil health trend for a field over time."""
    scores = await health_crud.soil_health.get_by_field(
        db, field_id=field_id, org_id=org_id
    )
    return scores


@router.get("/field/{field_id}/latest", response_model=SoilHealthScore)
async def get_latest_health_score(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get the most recent soil health score for a field."""
    score = await health_crud.soil_health.get_latest_by_field(
        db, field_id=field_id, org_id=org_id
    )
    if not score:
        raise HTTPException(status_code=404, detail="No soil health scores found for this field")
    return score

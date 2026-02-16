"""
Fertilizer Recommendation API

Endpoints for generating and managing fertilizer recommendations.

Scientific Framework (preserved per scientific-documentation.md):
    Nutrient Recommendation Methods:
    - Soil test-based: Calibrated to local response curves
    - Yield goal-based: Nutrients removed by target yield
    - Sufficiency approach: Maintain critical levels
    - Build-maintain: Build to optimum, then maintain
    
    Key formulas:
    - N recommendation = (Yield goal × N uptake) - Credits
    - P2O5 = Soil test P × Crop response factor
    - K2O = Soil test K × Crop response factor
    
    Nutrient credits:
    - Previous legume crop: 40-60 kg N/ha
    - Manure application: Based on analysis
    - Irrigation water: Based on nitrate content
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import fertilizer_recommendation as fert_crud
from app.schemas.future.soil_nutrients import (
    FertilizerRecommendation,
    FertilizerRecommendationCreate,
)
from app.models.core import User

router = APIRouter(prefix="/fertilizer-recommendations", tags=["Fertilizer Recommendations"])


@router.get("/", response_model=List[FertilizerRecommendation])
async def list_fertilizer_recommendations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all fertilizer recommendations for the organization."""
    recommendations, _ = await fert_crud.fertilizer_recommendation.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )
    return recommendations


@router.get("/{id}", response_model=FertilizerRecommendation)
async def get_fertilizer_recommendation(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single fertilizer recommendation by ID."""
    recommendation = await fert_crud.fertilizer_recommendation.get(db, id=id)
    if not recommendation or recommendation.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Fertilizer recommendation not found")
    return recommendation


@router.post("/", response_model=FertilizerRecommendation, status_code=201)
async def create_fertilizer_recommendation(
    recommendation_in: FertilizerRecommendationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new fertilizer recommendation.
    
    Recommendation is typically based on:
    - Soil test results
    - Target yield
    - Crop nutrient requirements
    - Previous crop credits
    """
    recommendation = await fert_crud.fertilizer_recommendation.create(
        db, obj_in=recommendation_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(recommendation)
    return recommendation


@router.delete("/{id}", status_code=204)
async def delete_fertilizer_recommendation(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a fertilizer recommendation."""
    recommendation = await fert_crud.fertilizer_recommendation.get(db, id=id)
    if not recommendation or recommendation.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Fertilizer recommendation not found")

    await fert_crud.fertilizer_recommendation.delete(db, id=id)
    await db.commit()
    return None


@router.get("/field/{field_id}", response_model=List[FertilizerRecommendation])
async def get_recommendations_by_field(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all fertilizer recommendations for a field."""
    recommendations = await fert_crud.fertilizer_recommendation.get_by_field(
        db, field_id=field_id, org_id=org_id
    )
    return recommendations


@router.get("/soil-test/{soil_test_id}", response_model=List[FertilizerRecommendation])
async def get_recommendations_by_soil_test(
    soil_test_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get fertilizer recommendations based on a specific soil test."""
    recommendations = await fert_crud.fertilizer_recommendation.get_by_soil_test(
        db, soil_test_id=soil_test_id, org_id=org_id
    )
    return recommendations

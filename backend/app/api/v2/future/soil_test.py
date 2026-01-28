"""
Soil Test API

Endpoints for managing soil test records and analysis.

Scientific Parameters (preserved per scientific-documentation.md):
    Macronutrients:
    - N (Nitrogen): Essential for vegetative growth
    - P (Phosphorus): Root development, flowering
    - K (Potassium): Disease resistance, water regulation
    
    Secondary nutrients:
    - Ca (Calcium), Mg (Magnesium), S (Sulfur)
    
    Micronutrients:
    - Fe, Mn, Zn, Cu, B, Mo, Cl
    
    Soil properties:
    - pH: Optimal range 6.0-7.0 for most crops
    - EC: Electrical conductivity (salinity indicator)
    - CEC: Cation Exchange Capacity (nutrient holding)
    - OM: Organic Matter (soil health indicator)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import soil_test as soil_test_crud
from app.schemas.future.soil_nutrients import (
    SoilTest,
    SoilTestCreate,
    SoilTestUpdate,
    NutrientSufficiency,
    NutrientSufficiencyParams,
)
from app.services import soil_analysis
from app.models.core import User

router = APIRouter(prefix="/soil-tests", tags=["Soil Tests"])


@router.get("/", response_model=List[SoilTest])
async def list_soil_tests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all soil tests for the organization."""
    tests, _ = await soil_test_crud.soil_test.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )
    return tests


@router.get("/{id}", response_model=SoilTest)
async def get_soil_test(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single soil test by ID."""
    test = await soil_test_crud.soil_test.get(db, id=id)
    if not test or test.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Soil test not found")
    return test


@router.post("/", response_model=SoilTest, status_code=201)
async def create_soil_test(
    test_in: SoilTestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new soil test record."""
    test = await soil_test_crud.soil_test.create(
        db, obj_in=test_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(test)
    return test


@router.put("/{id}", response_model=SoilTest)
async def update_soil_test(
    id: int,
    test_in: SoilTestUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Update a soil test record."""
    test = await soil_test_crud.soil_test.get(db, id=id)
    if not test or test.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Soil test not found")
    
    test = await soil_test_crud.soil_test.update(db, db_obj=test, obj_in=test_in)
    await db.commit()
    await db.refresh(test)
    return test


@router.delete("/{id}", status_code=204)
async def delete_soil_test(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a soil test record."""
    test = await soil_test_crud.soil_test.get(db, id=id)
    if not test or test.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Soil test not found")
    
    await soil_test_crud.soil_test.delete(db, id=id)
    await db.commit()
    return None


@router.get("/field/{field_id}/history", response_model=List[SoilTest])
async def get_field_soil_history(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get soil test history for a field, ordered by date."""
    tests = await soil_test_crud.soil_test.get_by_field(
        db, field_id=field_id, org_id=org_id
    )
    return tests


@router.post("/nutrient-sufficiency", response_model=NutrientSufficiency)
async def analyze_nutrient_sufficiency(
    params: NutrientSufficiencyParams,
    db: AsyncSession = Depends(get_db),
    # Note: No direct org_id dependency here, as we check ownership via the soil test
    # This assumes that the service layer will properly handle authorization.
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyzes soil nutrient sufficiency for a given soil test and target crop.
    """
    # Authorization check: Ensure the requested soil_test_id belongs to the user's organization
    soil_test = await soil_test_crud.soil_test.get(db, id=params.soil_test_id)
    if not soil_test or soil_test.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Soil test not found")

    return await soil_analysis.calculate_nutrient_sufficiency(
        db, soil_test_id=params.soil_test_id, target_crop=params.target_crop
    )

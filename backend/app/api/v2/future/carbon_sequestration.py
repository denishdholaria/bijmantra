"""
Carbon Sequestration API

Endpoints for tracking soil carbon and carbon credits.

Scientific Framework (preserved per scientific-documentation.md):
    Carbon Sequestration in Agriculture:
    
    Soil Organic Carbon (SOC):
    - Measured as % of soil mass
    - Typical agricultural soils: 1-5%
    - Target for regenerative: >3%
    
    Carbon stock calculation:
    SOC (t/ha) = SOC% × Bulk Density (g/cm³) × Depth (cm) × 100
    
    Sequestration practices:
    - Cover crops: 0.3-0.5 t C/ha/year
    - No-till: 0.2-0.4 t C/ha/year
    - Compost application: 0.5-1.0 t C/ha/year
    - Agroforestry: 1-5 t C/ha/year
    
    Carbon credits:
    - 1 carbon credit = 1 tonne CO2 equivalent
    - CO2 to C conversion: 1 t C = 3.67 t CO2
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import carbon_sequestration as carbon_crud
from app.schemas.future.soil_nutrients import (
    CarbonSequestration,
    CarbonSequestrationCreate,
)
from app.models.core import User

router = APIRouter(prefix="/carbon-sequestration", tags=["Carbon Sequestration"])


@router.get("/", response_model=List[CarbonSequestration])
async def list_carbon_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all carbon sequestration records for the organization."""
    records, _ = await carbon_crud.carbon_sequestration.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )
    return records


@router.get("/{id}", response_model=CarbonSequestration)
async def get_carbon_record(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single carbon sequestration record by ID."""
    record = await carbon_crud.carbon_sequestration.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Carbon record not found")
    return record


@router.post("/", response_model=CarbonSequestration, status_code=201)
async def create_carbon_record(
    record_in: CarbonSequestrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new carbon sequestration record.
    
    SOC calculation: SOC (t/ha) = SOC% × Bulk Density × Depth × 100
    """
    record = await carbon_crud.carbon_sequestration.create(
        db, obj_in=record_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{id}", status_code=204)
async def delete_carbon_record(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a carbon sequestration record."""
    record = await carbon_crud.carbon_sequestration.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Carbon record not found")

    await carbon_crud.carbon_sequestration.delete(db, id=id)
    await db.commit()
    return None


@router.get("/field/{field_id}", response_model=List[CarbonSequestration])
async def get_field_carbon_history(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get carbon sequestration history for a field."""
    records = await carbon_crud.carbon_sequestration.get_by_field(
        db, field_id=field_id, org_id=org_id
    )
    return records


@router.get("/field/{field_id}/summary")
async def get_field_carbon_summary(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get carbon sequestration summary for a field.
    
    Returns total sequestered carbon, average SOC%, and measurement count.
    """
    summary = await carbon_crud.carbon_sequestration.get_field_summary(
        db, field_id=field_id, org_id=org_id
    )
    return summary


@router.post("/estimate-credits")
async def estimate_carbon_credits(
    carbon_tonnes: float = Query(..., gt=0, description="Carbon sequestered in tonnes"),
    verification_standard: str = Query("verra", description="Verification standard (verra, gold_standard, etc.)")
):
    """
    Estimate carbon credits from sequestered carbon.
    
    1 tonne C = 3.67 tonnes CO2 equivalent
    1 carbon credit = 1 tonne CO2 equivalent
    
    Note: Actual credits depend on verification and permanence requirements.
    """
    co2_equivalent = carbon_tonnes * 3.67

    # Discount factors for different standards (simplified)
    discount_factors = {
        "verra": 0.8,  # 20% buffer pool
        "gold_standard": 0.85,
        "plan_vivo": 0.75,
        "default": 0.7
    }

    discount = discount_factors.get(verification_standard, discount_factors["default"])
    estimated_credits = co2_equivalent * discount

    return {
        "carbon_tonnes": carbon_tonnes,
        "co2_equivalent_tonnes": round(co2_equivalent, 2),
        "verification_standard": verification_standard,
        "buffer_discount": 1 - discount,
        "estimated_credits": round(estimated_credits, 2),
        "note": "Actual credits subject to verification and permanence requirements"
    }

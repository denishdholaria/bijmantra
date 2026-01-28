"""
Spray Application API

Endpoints for recording and managing pesticide/fungicide applications.

Scientific Framework (preserved per scientific-documentation.md):
    Application Rate Calculation:
        Total Product = Rate/ha × Area (ha)
        Spray Volume = Water volume (L/ha) × Area (ha)
    
    Compliance Requirements:
        - PHI: Pre-Harvest Interval (days before harvest)
        - REI: Re-Entry Interval (hours before field re-entry)
        - MRL: Maximum Residue Limits (regulatory compliance)
    
    Application Timing Factors:
        - Weather (wind speed, temperature, humidity)
        - Time of day (avoid heat of day, bee activity)
        - Crop growth stage
        - Pest/disease pressure level
    
    Spray Coverage:
        - Contact products: Thorough coverage essential
        - Systemic products: Less coverage-dependent
        - Adjuvants: Improve spreading and uptake
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import spray_application as spray_crud
from app.schemas.future.crop_protection import (
    SprayApplication,
    SprayApplicationCreate,
    SprayApplicationUpdate,
)
from app.models.core import User

router = APIRouter(prefix="/spray-applications", tags=["Spray Applications"])


@router.get("/", response_model=List[SprayApplication])
async def list_spray_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all spray applications for the organization."""
    records, _ = await spray_crud.spray_application.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )
    return records


@router.get("/compliance-report")
async def get_compliance_report(
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get spray application compliance summary.
    
    Returns total applications, compliant count, and compliance rate.
    Important for audit trails and regulatory compliance.
    """
    report = await spray_crud.spray_application.get_compliance_report(
        db, org_id=org_id
    )
    return report


@router.get("/{id}", response_model=SprayApplication)
async def get_spray_application(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single spray application by ID."""
    record = await spray_crud.spray_application.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Spray application not found")
    return record


@router.post("/", response_model=SprayApplication, status_code=201)
async def create_spray_application(
    record_in: SprayApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Record a new spray application.
    
    Application Rate: Total Product = Rate/ha × Area (ha)
    
    Important: Record PHI and REI for compliance tracking.
    """
    record = await spray_crud.spray_application.create(
        db, obj_in=record_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.put("/{id}", response_model=SprayApplication)
async def update_spray_application(
    id: int,
    record_in: SprayApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a spray application record."""
    record = await spray_crud.spray_application.get(db, id=id)
    if not record or record.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Spray application not found")
    
    record = await spray_crud.spray_application.update(
        db, db_obj=record, obj_in=record_in
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{id}", status_code=204)
async def delete_spray_application(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a spray application record."""
    record = await spray_crud.spray_application.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Spray application not found")
    
    await spray_crud.spray_application.delete(db, id=id)
    await db.commit()
    return None


@router.get("/field/{field_id}", response_model=List[SprayApplication])
async def get_field_spray_applications(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all spray applications for a field."""
    records = await spray_crud.spray_application.get_by_field(
        db, field_id=field_id, org_id=org_id
    )
    return records

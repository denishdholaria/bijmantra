"""
IPM Strategy API

Endpoints for Integrated Pest Management strategy planning and tracking.

Scientific Framework (preserved per scientific-documentation.md):
    IPM Hierarchy (in order of preference):
        1. Prevention (cultural practices, resistant varieties)
        2. Monitoring (scouting, traps, thresholds)
        3. Biological control (natural enemies, biopesticides)
        4. Physical/mechanical control (traps, barriers)
        5. Chemical control (last resort, targeted)
    
    Economic Threshold (ET):
        The pest density at which control costs equal potential crop loss.
        Action should be taken BEFORE reaching ET.
    
    Action Threshold:
        The pest density at which action must be taken to prevent
        reaching the economic injury level.
    
    IPM Principles:
        - Use multiple tactics in combination
        - Minimize environmental impact
        - Preserve natural enemies
        - Rotate modes of action (resistance management)
        - Monitor and adapt based on results
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import ipm_strategy as ipm_crud
from app.schemas.future.crop_protection import (
    IPMStrategy,
    IPMStrategyCreate,
    IPMStrategyUpdate,
)
from app.models.core import User

router = APIRouter(prefix="/ipm-strategies", tags=["IPM Strategies"])


@router.get("/", response_model=List[IPMStrategy])
async def list_ipm_strategies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all IPM strategies for the organization."""
    records, _ = await ipm_crud.ipm_strategy.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )
    return records


@router.get("/{id}", response_model=IPMStrategy)
async def get_ipm_strategy(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single IPM strategy by ID."""
    record = await ipm_crud.ipm_strategy.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="IPM strategy not found")
    return record


@router.post("/", response_model=IPMStrategy, status_code=201)
async def create_ipm_strategy(
    record_in: IPMStrategyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new IPM strategy.
    
    IPM Hierarchy:
        1. Prevention → 2. Monitoring → 3. Biological → 4. Physical → 5. Chemical
    
    Define economic and action thresholds for decision-making.
    """
    record = await ipm_crud.ipm_strategy.create(
        db, obj_in=record_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.put("/{id}", response_model=IPMStrategy)
async def update_ipm_strategy(
    id: int,
    record_in: IPMStrategyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an IPM strategy."""
    record = await ipm_crud.ipm_strategy.get(db, id=id)
    if not record or record.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="IPM strategy not found")
    
    record = await ipm_crud.ipm_strategy.update(
        db, db_obj=record, obj_in=record_in
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{id}", status_code=204)
async def delete_ipm_strategy(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete an IPM strategy."""
    record = await ipm_crud.ipm_strategy.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="IPM strategy not found")
    
    await ipm_crud.ipm_strategy.delete(db, id=id)
    await db.commit()
    return None


@router.get("/crop/{crop_name}", response_model=List[IPMStrategy])
async def get_crop_ipm_strategies(
    crop_name: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all IPM strategies for a specific crop."""
    records = await ipm_crud.ipm_strategy.get_by_crop(
        db, crop_name=crop_name, org_id=org_id
    )
    return records


@router.get("/pest/{pest_name}", response_model=List[IPMStrategy])
async def get_pest_ipm_strategies(
    pest_name: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get all IPM strategies targeting a specific pest.
    
    Results sorted by effectiveness rating (highest first).
    """
    records = await ipm_crud.ipm_strategy.get_by_pest(
        db, pest_name=pest_name, org_id=org_id
    )
    return records


@router.get("/field/{field_id}", response_model=List[IPMStrategy])
async def get_field_ipm_strategies(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all IPM strategies assigned to a field."""
    records = await ipm_crud.ipm_strategy.get_by_field(
        db, field_id=field_id, org_id=org_id
    )
    return records

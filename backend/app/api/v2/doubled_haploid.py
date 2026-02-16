"""
Doubled Haploid API Router
DH production management endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.doubled_haploid import doubled_haploid_service

router = APIRouter(prefix="/doubled-haploid", tags=["Doubled Haploid"])


class EfficiencyRequest(BaseModel):
    protocol_id: str
    donor_plants: int


@router.get("/protocols")
async def get_protocols(
    crop: Optional[str] = Query(None),
    method: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get DH protocols"""
    return await doubled_haploid_service.get_protocols(db, current_user.organization_id, crop, method)


@router.get("/protocols/{protocol_id}")
async def get_protocol(
    protocol_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get single protocol"""
    return await doubled_haploid_service.get_protocol(db, current_user.organization_id, protocol_id)


@router.get("/batches")
async def get_batches(
    protocol_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get DH batches"""
    return await doubled_haploid_service.get_batches(db, current_user.organization_id, protocol_id, status, stage)


@router.get("/batches/{batch_id}")
async def get_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get single batch"""
    return await doubled_haploid_service.get_batch(db, current_user.organization_id, batch_id)


@router.post("/calculate-efficiency")
async def calculate_efficiency(
    request: EfficiencyRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Calculate expected DH production efficiency"""
    return await doubled_haploid_service.calculate_efficiency(
        db, current_user.organization_id,
        request.protocol_id,
        request.donor_plants
    )


@router.get("/workflow/{protocol_id}")
async def get_stage_workflow(
    protocol_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get workflow stages for a protocol"""
    return await doubled_haploid_service.get_stage_workflow(db, current_user.organization_id, protocol_id)


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get DH production statistics"""
    return await doubled_haploid_service.get_statistics(db, current_user.organization_id)

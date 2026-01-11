"""
Doubled Haploid API Router
DH production management endpoints
"""
from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel

from app.services.doubled_haploid import doubled_haploid_service

router = APIRouter(prefix="/doubled-haploid", tags=["Doubled Haploid"])


class EfficiencyRequest(BaseModel):
    protocol_id: str
    donor_plants: int


@router.get("/protocols")
async def get_protocols(
    crop: Optional[str] = Query(None),
    method: Optional[str] = Query(None)
):
    """Get DH protocols"""
    return await doubled_haploid_service.get_protocols(crop, method)


@router.get("/protocols/{protocol_id}")
async def get_protocol(protocol_id: str):
    """Get single protocol"""
    return await doubled_haploid_service.get_protocol(protocol_id)


@router.get("/batches")
async def get_batches(
    protocol_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    stage: Optional[str] = Query(None)
):
    """Get DH batches"""
    return await doubled_haploid_service.get_batches(protocol_id, status, stage)


@router.get("/batches/{batch_id}")
async def get_batch(batch_id: str):
    """Get single batch"""
    return await doubled_haploid_service.get_batch(batch_id)


@router.post("/calculate-efficiency")
async def calculate_efficiency(request: EfficiencyRequest):
    """Calculate expected DH production efficiency"""
    return await doubled_haploid_service.calculate_efficiency(
        request.protocol_id,
        request.donor_plants
    )


@router.get("/workflow/{protocol_id}")
async def get_stage_workflow(protocol_id: str):
    """Get workflow stages for a protocol"""
    return await doubled_haploid_service.get_stage_workflow(protocol_id)


@router.get("/statistics")
async def get_statistics():
    """Get DH production statistics"""
    return await doubled_haploid_service.get_statistics()

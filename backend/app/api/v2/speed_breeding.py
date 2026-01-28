"""
Speed Breeding API Router
Accelerated generation advancement endpoints
"""
from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel

from app.services.speed_breeding import speed_breeding_service

router = APIRouter(prefix="/speed-breeding", tags=["Speed Breeding"])


class TimelineRequest(BaseModel):
    protocol_id: str
    target_generation: str
    start_date: Optional[str] = None


@router.get("/protocols")
async def get_protocols(
    crop: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get speed breeding protocols"""
    return await speed_breeding_service.get_protocols(crop, status)


@router.get("/protocols/{protocol_id}")
async def get_protocol(protocol_id: str):
    """Get single protocol"""
    return await speed_breeding_service.get_protocol(protocol_id)


@router.get("/batches")
async def get_batches(
    protocol_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    chamber: Optional[str] = Query(None)
):
    """Get active batches"""
    return await speed_breeding_service.get_batches(protocol_id, status, chamber)


@router.get("/batches/{batch_id}")
async def get_batch(batch_id: str):
    """Get single batch"""
    return await speed_breeding_service.get_batch(batch_id)


@router.post("/timeline")
async def calculate_timeline(request: TimelineRequest):
    """Calculate breeding timeline"""
    return await speed_breeding_service.calculate_timeline(
        request.protocol_id,
        request.target_generation,
        request.start_date
    )


@router.get("/chambers")
async def get_chamber_status():
    """Get growth chamber status"""
    return await speed_breeding_service.get_chamber_status()


@router.get("/statistics")
async def get_statistics():
    """Get speed breeding statistics"""
    return await speed_breeding_service.get_statistics()

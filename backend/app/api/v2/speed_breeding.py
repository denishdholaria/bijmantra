"""
Speed Breeding API Router
Accelerated generation advancement endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_organization_id
from app.schemas.speed_breeding import (
    SpeedBreedingBatchCreate,
    SpeedBreedingBatchResponse,
    SpeedBreedingChamberResponse,
    SpeedBreedingChamberStats,
    SpeedBreedingProtocolCreate,
    SpeedBreedingProtocolResponse,
    SpeedBreedingStatistics,
    TimelineRequest,
)
from app.services.speed_breeding import speed_breeding_service


from app.api.deps import get_current_user

router = APIRouter(prefix="/speed-breeding", tags=["Speed Breeding"], dependencies=[Depends(get_current_user)])

@router.get("/protocols", response_model=list[SpeedBreedingProtocolResponse])
async def get_protocols(
    crop: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """Get speed breeding protocols"""
    return await speed_breeding_service.get_protocols(db, organization_id, crop, status)

@router.post("/protocols", response_model=SpeedBreedingProtocolResponse)
async def create_protocol_std(
    protocol: SpeedBreedingProtocolCreate,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """Create a new speed breeding protocol (Standard REST)"""
    return await speed_breeding_service.create_protocol(db, organization_id, protocol)

@router.post("/protocol", response_model=SpeedBreedingProtocolResponse)
async def create_protocol(
    protocol: SpeedBreedingProtocolCreate,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """Create a new speed breeding protocol (Task compliant)"""
    return await speed_breeding_service.create_protocol(db, organization_id, protocol)

@router.get("/protocols/{protocol_id}", response_model=SpeedBreedingProtocolResponse)
async def get_protocol(
    protocol_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """Get single protocol"""
    protocol = await speed_breeding_service.get_protocol(db, organization_id, protocol_id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return protocol

@router.get("/batches", response_model=list[SpeedBreedingBatchResponse])
async def get_batches(
    protocol_id: str | None = Query(None),
    status: str | None = Query(None),
    chamber: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """Get active batches"""
    return await speed_breeding_service.get_batches(db, organization_id, protocol_id, status, chamber)

@router.post("/batches", response_model=SpeedBreedingBatchResponse)
async def create_batch(
    batch: SpeedBreedingBatchCreate,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """Create a new batch"""
    return await speed_breeding_service.create_batch(db, organization_id, batch)

@router.get("/batches/{batch_id}", response_model=SpeedBreedingBatchResponse)
async def get_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """Get single batch"""
    batch = await speed_breeding_service.get_batch(db, organization_id, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch

@router.get("/cycles", response_model=list[SpeedBreedingBatchResponse])
async def get_cycles(
    protocol_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """Get growth cycles (alias for batches)"""
    return await speed_breeding_service.get_batches(db, organization_id, protocol_id)

@router.post("/timeline")
async def calculate_timeline(
    request: TimelineRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """Calculate breeding timeline"""
    result = await speed_breeding_service.calculate_timeline(
        db,
        organization_id,
        request.protocol_id,
        request.target_generation,
        request.start_date
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/chambers", response_model=list[SpeedBreedingChamberResponse])
async def get_chamber_status(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """Get growth chamber status"""
    return await speed_breeding_service.get_chamber_status(db, organization_id)

@router.get("/statistics", response_model=SpeedBreedingStatistics)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """Get speed breeding statistics"""
    return await speed_breeding_service.get_statistics(db, organization_id)

@router.get("/stats", response_model=SpeedBreedingChamberStats)
async def get_chamber_statistics(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """Get aggregated chamber usage statistics"""
    return await speed_breeding_service.get_chamber_statistics(db, organization_id)

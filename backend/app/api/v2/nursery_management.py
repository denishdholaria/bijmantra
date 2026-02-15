"""
Nursery Management API
Seedling production and batch management

Migrated to database: December 25, 2025 (Session 17)

Endpoints:
- GET /api/v2/nursery-management/batches - List batches
- GET /api/v2/nursery-management/batches/{id} - Get batch details
- POST /api/v2/nursery-management/batches - Create batch
- PATCH /api/v2/nursery-management/batches/{id}/status - Update status
- PATCH /api/v2/nursery-management/batches/{id}/counts - Update counts
- DELETE /api/v2/nursery-management/batches/{id} - Delete batch
- GET /api/v2/nursery-management/stats - Get statistics
- GET /api/v2/nursery-management/locations - Get locations
- GET /api/v2/nursery-management/germplasm - Get germplasm list
"""

from typing import List, Optional
from datetime import date
from uuid import UUID
import uuid as uuid_module
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.field_operations import SeedlingBatch, NurseryLocation, BatchStatus
from app.models.germplasm import Germplasm
from app.api.deps import get_current_user

router = APIRouter(prefix="/nursery-management", tags=["Nursery Management"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class BatchCreateRequest(BaseModel):
    """Request to create a batch"""
    germplasm: str = Field(..., description="Germplasm name")
    sowingDate: str = Field(..., description="Sowing date (YYYY-MM-DD)")
    expectedTransplant: str = Field(..., description="Expected transplant date")
    quantity: int = Field(..., ge=1, description="Number of seeds/seedlings")
    location: str = Field(..., description="Location name")


class StatusUpdateRequest(BaseModel):
    """Request to update batch status"""
    status: str = Field(..., description="Status: sowing, germinating, growing, ready, transplanted")


class CountsUpdateRequest(BaseModel):
    """Request to update batch counts"""
    germinated: Optional[int] = Field(None, ge=0, description="Number germinated")
    healthy: Optional[int] = Field(None, ge=0, description="Number healthy")


# ============================================
# HELPER FUNCTIONS
# ============================================

def batch_to_dict(batch: SeedlingBatch) -> dict:
    """Convert SeedlingBatch model to API response dict"""
    return {
        "id": batch.batch_code,
        "db_id": str(batch.id),
        "germplasm": batch.germplasm_name,
        "sowingDate": batch.sowing_date.isoformat() if batch.sowing_date else None,
        "expectedTransplant": batch.expected_transplant_date.isoformat() if batch.expected_transplant_date else None,
        "actualTransplant": batch.actual_transplant_date.isoformat() if batch.actual_transplant_date else None,
        "quantity": batch.quantity_sown,
        "germinated": batch.quantity_germinated,
        "healthy": batch.quantity_healthy,
        "transplanted": batch.quantity_transplanted,
        "status": batch.status.value if batch.status else "sowing",
        "location": batch.location.name if batch.location else None,
        "notes": batch.notes,
    }


# ============================================
# ENDPOINTS
# ============================================

@router.get("/batches")
async def list_batches(
    status: Optional[str] = Query(None, description="Filter by status"),
    location: Optional[str] = Query(None, description="Filter by location"),
    db: AsyncSession = Depends(get_db),
):
    """List nursery batches"""
    query = select(SeedlingBatch).options(
        selectinload(SeedlingBatch.location)
    )
    
    if status:
        try:
            status_enum = BatchStatus(status.lower())
            query = query.where(SeedlingBatch.status == status_enum)
        except ValueError:
            pass  # Invalid status, ignore filter
    
    if location:
        # Join with location to filter by name
        query = query.join(NurseryLocation).where(
            NurseryLocation.name.ilike(f"%{location}%")
        )
    
    result = await db.execute(query.order_by(SeedlingBatch.sowing_date.desc()))
    batches = result.scalars().all()
    
    return {
        "success": True,
        "count": len(batches),
        "batches": [batch_to_dict(b) for b in batches],
    }


@router.get("/batches/{batch_id}")
async def get_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get batch details"""
    query = select(SeedlingBatch).options(
        selectinload(SeedlingBatch.location)
    ).where(
        (SeedlingBatch.batch_code == batch_id) |
        (SeedlingBatch.id == batch_id if len(batch_id) == 36 else False)
    )
    
    result = await db.execute(query)
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")
    
    return {
        "success": True,
        **batch_to_dict(batch),
    }


@router.post("/batches")
async def create_batch(
    request: BatchCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new nursery batch"""
    # Generate batch code
    batch_code = f"NB{str(uuid_module.uuid4())[:6].upper()}"
    
    # Find location by name
    location_query = select(NurseryLocation).where(
        NurseryLocation.name.ilike(request.location)
    )
    location_result = await db.execute(location_query)
    location = location_result.scalar_one_or_none()
    
    # Parse dates
    try:
        sowing_date = date.fromisoformat(request.sowingDate)
        expected_date = date.fromisoformat(request.expectedTransplant)
    except ValueError as e:
        raise HTTPException(400, f"Invalid date format: {e}")
    
    batch = SeedlingBatch(
        id=uuid_module.uuid4(),
        batch_code=batch_code,
        germplasm_name=request.germplasm,
        sowing_date=sowing_date,
        expected_transplant_date=expected_date,
        quantity_sown=request.quantity,
        quantity_germinated=0,
        quantity_healthy=0,
        status=BatchStatus.SOWING,
        location_id=location.id if location else None,
        # Note: organization_id should be set from current user context
    )
    
    db.add(batch)
    await db.commit()
    await db.refresh(batch)
    
    return {
        "success": True,
        "message": f"Batch {batch_code} created",
        **batch_to_dict(batch),
    }


@router.patch("/batches/{batch_id}/status")
async def update_batch_status(
    batch_id: str,
    request: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update batch status"""
    query = select(SeedlingBatch).where(
        (SeedlingBatch.batch_code == batch_id) |
        (SeedlingBatch.id == batch_id if len(batch_id) == 36 else False)
    )
    
    result = await db.execute(query)
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")
    
    valid_statuses = ["sowing", "germinating", "growing", "ready", "transplanted", "failed"]
    if request.status.lower() not in valid_statuses:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid_statuses}")
    
    batch.status = BatchStatus(request.status.lower())
    
    # If transplanted, set actual transplant date
    if request.status.lower() == "transplanted" and not batch.actual_transplant_date:
        batch.actual_transplant_date = date.today()
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Status updated to {request.status}",
    }


@router.patch("/batches/{batch_id}/counts")
async def update_batch_counts(
    batch_id: str,
    request: CountsUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update batch germination/healthy counts"""
    query = select(SeedlingBatch).where(
        (SeedlingBatch.batch_code == batch_id) |
        (SeedlingBatch.id == batch_id if len(batch_id) == 36 else False)
    )
    
    result = await db.execute(query)
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")
    
    if request.germinated is not None:
        batch.quantity_germinated = request.germinated
    if request.healthy is not None:
        batch.quantity_healthy = request.healthy
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Counts updated",
    }


@router.delete("/batches/{batch_id}")
async def delete_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a batch"""
    query = select(SeedlingBatch).where(
        (SeedlingBatch.batch_code == batch_id) |
        (SeedlingBatch.id == batch_id if len(batch_id) == 36 else False)
    )
    
    result = await db.execute(query)
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")
    
    await db.delete(batch)
    await db.commit()
    
    return {
        "success": True,
        "message": f"Batch {batch_id} deleted",
    }


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get nursery statistics"""
    # Total batches
    total_count = await db.execute(select(func.count(SeedlingBatch.id)))
    total = total_count.scalar() or 0
    
    # Sowing count
    sowing_count = await db.execute(
        select(func.count(SeedlingBatch.id)).where(
            SeedlingBatch.status == BatchStatus.SOWING
        )
    )
    sowing = sowing_count.scalar() or 0
    
    # Growing count (germinating + growing)
    growing_count = await db.execute(
        select(func.count(SeedlingBatch.id)).where(
            SeedlingBatch.status.in_([BatchStatus.GERMINATING, BatchStatus.GROWING])
        )
    )
    growing = growing_count.scalar() or 0
    
    # Ready count
    ready_count = await db.execute(
        select(func.count(SeedlingBatch.id)).where(
            SeedlingBatch.status == BatchStatus.READY
        )
    )
    ready = ready_count.scalar() or 0
    
    # Total healthy seedlings
    seedlings_sum = await db.execute(
        select(func.sum(SeedlingBatch.quantity_healthy))
    )
    total_seedlings = seedlings_sum.scalar() or 0
    
    return {
        "success": True,
        "total": total,
        "sowing": sowing,
        "growing": growing,
        "ready": ready,
        "totalSeedlings": total_seedlings,
    }


@router.get("/locations")
async def get_locations(db: AsyncSession = Depends(get_db)):
    """Get available locations"""
    query = select(NurseryLocation).where(NurseryLocation.is_active == True)
    
    result = await db.execute(query.order_by(NurseryLocation.name))
    locations = result.scalars().all()
    
    return {
        "success": True,
        "locations": [loc.name for loc in locations],
    }


@router.get("/germplasm")
async def get_germplasm_list(db: AsyncSession = Depends(get_db)):
    """Get available germplasm"""
    query = select(Germplasm.id, Germplasm.germplasm_name).limit(100)
    
    result = await db.execute(query)
    germplasm = result.all()
    
    return {
        "success": True,
        "germplasm": [
            {"id": str(g[0]), "name": g[1]}
            for g in germplasm
        ],
    }


@router.get("/export")
async def export_batches(
    format: str = Query("csv", description="Export format: csv or json"),
    db: AsyncSession = Depends(get_db),
):
    """Export batches"""
    query = select(SeedlingBatch).options(
        selectinload(SeedlingBatch.location)
    )
    
    result = await db.execute(query.order_by(SeedlingBatch.sowing_date.desc()))
    batches = result.scalars().all()
    
    batch_dicts = [batch_to_dict(b) for b in batches]
    
    if format == "json":
        return {
            "success": True,
            "data": batch_dicts,
        }
    
    # CSV format
    headers = ["id", "germplasm", "sowingDate", "expectedTransplant", "quantity", "germinated", "healthy", "status", "location"]
    lines = [",".join(headers)]
    for b in batch_dicts:
        lines.append(",".join(str(b.get(h, "")) for h in headers))
    
    return {
        "success": True,
        "csv": "\n".join(lines),
    }

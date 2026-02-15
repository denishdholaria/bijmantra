"""
Warehouse Management API
Storage locations, capacity tracking, and environmental monitoring

Endpoints:
- GET /warehouse/locations - List all storage locations
- GET /warehouse/locations/{id} - Get location details
- POST /warehouse/locations - Create storage location
- PATCH /warehouse/locations/{id} - Update location
- DELETE /warehouse/locations/{id} - Delete location
- GET /warehouse/summary - Get warehouse summary stats
- GET /warehouse/alerts - Get capacity/environment alerts

Refactored: Session 94 — migrated from in-memory demo data to real DB queries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.warehouse import StorageLocation

from app.api.deps import get_current_user

router = APIRouter(prefix="/warehouse", tags=["Warehouse Management"], dependencies=[Depends(get_current_user)])


# ============================================================================
# Schemas
# ============================================================================

class StorageLocationCreate(BaseModel):
    name: str = Field(..., description="Location name")
    code: str = Field(..., description="Location code (e.g., WH-A)")
    storage_type: str = Field("ambient", description="Storage type: cold, ambient, controlled, cryo")
    capacity_kg: float = Field(..., gt=0, description="Total capacity in kg")
    target_temperature: Optional[float] = Field(None, description="Target temperature °C")
    target_humidity: Optional[float] = Field(None, description="Target humidity %")
    description: Optional[str] = Field(None, description="Description")


class StorageLocationUpdate(BaseModel):
    name: Optional[str] = None
    storage_type: Optional[str] = None
    capacity_kg: Optional[float] = None
    used_kg: Optional[float] = None
    current_temperature: Optional[float] = None
    current_humidity: Optional[float] = None
    target_temperature: Optional[float] = None
    target_humidity: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None


class StorageLocationResponse(BaseModel):
    id: int
    code: str
    name: str
    storage_type: str
    capacity_kg: float
    used_kg: float
    current_temperature: Optional[float]
    current_humidity: Optional[float]
    target_temperature: Optional[float]
    target_humidity: Optional[float]
    lot_count: int
    status: str
    utilization_percent: float
    created_at: str
    updated_at: str


class WarehouseSummary(BaseModel):
    total_locations: int
    total_capacity_kg: float
    total_used_kg: float
    utilization_percent: float
    total_lots: int
    locations_by_type: dict
    alerts_count: int


class WarehouseAlert(BaseModel):
    id: str
    location_id: int
    location_name: str
    alert_type: str
    severity: str
    message: str
    current_value: float
    threshold_value: float
    created_at: str


# ============================================================================
# Helpers
# ============================================================================

def _utilization(used: float, capacity: float) -> float:
    if capacity <= 0:
        return 0
    return round((used / capacity) * 100, 1)


def _to_response(loc: StorageLocation) -> dict:
    return {
        "id": loc.id,
        "code": loc.code,
        "name": loc.name,
        "storage_type": loc.storage_type,
        "capacity_kg": loc.capacity_kg,
        "used_kg": loc.used_kg,
        "current_temperature": loc.current_temperature,
        "current_humidity": loc.current_humidity,
        "target_temperature": loc.target_temperature,
        "target_humidity": loc.target_humidity,
        "lot_count": loc.lot_count,
        "status": loc.status,
        "utilization_percent": _utilization(loc.used_kg, loc.capacity_kg),
        "created_at": loc.created_at.isoformat() if loc.created_at else "",
        "updated_at": loc.updated_at.isoformat() if loc.updated_at else "",
    }


def _determine_status(loc: StorageLocation) -> str:
    utilization = _utilization(loc.used_kg, loc.capacity_kg)
    if utilization >= 95:
        return "critical"
    if utilization >= 80:
        return "warning"
    if loc.target_temperature is not None and loc.current_temperature is not None:
        if abs(loc.current_temperature - loc.target_temperature) > 5:
            return "critical"
        if abs(loc.current_temperature - loc.target_temperature) > 2:
            return "warning"
    if loc.target_humidity is not None and loc.current_humidity is not None:
        if abs(loc.current_humidity - loc.target_humidity) > 15:
            return "critical"
        if abs(loc.current_humidity - loc.target_humidity) > 10:
            return "warning"
    return "normal"


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/locations")
async def list_locations(
    storage_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """List all storage locations with optional filters"""
    query = select(StorageLocation).where(StorageLocation.organization_id == organization_id)
    if storage_type:
        query = query.where(StorageLocation.storage_type == storage_type)
    if status:
        query = query.where(StorageLocation.status == status)
    query = query.order_by(StorageLocation.code)

    result = await db.execute(query)
    locations = result.scalars().all()
    return [_to_response(loc) for loc in locations]


@router.get("/locations/{location_id}")
async def get_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get a specific storage location"""
    result = await db.execute(
        select(StorageLocation).where(
            StorageLocation.id == location_id,
            StorageLocation.organization_id == organization_id,
        )
    )
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return _to_response(loc)


@router.post("/locations", response_model=StorageLocationResponse)
async def create_location(
    request: StorageLocationCreate,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Create a new storage location"""
    existing = await db.execute(
        select(StorageLocation).where(
            StorageLocation.code == request.code,
            StorageLocation.organization_id == organization_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Location code already exists")

    loc = StorageLocation(
        organization_id=organization_id,
        code=request.code,
        name=request.name,
        storage_type=request.storage_type,
        capacity_kg=request.capacity_kg,
        used_kg=0,
        current_temperature=request.target_temperature,
        current_humidity=request.target_humidity,
        target_temperature=request.target_temperature,
        target_humidity=request.target_humidity,
        lot_count=0,
        status="normal",
        description=request.description,
    )
    db.add(loc)
    await db.commit()
    await db.refresh(loc)
    return _to_response(loc)


@router.patch("/locations/{location_id}", response_model=StorageLocationResponse)
async def update_location(
    location_id: int,
    request: StorageLocationUpdate,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Update a storage location"""
    result = await db.execute(
        select(StorageLocation).where(
            StorageLocation.id == location_id,
            StorageLocation.organization_id == organization_id,
        )
    )
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(loc, key, value)

    loc.status = _determine_status(loc)
    await db.commit()
    await db.refresh(loc)
    return _to_response(loc)


@router.delete("/locations/{location_id}")
async def delete_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Delete a storage location"""
    result = await db.execute(
        select(StorageLocation).where(
            StorageLocation.id == location_id,
            StorageLocation.organization_id == organization_id,
        )
    )
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    if loc.lot_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete location with stored lots. Move lots first.")

    await db.delete(loc)
    await db.commit()
    return {"message": "Location deleted", "id": location_id}


@router.get("/summary", response_model=WarehouseSummary)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get warehouse summary statistics"""
    result = await db.execute(
        select(StorageLocation).where(StorageLocation.organization_id == organization_id)
    )
    locations = result.scalars().all()

    if not locations:
        return WarehouseSummary(
            total_locations=0, total_capacity_kg=0, total_used_kg=0,
            utilization_percent=0, total_lots=0, locations_by_type={}, alerts_count=0,
        )

    total_capacity = sum(l.capacity_kg for l in locations)
    total_used = sum(l.used_kg for l in locations)
    total_lots = sum(l.lot_count for l in locations)

    by_type: dict = {}
    for loc in locations:
        t = loc.storage_type
        if t not in by_type:
            by_type[t] = {"count": 0, "capacity_kg": 0, "used_kg": 0}
        by_type[t]["count"] += 1
        by_type[t]["capacity_kg"] += loc.capacity_kg
        by_type[t]["used_kg"] += loc.used_kg

    alerts_count = sum(1 for l in locations if l.status in ("warning", "critical"))

    return WarehouseSummary(
        total_locations=len(locations),
        total_capacity_kg=total_capacity,
        total_used_kg=total_used,
        utilization_percent=_utilization(total_used, total_capacity),
        total_lots=total_lots,
        locations_by_type=by_type,
        alerts_count=alerts_count,
    )


@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get warehouse alerts for capacity and environmental conditions"""
    result = await db.execute(
        select(StorageLocation).where(StorageLocation.organization_id == organization_id)
    )
    locations = result.scalars().all()

    alerts: List[WarehouseAlert] = []
    now = datetime.now(timezone.utc).isoformat() + "Z"

    for loc in locations:
        utilization = _utilization(loc.used_kg, loc.capacity_kg)

        if utilization >= 95:
            alerts.append(WarehouseAlert(
                id=f"alert-cap-{loc.id}", location_id=loc.id, location_name=loc.name,
                alert_type="capacity", severity="critical",
                message=f"Storage capacity critical at {utilization}%",
                current_value=utilization, threshold_value=95, created_at=now,
            ))
        elif utilization >= 80:
            alerts.append(WarehouseAlert(
                id=f"alert-cap-{loc.id}", location_id=loc.id, location_name=loc.name,
                alert_type="capacity", severity="warning",
                message=f"Storage capacity high at {utilization}%",
                current_value=utilization, threshold_value=80, created_at=now,
            ))

        if loc.target_temperature is not None and loc.current_temperature is not None:
            temp_diff = abs(loc.current_temperature - loc.target_temperature)
            if temp_diff > 5:
                alerts.append(WarehouseAlert(
                    id=f"alert-temp-{loc.id}", location_id=loc.id, location_name=loc.name,
                    alert_type="temperature", severity="critical",
                    message=f"Temperature deviation: {loc.current_temperature}°C (target: {loc.target_temperature}°C)",
                    current_value=loc.current_temperature, threshold_value=loc.target_temperature, created_at=now,
                ))
            elif temp_diff > 2:
                alerts.append(WarehouseAlert(
                    id=f"alert-temp-{loc.id}", location_id=loc.id, location_name=loc.name,
                    alert_type="temperature", severity="warning",
                    message=f"Temperature deviation: {loc.current_temperature}°C (target: {loc.target_temperature}°C)",
                    current_value=loc.current_temperature, threshold_value=loc.target_temperature, created_at=now,
                ))

    if severity:
        alerts = [a for a in alerts if a.severity == severity]

    return alerts

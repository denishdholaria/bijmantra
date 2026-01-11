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
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum
import uuid

from app.core.database import get_db

router = APIRouter(prefix="/warehouse", tags=["Warehouse Management"])


# ============================================================================
# Enums and Models
# ============================================================================

class StorageType(str, Enum):
    COLD = "cold"
    AMBIENT = "ambient"
    CONTROLLED = "controlled"
    CRYO = "cryo"


class LocationStatus(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"


class StorageLocationCreate(BaseModel):
    name: str = Field(..., description="Location name")
    code: str = Field(..., description="Location code (e.g., WH-A)")
    storage_type: StorageType = Field(StorageType.AMBIENT, description="Storage type")
    capacity_kg: float = Field(..., gt=0, description="Total capacity in kg")
    target_temperature: Optional[float] = Field(None, description="Target temperature °C")
    target_humidity: Optional[float] = Field(None, description="Target humidity %")
    description: Optional[str] = Field(None, description="Description")


class StorageLocationUpdate(BaseModel):
    name: Optional[str] = None
    storage_type: Optional[StorageType] = None
    capacity_kg: Optional[float] = None
    used_kg: Optional[float] = None
    current_temperature: Optional[float] = None
    current_humidity: Optional[float] = None
    target_temperature: Optional[float] = None
    target_humidity: Optional[float] = None
    status: Optional[LocationStatus] = None
    description: Optional[str] = None


class StorageLocationResponse(BaseModel):
    id: str
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
    location_id: str
    location_name: str
    alert_type: str  # capacity, temperature, humidity
    severity: str  # warning, critical
    message: str
    current_value: float
    threshold_value: float
    created_at: str


# ============================================================================
# In-memory storage (will be migrated to DB in future)
# For now, using database-like structure that can be easily migrated
# ============================================================================

# Storage locations - initialized with demo data for development
_locations: dict = {}
_initialized = False


def _init_demo_data():
    """Initialize demo warehouse data"""
    global _locations, _initialized
    if _initialized:
        return
    
    _locations = {
        "WH-A": {
            "id": "WH-A",
            "code": "WH-A",
            "name": "Warehouse A - Cold Storage",
            "storage_type": "cold",
            "capacity_kg": 50000,
            "used_kg": 35000,
            "current_temperature": -5,
            "current_humidity": 45,
            "target_temperature": -5,
            "target_humidity": 45,
            "lot_count": 45,
            "status": "normal",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": datetime.now(timezone.utc).isoformat() + "Z",
        },
        "WH-B": {
            "id": "WH-B",
            "code": "WH-B",
            "name": "Warehouse B - Ambient",
            "storage_type": "ambient",
            "capacity_kg": 100000,
            "used_kg": 82000,
            "current_temperature": 25,
            "current_humidity": 55,
            "target_temperature": 25,
            "target_humidity": 50,
            "lot_count": 120,
            "status": "warning",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": datetime.now(timezone.utc).isoformat() + "Z",
        },
        "WH-C": {
            "id": "WH-C",
            "code": "WH-C",
            "name": "Warehouse C - Controlled",
            "storage_type": "controlled",
            "capacity_kg": 30000,
            "used_kg": 12000,
            "current_temperature": 15,
            "current_humidity": 40,
            "target_temperature": 15,
            "target_humidity": 40,
            "lot_count": 28,
            "status": "normal",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": datetime.now(timezone.utc).isoformat() + "Z",
        },
        "WH-D": {
            "id": "WH-D",
            "code": "WH-D",
            "name": "Warehouse D - Long-term",
            "storage_type": "cold",
            "capacity_kg": 20000,
            "used_kg": 19500,
            "current_temperature": -18,
            "current_humidity": 30,
            "target_temperature": -18,
            "target_humidity": 30,
            "lot_count": 85,
            "status": "critical",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": datetime.now(timezone.utc).isoformat() + "Z",
        },
    }
    _initialized = True


def _calculate_utilization(used: float, capacity: float) -> float:
    """Calculate utilization percentage"""
    if capacity <= 0:
        return 0
    return round((used / capacity) * 100, 1)


def _determine_status(location: dict) -> str:
    """Determine location status based on conditions"""
    utilization = _calculate_utilization(location["used_kg"], location["capacity_kg"])
    
    # Check capacity
    if utilization >= 95:
        return "critical"
    if utilization >= 80:
        return "warning"
    
    # Check temperature deviation
    if location.get("target_temperature") is not None and location.get("current_temperature") is not None:
        temp_diff = abs(location["current_temperature"] - location["target_temperature"])
        if temp_diff > 5:
            return "critical"
        if temp_diff > 2:
            return "warning"
    
    # Check humidity deviation
    if location.get("target_humidity") is not None and location.get("current_humidity") is not None:
        humidity_diff = abs(location["current_humidity"] - location["target_humidity"])
        if humidity_diff > 15:
            return "critical"
        if humidity_diff > 10:
            return "warning"
    
    return "normal"


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/locations", response_model=List[StorageLocationResponse])
async def list_locations(
    storage_type: Optional[StorageType] = None,
    status: Optional[LocationStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all storage locations with optional filters"""
    _init_demo_data()
    
    locations = list(_locations.values())
    
    # Apply filters
    if storage_type:
        locations = [l for l in locations if l["storage_type"] == storage_type.value]
    if status:
        locations = [l for l in locations if l["status"] == status.value]
    
    # Add calculated fields
    result = []
    for loc in locations:
        result.append({
            **loc,
            "utilization_percent": _calculate_utilization(loc["used_kg"], loc["capacity_kg"]),
        })
    
    return result


@router.get("/locations/{location_id}", response_model=StorageLocationResponse)
async def get_location(location_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific storage location"""
    _init_demo_data()
    
    if location_id not in _locations:
        raise HTTPException(status_code=404, detail="Location not found")
    
    loc = _locations[location_id]
    return {
        **loc,
        "utilization_percent": _calculate_utilization(loc["used_kg"], loc["capacity_kg"]),
    }


@router.post("/locations", response_model=StorageLocationResponse)
async def create_location(
    request: StorageLocationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new storage location"""
    _init_demo_data()
    
    if request.code in _locations:
        raise HTTPException(status_code=400, detail="Location code already exists")
    
    now = datetime.now(timezone.utc).isoformat() + "Z"
    location = {
        "id": request.code,
        "code": request.code,
        "name": request.name,
        "storage_type": request.storage_type.value,
        "capacity_kg": request.capacity_kg,
        "used_kg": 0,
        "current_temperature": request.target_temperature,
        "current_humidity": request.target_humidity,
        "target_temperature": request.target_temperature,
        "target_humidity": request.target_humidity,
        "lot_count": 0,
        "status": "normal",
        "created_at": now,
        "updated_at": now,
    }
    
    _locations[request.code] = location
    
    return {
        **location,
        "utilization_percent": 0,
    }


@router.patch("/locations/{location_id}", response_model=StorageLocationResponse)
async def update_location(
    location_id: str,
    request: StorageLocationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a storage location"""
    _init_demo_data()
    
    if location_id not in _locations:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location = _locations[location_id]
    
    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            if isinstance(value, Enum):
                location[key] = value.value
            else:
                location[key] = value
    
    location["updated_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    
    # Recalculate status
    location["status"] = _determine_status(location)
    
    return {
        **location,
        "utilization_percent": _calculate_utilization(location["used_kg"], location["capacity_kg"]),
    }


@router.delete("/locations/{location_id}")
async def delete_location(location_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a storage location"""
    _init_demo_data()
    
    if location_id not in _locations:
        raise HTTPException(status_code=404, detail="Location not found")
    
    if _locations[location_id]["lot_count"] > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete location with stored lots. Move lots first."
        )
    
    del _locations[location_id]
    return {"message": "Location deleted", "id": location_id}


@router.get("/summary", response_model=WarehouseSummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    """Get warehouse summary statistics"""
    _init_demo_data()
    
    locations = list(_locations.values())
    
    total_capacity = sum(l["capacity_kg"] for l in locations)
    total_used = sum(l["used_kg"] for l in locations)
    total_lots = sum(l["lot_count"] for l in locations)
    
    # Count by type
    by_type = {}
    for loc in locations:
        t = loc["storage_type"]
        if t not in by_type:
            by_type[t] = {"count": 0, "capacity_kg": 0, "used_kg": 0}
        by_type[t]["count"] += 1
        by_type[t]["capacity_kg"] += loc["capacity_kg"]
        by_type[t]["used_kg"] += loc["used_kg"]
    
    # Count alerts
    alerts_count = sum(1 for l in locations if l["status"] in ["warning", "critical"])
    
    return WarehouseSummary(
        total_locations=len(locations),
        total_capacity_kg=total_capacity,
        total_used_kg=total_used,
        utilization_percent=_calculate_utilization(total_used, total_capacity),
        total_lots=total_lots,
        locations_by_type=by_type,
        alerts_count=alerts_count,
    )


@router.get("/alerts", response_model=List[WarehouseAlert])
async def get_alerts(
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get warehouse alerts for capacity and environmental conditions"""
    _init_demo_data()
    
    alerts = []
    now = datetime.now(timezone.utc).isoformat() + "Z"
    
    for loc in _locations.values():
        utilization = _calculate_utilization(loc["used_kg"], loc["capacity_kg"])
        
        # Capacity alerts
        if utilization >= 95:
            alerts.append(WarehouseAlert(
                id=f"alert-cap-{loc['id']}",
                location_id=loc["id"],
                location_name=loc["name"],
                alert_type="capacity",
                severity="critical",
                message=f"Storage capacity critical at {utilization}%",
                current_value=utilization,
                threshold_value=95,
                created_at=now,
            ))
        elif utilization >= 80:
            alerts.append(WarehouseAlert(
                id=f"alert-cap-{loc['id']}",
                location_id=loc["id"],
                location_name=loc["name"],
                alert_type="capacity",
                severity="warning",
                message=f"Storage capacity high at {utilization}%",
                current_value=utilization,
                threshold_value=80,
                created_at=now,
            ))
        
        # Temperature alerts
        if loc.get("target_temperature") is not None and loc.get("current_temperature") is not None:
            temp_diff = abs(loc["current_temperature"] - loc["target_temperature"])
            if temp_diff > 5:
                alerts.append(WarehouseAlert(
                    id=f"alert-temp-{loc['id']}",
                    location_id=loc["id"],
                    location_name=loc["name"],
                    alert_type="temperature",
                    severity="critical",
                    message=f"Temperature deviation: {loc['current_temperature']}°C (target: {loc['target_temperature']}°C)",
                    current_value=loc["current_temperature"],
                    threshold_value=loc["target_temperature"],
                    created_at=now,
                ))
            elif temp_diff > 2:
                alerts.append(WarehouseAlert(
                    id=f"alert-temp-{loc['id']}",
                    location_id=loc["id"],
                    location_name=loc["name"],
                    alert_type="temperature",
                    severity="warning",
                    message=f"Temperature deviation: {loc['current_temperature']}°C (target: {loc['target_temperature']}°C)",
                    current_value=loc["current_temperature"],
                    threshold_value=loc["target_temperature"],
                    created_at=now,
                ))
    
    # Filter by severity if specified
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    
    return alerts

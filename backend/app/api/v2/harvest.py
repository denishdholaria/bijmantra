"""
Harvest Management API
Track harvest operations, post-harvest handling, and storage
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.harvest_management import harvest_management_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/harvest", tags=["Harvest Management"], dependencies=[Depends(get_current_user)])


class HarvestPlan(BaseModel):
    trial_id: str
    plot_id: str
    crop: str
    variety: str
    planned_date: str
    area_ha: float
    expected_yield_kg: Optional[float] = None
    operator: Optional[str] = None
    notes: Optional[str] = None


class HarvestRecord(BaseModel):
    harvest_date: str
    yield_kg: float
    moisture_percent: float
    operator: Optional[str] = None
    notes: Optional[str] = None


class QualityCheck(BaseModel):
    check_type: str
    value: float
    unit: str
    passed: bool
    notes: Optional[str] = None


class StorageUnitCreate(BaseModel):
    name: str
    storage_type: str
    capacity_kg: float
    location: str
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = None


class StoreHarvest(BaseModel):
    harvest_id: str
    quantity_kg: float
    notes: Optional[str] = None


class WithdrawStorage(BaseModel):
    quantity_kg: float
    purpose: str
    destination: Optional[str] = None
    notes: Optional[str] = None


class DryWeightCalc(BaseModel):
    wet_weight_kg: float
    moisture_percent: float
    target_moisture: float = 14.0


# Harvest endpoints
@router.post("/harvests")
async def plan_harvest(data: HarvestPlan):
    """Plan a harvest operation"""
    harvest = harvest_management_service.plan_harvest(**data.model_dump())
    return {"status": "success", "data": harvest}


@router.put("/harvests/{harvest_id}/record")
async def record_harvest(harvest_id: str, data: HarvestRecord):
    """Record actual harvest data"""
    try:
        harvest = harvest_management_service.record_harvest(
            harvest_id=harvest_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": harvest}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/harvests")
async def list_harvests(
    trial_id: Optional[str] = None,
    crop: Optional[str] = None,
    status: Optional[str] = None,
    year: Optional[int] = None,
):
    """List harvests with optional filters"""
    harvests = harvest_management_service.list_harvests(
        trial_id=trial_id,
        crop=crop,
        status=status,
        year=year,
    )
    return {"status": "success", "data": harvests, "count": len(harvests)}


@router.get("/harvests/{harvest_id}")
async def get_harvest(harvest_id: str):
    """Get harvest details"""
    harvest = harvest_management_service.get_harvest(harvest_id)
    if not harvest:
        raise HTTPException(status_code=404, detail=f"Harvest {harvest_id} not found")
    return {"status": "success", "data": harvest}


@router.post("/harvests/{harvest_id}/quality")
async def add_quality_check(harvest_id: str, data: QualityCheck):
    """Add quality check for harvested material"""
    try:
        check = harvest_management_service.add_quality_check(
            harvest_id=harvest_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": check}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/harvests/{harvest_id}/quality")
async def get_quality_checks(harvest_id: str):
    """Get quality checks for a harvest"""
    checks = harvest_management_service.get_quality_checks(harvest_id)
    return {"status": "success", "data": checks, "count": len(checks)}


# Storage endpoints
@router.post("/storage/units")
async def create_storage_unit(data: StorageUnitCreate):
    """Create a new storage unit"""
    unit = harvest_management_service.create_storage_unit(**data.model_dump())
    return {"status": "success", "data": unit}


@router.get("/storage/units")
async def list_storage_units(
    storage_type: Optional[str] = None,
    location: Optional[str] = None,
):
    """List storage units"""
    units = harvest_management_service.list_storage_units(
        storage_type=storage_type,
        location=location,
    )
    return {"status": "success", "data": units, "count": len(units)}


@router.get("/storage/units/{unit_id}")
async def get_storage_unit(unit_id: str):
    """Get storage unit details"""
    unit = harvest_management_service.get_storage_unit(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail=f"Storage unit {unit_id} not found")
    return {"status": "success", "data": unit}


@router.post("/storage/units/{unit_id}/store")
async def store_harvest(unit_id: str, data: StoreHarvest):
    """Store harvested material in a storage unit"""
    try:
        record = harvest_management_service.store_harvest(
            harvest_id=data.harvest_id,
            unit_id=unit_id,
            quantity_kg=data.quantity_kg,
            notes=data.notes,
        )
        return {"status": "success", "data": record}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/storage/units/{unit_id}/withdraw")
async def withdraw_from_storage(unit_id: str, data: WithdrawStorage):
    """Withdraw material from storage"""
    try:
        record = harvest_management_service.withdraw_from_storage(
            unit_id=unit_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": record}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/storage/units/{unit_id}/history")
async def get_storage_history(unit_id: str):
    """Get storage transaction history"""
    history = harvest_management_service.get_storage_history(unit_id)
    return {"status": "success", "data": history, "count": len(history)}


# Utility endpoints
@router.post("/calculate/dry-weight")
async def calculate_dry_weight(data: DryWeightCalc):
    """Calculate dry weight at target moisture"""
    result = harvest_management_service.calculate_dry_weight(
        wet_weight_kg=data.wet_weight_kg,
        moisture_percent=data.moisture_percent,
        target_moisture=data.target_moisture,
    )
    return {"status": "success", "data": result}


@router.get("/storage/types")
async def get_storage_types():
    """Get available storage types"""
    types = harvest_management_service.get_storage_types()
    return {"status": "success", "data": types}


@router.get("/statistics")
async def get_statistics():
    """Get harvest and storage statistics"""
    stats = harvest_management_service.get_statistics()
    return {"status": "success", "data": stats}

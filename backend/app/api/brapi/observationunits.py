"""
BrAPI v2.1 Observation Units Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user

router = APIRouter()

_units_store: dict = {}
_units_counter = 0


class ObservationUnitBase(BaseModel):
    observationUnitName: Optional[str] = None
    observationUnitPUI: Optional[str] = None
    observationLevel: Optional[str] = None  # plot, plant, subplot, etc.
    observationLevelCode: Optional[str] = None
    studyDbId: Optional[str] = None
    studyName: Optional[str] = None
    germplasmDbId: Optional[str] = None
    germplasmName: Optional[str] = None
    locationDbId: Optional[str] = None
    locationName: Optional[str] = None
    trialDbId: Optional[str] = None
    trialName: Optional[str] = None
    programDbId: Optional[str] = None
    programName: Optional[str] = None
    positionCoordinateX: Optional[str] = None
    positionCoordinateY: Optional[str] = None
    positionCoordinateXType: Optional[str] = None
    positionCoordinateYType: Optional[str] = None
    replicate: Optional[str] = None
    blockNumber: Optional[str] = None
    entryNumber: Optional[str] = None


class ObservationUnitCreate(ObservationUnitBase):
    pass


def _init_demo_data():
    global _units_counter
    if _units_store:
        return
    
    demo_units = [
        {"observationUnitName": "Plot-001", "observationLevel": "plot", "germplasmName": "IR64", "studyName": "Rice Yield Trial 2025", "replicate": "1", "blockNumber": "1", "entryNumber": "1", "positionCoordinateX": "1", "positionCoordinateY": "1"},
        {"observationUnitName": "Plot-002", "observationLevel": "plot", "germplasmName": "Swarna", "studyName": "Rice Yield Trial 2025", "replicate": "1", "blockNumber": "1", "entryNumber": "2", "positionCoordinateX": "2", "positionCoordinateY": "1"},
        {"observationUnitName": "Plot-003", "observationLevel": "plot", "germplasmName": "HD2967", "studyName": "Wheat Trial 2025", "replicate": "1", "blockNumber": "1", "entryNumber": "1", "positionCoordinateX": "1", "positionCoordinateY": "1"},
        {"observationUnitName": "Plot-004", "observationLevel": "plot", "germplasmName": "PBW343", "studyName": "Wheat Trial 2025", "replicate": "1", "blockNumber": "1", "entryNumber": "2", "positionCoordinateX": "2", "positionCoordinateY": "1"},
        {"observationUnitName": "Plot-005", "observationLevel": "plot", "germplasmName": "IR64", "studyName": "Rice Yield Trial 2025", "replicate": "2", "blockNumber": "2", "entryNumber": "1", "positionCoordinateX": "1", "positionCoordinateY": "2"},
    ]
    
    for u in demo_units:
        _units_counter += 1
        uid = f"unit_{_units_counter}"
        _units_store[uid] = {"observationUnitDbId": uid, **u}


@router.get("/observationunits")
async def list_observation_units(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    studyDbId: Optional[str] = None,
    germplasmDbId: Optional[str] = None,
    observationLevel: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of observation units"""
    _init_demo_data()
    
    results = list(_units_store.values())
    
    if studyDbId:
        results = [u for u in results if u.get("studyDbId") == studyDbId]
    if germplasmDbId:
        results = [u for u in results if u.get("germplasmDbId") == germplasmDbId]
    if observationLevel:
        results = [u for u in results if u.get("observationLevel") == observationLevel]
    
    total = len(results)
    start = page * pageSize
    paginated = results[start:start + pageSize]
    
    return {
        "metadata": {"datafiles": [], "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": total, "totalPages": (total + pageSize - 1) // pageSize}, "status": [{"message": "Request successful", "messageType": "INFO"}]},
        "result": {"data": paginated}
    }


@router.post("/observationunits")
async def create_observation_unit(unit: ObservationUnitCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Create new observation unit"""
    global _units_counter
    _init_demo_data()
    
    _units_counter += 1
    uid = f"unit_{_units_counter}"
    new_unit = {"observationUnitDbId": uid, **unit.model_dump()}
    _units_store[uid] = new_unit
    
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": new_unit}


@router.get("/observationunits/{observationUnitDbId}")
async def get_observation_unit(observationUnitDbId: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_optional_user)):
    """Get observation unit by ID"""
    _init_demo_data()
    if observationUnitDbId not in _units_store:
        raise HTTPException(status_code=404, detail="Observation unit not found")
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": _units_store[observationUnitDbId]}

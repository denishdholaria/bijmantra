"""
BrAPI v2.1 Observations Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user

router = APIRouter()

_observations_store: dict = {}
_observations_counter = 0


class ObservationBase(BaseModel):
    observationUnitDbId: Optional[str] = None
    observationVariableDbId: Optional[str] = None
    observationVariableName: Optional[str] = None
    value: Optional[str] = None
    observationTimeStamp: Optional[str] = None
    collector: Optional[str] = None
    studyDbId: Optional[str] = None
    germplasmDbId: Optional[str] = None
    germplasmName: Optional[str] = None


class ObservationCreate(ObservationBase):
    pass


def _init_demo_data():
    global _observations_counter
    if _observations_store:
        return
    
    demo_observations = [
        {"observationVariableName": "Plant Height", "value": "125", "germplasmName": "IR64", "collector": "John Doe", "observationTimeStamp": "2025-01-15T10:30:00Z"},
        {"observationVariableName": "Plant Height", "value": "118", "germplasmName": "Swarna", "collector": "John Doe", "observationTimeStamp": "2025-01-15T10:35:00Z"},
        {"observationVariableName": "Days to Flowering", "value": "85", "germplasmName": "IR64", "collector": "Jane Smith", "observationTimeStamp": "2025-02-20T09:00:00Z"},
        {"observationVariableName": "Grain Yield", "value": "5500", "germplasmName": "HD2967", "collector": "Jane Smith", "observationTimeStamp": "2025-04-10T14:00:00Z"},
        {"observationVariableName": "1000 Grain Weight", "value": "42.5", "germplasmName": "PBW343", "collector": "John Doe", "observationTimeStamp": "2025-04-12T11:00:00Z"},
    ]
    
    for o in demo_observations:
        _observations_counter += 1
        oid = f"obs_{_observations_counter}"
        _observations_store[oid] = {"observationDbId": oid, **o}


@router.get("/observations")
async def list_observations(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    studyDbId: Optional[str] = None,
    germplasmDbId: Optional[str] = None,
    observationVariableDbId: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of observations"""
    _init_demo_data()
    
    results = list(_observations_store.values())
    
    if studyDbId:
        results = [o for o in results if o.get("studyDbId") == studyDbId]
    if germplasmDbId:
        results = [o for o in results if o.get("germplasmDbId") == germplasmDbId]
    if observationVariableDbId:
        results = [o for o in results if o.get("observationVariableDbId") == observationVariableDbId]
    
    total = len(results)
    start = page * pageSize
    paginated = results[start:start + pageSize]
    
    return {
        "metadata": {"datafiles": [], "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": total, "totalPages": (total + pageSize - 1) // pageSize}, "status": [{"message": "Request successful", "messageType": "INFO"}]},
        "result": {"data": paginated}
    }


@router.post("/observations")
async def create_observation(observation: ObservationCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Create new observation"""
    global _observations_counter
    _init_demo_data()
    
    _observations_counter += 1
    oid = f"obs_{_observations_counter}"
    new_obs = {"observationDbId": oid, "observationTimeStamp": datetime.utcnow().isoformat() + "Z", **observation.model_dump()}
    _observations_store[oid] = new_obs
    
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": new_obs}


@router.get("/observations/{observationDbId}")
async def get_observation(observationDbId: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_optional_user)):
    """Get observation by ID"""
    _init_demo_data()
    if observationDbId not in _observations_store:
        raise HTTPException(status_code=404, detail="Observation not found")
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": _observations_store[observationDbId]}

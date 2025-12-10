"""
BrAPI v2.1 Crosses Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user

router = APIRouter()

_crosses_store: dict = {}
_crosses_counter = 0


class CrossBase(BaseModel):
    crossName: Optional[str] = None
    crossType: Optional[str] = None  # BIPARENTAL, SELF, OPEN_POLLINATED, etc.
    crossingProjectDbId: Optional[str] = None
    crossingProjectName: Optional[str] = None
    parent1DbId: Optional[str] = None
    parent1Name: Optional[str] = None
    parent1Type: Optional[str] = None  # MALE, FEMALE, SELF, POPULATION
    parent2DbId: Optional[str] = None
    parent2Name: Optional[str] = None
    parent2Type: Optional[str] = None
    pollinationTimeStamp: Optional[str] = None
    plannedCrossDbId: Optional[str] = None


class CrossCreate(CrossBase):
    pass


def _init_demo_data():
    global _crosses_counter
    if _crosses_store:
        return
    
    demo_crosses = [
        {"crossName": "IR64 x Swarna", "crossType": "BIPARENTAL", "parent1Name": "IR64", "parent2Name": "Swarna", "parent1Type": "FEMALE", "parent2Type": "MALE"},
        {"crossName": "HD2967 x PBW343", "crossType": "BIPARENTAL", "parent1Name": "HD2967", "parent2Name": "PBW343", "parent1Type": "FEMALE", "parent2Type": "MALE"},
        {"crossName": "Pusa Basmati 1121 x IR64", "crossType": "BIPARENTAL", "parent1Name": "Pusa Basmati 1121", "parent2Name": "IR64", "parent1Type": "FEMALE", "parent2Type": "MALE"},
    ]
    
    for c in demo_crosses:
        _crosses_counter += 1
        cid = f"cross_{_crosses_counter}"
        _crosses_store[cid] = {"crossDbId": cid, **c}


@router.get("/crosses")
async def list_crosses(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    crossingProjectDbId: Optional[str] = None,
    crossType: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of crosses"""
    _init_demo_data()
    
    results = list(_crosses_store.values())
    
    if crossingProjectDbId:
        results = [c for c in results if c.get("crossingProjectDbId") == crossingProjectDbId]
    if crossType:
        results = [c for c in results if c.get("crossType") == crossType]
    
    total = len(results)
    start = page * pageSize
    paginated = results[start:start + pageSize]
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": total, "totalPages": (total + pageSize - 1) // pageSize},
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": {"data": paginated}
    }


@router.post("/crosses")
async def create_cross(
    cross: CrossCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Create new cross"""
    global _crosses_counter
    _init_demo_data()
    
    _crosses_counter += 1
    cid = f"cross_{_crosses_counter}"
    new_cross = {"crossDbId": cid, **cross.model_dump()}
    _crosses_store[cid] = new_cross
    
    return {
        "metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": [{"message": "Cross created", "messageType": "INFO"}]},
        "result": new_cross
    }


@router.get("/crosses/{crossDbId}")
async def get_cross(crossDbId: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_optional_user)):
    """Get cross by ID"""
    _init_demo_data()
    if crossDbId not in _crosses_store:
        raise HTTPException(status_code=404, detail="Cross not found")
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": _crosses_store[crossDbId]}

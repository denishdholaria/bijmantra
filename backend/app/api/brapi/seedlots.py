"""
BrAPI v2.1 Seed Lots Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user

router = APIRouter()

_seedlots_store: dict = {}
_seedlots_counter = 0


class SeedLotBase(BaseModel):
    seedLotName: Optional[str] = None
    seedLotDescription: Optional[str] = None
    germplasmDbId: Optional[str] = None
    locationDbId: Optional[str] = None
    programDbId: Optional[str] = None
    sourceCollection: Optional[str] = None
    storageLocation: Optional[str] = None
    amount: Optional[float] = None
    units: Optional[str] = None
    createdDate: Optional[str] = None
    lastUpdated: Optional[str] = None
    externalReferences: Optional[List[dict]] = []


class SeedLotCreate(SeedLotBase):
    pass


def _init_demo_data():
    global _seedlots_counter
    if _seedlots_store:
        return
    
    demo_seedlots = [
        {"seedLotName": "IR64-2025-001", "seedLotDescription": "Foundation seed", "storageLocation": "Cold Room A", "amount": 500, "units": "kg", "createdDate": "2025-01-01"},
        {"seedLotName": "Swarna-2025-001", "seedLotDescription": "Certified seed", "storageLocation": "Cold Room A", "amount": 300, "units": "kg", "createdDate": "2025-01-05"},
        {"seedLotName": "HD2967-2025-001", "seedLotDescription": "Breeder seed", "storageLocation": "Cold Room B", "amount": 100, "units": "kg", "createdDate": "2025-01-10"},
        {"seedLotName": "PBW343-2025-001", "seedLotDescription": "Foundation seed", "storageLocation": "Cold Room B", "amount": 250, "units": "kg", "createdDate": "2025-01-15"},
        {"seedLotName": "IR64-2024-002", "seedLotDescription": "Certified seed - previous season", "storageLocation": "Cold Room C", "amount": 150, "units": "kg", "createdDate": "2024-06-01"},
    ]
    
    for sl in demo_seedlots:
        _seedlots_counter += 1
        slid = f"seedlot_{_seedlots_counter}"
        _seedlots_store[slid] = {"seedLotDbId": slid, **sl}


@router.get("/seedlots")
async def list_seedlots(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    germplasmDbId: Optional[str] = None,
    locationDbId: Optional[str] = None,
    programDbId: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of seed lots"""
    _init_demo_data()
    
    results = list(_seedlots_store.values())
    
    if germplasmDbId:
        results = [sl for sl in results if sl.get("germplasmDbId") == germplasmDbId]
    if locationDbId:
        results = [sl for sl in results if sl.get("locationDbId") == locationDbId]
    if programDbId:
        results = [sl for sl in results if sl.get("programDbId") == programDbId]
    
    total = len(results)
    start = page * pageSize
    paginated = results[start:start + pageSize]
    
    return {
        "metadata": {"datafiles": [], "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": total, "totalPages": (total + pageSize - 1) // pageSize}, "status": [{"message": "Request successful", "messageType": "INFO"}]},
        "result": {"data": paginated}
    }


@router.post("/seedlots")
async def create_seedlot(seedlot: SeedLotCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Create new seed lot"""
    global _seedlots_counter
    _init_demo_data()
    
    _seedlots_counter += 1
    slid = f"seedlot_{_seedlots_counter}"
    new_seedlot = {"seedLotDbId": slid, **seedlot.model_dump()}
    _seedlots_store[slid] = new_seedlot
    
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": new_seedlot}


@router.get("/seedlots/{seedLotDbId}")
async def get_seedlot(seedLotDbId: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_optional_user)):
    """Get seed lot by ID"""
    _init_demo_data()
    if seedLotDbId not in _seedlots_store:
        raise HTTPException(status_code=404, detail="Seed lot not found")
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": _seedlots_store[seedLotDbId]}


@router.put("/seedlots/{seedLotDbId}")
async def update_seedlot(seedLotDbId: str, seedlot: SeedLotCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Update seed lot"""
    _init_demo_data()
    if seedLotDbId not in _seedlots_store:
        raise HTTPException(status_code=404, detail="Seed lot not found")
    
    _seedlots_store[seedLotDbId].update(seedlot.model_dump())
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": _seedlots_store[seedLotDbId]}

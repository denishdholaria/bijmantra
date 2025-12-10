"""
BrAPI v2.1 Samples Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter()

_samples_store: dict = {}
_samples_counter = 0


class SampleBase(BaseModel):
    sampleName: Optional[str] = None
    sampleType: Optional[str] = None  # DNA, RNA, Tissue, Seed, etc.
    sampleDescription: Optional[str] = None
    germplasmDbId: Optional[str] = None
    observationUnitDbId: Optional[str] = None
    plateDbId: Optional[str] = None
    plateIndex: Optional[str] = None
    plotDbId: Optional[str] = None
    studyDbId: Optional[str] = None
    takenBy: Optional[str] = None
    sampleTimestamp: Optional[str] = None
    tissueType: Optional[str] = None
    concentration: Optional[str] = None
    volume: Optional[str] = None
    sampleBarcode: Optional[str] = None
    samplePUI: Optional[str] = None


class SampleCreate(SampleBase):
    pass


def _init_demo_data():
    global _samples_counter
    if _samples_store:
        return
    
    demo_samples = [
        {"sampleName": "IR64-DNA-001", "sampleType": "DNA", "tissueType": "Leaf", "concentration": "50 ng/µL", "volume": "100 µL", "takenBy": "Lab Tech 1"},
        {"sampleName": "Swarna-DNA-001", "sampleType": "DNA", "tissueType": "Leaf", "concentration": "45 ng/µL", "volume": "100 µL", "takenBy": "Lab Tech 1"},
        {"sampleName": "HD2967-DNA-001", "sampleType": "DNA", "tissueType": "Leaf", "concentration": "55 ng/µL", "volume": "100 µL", "takenBy": "Lab Tech 2"},
        {"sampleName": "IR64-Seed-001", "sampleType": "Seed", "sampleDescription": "Seed sample for storage", "takenBy": "Field Tech 1"},
        {"sampleName": "Swarna-Tissue-001", "sampleType": "Tissue", "tissueType": "Root", "sampleDescription": "Root tissue for analysis", "takenBy": "Lab Tech 1"},
    ]
    
    for s in demo_samples:
        _samples_counter += 1
        sid = f"sample_{_samples_counter}"
        _samples_store[sid] = {"sampleDbId": sid, **s}


@router.get("/samples")
async def list_samples(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    sampleType: Optional[str] = None,
    germplasmDbId: Optional[str] = None,
    studyDbId: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get list of samples"""
    _init_demo_data()
    
    results = list(_samples_store.values())
    
    if sampleType:
        results = [s for s in results if sampleType.lower() in s.get("sampleType", "").lower()]
    if germplasmDbId:
        results = [s for s in results if s.get("germplasmDbId") == germplasmDbId]
    if studyDbId:
        results = [s for s in results if s.get("studyDbId") == studyDbId]
    
    total = len(results)
    start = page * pageSize
    paginated = results[start:start + pageSize]
    
    return {
        "metadata": {"datafiles": [], "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": total, "totalPages": (total + pageSize - 1) // pageSize}, "status": [{"message": "Request successful", "messageType": "INFO"}]},
        "result": {"data": paginated}
    }


@router.post("/samples")
async def create_sample(sample: SampleCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Create new sample"""
    global _samples_counter
    _init_demo_data()
    
    _samples_counter += 1
    sid = f"sample_{_samples_counter}"
    new_sample = {"sampleDbId": sid, **sample.model_dump()}
    _samples_store[sid] = new_sample
    
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": new_sample}


@router.get("/samples/{sampleDbId}")
async def get_sample(sampleDbId: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Get sample by ID"""
    _init_demo_data()
    if sampleDbId not in _samples_store:
        raise HTTPException(status_code=404, detail="Sample not found")
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": _samples_store[sampleDbId]}

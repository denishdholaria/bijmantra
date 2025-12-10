"""
BrAPI v2.1 Events Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter()

_events_store: dict = {}
_events_counter = 0


class EventBase(BaseModel):
    eventType: Optional[str] = None  # Planting, Fertilizing, Irrigation, Harvest, etc.
    eventDescription: Optional[str] = None
    studyDbId: Optional[str] = None
    observationUnitDbIds: Optional[List[str]] = []
    date: Optional[str] = None
    eventParameters: Optional[List[dict]] = []


class EventCreate(EventBase):
    pass


def _init_demo_data():
    global _events_counter
    if _events_store:
        return
    
    demo_events = [
        {"eventType": "Planting", "eventDescription": "Sowing of rice seeds", "date": "2025-01-10", "eventParameters": [{"key": "seed_rate", "value": "25 kg/ha"}]},
        {"eventType": "Fertilizing", "eventDescription": "Basal fertilizer application", "date": "2025-01-15", "eventParameters": [{"key": "fertilizer", "value": "NPK 10:26:26"}, {"key": "rate", "value": "100 kg/ha"}]},
        {"eventType": "Irrigation", "eventDescription": "First irrigation", "date": "2025-01-20", "eventParameters": [{"key": "method", "value": "Flood"}, {"key": "depth", "value": "5 cm"}]},
        {"eventType": "Weeding", "eventDescription": "Manual weeding", "date": "2025-02-01"},
        {"eventType": "Pesticide", "eventDescription": "Insecticide spray", "date": "2025-02-15", "eventParameters": [{"key": "chemical", "value": "Chlorpyrifos"}, {"key": "rate", "value": "2 ml/L"}]},
        {"eventType": "Harvest", "eventDescription": "Crop harvest", "date": "2025-04-20"},
    ]
    
    for e in demo_events:
        _events_counter += 1
        eid = f"event_{_events_counter}"
        _events_store[eid] = {"eventDbId": eid, **e}


@router.get("/events")
async def list_events(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    studyDbId: Optional[str] = None,
    eventType: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get list of events"""
    _init_demo_data()
    
    results = list(_events_store.values())
    
    if studyDbId:
        results = [e for e in results if e.get("studyDbId") == studyDbId]
    if eventType:
        results = [e for e in results if eventType.lower() in e.get("eventType", "").lower()]
    
    total = len(results)
    start = page * pageSize
    paginated = results[start:start + pageSize]
    
    return {
        "metadata": {"datafiles": [], "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": total, "totalPages": (total + pageSize - 1) // pageSize}, "status": [{"message": "Request successful", "messageType": "INFO"}]},
        "result": {"data": paginated}
    }


@router.post("/events")
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Create new event"""
    global _events_counter
    _init_demo_data()
    
    _events_counter += 1
    eid = f"event_{_events_counter}"
    new_event = {"eventDbId": eid, **event.model_dump()}
    _events_store[eid] = new_event
    
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": new_event}


@router.get("/events/{eventDbId}")
async def get_event(eventDbId: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Get event by ID"""
    _init_demo_data()
    if eventDbId not in _events_store:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": _events_store[eventDbId]}

"""
BrAPI v2.1 Events Endpoints

Database-backed implementation (no in-memory demo data).
Demo data is seeded into Demo Organization via seeders.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.models.phenotyping import Event

router = APIRouter()


class EventBase(BaseModel):
    eventType: str
    eventTypeDbId: Optional[str] = None
    eventDescription: Optional[str] = None
    date: Optional[str] = None
    studyDbId: Optional[str] = None
    observationUnitDbIds: Optional[List[str]] = None
    eventParameters: Optional[List[dict]] = None


class EventCreate(EventBase):
    pass


def _model_to_brapi(event: Event) -> dict:
    """Convert SQLAlchemy model to BrAPI response format"""
    return {
        "eventDbId": event.event_db_id,
        "eventType": event.event_type,
        "eventTypeDbId": event.event_type_db_id,
        "eventDescription": event.event_description,
        "date": event.date,
        "studyDbId": str(event.study_id) if event.study_id else None,
        "observationUnitDbIds": event.observation_unit_db_ids,
        "eventParameters": event.event_parameters,
        "additionalInfo": event.additional_info,
        "externalReferences": event.external_references,
    }


@router.get("/events")
async def list_events(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    eventDbId: Optional[str] = None,
    eventType: Optional[str] = None,
    studyDbId: Optional[str] = None,
    observationUnitDbId: Optional[str] = None,
    dateRangeStart: Optional[str] = None,
    dateRangeEnd: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of events from database"""
    query = db.query(Event)
    
    if eventDbId:
        query = query.filter(Event.event_db_id == eventDbId)
    if eventType:
        query = query.filter(Event.event_type.ilike(f"%{eventType}%"))
    if studyDbId:
        query = query.filter(Event.study_id == int(studyDbId))
    if observationUnitDbId:
        # Filter by JSON array contains
        query = query.filter(Event.observation_unit_db_ids.contains([observationUnitDbId]))
    if dateRangeStart:
        query = query.filter(Event.date >= dateRangeStart)
    if dateRangeEnd:
        query = query.filter(Event.date <= dateRangeEnd)
    
    total = query.count()
    results = query.offset(page * pageSize).limit(pageSize).all()
    data = [_model_to_brapi(e) for e in results]
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": pageSize,
                "totalCount": total,
                "totalPages": (total + pageSize - 1) // pageSize if total > 0 else 0
            },
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": {"data": data}
    }


@router.post("/events")
async def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new event in database"""
    org_id = current_user.organization_id if current_user else 1
    event_db_id = f"event_{uuid.uuid4().hex[:12]}"
    
    new_event = Event(
        organization_id=org_id,
        event_db_id=event_db_id,
        event_type=event.eventType,
        event_type_db_id=event.eventTypeDbId,
        event_description=event.eventDescription,
        date=event.date,
        study_id=int(event.studyDbId) if event.studyDbId else None,
        observation_unit_db_ids=event.observationUnitDbIds,
        event_parameters=event.eventParameters,
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Event created successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(new_event)
    }


@router.get("/events/{eventDbId}")
async def get_event(
    eventDbId: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Get event by ID from database"""
    event = db.query(Event).filter(Event.event_db_id == eventDbId).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": []
        },
        "result": _model_to_brapi(event)
    }

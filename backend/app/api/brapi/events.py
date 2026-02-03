"""
BrAPI v2.1 Events Endpoints

Database-backed implementation (no in-memory demo data).
Demo data is seeded into Demo Organization via seeders.

GOVERNANCE.md §4.3.1 Compliant: Fully async implementation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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
    """Convert SQLAlchemy model to BrAPI response format.

    Args:
        event (Event): The Event SQLAlchemy model.

    Returns:
        A dictionary representing the event in BrAPI format.
    """
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get a list of events.

    Args:
        page (int): The page number to return.
        pageSize (int): The number of items to return per page.
        eventDbId (Optional[str]): The database ID of the event to filter by.
        eventType (Optional[str]): The type of the event to filter by.
        studyDbId (Optional[str]): The database ID of the study to filter by.
        observationUnitDbId (Optional[str]): The database ID of the observation unit to filter by.
        dateRangeStart (Optional[str]): The start of the date range to filter by.
        dateRangeEnd (Optional[str]): The end of the date range to filter by.
        db (AsyncSession): The database session.
        current_user (Optional[User]): The current user.

    Returns:
        A dictionary containing the list of events and metadata.
    """
    # Build base statement
    stmt = select(Event)
    
    # Filter by user's organization (multi-tenant isolation)
    if current_user and current_user.organization_id:
        stmt = stmt.where(Event.organization_id == current_user.organization_id)
    
    # Apply filters
    if eventDbId:
        stmt = stmt.where(Event.event_db_id == eventDbId)
    if eventType:
        stmt = stmt.where(Event.event_type.ilike(f"%{eventType}%"))
    if studyDbId:
        stmt = stmt.where(Event.study_id == int(studyDbId))
    if observationUnitDbId:
        # Filter by JSON array contains
        stmt = stmt.where(Event.observation_unit_db_ids.contains([observationUnitDbId]))
    if dateRangeStart:
        stmt = stmt.where(Event.date >= dateRangeStart)
    if dateRangeEnd:
        stmt = stmt.where(Event.date <= dateRangeEnd)
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute
    stmt = stmt.offset(page * pageSize).limit(pageSize)
    result = await db.execute(stmt)
    results = result.scalars().all()
    
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new event.

    Args:
        event (EventCreate): The event to create.
        db (AsyncSession): The database session.
        current_user (User): The current user.

    Returns:
        A dictionary containing the newly created event and metadata.
    """
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
    await db.commit()
    await db.refresh(new_event)
    
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Get a single event by its database ID.

    Args:
        eventDbId (str): The database ID of the event.
        db (AsyncSession): The database session.
        current_user (Optional[User]): The current user.

    Returns:
        A dictionary containing the event data and metadata.

    Raises:
        HTTPException: If the event with the given ID is not found.
    """
    stmt = select(Event).where(Event.event_db_id == eventDbId)
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()
    
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

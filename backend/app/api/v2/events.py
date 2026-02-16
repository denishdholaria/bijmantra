"""
Event Bus API
Inter-module pub/sub communication endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.event_bus import event_bus, EventType, Event, DeadLetter
from app.api.deps import get_current_user

router = APIRouter(prefix="/events", tags=["Event Bus"], dependencies=[Depends(get_current_user)])


# Request/Response Models
class PublishEventRequest(BaseModel):
    """Publish an event"""
    event_type: str = Field(..., description="Event type (e.g., germplasm.created)")
    data: Dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="api", description="Source module")
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    correlation_id: Optional[str] = None


class EventResponse(BaseModel):
    """Event response"""
    id: str
    type: str
    source: str
    data: Dict[str, Any]
    timestamp: str
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    correlation_id: Optional[str] = None


class DeadLetterResponse(BaseModel):
    """Dead letter response"""
    event: EventResponse
    error: str
    handler_module: str
    failed_at: str
    retry_count: int


def _event_to_response(event: Event) -> EventResponse:
    """Convert Event to response"""
    return EventResponse(
        id=event.id,
        type=event.type.value,
        source=event.source,
        data=event.data,
        timestamp=event.timestamp.isoformat(),
        user_id=event.user_id,
        organization_id=event.organization_id,
        correlation_id=event.correlation_id,
    )


def _dead_letter_to_response(dl: DeadLetter) -> DeadLetterResponse:
    """Convert DeadLetter to response"""
    return DeadLetterResponse(
        event=_event_to_response(dl.event),
        error=dl.error,
        handler_module=dl.handler_module,
        failed_at=dl.failed_at.isoformat(),
        retry_count=dl.retry_count,
    )


# Endpoints
@router.get("/types")
async def get_event_types():
    """Get all available event types"""
    return {
        "event_types": [
            {"value": e.value, "name": e.name}
            for e in EventType
        ]
    }


@router.post("/publish", response_model=EventResponse)
async def publish_event(request: PublishEventRequest):
    """Publish an event to the event bus"""
    # Parse event type
    try:
        event_type = EventType(request.event_type)
    except ValueError:
        event_type = EventType.CUSTOM

    event = await event_bus.publish(
        event_type=event_type,
        data=request.data,
        source=request.source,
        user_id=request.user_id,
        organization_id=request.organization_id,
        correlation_id=request.correlation_id,
    )

    return _event_to_response(event)


@router.get("/history", response_model=List[EventResponse])
async def get_event_history(
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 100,
):
    """Get event history"""
    # Parse event type if provided
    parsed_type = None
    if event_type:
        try:
            parsed_type = EventType(event_type)
        except ValueError:
            pass

    events = event_bus.get_history(
        event_type=parsed_type,
        source=source,
        limit=limit,
    )

    return [_event_to_response(e) for e in events]


@router.get("/subscriptions")
async def get_subscriptions():
    """Get all active subscriptions"""
    return {"subscriptions": event_bus.get_subscriptions()}


@router.get("/dead-letters", response_model=List[DeadLetterResponse])
async def get_dead_letters(limit: int = 50):
    """Get failed events from dead letter queue"""
    dead_letters = event_bus.get_dead_letters(limit)
    return [_dead_letter_to_response(dl) for dl in dead_letters]


@router.post("/dead-letters/{index}/retry")
async def retry_dead_letter(index: int):
    """Retry a failed event"""
    success = await event_bus.retry_dead_letter(index)
    if not success:
        raise HTTPException(status_code=404, detail="Dead letter not found")
    return {"message": "Event retried successfully"}


@router.delete("/history")
async def clear_history():
    """Clear event history"""
    event_bus.clear_history()
    return {"message": "Event history cleared"}


@router.delete("/dead-letters")
async def clear_dead_letters():
    """Clear dead letter queue"""
    event_bus.clear_dead_letters()
    return {"message": "Dead letter queue cleared"}

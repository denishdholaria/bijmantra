"""
Plot History API
Endpoints for managing plot event history and timeline
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.plot_history import plot_history_service


router = APIRouter(prefix="/plot-history", tags=["Plot History"])


class CreateEventRequest(BaseModel):
    type: str
    description: str
    date: Optional[str] = None
    value: Optional[str] = None
    notes: Optional[str] = None
    recorded_by: Optional[str] = None


class UpdateEventRequest(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    value: Optional[str] = None
    notes: Optional[str] = None


@router.get("/stats")
async def get_stats(field_id: Optional[str] = Query(None)):
    """Get plot history statistics."""
    return plot_history_service.get_stats(field_id=field_id)


@router.get("/event-types")
async def get_event_types():
    """Get available event types."""
    return {"types": plot_history_service.get_event_types()}


@router.get("/fields")
async def get_fields():
    """Get available fields."""
    return {"fields": plot_history_service.get_fields()}


@router.get("/plots")
async def get_plots(
    field_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get plots with optional filters."""
    return plot_history_service.get_plots(
        field_id=field_id,
        status=status,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/plots/{plot_id}")
async def get_plot(plot_id: str):
    """Get a single plot with its events."""
    plot = plot_history_service.get_plot(plot_id)
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    return plot


@router.get("/plots/{plot_id}/events")
async def get_plot_events(
    plot_id: str,
    event_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Get events for a specific plot."""
    return plot_history_service.get_plot_events(
        plot_id=plot_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
    )


@router.post("/plots/{plot_id}/events")
async def create_event(plot_id: str, request: CreateEventRequest):
    """Create a new event for a plot."""
    event = plot_history_service.create_event(plot_id, request.model_dump())
    if not event:
        raise HTTPException(status_code=404, detail="Plot not found")
    return event


@router.patch("/events/{event_id}")
async def update_event(event_id: str, request: UpdateEventRequest):
    """Update an existing event."""
    data = {k: v for k, v in request.model_dump().items() if v is not None}
    event = plot_history_service.update_event(event_id, data)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/events/{event_id}")
async def delete_event(event_id: str):
    """Delete an event."""
    if not plot_history_service.delete_event(event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True, "message": "Event deleted"}

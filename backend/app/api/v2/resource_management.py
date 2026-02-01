"""
Resource Management API

Endpoints for:
- Budget allocation and tracking
- Staff allocation
- Field utilization
- Calendar scheduling
- Harvest logging
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date

from app.services.resource_management import resource_management_service

router = APIRouter(prefix="/resources", tags=["Resource Management"])


# ===========================================
# Pydantic Models
# ===========================================

class BudgetCategoryResponse(BaseModel):
    id: str
    name: str
    allocated: float
    used: float
    unit: str
    status: str
    year: int


class BudgetUpdateRequest(BaseModel):
    used: float = Field(..., ge=0, description="Amount used")


class StaffAllocationResponse(BaseModel):
    id: str
    role: str
    count: int
    projects: int
    department: str


class FieldAllocationResponse(BaseModel):
    id: str
    field: str
    area: float
    trials: int
    utilization: float


class CalendarEventResponse(BaseModel):
    id: str
    title: str
    type: str
    date: str
    time: str
    duration: str
    location: str
    assignee: str
    status: str
    description: Optional[str] = None


class CalendarEventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: str = Field(default="meeting", description="field, lab, equipment, meeting")
    date: str = Field(..., description="ISO date YYYY-MM-DD")
    time: str = Field(default="09:00", description="HH:MM format")
    duration: str = Field(default="1h", description="Duration like 1h, 2h, 30m")
    location: str = Field(default="TBD")
    assignee: str = Field(default="Unassigned")
    description: Optional[str] = None
    trial_id: Optional[int] = None


class HarvestRecordResponse(BaseModel):
    id: str
    entry: str
    plot: str
    harvest_date: str
    fresh_weight: float
    dry_weight: float
    moisture: float
    grain_yield: float
    quality: str
    notes: Optional[str] = None
    recorded_by: Optional[str] = None


class HarvestRecordCreate(BaseModel):
    entry: str = Field(..., min_length=1, max_length=100)
    plot: str = Field(..., min_length=1, max_length=50)
    harvest_date: Optional[str] = None
    fresh_weight: float = Field(..., ge=0)
    dry_weight: float = Field(..., ge=0)
    moisture: float = Field(default=14.0, ge=0, le=100)
    grain_yield: float = Field(..., ge=0)
    quality: str = Field(default="B", description="A, B, or C")
    trial_id: Optional[int] = None
    study_id: Optional[int] = None
    notes: Optional[str] = None
    recorded_by: Optional[str] = None


# ===========================================
# Resource Overview
# ===========================================

@router.get("/overview", summary="Get resource overview")
async def get_resource_overview():
    """Get complete resource overview including budget, staff, fields, calendar, and harvest."""
    return resource_management_service.get_resource_overview()


# ===========================================
# Budget Endpoints
# ===========================================

@router.get("/budget", summary="Get budget categories", response_model=List[BudgetCategoryResponse])
async def get_budget_categories(
    year: int = Query(default=2025, description="Budget year"),
):
    """Get all budget categories for a year."""
    return resource_management_service.get_budget_categories(year)


@router.get("/budget/summary", summary="Get budget summary")
async def get_budget_summary(
    year: int = Query(default=2025, description="Budget year"),
):
    """Get budget summary statistics."""
    return resource_management_service.get_budget_summary(year)


@router.patch("/budget/{category_id}", summary="Update budget usage")
async def update_budget_category(
    category_id: str,
    update: BudgetUpdateRequest,
):
    """Update budget usage for a category."""
    result = resource_management_service.update_budget_category(category_id, update.used)
    if not result:
        raise HTTPException(status_code=404, detail="Budget category not found")
    return result


# ===========================================
# Staff Endpoints
# ===========================================

@router.get("/staff", summary="Get staff allocations", response_model=List[StaffAllocationResponse])
async def get_staff_allocations():
    """Get all staff allocations."""
    return resource_management_service.get_staff_allocations()


@router.get("/staff/summary", summary="Get staff summary")
async def get_staff_summary():
    """Get staff summary statistics."""
    return resource_management_service.get_staff_summary()


# ===========================================
# Field Endpoints
# ===========================================

@router.get("/fields", summary="Get field allocations", response_model=List[FieldAllocationResponse])
async def get_field_allocations():
    """Get all field allocations."""
    return resource_management_service.get_field_allocations()


@router.get("/fields/summary", summary="Get field summary")
async def get_field_summary():
    """Get field summary statistics."""
    return resource_management_service.get_field_summary()


# ===========================================
# Calendar Endpoints
# ===========================================

@router.get("/calendar", summary="Get calendar events", response_model=List[CalendarEventResponse])
async def get_calendar_events(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    event_type: Optional[str] = Query(None, description="Event type: field, lab, equipment, meeting"),
    status: Optional[str] = Query(None, description="Event status: scheduled, in-progress, completed"),
):
    """Get calendar events with optional filters."""
    return resource_management_service.get_calendar_events(
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        status=status,
    )


@router.get("/calendar/date/{target_date}", summary="Get events for date")
async def get_events_by_date(target_date: str):
    """Get all events for a specific date."""
    return resource_management_service.get_events_by_date(target_date)


@router.get("/calendar/summary", summary="Get calendar summary")
async def get_calendar_summary():
    """Get calendar summary by event type."""
    return resource_management_service.get_calendar_summary()


@router.post("/calendar", summary="Create calendar event", response_model=CalendarEventResponse)
async def create_calendar_event(event: CalendarEventCreate):
    """Create a new calendar event."""
    return resource_management_service.create_calendar_event(event.model_dump())


@router.patch("/calendar/{event_id}/status", summary="Update event status")
async def update_event_status(
    event_id: str,
    status: str = Query(..., description="New status: scheduled, in-progress, completed, cancelled"),
):
    """Update event status."""
    result = resource_management_service.update_event_status(event_id, status)
    if not result:
        raise HTTPException(status_code=404, detail="Event not found")
    return result


@router.delete("/calendar/{event_id}", summary="Delete calendar event")
async def delete_calendar_event(event_id: str):
    """Delete a calendar event."""
    if not resource_management_service.delete_calendar_event(event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}


# ===========================================
# Harvest Endpoints
# ===========================================

@router.get("/harvest", summary="Get harvest records", response_model=List[HarvestRecordResponse])
async def get_harvest_records(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    quality: Optional[str] = Query(None, description="Quality grade: A, B, C"),
    search: Optional[str] = Query(None, description="Search by entry or plot"),
):
    """Get harvest records with optional filters."""
    return resource_management_service.get_harvest_records(
        start_date=start_date,
        end_date=end_date,
        quality=quality,
        search=search,
    )


@router.get("/harvest/summary", summary="Get harvest summary")
async def get_harvest_summary():
    """Get harvest summary statistics."""
    return resource_management_service.get_harvest_summary()


@router.post("/harvest", summary="Create harvest record", response_model=HarvestRecordResponse)
async def create_harvest_record(record: HarvestRecordCreate):
    """Create a new harvest record."""
    return resource_management_service.create_harvest_record(record.model_dump())


@router.patch("/harvest/{record_id}", summary="Update harvest record")
async def update_harvest_record(
    record_id: str,
    updates: Dict[str, Any],
):
    """Update a harvest record."""
    result = resource_management_service.update_harvest_record(record_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Harvest record not found")
    return result


@router.delete("/harvest/{record_id}", summary="Delete harvest record")
async def delete_harvest_record(record_id: str):
    """Delete a harvest record."""
    if not resource_management_service.delete_harvest_record(record_id):
        raise HTTPException(status_code=404, detail="Harvest record not found")
    return {"message": "Harvest record deleted successfully"}

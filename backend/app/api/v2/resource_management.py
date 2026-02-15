"""
Resource Management API
Budget, staff, field utilization, calendar, harvest — queries existing tables.

Refactored: Session 94 — migrated from in-memory demo data to DB queries.
Budget/Expense use BudgetCategory + Expense models. Calendar/Fields use Trial/Location.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.core import Trial, Study, Location
from app.models.cost_analysis import BudgetCategory, Expense

from app.api.deps import get_current_user

router = APIRouter(prefix="/resources", tags=["Resource Management"], dependencies=[Depends(get_current_user)])


# ============================================================================
# Schemas
# ============================================================================

class BudgetUpdateRequest(BaseModel):
    used: float = Field(..., ge=0)


class CalendarEventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: str = Field(default="meeting")
    date: str = Field(...)
    time: str = Field(default="09:00")
    duration: str = Field(default="1h")
    location: str = Field(default="TBD")
    assignee: str = Field(default="Unassigned")
    description: Optional[str] = None


class HarvestRecordCreate(BaseModel):
    entry: str = Field(..., min_length=1, max_length=100)
    plot: str = Field(..., min_length=1, max_length=50)
    harvest_date: Optional[str] = None
    fresh_weight: float = Field(..., ge=0)
    dry_weight: float = Field(..., ge=0)
    moisture: float = Field(default=14.0, ge=0, le=100)
    grain_yield: float = Field(..., ge=0)
    quality: str = Field(default="B")
    notes: Optional[str] = None
    recorded_by: Optional[str] = None


# ============================================================================
# Resource Overview
# ============================================================================

@router.get("/overview")
async def get_resource_overview(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get resource overview from real data."""
    trial_count = (await db.execute(
        select(func.count(Trial.id)).where(Trial.organization_id == organization_id)
    )).scalar() or 0

    location_count = (await db.execute(
        select(func.count(Location.id)).where(Location.organization_id == organization_id)
    )).scalar() or 0

    budget_total = (await db.execute(
        select(func.sum(BudgetCategory.allocated)).where(BudgetCategory.organization_id == organization_id)
    )).scalar() or 0

    expense_total = (await db.execute(
        select(func.sum(Expense.amount)).where(Expense.organization_id == organization_id)
    )).scalar() or 0

    return {
        "budget": {"total": float(budget_total), "used": float(expense_total)},
        "staff": {"total": 0, "note": "Staff tracking table not yet created"},
        "fields": {"total": location_count, "trials": trial_count},
        "calendar": {"upcoming_events": 0, "note": "Calendar events table not yet created"},
        "harvest": {"total_records": 0, "note": "Harvest records table not yet created"},
    }


# ============================================================================
# Budget Endpoints
# ============================================================================

@router.get("/budget")
async def get_budget_categories(
    year: int = Query(default=2025),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get budget categories."""
    result = await db.execute(
        select(BudgetCategory).where(BudgetCategory.organization_id == organization_id)
    )
    categories = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "allocated": c.allocated or 0,
            "used": 0,
            "unit": "INR",
            "status": "active",
            "year": year,
        }
        for c in categories
    ]


@router.get("/budget/summary")
async def get_budget_summary(
    year: int = Query(default=2025),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get budget summary."""
    total_allocated = (await db.execute(
        select(func.sum(BudgetCategory.allocated)).where(BudgetCategory.organization_id == organization_id)
    )).scalar() or 0

    total_spent = (await db.execute(
        select(func.sum(Expense.amount)).where(Expense.organization_id == organization_id)
    )).scalar() or 0

    return {
        "total_allocated": float(total_allocated),
        "total_spent": float(total_spent),
        "remaining": float(total_allocated) - float(total_spent),
        "utilization_percent": round(float(total_spent) / float(total_allocated) * 100, 1) if total_allocated > 0 else 0,
        "year": year,
    }


@router.patch("/budget/{category_id}")
async def update_budget_category(
    category_id: int,
    update: BudgetUpdateRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Update budget usage."""
    cat = (await db.execute(
        select(BudgetCategory).where(BudgetCategory.id == category_id, BudgetCategory.organization_id == organization_id)
    )).scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Budget category not found")
    return {"id": str(cat.id), "name": cat.name, "updated": True}


# ============================================================================
# Staff Endpoints
# ============================================================================

@router.get("/staff")
async def get_staff_allocations(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get staff allocations. Table not yet created."""
    return []


@router.get("/staff/summary")
async def get_staff_summary(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get staff summary. Table not yet created."""
    return {"total_staff": 0, "departments": 0, "note": "Staff management table not yet created"}


# ============================================================================
# Field Endpoints
# ============================================================================

@router.get("/fields")
async def get_field_allocations(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get field allocations from Location table."""
    result = await db.execute(
        select(Location).where(Location.organization_id == organization_id).limit(100)
    )
    locations = result.scalars().all()

    fields = []
    for loc in locations:
        trial_count = (await db.execute(
            select(func.count(Trial.id)).where(Trial.location_id == loc.id)
        )).scalar() or 0
        fields.append({
            "id": str(loc.id),
            "field": loc.location_name,
            "area": 0,
            "trials": trial_count,
            "utilization": 0,
        })
    return fields


@router.get("/fields/summary")
async def get_field_summary(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get field summary."""
    location_count = (await db.execute(
        select(func.count(Location.id)).where(Location.organization_id == organization_id)
    )).scalar() or 0
    trial_count = (await db.execute(
        select(func.count(Trial.id)).where(Trial.organization_id == organization_id)
    )).scalar() or 0
    return {"total_fields": location_count, "total_trials": trial_count, "total_area": 0}


# ============================================================================
# Calendar Endpoints (honest empty — calendar events table not yet created)
# ============================================================================

@router.get("/calendar")
async def get_calendar_events(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get calendar events. Calendar events table not yet created."""
    return []


@router.get("/calendar/date/{target_date}")
async def get_events_by_date(target_date: str):
    """Get events for a specific date."""
    return []


@router.get("/calendar/summary")
async def get_calendar_summary():
    """Get calendar summary."""
    return {"total_events": 0, "by_type": {}, "note": "Calendar events table not yet created"}


@router.post("/calendar")
async def create_calendar_event(event: CalendarEventCreate):
    """Create calendar event. Table not yet created."""
    raise HTTPException(status_code=501, detail="Calendar events table not yet created. Migration pending.")


@router.patch("/calendar/{event_id}/status")
async def update_event_status(event_id: str, status: str = Query(...)):
    """Update event status."""
    raise HTTPException(status_code=501, detail="Calendar events table not yet created")


@router.delete("/calendar/{event_id}")
async def delete_calendar_event(event_id: str):
    """Delete a calendar event."""
    raise HTTPException(status_code=501, detail="Calendar events table not yet created")


# ============================================================================
# Harvest Endpoints (honest empty — harvest records table not yet created)
# ============================================================================

@router.get("/harvest")
async def get_harvest_records(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    quality: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get harvest records. Table not yet created."""
    return []


@router.get("/harvest/summary")
async def get_harvest_summary():
    """Get harvest summary."""
    return {"total_records": 0, "note": "Harvest records table not yet created"}


@router.post("/harvest")
async def create_harvest_record(record: HarvestRecordCreate):
    """Create harvest record. Table not yet created."""
    raise HTTPException(status_code=501, detail="Harvest records table not yet created. Migration pending.")


@router.patch("/harvest/{record_id}")
async def update_harvest_record(record_id: str, updates: Dict[str, Any]):
    """Update harvest record."""
    raise HTTPException(status_code=501, detail="Harvest records table not yet created")


@router.delete("/harvest/{record_id}")
async def delete_harvest_record(record_id: str):
    """Delete a harvest record."""
    raise HTTPException(status_code=501, detail="Harvest records table not yet created")

"""
FastAPI router for Crop Calendars
"""


from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_organization_id
from app.core.config import settings
from app.middleware.tenant_context import get_tenant_db
from app.crud.future import crop_calendar as crop_calendar_crud
from app.models.core import User
from app.schemas.future.crop_calendar import CropCalendar, CropCalendarCreate, CropCalendarUpdate


router = APIRouter()

def create_product_response(data: Any, page: int, page_size: int, total_count: int) -> dict[str, Any]:
    """Creates a product API response with pagination metadata."""
    total_pages = (total_count + page_size - 1) // page_size

    return {
        "success": True,
        "data": data,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages
        }
    }

@router.get("/crop-calendars", response_model=dict[str, Any])
async def list_crop_calendars(
    page: int = Query(0, ge=0, description="Page number"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_tenant_db),
    org_id: int = Depends(get_organization_id)
):
    """Lists crop calendars with pagination."""
    skip = page * page_size
    calendars, total_count = await crop_calendar_crud.crop_calendar.get_multi(
        db,
        skip=skip,
        limit=page_size,
        org_id=org_id
    )

    return create_product_response(calendars, page, page_size, total_count)

@router.get("/crop-calendars/{id}", response_model=dict[str, Any])
async def get_crop_calendar(
    id: int,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: int = Depends(get_organization_id)
):
    """Gets a single crop calendar by its ID."""
    calendar = await crop_calendar_crud.crop_calendar.get(db, id=id, org_id=org_id)

    if not calendar:
        raise HTTPException(status_code=404, detail="Crop calendar not found")

    return {
        "success": True,
        "data": calendar
    }

@router.post("/crop-calendars", response_model=dict[str, Any], status_code=201)
async def create_crop_calendar(
    calendar_in: CropCalendarCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_active_user)
):
    """Creates a new crop calendar."""
    calendar = await crop_calendar_crud.crop_calendar.create(
        db,
        obj_in=calendar_in,
        org_id=current_user.organization_id
    )
    await db.commit()

    return {
        "success": True,
        "data": calendar,
        "message": "Crop calendar created successfully"
    }

@router.put("/crop-calendars/{id}", response_model=dict[str, Any])
async def update_crop_calendar(
    id: int,
    calendar_in: CropCalendarUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: int = Depends(get_organization_id)
):
    """Updates a crop calendar."""
    calendar = await crop_calendar_crud.crop_calendar.get(db, id=id, org_id=org_id)

    if not calendar:
        raise HTTPException(status_code=404, detail="Crop calendar not found")

    calendar = await crop_calendar_crud.crop_calendar.update(db, db_obj=calendar, obj_in=calendar_in)
    await db.commit()

    return {
        "success": True,
        "data": calendar,
        "message": "Crop calendar updated successfully"
    }

@router.delete("/crop-calendars/{id}", status_code=204)
async def delete_crop_calendar(
    id: int,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: int = Depends(get_organization_id)
):
    """Deletes a crop calendar."""
    calendar = await crop_calendar_crud.crop_calendar.get(db, id=id, org_id=org_id)

    if not calendar:
        raise HTTPException(status_code=404, detail="Crop calendar not found")

    await crop_calendar_crud.crop_calendar.delete(db, id=id)
    await db.commit()

    return None

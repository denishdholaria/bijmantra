
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.core import User
from app.modules.crop_calendar.schemas import (
    ActivityTypeCreate,
    ActivityTypeResponse,
    ActivityTypeUpdate,
    CropCalendarCreate,
    CropCalendarResponse,
    CropCalendarUpdate,
    GrowthStageCreate,
    GrowthStageResponse,
    GrowthStageUpdate,
    HarvestWindowCreate,
    HarvestWindowResponse,
    HarvestWindowUpdate,
    ResourceRequirementCreate,
    ResourceRequirementResponse,
    ResourceRequirementUpdate,
    ScheduleEventCreate,
    ScheduleEventResponse,
    ScheduleEventUpdate,
)
from app.modules.crop_calendar.service import CropCalendarService


router = APIRouter(prefix="/crop-calendar", tags=["Crop Calendar"])

# Helper to get service
def get_service(db: AsyncSession = Depends(get_db)) -> CropCalendarService:
    return CropCalendarService(db)

# ==========================
# ActivityType Endpoints
# ==========================
@router.post("/activity-types", response_model=ActivityTypeResponse)
async def create_activity_type(
    data: ActivityTypeCreate,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return await service.create_activity_type(data, current_user.organization_id)

@router.get("/activity-types", response_model=list[ActivityTypeResponse])
async def list_activity_types(
    skip: int = 0,
    limit: int = 100,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return await service.list_activity_types(current_user.organization_id, skip, limit)

@router.get("/activity-types/{id}", response_model=ActivityTypeResponse)
async def get_activity_type(
    id: int,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    item = await service.get_activity_type(id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Activity Type not found")
    return item

@router.put("/activity-types/{id}", response_model=ActivityTypeResponse)
async def update_activity_type(
    id: int,
    data: ActivityTypeUpdate,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    item = await service.update_activity_type(id, data, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Activity Type not found")
    return item

@router.delete("/activity-types/{id}")
async def delete_activity_type(
    id: int,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    success = await service.delete_activity_type(id, current_user.organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="Activity Type not found")
    return {"message": "Activity Type deleted"}

# ==========================
# GrowthStage Endpoints
# ==========================
@router.post("/growth-stages", response_model=GrowthStageResponse)
async def create_growth_stage(
    data: GrowthStageCreate,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return await service.create_growth_stage(data, current_user.organization_id)

@router.get("/growth-stages", response_model=list[GrowthStageResponse])
async def list_growth_stages(
    crop_id: str | None = None,
    skip: int = 0,
    limit: int = 100,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return await service.list_growth_stages(current_user.organization_id, crop_id, skip, limit)

@router.get("/growth-stages/{id}", response_model=GrowthStageResponse)
async def get_growth_stage(
    id: int,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    item = await service.get_growth_stage(id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Growth Stage not found")
    return item

@router.put("/growth-stages/{id}", response_model=GrowthStageResponse)
async def update_growth_stage(
    id: int,
    data: GrowthStageUpdate,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    item = await service.update_growth_stage(id, data, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Growth Stage not found")
    return item

@router.delete("/growth-stages/{id}")
async def delete_growth_stage(
    id: int,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    success = await service.delete_growth_stage(id, current_user.organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="Growth Stage not found")
    return {"message": "Growth Stage deleted"}

# ==========================
# CropCalendar Endpoints
# ==========================
@router.post("/calendars", response_model=CropCalendarResponse)
async def create_crop_calendar(
    data: CropCalendarCreate,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return await service.create_crop_calendar(data, current_user.organization_id)

@router.get("/calendars", response_model=list[CropCalendarResponse])
async def list_crop_calendars(
    skip: int = 0,
    limit: int = 100,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return await service.list_crop_calendars(current_user.organization_id, skip, limit)

@router.get("/calendars/{id}", response_model=CropCalendarResponse)
async def get_crop_calendar(
    id: int,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    item = await service.get_crop_calendar(id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Crop Calendar not found")
    return item

@router.put("/calendars/{id}", response_model=CropCalendarResponse)
async def update_crop_calendar(
    id: int,
    data: CropCalendarUpdate,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    item = await service.update_crop_calendar(id, data, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Crop Calendar not found")
    return item

@router.delete("/calendars/{id}")
async def delete_crop_calendar(
    id: int,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    success = await service.delete_crop_calendar(id, current_user.organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="Crop Calendar not found")
    return {"message": "Crop Calendar deleted"}

# ==========================
# ScheduleEvent Endpoints
# ==========================
@router.post("/events", response_model=ScheduleEventResponse)
async def create_schedule_event(
    data: ScheduleEventCreate,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    try:
        return await service.create_schedule_event(data, current_user.organization_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/events", response_model=list[ScheduleEventResponse])
async def list_schedule_events(
    calendar_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return await service.list_schedule_events(current_user.organization_id, calendar_id, skip, limit)

@router.get("/events/{id}", response_model=ScheduleEventResponse)
async def get_schedule_event(
    id: int,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    item = await service.get_schedule_event(id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Schedule Event not found")
    return item

@router.put("/events/{id}", response_model=ScheduleEventResponse)
async def update_schedule_event(
    id: int,
    data: ScheduleEventUpdate,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    item = await service.update_schedule_event(id, data, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Schedule Event not found")
    return item

@router.delete("/events/{id}")
async def delete_schedule_event(
    id: int,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    success = await service.delete_schedule_event(id, current_user.organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule Event not found")
    return {"message": "Schedule Event deleted"}

# ==========================
# ResourceRequirement Endpoints
# ==========================
@router.post("/events/{id}/resources", response_model=ResourceRequirementResponse)
async def add_resource_requirement(
    id: int,
    data: ResourceRequirementCreate,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    try:
        return await service.add_resource_requirement(id, data, current_user.organization_id)
    except ValueError as e:
         raise HTTPException(status_code=404, detail=str(e))

@router.get("/resources/{id}", response_model=ResourceRequirementResponse)
async def get_resource_requirement(
    id: int,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    item = await service.get_resource_requirement(id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Resource Requirement not found")
    return item

@router.get("/resources", response_model=list[ResourceRequirementResponse])
async def list_resource_requirements(
    event_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return await service.list_resource_requirements(current_user.organization_id, event_id, skip, limit)

@router.put("/resources/{id}", response_model=ResourceRequirementResponse)
async def update_resource_requirement(
    id: int,
    data: ResourceRequirementUpdate,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    item = await service.update_resource_requirement(id, data, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Resource Requirement not found")
    return item

@router.delete("/resources/{id}")
async def delete_resource_requirement(
    id: int,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    success = await service.delete_resource_requirement(id, current_user.organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resource Requirement not found")
    return {"message": "Resource Requirement deleted"}

# ==========================
# HarvestWindow Endpoints
# ==========================
@router.post("/harvest-windows", response_model=HarvestWindowResponse)
async def create_harvest_window(
    data: HarvestWindowCreate,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    try:
        return await service.add_harvest_window(data, current_user.organization_id)
    except ValueError as e:
         raise HTTPException(status_code=404, detail=str(e))

@router.get("/harvest-windows", response_model=list[HarvestWindowResponse])
async def list_harvest_windows(
    calendar_id: int | None = None,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return await service.list_harvest_windows(current_user.organization_id, calendar_id)

@router.get("/harvest-windows/{id}", response_model=HarvestWindowResponse)
async def get_harvest_window(
    id: int,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    item = await service.get_harvest_window(id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Harvest Window not found")
    return item

@router.put("/harvest-windows/{id}", response_model=HarvestWindowResponse)
async def update_harvest_window(
    id: int,
    data: HarvestWindowUpdate,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    item = await service.update_harvest_window(id, data, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Harvest Window not found")
    return item

@router.delete("/harvest-windows/{id}")
async def delete_harvest_window(
    id: int,
    service: CropCalendarService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    success = await service.delete_harvest_window(id, current_user.organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="Harvest Window not found")
    return {"message": "Harvest Window deleted"}

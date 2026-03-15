from datetime import date

from pydantic import BaseModel


# ActivityType
class ActivityTypeBase(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None

class ActivityTypeCreate(ActivityTypeBase):
    pass

class ActivityTypeUpdate(ActivityTypeBase):
    name: str | None = None

class ActivityTypeResponse(ActivityTypeBase):
    id: int
    organization_id: int

    model_config = {"from_attributes": True}

# GrowthStage
class GrowthStageBase(BaseModel):
    crop_id: str
    stage_name: str
    days_from_sowing: int
    description: str | None = None

class GrowthStageCreate(GrowthStageBase):
    pass

class GrowthStageUpdate(GrowthStageBase):
    crop_id: str | None = None
    stage_name: str | None = None
    days_from_sowing: int | None = None

class GrowthStageResponse(GrowthStageBase):
    id: int
    organization_id: int

    model_config = {"from_attributes": True}

# ResourceRequirement
class ResourceRequirementBase(BaseModel):
    resource_type: str
    resource_name: str
    quantity: float
    unit: str
    cost_estimate: float | None = None

class ResourceRequirementCreate(ResourceRequirementBase):
    pass

class ResourceRequirementUpdate(ResourceRequirementBase):
    resource_type: str | None = None
    resource_name: str | None = None
    quantity: float | None = None
    unit: str | None = None

class ResourceRequirementResponse(ResourceRequirementBase):
    id: int
    event_id: int
    organization_id: int

    model_config = {"from_attributes": True}

# ScheduleEvent
class ScheduleEventBase(BaseModel):
    activity_type_id: int | None = None
    activity_name: str
    scheduled_date: date
    completed_date: date | None = None
    status: str | None = "pending"
    notes: str | None = None

class ScheduleEventCreate(ScheduleEventBase):
    resource_requirements: list[ResourceRequirementCreate] | None = None
    calendar_id: int

class ScheduleEventUpdate(ScheduleEventBase):
    activity_name: str | None = None
    scheduled_date: date | None = None

class ScheduleEventResponse(ScheduleEventBase):
    id: int
    calendar_id: int
    organization_id: int
    resource_requirements: list[ResourceRequirementResponse] = []

    model_config = {"from_attributes": True}

# HarvestWindow
class HarvestWindowBase(BaseModel):
    window_start: date
    window_end: date
    predicted_yield: float | None = None
    unit: str | None = None
    confidence_level: float | None = None

class HarvestWindowCreate(HarvestWindowBase):
    calendar_id: int

class HarvestWindowUpdate(HarvestWindowBase):
    window_start: date | None = None
    window_end: date | None = None

class HarvestWindowResponse(HarvestWindowBase):
    id: int
    calendar_id: int
    organization_id: int

    model_config = {"from_attributes": True}

# CropCalendar
class CropCalendarBase(BaseModel):
    crop_id: str
    trial_id: str | None = None
    planting_date: date
    expected_harvest_date: date | None = None
    actual_harvest_date: date | None = None
    location_id: int | None = None
    location_name: str | None = None
    area_hectares: float | None = None
    status: str | None = "planned"
    notes: str | None = None

class CropCalendarCreate(CropCalendarBase):
    pass

class CropCalendarUpdate(CropCalendarBase):
    crop_id: str | None = None
    planting_date: date | None = None

class CropCalendarResponse(CropCalendarBase):
    id: int
    organization_id: int
    events: list[ScheduleEventResponse] = []
    harvest_windows: list[HarvestWindowResponse] = []

    model_config = {"from_attributes": True}

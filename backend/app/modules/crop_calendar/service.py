
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.crop_calendar.models import (
    ActivityType,
    CropCalendar,
    GrowthStage,
    HarvestWindow,
    ResourceRequirement,
    ScheduleEvent,
)
from app.modules.crop_calendar.schemas import (
    ActivityTypeCreate,
    ActivityTypeUpdate,
    CropCalendarCreate,
    CropCalendarUpdate,
    GrowthStageCreate,
    GrowthStageUpdate,
    HarvestWindowCreate,
    HarvestWindowUpdate,
    ResourceRequirementCreate,
    ResourceRequirementUpdate,
    ScheduleEventCreate,
    ScheduleEventUpdate,
)


class CropCalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==========================
    # ActivityType CRUD
    # ==========================
    async def create_activity_type(self, data: ActivityTypeCreate, organization_id: int) -> ActivityType:
        db_obj = ActivityType(**data.model_dump(), organization_id=organization_id)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_activity_type(self, activity_id: int, organization_id: int) -> ActivityType | None:
        query = select(ActivityType).where(
            ActivityType.id == activity_id,
            ActivityType.organization_id == organization_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_activity_types(self, organization_id: int, skip: int = 0, limit: int = 100) -> list[ActivityType]:
        query = select(ActivityType).where(
            ActivityType.organization_id == organization_id
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_activity_type(self, activity_id: int, data: ActivityTypeUpdate, organization_id: int) -> ActivityType | None:
        db_obj = await self.get_activity_type(activity_id, organization_id)
        if not db_obj:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_activity_type(self, activity_id: int, organization_id: int) -> bool:
        db_obj = await self.get_activity_type(activity_id, organization_id)
        if not db_obj:
            return False

        await self.db.delete(db_obj)
        await self.db.commit()
        return True

    # ==========================
    # GrowthStage CRUD
    # ==========================
    async def create_growth_stage(self, data: GrowthStageCreate, organization_id: int) -> GrowthStage:
        db_obj = GrowthStage(**data.model_dump(), organization_id=organization_id)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_growth_stage(self, stage_id: int, organization_id: int) -> GrowthStage | None:
        query = select(GrowthStage).where(
            GrowthStage.id == stage_id,
            GrowthStage.organization_id == organization_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_growth_stages(self, organization_id: int, crop_id: str | None = None, skip: int = 0, limit: int = 100) -> list[GrowthStage]:
        query = select(GrowthStage).where(
            GrowthStage.organization_id == organization_id
        )
        if crop_id:
            query = query.where(GrowthStage.crop_id == crop_id)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_growth_stage(self, stage_id: int, data: GrowthStageUpdate, organization_id: int) -> GrowthStage | None:
        db_obj = await self.get_growth_stage(stage_id, organization_id)
        if not db_obj:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_growth_stage(self, stage_id: int, organization_id: int) -> bool:
        db_obj = await self.get_growth_stage(stage_id, organization_id)
        if not db_obj:
            return False

        await self.db.delete(db_obj)
        await self.db.commit()
        return True

    # ==========================
    # CropCalendar CRUD
    # ==========================
    async def create_crop_calendar(self, data: CropCalendarCreate, organization_id: int) -> CropCalendar:
        db_obj = CropCalendar(**data.model_dump(), organization_id=organization_id)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_crop_calendar(self, calendar_id: int, organization_id: int) -> CropCalendar | None:
        query = select(CropCalendar).where(
            CropCalendar.id == calendar_id,
            CropCalendar.organization_id == organization_id
        ).options(
            selectinload(CropCalendar.events).selectinload(ScheduleEvent.resource_requirements),
            selectinload(CropCalendar.harvest_windows)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_crop_calendars(self, organization_id: int, skip: int = 0, limit: int = 100) -> list[CropCalendar]:
        query = select(CropCalendar).where(
            CropCalendar.organization_id == organization_id
        ).options(
            selectinload(CropCalendar.events).selectinload(ScheduleEvent.resource_requirements),
            selectinload(CropCalendar.harvest_windows)
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_crop_calendar(self, calendar_id: int, data: CropCalendarUpdate, organization_id: int) -> CropCalendar | None:
        db_obj = await self.get_crop_calendar(calendar_id, organization_id)
        if not db_obj:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_crop_calendar(self, calendar_id: int, organization_id: int) -> bool:
        db_obj = await self.get_crop_calendar(calendar_id, organization_id)
        if not db_obj:
            return False

        await self.db.delete(db_obj)
        await self.db.commit()
        return True

    # ==========================
    # ScheduleEvent CRUD
    # ==========================
    async def create_schedule_event(self, data: ScheduleEventCreate, organization_id: int) -> ScheduleEvent:
        # Check if calendar exists
        calendar = await self.get_crop_calendar(data.calendar_id, organization_id)
        if not calendar:
            raise ValueError(f"Crop Calendar {data.calendar_id} not found")

        event_data = data.model_dump(exclude={"resource_requirements"})
        db_obj = ScheduleEvent(**event_data, organization_id=organization_id)
        self.db.add(db_obj)
        await self.db.flush() # flush to get ID

        if data.resource_requirements:
            for res_data in data.resource_requirements:
                res_obj = ResourceRequirement(**res_data.model_dump(), event_id=db_obj.id, organization_id=organization_id)
                self.db.add(res_obj)

        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_schedule_event(self, event_id: int, organization_id: int) -> ScheduleEvent | None:
        query = select(ScheduleEvent).where(
            ScheduleEvent.id == event_id,
            ScheduleEvent.organization_id == organization_id
        ).options(selectinload(ScheduleEvent.resource_requirements))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_schedule_events(self, organization_id: int, calendar_id: int | None = None, skip: int = 0, limit: int = 100) -> list[ScheduleEvent]:
        query = select(ScheduleEvent).where(
            ScheduleEvent.organization_id == organization_id
        )
        if calendar_id:
            query = query.where(ScheduleEvent.calendar_id == calendar_id)

        query = query.options(selectinload(ScheduleEvent.resource_requirements)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_schedule_event(self, event_id: int, data: ScheduleEventUpdate, organization_id: int) -> ScheduleEvent | None:
        db_obj = await self.get_schedule_event(event_id, organization_id)
        if not db_obj:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_schedule_event(self, event_id: int, organization_id: int) -> bool:
        db_obj = await self.get_schedule_event(event_id, organization_id)
        if not db_obj:
            return False

        await self.db.delete(db_obj)
        await self.db.commit()
        return True

    # ==========================
    # ResourceRequirement CRUD
    # ==========================
    async def add_resource_requirement(self, event_id: int, data: ResourceRequirementCreate, organization_id: int) -> ResourceRequirement:
        event = await self.get_schedule_event(event_id, organization_id)
        if not event:
            raise ValueError(f"Schedule Event {event_id} not found")

        db_obj = ResourceRequirement(**data.model_dump(), event_id=event_id, organization_id=organization_id)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_resource_requirement(self, req_id: int, organization_id: int) -> ResourceRequirement | None:
        query = select(ResourceRequirement).where(
            ResourceRequirement.id == req_id,
            ResourceRequirement.organization_id == organization_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_resource_requirements(self, organization_id: int, event_id: int | None = None, skip: int = 0, limit: int = 100) -> list[ResourceRequirement]:
        query = select(ResourceRequirement).where(
            ResourceRequirement.organization_id == organization_id
        )
        if event_id:
            query = query.where(ResourceRequirement.event_id == event_id)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_resource_requirement(self, req_id: int, data: ResourceRequirementUpdate, organization_id: int) -> ResourceRequirement | None:
        db_obj = await self.get_resource_requirement(req_id, organization_id)
        if not db_obj:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_resource_requirement(self, req_id: int, organization_id: int) -> bool:
        db_obj = await self.get_resource_requirement(req_id, organization_id)
        if not db_obj:
            return False

        await self.db.delete(db_obj)
        await self.db.commit()
        return True

    # ==========================
    # HarvestWindow CRUD
    # ==========================
    async def add_harvest_window(self, data: HarvestWindowCreate, organization_id: int) -> HarvestWindow:
        calendar = await self.get_crop_calendar(data.calendar_id, organization_id)
        if not calendar:
             raise ValueError(f"Crop Calendar {data.calendar_id} not found")

        db_obj = HarvestWindow(**data.model_dump(), organization_id=organization_id)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def list_harvest_windows(self, organization_id: int, calendar_id: int | None = None) -> list[HarvestWindow]:
        query = select(HarvestWindow).where(
            HarvestWindow.organization_id == organization_id
        )
        if calendar_id:
            query = query.where(HarvestWindow.calendar_id == calendar_id)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_harvest_window(self, window_id: int, organization_id: int) -> HarvestWindow | None:
        query = select(HarvestWindow).where(
            HarvestWindow.id == window_id,
            HarvestWindow.organization_id == organization_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_harvest_window(self, window_id: int, data: HarvestWindowUpdate, organization_id: int) -> HarvestWindow | None:
        db_obj = await self.get_harvest_window(window_id, organization_id)
        if not db_obj:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_harvest_window(self, window_id: int, organization_id: int) -> bool:
        db_obj = await self.get_harvest_window(window_id, organization_id)
        if not db_obj:
            return False

        await self.db.delete(db_obj)
        await self.db.commit()
        return True

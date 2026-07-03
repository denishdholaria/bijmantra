from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ActivityType(BaseModel):
    """Reference table for types of farming activities"""
    __tablename__ = "activity_types"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100)) # e.g., "Field Prep", "Planting", "Harvest"

    # Relationships
    organization = relationship("Organization")


class GrowthStage(BaseModel):
    """Growth stages defined for a crop"""
    __tablename__ = "growth_stages"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    crop_id = Column(String(255), nullable=False, index=True) # Linking to crop identifier (string based for now to match service)
    stage_name = Column(String(255), nullable=False)
    days_from_sowing = Column(Integer, nullable=False)
    description = Column(Text)

    # Relationships
    organization = relationship("Organization")


class CropCalendar(BaseModel):
    """Represents a planting event or crop cycle"""
    __tablename__ = "crop_calendars"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    crop_id = Column(String(255), nullable=False, index=True) # crop type identifier
    trial_id = Column(String(255), index=True)

    planting_date = Column(Date, nullable=False)
    expected_harvest_date = Column(Date)
    actual_harvest_date = Column(Date)

    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    location_name = Column(String(255))

    area_hectares = Column(Float)
    status = Column(String(50), default="planned") # planned, active, completed, cancelled

    notes = Column(Text)

    # Relationships
    organization = relationship("Organization")
    location = relationship("Location")
    events = relationship("ScheduleEvent", back_populates="calendar", cascade="all, delete-orphan")
    harvest_windows = relationship("HarvestWindow", back_populates="calendar", cascade="all, delete-orphan")


class ScheduleEvent(BaseModel):
    """Specific event scheduled on the calendar"""
    __tablename__ = "schedule_events"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    calendar_id = Column(Integer, ForeignKey("crop_calendars.id"), nullable=False, index=True)
    activity_type_id = Column(Integer, ForeignKey("activity_types.id"), nullable=True)

    activity_name = Column(String(255), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    completed_date = Column(Date)
    status = Column(String(50), default="pending") # pending, completed, overdue, skipped, in_progress
    notes = Column(Text)

    # Relationships
    organization = relationship("Organization")
    calendar = relationship("CropCalendar", back_populates="events")
    activity_type = relationship("ActivityType")
    resource_requirements = relationship("ResourceRequirement", back_populates="event", cascade="all, delete-orphan")


class ResourceRequirement(BaseModel):
    """Resources required for a schedule event"""
    __tablename__ = "resource_requirements"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("schedule_events.id"), nullable=False, index=True)

    resource_type = Column(String(255), nullable=False)
    resource_name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    cost_estimate = Column(Float)

    # Relationships
    organization = relationship("Organization")
    event = relationship("ScheduleEvent", back_populates="resource_requirements")


class HarvestWindow(BaseModel):
    """Predicted harvest window"""
    __tablename__ = "harvest_windows"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    calendar_id = Column(Integer, ForeignKey("crop_calendars.id"), nullable=False, index=True)

    window_start = Column(Date, nullable=False)
    window_end = Column(Date, nullable=False)
    predicted_yield = Column(Float)
    unit = Column(String(50))
    confidence_level = Column(Float) # 0.0 to 1.0

    # Relationships
    organization = relationship("Organization")
    calendar = relationship("CropCalendar", back_populates="harvest_windows")

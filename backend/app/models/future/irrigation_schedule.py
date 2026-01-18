"""
Irrigation Schedule Model

Manages irrigation planning and tracking based on crop water requirements.

Scientific Basis:
    Crop Water Requirement (ETc) = ET0 × Kc
    
    Where:
    - ET0 = Reference evapotranspiration (mm/day)
    - Kc = Crop coefficient (varies by growth stage)
    
    Net Irrigation Requirement = ETc - Effective Rainfall - Soil Moisture Contribution

Common Crop Coefficients (Kc):
    - Initial stage: 0.3-0.5
    - Development: 0.7-0.85
    - Mid-season: 1.0-1.2
    - Late season: 0.6-0.8

Reference: FAO Irrigation and Drainage Paper 56
"""

from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Date, ForeignKey, Time,
    Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class IrrigationStatus(str, enum.Enum):
    """Irrigation schedule status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


class IrrigationSchedule(BaseModel):
    """
    Irrigation Schedule model for water management.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        field_id: Reference to field being irrigated
        crop_name: Crop being irrigated
        schedule_date: Planned irrigation date
        irrigation_method: Method (Drip, Sprinkler, Flood, etc.)
        water_requirement_mm: Calculated water need (mm)
        duration_minutes: Planned irrigation duration
        start_time: Scheduled start time
        actual_applied_mm: Actual water applied (mm)
        soil_moisture_before/after: Soil moisture readings (%)
        et_reference: Reference evapotranspiration (mm/day)
        crop_coefficient: Kc value for growth stage
        status: Schedule status (planned/in_progress/completed/canceled)
    """
    __tablename__ = "irrigation_schedules"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    field_id = Column(Integer, nullable=True, index=True)
    crop_name = Column(String(255), nullable=False)
    schedule_date = Column(Date, nullable=False, index=True)
    irrigation_method = Column(String(100))  # e.g., "Drip", "Sprinkler", "Flood"
    water_requirement_mm = Column(Float)
    duration_minutes = Column(Integer)
    start_time = Column(Time)
    actual_applied_mm = Column(Float)
    soil_moisture_before = Column(Float)
    soil_moisture_after = Column(Float)
    et_reference = Column(Float)  # Reference evapotranspiration
    crop_coefficient = Column(Float)
    status = Column(
        SQLEnum(IrrigationStatus, values_callable=lambda x: [e.value for e in x]),
        default=IrrigationStatus.PLANNED
    )
    notes = Column(Text)

    # Relationships
    organization = relationship("Organization")

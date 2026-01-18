"""
Water & Irrigation Schemas

Schemas for fields, water balance, irrigation scheduling, and soil moisture.

Scientific Formulas (preserved per scientific-documentation.md):

Crop Water Requirement (FAO-56):
    ETc = ET0 × Kc
    
    Where:
    - ETc = Crop evapotranspiration (mm/day)
    - ET0 = Reference evapotranspiration (mm/day)
    - Kc = Crop coefficient (varies by growth stage)

Net Irrigation Requirement:
    NIR = ETc - Effective Rainfall - Soil Moisture Contribution

Water Balance:
    ΔS = P + I - ET - R - D
    
    Where:
    - ΔS = Change in soil water storage
    - P = Precipitation
    - I = Irrigation
    - ET = Evapotranspiration
    - R = Runoff
    - D = Deep percolation

Common Crop Coefficients (Kc):
    - Initial: 0.3-0.5
    - Development: 0.7-0.85
    - Mid-season: 1.0-1.2
    - Late season: 0.6-0.8
"""

from datetime import date, datetime, time
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field as PydanticField, ConfigDict


class IrrigationStatus(str, Enum):
    """Irrigation schedule status."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


# ============= Field =============

class FieldBase(BaseModel):
    """Base schema for field."""
    name: str = PydanticField(..., max_length=255)
    description: Optional[str] = None
    location_id: Optional[int] = None
    area_hectares: Optional[float] = PydanticField(default=None, gt=0)


class FieldCreate(FieldBase):
    """Schema for creating field."""
    pass


class FieldUpdate(BaseModel):
    """Schema for updating field."""
    name: Optional[str] = None
    description: Optional[str] = None
    location_id: Optional[int] = None
    area_hectares: Optional[float] = None


class Field(FieldBase):
    """Field response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= Water Balance =============

class WaterBalanceBase(BaseModel):
    """
    Base schema for daily water balance.
    
    Water Balance Equation:
        ΔS = P + I - ET - R - D
    """
    field_id: int
    balance_date: date
    precipitation_mm: float = PydanticField(ge=0)
    irrigation_mm: float = PydanticField(ge=0)
    et_actual_mm: float = PydanticField(ge=0, description="Actual evapotranspiration")
    runoff_mm: float = PydanticField(ge=0)
    deep_percolation_mm: float = PydanticField(ge=0)
    soil_water_content_mm: float = PydanticField(ge=0)
    available_water_mm: float = PydanticField(ge=0)
    deficit_mm: float = PydanticField(ge=0)
    surplus_mm: float = PydanticField(ge=0)
    crop_name: Optional[str] = PydanticField(default=None, max_length=255)
    growth_stage: Optional[str] = PydanticField(default=None, max_length=100)


class WaterBalanceCreate(WaterBalanceBase):
    """Schema for creating water balance record."""
    pass


class WaterBalance(WaterBalanceBase):
    """Water balance response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= Irrigation Schedule =============

class IrrigationScheduleBase(BaseModel):
    """
    Base schema for irrigation schedule.
    
    Crop Water Requirement (FAO-56):
        ETc = ET0 × Kc
    
    Net Irrigation = ETc - Effective Rainfall - Soil Contribution
    """
    field_id: Optional[int] = None
    crop_name: str = PydanticField(..., max_length=255)
    schedule_date: date
    irrigation_method: Optional[str] = PydanticField(default=None, max_length=100)
    water_requirement_mm: Optional[float] = PydanticField(default=None, ge=0)
    duration_minutes: Optional[int] = PydanticField(default=None, ge=0)
    start_time: Optional[time] = None
    actual_applied_mm: Optional[float] = PydanticField(default=None, ge=0)
    soil_moisture_before: Optional[float] = PydanticField(default=None, ge=0, le=100, description="% VWC")
    soil_moisture_after: Optional[float] = PydanticField(default=None, ge=0, le=100, description="% VWC")
    et_reference: Optional[float] = PydanticField(default=None, ge=0, description="ET0 mm/day")
    crop_coefficient: Optional[float] = PydanticField(default=None, ge=0, le=2, description="Kc value")
    status: IrrigationStatus = IrrigationStatus.PLANNED
    notes: Optional[str] = None


class IrrigationScheduleCreate(IrrigationScheduleBase):
    """Schema for creating irrigation schedule."""
    pass


class IrrigationScheduleUpdate(BaseModel):
    """Schema for updating irrigation schedule."""
    schedule_date: Optional[date] = None
    water_requirement_mm: Optional[float] = None
    duration_minutes: Optional[int] = None
    start_time: Optional[time] = None
    actual_applied_mm: Optional[float] = None
    soil_moisture_before: Optional[float] = None
    soil_moisture_after: Optional[float] = None
    status: Optional[IrrigationStatus] = None
    notes: Optional[str] = None


class IrrigationSchedule(IrrigationScheduleBase):
    """Irrigation schedule response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= Soil Moisture Reading =============

class SoilMoistureReadingBase(BaseModel):
    """Base schema for soil moisture sensor reading."""
    device_id: int
    field_id: Optional[int] = None
    reading_timestamp: datetime
    depth_cm: float = PydanticField(gt=0)
    volumetric_water_content: float = PydanticField(ge=0, le=1, description="VWC as decimal 0-1")
    soil_temperature_c: Optional[float] = None
    electrical_conductivity: Optional[float] = PydanticField(default=None, ge=0, description="dS/m")
    sensor_type: str = PydanticField(default="soil_moisture", max_length=50)
    lat: Optional[float] = PydanticField(default=None, ge=-90, le=90)
    lon: Optional[float] = PydanticField(default=None, ge=-180, le=180)
    battery_level: Optional[int] = PydanticField(default=None, ge=0, le=100)
    signal_strength: Optional[int] = None


class SoilMoistureReadingCreate(SoilMoistureReadingBase):
    """Schema for creating soil moisture reading."""
    pass


class SoilMoistureReading(SoilMoistureReadingBase):
    """Soil moisture reading response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

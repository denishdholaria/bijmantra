"""
Crop Intelligence Schemas

Schemas for GDD tracking, crop calendars, suitability, and yield prediction.

Scientific Formulas (preserved per scientific-documentation.md):

GDD Calculation:
    GDD = max(0, (Tmax + Tmin) / 2 - Tbase)

    Where:
    - Tmax = Daily maximum temperature (°C)
    - Tmin = Daily minimum temperature (°C)
    - Tbase = Base temperature (crop-specific)

Common Base Temperatures:
    - Corn/Maize: 10°C
    - Wheat: 0°C
    - Rice: 10°C
    - Cotton: 15.5°C
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============= Growing Degree Day Log =============

class GrowingDegreeDayLogBase(BaseModel):
    """
    Base schema for GDD log.

    GDD Formula: GDD = max(0, (Tmax + Tmin) / 2 - Tbase)
    """
    field_id: int | None = None
    crop_name: str = Field(..., max_length=100)
    planting_date: date
    log_date: date
    daily_gdd: float = Field(..., ge=0, description="GDD accumulated on this day (≥0)")
    cumulative_gdd: float = Field(..., ge=0, description="Total GDD since planting")
    base_temperature: float = Field(default=10.0, description="Base temperature in °C")
    max_temperature: float | None = Field(None, description="Daily max temp °C")
    min_temperature: float | None = Field(None, description="Daily min temp °C")
    growth_stage: str | None = Field(None, max_length=100)


class GrowingDegreeDayLogCreate(GrowingDegreeDayLogBase):
    """Schema for creating GDD log entry."""
    pass


class GrowingDegreeDayLogUpdate(BaseModel):
    """Schema for updating GDD log entry."""
    daily_gdd: float | None = Field(None, ge=0)
    cumulative_gdd: float | None = Field(None, ge=0)
    growth_stage: str | None = None


class GrowingDegreeDayLog(GrowingDegreeDayLogBase):
    """GDD log response schema."""
    id: int
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Crop Calendar =============

class CropCalendarBase(BaseModel):
    """Base schema for crop calendar."""
    crop_name: str = Field(..., max_length=255)
    region: str | None = Field(None, max_length=255)
    planting_window_start: date | None = None
    planting_window_end: date | None = None
    harvest_window_start: date | None = None
    harvest_window_end: date | None = None
    growing_degree_days: int | None = Field(None, description="Total GDD to maturity")
    notes: str | None = None


class CropCalendarCreate(CropCalendarBase):
    """Schema for creating crop calendar."""
    pass


class CropCalendarUpdate(BaseModel):
    """Schema for updating crop calendar."""
    crop_name: str | None = None
    region: str | None = None
    planting_window_start: date | None = None
    planting_window_end: date | None = None
    harvest_window_start: date | None = None
    harvest_window_end: date | None = None
    growing_degree_days: int | None = None
    notes: str | None = None


class CropCalendar(CropCalendarBase):
    """Crop calendar response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Crop Suitability =============

class CropSuitabilityBase(BaseModel):
    """
    Base schema for crop suitability assessment.

    FAO Land Evaluation Framework:
    - S1 (Highly Suitable): 80-100%
    - S2 (Moderately Suitable): 60-80%
    - S3 (Marginally Suitable): 40-60%
    - N1 (Currently Not Suitable): 20-40%
    - N2 (Permanently Not Suitable): 0-20%
    """
    location_id: int
    crop_name: str = Field(..., max_length=255)
    variety: str | None = Field(None, max_length=255)
    suitability_class: str = Field(..., max_length=10, description="S1, S2, S3, N1, N2")
    suitability_score: float = Field(..., ge=0, le=100)
    climate_score: float | None = Field(None, ge=0, le=100)
    soil_score: float | None = Field(None, ge=0, le=100)
    terrain_score: float | None = Field(None, ge=0, le=100)
    water_score: float | None = Field(None, ge=0, le=100)
    limiting_factors: list[str] | None = None
    recommendations: list[str] | None = None
    assessment_method: str | None = Field(None, max_length=100)
    confidence_level: float | None = Field(None, ge=0, le=1)
    notes: str | None = None


class CropSuitabilityCreate(CropSuitabilityBase):
    """Schema for creating crop suitability assessment."""
    pass


class CropSuitability(CropSuitabilityBase):
    """Crop suitability response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Yield Prediction =============

class YieldPredictionBase(BaseModel):
    """
    Base schema for yield prediction.

    Prediction Methods:
    - Statistical: Historical yield regression
    - Process-based: Crop simulation (DSSAT, APSIM)
    - ML-based: Remote sensing + weather ML models
    - Hybrid: Combination approaches
    """
    field_id: int
    trial_id: int | None = None
    crop_name: str = Field(..., max_length=255)
    variety: str | None = Field(None, max_length=255)
    season: str = Field(..., max_length=50)
    predicted_yield: float
    yield_unit: str = Field(default="t/ha", max_length=50)
    prediction_date: date
    lower_bound: float | None = None
    upper_bound: float | None = None
    confidence_level: float = Field(default=0.95, ge=0, le=1)
    model_name: str = Field(..., max_length=100)
    model_version: str | None = Field(None, max_length=50)
    prediction_method: str | None = Field(None, max_length=50)
    weather_factors: dict[str, Any] | None = None
    soil_factors: dict[str, Any] | None = None
    management_factors: dict[str, Any] | None = None
    actual_yield: float | None = None
    prediction_error: float | None = None
    notes: str | None = None


class YieldPredictionCreate(YieldPredictionBase):
    """Schema for creating yield prediction."""
    pass


class YieldPrediction(YieldPredictionBase):
    """Yield prediction response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

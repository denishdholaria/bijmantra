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
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============= Growing Degree Day Log =============

class GrowingDegreeDayLogBase(BaseModel):
    """
    Base schema for GDD log.
    
    GDD Formula: GDD = max(0, (Tmax + Tmin) / 2 - Tbase)
    """
    field_id: Optional[int] = None
    crop_name: str = Field(..., max_length=100)
    planting_date: date
    log_date: date
    daily_gdd: float = Field(..., ge=0, description="GDD accumulated on this day (≥0)")
    cumulative_gdd: float = Field(..., ge=0, description="Total GDD since planting")
    base_temperature: float = Field(default=10.0, description="Base temperature in °C")
    max_temperature: Optional[float] = Field(None, description="Daily max temp °C")
    min_temperature: Optional[float] = Field(None, description="Daily min temp °C")
    growth_stage: Optional[str] = Field(None, max_length=100)


class GrowingDegreeDayLogCreate(GrowingDegreeDayLogBase):
    """Schema for creating GDD log entry."""
    pass


class GrowingDegreeDayLogUpdate(BaseModel):
    """Schema for updating GDD log entry."""
    daily_gdd: Optional[float] = Field(None, ge=0)
    cumulative_gdd: Optional[float] = Field(None, ge=0)
    growth_stage: Optional[str] = None


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
    region: Optional[str] = Field(None, max_length=255)
    planting_window_start: Optional[date] = None
    planting_window_end: Optional[date] = None
    harvest_window_start: Optional[date] = None
    harvest_window_end: Optional[date] = None
    growing_degree_days: Optional[int] = Field(None, description="Total GDD to maturity")
    notes: Optional[str] = None


class CropCalendarCreate(CropCalendarBase):
    """Schema for creating crop calendar."""
    pass


class CropCalendarUpdate(BaseModel):
    """Schema for updating crop calendar."""
    crop_name: Optional[str] = None
    region: Optional[str] = None
    planting_window_start: Optional[date] = None
    planting_window_end: Optional[date] = None
    harvest_window_start: Optional[date] = None
    harvest_window_end: Optional[date] = None
    growing_degree_days: Optional[int] = None
    notes: Optional[str] = None


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
    variety: Optional[str] = Field(None, max_length=255)
    suitability_class: str = Field(..., max_length=10, description="S1, S2, S3, N1, N2")
    suitability_score: float = Field(..., ge=0, le=100)
    climate_score: Optional[float] = Field(None, ge=0, le=100)
    soil_score: Optional[float] = Field(None, ge=0, le=100)
    terrain_score: Optional[float] = Field(None, ge=0, le=100)
    water_score: Optional[float] = Field(None, ge=0, le=100)
    limiting_factors: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    assessment_method: Optional[str] = Field(None, max_length=100)
    confidence_level: Optional[float] = Field(None, ge=0, le=1)
    notes: Optional[str] = None


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
    trial_id: Optional[int] = None
    crop_name: str = Field(..., max_length=255)
    variety: Optional[str] = Field(None, max_length=255)
    season: str = Field(..., max_length=50)
    predicted_yield: float
    yield_unit: str = Field(default="t/ha", max_length=50)
    prediction_date: date
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    confidence_level: float = Field(default=0.95, ge=0, le=1)
    model_name: str = Field(..., max_length=100)
    model_version: Optional[str] = Field(None, max_length=50)
    prediction_method: Optional[str] = Field(None, max_length=50)
    weather_factors: Optional[Dict[str, Any]] = None
    soil_factors: Optional[Dict[str, Any]] = None
    management_factors: Optional[Dict[str, Any]] = None
    actual_yield: Optional[float] = None
    prediction_error: Optional[float] = None
    notes: Optional[str] = None


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

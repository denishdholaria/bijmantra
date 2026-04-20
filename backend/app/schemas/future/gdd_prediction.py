"""
Pydantic schemas for GDD Prediction
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class GDDPredictionBase(BaseModel):
    """Base schema for GDD Prediction"""
    field_id: int | None = None
    crop_name: str
    prediction_date: date = Field(default_factory=date.today)
    target_stage: str
    predicted_date: date | None = None
    predicted_gdd: float | None = None
    confidence: float = 0.5
    notes: str | None = None


class GDDPredictionCreate(GDDPredictionBase):
    """Schema for creating GDD Prediction"""
    pass


class GDDPredictionUpdate(BaseModel):
    """Schema for updating GDD Prediction"""
    target_stage: str | None = None
    predicted_date: date | None = None
    predicted_gdd: float | None = None
    confidence: float | None = None
    notes: str | None = None


class GDDPredictionResponse(GDDPredictionBase):
    """Schema for GDD Prediction response"""
    id: int
    organization_id: int
    created_at: date  # Using date broadly, though model has datetime

    model_config = ConfigDict(from_attributes=True)

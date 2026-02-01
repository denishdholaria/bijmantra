"""
Pydantic schemas for GDD Prediction
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class GDDPredictionBase(BaseModel):
    """Base schema for GDD Prediction"""
    field_id: Optional[int] = None
    crop_name: str
    prediction_date: date = Field(default_factory=date.today)
    target_stage: str
    predicted_date: Optional[date] = None
    predicted_gdd: Optional[float] = None
    confidence: float = 0.5
    notes: Optional[str] = None


class GDDPredictionCreate(GDDPredictionBase):
    """Schema for creating GDD Prediction"""
    pass


class GDDPredictionUpdate(BaseModel):
    """Schema for updating GDD Prediction"""
    target_stage: Optional[str] = None
    predicted_date: Optional[date] = None
    predicted_gdd: Optional[float] = None
    confidence: Optional[float] = None
    notes: Optional[str] = None


class GDDPredictionResponse(GDDPredictionBase):
    """Schema for GDD Prediction response"""
    id: int
    organization_id: int
    created_at: date  # Using date broadly, though model has datetime

    model_config = ConfigDict(from_attributes=True)

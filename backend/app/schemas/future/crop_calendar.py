"""
Pydantic schemas for Crop Calendar
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, ConfigDict, Field

# Base schema for common fields
class CropCalendarBase(BaseModel):
    """Base crop calendar schema"""
    crop_name: str = Field(..., alias="cropName")
    planting_date: Optional[date] = Field(None, alias="plantingDate")
    harvest_date: Optional[date] = Field(None, alias="harvestDate")

    model_config = ConfigDict(populate_by_name=True)

# Schema for creating a new crop calendar
class CropCalendarCreate(CropCalendarBase):
    """Schema for creating a crop calendar"""
    pass

# Schema for updating an existing crop calendar
class CropCalendarUpdate(BaseModel):
    """Schema for updating a crop calendar"""
    crop_name: Optional[str] = Field(None, alias="cropName")
    planting_date: Optional[date] = Field(None, alias="plantingDate")
    harvest_date: Optional[date] = Field(None, alias="harvestDate")

    model_config = ConfigDict(populate_by_name=True)


# Schema for the response model
class CropCalendar(CropCalendarBase):
    """Crop calendar response schema"""
    id: int
    organization_id: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

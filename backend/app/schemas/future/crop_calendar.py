"""
Pydantic schemas for Crop Calendar
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


# Base schema for common fields
class CropCalendarBase(BaseModel):
    """Base crop calendar schema"""
    crop_id: str = Field(..., alias="cropId")
    planting_date: date | None = Field(None, alias="plantingDate")
    expected_harvest_date: date | None = Field(None, alias="expectedHarvestDate")
    actual_harvest_date: date | None = Field(None, alias="actualHarvestDate")
    status: str | None = Field("planned", alias="status")

    model_config = ConfigDict(populate_by_name=True)

# Schema for creating a new crop calendar
class CropCalendarCreate(CropCalendarBase):
    """Schema for creating a crop calendar"""
    pass

# Schema for updating an existing crop calendar
class CropCalendarUpdate(BaseModel):
    """Schema for updating a crop calendar"""
    crop_id: str | None = Field(None, alias="cropId")
    planting_date: date | None = Field(None, alias="plantingDate")
    expected_harvest_date: date | None = Field(None, alias="expectedHarvestDate")
    actual_harvest_date: date | None = Field(None, alias="actualHarvestDate")
    status: str | None = Field(None, alias="status")

    model_config = ConfigDict(populate_by_name=True)


# Schema for the response model
class CropCalendar(CropCalendarBase):
    """Crop calendar response schema"""
    id: int
    organization_id: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

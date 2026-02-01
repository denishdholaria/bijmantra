from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- Protocol Schemas ---

class SpeedBreedingProtocolBase(BaseModel):
    name: str
    description: Optional[str] = None
    crop: str
    photoperiod: Optional[int] = Field(None, description="Hours of light")
    temperature_day: Optional[float] = None
    temperature_night: Optional[float] = None
    humidity: Optional[float] = None
    light_intensity: Optional[float] = None
    days_to_flower: Optional[int] = None
    days_to_harvest: Optional[int] = None
    generations_per_year: Optional[float] = None
    success_rate: Optional[float] = 0.95
    status: Optional[str] = "active"

class SpeedBreedingProtocolCreate(SpeedBreedingProtocolBase):
    pass

class SpeedBreedingProtocolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    crop: Optional[str] = None
    photoperiod: Optional[int] = None
    temperature_day: Optional[float] = None
    temperature_night: Optional[float] = None
    humidity: Optional[float] = None
    light_intensity: Optional[float] = None
    days_to_flower: Optional[int] = None
    days_to_harvest: Optional[int] = None
    generations_per_year: Optional[float] = None
    success_rate: Optional[float] = None
    status: Optional[str] = None

class SpeedBreedingProtocolResponse(SpeedBreedingProtocolBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Chamber Schemas ---

class SpeedBreedingChamberBase(BaseModel):
    name: str
    location: Optional[str] = None
    status: Optional[str] = "active"
    capacity: Optional[int] = 0
    current_temperature: Optional[float] = None
    current_humidity: Optional[float] = None
    current_light_hours: Optional[float] = None

class SpeedBreedingChamberCreate(SpeedBreedingChamberBase):
    pass

class SpeedBreedingChamberUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    capacity: Optional[int] = None
    current_temperature: Optional[float] = None
    current_humidity: Optional[float] = None
    current_light_hours: Optional[float] = None

class SpeedBreedingChamberResponse(SpeedBreedingChamberBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    occupied: Optional[int] = 0 # Computed field
    batches: Optional[int] = 0 # Computed count

    class Config:
        from_attributes = True

# --- Batch Schemas ---

class SpeedBreedingBatchBase(BaseModel):
    name: str
    protocol_id: int
    chamber_id: Optional[int] = None
    generation: Optional[str] = None
    entries: Optional[int] = 0
    start_date: Optional[str] = None
    expected_harvest: Optional[str] = None
    status: Optional[str] = "growing"
    progress: Optional[int] = 0

class SpeedBreedingBatchCreate(SpeedBreedingBatchBase):
    pass

class SpeedBreedingBatchUpdate(BaseModel):
    name: Optional[str] = None
    protocol_id: Optional[int] = None
    chamber_id: Optional[int] = None
    generation: Optional[str] = None
    entries: Optional[int] = None
    start_date: Optional[str] = None
    expected_harvest: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None

class SpeedBreedingBatchResponse(SpeedBreedingBatchBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    protocol_name: Optional[str] = None # For convenience
    chamber_name: Optional[str] = None # For convenience

    class Config:
        from_attributes = True

# --- Statistics Schema ---

class SpeedBreedingStatistics(BaseModel):
    total_protocols: int
    active_batches: int
    total_entries: int
    chambers_in_use: int
    crops: List[str]
    avg_generations_per_year: float
    avg_success_rate: float

# --- Timeline Request (moved from API) ---
class TimelineRequest(BaseModel):
    protocol_id: str
    target_generation: str
    start_date: Optional[str] = None

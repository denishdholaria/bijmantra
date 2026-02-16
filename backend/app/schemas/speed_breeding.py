from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Protocol Schemas ---

class SpeedBreedingProtocolBase(BaseModel):
    name: str
    description: str | None = None
    crop: str
    photoperiod: int | None = Field(None, description="Hours of light")
    temperature_day: float | None = None
    temperature_night: float | None = None
    humidity: float | None = None
    light_intensity: float | None = None
    days_to_flower: int | None = None
    days_to_harvest: int | None = None
    generations_per_year: float | None = None
    success_rate: float | None = 0.95
    status: str | None = "active"

class SpeedBreedingProtocolCreate(SpeedBreedingProtocolBase):
    pass

class SpeedBreedingProtocolUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    crop: str | None = None
    photoperiod: int | None = None
    temperature_day: float | None = None
    temperature_night: float | None = None
    humidity: float | None = None
    light_intensity: float | None = None
    days_to_flower: int | None = None
    days_to_harvest: int | None = None
    generations_per_year: float | None = None
    success_rate: float | None = None
    status: str | None = None

class SpeedBreedingProtocolResponse(SpeedBreedingProtocolBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Chamber Schemas ---

class SpeedBreedingChamberBase(BaseModel):
    name: str
    location: str | None = None
    status: str | None = "active"
    capacity: int | None = 0
    current_temperature: float | None = None
    current_humidity: float | None = None
    current_light_hours: float | None = None

class SpeedBreedingChamberCreate(SpeedBreedingChamberBase):
    pass

class SpeedBreedingChamberUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    status: str | None = None
    capacity: int | None = None
    current_temperature: float | None = None
    current_humidity: float | None = None
    current_light_hours: float | None = None

class SpeedBreedingChamberResponse(SpeedBreedingChamberBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    occupied: int | None = 0 # Computed field
    batches: int | None = 0 # Computed count

    model_config = ConfigDict(from_attributes=True)

# --- Batch Schemas ---

class SpeedBreedingBatchBase(BaseModel):
    name: str
    protocol_id: int
    chamber_id: int | None = None
    generation: str | None = None
    entries: int | None = 0
    start_date: str | None = None
    expected_harvest: str | None = None
    status: str | None = "growing"
    progress: int | None = 0

class SpeedBreedingBatchCreate(SpeedBreedingBatchBase):
    pass

class SpeedBreedingBatchUpdate(BaseModel):
    name: str | None = None
    protocol_id: int | None = None
    chamber_id: int | None = None
    generation: str | None = None
    entries: int | None = None
    start_date: str | None = None
    expected_harvest: str | None = None
    status: str | None = None
    progress: int | None = None

class SpeedBreedingBatchResponse(SpeedBreedingBatchBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    protocol_name: str | None = None # For convenience
    chamber_name: str | None = None # For convenience

    model_config = ConfigDict(from_attributes=True)

# --- Statistics Schema ---

class SpeedBreedingStatistics(BaseModel):
    total_protocols: int
    active_batches: int
    total_entries: int
    chambers_in_use: int
    crops: list[str]
    avg_generations_per_year: float
    avg_success_rate: float

class SpeedBreedingChamberStats(BaseModel):
    total_chambers: int
    active_chambers: int
    maintenance_chambers: int
    offline_chambers: int
    total_capacity: int
    used_capacity: int
    utilization_percentage: float

# --- Timeline Request (moved from API) ---
class TimelineRequest(BaseModel):
    protocol_id: str
    target_generation: str
    start_date: str | None = None

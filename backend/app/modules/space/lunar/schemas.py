from enum import Enum
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class FailureMode(str, Enum):
    ROOT_DISORIENTATION = "ROOT_DISORIENTATION"
    ANCHORAGE_FAILURE = "ANCHORAGE_FAILURE"
    PHOTOPERIOD_COLLAPSE = "PHOTOPERIOD_COLLAPSE"
    TRANSLOCATION_IMPAIRMENT = "TRANSLOCATION_IMPAIRMENT"
    MORPHOGENETIC_INSTABILITY = "MORPHOGENETIC_INSTABILITY"
    UNKNOWN = "UNKNOWN"

class LunarEnvironmentProfileBase(BaseModel):
    gravity_factor: float = Field(..., gt=0, le=0.3, description="0 < g <= 0.3")
    light_cycle_days: float = Field(..., ge=1, description=">= 1")
    dark_cycle_days: float = Field(..., ge=1, description=">= 1")
    habitat_pressure_kpa: float = Field(..., gt=0, description="> 0")
    o2_ppm: float = Field(..., ge=0, le=210000, description="0-210000")
    co2_ppm: float = Field(..., ge=0, description=">= 0")
    root_support_factor: float = Field(..., ge=0, le=1, description="0-1")

class LunarEnvironmentProfileCreate(LunarEnvironmentProfileBase):
    pass

class LunarEnvironmentProfileResponse(LunarEnvironmentProfileBase):
    id: UUID
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LunarTrialBase(BaseModel):
    environment_profile_id: UUID
    germplasm_id: int
    generation: int
    anchorage_score: float
    morphology_stability: float
    yield_index: float
    failure_mode: FailureMode
    notes: Optional[str] = None

class LunarTrialCreate(LunarTrialBase):
    pass

class LunarTrialResponse(LunarTrialBase):
    id: UUID
    organization_id: int

    model_config = ConfigDict(from_attributes=True)

class LunarSimulationRequest(BaseModel):
    environment_profile_id: UUID
    germplasm_id: int
    generation: int

class LunarSimulationResponse(BaseModel):
    anchorage_score: float
    morphology_stability: float
    yield_index: float
    failure_mode: FailureMode

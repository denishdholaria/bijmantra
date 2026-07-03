from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.mars import MarsFailureMode


# Environment Profile Schemas
class MarsEnvironmentProfileBase(BaseModel):
    pressure_kpa: float = Field(..., gt=0, description="Pressure in kPa")
    co2_ppm: float = Field(..., ge=0, description="CO2 concentration in ppm")
    o2_ppm: float = Field(..., ge=0, le=210000, description="O2 concentration in ppm")
    radiation_msv: float = Field(..., ge=0, description="Radiation in mSv")
    gravity_factor: float = Field(..., gt=0, le=1, description="Gravity factor (relative to Earth)")
    photoperiod_hours: float = Field(..., ge=0, le=24, description="Photoperiod in hours")
    temperature_profile: dict[str, Any] = Field(..., description="JSON profile for temperature")
    humidity_profile: dict[str, Any] = Field(..., description="JSON profile for humidity")

class MarsEnvironmentProfileCreate(MarsEnvironmentProfileBase):
    pass

class MarsEnvironmentProfileRead(MarsEnvironmentProfileBase):
    id: UUID
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Closed Loop Metrics Schemas
class MarsClosedLoopMetricRead(BaseModel):
    water_recycling_pct: float
    nutrient_loss_pct: float
    energy_input_kwh: float
    oxygen_output: float

    model_config = ConfigDict(from_attributes=True)

# Trial Schemas
class MarsTrialBase(BaseModel):
    germplasm_id: int
    environment_profile_id: UUID
    generation: int

class MarsTrialRead(MarsTrialBase):
    id: UUID
    organization_id: int
    survival_score: float
    biomass_yield: float
    failure_mode: MarsFailureMode
    notes: str | None = None
    created_at: datetime
    closed_loop_metrics: MarsClosedLoopMetricRead | None = None

    model_config = ConfigDict(from_attributes=True)

# Simulation Schemas
class SimulationRequest(BaseModel):
    environment_profile_id: UUID
    germplasm_id: int
    generation: int = Field(1, ge=1)

class SimulationResponse(BaseModel):
    trial_id: UUID
    survival_score: float
    biomass_yield: float
    failure_mode: MarsFailureMode
    closed_loop_metrics: MarsClosedLoopMetricRead

"""
Sadhana Simulation Protocol Schemas

Pydantic models corresponding to docs/schemas/simulation_protocol.json.
Used for validating and parsing simulation definitions.
"""
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import UUID4, BaseModel, Field


# Enums
class DomainType(StrEnum):
    MARS = "mars"
    GREENHOUSE = "greenhouse"
    OPEN_FIELD = "open_field"
    GROWTH_CHAMBER = "growth_chamber"
    VERTICAL_FARM = "vertical_farm"
    LUNAR = "lunar"
    CUSTOM = "custom"

class GrowthPhase(StrEnum):
    GERMINATION = "germination"
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    REPRODUCTIVE = "reproductive"
    MATURATION = "maturation"
    HARVEST = "harvest"
    CUSTOM = "custom"

class StressType(StrEnum):
    DROUGHT = "drought"
    HEAT = "heat"
    COLD = "cold"
    SALINITY = "salinity"
    RADIATION = "radiation"
    NUTRIENT_DEFICIENCY = "nutrient_deficiency"
    ATMOSPHERIC_PRESSURE = "atmospheric_pressure"
    LOW_GRAVITY = "low_gravity"
    HIGH_GRAVITY = "high_gravity"
    PATHOGEN = "pathogen"
    CUSTOM = "custom"

class MetricType(StrEnum):
    SURVIVAL_RATE = "survival_rate"
    BIOMASS_YIELD = "biomass_yield"
    HARVEST_INDEX = "harvest_index"
    WATER_USE_EFFICIENCY = "water_use_efficiency"
    ENERGY_INPUT = "energy_input"
    NUTRIENT_UPTAKE = "nutrient_uptake"
    DAYS_TO_MATURITY = "days_to_maturity"
    FAILURE_MODE = "failure_mode"
    CUSTOM = "custom"

class TerminationType(StrEnum):
    SURVIVAL_BELOW = "survival_below"
    RESOURCE_DEPLETED = "resource_depleted"
    TIME_EXCEEDED = "time_exceeded"
    METRIC_THRESHOLD = "metric_threshold"

# Component Models

class TemperatureProfile(BaseModel):
    unit: str = "celsius"
    day: float
    night: float
    variance: float | None = 0.0

class Photoperiod(BaseModel):
    light_hours: float
    dark_hours: float
    intensity_par: float | None = None

class Atmosphere(BaseModel):
    pressure_kpa: float | None = None
    co2_ppm: float | None = None
    o2_ppm: float | None = None

class Radiation(BaseModel):
    msv_per_day: float | None = None
    shielding_factor: float | None = None

class Gravity(BaseModel):
    factor: float = 1.0

class EnvironmentProfile(BaseModel):
    temperature: TemperatureProfile
    photoperiod: Photoperiod
    humidity: dict[str, float] | None = None
    atmosphere: Atmosphere | None = None
    radiation: Radiation | None = None
    gravity: Gravity | None = None
    custom_parameters: dict[str, Any] | None = None

class GermplasmEntry(BaseModel):
    germplasm_id: int
    germplasm_name: str | None = None
    quantity: int = Field(..., ge=1)
    generation: int | None = None
    traits: dict[str, float] | None = None
    stress_tolerance: dict[str, float] | None = None

class TimeStepDuration(BaseModel):
    value: float
    unit: str = "days"

class TimeStep(BaseModel):
    step_id: int = Field(..., ge=0)
    phase: GrowthPhase
    duration: TimeStepDuration
    environment_overrides: dict[str, Any] | None = None
    events: list[dict[str, Any]] | None = None

class StressFactor(BaseModel):
    type: StressType
    intensity: float = Field(..., ge=0, le=1)
    start_step: int
    end_step: int | None = None
    parameters: dict[str, Any] | None = None

class OutputMetric(BaseModel):
    name: str
    type: MetricType
    unit: str | None = None
    aggregation: str = "final"

class TerminationCondition(BaseModel):
    type: TerminationType
    threshold: float
    metric_name: str | None = None
    failure_mode: str | None = None

class SimulationInputs(BaseModel):
    environment: EnvironmentProfile
    germplasm: list[GermplasmEntry]
    resources: dict[str, Any] | None = None # Simplified for now
    initial_conditions: dict[str, Any] | None = None

class SimulationMetadata(BaseModel):
    name: str | None = None
    description: str | None = None
    author: str | None = None
    created_at: datetime | None = None
    organization_id: int | None = None
    tags: list[str] | None = None

class SimulationOutputs(BaseModel):
    metrics: list[OutputMetric]
    export_format: str = "json"
    include_time_series: bool = False

# Main Protocol Model
class SimulationProtocol(BaseModel):
    version: str
    simulation_id: UUID4
    domain: DomainType
    metadata: SimulationMetadata | None = None
    inputs: SimulationInputs
    time_steps: list[TimeStep]
    stress_factors: list[StressFactor] | None = None
    outputs: SimulationOutputs
    termination_conditions: list[TerminationCondition] | None = None

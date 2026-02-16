"""
Sadhana Simulation Protocol Schemas

Pydantic models corresponding to docs/schemas/simulation_protocol.json.
Used for validating and parsing simulation definitions.
"""
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, UUID4

# Enums
class DomainType(str, Enum):
    MARS = "mars"
    GREENHOUSE = "greenhouse"
    OPEN_FIELD = "open_field"
    GROWTH_CHAMBER = "growth_chamber"
    VERTICAL_FARM = "vertical_farm"
    LUNAR = "lunar"
    CUSTOM = "custom"

class GrowthPhase(str, Enum):
    GERMINATION = "germination"
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    REPRODUCTIVE = "reproductive"
    MATURATION = "maturation"
    HARVEST = "harvest"
    CUSTOM = "custom"

class StressType(str, Enum):
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

class MetricType(str, Enum):
    SURVIVAL_RATE = "survival_rate"
    BIOMASS_YIELD = "biomass_yield"
    HARVEST_INDEX = "harvest_index"
    WATER_USE_EFFICIENCY = "water_use_efficiency"
    ENERGY_INPUT = "energy_input"
    NUTRIENT_UPTAKE = "nutrient_uptake"
    DAYS_TO_MATURITY = "days_to_maturity"
    FAILURE_MODE = "failure_mode"
    CUSTOM = "custom"

class TerminationType(str, Enum):
    SURVIVAL_BELOW = "survival_below"
    RESOURCE_DEPLETED = "resource_depleted"
    TIME_EXCEEDED = "time_exceeded"
    METRIC_THRESHOLD = "metric_threshold"

# Component Models

class TemperatureProfile(BaseModel):
    unit: str = "celsius"
    day: float
    night: float
    variance: Optional[float] = 0.0

class Photoperiod(BaseModel):
    light_hours: float
    dark_hours: float
    intensity_par: Optional[float] = None

class Atmosphere(BaseModel):
    pressure_kpa: Optional[float] = None
    co2_ppm: Optional[float] = None
    o2_ppm: Optional[float] = None

class Radiation(BaseModel):
    msv_per_day: Optional[float] = None
    shielding_factor: Optional[float] = None

class Gravity(BaseModel):
    factor: float = 1.0

class EnvironmentProfile(BaseModel):
    temperature: TemperatureProfile
    photoperiod: Photoperiod
    humidity: Optional[Dict[str, float]] = None
    atmosphere: Optional[Atmosphere] = None
    radiation: Optional[Radiation] = None
    gravity: Optional[Gravity] = None
    custom_parameters: Optional[Dict[str, Any]] = None

class GermplasmEntry(BaseModel):
    germplasm_id: int
    germplasm_name: Optional[str] = None
    quantity: int = Field(..., ge=1)
    generation: Optional[int] = None
    traits: Optional[Dict[str, float]] = None
    stress_tolerance: Optional[Dict[str, float]] = None

class TimeStepDuration(BaseModel):
    value: float
    unit: str = "days"

class TimeStep(BaseModel):
    step_id: int = Field(..., ge=0)
    phase: GrowthPhase
    duration: TimeStepDuration
    environment_overrides: Optional[Dict[str, Any]] = None
    events: Optional[List[Dict[str, Any]]] = None

class StressFactor(BaseModel):
    type: StressType
    intensity: float = Field(..., ge=0, le=1)
    start_step: int
    end_step: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None

class OutputMetric(BaseModel):
    name: str
    type: MetricType
    unit: Optional[str] = None
    aggregation: str = "final"

class TerminationCondition(BaseModel):
    type: TerminationType
    threshold: float
    metric_name: Optional[str] = None
    failure_mode: Optional[str] = None

class SimulationInputs(BaseModel):
    environment: EnvironmentProfile
    germplasm: List[GermplasmEntry]
    resources: Optional[Dict[str, Any]] = None # Simplified for now
    initial_conditions: Optional[Dict[str, Any]] = None

class SimulationMetadata(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    organization_id: Optional[int] = None
    tags: Optional[List[str]] = None

class SimulationOutputs(BaseModel):
    metrics: List[OutputMetric]
    export_format: str = "json"
    include_time_series: bool = False

# Main Protocol Model
class SimulationProtocol(BaseModel):
    version: str
    simulation_id: UUID4
    domain: DomainType
    metadata: Optional[SimulationMetadata] = None
    inputs: SimulationInputs
    time_steps: List[TimeStep]
    stress_factors: Optional[List[StressFactor]] = None
    outputs: SimulationOutputs
    termination_conditions: Optional[List[TerminationCondition]] = None

"""
Crop Protection Schemas

Schemas for disease forecasting, spray applications, pest observations, and IPM strategies.

Scientific Context (preserved per scientific-documentation.md):

Disease Risk Models:
    - Late Blight (Blitecast, SIMCAST): Temperature + humidity + leaf wetness
    - Powdery Mildew: Temperature + relative humidity
    - Rust diseases: Degree-day accumulation models

Pest Severity Scale (0-10):
    - 0: No presence
    - 1-3: Low (below economic threshold)
    - 4-6: Moderate (approaching threshold)
    - 7-9: High (above threshold, action needed)
    - 10: Severe (crop loss imminent)

IPM Hierarchy:
    1. Prevention (cultural practices, resistant varieties)
    2. Monitoring (scouting, traps, thresholds)
    3. Biological control (natural enemies, biopesticides)
    4. Physical/mechanical control
    5. Chemical control (last resort)

Spray Compliance:
    - PHI: Pre-Harvest Interval (days)
    - REI: Re-Entry Interval (hours)
    - MRL: Maximum Residue Limits
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============= Disease Risk Forecast =============

class DiseaseRiskForecastBase(BaseModel):
    """
    Base schema for disease risk forecast.

    Risk models consider:
    - Weather (temperature, humidity, leaf wetness)
    - Crop growth stage
    - Historical disease pressure
    - Inoculum presence
    """
    location_id: int | None = None
    forecast_date: date
    valid_from: datetime
    valid_until: datetime
    disease_name: str = Field(..., max_length=255)
    crop_name: str = Field(..., max_length=255)
    risk_level: str = Field(..., max_length=50, description="Low, Medium, High")
    risk_score: float | None = Field(None, ge=0, le=1)
    contributing_factors: dict[str, Any] | None = None
    recommended_actions: list[str] | None = None
    model_name: str = Field(..., max_length=255)
    model_version: str = Field(..., max_length=50)


class DiseaseRiskForecastCreate(DiseaseRiskForecastBase):
    """Schema for creating disease risk forecast."""
    pass


class DiseaseRiskForecast(DiseaseRiskForecastBase):
    """Disease risk forecast response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Spray Application =============

class SprayApplicationBase(BaseModel):
    """
    Base schema for spray application record.

    Application Rate:
        Total Product = Rate/ha × Area (ha)
        Spray Volume = Water volume (L/ha) × Area (ha)

    Compliance Fields:
        - PHI: Pre-Harvest Interval (days)
        - REI: Re-Entry Interval (hours)
    """
    field_id: int | None = None
    application_date: date
    product_name: str = Field(..., max_length=255)
    product_type: str | None = Field(None, max_length=100)
    active_ingredient: str | None = Field(None, max_length=255)
    rate_per_ha: float | None = Field(None, ge=0)
    rate_unit: str | None = Field(None, max_length=50)
    total_area_ha: float | None = Field(None, ge=0)
    water_volume_l_ha: float | None = Field(None, ge=0)
    applicator_name: str | None = Field(None, max_length=255)
    equipment_used: str | None = Field(None, max_length=255)
    weather_conditions: dict[str, Any] | None = None
    target_pest: str | None = Field(None, max_length=255)
    pre_harvest_interval_days: int | None = Field(None, ge=0, description="PHI in days")
    re_entry_interval_hours: int | None = Field(None, ge=0, description="REI in hours")
    notes: str | None = None


class SprayApplicationCreate(SprayApplicationBase):
    """Schema for creating spray application."""
    pass


class SprayApplicationUpdate(BaseModel):
    """Schema for updating spray application."""
    application_date: date | None = None
    product_name: str | None = None
    rate_per_ha: float | None = None
    total_area_ha: float | None = None
    applicator_name: str | None = None
    notes: str | None = None


class SprayApplication(SprayApplicationBase):
    """Spray application response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Pest Observation =============

class PestObservationBase(BaseModel):
    """
    Base schema for pest scouting observation.

    Severity Scale (0-10):
        - 0: No presence
        - 1-3: Low (below economic threshold)
        - 4-6: Moderate (approaching threshold)
        - 7-9: High (above threshold)
        - 10: Severe (crop loss imminent)
    """
    field_id: int
    study_id: int | None = None
    observation_date: date
    observation_time: datetime | None = None
    observer_name: str | None = Field(None, max_length=255)
    pest_name: str = Field(..., max_length=255)
    pest_type: str = Field(..., max_length=50, description="insect, disease, weed, nematode")
    pest_stage: str | None = Field(None, max_length=100)
    crop_name: str = Field(..., max_length=255)
    growth_stage: str | None = Field(None, max_length=100)
    plant_part_affected: str | None = Field(None, max_length=100)
    severity_score: float | None = Field(None, ge=0, le=10)
    incidence_percent: float | None = Field(None, ge=0, le=100)
    count_per_plant: float | None = Field(None, ge=0)
    count_per_trap: float | None = Field(None, ge=0)
    area_affected_percent: float | None = Field(None, ge=0, le=100)
    sample_location: str | None = Field(None, max_length=100)
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    weather_conditions: dict[str, Any] | None = None
    image_urls: list[str] | None = None
    notes: str | None = None


class PestObservationCreate(PestObservationBase):
    """Schema for creating pest observation."""
    pass


class PestObservationUpdate(BaseModel):
    """Schema for updating pest observation."""

    field_id: int | None = None
    study_id: int | None = None
    observation_date: date | None = None
    observation_time: datetime | None = None
    observer_name: str | None = None
    pest_name: str | None = None
    pest_type: str | None = None
    pest_stage: str | None = None
    crop_name: str | None = None
    growth_stage: str | None = None
    plant_part_affected: str | None = None
    severity_score: float | None = Field(None, ge=0, le=10)
    incidence_percent: float | None = Field(None, ge=0, le=100)
    count_per_plant: float | None = Field(None, ge=0)
    count_per_trap: float | None = Field(None, ge=0)
    area_affected_percent: float | None = Field(None, ge=0, le=100)
    sample_location: str | None = None
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    weather_conditions: dict[str, Any] | None = None
    image_urls: list[str] | None = None
    notes: str | None = None


class PestObservation(PestObservationBase):
    """Pest observation response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= IPM Strategy =============

class IPMStrategyBase(BaseModel):
    """
    Base schema for Integrated Pest Management strategy.

    IPM Hierarchy:
        1. Prevention (cultural practices, resistant varieties)
        2. Monitoring (scouting, traps, thresholds)
        3. Biological control (natural enemies, biopesticides)
        4. Physical/mechanical control (traps, barriers)
        5. Chemical control (last resort, targeted)
    """
    field_id: int | None = None
    strategy_name: str = Field(..., max_length=255)
    crop_name: str = Field(..., max_length=255)
    target_pest: str = Field(..., max_length=255)
    pest_type: str | None = Field(None, max_length=50)
    economic_threshold: str | None = Field(None, max_length=255)
    action_threshold: str | None = Field(None, max_length=255)
    prevention_methods: list[str] | None = None
    monitoring_methods: list[str] | None = None
    biological_controls: list[str] | None = None
    physical_controls: list[str] | None = None
    chemical_controls: list[str] | None = None
    implementation_start: date | None = None
    implementation_end: date | None = None
    growth_stages: list[str] | None = None
    effectiveness_rating: float | None = Field(None, ge=0, le=100)
    cost_effectiveness: float | None = Field(None, ge=0)
    environmental_impact_score: float | None = Field(None, ge=0)
    notes: str | None = None


class IPMStrategyCreate(IPMStrategyBase):
    """Schema for creating IPM strategy."""
    pass


class IPMStrategyUpdate(BaseModel):
    """Schema for updating IPM strategy."""
    strategy_name: str | None = None
    economic_threshold: str | None = None
    action_threshold: str | None = None
    prevention_methods: list[str] | None = None
    monitoring_methods: list[str] | None = None
    biological_controls: list[str] | None = None
    physical_controls: list[str] | None = None
    chemical_controls: list[str] | None = None
    effectiveness_rating: float | None = None
    notes: str | None = None


class IPMStrategy(IPMStrategyBase):
    """IPM strategy response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

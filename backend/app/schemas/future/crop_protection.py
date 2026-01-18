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
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


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
    location_id: Optional[int] = None
    forecast_date: date
    valid_from: datetime
    valid_until: datetime
    disease_name: str = Field(..., max_length=255)
    crop_name: str = Field(..., max_length=255)
    risk_level: str = Field(..., max_length=50, description="Low, Medium, High")
    risk_score: Optional[float] = Field(None, ge=0, le=1)
    contributing_factors: Optional[Dict[str, Any]] = None
    recommended_actions: Optional[List[str]] = None
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
    field_id: Optional[int] = None
    application_date: date
    product_name: str = Field(..., max_length=255)
    product_type: Optional[str] = Field(None, max_length=100)
    active_ingredient: Optional[str] = Field(None, max_length=255)
    rate_per_ha: Optional[float] = Field(None, ge=0)
    rate_unit: Optional[str] = Field(None, max_length=50)
    total_area_ha: Optional[float] = Field(None, ge=0)
    water_volume_l_ha: Optional[float] = Field(None, ge=0)
    applicator_name: Optional[str] = Field(None, max_length=255)
    equipment_used: Optional[str] = Field(None, max_length=255)
    weather_conditions: Optional[Dict[str, Any]] = None
    target_pest: Optional[str] = Field(None, max_length=255)
    pre_harvest_interval_days: Optional[int] = Field(None, ge=0, description="PHI in days")
    re_entry_interval_hours: Optional[int] = Field(None, ge=0, description="REI in hours")
    notes: Optional[str] = None


class SprayApplicationCreate(SprayApplicationBase):
    """Schema for creating spray application."""
    pass


class SprayApplicationUpdate(BaseModel):
    """Schema for updating spray application."""
    application_date: Optional[date] = None
    product_name: Optional[str] = None
    rate_per_ha: Optional[float] = None
    total_area_ha: Optional[float] = None
    applicator_name: Optional[str] = None
    notes: Optional[str] = None


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
    study_id: Optional[int] = None
    observation_date: date
    observation_time: Optional[datetime] = None
    observer_name: Optional[str] = Field(None, max_length=255)
    pest_name: str = Field(..., max_length=255)
    pest_type: str = Field(..., max_length=50, description="insect, disease, weed, nematode")
    pest_stage: Optional[str] = Field(None, max_length=100)
    crop_name: str = Field(..., max_length=255)
    growth_stage: Optional[str] = Field(None, max_length=100)
    plant_part_affected: Optional[str] = Field(None, max_length=100)
    severity_score: Optional[float] = Field(None, ge=0, le=10)
    incidence_percent: Optional[float] = Field(None, ge=0, le=100)
    count_per_plant: Optional[float] = Field(None, ge=0)
    count_per_trap: Optional[float] = Field(None, ge=0)
    area_affected_percent: Optional[float] = Field(None, ge=0, le=100)
    sample_location: Optional[str] = Field(None, max_length=100)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    weather_conditions: Optional[Dict[str, Any]] = None
    image_urls: Optional[List[str]] = None
    notes: Optional[str] = None


class PestObservationCreate(PestObservationBase):
    """Schema for creating pest observation."""
    pass


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
    field_id: Optional[int] = None
    strategy_name: str = Field(..., max_length=255)
    crop_name: str = Field(..., max_length=255)
    target_pest: str = Field(..., max_length=255)
    pest_type: Optional[str] = Field(None, max_length=50)
    economic_threshold: Optional[str] = Field(None, max_length=255)
    action_threshold: Optional[str] = Field(None, max_length=255)
    prevention_methods: Optional[List[str]] = None
    monitoring_methods: Optional[List[str]] = None
    biological_controls: Optional[List[str]] = None
    physical_controls: Optional[List[str]] = None
    chemical_controls: Optional[List[str]] = None
    implementation_start: Optional[date] = None
    implementation_end: Optional[date] = None
    growth_stages: Optional[List[str]] = None
    effectiveness_rating: Optional[float] = Field(None, ge=0, le=100)
    cost_effectiveness: Optional[float] = Field(None, ge=0)
    environmental_impact_score: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class IPMStrategyCreate(IPMStrategyBase):
    """Schema for creating IPM strategy."""
    pass


class IPMStrategyUpdate(BaseModel):
    """Schema for updating IPM strategy."""
    strategy_name: Optional[str] = None
    economic_threshold: Optional[str] = None
    action_threshold: Optional[str] = None
    prevention_methods: Optional[List[str]] = None
    monitoring_methods: Optional[List[str]] = None
    biological_controls: Optional[List[str]] = None
    physical_controls: Optional[List[str]] = None
    chemical_controls: Optional[List[str]] = None
    effectiveness_rating: Optional[float] = None
    notes: Optional[str] = None


class IPMStrategy(IPMStrategyBase):
    """IPM strategy response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

"""
Soil & Nutrients Schemas

Schemas for soil testing, health scoring, fertilizer recommendations, and carbon sequestration.

Scientific Formulas (preserved per scientific-documentation.md):

Fertilizer Requirement:
    Nutrient requirement = (Target yield × Crop uptake) - Soil supply
    
    Where:
    - Target yield: Expected yield (t/ha)
    - Crop uptake: Nutrient removed per unit yield (kg/t)
    - Soil supply: Available nutrients from soil test

Fertilizer Use Efficiency:
    - Nitrogen: 40-60%
    - Phosphorus: 15-25%
    - Potassium: 50-70%

Soil Health Scoring (USDA NRCS):
    - 80-100: Excellent
    - 60-79: Good
    - 40-59: Fair
    - <40: Poor

Carbon Sequestration:
    Typical rates: 0.2-1.0 tonnes C/ha/year
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============= Soil Test =============

class SoilTestBase(BaseModel):
    """Base schema for soil test results."""
    field_id: Optional[int] = None
    sample_id: str = Field(..., max_length=255)
    sample_date: date
    lab_name: Optional[str] = Field(None, max_length=255)
    # Chemistry
    ph: Optional[float] = Field(None, ge=0, le=14)
    organic_matter_percent: Optional[float] = Field(None, ge=0, le=100)
    n_ppm: Optional[float] = Field(None, ge=0)
    p_ppm: Optional[float] = Field(None, ge=0)
    k_ppm: Optional[float] = Field(None, ge=0)
    ca_ppm: Optional[float] = Field(None, ge=0)
    mg_ppm: Optional[float] = Field(None, ge=0)
    s_ppm: Optional[float] = Field(None, ge=0)
    zn_ppm: Optional[float] = Field(None, ge=0)
    fe_ppm: Optional[float] = Field(None, ge=0)
    mn_ppm: Optional[float] = Field(None, ge=0)
    cu_ppm: Optional[float] = Field(None, ge=0)
    b_ppm: Optional[float] = Field(None, ge=0)
    cec: Optional[float] = Field(None, ge=0, description="Cation Exchange Capacity (meq/100g)")
    # Physics
    texture_class: Optional[str] = Field(None, max_length=100)
    sand_percent: Optional[float] = Field(None, ge=0, le=100)
    silt_percent: Optional[float] = Field(None, ge=0, le=100)
    clay_percent: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class SoilTestCreate(SoilTestBase):
    """Schema for creating soil test."""
    pass


class SoilTestUpdate(BaseModel):
    """Schema for updating soil test."""
    lab_name: Optional[str] = None
    ph: Optional[float] = None
    organic_matter_percent: Optional[float] = None
    notes: Optional[str] = None


class SoilTest(SoilTestBase):
    """Soil test response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= Soil Health Score =============

class SoilHealthScoreBase(BaseModel):
    """
    Base schema for soil health assessment.
    
    USDA NRCS Soil Health Framework:
    - Physical: Aggregate stability, infiltration, bulk density
    - Chemical: pH, organic carbon, CEC
    - Biological: Microbial biomass, respiration, earthworms
    
    Scoring (0-100):
    - 80-100: Excellent
    - 60-79: Good
    - 40-59: Fair
    - <40: Poor (needs intervention)
    """
    field_id: Optional[int] = None
    assessment_date: date
    overall_score: Optional[float] = Field(None, ge=0, le=100)
    physical_score: Optional[float] = Field(None, ge=0, le=100)
    chemical_score: Optional[float] = Field(None, ge=0, le=100)
    biological_score: Optional[float] = Field(None, ge=0, le=100)
    organic_carbon_percent: Optional[float] = Field(None, ge=0)
    aggregate_stability: Optional[float] = Field(None, ge=0, le=100, description="Water-stable aggregates %")
    water_infiltration_rate: Optional[float] = Field(None, ge=0, description="mm/hour")
    earthworm_count: Optional[int] = Field(None, ge=0, description="Per m²")
    microbial_biomass: Optional[float] = Field(None, ge=0, description="mg/kg")
    respiration_rate: Optional[float] = Field(None, ge=0, description="mg CO2/kg/day")
    recommendations: Optional[Dict[str, Any]] = None


class SoilHealthScoreCreate(SoilHealthScoreBase):
    """Schema for creating soil health score."""
    pass


class SoilHealthScore(SoilHealthScoreBase):
    """Soil health score response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= Fertilizer Recommendation =============

class FertilizerRecommendationBase(BaseModel):
    """
    Base schema for fertilizer recommendation.
    
    Nutrient Requirement Formula:
        Requirement = (Target yield × Crop uptake) - Soil supply
    
    Common Crop Uptake (kg/t grain):
        - Wheat: N=25, P2O5=10, K2O=20
        - Rice: N=20, P2O5=10, K2O=25
        - Corn: N=25, P2O5=10, K2O=20
    """
    soil_test_id: Optional[int] = None
    field_id: Optional[int] = None
    crop_name: str = Field(..., max_length=100)
    target_yield: float = Field(..., gt=0)
    yield_unit: str = Field(default="t/ha", max_length=20)
    n_kg_ha: float = Field(default=0.0, ge=0, description="Nitrogen kg/ha")
    p_kg_ha: float = Field(default=0.0, ge=0, description="P2O5 kg/ha")
    k_kg_ha: float = Field(default=0.0, ge=0, description="K2O kg/ha")
    s_kg_ha: Optional[float] = Field(default=0.0, ge=0, description="Sulfur kg/ha")
    zn_kg_ha: Optional[float] = Field(default=0.0, ge=0, description="Zinc kg/ha")
    application_timing: Optional[Dict[str, Any]] = Field(None, description="Split application schedule")
    estimated_cost: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(default="USD", max_length=3)
    recommendation_date: date
    valid_until: Optional[date] = None
    notes: Optional[str] = None


class FertilizerRecommendationCreate(FertilizerRecommendationBase):
    """Schema for creating fertilizer recommendation."""
    pass


class FertilizerRecommendation(FertilizerRecommendationBase):
    """Fertilizer recommendation response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    
    @property
    def total_npk_kg_ha(self) -> float:
        """Total NPK in kg/ha."""
        return self.n_kg_ha + self.p_kg_ha + self.k_kg_ha
    
    model_config = ConfigDict(from_attributes=True)


# ============= Carbon Sequestration =============

class CarbonSequestrationBase(BaseModel):
    """
    Base schema for carbon sequestration tracking.
    
    SOC Sequestration depends on:
    - Land management (tillage, cover crops, residue)
    - Climate and soil type
    - Baseline SOC levels
    
    Typical rates: 0.2-1.0 tonnes C/ha/year
    """
    field_id: Optional[int] = None
    measurement_date: date
    soil_organic_carbon_baseline: float = Field(..., ge=0, description="Baseline SOC %")
    soil_organic_carbon_current: float = Field(..., ge=0, description="Current SOC %")
    sequestration_rate: Optional[float] = Field(None, description="tonnes C/ha/year")
    measurement_depth_cm: int = Field(..., gt=0)
    methodology: Optional[str] = Field(None, max_length=255)
    verification_status: Optional[str] = Field(default="Pending", max_length=50)
    carbon_credits_potential: Optional[float] = Field(None, ge=0)
    practice_changes: Optional[Dict[str, Any]] = None


class CarbonSequestrationCreate(CarbonSequestrationBase):
    """Schema for creating carbon sequestration record."""
    pass


class CarbonSequestration(CarbonSequestrationBase):
    """Carbon sequestration response schema."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

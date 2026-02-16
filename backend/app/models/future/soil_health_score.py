"""
Soil Health Score Model

Comprehensive soil health assessment combining physical, chemical, and biological indicators.

Soil Health Framework (USDA NRCS):
    - Physical: Aggregate stability, water infiltration, bulk density
    - Chemical: pH, organic carbon, nutrient availability, CEC
    - Biological: Microbial biomass, respiration, earthworm count

Scoring typically on 0-100 scale:
    - 80-100: Excellent soil health
    - 60-79: Good soil health
    - 40-59: Fair soil health
    - <40: Poor soil health (needs intervention)

Reference: USDA Soil Health Assessment Framework
"""

from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Date, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SoilHealthScore(BaseModel):
    """
    Represents a soil health assessment for a specific field.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        field_id: Reference to assessed field/location
        assessment_date: Date of assessment
        overall_score: Composite soil health score (0-100)
        physical_score: Physical health component score
        chemical_score: Chemical health component score
        biological_score: Biological health component score
        organic_carbon_percent: Soil organic carbon (%)
        aggregate_stability: Water-stable aggregates (%)
        water_infiltration_rate: Infiltration rate (mm/hour)
        earthworm_count: Earthworms per m²
        microbial_biomass: Microbial biomass carbon (mg/kg)
        respiration_rate: Soil respiration (mg CO2/kg/day)
        recommendations: JSON with improvement recommendations
    """
    __tablename__ = "soil_health_scores"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    field_id = Column(Integer, nullable=True, index=True)

    assessment_date = Column(Date, nullable=False, default=date.today, index=True)

    # Overall and category scores (0-100 scale)
    overall_score = Column(Float, index=True)
    physical_score = Column(Float)
    chemical_score = Column(Float)
    biological_score = Column(Float)

    # Key indicators
    organic_carbon_percent = Column(Float)
    aggregate_stability = Column(Float)  # Percentage
    water_infiltration_rate = Column(Float)  # mm/hour
    earthworm_count = Column(Integer)  # Per square meter
    microbial_biomass = Column(Float)  # mg/kg
    respiration_rate = Column(Float)  # mg CO2/kg/day

    # Recommendations
    recommendations = Column(JSON)  # Structured recommendations

    # Relationships
    organization = relationship("Organization")

    def __repr__(self):
        return f"<SoilHealthScore(field_id='{self.field_id}', date='{self.assessment_date}', score='{self.overall_score}')>"

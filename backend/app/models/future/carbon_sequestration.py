"""
Carbon Sequestration Module Models

Tracks soil carbon data for carbon credit programs and sustainability metrics.

Scientific Basis:
    Soil Organic Carbon (SOC) sequestration rate depends on:
    - Land management practices (tillage, cover crops, residue management)
    - Climate and soil type
    - Baseline SOC levels
    
    Typical sequestration rates: 0.2-1.0 tonnes C/ha/year
"""

from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Float, Date
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class CarbonSequestration(BaseModel):
    """
    Carbon Sequestration model for tracking soil carbon data and credits.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        field_id: Reference to field/location
        measurement_date: Date of SOC measurement
        soil_organic_carbon_baseline: Initial SOC measurement (%)
        soil_organic_carbon_current: Current SOC measurement (%)
        sequestration_rate: Calculated rate (tonnes C/ha/year)
        measurement_depth_cm: Soil sampling depth
        methodology: Verification methodology used
        verification_status: Status of carbon credit verification
        carbon_credits_potential: Estimated carbon credits
        practice_changes: JSON of agricultural practice changes
    """

    __tablename__ = "carbon_sequestration"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("locations.id"), nullable=True, index=True)

    measurement_date = Column(Date, nullable=False)

    # Soil Organic Carbon (SOC) measurements
    soil_organic_carbon_baseline = Column(Float, nullable=False)
    soil_organic_carbon_current = Column(Float, nullable=False)

    # Sequestration metrics
    sequestration_rate = Column(Float)
    measurement_depth_cm = Column(Integer, nullable=False)

    # Verification and methodology
    methodology = Column(String(255))
    verification_status = Column(String(50), default="Pending")

    # Carbon credits
    carbon_credits_potential = Column(Float)

    # Agricultural practices
    practice_changes = Column(JSON)  # Changes in tilling, cover crops, etc.

    # Relationships
    organization = relationship("Organization")

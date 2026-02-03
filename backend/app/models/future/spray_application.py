"""
Spray Application Model

Records pesticide, herbicide, and fungicide applications for compliance and IPM tracking.

Key Compliance Fields:
    - Pre-Harvest Interval (PHI): Days before harvest when application is allowed
    - Re-Entry Interval (REI): Hours before workers can re-enter treated area
    - Maximum Residue Limits (MRL): Regulatory limits for residues on produce

Application Rate Calculations:
    Total Product = Rate per ha × Area (ha)
    Spray Volume = Water volume (L/ha) × Area (ha)
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    JSON,
    Float,
    Date,
)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SprayApplication(BaseModel):
    """
    Spray application record for pesticide/herbicide/fungicide tracking.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        field_id: Reference to treated field
        application_date: Date of application
        product_name: Commercial product name
        product_type: Category (Herbicide, Insecticide, Fungicide, etc.)
        active_ingredient: Active ingredient name
        rate_per_ha: Application rate per hectare
        rate_unit: Unit for rate (L, kg, g, etc.)
        total_area_ha: Total area treated
        water_volume_l_ha: Spray volume per hectare
        applicator_name: Person who applied
        equipment_used: Sprayer/equipment description
        weather_conditions: JSON with temp, wind, humidity
        target_pest: Target pest/disease/weed
        pre_harvest_interval_days: PHI in days
        re_entry_interval_hours: REI in hours
    """

    __tablename__ = "spray_applications"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    field_id = Column(Integer, nullable=True, index=True)
    application_date = Column(Date, nullable=False, index=True)
    product_name = Column(String(255), nullable=False, index=True)
    product_type = Column(String(100))
    active_ingredient = Column(String(255))
    rate_per_ha = Column(Float)
    rate_unit = Column(String(50))
    total_area_ha = Column(Float)
    water_volume_l_ha = Column(Float)
    applicator_name = Column(String(255))
    equipment_used = Column(String(255))
    weather_conditions = Column(JSON)
    target_pest = Column(String(255))
    pre_harvest_interval_days = Column(Integer)
    re_entry_interval_hours = Column(Integer)
    notes = Column(Text)

    # Relationships
    organization = relationship("Organization")

    def __repr__(self):
        return f"<SprayApplication(id={self.id}, product_name='{self.product_name}', application_date='{self.application_date}')>"

"""
Soil Test Model

Stores soil analysis results for nutrient management and fertilizer recommendations.

Key Soil Parameters:
    - pH: Soil acidity/alkalinity (optimal 6.0-7.0 for most crops)
    - Organic Matter: Indicator of soil health (target >3%)
    - CEC: Cation Exchange Capacity (nutrient holding capacity)
    - Macronutrients: N, P, K, Ca, Mg, S
    - Micronutrients: Zn, Fe, Mn, Cu, B
    - Texture: Sand/Silt/Clay percentages
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, Float
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SoilTest(BaseModel):
    """
    Soil Test model for storing laboratory analysis results.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        field_id: Reference to field where sample was taken
        sample_id: Unique sample identifier
        sample_date: Date sample was collected
        lab_name: Laboratory that performed analysis
        ph: Soil pH (0-14 scale)
        organic_matter_percent: Organic matter content (%)
        n_ppm to b_ppm: Nutrient concentrations (parts per million)
        cec: Cation Exchange Capacity (meq/100g)
        texture_class: USDA texture classification
        sand/silt/clay_percent: Particle size distribution
    """

    __tablename__ = "soil_tests"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    field_id = Column(Integer, nullable=True, index=True)
    sample_id = Column(String(255), unique=True, index=True, nullable=False)
    sample_date = Column(Date, nullable=False)
    lab_name = Column(String(255))

    # Soil Chemistry
    ph = Column(Float)
    organic_matter_percent = Column(Float)
    n_ppm = Column(Float)
    p_ppm = Column(Float)
    k_ppm = Column(Float)
    ca_ppm = Column(Float)
    mg_ppm = Column(Float)
    s_ppm = Column(Float)
    zn_ppm = Column(Float)
    fe_ppm = Column(Float)
    mn_ppm = Column(Float)
    cu_ppm = Column(Float)
    b_ppm = Column(Float)
    cec = Column(Float)

    # Soil Physics
    texture_class = Column(String(100))
    sand_percent = Column(Float)
    silt_percent = Column(Float)
    clay_percent = Column(Float)

    # Other
    notes = Column(Text)

    # Relationships
    organization = relationship("Organization")

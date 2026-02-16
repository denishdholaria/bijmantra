"""
IPM Strategy Model

Integrated Pest Management strategies combining biological, cultural,
physical, and chemical control methods.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, Text, Date
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class IPMStrategy(BaseModel):
    """
    Represents an Integrated Pest Management strategy for a crop/field.
    
    IPM follows the hierarchy:
    1. Prevention (cultural practices, resistant varieties)
    2. Monitoring (scouting, traps, thresholds)
    3. Biological control (natural enemies, biopesticides)
    4. Physical/mechanical control (traps, barriers)
    5. Chemical control (as last resort, targeted application)
    """
    __tablename__ = "ipm_strategies"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("locations.id"), nullable=True, index=True)

    strategy_name = Column(String(255), nullable=False)
    crop_name = Column(String(255), nullable=False, index=True)
    target_pest = Column(String(255), nullable=False, index=True)
    pest_type = Column(String(50))  # insect, disease, weed, nematode

    # Economic threshold
    economic_threshold = Column(String(255))  # e.g., "5 larvae per plant"
    action_threshold = Column(String(255))  # e.g., "10 larvae per plant"

    # Control methods (JSON arrays)
    prevention_methods = Column(JSON)  # Cultural practices
    monitoring_methods = Column(JSON)  # Scouting protocols
    biological_controls = Column(JSON)  # Natural enemies, biopesticides
    physical_controls = Column(JSON)  # Traps, barriers
    chemical_controls = Column(JSON)  # Pesticides (last resort)

    # Timing
    implementation_start = Column(Date)
    implementation_end = Column(Date)
    growth_stages = Column(JSON)  # Applicable growth stages

    # Effectiveness tracking
    effectiveness_rating = Column(Float)  # 0-100
    cost_effectiveness = Column(Float)  # Benefit/cost ratio
    environmental_impact_score = Column(Float)  # Lower is better

    notes = Column(Text)

    # Relationships
    organization = relationship("Organization")
    field = relationship("Location")

    def __repr__(self):
        return f"<IPMStrategy(crop={self.crop_name}, pest={self.target_pest})>"

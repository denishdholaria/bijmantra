"""
Pest Observation Model

Records pest scouting observations for IPM decision support.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, Text, DateTime, Date
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PestObservation(BaseModel):
    """
    Represents a pest scouting observation in the field.
    
    Severity scale (0-10):
    - 0: No pest presence
    - 1-3: Low (below economic threshold)
    - 4-6: Moderate (approaching threshold)
    - 7-9: High (above threshold, action needed)
    - 10: Severe (crop loss imminent)
    """
    __tablename__ = "pest_observations"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), nullable=True, index=True)

    # Observation details
    observation_date = Column(Date, nullable=False, index=True)
    observation_time = Column(DateTime(timezone=True))
    observer_name = Column(String(255))

    # Pest identification
    pest_name = Column(String(255), nullable=False, index=True)
    pest_type = Column(String(50), nullable=False)  # insect, disease, weed, nematode
    pest_stage = Column(String(100))  # e.g., "adult", "larva", "spore"
    
    # Crop context
    crop_name = Column(String(255), nullable=False)
    growth_stage = Column(String(100))
    plant_part_affected = Column(String(100))  # leaf, stem, root, fruit

    # Quantitative data
    severity_score = Column(Float)  # 0-10 scale
    incidence_percent = Column(Float)  # % of plants affected
    count_per_plant = Column(Float)  # Average count per plant
    count_per_trap = Column(Float)  # For trap-based monitoring
    area_affected_percent = Column(Float)  # % of field affected

    # Location within field
    sample_location = Column(String(100))  # e.g., "NE corner", "center"
    lat = Column(Float)
    lon = Column(Float)
    
    # Environmental conditions
    weather_conditions = Column(JSON)  # Temperature, humidity, etc.

    # Evidence
    image_urls = Column(JSON)  # Photos of pest/damage
    notes = Column(Text)

    # Relationships
    organization = relationship("Organization")
    field = relationship("Location")
    study = relationship("Study")

    def __repr__(self):
        return f"<PestObservation(pest={self.pest_name}, severity={self.severity_score})>"

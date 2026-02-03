"""
Crop Suitability Model

Stores crop suitability assessments for specific locations based on
soil, climate, and agronomic factors.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CropSuitability(BaseModel):
    """
    Represents a crop suitability assessment for a location.
    
    Suitability scoring follows FAO land evaluation framework:
    - S1 (Highly Suitable): 80-100%
    - S2 (Moderately Suitable): 60-80%
    - S3 (Marginally Suitable): 40-60%
    - N1 (Currently Not Suitable): 20-40%
    - N2 (Permanently Not Suitable): 0-20%
    """
    __tablename__ = "crop_suitabilities"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)

    crop_name = Column(String(255), nullable=False, index=True)
    variety = Column(String(255), nullable=True)

    # Overall suitability
    suitability_class = Column(String(10), nullable=False)  # S1, S2, S3, N1, N2
    suitability_score = Column(Float, nullable=False)  # 0-100

    # Factor scores (0-100)
    climate_score = Column(Float)
    soil_score = Column(Float)
    terrain_score = Column(Float)
    water_score = Column(Float)

    # Limiting factors
    limiting_factors = Column(JSON)  # List of factors limiting suitability
    recommendations = Column(JSON)  # Suggested improvements

    # Assessment metadata
    assessment_method = Column(String(100))  # e.g., "FAO", "ALES", "MicroLEIS"
    confidence_level = Column(Float)  # 0-1
    notes = Column(Text)

    # Relationships
    organization = relationship("Organization")
    location = relationship("Location")

    def __repr__(self):
        return f"<CropSuitability(crop={self.crop_name}, class={self.suitability_class})>"

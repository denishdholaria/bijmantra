"""
Space Research Models

Database models for interplanetary agriculture research.
Tracks space-suitable crops and experiments for microgravity environments.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Index, Date, JSON
)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SpaceCrop(BaseModel):
    """
    Space Crop - Crops suitable for space agriculture.
    
    Tracks crops that have been tested or are candidates for
    microgravity and controlled environment agriculture.
    """

    __tablename__ = "space_crops"

    # Core identifiers
    crop_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    species = Column(String(255), nullable=False)

    # Space heritage
    space_heritage = Column(String(255))  # e.g., "ISS Veggie, 2014-present"

    # Growth characteristics
    growth_cycle_days = Column(Integer)
    caloric_yield = Column(Integer)  # kcal per kg

    # Space suitability ratings
    radiation_tolerance = Column(String(50))  # Low, Moderate, High
    microgravity_adaptation = Column(String(50))  # Poor, Good, Excellent

    # Status
    status = Column(String(20), nullable=False, default="active", index=True)

    # Notes
    notes = Column(Text)

    # Organization (multi-tenant)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Relationships
    organization = relationship("Organization")
    experiments = relationship("SpaceExperiment", back_populates="crop")

    def __repr__(self):
        return f"<SpaceCrop {self.crop_code}: {self.name}>"


class SpaceExperiment(BaseModel):
    """
    Space Experiment - Space agriculture research experiment.
    
    Tracks experiments conducted in space or ground-based simulations
    for space agriculture research.
    """

    __tablename__ = "space_experiments"

    # Core identifiers
    experiment_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Experiment details
    crop_id = Column(Integer, ForeignKey("space_crops.id"), nullable=True, index=True)
    crop_name = Column(String(255))  # For "Multiple" crop experiments

    # Environment
    environment = Column(String(100))  # ISS Veggie, Ground Simulation, etc.

    # Parameters (stored as JSON for flexibility)
    parameters = Column(JSON)  # e.g., {"light_hours": 16, "temperature_c": 22}

    # Progress tracking
    start_date = Column(Date)
    end_date = Column(Date)
    observations = Column(Integer, default=0)

    # Status
    status = Column(String(20), nullable=False, default="planned", index=True)  # planned, active, completed

    # Notes
    description = Column(Text)
    notes = Column(Text)

    # Organization (multi-tenant)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Relationships
    organization = relationship("Organization")
    crop = relationship("SpaceCrop", back_populates="experiments")

    __table_args__ = (
        Index('ix_space_experiments_crop_status', 'crop_id', 'status'),
    )

    def __repr__(self):
        return f"<SpaceExperiment {self.experiment_code}: {self.name}>"

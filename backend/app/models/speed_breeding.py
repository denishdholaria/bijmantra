"""
Speed Breeding Models
Protocols, Batches, and Chambers for accelerated generation advancement
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class SpeedBreedingProtocol(BaseModel):
    """Protocol for speed breeding defining conditions and timing"""

    __tablename__ = "speed_breeding_protocols"
    __table_args__ = {'extend_existing': True}

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    crop = Column(String(100), index=True)

    # Environmental Conditions
    photoperiod = Column(Integer) # hours of light
    temperature_day = Column(Float)
    temperature_night = Column(Float)
    humidity = Column(Float)
    light_intensity = Column(Float) # e.g. µmol/m²/s

    # Timing
    days_to_flower = Column(Integer)
    days_to_harvest = Column(Integer)
    generations_per_year = Column(Float)
    success_rate = Column(Float, default=0.95)

    status = Column(String(50), default="active") # active, inactive

    # Relationships
    organization = relationship("Organization")
    batches = relationship("SpeedBreedingBatch", back_populates="protocol")


class SpeedBreedingChamber(BaseModel):
    """Growth chamber for speed breeding"""

    __tablename__ = "speed_breeding_chambers"
    __table_args__ = {'extend_existing': True}

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255)) # Physical location description

    status = Column(String(50), default="active") # active, maintenance, offline
    capacity = Column(Integer, default=0)

    # Current readings (cached/last known)
    current_temperature = Column(Float)
    current_humidity = Column(Float)
    current_light_hours = Column(Float)

    # Relationships
    organization = relationship("Organization")
    batches = relationship("SpeedBreedingBatch", back_populates="chamber")


class SpeedBreedingBatch(BaseModel):
    """Active breeding batch in a chamber"""

    __tablename__ = "speed_breeding_batches"
    __table_args__ = {'extend_existing': True}

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    protocol_id = Column(Integer, ForeignKey("speed_breeding_protocols.id"), nullable=False)
    chamber_id = Column(Integer, ForeignKey("speed_breeding_chambers.id"))

    name = Column(String(255), nullable=False)
    generation = Column(String(50)) # e.g. F3
    entries = Column(Integer, default=0)

    start_date = Column(String(50)) # ISO Date
    expected_harvest = Column(String(50)) # ISO Date

    status = Column(String(50), default="growing") # growing, flowering, harvesting, completed
    progress = Column(Integer, default=0) # 0-100

    # Relationships
    organization = relationship("Organization")
    protocol = relationship("SpeedBreedingProtocol", back_populates="batches")
    chamber = relationship("SpeedBreedingChamber", back_populates="batches")

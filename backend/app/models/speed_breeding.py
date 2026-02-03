"""
Speed Breeding Models
Protocols, Batches, and Chambers for accelerated generation advancement
"""

from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class SpeedBreedingProtocol(BaseModel):
    """Protocol for speed breeding defining conditions and timing"""

    __tablename__ = "speed_breeding_protocols"
    __table_args__ = {'extend_existing': True}

    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    crop: Mapped[str | None] = mapped_column(String(100), index=True)

    # Environmental Conditions
    photoperiod: Mapped[int | None] = mapped_column(Integer) # hours of light
    temperature_day: Mapped[float | None] = mapped_column(Float)
    temperature_night: Mapped[float | None] = mapped_column(Float)
    humidity: Mapped[float | None] = mapped_column(Float)
    light_intensity: Mapped[float | None] = mapped_column(Float) # e.g. µmol/m²/s

    # Timing
    days_to_flower: Mapped[int | None] = mapped_column(Integer)
    days_to_harvest: Mapped[int | None] = mapped_column(Integer)
    generations_per_year: Mapped[float | None] = mapped_column(Float)
    success_rate: Mapped[float | None] = mapped_column(Float, default=0.95)

    status: Mapped[str | None] = mapped_column(String(50), default="active") # active, inactive

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    batches: Mapped[list["SpeedBreedingBatch"]] = relationship("SpeedBreedingBatch", back_populates="protocol")


class SpeedBreedingChamber(BaseModel):
    """Growth chamber for speed breeding"""

    __tablename__ = "speed_breeding_chambers"
    __table_args__ = {'extend_existing': True}

    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255)) # Physical location description

    status: Mapped[str | None] = mapped_column(String(50), default="active") # active, maintenance, offline
    capacity: Mapped[int | None] = mapped_column(Integer, default=0)

    # Current readings (cached/last known)
    current_temperature: Mapped[float | None] = mapped_column(Float)
    current_humidity: Mapped[float | None] = mapped_column(Float)
    current_light_hours: Mapped[float | None] = mapped_column(Float)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    batches: Mapped[list["SpeedBreedingBatch"]] = relationship("SpeedBreedingBatch", back_populates="chamber")


class SpeedBreedingBatch(BaseModel):
    """Active breeding batch in a chamber"""

    __tablename__ = "speed_breeding_batches"
    __table_args__ = {'extend_existing': True}

    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    protocol_id: Mapped[int] = mapped_column(Integer, ForeignKey("speed_breeding_protocols.id"), nullable=False)
    chamber_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("speed_breeding_chambers.id"))

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    generation: Mapped[str | None] = mapped_column(String(50)) # e.g. F3
    entries: Mapped[int | None] = mapped_column(Integer, default=0)

    start_date: Mapped[str | None] = mapped_column(String(50)) # ISO Date
    expected_harvest: Mapped[str | None] = mapped_column(String(50)) # ISO Date

    status: Mapped[str | None] = mapped_column(String(50), default="growing") # growing, flowering, harvesting, completed
    progress: Mapped[int | None] = mapped_column(Integer, default=0) # 0-100

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    protocol: Mapped["SpeedBreedingProtocol"] = relationship("SpeedBreedingProtocol", back_populates="batches")
    chamber: Mapped[Optional["SpeedBreedingChamber"]] = relationship("SpeedBreedingChamber", back_populates="batches")

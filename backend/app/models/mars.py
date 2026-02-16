import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

class MarsFailureMode(str, enum.Enum):
    ATMOSPHERIC_COLLAPSE = "ATMOSPHERIC_COLLAPSE"
    RADIATION_DAMAGE = "RADIATION_DAMAGE"
    WATER_STARVATION = "WATER_STARVATION"
    NUTRIENT_LOCKOUT = "NUTRIENT_LOCKOUT"
    ENERGY_DEFICIT = "ENERGY_DEFICIT"
    PHYSIOLOGICAL_LIMIT = "PHYSIOLOGICAL_LIMIT"
    UNKNOWN = "UNKNOWN"

class MarsEnvironmentProfile(Base):
    __tablename__ = "mars_environment_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    pressure_kpa = Column(Float, nullable=False)
    co2_ppm = Column(Float, nullable=False)
    o2_ppm = Column(Float, nullable=False)
    radiation_msv = Column(Float, nullable=False)
    gravity_factor = Column(Float, nullable=False)
    photoperiod_hours = Column(Float, nullable=False)
    temperature_profile = Column(JSONB, nullable=False)
    humidity_profile = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    trials = relationship("MarsTrial", back_populates="environment_profile")

class MarsTrial(Base):
    __tablename__ = "mars_trials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    environment_profile_id = Column(UUID(as_uuid=True), ForeignKey("mars_environment_profiles.id"), nullable=False)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), nullable=False)
    generation = Column(Integer, nullable=False)
    survival_score = Column(Float, nullable=False)
    biomass_yield = Column(Float, nullable=False)
    failure_mode = Column(Enum(MarsFailureMode), nullable=False)
    notes = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    environment_profile = relationship("MarsEnvironmentProfile", back_populates="trials")
    closed_loop_metrics = relationship("MarsClosedLoopMetric", back_populates="trial", uselist=False)

class MarsClosedLoopMetric(Base):
    __tablename__ = "mars_closed_loop_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id = Column(UUID(as_uuid=True), ForeignKey("mars_trials.id"), nullable=False, unique=True)
    water_recycling_pct = Column(Float, nullable=False)
    nutrient_loss_pct = Column(Float, nullable=False)
    energy_input_kwh = Column(Float, nullable=False)
    oxygen_output = Column(Float, nullable=False)

    trial = relationship("MarsTrial", back_populates="closed_loop_metrics")

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, Float, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class LunarEnvironmentProfile(Base):
    __tablename__ = "lunar_environment_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    gravity_factor = Column(Float, nullable=False) # 0 < g <= 0.3
    light_cycle_days = Column(Float, nullable=False) # >= 1
    dark_cycle_days = Column(Float, nullable=False) # >= 1
    habitat_pressure_kpa = Column(Float, nullable=False) # > 0
    o2_ppm = Column(Float, nullable=False) # 0-210000
    co2_ppm = Column(Float, nullable=False) # >= 0
    root_support_factor = Column(Float, nullable=False) # 0-1
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    trials = relationship("LunarTrial", back_populates="environment_profile")


class LunarTrial(Base):
    __tablename__ = "lunar_trials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    environment_profile_id = Column(UUID(as_uuid=True), ForeignKey("lunar_environment_profiles.id"), nullable=False)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), nullable=False)
    generation = Column(Integer, nullable=False)
    anchorage_score = Column(Float, nullable=False)
    morphology_stability = Column(Float, nullable=False)
    yield_index = Column(Float, nullable=False)
    failure_mode = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)

    environment_profile = relationship("LunarEnvironmentProfile", back_populates="trials")
    germplasm = relationship("Germplasm")

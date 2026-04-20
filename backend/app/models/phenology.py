from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class PhenologyRecord(BaseModel):
    """
    Phenology Record
    Tracks the growth stages of a germplasm in a study/plot.
    """
    __tablename__ = "phenology_records"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Public ID (string) used in API
    record_id = Column(String(255), unique=True, index=True, nullable=False)

    # External references (Strings to match API input, no strict FK constraint for flexibility)
    germplasm_id = Column(String(255), index=True)
    study_id = Column(String(255), index=True)
    plot_id = Column(String(255), index=True)

    germplasm_name = Column(String(255))

    sowing_date = Column(DateTime(timezone=True))
    current_stage = Column(Integer, default=0)
    current_stage_name = Column(String(100))
    days_from_sowing = Column(Integer)
    expected_maturity = Column(Integer, default=120)
    crop = Column(String(100), default="rice")

    # Relationships
    organization = relationship("Organization")
    observations = relationship("PhenologyObservation", back_populates="record", cascade="all, delete-orphan")


class PhenologyObservation(BaseModel):
    """
    Phenology Observation
    A specific observation recorded for a phenology record at a specific stage.
    """
    __tablename__ = "phenology_observations"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Public ID (string)
    observation_id = Column(String(255), unique=True, index=True, nullable=False)

    # Link to internal ID of the record
    record_id = Column(Integer, ForeignKey("phenology_records.id"), nullable=False, index=True)

    stage = Column(Integer)
    stage_name = Column(String(100))
    date = Column(DateTime(timezone=True))
    notes = Column(Text)
    recorded_by = Column(String(255))

    # Relationships
    organization = relationship("Organization")
    record = relationship("PhenologyRecord", back_populates="observations")

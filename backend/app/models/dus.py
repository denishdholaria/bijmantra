"""
DUS Testing Models (Distinctness, Uniformity, Stability)

Database models for UPOV-compliant variety testing for Plant Variety Protection (PVP).
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Index, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class DUSTrialStatus(str, enum.Enum):
    PLANNED = "planned"
    YEAR_1 = "year_1"
    YEAR_2 = "year_2"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DUSResult(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"


class DUSTrial(BaseModel):
    """
    DUS Trial - Main trial record for variety testing.
    
    Tracks multi-year DUS trials for Plant Variety Protection applications.
    """

    __tablename__ = "dus_trials"

    # Core identifiers
    trial_code = Column(String(50), unique=True, nullable=False, index=True)
    trial_name = Column(String(255), nullable=False)

    # Crop reference (uses UPOV crop templates)
    crop_code = Column(String(50), nullable=False, index=True)  # rice, wheat, maize, etc.

    # Trial details
    year = Column(Integer, nullable=False, index=True)
    location = Column(String(255))
    sample_size = Column(Integer, nullable=False, default=100)

    # Status
    status = Column(String(50), nullable=False, default=DUSTrialStatus.PLANNED.value, index=True)

    # Results (populated after analysis)
    distinctness_result = Column(String(20))  # pass/fail/pending
    uniformity_result = Column(String(20))
    stability_result = Column(String(20))
    overall_result = Column(String(20))

    # Metadata
    notes = Column(Text)
    report_generated_at = Column(DateTime(timezone=True))

    # Organization (multi-tenant)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Relationships
    organization = relationship("Organization")
    entries = relationship("DUSEntry", back_populates="trial", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_dus_trials_year_crop', 'year', 'crop_code'),
    )

    def __repr__(self):
        return f"<DUSTrial {self.trial_code}: {self.crop_code} {self.year}>"


class DUSEntry(BaseModel):
    """
    DUS Entry - Variety entry in a DUS trial.
    
    Can be a candidate variety (being tested) or reference variety (for comparison).
    """

    __tablename__ = "dus_entries"

    # Parent trial
    trial_id = Column(Integer, ForeignKey("dus_trials.id", ondelete="CASCADE"), nullable=False, index=True)

    # Entry identifiers
    entry_code = Column(String(50), nullable=False)  # E1, E2, etc.
    variety_name = Column(String(255), nullable=False)

    # Entry type
    is_candidate = Column(Boolean, nullable=False, default=False)
    is_reference = Column(Boolean, nullable=False, default=False)

    # Variety details
    breeder = Column(String(255))
    origin = Column(String(255))  # Institution/country of origin

    # Germplasm link (optional)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), nullable=True, index=True)

    # Uniformity data
    off_type_count = Column(Integer)
    uniformity_passed = Column(Boolean)

    # Notes
    notes = Column(Text)

    # Relationships
    trial = relationship("DUSTrial", back_populates="entries")
    germplasm = relationship("Germplasm")
    scores = relationship("DUSScore", back_populates="entry", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_dus_entries_trial_entry', 'trial_id', 'entry_code', unique=True),
    )

    def __repr__(self):
        return f"<DUSEntry {self.entry_code}: {self.variety_name}>"


class DUSScore(BaseModel):
    """
    DUS Score - Character observation score for an entry.
    
    Records the value for a specific UPOV character on a specific entry.
    """

    __tablename__ = "dus_scores"

    # Parent entry
    entry_id = Column(Integer, ForeignKey("dus_entries.id", ondelete="CASCADE"), nullable=False, index=True)

    # Character reference (from UPOV templates)
    character_id = Column(String(50), nullable=False, index=True)  # rice_1, wheat_4, etc.

    # Score value (can be state code or measurement)
    value = Column(Float)  # State code (1-9) or measurement value
    value_text = Column(String(255))  # Text description of state

    # Year tracking (for stability analysis)
    observation_year = Column(Integer)  # 1 or 2 for multi-year trials

    # Audit
    scored_by = Column(String(255))
    scored_at = Column(DateTime(timezone=True))

    # Notes
    notes = Column(Text)

    # Relationships
    entry = relationship("DUSEntry", back_populates="scores")

    __table_args__ = (
        Index('ix_dus_scores_entry_char_year', 'entry_id', 'character_id', 'observation_year'),
    )

    def __repr__(self):
        return f"<DUSScore {self.character_id}: {self.value}>"

"""
Field Operations Models
Database models for nursery management and field book operations
"""
from datetime import datetime, date, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, Date, ForeignKey,
    JSON, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel
from app.core.database import Base


class BatchStatus(str, enum.Enum):
    """Nursery batch status"""
    SOWING = "sowing"
    GERMINATING = "germinating"
    GROWING = "growing"
    READY = "ready"
    TRANSPLANTED = "transplanted"
    FAILED = "failed"


# ============================================
# NURSERY MANAGEMENT MODELS
# ============================================

class NurseryLocation(Base):
    """Nursery locations (greenhouses, fields, etc.)"""
    __tablename__ = "nursery_locations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    name = Column(String(255), nullable=False)  # e.g., "Greenhouse A"
    location_type = Column(String(100))  # greenhouse, field, shed
    capacity = Column(Integer)  # Max seedlings
    description = Column(Text)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    batches = relationship("SeedlingBatch", back_populates="location")
    
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_nursery_location_name"),
    )


class SeedlingBatch(Base):
    """Seedling batches in nursery"""
    __tablename__ = "seedling_batches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("nursery_locations.id"))
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"))
    
    # Batch identification
    batch_code = Column(String(50), nullable=False)  # e.g., "NB001"
    germplasm_name = Column(String(255), nullable=False)  # Denormalized for quick access
    
    # Dates
    sowing_date = Column(Date, nullable=False)
    expected_transplant_date = Column(Date)
    actual_transplant_date = Column(Date)
    
    # Quantities
    quantity_sown = Column(Integer, nullable=False)
    quantity_germinated = Column(Integer, default=0)
    quantity_healthy = Column(Integer, default=0)
    quantity_transplanted = Column(Integer, default=0)
    
    # Status
    status = Column(SQLEnum(BatchStatus, values_callable=lambda x: [e.value for e in x]), default=BatchStatus.SOWING)
    
    # Notes
    notes = Column(Text)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    location = relationship("NurseryLocation", back_populates="batches")
    
    __table_args__ = (
        UniqueConstraint("organization_id", "batch_code", name="uq_seedling_batch_code"),
        Index("ix_seedling_batch_org_status", "organization_id", "status"),
        Index("ix_seedling_batch_org_location", "organization_id", "location_id"),
    )


# ============================================
# FIELD BOOK MODELS
# ============================================

class FieldBookStudy(Base):
    """Studies with field books for data collection"""
    __tablename__ = "field_book_studies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    study_id = Column(Integer, ForeignKey("studies.id"))  # Link to BrAPI study
    
    # Study identification
    study_code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    
    # Study details
    location = Column(String(255))
    season = Column(String(100))
    design = Column(String(100))  # RCBD, Augmented, Alpha-Lattice
    replications = Column(Integer, default=1)
    
    # Counts
    total_entries = Column(Integer, default=0)
    total_traits = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    data_collection_started = Column(DateTime)
    data_collection_completed = Column(DateTime)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    entries = relationship("FieldBookEntry", back_populates="study", cascade="all, delete-orphan")
    traits = relationship("FieldBookTrait", back_populates="study", cascade="all, delete-orphan")
    observations = relationship("FieldBookObservation", back_populates="study", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("organization_id", "study_code", name="uq_field_book_study_code"),
        Index("ix_field_book_study_org_active", "organization_id", "is_active"),
    )


class FieldBookTrait(Base):
    """Traits to be measured in field book"""
    __tablename__ = "field_book_traits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    study_id = Column(Integer, ForeignKey("field_book_studies.id"), nullable=False)
    variable_id = Column(Integer, ForeignKey("observation_variables.id"))  # Link to BrAPI variable
    
    # Trait identification
    trait_code = Column(String(50), nullable=False)  # e.g., "plant_height"
    name = Column(String(255), nullable=False)  # e.g., "Plant Height"
    
    # Measurement details
    unit = Column(String(50))  # e.g., "cm"
    data_type = Column(String(50), default="numeric")  # numeric, categorical, text, date
    min_value = Column(Float)
    max_value = Column(Float)
    step = Column(Float, default=1)
    categories = Column(ARRAY(String))  # For categorical traits
    
    # Display order
    display_order = Column(Integer, default=0)
    
    # Metadata
    is_required = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    study = relationship("FieldBookStudy", back_populates="traits")
    observations = relationship("FieldBookObservation", back_populates="trait", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("study_id", "trait_code", name="uq_field_book_trait_code"),
        Index("ix_field_book_trait_study", "study_id", "display_order"),
    )


class FieldBookEntry(Base):
    """Entries (plots) in field book"""
    __tablename__ = "field_book_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    study_id = Column(Integer, ForeignKey("field_book_studies.id"), nullable=False)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"))
    
    # Plot identification
    plot_id = Column(String(50), nullable=False)  # e.g., "A-01-01"
    germplasm_name = Column(String(255))  # Denormalized
    
    # Position
    replication = Column(String(20))  # e.g., "R1"
    block = Column(String(20))
    row = Column(Integer)
    column = Column(Integer)
    
    # Status
    is_check = Column(Boolean, default=False)  # Check/control entry
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    study = relationship("FieldBookStudy", back_populates="entries")
    observations = relationship("FieldBookObservation", back_populates="entry", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("study_id", "plot_id", name="uq_field_book_entry_plot"),
        Index("ix_field_book_entry_study_rep", "study_id", "replication"),
    )


class FieldBookObservation(Base):
    """Individual observations recorded in field book"""
    __tablename__ = "field_book_observations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    study_id = Column(Integer, ForeignKey("field_book_studies.id"), nullable=False)
    entry_id = Column(Integer, ForeignKey("field_book_entries.id"), nullable=False)
    trait_id = Column(Integer, ForeignKey("field_book_traits.id"), nullable=False)
    
    # Observation value
    value_numeric = Column(Float)
    value_text = Column(Text)
    value_date = Column(Date)
    
    # Metadata
    observation_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    collector_id = Column(Integer, ForeignKey("users.id"))
    notes = Column(Text)
    
    # GPS location (for mobile collection)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Quality flags
    is_outlier = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    study = relationship("FieldBookStudy", back_populates="observations")
    entry = relationship("FieldBookEntry", back_populates="observations")
    trait = relationship("FieldBookTrait", back_populates="observations")
    
    __table_args__ = (
        UniqueConstraint("entry_id", "trait_id", name="uq_field_book_observation"),
        Index("ix_field_book_obs_study_trait", "study_id", "trait_id"),
        Index("ix_field_book_obs_entry", "entry_id"),
    )

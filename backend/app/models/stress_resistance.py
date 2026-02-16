"""
Stress Resistance Models
Database models for abiotic stress and disease resistance tracking
"""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey,
    JSON, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel
from app.core.database import Base


class StressCategory(str, enum.Enum):
    """Abiotic stress categories"""
    WATER = "water"
    TEMPERATURE = "temperature"
    SOIL = "soil"
    RADIATION = "radiation"
    NUTRIENT = "nutrient"
    OTHER = "other"


class PathogenType(str, enum.Enum):
    """Disease pathogen types"""
    BACTERIA = "bacteria"
    FUNGUS = "fungus"
    VIRUS = "virus"
    INSECT = "insect"
    NEMATODE = "nematode"
    OTHER = "other"


class ResistanceType(str, enum.Enum):
    """Resistance gene types"""
    COMPLETE = "complete"
    PARTIAL = "partial"
    RECESSIVE = "recessive"
    DOMINANT = "dominant"
    QUANTITATIVE = "quantitative"


# ============================================
# ABIOTIC STRESS MODELS
# ============================================

class AbioticStress(Base):
    """Abiotic stress types (drought, heat, salinity, etc.)"""
    __tablename__ = "abiotic_stresses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Stress identification
    stress_code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(SQLEnum(StressCategory, values_callable=lambda x: [e.value for e in x]), nullable=False)
    description = Column(Text)

    # Screening info
    screening_method = Column(String(255))
    screening_stages = Column(ARRAY(String))
    screening_duration = Column(String(100))
    indicators = Column(ARRAY(String))

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    tolerance_genes = relationship("ToleranceGene", back_populates="stress", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "stress_code", name="uq_abiotic_stress_code"),
        Index("ix_abiotic_stress_org_category", "organization_id", "category"),
    )


class ToleranceGene(Base):
    """Genes conferring tolerance to abiotic stresses"""
    __tablename__ = "tolerance_genes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    stress_id = Column(Integer, ForeignKey("abiotic_stresses.id"), nullable=False)

    # Gene identification
    gene_code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    # Gene details
    mechanism = Column(String(255))
    crop = Column(String(100))
    chromosome = Column(String(50))
    position_start = Column(Integer)
    position_end = Column(Integer)

    # Markers for MAS
    markers = Column(ARRAY(String))

    # Source
    source_germplasm = Column(String(255))
    reference = Column(Text)

    # Metadata
    is_validated = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    stress = relationship("AbioticStress", back_populates="tolerance_genes")

    __table_args__ = (
        UniqueConstraint("organization_id", "gene_code", name="uq_tolerance_gene_code"),
        Index("ix_tolerance_gene_org_crop", "organization_id", "crop"),
    )


# ============================================
# DISEASE RESISTANCE MODELS
# ============================================

class Disease(Base):
    """Plant diseases"""
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Disease identification
    disease_code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    # Pathogen info
    pathogen = Column(String(255))
    pathogen_type = Column(SQLEnum(PathogenType, values_callable=lambda x: [e.value for e in x]), nullable=False)

    # Crop and symptoms
    crop = Column(String(100), nullable=False)
    symptoms = Column(Text)
    severity_scale = Column(ARRAY(String))

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    resistance_genes = relationship("ResistanceGene", back_populates="disease", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "disease_code", name="uq_disease_code"),
        Index("ix_disease_org_crop", "organization_id", "crop"),
        Index("ix_disease_org_pathogen_type", "organization_id", "pathogen_type"),
    )


class ResistanceGene(Base):
    """Genes conferring resistance to diseases"""
    __tablename__ = "resistance_genes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=False)

    # Gene identification
    gene_code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    # Gene details
    chromosome = Column(String(50))
    resistance_type = Column(SQLEnum(ResistanceType, values_callable=lambda x: [e.value for e in x]), nullable=False)

    # Source and markers
    source_germplasm = Column(String(255))
    markers = Column(ARRAY(String))

    # Reference
    reference = Column(Text)

    # Metadata
    is_validated = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    disease = relationship("Disease", back_populates="resistance_genes")

    __table_args__ = (
        UniqueConstraint("organization_id", "gene_code", name="uq_resistance_gene_code"),
        Index("ix_resistance_gene_org_type", "organization_id", "resistance_type"),
    )


class PyramidingStrategy(Base):
    """Gene pyramiding strategies for durable resistance"""
    __tablename__ = "pyramiding_strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Strategy identification
    strategy_code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    # Target
    target_disease = Column(String(255))
    target_stress = Column(String(255))

    # Genes to combine
    gene_names = Column(ARRAY(String), nullable=False)

    # Details
    description = Column(Text)
    status = Column(String(50), default="recommended")
    warning_message = Column(Text)

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("organization_id", "strategy_code", name="uq_pyramiding_strategy_code"),
    )

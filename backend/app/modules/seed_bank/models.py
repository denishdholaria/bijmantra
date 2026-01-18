"""
Seed Bank Division - Database Models
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
import enum

from app.core.database import Base


class VaultType(str, enum.Enum):
    BASE = "base"
    ACTIVE = "active"
    CRYO = "cryo"


class VaultStatus(str, enum.Enum):
    OPTIMAL = "optimal"
    WARNING = "warning"
    CRITICAL = "critical"


class AccessionStatus(str, enum.Enum):
    ACTIVE = "active"
    DEPLETED = "depleted"
    REGENERATING = "regenerating"


class TestStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"


class RegenerationPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RegenerationStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in-progress"
    HARVESTED = "harvested"
    COMPLETED = "completed"


class ExchangeType(str, enum.Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class ExchangeStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SHIPPED = "shipped"
    RECEIVED = "received"
    REJECTED = "rejected"


class Vault(Base):
    """Seed storage vault/facility"""
    __tablename__ = "seed_bank_vaults"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum(VaultType), nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)
    used = Column(Integer, default=0)
    status = Column(Enum(VaultStatus), default=VaultStatus.OPTIMAL)
    last_inspection = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    accessions = relationship("Accession", back_populates="vault")


class Accession(Base):
    """Germplasm accession record"""
    __tablename__ = "seed_bank_accessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    accession_number = Column(String(50), nullable=False, unique=True, index=True)
    genus = Column(String(100), nullable=False, index=True)
    species = Column(String(100), nullable=False, index=True)
    subspecies = Column(String(100))
    common_name = Column(String(255))
    origin = Column(String(100), index=True)
    collection_date = Column(DateTime)
    collection_site = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    vault_id = Column(UUID(as_uuid=True), ForeignKey("seed_bank_vaults.id"))
    seed_count = Column(Integer, default=0)
    viability = Column(Float, default=100.0)
    status = Column(Enum(AccessionStatus), default=AccessionStatus.ACTIVE, index=True)
    acquisition_type = Column(String(50))
    donor_institution = Column(String(255))
    mls = Column(Boolean, default=False)  # Multilateral System
    pedigree = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    vault = relationship("Vault", back_populates="accessions")
    viability_tests = relationship("ViabilityTest", back_populates="accession")
    regeneration_tasks = relationship("RegenerationTask", back_populates="accession")


class ViabilityTest(Base):
    """Germination/viability test record"""
    __tablename__ = "seed_bank_viability_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    batch_number = Column(String(50), nullable=False, unique=True)
    accession_id = Column(UUID(as_uuid=True), ForeignKey("seed_bank_accessions.id"), nullable=False)
    test_date = Column(DateTime, nullable=False)
    seeds_tested = Column(Integer, nullable=False)
    germinated = Column(Integer, default=0)
    germination_rate = Column(Float, default=0.0)
    status = Column(Enum(TestStatus), default=TestStatus.SCHEDULED)
    technician_id = Column(UUID(as_uuid=True))
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    accession = relationship("Accession", back_populates="viability_tests")


class RegenerationTask(Base):
    """Seed regeneration planning and tracking"""
    __tablename__ = "seed_bank_regeneration_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    accession_id = Column(UUID(as_uuid=True), ForeignKey("seed_bank_accessions.id"), nullable=False)
    reason = Column(String(50), nullable=False)
    priority = Column(Enum(RegenerationPriority), default=RegenerationPriority.MEDIUM)
    target_quantity = Column(Integer, nullable=False)
    planned_season = Column(String(50))
    status = Column(Enum(RegenerationStatus), default=RegenerationStatus.PLANNED)
    location_id = Column(UUID(as_uuid=True))
    harvested_quantity = Column(Integer)
    completed_date = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    accession = relationship("Accession", back_populates="regeneration_tasks")


class GermplasmExchange(Base):
    """Germplasm exchange/transfer record"""
    __tablename__ = "seed_bank_exchanges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    request_number = Column(String(50), nullable=False, unique=True)
    type = Column(Enum(ExchangeType), nullable=False)
    institution_id = Column(UUID(as_uuid=True))
    institution_name = Column(String(255), nullable=False)
    accession_ids = Column(ARRAY(UUID(as_uuid=True)))
    status = Column(Enum(ExchangeStatus), default=ExchangeStatus.PENDING)
    request_date = Column(DateTime, nullable=False)
    smta = Column(Boolean, default=True)  # Standard Material Transfer Agreement
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

"""
Data Management Models
Models for germplasm collections, data validation, and backups
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, ForeignKey,
    Enum as SQLEnum, JSON, Float
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel
from app.core.database import Base


# ============================================
# ENUMS
# ============================================

class CollectionType(str, enum.Enum):
    """Types of germplasm collections"""
    CORE = "core"
    WORKING = "working"
    ACTIVE = "active"
    BASE = "base"
    BREEDING = "breeding"
    REFERENCE = "reference"


class CollectionStatus(str, enum.Enum):
    """Collection status"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING = "pending"


class ValidationSeverity(str, enum.Enum):
    """Validation issue severity"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssueStatus(str, enum.Enum):
    """Validation issue status"""
    OPEN = "open"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class ValidationRunStatus(str, enum.Enum):
    """Validation run status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BackupType(str, enum.Enum):
    """Backup types"""
    FULL = "full"
    INCREMENTAL = "incremental"
    MANUAL = "manual"


class BackupStatus(str, enum.Enum):
    """Backup status"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================
# GERMPLASM COLLECTION MODELS
# ============================================

class GermplasmCollection(Base):
    """Germplasm collection for organizing accessions"""
    
    __tablename__ = "germplasm_collections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Collection info
    collection_code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    collection_type = Column(SQLEnum(CollectionType, values_callable=lambda x: [e.value for e in x]), default=CollectionType.WORKING)
    status = Column(SQLEnum(CollectionStatus, values_callable=lambda x: [e.value for e in x]), default=CollectionStatus.ACTIVE)
    
    # Statistics (denormalized for performance)
    accession_count = Column(Integer, default=0)
    species = Column(ARRAY(String), default=list)
    
    # Curator info
    curator_name = Column(String(255))
    curator_email = Column(String(255))
    curator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    notes = Column(Text)
    tags = Column(ARRAY(String), default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization = relationship("Organization", backref="germplasm_collections")
    members = relationship("GermplasmCollectionMember", back_populates="collection", cascade="all, delete-orphan")


class GermplasmCollectionMember(Base):
    """Association between germplasm and collections"""
    
    __tablename__ = "germplasm_collection_members"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(Integer, ForeignKey("germplasm_collections.id", ondelete="CASCADE"), nullable=False, index=True)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Membership info
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(Text)
    
    # Relationships
    collection = relationship("GermplasmCollection", back_populates="members")
    germplasm = relationship("Germplasm")


# ============================================
# DATA VALIDATION MODELS
# ============================================

class ValidationRule(Base):
    """Data validation rules"""
    
    __tablename__ = "validation_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Rule definition
    rule_code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Configuration
    enabled = Column(Boolean, default=True)
    severity = Column(SQLEnum(ValidationSeverity, values_callable=lambda x: [e.value for e in x]), default=ValidationSeverity.WARNING)
    entity_types = Column(ARRAY(String), default=list)  # observation, germplasm, trial, etc.
    
    # Rule logic (JSON for flexibility)
    rule_type = Column(String(50))  # range_check, referential, outlier, format, etc.
    rule_config = Column(JSON, default=dict)  # Rule-specific configuration
    
    # Metadata
    is_system = Column(Boolean, default=False)  # System rules can't be deleted
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization = relationship("Organization", backref="validation_rules")
    issues = relationship("ValidationIssue", back_populates="rule", cascade="all, delete-orphan")


class ValidationIssue(Base):
    """Detected validation issues"""
    
    __tablename__ = "validation_issues"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("validation_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    run_id = Column(Integer, ForeignKey("validation_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Issue details
    issue_type = Column(SQLEnum(ValidationSeverity, values_callable=lambda x: [e.value for e in x]), default=ValidationSeverity.WARNING)
    status = Column(SQLEnum(ValidationIssueStatus, values_callable=lambda x: [e.value for e in x]), default=ValidationIssueStatus.OPEN, index=True)
    
    # Affected record
    entity_type = Column(String(50), index=True)  # observation, germplasm, etc.
    record_id = Column(String(255), index=True)
    field_name = Column(String(100))
    
    # Issue info
    message = Column(Text, nullable=False)
    suggestion = Column(Text)
    actual_value = Column(Text)
    expected_value = Column(Text)
    
    # Resolution
    resolved_at = Column(DateTime)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization = relationship("Organization", backref="validation_issues")
    rule = relationship("ValidationRule", back_populates="issues")
    run = relationship("ValidationRun", back_populates="issues")


class ValidationRun(Base):
    """Validation run history"""
    
    __tablename__ = "validation_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Run info
    status = Column(SQLEnum(ValidationRunStatus, values_callable=lambda x: [e.value for e in x]), default=ValidationRunStatus.PENDING)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime)
    
    # Configuration
    entity_types = Column(ARRAY(String), default=list)  # What was validated
    rule_ids = Column(ARRAY(Integer), default=list)  # Which rules were applied
    
    # Results
    records_checked = Column(Integer, default=0)
    issues_found = Column(Integer, default=0)
    errors_found = Column(Integer, default=0)
    warnings_found = Column(Integer, default=0)
    
    # Triggered by
    triggered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    trigger_type = Column(String(50))  # manual, scheduled, on_import
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization = relationship("Organization", backref="validation_runs")
    issues = relationship("ValidationIssue", back_populates="run")


# ============================================
# BACKUP MODELS
# ============================================

class Backup(Base):
    """Database backup records"""
    
    __tablename__ = "backups"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Backup info
    backup_name = Column(String(255), nullable=False)
    backup_type = Column(SQLEnum(BackupType, values_callable=lambda x: [e.value for e in x]), default=BackupType.MANUAL)
    status = Column(SQLEnum(BackupStatus, values_callable=lambda x: [e.value for e in x]), default=BackupStatus.IN_PROGRESS)
    
    # Size and location
    size_bytes = Column(Integer, default=0)
    storage_path = Column(String(500))
    storage_provider = Column(String(50), default="local")  # local, s3, gcs
    
    # Timing
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime)
    
    # Content
    tables_included = Column(ARRAY(String), default=list)
    record_counts = Column(JSON, default=dict)  # {table_name: count}
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text)
    error_message = Column(Text)
    
    # Retention
    expires_at = Column(DateTime)
    is_retained = Column(Boolean, default=False)  # Prevent auto-deletion
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization = relationship("Organization", backref="backups")


# ============================================
# CROP HEALTH MODELS
# ============================================

class DiseaseRiskLevel(str, enum.Enum):
    """Disease risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertType(str, enum.Enum):
    """Health alert types"""
    DISEASE = "disease"
    STRESS = "stress"
    PEST = "pest"
    WEATHER = "weather"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrialHealth(Base):
    """Trial health monitoring records"""
    
    __tablename__ = "trial_health"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    trial_id = Column(Integer, ForeignKey("trials.id"), nullable=True, index=True)
    
    # Trial info (denormalized for quick access)
    trial_name = Column(String(255), nullable=False)
    location = Column(String(255))
    crop = Column(String(100))
    
    # Health metrics
    health_score = Column(Float, default=100.0)  # 0-100
    disease_risk = Column(SQLEnum(DiseaseRiskLevel, values_callable=lambda x: [e.value for e in x]), default=DiseaseRiskLevel.LOW)
    stress_level = Column(Float, default=0.0)  # 0-100
    
    # Scan info
    last_scan_at = Column(DateTime)
    plots_scanned = Column(Integer, default=0)
    total_plots = Column(Integer, default=0)
    issues = Column(ARRAY(String), default=list)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization = relationship("Organization", backref="trial_health_records")
    alerts = relationship("HealthAlert", back_populates="trial_health", cascade="all, delete-orphan")


class HealthAlert(Base):
    """Health alerts for trials"""
    
    __tablename__ = "health_alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    trial_health_id = Column(Integer, ForeignKey("trial_health.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Alert info
    alert_type = Column(SQLEnum(AlertType, values_callable=lambda x: [e.value for e in x]), default=AlertType.DISEASE)
    severity = Column(SQLEnum(AlertSeverity, values_callable=lambda x: [e.value for e in x]), default=AlertSeverity.MEDIUM)
    message = Column(Text, nullable=False)
    location = Column(String(255))
    
    # Status
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization = relationship("Organization", backref="health_alerts")
    trial_health = relationship("TrialHealth", back_populates="alerts")

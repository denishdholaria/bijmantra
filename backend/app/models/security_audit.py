"""
Security Audit Database Models

SQLAlchemy models for persistent security audit logging.
Designed for compliance and long-term forensic analysis.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class SecurityAuditEntry(Base):
    """
    Security audit log entry.
    
    Stores all security-relevant events for compliance and forensics.
    """
    __tablename__ = "security_audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Classification
    category = Column(String(50), nullable=False, index=True)  # authentication, authorization, etc.
    severity = Column(String(20), nullable=False, index=True)  # info, warning, error, critical
    action = Column(String(100), nullable=False, index=True)  # login_attempt, access_denied, etc.
    
    # Actor and target
    actor = Column(String(255), nullable=True, index=True)  # User ID or system component
    target = Column(String(500), nullable=True, index=True)  # Resource being accessed
    source_ip = Column(String(45), nullable=True, index=True)  # IPv4 or IPv6
    
    # Details
    details = Column(JSON, nullable=True)  # Additional context
    success = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_audit_timestamp_category', 'timestamp', 'category'),
        Index('ix_audit_actor_timestamp', 'actor', 'timestamp'),
        Index('ix_audit_source_ip_timestamp', 'source_ip', 'timestamp'),
        Index('ix_audit_severity_timestamp', 'severity', 'timestamp'),
    )


class SecurityThreat(Base):
    """
    Detected security threat record.
    
    Stores threat assessments from PRAHARI VIVEK.
    """
    __tablename__ = "security_threats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Threat classification
    category = Column(String(50), nullable=False, index=True)  # brute_force, injection, etc.
    confidence = Column(String(20), nullable=False)  # low, medium, high, confirmed
    confidence_score = Column(Integer, nullable=False)  # 0-100
    severity = Column(String(20), nullable=False, index=True)
    
    # Source
    source_ip = Column(String(45), nullable=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    
    # Details
    event_id = Column(String(100), nullable=True)
    indicators = Column(JSON, nullable=True)  # List of IOCs
    recommended_actions = Column(JSON, nullable=True)
    
    # Resolution
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)


class SecurityResponse(Base):
    """
    Security response action record.
    
    Stores response actions from PRAHARI SHAKTI.
    """
    __tablename__ = "security_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Response details
    action = Column(String(50), nullable=False, index=True)  # block_ip, rate_limit, etc.
    status = Column(String(20), nullable=False)  # success, failed, skipped
    
    # Target
    target_type = Column(String(20), nullable=True)  # ip, user, endpoint
    target = Column(String(255), nullable=True, index=True)
    
    # Context
    threat_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    triggered_by = Column(String(50), nullable=True)  # auto, manual
    
    # Result
    result = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Metadata
    executed_by = Column(String(255), nullable=True)  # User who triggered manual action


class BlockedEntity(Base):
    """
    Currently blocked IP or user.
    
    Persistent storage for blocking (backup to Redis).
    """
    __tablename__ = "security_blocked"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    entity_type = Column(String(20), nullable=False, index=True)  # ip, user
    entity_value = Column(String(255), nullable=False, index=True)
    
    blocked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    reason = Column(Text, nullable=True)
    blocked_by = Column(String(255), nullable=True)
    threat_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Unique constraint
    __table_args__ = (
        Index('ix_blocked_entity', 'entity_type', 'entity_value', unique=True),
        Index('ix_blocked_expires', 'expires_at'),
    )

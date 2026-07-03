"""
CFR Part 11 Audit Log Model

Defines the schema for immutable audit trails required by FDA 21 CFR Part 11.
Provides tamper-evident logging via cryptographic chaining.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CFRLog(Base):
    """
    Immutable audit log entry complying with 21 CFR Part 11.

    Features:
    - distinct timestamps
    - user identification
    - reason for change
    - cryptographic linking (blockchain-style) for tamper evidence
    """

    __tablename__ = "cfr_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)

    # Actor
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)

    # Action
    action_type = Column(String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE, SIGN, EXPORT
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True, index=True)
    reason = Column(Text, nullable=True)  # Required for updates/deletes in strict mode

    # Data
    changes = Column(JSON, nullable=True)  # {"before": ..., "after": ...}

    # Integrity (Blockchain-style linking)
    signature = Column(String(64), nullable=False)  # SHA256 hash of this record
    previous_hash = Column(String(64), nullable=False, index=True)  # Hash of the previous record

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")

    __table_args__ = (
        Index("ix_cfr_logs_chain", "previous_hash", unique=False),  # Optimize chain verification
        Index("ix_cfr_logs_resource", "resource_type", "resource_id"),
    )

"""Persistent compute lineage records."""

from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ComputeLineageRecord(BaseModel):
    """Durable lineage state for compute runs and jobs."""

    __tablename__ = "compute_lineage_records"

    lineage_record_id = Column(String(64), nullable=False, unique=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    job_id = Column(String(255), nullable=True, index=True)
    routine = Column(String(32), nullable=False, index=True)
    output_kind = Column(String(64), nullable=True)
    execution_mode = Column(String(16), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    contract_version = Column(String(32), nullable=False)
    input_summary = Column(JSON, nullable=True)
    provenance = Column(JSON, nullable=True)
    policy_flags = Column(JSON, nullable=True)
    result_summary = Column(JSON, nullable=True)
    error = Column(JSON, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)

    organization = relationship("Organization")
    user = relationship("User")

    __table_args__ = (
        Index("ix_compute_lineage_org_status", "organization_id", "status"),
        Index("ix_compute_lineage_job_status", "job_id", "status"),
        Index("ix_compute_lineage_org_created", "organization_id", "created_at"),
    )


def mark_compute_lineage_completed(record: ComputeLineageRecord) -> None:
    """Set completion time for terminal lineage states."""

    if record.status in {"completed", "failed", "succeeded"} and record.completed_at is None:
        record.completed_at = datetime.now(UTC)
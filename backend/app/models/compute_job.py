"""
ComputeJob — durable persistence for background compute tasks.

Every job submitted to TaskQueue is mirrored here so that:
  - Status survives process restarts (PENDING jobs are re-enqueued on startup).
  - Progress and results are queryable via the API without holding the job in memory.
  - Failed jobs have a permanent audit trail.

Schema is intentionally minimal — the full result payload is stored as JSONB
so the table never needs a migration for new compute routine output shapes.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel


class ComputeJob(BaseModel):
    """Durable record for a background compute job."""

    __tablename__ = "compute_jobs"
    __table_args__ = (
        Index("ix_compute_jobs_status", "status"),
        Index("ix_compute_jobs_org_status", "organization_id", "status"),
        Index("ix_compute_jobs_user_id", "user_id"),
        {"extend_existing": True},
    )

    # Identity
    job_id = Column(String(36), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)

    # Ownership
    user_id = Column(String(255), nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)

    # Lifecycle
    status = Column(String(32), nullable=False, default="pending")  # pending/running/completed/failed/cancelled
    priority = Column(Integer, nullable=False, default=1)
    compute_type = Column(String(32), nullable=True)  # light_python / heavy_compute / gpu_compute

    # Progress
    progress = Column(Float, nullable=False, default=0.0)
    progress_message = Column(Text, nullable=True)

    # Payload — stored as JSONB so no migration is needed for new output shapes
    result_json = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSONB, nullable=True)

    # Timestamps (created_at / updated_at come from BaseModel)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

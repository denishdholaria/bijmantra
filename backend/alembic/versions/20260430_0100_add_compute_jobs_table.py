"""Add compute_jobs table for durable task queue persistence.

Revision ID: 20260430_0100
Revises: 20260423_1000
Create Date: 2026-04-30 01:00:00.000000

Purpose
-------
The in-process TaskQueue loses all PENDING/RUNNING jobs on process restart.
This table mirrors every enqueued job so that:
  - Status survives restarts (startup re-enqueues PENDING rows).
  - Progress and results are queryable via the API.
  - Failed jobs have a permanent audit trail.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "20260430_0100"
down_revision = "20260423_1000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compute_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("compute_type", sa.String(32), nullable=True),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("progress_message", sa.Text(), nullable=True),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", name="uq_compute_jobs_job_id"),
    )

    # Indexes for the most common query patterns
    op.create_index("ix_compute_jobs_job_id", "compute_jobs", ["job_id"], unique=True)
    op.create_index("ix_compute_jobs_status", "compute_jobs", ["status"])
    op.create_index("ix_compute_jobs_org_status", "compute_jobs", ["organization_id", "status"])
    op.create_index("ix_compute_jobs_user_id", "compute_jobs", ["user_id"])

    # Enable RLS so tenant isolation applies automatically
    op.execute("ALTER TABLE compute_jobs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE compute_jobs FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY compute_jobs_tenant_isolation
        ON compute_jobs
        FOR ALL
        USING (
            current_setting('app.current_organization_id', true)::integer = 0
            OR organization_id IS NULL
            OR organization_id = current_setting('app.current_organization_id', true)::integer
        )
        WITH CHECK (
            current_setting('app.current_organization_id', true)::integer = 0
            OR organization_id IS NULL
            OR organization_id = current_setting('app.current_organization_id', true)::integer
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS compute_jobs_tenant_isolation ON compute_jobs")
    op.execute("ALTER TABLE compute_jobs DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_compute_jobs_user_id", table_name="compute_jobs")
    op.drop_index("ix_compute_jobs_org_status", table_name="compute_jobs")
    op.drop_index("ix_compute_jobs_status", table_name="compute_jobs")
    op.drop_index("ix_compute_jobs_job_id", table_name="compute_jobs")
    op.drop_table("compute_jobs")

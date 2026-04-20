"""Add structured queue and lane linkage to durable orchestrator missions.

Revision ID: 20260323_0100
Revises: 20260315_0300
Create Date: 2026-03-23 01:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260323_0100"
down_revision = "20260315_0300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "orchestrator_missions",
        sa.Column("queue_job_id", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "orchestrator_missions",
        sa.Column("source_lane_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "orchestrator_missions",
        sa.Column("source_board_concurrency_token", sa.String(length=128), nullable=True),
    )
    op.create_index(
        op.f("ix_orchestrator_missions_queue_job_id"),
        "orchestrator_missions",
        ["queue_job_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_orchestrator_missions_source_lane_id"),
        "orchestrator_missions",
        ["source_lane_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_orchestrator_missions_source_board_concurrency_token"),
        "orchestrator_missions",
        ["source_board_concurrency_token"],
        unique=False,
    )
    op.execute(
        """
        UPDATE orchestrator_missions
        SET
            source_lane_id = substring(source_request from 'for lane ([^ ]+) from queue job [^.]+\\.'),
            queue_job_id = substring(source_request from 'from queue job ([^.]+)\\.'),
            source_board_concurrency_token = substring(
                source_request from 'source_board_concurrency_token=([^.]+)\\.'
            )
        WHERE source_request LIKE 'Developer control-plane %'
        """
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_orchestrator_missions_source_board_concurrency_token"),
        table_name="orchestrator_missions",
    )
    op.drop_index(
        op.f("ix_orchestrator_missions_source_lane_id"),
        table_name="orchestrator_missions",
    )
    op.drop_index(
        op.f("ix_orchestrator_missions_queue_job_id"),
        table_name="orchestrator_missions",
    )
    op.drop_column("orchestrator_missions", "source_board_concurrency_token")
    op.drop_column("orchestrator_missions", "source_lane_id")
    op.drop_column("orchestrator_missions", "queue_job_id")
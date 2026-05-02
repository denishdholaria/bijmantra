"""Add producer provenance to durable orchestrator missions.

Revision ID: 20260315_0300
Revises: 20260315_0200
Create Date: 2026-03-15 03:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260315_0300"
down_revision = "20260315_0200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "orchestrator_missions",
        sa.Column("producer_key", sa.String(length=64), nullable=True),
    )
    op.create_index(
        op.f("ix_orchestrator_missions_producer_key"),
        "orchestrator_missions",
        ["producer_key"],
        unique=False,
    )
    op.execute(
        """
        UPDATE orchestrator_missions
        SET producer_key = 'chaitanya'
        WHERE producer_key IS NULL
          AND objective LIKE 'CHAITANYA posture transition: %'
          AND (
              source_request LIKE 'Manual posture override: %'
              OR source_request LIKE 'Automatic posture transition: %'
          )
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_orchestrator_missions_producer_key"), table_name="orchestrator_missions")
    op.drop_column("orchestrator_missions", "producer_key")
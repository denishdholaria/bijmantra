"""Enable TimescaleDB extension for time-series optimization.

Revision ID: 20260423_0400
Revises: 20260423_0300
Create Date: 2026-04-23 04:00:00.000000
"""

from alembic import op


revision = "20260423_0400"
down_revision = "20260423_0300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS timescaledb CASCADE")

"""Enable pgcrypto extension for database-level credential encryption.

Revision ID: 20260423_0100
Revises: 20260402_0600
Create Date: 2026-04-23 01:00:00.000000
"""

from alembic import op


revision = "20260423_0100"
down_revision = "20260402_0600"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")

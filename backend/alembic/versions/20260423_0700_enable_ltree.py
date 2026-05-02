"""Enable ltree extension for hierarchical data queries.

Revision ID: 20260423_0700
Revises: 20260423_0600
Create Date: 2026-04-23 07:00:00.000000

Task 6.1: Enable the ltree extension which provides a data type for representing
          labels of data stored in a hierarchical tree-like structure.
          Required before adding ltree columns to the organizations table.
"""

from alembic import op


revision = "20260423_0700"
down_revision = "20260423_0600"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS ltree")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS ltree")

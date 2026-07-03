"""Add ontology term metadata to observation variables.

Revision ID: 20260520_0100
Revises: 20260514_0100
Create Date: 2026-05-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260520_0100"
down_revision = "20260514_0100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "observation_variables",
        sa.Column("ontology_term_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "observation_variables",
        sa.Column("ontology_version", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "observation_variables",
        sa.Column("ontology_documentation_links", sa.JSON(), nullable=True),
    )
    op.create_index(
        op.f("ix_observation_variables_ontology_term_id"),
        "observation_variables",
        ["ontology_term_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_observation_variables_ontology_term_id"),
        table_name="observation_variables",
    )
    op.drop_column("observation_variables", "ontology_documentation_links")
    op.drop_column("observation_variables", "ontology_version")
    op.drop_column("observation_variables", "ontology_term_id")

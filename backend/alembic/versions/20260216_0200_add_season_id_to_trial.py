"""add_season_id_to_trial

Revision ID: 2c3d4e5f6a1b
Revises: 9fbe32df2a10
Create Date: 2026-02-16 02:00:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "2c3d4e5f6a1b"
down_revision = "9fbe32df2a10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trials", sa.Column("season_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_trials_season_id"), "trials", ["season_id"], unique=False)
    op.create_foreign_key("fk_trials_season_id", "trials", "seasons", ["season_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_trials_season_id", "trials", type_="foreignkey")
    op.drop_index(op.f("ix_trials_season_id"), table_name="trials")
    op.drop_column("trials", "season_id")

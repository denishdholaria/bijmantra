"""Add prompt mode capabilities to REEVU agent settings.

Revision ID: 20260310_0200
Revises: 20260310_0100
Create Date: 2026-03-10 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
revision = '20260310_0200'
down_revision = '20260310_0100'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.add_column(
		'reevu_agent_settings',
		sa.Column('prompt_mode_capabilities', sa.JSON(), nullable=True),
	)


def downgrade() -> None:
	op.drop_column('reevu_agent_settings', 'prompt_mode_capabilities')
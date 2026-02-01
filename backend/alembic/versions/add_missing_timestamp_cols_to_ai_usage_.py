"""add missing timestamp cols to ai_usage_daily

Revision ID: 043
Revises: 5fc61144136f
Create Date: 2026-01-31 05:56:33.296261+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '043'
down_revision = '5fc61144136f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add created_at and updated_at columns to ai_usage_daily table
    # We use server_default=sa.func.now() to populate existing rows
    
    op.add_column('ai_usage_daily', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('ai_usage_daily', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))


def downgrade() -> None:
    op.drop_column('ai_usage_daily', 'updated_at')
    op.drop_column('ai_usage_daily', 'created_at')

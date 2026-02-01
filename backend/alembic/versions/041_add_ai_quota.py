"""add_ai_quota_tables

Revision ID: 4097beta
Revises: 4096alpha
Create Date: 2026-01-30 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4097beta'
down_revision = '4096alpha'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add ai_daily_limit to organizations
    op.add_column('organizations', sa.Column('ai_daily_limit', sa.Integer(), nullable=False, server_default='50'))
    
    # 2. Create ai_usage_daily table
    # Simple aggregated daily tracking. For audit logs, we'd use a different table, but this is for billing/quota.
    op.create_table('ai_usage_daily',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('usage_date', sa.Date(), nullable=False),
        sa.Column('request_count', sa.Integer(), default=0, nullable=False),
        sa.Column('token_count_input', sa.Integer(), default=0),
        sa.Column('token_count_output', sa.Integer(), default=0),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'usage_date', name='uq_org_daily_usage')
    )
    op.create_index(op.f('ix_ai_usage_daily_usage_date'), 'ai_usage_daily', ['usage_date'], unique=False)


def downgrade() -> None:
    op.drop_table('ai_usage_daily')
    op.drop_column('organizations', 'ai_daily_limit')

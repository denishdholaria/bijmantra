"""Add space research tables for interplanetary agriculture

Revision ID: 034
Revises: 033
Create Date: 2026-01-15

Tables created:
- space_crops: Crops suitable for space agriculture
- space_experiments: Space agriculture research experiments
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision = '034'
down_revision = '033'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== SPACE CROPS TABLE ====================
    op.create_table(
        'space_crops',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crop_code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('species', sa.String(255), nullable=False),
        sa.Column('space_heritage', sa.String(255), nullable=True),
        sa.Column('growth_cycle_days', sa.Integer(), nullable=True),
        sa.Column('caloric_yield', sa.Integer(), nullable=True),
        sa.Column('radiation_tolerance', sa.String(50), nullable=True),
        sa.Column('microgravity_adaptation', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_space_crops_crop_code', 'space_crops', ['crop_code'], unique=True)
    op.create_index('ix_space_crops_organization_id', 'space_crops', ['organization_id'])
    op.create_index('ix_space_crops_status', 'space_crops', ['status'])
    
    # ==================== SPACE EXPERIMENTS TABLE ====================
    op.create_table(
        'space_experiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('crop_id', sa.Integer(), sa.ForeignKey('space_crops.id'), nullable=True),
        sa.Column('crop_name', sa.String(255), nullable=True),
        sa.Column('environment', sa.String(100), nullable=True),
        sa.Column('parameters', JSON, nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('observations', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='planned'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_space_experiments_experiment_code', 'space_experiments', ['experiment_code'], unique=True)
    op.create_index('ix_space_experiments_organization_id', 'space_experiments', ['organization_id'])
    op.create_index('ix_space_experiments_crop_id', 'space_experiments', ['crop_id'])
    op.create_index('ix_space_experiments_status', 'space_experiments', ['status'])
    op.create_index('ix_space_experiments_crop_status', 'space_experiments', ['crop_id', 'status'])
    
    # ==================== ENABLE RLS ====================
    op.execute("ALTER TABLE space_crops ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE space_experiments ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE space_experiments DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE space_crops DISABLE ROW LEVEL SECURITY")
    
    op.drop_table('space_experiments')
    op.drop_table('space_crops')

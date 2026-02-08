"""Add storage_locations and field_scans tables

Revision ID: 047
Revises: 046
Create Date: 2026-02-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '047'
down_revision = '046'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Storage Locations (warehouse management)
    op.create_table(
        'storage_locations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('storage_type', sa.String(20), nullable=False, server_default='ambient'),
        sa.Column('capacity_kg', sa.Float(), nullable=False, server_default='0'),
        sa.Column('used_kg', sa.Float(), nullable=False, server_default='0'),
        sa.Column('current_temperature', sa.Float(), nullable=True),
        sa.Column('current_humidity', sa.Float(), nullable=True),
        sa.Column('target_temperature', sa.Float(), nullable=True),
        sa.Column('target_humidity', sa.Float(), nullable=True),
        sa.Column('lot_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='normal'),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_storage_locations_org_code', 'storage_locations', ['organization_id', 'code'], unique=True)

    # Field Scans
    op.create_table(
        'field_scans',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('plot_id', sa.String(100), nullable=True, index=True),
        sa.Column('study_id', sa.String(100), nullable=True, index=True),
        sa.Column('crop', sa.String(100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('results', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('notes', sa.String(2000), nullable=True),
        sa.Column('weather', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('field_scans')
    op.drop_index('ix_storage_locations_org_code', table_name='storage_locations')
    op.drop_table('storage_locations')

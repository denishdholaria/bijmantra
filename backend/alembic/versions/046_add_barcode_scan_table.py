"""Add barcode scan table

Revision ID: 046
Revises: 045
Create Date: 2026-02-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '046'
down_revision = '045'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'barcode_scans',
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('barcode_value', sa.String(length=255), nullable=False),
        sa.Column('scanned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scanned_by', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('found', sa.Boolean(), nullable=True),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.String(length=255), nullable=True),
        sa.Column('entity_name', sa.String(length=255), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_barcode_scans_id'), 'barcode_scans', ['id'], unique=False)
    op.create_index(op.f('ix_barcode_scans_organization_id'), 'barcode_scans', ['organization_id'], unique=False)
    op.create_index(op.f('ix_barcode_scans_barcode_value'), 'barcode_scans', ['barcode_value'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_barcode_scans_barcode_value'), table_name='barcode_scans')
    op.drop_index(op.f('ix_barcode_scans_organization_id'), table_name='barcode_scans')
    op.drop_index(op.f('ix_barcode_scans_id'), table_name='barcode_scans')
    op.drop_table('barcode_scans')

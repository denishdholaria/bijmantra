"""Add cross_id to germplasm for lineage tracking

Revision ID: 025
Revises: 024
Create Date: 2026-01-05

Jules Session: germplasm-progeny-impl-15629767980660815179
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '025'
down_revision = '024'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add cross_id column to germplasm table
    op.add_column('germplasm', sa.Column('cross_id', sa.Integer(), nullable=True))
    op.create_index('ix_germplasm_cross_id', 'germplasm', ['cross_id'], unique=False)
    op.create_foreign_key(
        'fk_germplasm_cross_id', 
        'germplasm', 
        'crosses', 
        ['cross_id'], 
        ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_germplasm_cross_id', 'germplasm', type_='foreignkey')
    op.drop_index('ix_germplasm_cross_id', table_name='germplasm')
    op.drop_column('germplasm', 'cross_id')

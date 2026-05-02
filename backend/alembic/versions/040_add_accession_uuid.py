"""Add accession_uuid column to seedlots table

Revision ID: 4096alpha
Revises: 231d109dc824
Create Date: 2026-01-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4096alpha'
down_revision = '231d109dc824'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add accession_uuid column generic implementation, targeting postgresql
    op.add_column('seedlots', sa.Column('accession_uuid', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_seedlots_accession_uuid'), 'seedlots', ['accession_uuid'], unique=False)
    op.create_foreign_key(None, 'seedlots', 'seed_bank_accessions', ['accession_uuid'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'seedlots', type_='foreignkey')
    op.drop_index(op.f('ix_seedlots_accession_uuid'), table_name='seedlots')
    op.drop_column('seedlots', 'accession_uuid')

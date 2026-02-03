"""Add research project flag to programs

Revision ID: 020
Revises: 019
Create Date: 2025-12-29

Adds is_research_project flag and research_context JSON to programs table
for DevGuru integration with BrAPI entities.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add research project flag to programs
    op.add_column('programs', sa.Column('is_research_project', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('programs', sa.Column('research_context', JSONB, nullable=True))
    
    # Add program_id to research_projects for linking
    op.add_column('research_projects', sa.Column('program_id', sa.Integer(), sa.ForeignKey('programs.id'), nullable=True))
    
    # Create index for research programs
    op.create_index('ix_programs_is_research_project', 'programs', ['is_research_project'])


def downgrade() -> None:
    op.drop_index('ix_programs_is_research_project', table_name='programs')
    op.drop_column('research_projects', 'program_id')
    op.drop_column('programs', 'research_context')
    op.drop_column('programs', 'is_research_project')

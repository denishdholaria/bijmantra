"""DevGuru research project tables

Revision ID: 019
Revises: 018
Create Date: 2025-12-29

Tables for PhD research project tracking and mentoring.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Research Projects table
    op.create_table(
        'research_projects',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('student_name', sa.String(200), nullable=False),
        sa.Column('supervisor', sa.String(200), nullable=True),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('expected_end_date', sa.Date, nullable=False),
        sa.Column('current_phase', sa.String(50), default='coursework'),
        sa.Column('research_area', sa.String(200), nullable=True),
        sa.Column('objectives', sa.Text, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Research Milestones table
    op.create_table(
        'research_milestones',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('project_id', sa.String(50), sa.ForeignKey('research_projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('phase', sa.String(50), nullable=False),
        sa.Column('target_date', sa.Date, nullable=False),
        sa.Column('completed_date', sa.Date, nullable=True),
        sa.Column('status', sa.String(50), default='not_started'),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('research_milestones')
    op.drop_table('research_projects')

"""DevGuru Phases 3, 4, 5 - Literature, Writing, Collaboration

Revision ID: 021
Revises: 020
Create Date: 2025-12-29

Phase 3: Literature Integration - papers, citations, literature reviews
Phase 4: Writing Assistant - chapters, drafts, word counts
Phase 5: Collaboration - committee members, meetings, feedback
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Phase 3: Literature Integration
    op.create_table(
        'research_papers',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('project_id', sa.String(50), sa.ForeignKey('research_projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('authors', sa.Text),  # JSON array
        sa.Column('journal', sa.String(300)),
        sa.Column('year', sa.Integer),
        sa.Column('doi', sa.String(200)),
        sa.Column('url', sa.String(500)),
        sa.Column('abstract', sa.Text),
        sa.Column('notes', sa.Text),
        sa.Column('tags', sa.Text),  # JSON array
        sa.Column('relevance_score', sa.Integer),  # 1-5
        sa.Column('read_status', sa.String(50), default='unread'),  # unread, reading, read
        sa.Column('citation_key', sa.String(100)),  # BibTeX key
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    op.create_table(
        'paper_experiment_links',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('paper_id', sa.String(50), sa.ForeignKey('research_papers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('trial_id', sa.Integer, sa.ForeignKey('trials.id', ondelete='CASCADE'), nullable=True),
        sa.Column('study_id', sa.Integer, sa.ForeignKey('studies.id', ondelete='CASCADE'), nullable=True),
        sa.Column('link_type', sa.String(50)),  # supports, contradicts, extends, methodology
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    
    # Phase 4: Writing Assistant
    op.create_table(
        'thesis_chapters',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('project_id', sa.String(50), sa.ForeignKey('research_projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('chapter_number', sa.Integer, nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('chapter_type', sa.String(50)),  # introduction, literature_review, methodology, results, discussion, conclusion
        sa.Column('target_word_count', sa.Integer, default=5000),
        sa.Column('current_word_count', sa.Integer, default=0),
        sa.Column('status', sa.String(50), default='not_started'),  # not_started, drafting, review, revision, complete
        sa.Column('outline', sa.Text),  # JSON structure
        sa.Column('notes', sa.Text),
        sa.Column('target_date', sa.Date),
        sa.Column('completed_date', sa.Date),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    op.create_table(
        'writing_sessions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('chapter_id', sa.String(50), sa.ForeignKey('thesis_chapters.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('session_date', sa.Date, nullable=False),
        sa.Column('words_written', sa.Integer, default=0),
        sa.Column('duration_minutes', sa.Integer),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    
    # Phase 5: Collaboration
    op.create_table(
        'committee_members',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('project_id', sa.String(50), sa.ForeignKey('research_projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('role', sa.String(50)),  # supervisor, co_supervisor, committee, external
        sa.Column('institution', sa.String(300)),
        sa.Column('expertise', sa.String(300)),
        sa.Column('notes', sa.Text),
        sa.Column('is_primary', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    op.create_table(
        'committee_meetings',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('project_id', sa.String(50), sa.ForeignKey('research_projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('meeting_type', sa.String(50)),  # progress, proposal, defense, informal
        sa.Column('scheduled_date', sa.DateTime, nullable=False),
        sa.Column('duration_minutes', sa.Integer, default=60),
        sa.Column('location', sa.String(300)),
        sa.Column('agenda', sa.Text),
        sa.Column('minutes', sa.Text),
        sa.Column('action_items', sa.Text),  # JSON array
        sa.Column('status', sa.String(50), default='scheduled'),  # scheduled, completed, cancelled
        sa.Column('attendees', sa.Text),  # JSON array of committee_member IDs
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    op.create_table(
        'feedback_items',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('project_id', sa.String(50), sa.ForeignKey('research_projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('chapter_id', sa.String(50), sa.ForeignKey('thesis_chapters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('meeting_id', sa.String(50), sa.ForeignKey('committee_meetings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('from_member_id', sa.String(50), sa.ForeignKey('committee_members.id', ondelete='SET NULL'), nullable=True),
        sa.Column('feedback_type', sa.String(50)),  # suggestion, correction, question, praise
        sa.Column('priority', sa.String(50), default='medium'),  # low, medium, high, critical
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('response', sa.Text),
        sa.Column('status', sa.String(50), default='pending'),  # pending, in_progress, addressed, dismissed
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Indexes are already created with the tables via index=True on ForeignKey columns
    # No need for explicit create_index calls


def downgrade() -> None:
    op.drop_table('feedback_items')
    op.drop_table('committee_meetings')
    op.drop_table('committee_members')
    op.drop_table('writing_sessions')
    op.drop_table('thesis_chapters')
    op.drop_table('paper_experiment_links')
    op.drop_table('research_papers')

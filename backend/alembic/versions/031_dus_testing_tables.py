"""Add DUS testing tables for variety protection

Revision ID: 031
Revises: 030
Create Date: 2026-01-15

Tables created:
- dus_trials: Main DUS trial records
- dus_entries: Variety entries in trials (candidate/reference)
- dus_scores: Character observation scores
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '031'
down_revision = '030'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== DUS TRIALS TABLE ====================
    op.create_table(
        'dus_trials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trial_code', sa.String(50), nullable=False, unique=True),
        sa.Column('trial_name', sa.String(255), nullable=False),
        sa.Column('crop_code', sa.String(50), nullable=False),  # rice, wheat, maize
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('status', sa.String(50), nullable=False, server_default='planned'),
        sa.Column('distinctness_result', sa.String(20), nullable=True),
        sa.Column('uniformity_result', sa.String(20), nullable=True),
        sa.Column('stability_result', sa.String(20), nullable=True),
        sa.Column('overall_result', sa.String(20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('report_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dus_trials_organization_id', 'dus_trials', ['organization_id'])
    op.create_index('ix_dus_trials_crop_code', 'dus_trials', ['crop_code'])
    op.create_index('ix_dus_trials_year', 'dus_trials', ['year'])
    op.create_index('ix_dus_trials_status', 'dus_trials', ['status'])
    op.create_index('ix_dus_trials_year_crop', 'dus_trials', ['year', 'crop_code'])
    
    # ==================== DUS ENTRIES TABLE ====================
    op.create_table(
        'dus_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trial_id', sa.Integer(), sa.ForeignKey('dus_trials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entry_code', sa.String(50), nullable=False),  # E1, E2, etc.
        sa.Column('variety_name', sa.String(255), nullable=False),
        sa.Column('is_candidate', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_reference', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('breeder', sa.String(255), nullable=True),
        sa.Column('origin', sa.String(255), nullable=True),
        sa.Column('germplasm_id', sa.Integer(), sa.ForeignKey('germplasm.id'), nullable=True),
        sa.Column('off_type_count', sa.Integer(), nullable=True),
        sa.Column('uniformity_passed', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dus_entries_trial_id', 'dus_entries', ['trial_id'])
    op.create_index('ix_dus_entries_germplasm_id', 'dus_entries', ['germplasm_id'])
    op.create_index('ix_dus_entries_trial_entry', 'dus_entries', ['trial_id', 'entry_code'], unique=True)
    
    # ==================== DUS SCORES TABLE ====================
    op.create_table(
        'dus_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entry_id', sa.Integer(), sa.ForeignKey('dus_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('character_id', sa.String(50), nullable=False),  # rice_1, wheat_4, etc.
        sa.Column('value', sa.Float(), nullable=True),  # State code or measurement
        sa.Column('value_text', sa.String(255), nullable=True),  # Text description
        sa.Column('observation_year', sa.Integer(), nullable=True),  # 1 or 2
        sa.Column('scored_by', sa.String(255), nullable=True),
        sa.Column('scored_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dus_scores_entry_id', 'dus_scores', ['entry_id'])
    op.create_index('ix_dus_scores_character_id', 'dus_scores', ['character_id'])
    op.create_index('ix_dus_scores_entry_char_year', 'dus_scores', ['entry_id', 'character_id', 'observation_year'])
    
    # ==================== ENABLE RLS ====================
    op.execute("ALTER TABLE dus_trials ENABLE ROW LEVEL SECURITY")
    # dus_entries and dus_scores inherit RLS through trial_id FK


def downgrade() -> None:
    op.execute("ALTER TABLE dus_trials DISABLE ROW LEVEL SECURITY")
    
    op.drop_table('dus_scores')
    op.drop_table('dus_entries')
    op.drop_table('dus_trials')

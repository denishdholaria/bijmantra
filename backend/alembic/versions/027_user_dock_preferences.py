"""Add user dock preferences table for Mahasarthi navigation

Revision ID: 027
Revises: 026
Create Date: 2026-01-07

Stores user dock preferences (pinned pages, recent pages) for the
Mahasarthi navigation system. Enables cross-device sync and
role-based defaults.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision = '027'
down_revision = '026'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_dock_preferences table
    op.create_table(
        'user_dock_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        
        # Dock items stored as JSON arrays
        sa.Column('pinned_items', JSON, nullable=False, server_default='[]'),
        sa.Column('recent_items', JSON, nullable=False, server_default='[]'),
        
        # Dock preferences
        sa.Column('max_pinned', sa.Integer(), nullable=False, server_default='8'),
        sa.Column('max_recent', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('show_labels', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('compact_mode', sa.Boolean(), nullable=False, server_default='false'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', name='uq_user_dock_preferences_user_id'),
    )
    
    # Create indexes
    op.create_index('ix_user_dock_preferences_organization_id', 'user_dock_preferences', ['organization_id'])
    op.create_index('ix_user_dock_preferences_user_id', 'user_dock_preferences', ['user_id'])
    
    # Enable RLS
    op.execute('ALTER TABLE user_dock_preferences ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policy
    op.execute('''
        CREATE POLICY user_dock_preferences_org_isolation ON user_dock_preferences
        FOR ALL
        USING (organization_id = current_setting('app.current_organization_id', true)::integer)
        WITH CHECK (organization_id = current_setting('app.current_organization_id', true)::integer)
    ''')


def downgrade() -> None:
    # Drop RLS policy
    op.execute('DROP POLICY IF EXISTS user_dock_preferences_org_isolation ON user_dock_preferences')
    
    # Drop indexes
    op.drop_index('ix_user_dock_preferences_user_id', table_name='user_dock_preferences')
    op.drop_index('ix_user_dock_preferences_organization_id', table_name='user_dock_preferences')
    
    # Drop table
    op.drop_table('user_dock_preferences')

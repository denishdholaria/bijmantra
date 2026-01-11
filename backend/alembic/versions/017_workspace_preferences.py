"""Add workspace preference fields to user_preferences

Revision ID: 017
Revises: 016
Create Date: 2025-12-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add workspace preference columns to user_preferences table"""
    
    # Add workspace preference columns
    op.add_column('user_preferences', 
        sa.Column('default_workspace', sa.String(20), nullable=True,
                  comment='Default workspace: breeding, seed-ops, research, genebank, admin'))
    
    op.add_column('user_preferences',
        sa.Column('recent_workspaces', sa.JSON(), nullable=True, server_default='[]',
                  comment='List of recently used workspace IDs'))
    
    op.add_column('user_preferences',
        sa.Column('show_gateway_on_login', sa.Boolean(), nullable=True, server_default='true',
                  comment='Whether to show workspace gateway on login'))
    
    op.add_column('user_preferences',
        sa.Column('last_workspace', sa.String(20), nullable=True,
                  comment='Last active workspace'))
    
    # Add index for default_workspace for faster lookups
    op.create_index(
        'ix_user_preferences_default_workspace',
        'user_preferences',
        ['default_workspace'],
        unique=False
    )


def downgrade() -> None:
    """Remove workspace preference columns"""
    
    op.drop_index('ix_user_preferences_default_workspace', table_name='user_preferences')
    op.drop_column('user_preferences', 'last_workspace')
    op.drop_column('user_preferences', 'show_gateway_on_login')
    op.drop_column('user_preferences', 'recent_workspaces')
    op.drop_column('user_preferences', 'default_workspace')

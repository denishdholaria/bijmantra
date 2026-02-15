"""Add chat messages tables

Revision ID: 026
Revises: 025
Create Date: 2026-01-05

Jules Session: add-chat-messages-table-11087981545318719513
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '026'
down_revision = '025'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ConversationType enum
    op.execute("""
        CREATE TYPE conversationtype AS ENUM ('direct', 'group', 'team');
    """)

    # Conversations
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('type', postgresql.ENUM('direct', 'group', 'team', name='conversationtype', create_type=False), server_default='direct'),
        sa.Column('workspace_id', sa.Integer()),
        sa.Column('last_message_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['workspace_id'], ['collaboration_workspaces.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversations_organization_id', 'conversations', ['organization_id'])
    op.create_index('ix_conversations_workspace_id', 'conversations', ['workspace_id'])

    # Conversation Participants
    op.create_table(
        'conversation_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('last_read_at', sa.DateTime()),
        sa.Column('joined_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id', 'user_id', name='uq_conversation_participant')
    )
    op.create_index('ix_conversation_participants_conversation_id', 'conversation_participants', ['conversation_id'])
    op.create_index('ix_conversation_participants_user_id', 'conversation_participants', ['user_id'])

    # Messages
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_system', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_sender_id', 'messages', ['sender_id'])

    # Enable RLS on all new tables
    for table in ['conversations', 'conversation_participants', 'messages']:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    
    # RLS policy for conversations
    op.execute("""
        CREATE POLICY conversations_org_isolation ON conversations
        USING (organization_id = current_setting('app.current_organization_id', true)::integer)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS conversations_org_isolation ON conversations")
    
    op.drop_table('messages')
    op.drop_table('conversation_participants')
    op.drop_table('conversations')

    op.execute("DROP TYPE IF EXISTS conversationtype;")

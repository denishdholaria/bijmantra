"""add_veena_cognitive_v2

Revision ID: c2e7af1f4b10
Revises: 8ab6bae802c6
Create Date: 2026-02-15 14:00:00.000000+00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c2e7af1f4b10'
down_revision = '8ab6bae802c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'veena_memories_v2',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('context_tags', sa.JSON(), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('pinned', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('ttl_days', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_veena_memories_v2_user_id', 'veena_memories_v2', ['user_id'])
    op.create_index('ix_veena_memories_v2_created_at', 'veena_memories_v2', ['created_at'])

    op.create_table(
        'veena_reasoning_traces_v2',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.String(length=128), nullable=False),
        sa.Column('step_id', sa.String(length=128), nullable=False),
        sa.Column('thought', sa.Text(), nullable=False),
        sa.Column('tool_used', sa.String(length=128), nullable=True),
        sa.Column('outcome', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_reasoning_trace_v2_session', 'veena_reasoning_traces_v2', ['session_id'])
    op.create_index('ix_reasoning_trace_v2_session_step', 'veena_reasoning_traces_v2', ['session_id', 'step_id'], unique=True)

    op.create_table(
        'veena_user_contexts_v2',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('preferences', sa.JSON(), nullable=False),
        sa.Column('expertise_level', sa.String(length=64), nullable=False, server_default='manager'),
        sa.Column('active_project', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_veena_user_contexts_v2_user_id', 'veena_user_contexts_v2', ['user_id'], unique=True)

    op.create_table(
        'veena_audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=128), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('generated_draft', sa.Text(), nullable=False),
        sa.Column('flagged_sensitive', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # pgvector index creation (Postgres only; safe no-op in other engines)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_veena_memories_v2_embedding
        ON veena_memories_v2 USING ivfflat ((embedding::vector(32)) vector_cosine_ops)
        """
    )

    # RLS: users can access only their own memories
    op.execute("ALTER TABLE veena_memories_v2 ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY IF NOT EXISTS veena_memories_v2_user_scope
        ON veena_memories_v2
        USING (user_id = current_setting('app.current_user_id', true)::int)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS veena_memories_v2_user_scope ON veena_memories_v2")
    op.drop_table('veena_audit_logs')
    op.drop_index('ix_veena_user_contexts_v2_user_id', table_name='veena_user_contexts_v2')
    op.drop_table('veena_user_contexts_v2')
    op.drop_index('ix_reasoning_trace_v2_session_step', table_name='veena_reasoning_traces_v2')
    op.drop_index('ix_reasoning_trace_v2_session', table_name='veena_reasoning_traces_v2')
    op.drop_table('veena_reasoning_traces_v2')
    op.drop_index('ix_veena_memories_v2_created_at', table_name='veena_memories_v2')
    op.drop_index('ix_veena_memories_v2_user_id', table_name='veena_memories_v2')
    op.drop_table('veena_memories_v2')

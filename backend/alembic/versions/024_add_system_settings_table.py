"""Add system_settings table

Revision ID: 024
Revises: 023
Create Date: 2026-01-05

Jules Session: system-settings-table-13560479686725070815
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'category', name='uq_system_settings_org_category')
    )
    op.create_index('ix_system_settings_organization_id', 'system_settings', ['organization_id'])
    op.create_index('ix_system_settings_category', 'system_settings', ['category'])
    
    # Enable RLS
    op.execute("ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY system_settings_org_isolation ON system_settings
        USING (organization_id = current_setting('app.current_organization_id', true)::integer)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS system_settings_org_isolation ON system_settings")
    op.drop_index('ix_system_settings_category', table_name='system_settings')
    op.drop_index('ix_system_settings_organization_id', table_name='system_settings')
    op.drop_table('system_settings')

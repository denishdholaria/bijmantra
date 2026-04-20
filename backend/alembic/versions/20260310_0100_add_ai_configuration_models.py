"""Add persisted AI provider and REEVU agent configuration tables.

Revision ID: 20260310_0100
Revises: 20260217_0000
Create Date: 2026-03-10 01:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20260310_0100'
down_revision = '20260217_0000'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.create_table(
		'ai_providers',
		sa.Column('organization_id', sa.Integer(), nullable=False),
		sa.Column('provider_key', sa.String(length=50), nullable=False),
		sa.Column('display_name', sa.String(length=255), nullable=False),
		sa.Column('base_url', sa.String(length=500), nullable=True),
		sa.Column('auth_mode', sa.String(length=50), nullable=False, server_default='api_key'),
		sa.Column('encrypted_api_key', sa.Text(), nullable=True),
		sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
		sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
		sa.Column('is_byok_allowed', sa.Boolean(), nullable=False, server_default=sa.true()),
		sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
		sa.Column('id', sa.Integer(), nullable=False),
		sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
		sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
		sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
		sa.PrimaryKeyConstraint('id'),
		sa.UniqueConstraint('organization_id', 'provider_key', name='uq_ai_provider_org_key'),
	)
	op.create_index(op.f('ix_ai_providers_id'), 'ai_providers', ['id'], unique=False)
	op.create_index(op.f('ix_ai_providers_organization_id'), 'ai_providers', ['organization_id'], unique=False)
	op.create_index(op.f('ix_ai_providers_provider_key'), 'ai_providers', ['provider_key'], unique=False)

	op.create_table(
		'ai_provider_models',
		sa.Column('organization_id', sa.Integer(), nullable=False),
		sa.Column('provider_id', sa.Integer(), nullable=False),
		sa.Column('model_name', sa.String(length=255), nullable=False),
		sa.Column('display_name', sa.String(length=255), nullable=True),
		sa.Column('capability_tags', postgresql.ARRAY(sa.String()), nullable=True),
		sa.Column('max_tokens', sa.Integer(), nullable=True),
		sa.Column('temperature', sa.Float(), nullable=True),
		sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()),
		sa.Column('is_streaming_supported', sa.Boolean(), nullable=False, server_default=sa.false()),
		sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
		sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
		sa.Column('id', sa.Integer(), nullable=False),
		sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
		sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
		sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
		sa.ForeignKeyConstraint(['provider_id'], ['ai_providers.id']),
		sa.PrimaryKeyConstraint('id'),
		sa.UniqueConstraint('provider_id', 'model_name', name='uq_ai_provider_model_name'),
	)
	op.create_index(op.f('ix_ai_provider_models_id'), 'ai_provider_models', ['id'], unique=False)
	op.create_index(op.f('ix_ai_provider_models_organization_id'), 'ai_provider_models', ['organization_id'], unique=False)
	op.create_index(op.f('ix_ai_provider_models_provider_id'), 'ai_provider_models', ['provider_id'], unique=False)

	op.create_table(
		'reevu_agent_settings',
		sa.Column('organization_id', sa.Integer(), nullable=False),
		sa.Column('agent_key', sa.String(length=100), nullable=False),
		sa.Column('display_name', sa.String(length=255), nullable=True),
		sa.Column('provider_id', sa.Integer(), nullable=True),
		sa.Column('provider_model_id', sa.Integer(), nullable=True),
		sa.Column('system_prompt_override', sa.Text(), nullable=True),
		sa.Column('tool_policy', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
		sa.Column('default_task_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
		sa.Column('sampling_temperature', sa.Float(), nullable=True),
		sa.Column('max_tokens', sa.Integer(), nullable=True),
		sa.Column('capability_overrides', postgresql.ARRAY(sa.String()), nullable=True),
		sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
		sa.Column('id', sa.Integer(), nullable=False),
		sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
		sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
		sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
		sa.ForeignKeyConstraint(['provider_id'], ['ai_providers.id']),
		sa.ForeignKeyConstraint(['provider_model_id'], ['ai_provider_models.id']),
		sa.PrimaryKeyConstraint('id'),
		sa.UniqueConstraint('organization_id', 'agent_key', name='uq_reevu_agent_org_key'),
	)
	op.create_index(op.f('ix_reevu_agent_settings_agent_key'), 'reevu_agent_settings', ['agent_key'], unique=False)
	op.create_index(op.f('ix_reevu_agent_settings_id'), 'reevu_agent_settings', ['id'], unique=False)
	op.create_index(op.f('ix_reevu_agent_settings_organization_id'), 'reevu_agent_settings', ['organization_id'], unique=False)
	op.create_index(op.f('ix_reevu_agent_settings_provider_id'), 'reevu_agent_settings', ['provider_id'], unique=False)
	op.create_index(op.f('ix_reevu_agent_settings_provider_model_id'), 'reevu_agent_settings', ['provider_model_id'], unique=False)

	op.execute(
		"""
		ALTER TABLE ai_providers ENABLE ROW LEVEL SECURITY;
		ALTER TABLE ai_providers FORCE ROW LEVEL SECURITY;
		DROP POLICY IF EXISTS ai_providers_tenant_isolation ON ai_providers;
		CREATE POLICY ai_providers_tenant_isolation ON ai_providers
			FOR ALL
			USING (organization_id = current_organization_id() OR current_organization_id() = 0)
			WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);

		ALTER TABLE ai_provider_models ENABLE ROW LEVEL SECURITY;
		ALTER TABLE ai_provider_models FORCE ROW LEVEL SECURITY;
		DROP POLICY IF EXISTS ai_provider_models_tenant_isolation ON ai_provider_models;
		CREATE POLICY ai_provider_models_tenant_isolation ON ai_provider_models
			FOR ALL
			USING (organization_id = current_organization_id() OR current_organization_id() = 0)
			WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);

		ALTER TABLE reevu_agent_settings ENABLE ROW LEVEL SECURITY;
		ALTER TABLE reevu_agent_settings FORCE ROW LEVEL SECURITY;
		DROP POLICY IF EXISTS reevu_agent_settings_tenant_isolation ON reevu_agent_settings;
		CREATE POLICY reevu_agent_settings_tenant_isolation ON reevu_agent_settings
			FOR ALL
			USING (organization_id = current_organization_id() OR current_organization_id() = 0)
			WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);
		"""
	)


def downgrade() -> None:
	op.execute("DROP POLICY IF EXISTS reevu_agent_settings_tenant_isolation ON reevu_agent_settings")
	op.execute("ALTER TABLE reevu_agent_settings DISABLE ROW LEVEL SECURITY")
	op.execute("DROP POLICY IF EXISTS ai_provider_models_tenant_isolation ON ai_provider_models")
	op.execute("ALTER TABLE ai_provider_models DISABLE ROW LEVEL SECURITY")
	op.execute("DROP POLICY IF EXISTS ai_providers_tenant_isolation ON ai_providers")
	op.execute("ALTER TABLE ai_providers DISABLE ROW LEVEL SECURITY")

	op.drop_index(op.f('ix_reevu_agent_settings_provider_model_id'), table_name='reevu_agent_settings')
	op.drop_index(op.f('ix_reevu_agent_settings_provider_id'), table_name='reevu_agent_settings')
	op.drop_index(op.f('ix_reevu_agent_settings_organization_id'), table_name='reevu_agent_settings')
	op.drop_index(op.f('ix_reevu_agent_settings_id'), table_name='reevu_agent_settings')
	op.drop_index(op.f('ix_reevu_agent_settings_agent_key'), table_name='reevu_agent_settings')
	op.drop_table('reevu_agent_settings')

	op.drop_index(op.f('ix_ai_provider_models_provider_id'), table_name='ai_provider_models')
	op.drop_index(op.f('ix_ai_provider_models_organization_id'), table_name='ai_provider_models')
	op.drop_index(op.f('ix_ai_provider_models_id'), table_name='ai_provider_models')
	op.drop_table('ai_provider_models')

	op.drop_index(op.f('ix_ai_providers_provider_key'), table_name='ai_providers')
	op.drop_index(op.f('ix_ai_providers_organization_id'), table_name='ai_providers')
	op.drop_index(op.f('ix_ai_providers_id'), table_name='ai_providers')
	op.drop_table('ai_providers')
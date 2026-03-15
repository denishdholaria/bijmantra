"""Add REEVU routing policies.

Revision ID: 20260311_0400
Revises: 20260311_0300
Create Date: 2026-03-11 04:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '20260311_0400'
down_revision = '20260311_0300'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.create_table(
		'reevu_routing_policies',
		sa.Column('organization_id', sa.Integer(), nullable=False),
		sa.Column('agent_key', sa.String(length=100), nullable=False),
		sa.Column('display_name', sa.String(length=255), nullable=True),
		sa.Column('preferred_provider_id', sa.Integer(), nullable=True),
		sa.Column('preferred_provider_model_id', sa.Integer(), nullable=True),
		sa.Column('fallback_to_priority_order', sa.Boolean(), nullable=False, server_default=sa.true()),
		sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
		sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
		sa.Column('id', sa.Integer(), nullable=False),
		sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
		sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
		sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
		sa.ForeignKeyConstraint(['preferred_provider_id'], ['ai_providers.id']),
		sa.ForeignKeyConstraint(['preferred_provider_model_id'], ['ai_provider_models.id']),
		sa.PrimaryKeyConstraint('id'),
		sa.UniqueConstraint('organization_id', 'agent_key', name='uq_reevu_routing_policy_org_key'),
	)
	op.create_index(op.f('ix_reevu_routing_policies_id'), 'reevu_routing_policies', ['id'], unique=False)
	op.create_index(op.f('ix_reevu_routing_policies_organization_id'), 'reevu_routing_policies', ['organization_id'], unique=False)
	op.create_index(op.f('ix_reevu_routing_policies_agent_key'), 'reevu_routing_policies', ['agent_key'], unique=False)
	op.create_index(op.f('ix_reevu_routing_policies_preferred_provider_id'), 'reevu_routing_policies', ['preferred_provider_id'], unique=False)
	op.create_index(op.f('ix_reevu_routing_policies_preferred_provider_model_id'), 'reevu_routing_policies', ['preferred_provider_model_id'], unique=False)

	op.execute(
		"""
		ALTER TABLE reevu_routing_policies ENABLE ROW LEVEL SECURITY;
		ALTER TABLE reevu_routing_policies FORCE ROW LEVEL SECURITY;
		DROP POLICY IF EXISTS reevu_routing_policies_tenant_isolation ON reevu_routing_policies;
		CREATE POLICY reevu_routing_policies_tenant_isolation ON reevu_routing_policies
			FOR ALL
			USING (organization_id = current_organization_id() OR current_organization_id() = 0)
			WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);
		"""
	)


def downgrade() -> None:
	op.execute("DROP POLICY IF EXISTS reevu_routing_policies_tenant_isolation ON reevu_routing_policies")
	op.execute("ALTER TABLE reevu_routing_policies DISABLE ROW LEVEL SECURITY")
	op.drop_index(op.f('ix_reevu_routing_policies_preferred_provider_model_id'), table_name='reevu_routing_policies')
	op.drop_index(op.f('ix_reevu_routing_policies_preferred_provider_id'), table_name='reevu_routing_policies')
	op.drop_index(op.f('ix_reevu_routing_policies_agent_key'), table_name='reevu_routing_policies')
	op.drop_index(op.f('ix_reevu_routing_policies_organization_id'), table_name='reevu_routing_policies')
	op.drop_index(op.f('ix_reevu_routing_policies_id'), table_name='reevu_routing_policies')
	op.drop_table('reevu_routing_policies')
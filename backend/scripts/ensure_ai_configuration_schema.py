"""Ensure AI configuration persistence tables exist.

This is a targeted recovery script for local development environments where the
Alembic history is temporarily inconsistent but REEVU operator configuration
still needs the persisted AI settings schema.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, engine
from app.models.ai_configuration import AIProvider, AIProviderModel, ReevuAgentSetting, ReevuRoutingPolicy


TABLES = [
	AIProvider.__table__,
	AIProviderModel.__table__,
	ReevuAgentSetting.__table__,
	ReevuRoutingPolicy.__table__,
]


POLICY_STATEMENTS = [
	"ALTER TABLE ai_providers ENABLE ROW LEVEL SECURITY",
	"ALTER TABLE ai_providers FORCE ROW LEVEL SECURITY",
	"DROP POLICY IF EXISTS ai_providers_tenant_isolation ON ai_providers",
	(
		"CREATE POLICY ai_providers_tenant_isolation ON ai_providers "
		"FOR ALL USING (organization_id = current_organization_id() OR current_organization_id() = 0) "
		"WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0)"
	),
	"ALTER TABLE ai_provider_models ENABLE ROW LEVEL SECURITY",
	"ALTER TABLE ai_provider_models FORCE ROW LEVEL SECURITY",
	"DROP POLICY IF EXISTS ai_provider_models_tenant_isolation ON ai_provider_models",
	(
		"CREATE POLICY ai_provider_models_tenant_isolation ON ai_provider_models "
		"FOR ALL USING (organization_id = current_organization_id() OR current_organization_id() = 0) "
		"WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0)"
	),
	"ALTER TABLE reevu_agent_settings ENABLE ROW LEVEL SECURITY",
	"ALTER TABLE reevu_agent_settings FORCE ROW LEVEL SECURITY",
	"DROP POLICY IF EXISTS reevu_agent_settings_tenant_isolation ON reevu_agent_settings",
	(
		"CREATE POLICY reevu_agent_settings_tenant_isolation ON reevu_agent_settings "
		"FOR ALL USING (organization_id = current_organization_id() OR current_organization_id() = 0) "
		"WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0)"
	),
	"ALTER TABLE reevu_routing_policies ENABLE ROW LEVEL SECURITY",
	"ALTER TABLE reevu_routing_policies FORCE ROW LEVEL SECURITY",
	"DROP POLICY IF EXISTS reevu_routing_policies_tenant_isolation ON reevu_routing_policies",
	(
		"CREATE POLICY reevu_routing_policies_tenant_isolation ON reevu_routing_policies "
		"FOR ALL USING (organization_id = current_organization_id() OR current_organization_id() = 0) "
		"WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0)"
	),
]


async def ensure_ai_configuration_schema() -> None:
	async with engine.begin() as conn:
		await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=TABLES, checkfirst=True))
		for statement in POLICY_STATEMENTS:
			await conn.execute(text(statement))


if __name__ == "__main__":
	asyncio.run(ensure_ai_configuration_schema())
	print("AI configuration schema ensured")
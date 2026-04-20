import httpx
import pytest

from app.core.tracing import TRACE_ID_HEADER, trace_context
from app.modules.ai.services.project_brain_memory_surreal_schema import (
    ProjectBrainSurrealSchemaManager,
    build_project_brain_surreal_schema_statements,
)
from tests.units.services.project_brain_surreal_testkit import (
    MockSurrealHttpServer,
    project_brain_surreal_test_config,
)


@pytest.mark.asyncio
async def test_surreal_schema_manager_defines_tables_and_indexes():
    config = project_brain_surreal_test_config()
    server = MockSurrealHttpServer(namespace=config.namespace, database=config.database)
    manager = ProjectBrainSurrealSchemaManager(config, transport=httpx.MockTransport(server))

    try:
        with trace_context("schema-trace-12345678"):
            report = await manager.ensure_schema()

        assert report.namespace == config.namespace
        assert report.database == config.database
        assert report.table_count == 5
        assert report.statement_count == len(build_project_brain_surreal_schema_statements(config))
        assert report.index_count == report.statement_count - 7
        assert len(server.sql_payloads) == 1
        sql_payload = server.sql_payloads[0]
        assert f"DEFINE NAMESPACE IF NOT EXISTS {config.namespace}" in sql_payload
        assert f"DEFINE DATABASE IF NOT EXISTS {config.database}" in sql_payload
        assert f"DEFINE TABLE IF NOT EXISTS {config.memory_node_table} SCHEMALESS TYPE NORMAL" in sql_payload
        assert f"DEFINE INDEX IF NOT EXISTS memory_node_title_idx ON TABLE {config.memory_node_table}" in sql_payload
        assert all(request.headers.get("Surreal-NS") == config.namespace for request in server.requests)
        assert all(request.headers.get("Surreal-DB") == config.database for request in server.requests)
        assert all(request.headers.get(TRACE_ID_HEADER) == "schema-trace-12345678" for request in server.requests)
    finally:
        await manager.aclose()

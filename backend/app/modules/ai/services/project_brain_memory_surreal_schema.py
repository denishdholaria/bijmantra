"""Schema bootstrap for the project-brain SurrealDB sidecar.

primary_domain = "ai_orchestration"
secondary_domains = ["knowledge_management", "operations", "developer_experience"]
assumptions = [
    "The project-brain sidecar should have explicit SurrealDB tables and lookup indexes before persistent usage grows.",
    "Schema bootstrap should remain subordinate to the storage-neutral repository contract and must not promote the sidecar into an authority surface.",
    "The same namespace and database identity used by the repository adapter should drive schema bootstrap."
]
limitations = [
    "This bootstrap defines schemaless normal tables and practical lookup indexes only.",
    "It does not attempt graph-native relation modeling or migration/version orchestration.",
    "It relies on root or sufficiently privileged credentials to execute DEFINE statements."
]
uncertainty_handling = "The first schema slice keeps the sidecar explicit and query-ready without prematurely forcing a graph-native or strict-schema commitment."
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.http_tracing import create_traced_async_client
from app.modules.ai.services.project_brain_memory_surreal import ProjectBrainSurrealConnectionConfig


@dataclass(frozen=True, slots=True)
class ProjectBrainSurrealSchemaBootstrapReport:
    namespace: str
    database: str
    statement_count: int
    table_count: int
    index_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "database": self.database,
            "statement_count": self.statement_count,
            "table_count": self.table_count,
            "index_count": self.index_count,
        }


class ProjectBrainSurrealSchemaBootstrapError(RuntimeError):
    pass


def build_project_brain_surreal_schema_statements(
    config: ProjectBrainSurrealConnectionConfig,
) -> tuple[str, ...]:
    return (
        (
            f'DEFINE NAMESPACE IF NOT EXISTS {config.namespace} '
            'COMMENT "Being Bijmantra project-brain namespace";'
        ),
        (
            f'DEFINE DATABASE IF NOT EXISTS {config.database} '
            'COMMENT "Non-authoritative Being Bijmantra project-brain sidecar lane";'
        ),
        (
            f'DEFINE TABLE IF NOT EXISTS {config.source_artifact_table} SCHEMALESS TYPE NORMAL '
            'PERMISSIONS NONE COMMENT "Project-brain source artifacts";'
        ),
        (
            f'DEFINE TABLE IF NOT EXISTS {config.projection_table} SCHEMALESS TYPE NORMAL '
            'PERMISSIONS NONE COMMENT "Project-brain projections";'
        ),
        (
            f'DEFINE TABLE IF NOT EXISTS {config.memory_node_table} SCHEMALESS TYPE NORMAL '
            'PERMISSIONS NONE COMMENT "Project-brain memory nodes";'
        ),
        (
            f'DEFINE TABLE IF NOT EXISTS {config.memory_edge_table} SCHEMALESS TYPE NORMAL '
            'PERMISSIONS NONE COMMENT "Project-brain memory edges";'
        ),
        (
            f'DEFINE TABLE IF NOT EXISTS {config.correction_table} SCHEMALESS TYPE NORMAL '
            'PERMISSIONS NONE COMMENT "Project-brain correction records";'
        ),
        (
            f'DEFINE INDEX IF NOT EXISTS source_artifact_path_idx ON TABLE {config.source_artifact_table} '
            'COLUMNS source_path;'
        ),
        (
            f'DEFINE INDEX IF NOT EXISTS source_artifact_surface_kind_idx ON TABLE {config.source_artifact_table} '
            'COLUMNS source_surface, source_kind;'
        ),
        (
            f'DEFINE INDEX IF NOT EXISTS source_artifact_authority_idx ON TABLE {config.source_artifact_table} '
            'COLUMNS authority_class;'
        ),
        (
            f'DEFINE INDEX IF NOT EXISTS projection_source_idx ON TABLE {config.projection_table} '
            'COLUMNS source_id;'
        ),
        (
            f'DEFINE INDEX IF NOT EXISTS projection_type_rank_scope_idx ON TABLE {config.projection_table} '
            'COLUMNS projection_type, trust_rank, scope;'
        ),
        (
            f'DEFINE INDEX IF NOT EXISTS memory_node_title_idx ON TABLE {config.memory_node_table} '
            'COLUMNS title;'
        ),
        (
            f'DEFINE INDEX IF NOT EXISTS memory_node_type_rank_scope_idx ON TABLE {config.memory_node_table} '
            'COLUMNS node_type, trust_rank, scope;'
        ),
        (
            f'DEFINE INDEX IF NOT EXISTS memory_edge_endpoints_idx ON TABLE {config.memory_edge_table} '
            'COLUMNS from_node_id, to_node_id;'
        ),
        (
            f'DEFINE INDEX IF NOT EXISTS memory_edge_relation_source_idx ON TABLE {config.memory_edge_table} '
            'COLUMNS relation_type, source_id;'
        ),
        (
            f'DEFINE INDEX IF NOT EXISTS correction_target_idx ON TABLE {config.correction_table} '
            'COLUMNS target_kind, target_id;'
        ),
    )


class ProjectBrainSurrealSchemaManager:
    def __init__(
        self,
        config: ProjectBrainSurrealConnectionConfig | None = None,
        *,
        transport: Any | None = None,
    ) -> None:
        self.config = config or ProjectBrainSurrealConnectionConfig()
        self._client = create_traced_async_client(
            base_url=self.config.base_url.rstrip("/"),
            auth=httpx.BasicAuth(self.config.username, self.config.password),
            headers={
                "Accept": "application/json",
                "Content-Type": "text/plain",
                "Surreal-NS": self.config.namespace,
                "Surreal-DB": self.config.database,
            },
            timeout=self.config.timeout_seconds,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def ensure_schema(self) -> ProjectBrainSurrealSchemaBootstrapReport:
        statements = build_project_brain_surreal_schema_statements(self.config)
        response = await self._client.post("/sql", content="\n".join(statements))
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text.strip() or exc.response.reason_phrase
            raise ProjectBrainSurrealSchemaBootstrapError(
                f"SurrealDB schema bootstrap failed: {detail}"
            ) from exc

        payload = response.json()
        if not isinstance(payload, list):
            raise ProjectBrainSurrealSchemaBootstrapError(
                f"Unexpected SurrealDB schema bootstrap payload: {payload!r}"
            )
        failed = [item for item in payload if isinstance(item, dict) and item.get("status") not in {None, "OK"}]
        if failed:
            raise ProjectBrainSurrealSchemaBootstrapError(
                f"SurrealDB schema bootstrap returned failures: {failed!r}"
            )

        table_count = 5
        index_count = len(statements) - 2 - table_count
        return ProjectBrainSurrealSchemaBootstrapReport(
            namespace=self.config.namespace,
            database=self.config.database,
            statement_count=len(statements),
            table_count=table_count,
            index_count=index_count,
        )

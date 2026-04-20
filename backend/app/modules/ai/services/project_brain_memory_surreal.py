"""HTTP-backed SurrealDB adapter for project-brain memory.

primary_domain = "ai_orchestration"
secondary_domains = ["knowledge_management", "developer_experience", "operations"]
assumptions = [
    "The first persistent adapter should reuse the existing storage-neutral project-brain repository contract.",
    "The project-brain sidecar remains non-authoritative and should persist the same source, projection, node, edge, and correction families used by the bootstrap adapters.",
    "Using SurrealDB's documented HTTP key endpoints is preferable here to introducing a new Python SDK dependency."
]
limitations = [
    "This adapter currently stores project-brain records as document tables, not native graph relations.",
    "It performs existence checks before updates, which is acceptable for bootstrap-scale usage but not yet optimized for higher write throughput.",
    "Schema orchestration stays separate from the repository adapter; use the dedicated schema manager or bootstrap CLIs when the sidecar needs explicit tables and indexes."
]
uncertainty_handling = "The first persistent adapter intentionally favors contract fidelity and verifiability over database-specific optimization, so the project brain can prove its persistence path before deeper SurrealDB modeling work begins."
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

from app.core.http_tracing import create_traced_async_client
from app.modules.ai.services.project_brain_memory import (
    ProjectBrainCorrectionRecord,
    ProjectBrainMemoryEdgeRecord,
    ProjectBrainMemoryRepository,
    ProjectBrainMemoryNodeRecord,
    ProjectBrainProjectionRecord,
    ProjectBrainSourceArtifactRecord,
)
from app.modules.ai.services.project_brain_memory_codec import (
    decode_correction_record,
    decode_memory_edge_record,
    decode_memory_node_record,
    decode_projection_record,
    decode_source_artifact_record,
)


@dataclass(frozen=True, slots=True)
class ProjectBrainSurrealConnectionConfig:
    base_url: str = "http://127.0.0.1:8083"
    namespace: str = "beingbijmantra"
    database: str = "beingbijmantra_surrealdb"
    username: str = "root"
    password: str = "root"
    timeout_seconds: float = 10.0
    source_artifact_table: str = "project_brain_source_artifact"
    projection_table: str = "project_brain_projection"
    memory_node_table: str = "project_brain_memory_node"
    memory_edge_table: str = "project_brain_memory_edge"
    correction_table: str = "project_brain_correction"


class ProjectBrainSurrealRepositoryError(RuntimeError):
    pass


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _surreal_record_id(domain_id: str) -> str:
    return quote(domain_id, safe="")


def _project_brain_id_from_surreal(value: str | None) -> str:
    if value is None:
        raise ProjectBrainSurrealRepositoryError("SurrealDB record is missing an id field")
    if ":" not in value:
        return value
    return value.split(":", 1)[1]


def _surreal_content(record: dict[str, Any]) -> dict[str, Any]:
    payload = dict(record)
    payload["project_brain_id"] = payload.pop("id")
    return payload


def _normalize_surreal_record(record: dict[str, Any]) -> dict[str, Any]:
    payload = dict(record)
    payload["id"] = payload.get("project_brain_id") or _project_brain_id_from_surreal(payload.get("id"))
    payload.pop("project_brain_id", None)
    return payload


def _unwrap_surreal_payload(payload: Any) -> list[dict[str, Any]]:
    result = payload
    if isinstance(payload, list) and payload and isinstance(payload[0], dict) and "status" in payload[0]:
        statement = payload[0]
        if statement.get("status") not in {None, "OK"}:
            raise ProjectBrainSurrealRepositoryError(
                f"SurrealDB statement failed: {statement.get('result') or statement}"
            )
        result = statement.get("result")
    if result is None:
        return []
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if isinstance(result, dict):
        return [result]
    raise ProjectBrainSurrealRepositoryError(f"Unexpected SurrealDB payload shape: {result!r}")


class SurrealProjectBrainMemoryRepository(ProjectBrainMemoryRepository):
    def __init__(
        self,
        config: ProjectBrainSurrealConnectionConfig | None = None,
        *,
        transport: Any | None = None,
    ) -> None:
        self.config = config or ProjectBrainSurrealConnectionConfig()
        self._client = create_traced_async_client(
            base_url=_normalize_base_url(self.config.base_url),
            auth=httpx.BasicAuth(self.config.username, self.config.password),
            headers={
                "Accept": "application/json",
                "Surreal-NS": self.config.namespace,
                "Surreal-DB": self.config.database,
            },
            timeout=self.config.timeout_seconds,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def check_health(self) -> bool:
        response = await self._client.get("/health")
        response.raise_for_status()
        return response.status_code == 200

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        response = await self._client.request(method, path, json=json_body)
        if response.status_code == 404:
            return None
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text.strip() or exc.response.reason_phrase
            raise ProjectBrainSurrealRepositoryError(
                f"SurrealDB request failed for {method} {path}: {detail}"
            ) from exc
        if not response.content:
            return None
        return response.json()

    async def _get_record(self, table: str, record_id: str) -> dict[str, Any] | None:
        payload = await self._request_json("GET", f"/key/{table}/{_surreal_record_id(record_id)}")
        if payload is None:
            return None
        records = _unwrap_surreal_payload(payload)
        if not records:
            return None
        return _normalize_surreal_record(records[0])

    async def _list_records(self, table: str) -> list[dict[str, Any]]:
        payload = await self._request_json("GET", f"/key/{table}")
        if payload is None:
            return []
        records = _unwrap_surreal_payload(payload)
        normalized = [_normalize_surreal_record(item) for item in records]
        normalized.sort(key=lambda item: item["id"])
        return normalized

    async def _save_record(self, table: str, record_id: str, record: dict[str, Any]) -> dict[str, Any]:
        path = f"/key/{table}/{_surreal_record_id(record_id)}"
        existing = await self._get_record(table, record_id)
        payload = _surreal_content(record)
        response_payload = await self._request_json("POST" if existing is None else "PUT", path, json_body=payload)
        records = _unwrap_surreal_payload(response_payload)
        if not records:
            raise ProjectBrainSurrealRepositoryError(f"SurrealDB save returned no record for {table}:{record_id}")
        return _normalize_surreal_record(records[0])

    async def _delete_record(self, table: str, record_id: str) -> None:
        await self._request_json("DELETE", f"/key/{table}/{_surreal_record_id(record_id)}")

    async def save_source_artifact(
        self,
        artifact: ProjectBrainSourceArtifactRecord,
    ) -> ProjectBrainSourceArtifactRecord:
        data = await self._save_record(self.config.source_artifact_table, artifact.id, artifact.to_dict())
        return decode_source_artifact_record(data)

    async def get_source_artifact(self, artifact_id: str) -> ProjectBrainSourceArtifactRecord | None:
        data = await self._get_record(self.config.source_artifact_table, artifact_id)
        if data is None:
            return None
        return decode_source_artifact_record(data)

    async def list_source_artifacts(self) -> list[ProjectBrainSourceArtifactRecord]:
        return [
            decode_source_artifact_record(item)
            for item in await self._list_records(self.config.source_artifact_table)
        ]

    async def save_projection(
        self,
        projection: ProjectBrainProjectionRecord,
    ) -> ProjectBrainProjectionRecord:
        data = await self._save_record(self.config.projection_table, projection.id, projection.to_dict())
        return decode_projection_record(data)

    async def get_projection(self, projection_id: str) -> ProjectBrainProjectionRecord | None:
        data = await self._get_record(self.config.projection_table, projection_id)
        if data is None:
            return None
        return decode_projection_record(data)

    async def list_projections(self) -> list[ProjectBrainProjectionRecord]:
        return [
            decode_projection_record(item)
            for item in await self._list_records(self.config.projection_table)
        ]

    async def delete_projection(self, projection_id: str) -> None:
        await self._delete_record(self.config.projection_table, projection_id)

    async def save_memory_node(
        self,
        node: ProjectBrainMemoryNodeRecord,
    ) -> ProjectBrainMemoryNodeRecord:
        data = await self._save_record(self.config.memory_node_table, node.id, node.to_dict())
        return decode_memory_node_record(data)

    async def get_memory_node(self, node_id: str) -> ProjectBrainMemoryNodeRecord | None:
        data = await self._get_record(self.config.memory_node_table, node_id)
        if data is None:
            return None
        return decode_memory_node_record(data)

    async def list_memory_nodes(self) -> list[ProjectBrainMemoryNodeRecord]:
        return [
            decode_memory_node_record(item)
            for item in await self._list_records(self.config.memory_node_table)
        ]

    async def delete_memory_node(self, node_id: str) -> None:
        await self._delete_record(self.config.memory_node_table, node_id)

    async def save_memory_edge(
        self,
        edge: ProjectBrainMemoryEdgeRecord,
    ) -> ProjectBrainMemoryEdgeRecord:
        data = await self._save_record(self.config.memory_edge_table, edge.id, edge.to_dict())
        return decode_memory_edge_record(data)

    async def list_memory_edges(self) -> list[ProjectBrainMemoryEdgeRecord]:
        return [
            decode_memory_edge_record(item)
            for item in await self._list_records(self.config.memory_edge_table)
        ]

    async def delete_memory_edge(self, edge_id: str) -> None:
        await self._delete_record(self.config.memory_edge_table, edge_id)

    async def save_correction(
        self,
        correction: ProjectBrainCorrectionRecord,
    ) -> ProjectBrainCorrectionRecord:
        data = await self._save_record(self.config.correction_table, correction.id, correction.to_dict())
        return decode_correction_record(data)

    async def list_corrections(self) -> list[ProjectBrainCorrectionRecord]:
        return [
            decode_correction_record(item)
            for item in await self._list_records(self.config.correction_table)
        ]

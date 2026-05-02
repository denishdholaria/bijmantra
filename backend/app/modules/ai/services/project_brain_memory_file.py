"""File-backed bootstrap adapter for project-brain memory.

primary_domain = "ai_orchestration"
secondary_domains = ["knowledge_management", "developer_experience", "operations"]
assumptions = [
    "Repeatable local snapshots are useful before any database-backed sidecar is introduced.",
    "The file-backed adapter should behave like the volatile adapter with persistence added, not like a new authority surface.",
    "JSON snapshots should preserve provenance, trust rank, and scope metadata in a human-inspectable form."
]
limitations = [
    "This adapter is local-file persistence only and not a concurrent multi-writer system.",
    "Snapshots are intended for bootstrap proof and local continuity, not high-scale runtime use.",
    "No schema migration tooling is included beyond a simple snapshot version field."
]
uncertainty_handling = "The adapter stays deliberately simple so the value of persistent snapshots can be proven before choosing a faster sidecar runtime."
"""

from __future__ import annotations

import json
from pathlib import Path

from app.modules.ai.services.project_brain_memory import (
    VolatileProjectBrainMemoryRepository,
    _utc_now,
)
from app.modules.ai.services.project_brain_memory_codec import (
    decode_correction_record,
    decode_memory_edge_record,
    decode_memory_node_record,
    decode_projection_record,
    decode_source_artifact_record,
)


class FileBackedProjectBrainMemoryRepository(VolatileProjectBrainMemoryRepository):
    def __init__(self, snapshot_path: str | Path) -> None:
        super().__init__()
        self.snapshot_path = Path(snapshot_path)
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        if not self.snapshot_path.exists():
            return
        payload = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
        self._source_artifacts = {
            item["id"]: decode_source_artifact_record(item)
            for item in payload.get("source_artifacts", [])
        }
        self._projections = {
            item["id"]: decode_projection_record(item)
            for item in payload.get("projections", [])
        }
        self._memory_nodes = {
            item["id"]: decode_memory_node_record(item)
            for item in payload.get("memory_nodes", [])
        }
        self._memory_edges = {
            item["id"]: decode_memory_edge_record(item)
            for item in payload.get("memory_edges", [])
        }
        self._corrections = {
            item["id"]: decode_correction_record(item)
            for item in payload.get("corrections", [])
        }

    def _persist(self) -> None:
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "updated_at": _utc_now().isoformat(),
            "source_artifacts": [item.to_dict() for item in self._source_artifacts.values()],
            "projections": [item.to_dict() for item in self._projections.values()],
            "memory_nodes": [item.to_dict() for item in self._memory_nodes.values()],
            "memory_edges": [item.to_dict() for item in self._memory_edges.values()],
            "corrections": [item.to_dict() for item in self._corrections.values()],
        }
        self.snapshot_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    async def save_source_artifact(self, artifact: ProjectBrainSourceArtifactRecord) -> ProjectBrainSourceArtifactRecord:
        saved = await super().save_source_artifact(artifact)
        self._persist()
        return saved

    async def save_projection(self, projection: ProjectBrainProjectionRecord) -> ProjectBrainProjectionRecord:
        saved = await super().save_projection(projection)
        self._persist()
        return saved

    async def delete_projection(self, projection_id: str) -> None:
        await super().delete_projection(projection_id)
        self._persist()

    async def save_memory_node(self, node: ProjectBrainMemoryNodeRecord) -> ProjectBrainMemoryNodeRecord:
        saved = await super().save_memory_node(node)
        self._persist()
        return saved

    async def delete_memory_node(self, node_id: str) -> None:
        await super().delete_memory_node(node_id)
        self._persist()

    async def save_memory_edge(self, edge: ProjectBrainMemoryEdgeRecord) -> ProjectBrainMemoryEdgeRecord:
        saved = await super().save_memory_edge(edge)
        self._persist()
        return saved

    async def delete_memory_edge(self, edge_id: str) -> None:
        await super().delete_memory_edge(edge_id)
        self._persist()

    async def save_correction(self, correction: ProjectBrainCorrectionRecord) -> ProjectBrainCorrectionRecord:
        saved = await super().save_correction(correction)
        self._persist()
        return saved

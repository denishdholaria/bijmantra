"""Storage-neutral project-brain memory bootstrap.

primary_domain = "ai_orchestration"
secondary_domains = ["knowledge_management", "governance", "operations"]
assumptions = [
    "The first slice should prove the project-brain memory contract before any SurrealDB adapter is introduced.",
    "Source artifacts remain authoritative over projections, graph links, and recall views.",
    "Async repository interfaces should match the surrounding FastAPI and SQLAlchemy service layer."
]
limitations = [
    "This module ships only a volatile in-process repository adapter.",
    "No source parsing pipeline is implemented yet; callers register structured source metadata explicitly.",
    "The bootstrap service is for project-development memory only and does not expose a REEVU runtime bridge."
]
uncertainty_handling = "Database-backed sidecars remain deferred until the contract, inventory, and adapter access patterns are proven useful."
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol
from uuid import uuid4


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


def _iter_searchable_text(value: Any):
    if value is None:
        return
    if isinstance(value, (str, int, float, bool)):
        yield str(value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _iter_searchable_text(item)
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _iter_searchable_text(item)


def _matches_query(lowered_query: str, *values: Any) -> bool:
    return any(lowered_query in text.lower() for value in values for text in _iter_searchable_text(value))


class ProjectBrainSourceSurface(StrEnum):
    BEING = "being"
    AI = "ai"
    GITHUB = "github"
    RUNTIME_EVIDENCE = "runtime_evidence"
    OTHER = "other"


class ProjectBrainTrustRank(StrEnum):
    RANK_A = "rank_a"
    RANK_B = "rank_b"
    RANK_C = "rank_c"
    RANK_D = "rank_d"
    RANK_E = "rank_e"


class ProjectBrainScope(StrEnum):
    GLOBAL_PROJECT = "global_project"
    SURFACE = "surface"
    WORKSTREAM = "workstream"
    SESSION = "session"
    RESTRICTED = "restricted"


@dataclass(frozen=True, slots=True)
class ProjectBrainSourceArtifactRecord:
    id: str
    source_path: str
    source_surface: ProjectBrainSourceSurface
    source_kind: str
    authority_class: str
    capture_timestamp: datetime = field(default_factory=_utc_now)
    version: str | None = None
    digest: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class ProjectBrainProjectionRecord:
    id: str
    source_id: str
    projection_type: str
    summary: str
    trust_rank: ProjectBrainTrustRank
    scope: ProjectBrainScope
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utc_now)
    invalidated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class ProjectBrainMemoryNodeRecord:
    id: str
    node_type: str
    title: str
    trust_rank: ProjectBrainTrustRank
    scope: ProjectBrainScope
    source_ids: tuple[str, ...] = tuple()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utc_now)
    invalidated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class ProjectBrainMemoryEdgeRecord:
    id: str
    from_node_id: str
    to_node_id: str
    relation_type: str
    source_id: str | None = None
    confidence: float | None = None
    is_derived: bool = False
    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class ProjectBrainCorrectionRecord:
    id: str
    target_kind: str
    target_id: str
    reason: str
    recorded_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class ProjectBrainRecallView:
    query: str
    source_artifacts: tuple[ProjectBrainSourceArtifactRecord, ...] = tuple()
    projections: tuple[ProjectBrainProjectionRecord, ...] = tuple()
    nodes: tuple[ProjectBrainMemoryNodeRecord, ...] = tuple()
    edges: tuple[ProjectBrainMemoryEdgeRecord, ...] = tuple()

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "source_artifacts": [item.to_dict() for item in self.source_artifacts],
            "projections": [item.to_dict() for item in self.projections],
            "nodes": [item.to_dict() for item in self.nodes],
            "edges": [item.to_dict() for item in self.edges],
        }


@dataclass(frozen=True, slots=True)
class ProjectBrainProvenanceTrail:
    node: ProjectBrainMemoryNodeRecord
    source_artifacts: tuple[ProjectBrainSourceArtifactRecord, ...] = tuple()
    related_edges: tuple[ProjectBrainMemoryEdgeRecord, ...] = tuple()
    corrections: tuple[ProjectBrainCorrectionRecord, ...] = tuple()

    def to_dict(self) -> dict[str, Any]:
        return {
            "node": self.node.to_dict(),
            "source_artifacts": [item.to_dict() for item in self.source_artifacts],
            "related_edges": [item.to_dict() for item in self.related_edges],
            "corrections": [item.to_dict() for item in self.corrections],
        }


class ProjectBrainMemoryRepository(Protocol):
    async def save_source_artifact(
        self,
        artifact: ProjectBrainSourceArtifactRecord,
    ) -> ProjectBrainSourceArtifactRecord: ...

    async def get_source_artifact(self, artifact_id: str) -> ProjectBrainSourceArtifactRecord | None: ...

    async def list_source_artifacts(self) -> list[ProjectBrainSourceArtifactRecord]: ...

    async def save_projection(
        self,
        projection: ProjectBrainProjectionRecord,
    ) -> ProjectBrainProjectionRecord: ...

    async def get_projection(self, projection_id: str) -> ProjectBrainProjectionRecord | None: ...

    async def list_projections(self) -> list[ProjectBrainProjectionRecord]: ...

    async def delete_projection(self, projection_id: str) -> None: ...

    async def save_memory_node(
        self,
        node: ProjectBrainMemoryNodeRecord,
    ) -> ProjectBrainMemoryNodeRecord: ...

    async def get_memory_node(self, node_id: str) -> ProjectBrainMemoryNodeRecord | None: ...

    async def list_memory_nodes(self) -> list[ProjectBrainMemoryNodeRecord]: ...

    async def delete_memory_node(self, node_id: str) -> None: ...

    async def save_memory_edge(
        self,
        edge: ProjectBrainMemoryEdgeRecord,
    ) -> ProjectBrainMemoryEdgeRecord: ...

    async def list_memory_edges(self) -> list[ProjectBrainMemoryEdgeRecord]: ...

    async def delete_memory_edge(self, edge_id: str) -> None: ...

    async def save_correction(
        self,
        correction: ProjectBrainCorrectionRecord,
    ) -> ProjectBrainCorrectionRecord: ...

    async def list_corrections(self) -> list[ProjectBrainCorrectionRecord]: ...


class VolatileProjectBrainMemoryRepository:
    def __init__(self) -> None:
        self._source_artifacts: dict[str, ProjectBrainSourceArtifactRecord] = {}
        self._projections: dict[str, ProjectBrainProjectionRecord] = {}
        self._memory_nodes: dict[str, ProjectBrainMemoryNodeRecord] = {}
        self._memory_edges: dict[str, ProjectBrainMemoryEdgeRecord] = {}
        self._corrections: dict[str, ProjectBrainCorrectionRecord] = {}

    async def save_source_artifact(
        self,
        artifact: ProjectBrainSourceArtifactRecord,
    ) -> ProjectBrainSourceArtifactRecord:
        self._source_artifacts[artifact.id] = artifact
        return artifact

    async def get_source_artifact(self, artifact_id: str) -> ProjectBrainSourceArtifactRecord | None:
        return self._source_artifacts.get(artifact_id)

    async def list_source_artifacts(self) -> list[ProjectBrainSourceArtifactRecord]:
        return list(self._source_artifacts.values())

    async def save_projection(
        self,
        projection: ProjectBrainProjectionRecord,
    ) -> ProjectBrainProjectionRecord:
        self._projections[projection.id] = projection
        return projection

    async def get_projection(self, projection_id: str) -> ProjectBrainProjectionRecord | None:
        return self._projections.get(projection_id)

    async def list_projections(self) -> list[ProjectBrainProjectionRecord]:
        return list(self._projections.values())

    async def delete_projection(self, projection_id: str) -> None:
        self._projections.pop(projection_id, None)

    async def save_memory_node(
        self,
        node: ProjectBrainMemoryNodeRecord,
    ) -> ProjectBrainMemoryNodeRecord:
        self._memory_nodes[node.id] = node
        return node

    async def get_memory_node(self, node_id: str) -> ProjectBrainMemoryNodeRecord | None:
        return self._memory_nodes.get(node_id)

    async def list_memory_nodes(self) -> list[ProjectBrainMemoryNodeRecord]:
        return list(self._memory_nodes.values())

    async def delete_memory_node(self, node_id: str) -> None:
        self._memory_nodes.pop(node_id, None)

    async def save_memory_edge(
        self,
        edge: ProjectBrainMemoryEdgeRecord,
    ) -> ProjectBrainMemoryEdgeRecord:
        self._memory_edges[edge.id] = edge
        return edge

    async def list_memory_edges(self) -> list[ProjectBrainMemoryEdgeRecord]:
        return list(self._memory_edges.values())

    async def delete_memory_edge(self, edge_id: str) -> None:
        self._memory_edges.pop(edge_id, None)

    async def save_correction(
        self,
        correction: ProjectBrainCorrectionRecord,
    ) -> ProjectBrainCorrectionRecord:
        self._corrections[correction.id] = correction
        return correction

    async def list_corrections(self) -> list[ProjectBrainCorrectionRecord]:
        return list(self._corrections.values())


class ProjectBrainMemoryService:
    def __init__(self, repository: ProjectBrainMemoryRepository):
        self.repository = repository

    async def register_source_artifact(
        self,
        *,
        source_path: str,
        source_surface: ProjectBrainSourceSurface,
        source_kind: str,
        authority_class: str,
        version: str | None = None,
        digest: str | None = None,
        metadata: dict[str, Any] | None = None,
        source_artifact_id: str | None = None,
    ) -> ProjectBrainSourceArtifactRecord:
        if not source_path.strip():
            raise ValueError("source_path is required")
        if not source_kind.strip():
            raise ValueError("source_kind is required")
        if not authority_class.strip():
            raise ValueError("authority_class is required")

        artifact = ProjectBrainSourceArtifactRecord(
            id=source_artifact_id or _new_id("source"),
            source_path=source_path,
            source_surface=source_surface,
            source_kind=source_kind,
            authority_class=authority_class,
            version=version,
            digest=digest,
            metadata=metadata or {},
        )
        return await self.repository.save_source_artifact(artifact)

    async def project_from_source(
        self,
        *,
        source_id: str,
        projection_type: str,
        summary: str,
        trust_rank: ProjectBrainTrustRank,
        scope: ProjectBrainScope,
        metadata: dict[str, Any] | None = None,
        projection_id: str | None = None,
    ) -> ProjectBrainProjectionRecord:
        source = await self.repository.get_source_artifact(source_id)
        if source is None:
            raise ValueError("Unknown source artifact")
        if not summary.strip():
            raise ValueError("summary is required")

        projection = ProjectBrainProjectionRecord(
            id=projection_id or _new_id("projection"),
            source_id=source.id,
            projection_type=projection_type,
            summary=summary,
            trust_rank=trust_rank,
            scope=scope,
            metadata=metadata or {},
        )
        return await self.repository.save_projection(projection)

    async def upsert_memory_node(
        self,
        *,
        node_type: str,
        title: str,
        trust_rank: ProjectBrainTrustRank,
        scope: ProjectBrainScope,
        source_ids: Sequence[str] = (),
        metadata: dict[str, Any] | None = None,
        node_id: str | None = None,
    ) -> ProjectBrainMemoryNodeRecord:
        if not title.strip():
            raise ValueError("title is required")
        for source_id in source_ids:
            if await self.repository.get_source_artifact(source_id) is None:
                raise ValueError("Unknown source artifact")

        existing = await self.repository.get_memory_node(node_id) if node_id else None
        if existing is None:
            node = ProjectBrainMemoryNodeRecord(
                id=node_id or _new_id("node"),
                node_type=node_type,
                title=title,
                trust_rank=trust_rank,
                scope=scope,
                source_ids=tuple(source_ids),
                metadata=metadata or {},
            )
        else:
            node = replace(
                existing,
                node_type=node_type,
                title=title,
                trust_rank=trust_rank,
                scope=scope,
                source_ids=tuple(source_ids),
                metadata=metadata or {},
            )
        return await self.repository.save_memory_node(node)

    async def link_memory_objects(
        self,
        *,
        from_node_id: str,
        to_node_id: str,
        relation_type: str,
        source_id: str | None = None,
        confidence: float | None = None,
        is_derived: bool = False,
        edge_id: str | None = None,
    ) -> ProjectBrainMemoryEdgeRecord:
        if await self.repository.get_memory_node(from_node_id) is None:
            raise ValueError("Unknown from_node_id")
        if await self.repository.get_memory_node(to_node_id) is None:
            raise ValueError("Unknown to_node_id")
        if source_id is not None and await self.repository.get_source_artifact(source_id) is None:
            raise ValueError("Unknown source artifact")
        if confidence is not None and not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        edge = ProjectBrainMemoryEdgeRecord(
            id=edge_id or _new_id("edge"),
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            relation_type=relation_type,
            source_id=source_id,
            confidence=confidence,
            is_derived=is_derived,
        )
        return await self.repository.save_memory_edge(edge)

    async def recall(
        self,
        query: str,
        *,
        trust_ranks: Sequence[ProjectBrainTrustRank] | None = None,
        scopes: Sequence[ProjectBrainScope] | None = None,
    ) -> ProjectBrainRecallView:
        lowered_query = query.lower().strip()
        allowed_ranks = set(trust_ranks) if trust_ranks is not None else None
        allowed_scopes = set(scopes) if scopes is not None else None

        source_artifacts = tuple(
            artifact
            for artifact in await self.repository.list_source_artifacts()
            if _matches_query(
                lowered_query,
                artifact.source_path,
                artifact.source_kind,
                artifact.authority_class,
                artifact.metadata,
            )
        )
        projections = tuple(
            projection
            for projection in await self.repository.list_projections()
            if _matches_query(lowered_query, projection.summary, projection.metadata)
            and (allowed_ranks is None or projection.trust_rank in allowed_ranks)
            and (allowed_scopes is None or projection.scope in allowed_scopes)
        )
        nodes = tuple(
            node
            for node in await self.repository.list_memory_nodes()
            if _matches_query(lowered_query, node.title, node.metadata)
            and (allowed_ranks is None or node.trust_rank in allowed_ranks)
            and (allowed_scopes is None or node.scope in allowed_scopes)
        )
        node_ids = {node.id for node in nodes}
        edges = tuple(
            edge
            for edge in await self.repository.list_memory_edges()
            if edge.from_node_id in node_ids or edge.to_node_id in node_ids
        )
        return ProjectBrainRecallView(
            query=query,
            source_artifacts=source_artifacts,
            projections=projections,
            nodes=nodes,
            edges=edges,
        )

    async def list_related(self, node_id: str) -> tuple[ProjectBrainMemoryEdgeRecord, ...]:
        node = await self.repository.get_memory_node(node_id)
        if node is None:
            raise ValueError("Unknown memory node")
        return tuple(
            edge
            for edge in await self.repository.list_memory_edges()
            if edge.from_node_id == node.id or edge.to_node_id == node.id
        )

    async def get_provenance_trail(self, node_id: str) -> ProjectBrainProvenanceTrail:
        node = await self.repository.get_memory_node(node_id)
        if node is None:
            raise ValueError("Unknown memory node")
        edges = await self.list_related(node.id)
        source_ids = set(node.source_ids)
        source_ids.update(edge.source_id for edge in edges if edge.source_id is not None)
        source_artifacts = tuple(
            artifact
            for artifact in await self.repository.list_source_artifacts()
            if artifact.id in source_ids
        )
        corrections = tuple(
            correction
            for correction in await self.repository.list_corrections()
            if correction.target_id == node.id or correction.target_id in source_ids
        )
        return ProjectBrainProvenanceTrail(
            node=node,
            source_artifacts=source_artifacts,
            related_edges=edges,
            corrections=corrections,
        )

    async def mark_invalid(
        self,
        *,
        target_kind: str,
        target_id: str,
        reason: str,
        correction_id: str | None = None,
    ) -> ProjectBrainCorrectionRecord:
        if not reason.strip():
            raise ValueError("reason is required")
        if target_kind == "source":
            target_exists = await self.repository.get_source_artifact(target_id) is not None
        elif target_kind == "projection":
            target = await self.repository.get_projection(target_id)
            target_exists = target is not None
            if target is not None:
                await self.repository.save_projection(replace(target, invalidated_at=_utc_now()))
        elif target_kind == "node":
            target = await self.repository.get_memory_node(target_id)
            target_exists = target is not None
            if target is not None:
                await self.repository.save_memory_node(replace(target, invalidated_at=_utc_now()))
        else:
            raise ValueError("Unsupported target_kind")

        if not target_exists:
            raise ValueError("Unknown target for correction")

        correction = ProjectBrainCorrectionRecord(
            id=correction_id or _new_id("correction"),
            target_kind=target_kind,
            target_id=target_id,
            reason=reason,
        )
        return await self.repository.save_correction(correction)

    async def forget_scope(
        self,
        scope: ProjectBrainScope,
        *,
        allow_non_ephemeral: bool = False,
    ) -> dict[str, int]:
        if scope is not ProjectBrainScope.SESSION and not allow_non_ephemeral:
            raise ValueError("Non-session forgetting requires allow_non_ephemeral=True")

        projection_ids = [
            projection.id
            for projection in await self.repository.list_projections()
            if projection.scope is scope
        ]
        node_ids = [
            node.id
            for node in await self.repository.list_memory_nodes()
            if node.scope is scope
        ]
        edge_ids = [
            edge.id
            for edge in await self.repository.list_memory_edges()
            if edge.from_node_id in node_ids or edge.to_node_id in node_ids
        ]

        for projection_id in projection_ids:
            await self.repository.delete_projection(projection_id)
        for edge_id in edge_ids:
            await self.repository.delete_memory_edge(edge_id)
        for node_id in node_ids:
            await self.repository.delete_memory_node(node_id)

        return {
            "projections_removed": len(projection_ids),
            "nodes_removed": len(node_ids),
            "edges_removed": len(edge_ids),
        }

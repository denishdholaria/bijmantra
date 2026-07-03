"""Application-facing records for Knowledge Graph ports."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class KnowledgeGraphEdgeRecord:
    """Tenant-scoped graph edge exposed by Knowledge Graph ports."""

    id: int
    organization_id: int
    edge_id: str
    source_asset_type: str
    source_asset_id: str
    relationship_type: str
    target_asset_type: str
    target_asset_id: str
    status: str
    schema_version: str
    created_at: datetime
    updated_at: datetime
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    derivation_method: str | None = None


@dataclass(frozen=True)
class KnowledgeGraphFairAssetRecord:
    """FAIR asset reference exposed by Knowledge Graph ports."""

    asset_type: str
    asset_id: str
    asset_title: str
    persistent_identifier: str


@dataclass(frozen=True)
class KnowledgeGraphNeighborhoodRecord:
    """One-hop graph neighborhood exposed by Knowledge Graph ports."""

    asset_type: str
    asset_id: str
    direction: str
    relationship_type: str | None = None
    outgoing_edges: list[KnowledgeGraphEdgeRecord] = field(default_factory=list)
    incoming_edges: list[KnowledgeGraphEdgeRecord] = field(default_factory=list)
    edge_count: int = 0

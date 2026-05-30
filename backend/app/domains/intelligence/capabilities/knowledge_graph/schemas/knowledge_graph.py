"""Intelligence Knowledge Graph application schemas and commands.

These query and command objects wrap the stable public Pydantic schemas while
the `/api/v2/knowledge-graph/*` API surface remains unchanged.
"""

from dataclasses import dataclass

from app.schemas.knowledge_graph import (
    KnowledgeGraphEdgeCreate,
    KnowledgeGraphEdgeResponse,
    KnowledgeGraphEvidencePackResponse,
    KnowledgeGraphEvidenceSearchResponse,
    KnowledgeGraphEvidenceSearchResult,
    KnowledgeGraphExplorerSnapshotResponse,
    KnowledgeGraphFacetResponse,
    KnowledgeGraphNeighborhoodResponse,
    KnowledgeGraphRankedCandidateResponse,
    KnowledgeGraphReevuDryRunPreviewResponse,
    KnowledgeGraphRetrievalCandidate,
    KnowledgeGraphRetrievalCandidateResponse,
    KnowledgeGraphRetrievalDiagnosticsResponse,
)


class GraphAssetNotFound(ValueError):
    """Raised when a graph edge references an asset without tenant-owned metadata."""


@dataclass(frozen=True, slots=True)
class KnowledgeGraphExplorerSnapshotQuery:
    organization_id: int
    source_asset_type: str | None = None
    source_asset_id: str | None = None
    target_asset_type: str | None = None
    target_asset_id: str | None = None
    relationship_type: str | None = None
    result_side: str = "source"
    candidate_direction: str = "both"
    minimum_confidence: float = 0.5
    limit: int = 100
    offset: int = 0
    candidate_edge_limit: int = 100


@dataclass(frozen=True, slots=True)
class KnowledgeGraphRankedCandidatesQuery:
    organization_id: int
    source_asset_type: str | None = None
    source_asset_id: str | None = None
    target_asset_type: str | None = None
    target_asset_id: str | None = None
    relationship_type: str | None = None
    result_side: str = "source"
    candidate_direction: str = "both"
    limit: int = 100
    offset: int = 0
    candidate_edge_limit: int = 100


@dataclass(frozen=True, slots=True)
class KnowledgeGraphRetrievalDiagnosticsQuery:
    organization_id: int
    source_asset_type: str | None = None
    source_asset_id: str | None = None
    target_asset_type: str | None = None
    target_asset_id: str | None = None
    relationship_type: str | None = None
    result_side: str = "source"
    candidate_direction: str = "both"
    minimum_confidence: float = 0.5
    limit: int = 100
    offset: int = 0
    candidate_edge_limit: int = 100


@dataclass(frozen=True, slots=True)
class KnowledgeGraphRetrievalCandidatesQuery:
    organization_id: int
    source_asset_type: str | None = None
    source_asset_id: str | None = None
    target_asset_type: str | None = None
    target_asset_id: str | None = None
    relationship_type: str | None = None
    result_side: str = "source"
    candidate_direction: str = "both"
    limit: int = 100
    offset: int = 0
    candidate_edge_limit: int = 100


@dataclass(frozen=True, slots=True)
class KnowledgeGraphEvidenceSearchQuery:
    organization_id: int
    source_asset_type: str | None = None
    source_asset_id: str | None = None
    target_asset_type: str | None = None
    target_asset_id: str | None = None
    relationship_type: str | None = None
    result_side: str = "source"
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True, slots=True)
class KnowledgeGraphFairAssetRef:
    asset_type: str
    asset_id: str
    asset_title: str
    persistent_identifier: str


@dataclass(frozen=True, slots=True)
class KnowledgeGraphFacetsQuery:
    organization_id: int
    source_asset_type: str | None = None
    source_asset_id: str | None = None
    target_asset_type: str | None = None
    target_asset_id: str | None = None
    relationship_type: str | None = None


@dataclass(frozen=True, slots=True)
class KnowledgeGraphEdgesListQuery:
    organization_id: int
    source_asset_type: str | None = None
    source_asset_id: str | None = None
    target_asset_type: str | None = None
    target_asset_id: str | None = None
    relationship_type: str | None = None
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True, slots=True)
class KnowledgeGraphUpsertEdgeCommand:
    organization_id: int
    payload: KnowledgeGraphEdgeCreate


@dataclass(frozen=True, slots=True)
class KnowledgeGraphNeighborhoodQuery:
    organization_id: int
    asset_type: str
    asset_id: str
    direction: str = "both"
    relationship_type: str | None = None
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True, slots=True)
class KnowledgeGraphEvidencePackQuery:
    organization_id: int
    asset_type: str
    asset_id: str
    direction: str = "both"
    relationship_type: str | None = None
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True, slots=True)
class KnowledgeGraphReevuDryRunPreviewQuery:
    organization_id: int
    prompt: str | None = None
    source_asset_type: str | None = None
    source_asset_id: str | None = None
    target_asset_type: str | None = None
    target_asset_id: str | None = None
    relationship_type: str | None = None
    result_side: str = "source"
    candidate_direction: str = "both"
    minimum_confidence: float = 0.5
    limit: int = 100
    offset: int = 0
    candidate_edge_limit: int = 100


__all__ = [
    "GraphAssetNotFound",
    "KnowledgeGraphEdgeCreate",
    "KnowledgeGraphEdgeResponse",
    "KnowledgeGraphEdgesListQuery",
    "KnowledgeGraphEvidencePackQuery",
    "KnowledgeGraphEvidencePackResponse",
    "KnowledgeGraphEvidenceSearchQuery",
    "KnowledgeGraphEvidenceSearchResponse",
    "KnowledgeGraphEvidenceSearchResult",
    "KnowledgeGraphExplorerSnapshotQuery",
    "KnowledgeGraphExplorerSnapshotResponse",
    "KnowledgeGraphFacetResponse",
    "KnowledgeGraphFacetsQuery",
    "KnowledgeGraphFairAssetRef",
    "KnowledgeGraphNeighborhoodQuery",
    "KnowledgeGraphNeighborhoodResponse",
    "KnowledgeGraphRankedCandidateResponse",
    "KnowledgeGraphRankedCandidatesQuery",
    "KnowledgeGraphReevuDryRunPreviewQuery",
    "KnowledgeGraphReevuDryRunPreviewResponse",
    "KnowledgeGraphRetrievalCandidate",
    "KnowledgeGraphRetrievalCandidateResponse",
    "KnowledgeGraphRetrievalCandidatesQuery",
    "KnowledgeGraphRetrievalDiagnosticsQuery",
    "KnowledgeGraphRetrievalDiagnosticsResponse",
    "KnowledgeGraphUpsertEdgeCommand",
]

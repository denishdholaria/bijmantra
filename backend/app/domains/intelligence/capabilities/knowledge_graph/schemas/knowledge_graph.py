"""Capability-owned Knowledge Graph schemas, queries, commands, and errors."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domains.intelligence.capabilities.knowledge_graph.domain import (
    SUPPORTED_GRAPH_DIRECTIONS,
    SUPPORTED_GRAPH_RELATIONSHIP_TYPES,
    SUPPORTED_GRAPH_RESULT_SIDES,
)


class KnowledgeGraphEdgeCreate(BaseModel):
    source_asset_type: str
    source_asset_id: str
    relationship_type: str
    target_asset_type: str
    target_asset_id: str
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    derivation_method: str | None = None
    status: str = "active"


class KnowledgeGraphEdgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    edge_id: str
    source_asset_type: str
    source_asset_id: str
    relationship_type: str
    target_asset_type: str
    target_asset_id: str
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    derivation_method: str | None = None
    status: str
    schema_version: str
    created_at: datetime
    updated_at: datetime


class KnowledgeGraphNeighborhoodResponse(BaseModel):
    asset_type: str
    asset_id: str
    direction: str
    relationship_type: str | None = None
    outgoing_edges: list[KnowledgeGraphEdgeResponse] = Field(default_factory=list)
    incoming_edges: list[KnowledgeGraphEdgeResponse] = Field(default_factory=list)
    edge_count: int


class KnowledgeGraphEvidencePackResponse(BaseModel):
    asset_type: str
    asset_id: str
    asset_title: str
    persistent_identifier: str
    direction: str
    relationship_type: str | None = None
    neighborhood: KnowledgeGraphNeighborhoodResponse
    relationship_types: list[str] = Field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    retrieval_policy: dict[str, Any] = Field(default_factory=dict)
    edge_count: int


class KnowledgeGraphEvidenceSearchResult(BaseModel):
    asset_type: str
    asset_id: str
    asset_title: str
    persistent_identifier: str
    relationship_type: str
    matched_edge: KnowledgeGraphEdgeResponse
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    derivation_method: str | None = None


class KnowledgeGraphEvidenceSearchResponse(BaseModel):
    source_asset_type: str | None = None
    source_asset_id: str | None = None
    target_asset_type: str | None = None
    target_asset_id: str | None = None
    relationship_type: str | None = None
    result_side: str
    results: list[KnowledgeGraphEvidenceSearchResult] = Field(default_factory=list)
    retrieval_policy: dict[str, Any] = Field(default_factory=dict)
    result_count: int


class KnowledgeGraphRetrievalCandidate(BaseModel):
    asset_type: str
    asset_id: str
    asset_title: str
    persistent_identifier: str
    matched_edges: list[KnowledgeGraphEdgeResponse] = Field(default_factory=list)
    matched_evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    evidence_pack: KnowledgeGraphEvidencePackResponse
    match_count: int


class KnowledgeGraphRetrievalCandidateResponse(BaseModel):
    source_asset_type: str | None = None
    source_asset_id: str | None = None
    target_asset_type: str | None = None
    target_asset_id: str | None = None
    relationship_type: str | None = None
    result_side: str
    candidate_direction: str
    candidates: list[KnowledgeGraphRetrievalCandidate] = Field(default_factory=list)
    retrieval_policy: dict[str, Any] = Field(default_factory=dict)
    search_result_count: int
    candidate_count: int


class KnowledgeGraphRetrievalDiagnosticCandidate(BaseModel):
    asset_type: str
    asset_id: str
    asset_title: str
    persistent_identifier: str
    matched_edge_count: int
    matched_evidence_ref_count: int
    matched_edges_without_evidence_count: int
    low_confidence_edge_count: int
    missing_confidence_edge_count: int
    evidence_pack_edge_count: int
    warnings: list[str] = Field(default_factory=list)


class KnowledgeGraphRetrievalDiagnosticsResponse(BaseModel):
    candidates: KnowledgeGraphRetrievalCandidateResponse
    relationship_type_counts: dict[str, int] = Field(default_factory=dict)
    total_matched_edges: int
    total_matched_evidence_refs: int
    matched_edges_without_evidence_count: int
    low_confidence_edge_count: int
    missing_confidence_edge_count: int
    candidate_diagnostics: list[KnowledgeGraphRetrievalDiagnosticCandidate] = Field(
        default_factory=list
    )
    readiness: dict[str, Any] = Field(default_factory=dict)
    retrieval_policy: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphAssetTypePairFacet(BaseModel):
    source_asset_type: str
    target_asset_type: str
    count: int


class KnowledgeGraphFacetResponse(BaseModel):
    source_asset_type: str | None = None
    source_asset_id: str | None = None
    target_asset_type: str | None = None
    target_asset_id: str | None = None
    relationship_type: str | None = None
    total_edge_count: int
    relationship_type_counts: dict[str, int] = Field(default_factory=dict)
    source_asset_type_counts: dict[str, int] = Field(default_factory=dict)
    target_asset_type_counts: dict[str, int] = Field(default_factory=dict)
    status_counts: dict[str, int] = Field(default_factory=dict)
    derivation_method_counts: dict[str, int] = Field(default_factory=dict)
    asset_type_pair_counts: list[KnowledgeGraphAssetTypePairFacet] = Field(
        default_factory=list
    )
    retrieval_policy: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphRankedCandidate(BaseModel):
    rank: int
    candidate: KnowledgeGraphRetrievalCandidate
    retrieval_score: float
    score_factors: dict[str, float] = Field(default_factory=dict)


class KnowledgeGraphRankedCandidateResponse(BaseModel):
    candidates: KnowledgeGraphRetrievalCandidateResponse
    ranked_candidates: list[KnowledgeGraphRankedCandidate] = Field(default_factory=list)
    retrieval_policy: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphExplorerSnapshotResponse(BaseModel):
    facets: KnowledgeGraphFacetResponse
    ranked_candidates: KnowledgeGraphRankedCandidateResponse
    diagnostics: KnowledgeGraphRetrievalDiagnosticsResponse
    snapshot_summary: dict[str, Any] = Field(default_factory=dict)
    retrieval_policy: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphReevuDryRunPreviewResponse(BaseModel):
    prompt: str | None = None
    ranked_candidates: KnowledgeGraphRankedCandidateResponse
    diagnostics: KnowledgeGraphRetrievalDiagnosticsResponse
    preview_summary: dict[str, Any] = Field(default_factory=dict)
    authority_boundary: dict[str, Any] = Field(default_factory=dict)
    retrieval_policy: dict[str, Any] = Field(default_factory=dict)


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
    "SUPPORTED_GRAPH_DIRECTIONS",
    "SUPPORTED_GRAPH_RELATIONSHIP_TYPES",
    "SUPPORTED_GRAPH_RESULT_SIDES",
    "KnowledgeGraphAssetTypePairFacet",
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
    "KnowledgeGraphRankedCandidate",
    "KnowledgeGraphRankedCandidateResponse",
    "KnowledgeGraphRankedCandidatesQuery",
    "KnowledgeGraphReevuDryRunPreviewQuery",
    "KnowledgeGraphReevuDryRunPreviewResponse",
    "KnowledgeGraphRetrievalCandidate",
    "KnowledgeGraphRetrievalCandidateResponse",
    "KnowledgeGraphRetrievalCandidatesQuery",
    "KnowledgeGraphRetrievalDiagnosticCandidate",
    "KnowledgeGraphRetrievalDiagnosticsQuery",
    "KnowledgeGraphRetrievalDiagnosticsResponse",
    "KnowledgeGraphUpsertEdgeCommand",
]

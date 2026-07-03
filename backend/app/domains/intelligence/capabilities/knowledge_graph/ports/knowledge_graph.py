"""Intelligence Knowledge Graph ports.

Ports are protocol interfaces owned by the Intelligence domain. Infrastructure
adapters implement these interfaces; application use cases depend on them.
"""

from typing import Protocol

from app.domains.intelligence.capabilities.knowledge_graph.ports.records import (
    KnowledgeGraphEdgeRecord,
    KnowledgeGraphFairAssetRecord,
    KnowledgeGraphNeighborhoodRecord,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEdgesListQuery,
    KnowledgeGraphEvidencePackQuery,
    KnowledgeGraphEvidencePackResponse,
    KnowledgeGraphEvidenceSearchQuery,
    KnowledgeGraphEvidenceSearchResponse,
    KnowledgeGraphExplorerSnapshotQuery,
    KnowledgeGraphExplorerSnapshotResponse,
    KnowledgeGraphFacetResponse,
    KnowledgeGraphFacetsQuery,
    KnowledgeGraphNeighborhoodQuery,
    KnowledgeGraphRankedCandidateResponse,
    KnowledgeGraphRankedCandidatesQuery,
    KnowledgeGraphReevuDryRunPreviewQuery,
    KnowledgeGraphReevuDryRunPreviewResponse,
    KnowledgeGraphRetrievalCandidateResponse,
    KnowledgeGraphRetrievalCandidatesQuery,
    KnowledgeGraphRetrievalDiagnosticsQuery,
    KnowledgeGraphRetrievalDiagnosticsResponse,
    KnowledgeGraphUpsertEdgeCommand,
)


class KnowledgeGraphExplorerSnapshotReader(Protocol):
    async def build_explorer_snapshot(
        self, query: KnowledgeGraphExplorerSnapshotQuery
    ) -> KnowledgeGraphExplorerSnapshotResponse:
        """Return a UI-ready Knowledge Graph explorer snapshot."""


class KnowledgeGraphExplorerSnapshotDataSource(Protocol):
    async def get_facets(self, query: KnowledgeGraphFacetsQuery) -> KnowledgeGraphFacetResponse:
        """Return Knowledge Graph facets for a snapshot."""

    async def rank_retrieval_candidates(
        self, query: KnowledgeGraphRankedCandidatesQuery
    ) -> KnowledgeGraphRankedCandidateResponse:
        """Return ranked retrieval candidates for a snapshot."""

    async def build_retrieval_diagnostics(
        self, query: KnowledgeGraphRetrievalDiagnosticsQuery
    ) -> KnowledgeGraphRetrievalDiagnosticsResponse:
        """Return retrieval diagnostics for a snapshot."""


class KnowledgeGraphRankedCandidatesReader(Protocol):
    async def rank_retrieval_candidates(
        self, query: KnowledgeGraphRankedCandidatesQuery
    ) -> KnowledgeGraphRankedCandidateResponse:
        """Return deterministic Knowledge Graph retrieval candidate ranking."""


class KnowledgeGraphRetrievalDiagnosticsReader(Protocol):
    async def build_retrieval_diagnostics(
        self, query: KnowledgeGraphRetrievalDiagnosticsQuery
    ) -> KnowledgeGraphRetrievalDiagnosticsResponse:
        """Return diagnostics for Knowledge Graph retrieval readiness."""


class KnowledgeGraphRetrievalCandidatesReader(Protocol):
    async def build_retrieval_candidates(
        self, query: KnowledgeGraphRetrievalCandidatesQuery
    ) -> KnowledgeGraphRetrievalCandidateResponse:
        """Return Knowledge Graph retrieval candidates."""


class KnowledgeGraphEvidenceSearchReader(Protocol):
    async def search_evidence(
        self, query: KnowledgeGraphEvidenceSearchQuery
    ) -> KnowledgeGraphEvidenceSearchResponse:
        """Return one-hop evidence search results."""


class KnowledgeGraphEvidenceSearchDataSource(Protocol):
    def normalize_result_side(self, result_side: str) -> str:
        """Return the canonical evidence-search result side."""

    def normalize_asset_type(self, asset_type: str) -> str:
        """Return the canonical FAIR asset type."""

    def normalize_relationship_type(self, relationship_type: str) -> str:
        """Return the canonical graph relationship type."""

    async def list_edges(
        self, query: KnowledgeGraphEdgesListQuery
    ) -> list[KnowledgeGraphEdgeRecord]:
        """Return candidate evidence edges."""

    async def require_fair_asset(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_id: str,
    ) -> KnowledgeGraphFairAssetRecord:
        """Return FAIR metadata for an evidence result asset."""


class KnowledgeGraphEvidencePackReader(Protocol):
    async def build_evidence_pack(
        self, query: KnowledgeGraphEvidencePackQuery
    ) -> KnowledgeGraphEvidencePackResponse:
        """Return an evidence pack for a graph asset."""


class KnowledgeGraphEvidencePackDataSource(Protocol):
    def normalize_asset_type(self, asset_type: str) -> str:
        """Return the canonical FAIR asset type."""

    async def require_fair_asset(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_id: str,
    ) -> KnowledgeGraphFairAssetRecord:
        """Return FAIR metadata for an evidence-pack asset."""

    async def get_neighborhood(
        self, query: KnowledgeGraphNeighborhoodQuery
    ) -> KnowledgeGraphNeighborhoodRecord:
        """Return the one-hop graph neighborhood for an evidence pack."""


class KnowledgeGraphFacetsReader(Protocol):
    async def get_facets(self, query: KnowledgeGraphFacetsQuery) -> KnowledgeGraphFacetResponse:
        """Return Knowledge Graph facets."""


class KnowledgeGraphEdgesListReader(Protocol):
    async def list_edges(
        self, query: KnowledgeGraphEdgesListQuery
    ) -> list[KnowledgeGraphEdgeRecord]:
        """Return Knowledge Graph edges."""


class KnowledgeGraphEdgeWriter(Protocol):
    async def upsert_edge(self, command: KnowledgeGraphUpsertEdgeCommand) -> KnowledgeGraphEdgeRecord:
        """Create or update a Knowledge Graph edge."""


class KnowledgeGraphNeighborhoodReader(Protocol):
    async def get_neighborhood(
        self, query: KnowledgeGraphNeighborhoodQuery
    ) -> KnowledgeGraphNeighborhoodRecord:
        """Return a Knowledge Graph one-hop neighborhood."""


class KnowledgeGraphRetrievalCandidateDataSource(Protocol):
    def normalize_direction(self, direction: str) -> str:
        """Return the canonical graph direction or raise the current validation error."""

    async def search_evidence(
        self, query: KnowledgeGraphEvidenceSearchQuery
    ) -> KnowledgeGraphEvidenceSearchResponse:
        """Return one-hop evidence search results."""

    async def build_evidence_pack(
        self, query: KnowledgeGraphEvidencePackQuery
    ) -> KnowledgeGraphEvidencePackResponse:
        """Return an evidence pack for a candidate asset."""


class KnowledgeGraphReevuDryRunPreviewReader(Protocol):
    async def build_reevu_dry_run_preview(
        self, query: KnowledgeGraphReevuDryRunPreviewQuery
    ) -> KnowledgeGraphReevuDryRunPreviewResponse:
        """Return a dry-run REEVU preview without invoking the REEVU runtime."""


class KnowledgeGraphReevuDryRunPreviewDataSource(Protocol):
    async def rank_retrieval_candidates(
        self, query: KnowledgeGraphRankedCandidatesQuery
    ) -> KnowledgeGraphRankedCandidateResponse:
        """Return ranked retrieval candidates for a dry-run preview."""

    async def build_retrieval_diagnostics(
        self, query: KnowledgeGraphRetrievalDiagnosticsQuery
    ) -> KnowledgeGraphRetrievalDiagnosticsResponse:
        """Return retrieval diagnostics for a dry-run preview."""

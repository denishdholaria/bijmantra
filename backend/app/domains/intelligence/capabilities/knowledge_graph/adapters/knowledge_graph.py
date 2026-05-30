"""Infrastructure adapters for Intelligence Knowledge Graph use cases."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEdgeResponse,
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
    KnowledgeGraphNeighborhoodResponse,
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
from app.services.knowledge_graph_service import KnowledgeGraphService


class SqlAlchemyKnowledgeGraphAdapter:
    """Adapter from Intelligence Knowledge Graph use case ports to the legacy service."""

    def __init__(
        self,
        db: AsyncSession,
        service: KnowledgeGraphService | None = None,
    ) -> None:
        self._db = db
        self._service = service or KnowledgeGraphService()

    async def upsert_edge(
        self, command: KnowledgeGraphUpsertEdgeCommand
    ) -> KnowledgeGraphEdgeResponse:
        edge = await self._service.upsert_edge(
            self._db,
            organization_id=command.organization_id,
            payload=command.payload,
        )
        return KnowledgeGraphEdgeResponse.model_validate(edge)

    async def build_explorer_snapshot(
        self, query: KnowledgeGraphExplorerSnapshotQuery
    ) -> KnowledgeGraphExplorerSnapshotResponse:
        return await self._service.build_explorer_snapshot(
            self._db,
            organization_id=query.organization_id,
            source_asset_type=query.source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=query.target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=query.relationship_type,
            result_side=query.result_side,
            candidate_direction=query.candidate_direction,
            minimum_confidence=query.minimum_confidence,
            limit=query.limit,
            offset=query.offset,
            candidate_edge_limit=query.candidate_edge_limit,
        )

    async def rank_retrieval_candidates(
        self, query: KnowledgeGraphRankedCandidatesQuery
    ) -> KnowledgeGraphRankedCandidateResponse:
        return await self._service.rank_retrieval_candidates(
            self._db,
            organization_id=query.organization_id,
            source_asset_type=query.source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=query.target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=query.relationship_type,
            result_side=query.result_side,
            candidate_direction=query.candidate_direction,
            limit=query.limit,
            offset=query.offset,
            candidate_edge_limit=query.candidate_edge_limit,
        )

    async def build_retrieval_diagnostics(
        self, query: KnowledgeGraphRetrievalDiagnosticsQuery
    ) -> KnowledgeGraphRetrievalDiagnosticsResponse:
        return await self._service.build_retrieval_diagnostics(
            self._db,
            organization_id=query.organization_id,
            source_asset_type=query.source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=query.target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=query.relationship_type,
            result_side=query.result_side,
            candidate_direction=query.candidate_direction,
            minimum_confidence=query.minimum_confidence,
            limit=query.limit,
            offset=query.offset,
            candidate_edge_limit=query.candidate_edge_limit,
        )

    async def build_retrieval_candidates(
        self, query: KnowledgeGraphRetrievalCandidatesQuery
    ) -> KnowledgeGraphRetrievalCandidateResponse:
        return await self._service.build_retrieval_candidates(
            self._db,
            organization_id=query.organization_id,
            source_asset_type=query.source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=query.target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=query.relationship_type,
            result_side=query.result_side,
            candidate_direction=query.candidate_direction,
            limit=query.limit,
            offset=query.offset,
            candidate_edge_limit=query.candidate_edge_limit,
        )

    async def search_evidence(
        self, query: KnowledgeGraphEvidenceSearchQuery
    ) -> KnowledgeGraphEvidenceSearchResponse:
        return await self._service.search_evidence(
            self._db,
            organization_id=query.organization_id,
            source_asset_type=query.source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=query.target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=query.relationship_type,
            result_side=query.result_side,
            limit=query.limit,
            offset=query.offset,
        )

    async def get_facets(self, query: KnowledgeGraphFacetsQuery) -> KnowledgeGraphFacetResponse:
        return await self._service.get_facets(
            self._db,
            organization_id=query.organization_id,
            source_asset_type=query.source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=query.target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=query.relationship_type,
        )

    async def list_edges(
        self, query: KnowledgeGraphEdgesListQuery
    ) -> list[KnowledgeGraphEdgeResponse]:
        edges = await self._service.list_edges(
            self._db,
            organization_id=query.organization_id,
            source_asset_type=query.source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=query.target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=query.relationship_type,
            limit=query.limit,
            offset=query.offset,
        )
        return [KnowledgeGraphEdgeResponse.model_validate(edge) for edge in edges]

    async def get_neighborhood(
        self, query: KnowledgeGraphNeighborhoodQuery
    ) -> KnowledgeGraphNeighborhoodResponse:
        return await self._service.get_neighborhood(
            self._db,
            organization_id=query.organization_id,
            asset_type=query.asset_type,
            asset_id=query.asset_id,
            direction=query.direction,
            relationship_type=query.relationship_type,
            limit=query.limit,
            offset=query.offset,
        )

    async def build_evidence_pack(
        self, query: KnowledgeGraphEvidencePackQuery
    ) -> KnowledgeGraphEvidencePackResponse:
        return await self._service.build_evidence_pack(
            self._db,
            organization_id=query.organization_id,
            asset_type=query.asset_type,
            asset_id=query.asset_id,
            direction=query.direction,
            relationship_type=query.relationship_type,
            limit=query.limit,
            offset=query.offset,
        )

    async def build_reevu_dry_run_preview(
        self, query: KnowledgeGraphReevuDryRunPreviewQuery
    ) -> KnowledgeGraphReevuDryRunPreviewResponse:
        return await self._service.build_reevu_dry_run_preview(
            self._db,
            organization_id=query.organization_id,
            prompt=query.prompt,
            source_asset_type=query.source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=query.target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=query.relationship_type,
            result_side=query.result_side,
            candidate_direction=query.candidate_direction,
            minimum_confidence=query.minimum_confidence,
            limit=query.limit,
            offset=query.offset,
            candidate_edge_limit=query.candidate_edge_limit,
        )


class SqlAlchemyKnowledgeGraphExplorerSnapshotAdapter(SqlAlchemyKnowledgeGraphAdapter):
    """Backward-compatible alias for the first Intelligence Knowledge Graph bridge."""

import pytest

from app.domains.intelligence.capabilities.knowledge_graph.application.knowledge_graph import (
    KnowledgeGraphExplorerSnapshotBuilder,
    KnowledgeGraphReevuDryRunPreviewBuilder,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphExplorerSnapshotQuery,
    KnowledgeGraphFacetResponse,
    KnowledgeGraphFacetsQuery,
    KnowledgeGraphRankedCandidateResponse,
    KnowledgeGraphRankedCandidatesQuery,
    KnowledgeGraphReevuDryRunPreviewQuery,
    KnowledgeGraphRetrievalCandidateResponse,
    KnowledgeGraphRetrievalDiagnosticsQuery,
    KnowledgeGraphRetrievalDiagnosticsResponse,
)


def _empty_candidates() -> KnowledgeGraphRetrievalCandidateResponse:
    return KnowledgeGraphRetrievalCandidateResponse(
        result_side="source",
        candidate_direction="both",
        search_result_count=0,
        candidate_count=0,
    )


def _empty_ranked_candidates() -> KnowledgeGraphRankedCandidateResponse:
    return KnowledgeGraphRankedCandidateResponse(candidates=_empty_candidates())


def _empty_diagnostics() -> KnowledgeGraphRetrievalDiagnosticsResponse:
    return KnowledgeGraphRetrievalDiagnosticsResponse(
        candidates=_empty_candidates(),
        total_matched_edges=0,
        total_matched_evidence_refs=0,
        matched_edges_without_evidence_count=0,
        low_confidence_edge_count=0,
        missing_confidence_edge_count=0,
        readiness={"status": "ready_for_experimentation", "reasons": []},
    )


class FakePreviewSnapshotDataSource:
    def __init__(self) -> None:
        self.seen_facets_queries: list[KnowledgeGraphFacetsQuery] = []
        self.seen_ranked_queries: list[KnowledgeGraphRankedCandidatesQuery] = []
        self.seen_diagnostics_queries: list[KnowledgeGraphRetrievalDiagnosticsQuery] = []

    async def get_facets(self, query: KnowledgeGraphFacetsQuery) -> KnowledgeGraphFacetResponse:
        self.seen_facets_queries.append(query)
        return KnowledgeGraphFacetResponse(
            total_edge_count=3,
            relationship_type_counts={"has_trait": 2},
            source_asset_type_counts={"germplasm": 2},
            target_asset_type_counts={"observation_variable": 2},
        )

    async def rank_retrieval_candidates(
        self, query: KnowledgeGraphRankedCandidatesQuery
    ) -> KnowledgeGraphRankedCandidateResponse:
        self.seen_ranked_queries.append(query)
        return _empty_ranked_candidates()

    async def build_retrieval_diagnostics(
        self, query: KnowledgeGraphRetrievalDiagnosticsQuery
    ) -> KnowledgeGraphRetrievalDiagnosticsResponse:
        self.seen_diagnostics_queries.append(query)
        return _empty_diagnostics()


@pytest.mark.asyncio
async def test_reevu_preview_builder_keeps_authority_boundary_explicit() -> None:
    data_source = FakePreviewSnapshotDataSource()
    query = KnowledgeGraphReevuDryRunPreviewQuery(
        organization_id=7,
        prompt="what evidence supports IR64?",
        source_asset_type="germplasm",
        source_asset_id="IR64",
        target_asset_type="observation_variable",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="both",
        minimum_confidence=0.75,
        limit=20,
        offset=5,
        candidate_edge_limit=25,
    )

    response = await KnowledgeGraphReevuDryRunPreviewBuilder(data_source).execute(query)

    assert data_source.seen_ranked_queries == [
        KnowledgeGraphRankedCandidatesQuery(
            organization_id=7,
            source_asset_type="germplasm",
            source_asset_id="IR64",
            target_asset_type="observation_variable",
            relationship_type="has_trait",
            result_side="source",
            candidate_direction="both",
            limit=20,
            offset=5,
            candidate_edge_limit=25,
        )
    ]
    assert data_source.seen_diagnostics_queries == [
        KnowledgeGraphRetrievalDiagnosticsQuery(
            organization_id=7,
            source_asset_type="germplasm",
            source_asset_id="IR64",
            target_asset_type="observation_variable",
            relationship_type="has_trait",
            result_side="source",
            candidate_direction="both",
            minimum_confidence=0.75,
            limit=20,
            offset=5,
            candidate_edge_limit=25,
        )
    ]
    assert response.authority_boundary["dryRunOnly"] is True
    assert response.authority_boundary["reevuRuntimeInvoked"] is False
    assert response.retrieval_policy["trustedReevuSurfaceExpanded"] is False


@pytest.mark.asyncio
async def test_explorer_snapshot_builder_packages_ui_ready_context() -> None:
    data_source = FakePreviewSnapshotDataSource()
    query = KnowledgeGraphExplorerSnapshotQuery(
        organization_id=7,
        source_asset_type="germplasm",
        source_asset_id="IR64",
        target_asset_type="observation_variable",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="both",
        minimum_confidence=0.75,
        limit=20,
        offset=5,
        candidate_edge_limit=25,
    )

    response = await KnowledgeGraphExplorerSnapshotBuilder(data_source).execute(query)

    assert data_source.seen_facets_queries == [
        KnowledgeGraphFacetsQuery(
            organization_id=7,
            source_asset_type="germplasm",
            source_asset_id="IR64",
            target_asset_type="observation_variable",
            relationship_type="has_trait",
        )
    ]
    assert response.snapshot_summary == {
        "totalEdgeCount": 3,
        "candidateCount": 0,
        "rankedCandidateCount": 0,
        "matchedEdgeCount": 0,
        "matchedEvidenceRefCount": 0,
        "readinessStatus": "ready_for_experimentation",
        "relationshipTypeCount": 1,
        "sourceAssetTypeCount": 1,
        "targetAssetTypeCount": 1,
        "assetTypePairCount": 0,
    }
    assert response.retrieval_policy["explorerOnly"] is True
    assert response.retrieval_policy["reevuRuntimeInvoked"] is False

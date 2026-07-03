from datetime import UTC, datetime

import pytest

from app.domains.intelligence.capabilities.knowledge_graph.application.knowledge_graph import (
    KnowledgeGraphEdgesListUseCase,
    KnowledgeGraphEvidencePackUseCase,
    KnowledgeGraphEvidenceSearchUseCase,
    KnowledgeGraphExplorerSnapshotUseCase,
    KnowledgeGraphFacetsUseCase,
    KnowledgeGraphNeighborhoodUseCase,
    KnowledgeGraphRankedCandidatesUseCase,
    KnowledgeGraphReevuDryRunPreviewUseCase,
    KnowledgeGraphRetrievalCandidatesUseCase,
    KnowledgeGraphRetrievalDiagnosticsUseCase,
    KnowledgeGraphUpsertEdgeUseCase,
)
from app.domains.intelligence.capabilities.knowledge_graph.ports.records import (
    KnowledgeGraphEdgeRecord,
    KnowledgeGraphNeighborhoodRecord,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEdgesListQuery,
    KnowledgeGraphEdgeCreate,
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
    KnowledgeGraphReevuDryRunPreviewResponse,
    KnowledgeGraphReevuDryRunPreviewQuery,
    KnowledgeGraphRetrievalCandidateResponse,
    KnowledgeGraphRetrievalCandidatesQuery,
    KnowledgeGraphRetrievalDiagnosticsResponse,
    KnowledgeGraphRetrievalDiagnosticsQuery,
    KnowledgeGraphUpsertEdgeCommand,
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
    )


def _empty_snapshot() -> KnowledgeGraphExplorerSnapshotResponse:
    return KnowledgeGraphExplorerSnapshotResponse(
        facets=KnowledgeGraphFacetResponse(total_edge_count=0),
        ranked_candidates=_empty_ranked_candidates(),
        diagnostics=_empty_diagnostics(),
    )


def _empty_reevu_preview() -> KnowledgeGraphReevuDryRunPreviewResponse:
    return KnowledgeGraphReevuDryRunPreviewResponse(
        ranked_candidates=_empty_ranked_candidates(),
        diagnostics=_empty_diagnostics(),
    )


def _empty_evidence_search() -> KnowledgeGraphEvidenceSearchResponse:
    return KnowledgeGraphEvidenceSearchResponse(
        result_side="source",
        result_count=0,
    )


def _empty_evidence_pack() -> KnowledgeGraphEvidencePackResponse:
    return KnowledgeGraphEvidencePackResponse(
        asset_type="germplasm",
        asset_id="IR64",
        asset_title="IR64",
        persistent_identifier="bijmantra:germplasm:IR64",
        direction="outgoing",
        neighborhood=KnowledgeGraphNeighborhoodResponse(
            asset_type="germplasm",
            asset_id="IR64",
            direction="outgoing",
            edge_count=0,
        ),
        edge_count=0,
    )


def _edge_record() -> KnowledgeGraphEdgeRecord:
    now = datetime(2026, 5, 24, tzinfo=UTC)
    return KnowledgeGraphEdgeRecord(
        id=1,
        organization_id=7,
        edge_id="kg-edge-1",
        source_asset_type="germplasm",
        source_asset_id="IR64",
        relationship_type="has_trait",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        evidence_refs=[],
        provenance={},
        confidence=0.88,
        derivation_method="manual_curated",
        status="active",
        schema_version="agricultural_knowledge_graph_edge.v1",
        created_at=now,
        updated_at=now,
    )


class FakeExplorerSnapshotReader:
    def __init__(self) -> None:
        self.seen_queries: list[KnowledgeGraphExplorerSnapshotQuery] = []
        self.seen_ranked_queries: list[KnowledgeGraphRankedCandidatesQuery] = []
        self.seen_diagnostics_queries: list[KnowledgeGraphRetrievalDiagnosticsQuery] = []
        self.seen_candidates_queries: list[KnowledgeGraphRetrievalCandidatesQuery] = []
        self.seen_reevu_preview_queries: list[KnowledgeGraphReevuDryRunPreviewQuery] = []
        self.seen_evidence_search_queries: list[KnowledgeGraphEvidenceSearchQuery] = []
        self.seen_evidence_pack_queries: list[KnowledgeGraphEvidencePackQuery] = []
        self.seen_facets_queries: list[KnowledgeGraphFacetsQuery] = []
        self.seen_edges_list_queries: list[KnowledgeGraphEdgesListQuery] = []
        self.seen_neighborhood_queries: list[KnowledgeGraphNeighborhoodQuery] = []
        self.seen_upsert_commands: list[KnowledgeGraphUpsertEdgeCommand] = []

    async def build_explorer_snapshot(
        self, query: KnowledgeGraphExplorerSnapshotQuery
    ) -> KnowledgeGraphExplorerSnapshotResponse:
        self.seen_queries.append(query)
        return _empty_snapshot()

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

    async def build_retrieval_candidates(
        self, query: KnowledgeGraphRetrievalCandidatesQuery
    ) -> KnowledgeGraphRetrievalCandidateResponse:
        self.seen_candidates_queries.append(query)
        return _empty_candidates()

    async def build_reevu_dry_run_preview(
        self, query: KnowledgeGraphReevuDryRunPreviewQuery
    ) -> KnowledgeGraphReevuDryRunPreviewResponse:
        self.seen_reevu_preview_queries.append(query)
        return _empty_reevu_preview()

    async def search_evidence(
        self, query: KnowledgeGraphEvidenceSearchQuery
    ) -> KnowledgeGraphEvidenceSearchResponse:
        self.seen_evidence_search_queries.append(query)
        return _empty_evidence_search()

    async def build_evidence_pack(
        self, query: KnowledgeGraphEvidencePackQuery
    ) -> KnowledgeGraphEvidencePackResponse:
        self.seen_evidence_pack_queries.append(query)
        return _empty_evidence_pack()

    async def get_facets(self, query: KnowledgeGraphFacetsQuery) -> KnowledgeGraphFacetResponse:
        self.seen_facets_queries.append(query)
        return KnowledgeGraphFacetResponse(total_edge_count=0)

    async def list_edges(
        self, query: KnowledgeGraphEdgesListQuery
    ) -> list[KnowledgeGraphEdgeRecord]:
        self.seen_edges_list_queries.append(query)
        return []

    async def get_neighborhood(
        self, query: KnowledgeGraphNeighborhoodQuery
    ) -> KnowledgeGraphNeighborhoodRecord:
        self.seen_neighborhood_queries.append(query)
        return KnowledgeGraphNeighborhoodRecord(
            asset_type=query.asset_type,
            asset_id=query.asset_id,
            direction=query.direction,
            edge_count=0,
        )

    async def upsert_edge(
        self, command: KnowledgeGraphUpsertEdgeCommand
    ) -> KnowledgeGraphEdgeRecord:
        self.seen_upsert_commands.append(command)
        return _edge_record()


@pytest.mark.asyncio
async def test_intelligence_explorer_snapshot_use_case_delegates_through_port() -> None:
    reader = FakeExplorerSnapshotReader()
    query = KnowledgeGraphExplorerSnapshotQuery(
        organization_id=7,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        minimum_confidence=0.75,
        limit=20,
        offset=5,
        candidate_edge_limit=25,
    )

    response = await KnowledgeGraphExplorerSnapshotUseCase(reader).execute(query)

    assert reader.seen_queries == [query]
    assert response.facets.total_edge_count == 0
    assert response.ranked_candidates.candidates.candidate_count == 0


@pytest.mark.asyncio
async def test_intelligence_ranked_candidates_use_case_delegates_through_port() -> None:
    reader = FakeExplorerSnapshotReader()
    query = KnowledgeGraphRankedCandidatesQuery(
        organization_id=7,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        limit=20,
        offset=5,
        candidate_edge_limit=25,
    )

    response = await KnowledgeGraphRankedCandidatesUseCase(reader).execute(query)

    assert reader.seen_ranked_queries == [query]
    assert response.candidates.candidate_count == 0


@pytest.mark.asyncio
async def test_intelligence_retrieval_diagnostics_use_case_delegates_through_port() -> None:
    reader = FakeExplorerSnapshotReader()
    query = KnowledgeGraphRetrievalDiagnosticsQuery(
        organization_id=7,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        minimum_confidence=0.75,
        limit=20,
        offset=5,
        candidate_edge_limit=25,
    )

    response = await KnowledgeGraphRetrievalDiagnosticsUseCase(reader).execute(query)

    assert reader.seen_diagnostics_queries == [query]
    assert response.total_matched_edges == 0


@pytest.mark.asyncio
async def test_intelligence_retrieval_candidates_use_case_delegates_through_port() -> None:
    reader = FakeExplorerSnapshotReader()
    query = KnowledgeGraphRetrievalCandidatesQuery(
        organization_id=7,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        limit=20,
        offset=5,
        candidate_edge_limit=25,
    )

    response = await KnowledgeGraphRetrievalCandidatesUseCase(reader).execute(query)

    assert reader.seen_candidates_queries == [query]
    assert response.candidate_count == 0


@pytest.mark.asyncio
async def test_intelligence_reevu_dry_run_preview_use_case_delegates_through_port() -> None:
    reader = FakeExplorerSnapshotReader()
    query = KnowledgeGraphReevuDryRunPreviewQuery(
        organization_id=7,
        prompt="Inspect drought candidates",
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        minimum_confidence=0.75,
        limit=20,
        offset=5,
        candidate_edge_limit=25,
    )

    response = await KnowledgeGraphReevuDryRunPreviewUseCase(reader).execute(query)

    assert reader.seen_reevu_preview_queries == [query]
    assert response.ranked_candidates.candidates.candidate_count == 0


@pytest.mark.asyncio
async def test_intelligence_evidence_search_use_case_delegates_through_port() -> None:
    reader = FakeExplorerSnapshotReader()
    query = KnowledgeGraphEvidenceSearchQuery(
        organization_id=7,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        relationship_type="has_trait",
        result_side="source",
        limit=20,
        offset=5,
    )

    response = await KnowledgeGraphEvidenceSearchUseCase(reader).execute(query)

    assert reader.seen_evidence_search_queries == [query]
    assert response.result_count == 0


@pytest.mark.asyncio
async def test_intelligence_evidence_pack_use_case_delegates_through_port() -> None:
    reader = FakeExplorerSnapshotReader()
    query = KnowledgeGraphEvidencePackQuery(
        organization_id=7,
        asset_type="germplasm",
        asset_id="IR64",
        direction="outgoing",
        relationship_type="has_trait",
        limit=20,
        offset=5,
    )

    response = await KnowledgeGraphEvidencePackUseCase(reader).execute(query)

    assert reader.seen_evidence_pack_queries == [query]
    assert response.asset_id == "IR64"


@pytest.mark.asyncio
async def test_intelligence_facets_use_case_delegates_through_port() -> None:
    reader = FakeExplorerSnapshotReader()
    query = KnowledgeGraphFacetsQuery(
        organization_id=7,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        relationship_type="has_trait",
    )

    response = await KnowledgeGraphFacetsUseCase(reader).execute(query)

    assert reader.seen_facets_queries == [query]
    assert response.total_edge_count == 0


@pytest.mark.asyncio
async def test_intelligence_edges_list_use_case_delegates_through_port() -> None:
    reader = FakeExplorerSnapshotReader()
    query = KnowledgeGraphEdgesListQuery(
        organization_id=7,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        relationship_type="has_trait",
        limit=20,
        offset=5,
    )

    response = await KnowledgeGraphEdgesListUseCase(reader).execute(query)

    assert reader.seen_edges_list_queries == [query]
    assert response == []


@pytest.mark.asyncio
async def test_intelligence_neighborhood_use_case_delegates_through_port() -> None:
    reader = FakeExplorerSnapshotReader()
    query = KnowledgeGraphNeighborhoodQuery(
        organization_id=7,
        asset_type="germplasm",
        asset_id="IR64",
        direction="outgoing",
        relationship_type="has_trait",
        limit=20,
        offset=5,
    )

    response = await KnowledgeGraphNeighborhoodUseCase(reader).execute(query)

    assert reader.seen_neighborhood_queries == [query]
    assert response.asset_id == "IR64"


@pytest.mark.asyncio
async def test_intelligence_upsert_edge_use_case_delegates_through_port() -> None:
    reader = FakeExplorerSnapshotReader()
    command = KnowledgeGraphUpsertEdgeCommand(
        organization_id=7,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            confidence=0.88,
        ),
    )

    response = await KnowledgeGraphUpsertEdgeUseCase(reader).execute(command)

    assert reader.seen_upsert_commands == [command]
    assert response.edge_id == "kg-edge-1"

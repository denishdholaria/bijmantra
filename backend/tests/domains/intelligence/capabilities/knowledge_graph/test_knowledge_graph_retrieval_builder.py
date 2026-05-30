from datetime import UTC, datetime

import pytest

from app.domains.intelligence.capabilities.knowledge_graph.application.knowledge_graph import (
    KnowledgeGraphRetrievalCandidatesBuilder,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEvidencePackQuery,
    KnowledgeGraphEvidenceSearchQuery,
    KnowledgeGraphRetrievalCandidatesQuery,
)
from app.schemas.knowledge_graph import (
    KnowledgeGraphEdgeResponse,
    KnowledgeGraphEvidencePackResponse,
    KnowledgeGraphEvidenceSearchResponse,
    KnowledgeGraphEvidenceSearchResult,
    KnowledgeGraphNeighborhoodResponse,
)


def _edge(edge_id: str, confidence: float) -> KnowledgeGraphEdgeResponse:
    now = datetime(2026, 5, 24, tzinfo=UTC)
    return KnowledgeGraphEdgeResponse(
        id=1 if edge_id == "edge-1" else 2,
        organization_id=7,
        edge_id=edge_id,
        source_asset_type="germplasm",
        source_asset_id="IR64",
        relationship_type="has_trait",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
        provenance={},
        confidence=confidence,
        derivation_method="manual_curated",
        status="active",
        schema_version="agricultural_knowledge_graph_edge.v1",
        created_at=now,
        updated_at=now,
    )


def _evidence_pack() -> KnowledgeGraphEvidencePackResponse:
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
            outgoing_edges=[],
            incoming_edges=[],
            edge_count=2,
        ),
        relationship_types=["has_trait"],
        evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
        edge_count=2,
    )


class FakeRetrievalDataSource:
    def __init__(self) -> None:
        self.seen_search_queries: list[KnowledgeGraphEvidenceSearchQuery] = []
        self.seen_pack_queries: list[KnowledgeGraphEvidencePackQuery] = []

    def normalize_direction(self, direction: str) -> str:
        assert direction == "outgoing"
        return "outgoing"

    async def search_evidence(
        self, query: KnowledgeGraphEvidenceSearchQuery
    ) -> KnowledgeGraphEvidenceSearchResponse:
        self.seen_search_queries.append(query)
        first_edge = _edge("edge-1", 0.88)
        second_edge = _edge("edge-2", 0.92)
        return KnowledgeGraphEvidenceSearchResponse(
            source_asset_type=query.source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=query.target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=query.relationship_type,
            result_side=query.result_side,
            results=[
                KnowledgeGraphEvidenceSearchResult(
                    asset_type="germplasm",
                    asset_id="IR64",
                    asset_title="IR64",
                    persistent_identifier="bijmantra:germplasm:IR64",
                    relationship_type="has_trait",
                    matched_edge=first_edge,
                    evidence_refs=first_edge.evidence_refs,
                    confidence=first_edge.confidence,
                ),
                KnowledgeGraphEvidenceSearchResult(
                    asset_type="germplasm",
                    asset_id="IR64",
                    asset_title="IR64",
                    persistent_identifier="bijmantra:germplasm:IR64",
                    relationship_type="has_trait",
                    matched_edge=second_edge,
                    evidence_refs=second_edge.evidence_refs,
                    confidence=second_edge.confidence,
                ),
            ],
            result_count=2,
        )

    async def build_evidence_pack(
        self, query: KnowledgeGraphEvidencePackQuery
    ) -> KnowledgeGraphEvidencePackResponse:
        self.seen_pack_queries.append(query)
        return _evidence_pack()


@pytest.mark.asyncio
async def test_intelligence_retrieval_builder_groups_results_and_builds_evidence_pack() -> None:
    data_source = FakeRetrievalDataSource()
    query = KnowledgeGraphRetrievalCandidatesQuery(
        organization_id=7,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        limit=20,
        offset=5,
        candidate_edge_limit=25,
    )

    response = await KnowledgeGraphRetrievalCandidatesBuilder(data_source).execute(query)

    assert response.result_side == "source"
    assert response.candidate_direction == "outgoing"
    assert response.search_result_count == 2
    assert response.candidate_count == 1
    assert response.candidates[0].asset_id == "IR64"
    assert response.candidates[0].match_count == 2
    assert len(response.candidates[0].matched_edges) == 2
    assert response.candidates[0].matched_evidence_refs == [
        {"entity_id": "trial:TRIAL-1"}
    ]
    assert data_source.seen_pack_queries == [
        KnowledgeGraphEvidencePackQuery(
            organization_id=7,
            asset_type="germplasm",
            asset_id="IR64",
            direction="outgoing",
            relationship_type=None,
            limit=25,
            offset=0,
        )
    ]

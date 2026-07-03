from datetime import UTC, datetime

import pytest

from app.domains.intelligence.capabilities.knowledge_graph.application.knowledge_graph import (
    KnowledgeGraphRankedCandidatesBuilder,
    KnowledgeGraphRetrievalDiagnosticsBuilder,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEdgeResponse,
    KnowledgeGraphEvidencePackResponse,
    KnowledgeGraphNeighborhoodResponse,
    KnowledgeGraphRankedCandidatesQuery,
    KnowledgeGraphRetrievalCandidate,
    KnowledgeGraphRetrievalCandidateResponse,
    KnowledgeGraphRetrievalCandidatesQuery,
    KnowledgeGraphRetrievalDiagnosticsQuery,
)


def _edge(edge_id: str, confidence: float | None) -> KnowledgeGraphEdgeResponse:
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


def _candidate_response() -> KnowledgeGraphRetrievalCandidateResponse:
    edges = [_edge("edge-1", 0.88), _edge("edge-2", 0.92)]
    return KnowledgeGraphRetrievalCandidateResponse(
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        candidates=[
            KnowledgeGraphRetrievalCandidate(
                asset_type="germplasm",
                asset_id="IR64",
                asset_title="IR64",
                persistent_identifier="bijmantra:germplasm:IR64",
                matched_edges=edges,
                matched_evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
                evidence_pack=KnowledgeGraphEvidencePackResponse(
                    asset_type="germplasm",
                    asset_id="IR64",
                    asset_title="IR64",
                    persistent_identifier="bijmantra:germplasm:IR64",
                    direction="outgoing",
                    neighborhood=KnowledgeGraphNeighborhoodResponse(
                        asset_type="germplasm",
                        asset_id="IR64",
                        direction="outgoing",
                        edge_count=2,
                    ),
                    edge_count=2,
                ),
                match_count=2,
            )
        ],
        search_result_count=2,
        candidate_count=1,
    )


class FakeRetrievalCandidatesReader:
    def __init__(self) -> None:
        self.seen_queries: list[KnowledgeGraphRetrievalCandidatesQuery] = []

    async def build_retrieval_candidates(
        self, query: KnowledgeGraphRetrievalCandidatesQuery
    ) -> KnowledgeGraphRetrievalCandidateResponse:
        self.seen_queries.append(query)
        return _candidate_response()


@pytest.mark.asyncio
async def test_ranked_candidates_builder_owns_deterministic_scoring_policy() -> None:
    reader = FakeRetrievalCandidatesReader()
    query = KnowledgeGraphRankedCandidatesQuery(
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

    response = await KnowledgeGraphRankedCandidatesBuilder(reader).execute(query)

    assert reader.seen_queries == [
        KnowledgeGraphRetrievalCandidatesQuery(
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
    ]
    assert response.ranked_candidates[0].rank == 1
    assert response.ranked_candidates[0].retrieval_score == 0.602
    assert response.ranked_candidates[0].score_factors == {
        "match_count": 0.667,
        "average_confidence": 0.9,
        "evidence_refs": 0.333,
        "evidence_pack_edges": 0.4,
    }
    assert response.retrieval_policy["deterministicScoring"] is True
    assert response.retrieval_policy["truthScore"] is False


@pytest.mark.asyncio
async def test_retrieval_diagnostics_builder_owns_quality_summary_policy() -> None:
    reader = FakeRetrievalCandidatesReader()
    query = KnowledgeGraphRetrievalDiagnosticsQuery(
        organization_id=7,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        minimum_confidence=0.9,
        limit=20,
        offset=5,
        candidate_edge_limit=25,
    )

    response = await KnowledgeGraphRetrievalDiagnosticsBuilder(reader).execute(query)

    assert response.relationship_type_counts == {"has_trait": 2}
    assert response.total_matched_edges == 2
    assert response.total_matched_evidence_refs == 1
    assert response.low_confidence_edge_count == 1
    assert response.missing_confidence_edge_count == 0
    assert response.candidate_diagnostics[0].warnings == ["low_confidence_edges"]
    assert response.readiness == {
        "status": "needs_review",
        "reasons": ["low_confidence_edges"],
    }
    assert response.retrieval_policy["diagnosticOnly"] is True

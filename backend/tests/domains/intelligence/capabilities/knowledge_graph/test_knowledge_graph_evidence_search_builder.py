from datetime import UTC, datetime

import pytest

from app.domains.intelligence.capabilities.knowledge_graph.application.knowledge_graph import KnowledgeGraphEvidenceSearchBuilder
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEdgeResponse,
    KnowledgeGraphEdgesListQuery,
    KnowledgeGraphEvidenceSearchQuery,
    KnowledgeGraphFairAssetRef,
)


def _edge() -> KnowledgeGraphEdgeResponse:
    now = datetime(2026, 5, 24, tzinfo=UTC)
    return KnowledgeGraphEdgeResponse(
        id=1,
        organization_id=7,
        edge_id="kg-edge-1",
        source_asset_type="germplasm",
        source_asset_id="IR64",
        relationship_type="has_trait",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
        provenance={"source": "curated"},
        confidence=0.88,
        derivation_method="manual_curated",
        status="active",
        schema_version="agricultural_knowledge_graph_edge.v1",
        created_at=now,
        updated_at=now,
    )


class FakeEvidenceSearchDataSource:
    def __init__(self) -> None:
        self.seen_edge_queries: list[KnowledgeGraphEdgesListQuery] = []
        self.seen_asset_refs: list[tuple[int, str, str]] = []

    def normalize_result_side(self, result_side: str) -> str:
        assert result_side == "source"
        return "source"

    def normalize_asset_type(self, asset_type: str) -> str:
        return asset_type.lower()

    def normalize_relationship_type(self, relationship_type: str) -> str:
        return relationship_type.lower()

    async def list_edges(
        self, query: KnowledgeGraphEdgesListQuery
    ) -> list[KnowledgeGraphEdgeResponse]:
        self.seen_edge_queries.append(query)
        return [_edge()]

    async def require_fair_asset(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_id: str,
    ) -> KnowledgeGraphFairAssetRef:
        self.seen_asset_refs.append((organization_id, asset_type, asset_id))
        return KnowledgeGraphFairAssetRef(
            asset_type=asset_type,
            asset_id=asset_id,
            asset_title="IR64",
            persistent_identifier="bijmantra:germplasm:IR64",
        )


@pytest.mark.asyncio
async def test_intelligence_evidence_search_builder_projects_result_assets() -> None:
    data_source = FakeEvidenceSearchDataSource()

    response = await KnowledgeGraphEvidenceSearchBuilder(data_source).execute(
        KnowledgeGraphEvidenceSearchQuery(
            organization_id=7,
            source_asset_type="GERMPLASM",
            target_asset_type="OBSERVATION_VARIABLE",
            target_asset_id="CO:0000001",
            relationship_type="HAS_TRAIT",
            result_side="source",
            limit=20,
            offset=5,
        )
    )

    assert data_source.seen_edge_queries == [
        KnowledgeGraphEdgesListQuery(
            organization_id=7,
            source_asset_type="germplasm",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            relationship_type="has_trait",
            limit=20,
            offset=5,
        )
    ]
    assert data_source.seen_asset_refs == [(7, "germplasm", "IR64")]
    assert response.result_side == "source"
    assert response.result_count == 1
    assert response.results[0].asset_title == "IR64"
    assert response.results[0].matched_edge.edge_id == "kg-edge-1"
    assert response.retrieval_policy["trustedReevuSurfaceExpanded"] is False

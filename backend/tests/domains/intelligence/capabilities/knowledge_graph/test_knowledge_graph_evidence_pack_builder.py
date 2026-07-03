from datetime import UTC, datetime

import pytest

from app.domains.intelligence.capabilities.knowledge_graph.application.knowledge_graph import KnowledgeGraphEvidencePackBuilder
from app.domains.intelligence.capabilities.knowledge_graph.ports.records import (
    KnowledgeGraphEdgeRecord,
    KnowledgeGraphFairAssetRecord,
    KnowledgeGraphNeighborhoodRecord,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEvidencePackQuery,
    KnowledgeGraphNeighborhoodQuery,
)


def _edge(edge_id: str) -> KnowledgeGraphEdgeRecord:
    now = datetime(2026, 5, 24, tzinfo=UTC)
    return KnowledgeGraphEdgeRecord(
        id=1 if edge_id == "kg-edge-1" else 2,
        organization_id=7,
        edge_id=edge_id,
        source_asset_type="germplasm",
        source_asset_id="IR64",
        relationship_type="has_trait",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
        provenance={},
        confidence=0.88,
        derivation_method="manual_curated",
        status="active",
        schema_version="agricultural_knowledge_graph_edge.v1",
        created_at=now,
        updated_at=now,
    )


class FakeEvidencePackDataSource:
    def __init__(self) -> None:
        self.seen_assets: list[tuple[int, str, str]] = []
        self.seen_neighborhood_queries: list[KnowledgeGraphNeighborhoodQuery] = []

    def normalize_asset_type(self, asset_type: str) -> str:
        return asset_type.lower()

    async def require_fair_asset(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_id: str,
    ) -> KnowledgeGraphFairAssetRecord:
        self.seen_assets.append((organization_id, asset_type, asset_id))
        return KnowledgeGraphFairAssetRecord(
            asset_type=asset_type,
            asset_id=asset_id,
            asset_title="IR64",
            persistent_identifier="bijmantra:germplasm:IR64",
        )

    async def get_neighborhood(
        self, query: KnowledgeGraphNeighborhoodQuery
    ) -> KnowledgeGraphNeighborhoodRecord:
        self.seen_neighborhood_queries.append(query)
        return KnowledgeGraphNeighborhoodRecord(
            asset_type=query.asset_type,
            asset_id=query.asset_id,
            direction=query.direction,
            relationship_type=query.relationship_type,
            outgoing_edges=[_edge("kg-edge-1"), _edge("kg-edge-2")],
            incoming_edges=[],
            edge_count=2,
        )


@pytest.mark.asyncio
async def test_intelligence_evidence_pack_builder_deduplicates_refs_and_preserves_policy() -> None:
    data_source = FakeEvidencePackDataSource()

    response = await KnowledgeGraphEvidencePackBuilder(data_source).execute(
        KnowledgeGraphEvidencePackQuery(
            organization_id=7,
            asset_type="GERMPLASM",
            asset_id="IR64",
            direction="outgoing",
            relationship_type="has_trait",
            limit=20,
            offset=5,
        )
    )

    assert data_source.seen_assets == [(7, "germplasm", "IR64")]
    assert data_source.seen_neighborhood_queries == [
        KnowledgeGraphNeighborhoodQuery(
            organization_id=7,
            asset_type="germplasm",
            asset_id="IR64",
            direction="outgoing",
            relationship_type="has_trait",
            limit=20,
            offset=5,
        )
    ]
    assert response.asset_title == "IR64"
    assert response.relationship_types == ["has_trait"]
    assert response.evidence_refs == [{"entity_id": "trial:TRIAL-1"}]
    assert response.edge_count == 2
    assert response.retrieval_policy["trustedReevuSurfaceExpanded"] is False

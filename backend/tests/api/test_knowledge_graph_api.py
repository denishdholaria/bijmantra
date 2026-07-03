from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.intelligence.capabilities.knowledge_graph.adapters.api import (
    knowledge_graph as knowledge_graph_api,
)
from app.domains.intelligence.capabilities.knowledge_graph.adapters.api.knowledge_graph import (
    create_knowledge_graph_edge,
    get_knowledge_graph_evidence_pack,
    get_knowledge_graph_neighborhood,
    list_knowledge_graph_edges,
)
from app.models.fair_metadata import FairAssetMetadata
from app.models.knowledge_graph import AgriculturalKnowledgeGraphEdge
from app.schemas.knowledge_graph import KnowledgeGraphEdgeCreate


@pytest.fixture(autouse=True)
async def create_knowledge_graph_api_tables(async_db_session: AsyncSession):
    engine = async_db_session.bind
    tables = [
        FairAssetMetadata.__table__,
        AgriculturalKnowledgeGraphEdge.__table__,
    ]
    async with engine.begin() as conn:
        for table in tables:
            await conn.run_sync(lambda sync_conn, table=table: table.create(sync_conn, checkfirst=True))
    yield


async def _fair_asset(
    db: AsyncSession,
    *,
    organization_id: int,
    asset_type: str,
    asset_db_id: str,
    title: str,
) -> None:
    db.add(
        FairAssetMetadata(
            organization_id=organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            persistent_identifier=f"bijmantra:{asset_type}:{asset_db_id}",
            title=title,
            schema_version="fair_asset_metadata.v1",
        )
    )
    await db.flush()


def _current_user(test_user):
    return SimpleNamespace(id=test_user.id, organization_id=test_user.organization_id)


@pytest.mark.asyncio
async def test_knowledge_graph_api_create_and_list_edges_shape(
    async_db_session: AsyncSession,
    test_user,
):
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_db_id="IR64",
        title="IR64",
    )
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="observation_variable",
        asset_db_id="CO:0000001",
        title="Drought tolerance",
    )
    current_user = _current_user(test_user)

    created = await create_knowledge_graph_edge(
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            confidence=0.88,
            evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
        ),
        db=async_db_session,
        current_user=current_user,
    )

    assert created.organization_id == test_user.organization_id
    assert created.relationship_type == "has_trait"
    assert created.evidence_refs == [{"entity_id": "trial:TRIAL-1"}]

    listed = await list_knowledge_graph_edges(
        source_asset_type="germplasm",
        source_asset_id="IR64",
        target_asset_type=None,
        target_asset_id=None,
        relationship_type="has_trait",
        limit=20,
        offset=0,
        db=async_db_session,
        current_user=current_user,
    )

    assert [edge.id for edge in listed] == [created.id]

    neighborhood = await get_knowledge_graph_neighborhood(
        asset_type="germplasm",
        asset_id="IR64",
        direction="outgoing",
        relationship_type="has_trait",
        limit=20,
        offset=0,
        db=async_db_session,
        current_user=current_user,
    )

    assert neighborhood.asset_type == "germplasm"
    assert neighborhood.asset_id == "IR64"
    assert neighborhood.edge_count == 1
    assert [edge.id for edge in neighborhood.outgoing_edges] == [created.id]
    assert neighborhood.incoming_edges == []

    evidence_pack = await get_knowledge_graph_evidence_pack(
        asset_type="germplasm",
        asset_id="IR64",
        direction="outgoing",
        relationship_type="has_trait",
        limit=20,
        offset=0,
        db=async_db_session,
        current_user=current_user,
    )

    assert evidence_pack.asset_title == "IR64"
    assert evidence_pack.persistent_identifier == "bijmantra:germplasm:IR64"
    assert evidence_pack.edge_count == 1
    assert evidence_pack.relationship_types == ["has_trait"]
    assert evidence_pack.evidence_refs == [{"entity_id": "trial:TRIAL-1"}]
    assert evidence_pack.retrieval_policy["trustedReevuSurfaceExpanded"] is False


@pytest.mark.asyncio
async def test_knowledge_graph_api_evidence_search_shape(
    async_db_session: AsyncSession,
    test_user,
):
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_db_id="IR64",
        title="IR64",
    )
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="observation_variable",
        asset_db_id="CO:0000001",
        title="Drought tolerance",
    )
    current_user = _current_user(test_user)
    created = await create_knowledge_graph_edge(
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
            confidence=0.88,
        ),
        db=async_db_session,
        current_user=current_user,
    )

    response = await knowledge_graph_api.search_knowledge_graph_evidence(
        source_asset_type="germplasm",
        source_asset_id=None,
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        relationship_type="has_trait",
        result_side="source",
        limit=20,
        offset=0,
        db=async_db_session,
        current_user=current_user,
    )

    assert response.result_side == "source"
    assert response.result_count == 1
    assert response.results[0].asset_type == "germplasm"
    assert response.results[0].asset_id == "IR64"
    assert response.results[0].asset_title == "IR64"
    assert response.results[0].persistent_identifier == "bijmantra:germplasm:IR64"
    assert response.results[0].matched_edge.id == created.id
    assert response.results[0].evidence_refs == [{"entity_id": "trial:TRIAL-1"}]
    assert response.retrieval_policy["trustedReevuSurfaceExpanded"] is False


@pytest.mark.asyncio
async def test_knowledge_graph_api_retrieval_candidates_shape(
    async_db_session: AsyncSession,
    test_user,
):
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_db_id="IR64",
        title="IR64",
    )
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="observation_variable",
        asset_db_id="CO:0000001",
        title="Drought tolerance",
    )
    current_user = _current_user(test_user)
    created = await create_knowledge_graph_edge(
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
            confidence=0.88,
        ),
        db=async_db_session,
        current_user=current_user,
    )

    response = await knowledge_graph_api.get_knowledge_graph_retrieval_candidates(
        source_asset_type="germplasm",
        source_asset_id=None,
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        limit=20,
        offset=0,
        candidate_edge_limit=20,
        db=async_db_session,
        current_user=current_user,
    )

    assert response.result_side == "source"
    assert response.candidate_direction == "outgoing"
    assert response.search_result_count == 1
    assert response.candidate_count == 1
    assert response.candidates[0].asset_type == "germplasm"
    assert response.candidates[0].asset_id == "IR64"
    assert response.candidates[0].matched_edges[0].id == created.id
    assert response.candidates[0].matched_evidence_refs == [{"entity_id": "trial:TRIAL-1"}]
    assert response.candidates[0].evidence_pack.edge_count == 1
    assert response.retrieval_policy["candidateUseOnly"] is True
    assert response.retrieval_policy["trustedReevuSurfaceExpanded"] is False


@pytest.mark.asyncio
async def test_knowledge_graph_api_retrieval_diagnostics_shape(
    async_db_session: AsyncSession,
    test_user,
):
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_db_id="IR64",
        title="IR64",
    )
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="observation_variable",
        asset_db_id="CO:0000001",
        title="Drought tolerance",
    )
    current_user = _current_user(test_user)
    created = await create_knowledge_graph_edge(
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
            confidence=0.88,
        ),
        db=async_db_session,
        current_user=current_user,
    )

    response = await knowledge_graph_api.get_knowledge_graph_retrieval_diagnostics(
        source_asset_type="germplasm",
        source_asset_id=None,
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        minimum_confidence=0.5,
        limit=20,
        offset=0,
        candidate_edge_limit=20,
        db=async_db_session,
        current_user=current_user,
    )

    assert response.candidates.candidate_count == 1
    assert response.total_matched_edges == 1
    assert response.total_matched_evidence_refs == 1
    assert response.relationship_type_counts == {"has_trait": 1}
    assert response.candidate_diagnostics[0].asset_id == "IR64"
    assert response.candidate_diagnostics[0].matched_edge_count == 1
    assert response.candidate_diagnostics[0].matched_edges_without_evidence_count == 0
    assert response.candidate_diagnostics[0].warnings == []
    assert response.candidates.candidates[0].matched_edges[0].id == created.id
    assert response.readiness["status"] == "ready_for_experimentation"
    assert response.retrieval_policy["diagnosticOnly"] is True
    assert response.retrieval_policy["trustedReevuSurfaceExpanded"] is False


@pytest.mark.asyncio
async def test_knowledge_graph_api_facets_shape(
    async_db_session: AsyncSession,
    test_user,
):
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_db_id="IR64",
        title="IR64",
    )
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="observation_variable",
        asset_db_id="CO:0000001",
        title="Drought tolerance",
    )
    current_user = _current_user(test_user)
    await create_knowledge_graph_edge(
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            derivation_method="manual_curated",
            confidence=0.88,
        ),
        db=async_db_session,
        current_user=current_user,
    )

    response = await knowledge_graph_api.get_knowledge_graph_facets(
        source_asset_type="germplasm",
        source_asset_id=None,
        target_asset_type="observation_variable",
        target_asset_id=None,
        relationship_type="has_trait",
        db=async_db_session,
        current_user=current_user,
    )

    assert response.total_edge_count == 1
    assert response.relationship_type == "has_trait"
    assert response.relationship_type_counts == {"has_trait": 1}
    assert response.source_asset_type_counts == {"germplasm": 1}
    assert response.target_asset_type_counts == {"observation_variable": 1}
    assert response.status_counts == {"active": 1}
    assert response.derivation_method_counts == {"manual_curated": 1}
    assert [pair.model_dump() for pair in response.asset_type_pair_counts] == [
        {
            "source_asset_type": "germplasm",
            "target_asset_type": "observation_variable",
            "count": 1,
        }
    ]
    assert response.retrieval_policy["facetOnly"] is True
    assert response.retrieval_policy["trustedReevuSurfaceExpanded"] is False


@pytest.mark.asyncio
async def test_knowledge_graph_api_ranked_candidates_shape(
    async_db_session: AsyncSession,
    test_user,
):
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_db_id="IR64",
        title="IR64",
    )
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="observation_variable",
        asset_db_id="CO:0000001",
        title="Drought tolerance",
    )
    current_user = _current_user(test_user)
    created = await create_knowledge_graph_edge(
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
            confidence=0.88,
        ),
        db=async_db_session,
        current_user=current_user,
    )

    response = await knowledge_graph_api.get_knowledge_graph_ranked_candidates(
        source_asset_type="germplasm",
        source_asset_id=None,
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        limit=20,
        offset=0,
        candidate_edge_limit=20,
        db=async_db_session,
        current_user=current_user,
    )

    assert response.candidates.candidate_count == 1
    assert response.ranked_candidates[0].rank == 1
    assert response.ranked_candidates[0].candidate.asset_id == "IR64"
    assert response.ranked_candidates[0].candidate.matched_edges[0].id == created.id
    assert response.ranked_candidates[0].retrieval_score > 0
    assert response.ranked_candidates[0].score_factors["average_confidence"] == 0.88
    assert response.retrieval_policy["deterministicScoring"] is True
    assert response.retrieval_policy["truthScore"] is False
    assert response.retrieval_policy["trustedReevuSurfaceExpanded"] is False


@pytest.mark.asyncio
async def test_knowledge_graph_api_reevu_dry_run_preview_shape(
    async_db_session: AsyncSession,
    test_user,
):
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_db_id="IR64",
        title="IR64",
    )
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="observation_variable",
        asset_db_id="CO:0000001",
        title="Drought tolerance",
    )
    current_user = _current_user(test_user)
    await create_knowledge_graph_edge(
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
            confidence=0.88,
        ),
        db=async_db_session,
        current_user=current_user,
    )

    response = await knowledge_graph_api.get_knowledge_graph_reevu_dry_run_preview(
        prompt="Which drought tolerant rice candidates should I inspect?",
        source_asset_type="germplasm",
        source_asset_id=None,
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        minimum_confidence=0.5,
        limit=20,
        offset=0,
        candidate_edge_limit=20,
        db=async_db_session,
        current_user=current_user,
    )

    assert response.prompt == "Which drought tolerant rice candidates should I inspect?"
    assert response.ranked_candidates.ranked_candidates[0].candidate.asset_id == "IR64"
    assert response.diagnostics.total_matched_edges == 1
    assert response.preview_summary["candidateCount"] == 1
    assert response.preview_summary["readinessStatus"] == "ready_for_experimentation"
    assert response.authority_boundary["dryRunOnly"] is True
    assert response.authority_boundary["answerGenerated"] is False
    assert response.authority_boundary["reevuRuntimeInvoked"] is False
    assert response.authority_boundary["trustedSurfaceExpanded"] is False
    assert response.retrieval_policy["dryRunOnly"] is True
    assert response.retrieval_policy["trustedReevuSurfaceExpanded"] is False


@pytest.mark.asyncio
async def test_knowledge_graph_api_explorer_snapshot_shape(
    async_db_session: AsyncSession,
    test_user,
):
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_db_id="IR64",
        title="IR64",
    )
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="observation_variable",
        asset_db_id="CO:0000001",
        title="Drought tolerance",
    )
    current_user = _current_user(test_user)
    await create_knowledge_graph_edge(
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
            confidence=0.88,
        ),
        db=async_db_session,
        current_user=current_user,
    )

    response = await knowledge_graph_api.get_knowledge_graph_explorer_snapshot(
        source_asset_type="germplasm",
        source_asset_id=None,
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
        minimum_confidence=0.5,
        limit=20,
        offset=0,
        candidate_edge_limit=20,
        db=async_db_session,
        current_user=current_user,
    )

    assert response.facets.total_edge_count == 1
    assert response.ranked_candidates.ranked_candidates[0].candidate.asset_id == "IR64"
    assert response.diagnostics.total_matched_edges == 1
    assert response.snapshot_summary == {
        "totalEdgeCount": 1,
        "candidateCount": 1,
        "rankedCandidateCount": 1,
        "matchedEdgeCount": 1,
        "matchedEvidenceRefCount": 1,
        "readinessStatus": "ready_for_experimentation",
        "relationshipTypeCount": 1,
        "sourceAssetTypeCount": 1,
        "targetAssetTypeCount": 1,
        "assetTypePairCount": 1,
    }
    assert response.retrieval_policy["explorerOnly"] is True
    assert response.retrieval_policy["answerGenerated"] is False
    assert response.retrieval_policy["reevuRuntimeInvoked"] is False
    assert response.retrieval_policy["trustedReevuSurfaceExpanded"] is False

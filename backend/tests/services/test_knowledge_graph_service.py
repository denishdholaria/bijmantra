import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Organization
from app.models.fair_metadata import FairAssetMetadata
from app.models.knowledge_graph import AgriculturalKnowledgeGraphEdge
from app.schemas.knowledge_graph import KnowledgeGraphEdgeCreate
from app.services.knowledge_graph_service import (
    GraphAssetNotFound,
    KnowledgeGraphService,
    UnsupportedGraphRelationshipType,
)


@pytest.fixture(autouse=True)
async def create_knowledge_graph_tables(async_db_session: AsyncSession):
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
) -> FairAssetMetadata:
    metadata = FairAssetMetadata(
        organization_id=organization_id,
        asset_type=asset_type,
        asset_db_id=asset_db_id,
        persistent_identifier=f"bijmantra:{asset_type}:{asset_db_id}",
        title=title,
        schema_version="fair_asset_metadata.v1",
    )
    db.add(metadata)
    await db.flush()
    return metadata


@pytest.mark.asyncio
async def test_graph_edge_create_requires_fair_assets_and_persists_evidence(
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
    service = KnowledgeGraphService()

    edge = await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[
                {
                    "source_type": "database",
                    "entity_id": "trial:TRIAL-1",
                    "query_or_method": "manual_review",
                }
            ],
            provenance={"curated_by": "operator"},
            confidence=0.86,
            derivation_method="operator_curated",
        ),
    )

    assert edge.organization_id == test_user.organization_id
    assert edge.edge_id.startswith("kg-edge-")
    assert edge.source_asset_type == "germplasm"
    assert edge.relationship_type == "has_trait"
    assert edge.target_asset_id == "CO:0000001"
    assert edge.evidence_refs[0]["entity_id"] == "trial:TRIAL-1"
    assert edge.provenance == {"curated_by": "operator"}
    assert edge.confidence == 0.86
    assert edge.derivation_method == "operator_curated"


@pytest.mark.asyncio
async def test_graph_edge_upsert_is_idempotent_and_filterable(
    async_db_session: AsyncSession,
    test_user,
):
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="trial",
        asset_db_id="TRIAL-1",
        title="Drought nursery",
    )
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_db_id="IR64",
        title="IR64",
    )
    service = KnowledgeGraphService()
    payload = KnowledgeGraphEdgeCreate(
        source_asset_type="germplasm",
        source_asset_id="IR64",
        relationship_type="evaluated_in",
        target_asset_type="trial",
        target_asset_id="TRIAL-1",
        confidence=0.7,
    )

    first = await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=payload,
    )
    second = await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=payload.model_copy(update={"confidence": 0.91}),
    )
    edges = await service.list_edges(
        async_db_session,
        organization_id=test_user.organization_id,
        source_asset_type="germplasm",
        source_asset_id="IR64",
        relationship_type="evaluated_in",
    )

    assert second.id == first.id
    assert second.confidence == 0.91
    assert [edge.id for edge in edges] == [first.id]


@pytest.mark.asyncio
async def test_graph_neighborhood_returns_one_hop_edges_by_direction(
    async_db_session: AsyncSession,
    test_user,
):
    for asset_type, asset_db_id, title in (
        ("germplasm", "IR64", "IR64"),
        ("observation_variable", "CO:0000001", "Drought tolerance"),
        ("trial", "TRIAL-1", "Drought nursery"),
    ):
        await _fair_asset(
            async_db_session,
            organization_id=test_user.organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            title=title,
        )
    service = KnowledgeGraphService()
    outgoing = await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            confidence=0.88,
        ),
    )
    incoming = await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="trial",
            source_asset_id="TRIAL-1",
            relationship_type="has_evidence",
            target_asset_type="germplasm",
            target_asset_id="IR64",
            evidence_refs=[{"entity_id": "observation:OBS-1"}],
        ),
    )

    neighborhood = await service.get_neighborhood(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_id="IR64",
        direction="both",
    )

    assert neighborhood.asset_type == "germplasm"
    assert neighborhood.asset_id == "IR64"
    assert neighborhood.direction == "both"
    assert neighborhood.edge_count == 2
    assert [edge.id for edge in neighborhood.outgoing_edges] == [outgoing.id]
    assert [edge.id for edge in neighborhood.incoming_edges] == [incoming.id]

    incoming_only = await service.get_neighborhood(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_id="IR64",
        direction="incoming",
        relationship_type="has_evidence",
    )
    assert incoming_only.edge_count == 1
    assert incoming_only.outgoing_edges == []
    assert incoming_only.incoming_edges[0].evidence_refs == [{"entity_id": "observation:OBS-1"}]


@pytest.mark.asyncio
async def test_graph_evidence_pack_deduplicates_refs_and_marks_policy(
    async_db_session: AsyncSession,
    test_user,
):
    for asset_type, asset_db_id, title in (
        ("germplasm", "IR64", "IR64"),
        ("observation_variable", "CO:0000001", "Drought tolerance"),
        ("trial", "TRIAL-1", "Drought nursery"),
    ):
        await _fair_asset(
            async_db_session,
            organization_id=test_user.organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            title=title,
        )
    service = KnowledgeGraphService()
    shared_ref = {"entity_id": "observation:OBS-1", "source_type": "database"}
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[shared_ref],
            confidence=0.88,
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="trial",
            source_asset_id="TRIAL-1",
            relationship_type="has_evidence",
            target_asset_type="germplasm",
            target_asset_id="IR64",
            evidence_refs=[shared_ref, {"entity_id": "trial:TRIAL-1"}],
        ),
    )

    pack = await service.build_evidence_pack(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_id="IR64",
        direction="both",
    )

    assert pack.asset_type == "germplasm"
    assert pack.asset_id == "IR64"
    assert pack.asset_title == "IR64"
    assert pack.persistent_identifier == "bijmantra:germplasm:IR64"
    assert pack.edge_count == 2
    assert pack.relationship_types == ["has_evidence", "has_trait"]
    assert pack.evidence_refs == [shared_ref, {"entity_id": "trial:TRIAL-1"}]
    assert pack.retrieval_policy == {
        "graphDepth": 1,
        "rawDataImported": False,
        "trustedReevuSurfaceExpanded": False,
    }


@pytest.mark.asyncio
async def test_graph_evidence_search_projects_fair_assets_and_stays_tenant_scoped(
    async_db_session: AsyncSession,
    test_user,
):
    for asset_type, asset_db_id, title in (
        ("germplasm", "IR64", "IR64"),
        ("germplasm", "SAHBHAGI-DHAN", "Sahbhagi Dhan"),
        ("observation_variable", "CO:0000001", "Drought tolerance"),
        ("observation_variable", "CO:0000002", "Blast resistance"),
    ):
        await _fair_asset(
            async_db_session,
            organization_id=test_user.organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            title=title,
        )
    other = Organization(name="Graph Search Other Org")
    async_db_session.add(other)
    await async_db_session.flush()
    for asset_type, asset_db_id, title in (
        ("germplasm", "FOREIGN-RICE", "Foreign Rice"),
        ("observation_variable", "CO:0000001", "Drought tolerance"),
    ):
        await _fair_asset(
            async_db_session,
            organization_id=other.id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            title=title,
        )

    service = KnowledgeGraphService()
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "observation:OBS-IR64"}],
            confidence=0.88,
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="SAHBHAGI-DHAN",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "observation:OBS-SD"}],
            confidence=0.91,
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000002",
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=other.id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="FOREIGN-RICE",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
        ),
    )

    source_results = await service.search_evidence(
        async_db_session,
        organization_id=test_user.organization_id,
        source_asset_type="germplasm",
        relationship_type="has_trait",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        result_side="source",
    )

    assert source_results.result_side == "source"
    assert source_results.result_count == 2
    assert {result.asset_id for result in source_results.results} == {"IR64", "SAHBHAGI-DHAN"}
    assert {result.asset_title for result in source_results.results} == {"IR64", "Sahbhagi Dhan"}
    assert all(
        result.persistent_identifier.startswith("bijmantra:germplasm:")
        for result in source_results.results
    )
    assert all(
        result.matched_edge.target_asset_id == "CO:0000001"
        for result in source_results.results
    )
    assert all(result.evidence_refs for result in source_results.results)
    assert source_results.retrieval_policy == {
        "graphDepth": 1,
        "searchMode": "edge_filter",
        "rawDataImported": False,
        "trustedReevuSurfaceExpanded": False,
    }

    target_results = await service.search_evidence(
        async_db_session,
        organization_id=test_user.organization_id,
        source_asset_type="germplasm",
        source_asset_id="IR64",
        relationship_type="has_trait",
        result_side="target",
    )

    assert target_results.result_side == "target"
    assert target_results.result_count == 2
    assert {result.asset_id for result in target_results.results} == {
        "CO:0000001",
        "CO:0000002",
    }


@pytest.mark.asyncio
async def test_graph_retrieval_candidates_group_matches_and_attach_evidence_packs(
    async_db_session: AsyncSession,
    test_user,
):
    for asset_type, asset_db_id, title in (
        ("germplasm", "IR64", "IR64"),
        ("germplasm", "SAHBHAGI-DHAN", "Sahbhagi Dhan"),
        ("observation_variable", "CO:0000001", "Drought tolerance"),
        ("trial", "TRIAL-1", "Drought nursery"),
    ):
        await _fair_asset(
            async_db_session,
            organization_id=test_user.organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            title=title,
        )
    service = KnowledgeGraphService()
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "observation:OBS-IR64"}],
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="resistant_to",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="evaluated_in",
            target_asset_type="trial",
            target_asset_id="TRIAL-1",
            evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="SAHBHAGI-DHAN",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "observation:OBS-SD"}],
        ),
    )

    candidates = await service.build_retrieval_candidates(
        async_db_session,
        organization_id=test_user.organization_id,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        result_side="source",
        candidate_direction="outgoing",
    )

    assert candidates.result_side == "source"
    assert candidates.candidate_direction == "outgoing"
    assert candidates.search_result_count == 3
    assert candidates.candidate_count == 2
    assert candidates.retrieval_policy == {
        "graphDepth": 1,
        "searchMode": "edge_filter",
        "candidateUseOnly": True,
        "rawDataImported": False,
        "trustedReevuSurfaceExpanded": False,
    }

    by_asset_id = {candidate.asset_id: candidate for candidate in candidates.candidates}
    ir64 = by_asset_id["IR64"]
    assert ir64.asset_title == "IR64"
    assert ir64.persistent_identifier == "bijmantra:germplasm:IR64"
    assert ir64.match_count == 2
    assert {edge.relationship_type for edge in ir64.matched_edges} == {
        "has_trait",
        "resistant_to",
    }
    assert ir64.matched_evidence_refs == [
        {"entity_id": "trial:TRIAL-1"},
        {"entity_id": "observation:OBS-IR64"},
    ]
    assert ir64.evidence_pack.edge_count == 3
    assert set(ir64.evidence_pack.relationship_types) == {
        "evaluated_in",
        "has_trait",
        "resistant_to",
    }

    assert by_asset_id["SAHBHAGI-DHAN"].match_count == 1


@pytest.mark.asyncio
async def test_graph_retrieval_diagnostics_summarize_candidate_quality(
    async_db_session: AsyncSession,
    test_user,
):
    for asset_type, asset_db_id, title in (
        ("germplasm", "IR64", "IR64"),
        ("germplasm", "SAHBHAGI-DHAN", "Sahbhagi Dhan"),
        ("observation_variable", "CO:0000001", "Drought tolerance"),
    ):
        await _fair_asset(
            async_db_session,
            organization_id=test_user.organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            title=title,
        )
    service = KnowledgeGraphService()
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "observation:OBS-IR64"}],
            confidence=0.92,
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="resistant_to",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            confidence=0.4,
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="SAHBHAGI-DHAN",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
        ),
    )

    diagnostics = await service.build_retrieval_diagnostics(
        async_db_session,
        organization_id=test_user.organization_id,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        result_side="source",
        candidate_direction="outgoing",
        minimum_confidence=0.5,
    )

    assert diagnostics.candidates.candidate_count == 2
    assert diagnostics.total_matched_edges == 3
    assert diagnostics.total_matched_evidence_refs == 1
    assert diagnostics.matched_edges_without_evidence_count == 2
    assert diagnostics.low_confidence_edge_count == 1
    assert diagnostics.missing_confidence_edge_count == 1
    assert diagnostics.relationship_type_counts == {
        "has_trait": 2,
        "resistant_to": 1,
    }
    assert diagnostics.readiness == {
        "status": "needs_review",
        "reasons": [
            "matched_edge_missing_evidence",
            "low_confidence_edges",
            "missing_confidence_edges",
        ],
    }
    by_asset_id = {candidate.asset_id: candidate for candidate in diagnostics.candidate_diagnostics}
    assert by_asset_id["IR64"].warnings == [
        "matched_edge_missing_evidence",
        "low_confidence_edges",
    ]
    assert by_asset_id["SAHBHAGI-DHAN"].warnings == [
        "matched_edge_missing_evidence",
        "missing_confidence_edges",
    ]
    assert diagnostics.retrieval_policy == {
        "graphDepth": 1,
        "searchMode": "edge_filter",
        "candidateUseOnly": True,
        "diagnosticOnly": True,
        "rawDataImported": False,
        "trustedReevuSurfaceExpanded": False,
    }


@pytest.mark.asyncio
async def test_graph_facets_count_filtered_edges_and_remain_tenant_scoped(
    async_db_session: AsyncSession,
    test_user,
):
    for asset_type, asset_db_id, title in (
        ("germplasm", "IR64", "IR64"),
        ("germplasm", "SAHBHAGI-DHAN", "Sahbhagi Dhan"),
        ("observation_variable", "CO:0000001", "Drought tolerance"),
        ("trial", "TRIAL-1", "Drought nursery"),
    ):
        await _fair_asset(
            async_db_session,
            organization_id=test_user.organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            title=title,
        )
    other = Organization(name="Graph Facet Other Org")
    async_db_session.add(other)
    await async_db_session.flush()
    for asset_type, asset_db_id, title in (
        ("germplasm", "FOREIGN-RICE", "Foreign Rice"),
        ("observation_variable", "CO:0000001", "Drought tolerance"),
    ):
        await _fair_asset(
            async_db_session,
            organization_id=other.id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            title=title,
        )

    service = KnowledgeGraphService()
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            derivation_method="manual_curated",
            confidence=0.92,
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="SAHBHAGI-DHAN",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            derivation_method="manual_curated",
            confidence=0.88,
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="evaluated_in",
            target_asset_type="trial",
            target_asset_id="TRIAL-1",
            derivation_method="trial_import",
            confidence=0.81,
            status="inactive",
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=other.id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="FOREIGN-RICE",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
        ),
    )

    facets = await service.get_facets(
        async_db_session,
        organization_id=test_user.organization_id,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
    )

    assert facets.total_edge_count == 2
    assert facets.source_asset_type == "germplasm"
    assert facets.target_asset_type == "observation_variable"
    assert facets.relationship_type_counts == {"has_trait": 2}
    assert facets.source_asset_type_counts == {"germplasm": 2}
    assert facets.target_asset_type_counts == {"observation_variable": 2}
    assert facets.status_counts == {"active": 2}
    assert facets.derivation_method_counts == {"manual_curated": 2}
    assert [pair.model_dump() for pair in facets.asset_type_pair_counts] == [
        {
            "source_asset_type": "germplasm",
            "target_asset_type": "observation_variable",
            "count": 2,
        }
    ]
    assert facets.retrieval_policy == {
        "graphDepth": 1,
        "facetOnly": True,
        "rawDataImported": False,
        "trustedReevuSurfaceExpanded": False,
    }


@pytest.mark.asyncio
async def test_graph_ranked_candidates_order_by_visible_score_factors(
    async_db_session: AsyncSession,
    test_user,
):
    for asset_type, asset_db_id, title in (
        ("germplasm", "IR64", "IR64"),
        ("germplasm", "SAHBHAGI-DHAN", "Sahbhagi Dhan"),
        ("observation_variable", "CO:0000001", "Drought tolerance"),
        ("trial", "TRIAL-1", "Drought nursery"),
    ):
        await _fair_asset(
            async_db_session,
            organization_id=test_user.organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            title=title,
        )
    service = KnowledgeGraphService()
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "observation:OBS-IR64"}],
            confidence=0.9,
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="evaluated_in",
            target_asset_type="trial",
            target_asset_id="TRIAL-1",
            evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
            confidence=0.8,
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="SAHBHAGI-DHAN",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            confidence=0.4,
        ),
    )

    ranked = await service.rank_retrieval_candidates(
        async_db_session,
        organization_id=test_user.organization_id,
        source_asset_type="germplasm",
        result_side="source",
        candidate_direction="outgoing",
    )

    assert ranked.candidates.candidate_count == 2
    assert [entry.rank for entry in ranked.ranked_candidates] == [1, 2]
    assert [entry.candidate.asset_id for entry in ranked.ranked_candidates] == [
        "IR64",
        "SAHBHAGI-DHAN",
    ]
    assert ranked.ranked_candidates[0].retrieval_score > ranked.ranked_candidates[1].retrieval_score
    assert ranked.ranked_candidates[0].score_factors == {
        "match_count": 0.667,
        "average_confidence": 0.85,
        "evidence_refs": 0.667,
        "evidence_pack_edges": 0.4,
    }
    assert ranked.ranked_candidates[1].score_factors == {
        "match_count": 0.333,
        "average_confidence": 0.4,
        "evidence_refs": 0.0,
        "evidence_pack_edges": 0.2,
    }
    assert ranked.retrieval_policy == {
        "graphDepth": 1,
        "searchMode": "edge_filter",
        "candidateUseOnly": True,
        "deterministicScoring": True,
        "truthScore": False,
        "modelGenerated": False,
        "rawDataImported": False,
        "trustedReevuSurfaceExpanded": False,
    }


@pytest.mark.asyncio
async def test_graph_reevu_dry_run_preview_keeps_authority_boundary_explicit(
    async_db_session: AsyncSession,
    test_user,
):
    for asset_type, asset_db_id, title in (
        ("germplasm", "IR64", "IR64"),
        ("observation_variable", "CO:0000001", "Drought tolerance"),
    ):
        await _fair_asset(
            async_db_session,
            organization_id=test_user.organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            title=title,
        )
    service = KnowledgeGraphService()
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "observation:OBS-IR64"}],
            confidence=0.9,
        ),
    )

    preview = await service.build_reevu_dry_run_preview(
        async_db_session,
        organization_id=test_user.organization_id,
        prompt="Which drought tolerant rice candidates should I inspect?",
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
    )

    assert preview.prompt == "Which drought tolerant rice candidates should I inspect?"
    assert preview.ranked_candidates.ranked_candidates[0].candidate.asset_id == "IR64"
    assert preview.diagnostics.readiness["status"] == "ready_for_experimentation"
    assert preview.preview_summary == {
        "candidateCount": 1,
        "rankedCandidateCount": 1,
        "matchedEdgeCount": 1,
        "matchedEvidenceRefCount": 1,
        "readinessStatus": "ready_for_experimentation",
    }
    assert preview.authority_boundary == {
        "dryRunOnly": True,
        "answerGenerated": False,
        "reevuRuntimeInvoked": False,
        "trustedSurfaceExpanded": False,
        "benchmarkAuthorityChanged": False,
    }
    assert preview.retrieval_policy == {
        "graphDepth": 1,
        "searchMode": "edge_filter",
        "candidateUseOnly": True,
        "dryRunOnly": True,
        "answerGenerated": False,
        "trustedReevuSurfaceExpanded": False,
    }


@pytest.mark.asyncio
async def test_graph_explorer_snapshot_packages_ui_ready_graph_context(
    async_db_session: AsyncSession,
    test_user,
):
    for asset_type, asset_db_id, title in (
        ("germplasm", "IR64", "IR64"),
        ("germplasm", "SAHBHAGI-DHAN", "Sahbhagi Dhan"),
        ("observation_variable", "CO:0000001", "Drought tolerance"),
        ("trial", "TRIAL-1", "Drought nursery"),
    ):
        await _fair_asset(
            async_db_session,
            organization_id=test_user.organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            title=title,
        )
    service = KnowledgeGraphService()
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "observation:OBS-IR64"}],
            confidence=0.9,
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="SAHBHAGI-DHAN",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "observation:OBS-SD"}],
            confidence=0.86,
        ),
    )
    await service.upsert_edge(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="evaluated_in",
            target_asset_type="trial",
            target_asset_id="TRIAL-1",
            evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
            confidence=0.8,
        ),
    )

    snapshot = await service.build_explorer_snapshot(
        async_db_session,
        organization_id=test_user.organization_id,
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        relationship_type="has_trait",
        result_side="source",
        candidate_direction="outgoing",
    )

    assert snapshot.facets.total_edge_count == 2
    assert snapshot.facets.relationship_type_counts == {"has_trait": 2}
    assert snapshot.ranked_candidates.candidates.candidate_count == 2
    assert [entry.candidate.asset_id for entry in snapshot.ranked_candidates.ranked_candidates] == [
        "IR64",
        "SAHBHAGI-DHAN",
    ]
    assert snapshot.diagnostics.total_matched_edges == 2
    assert snapshot.diagnostics.total_matched_evidence_refs == 2
    assert snapshot.diagnostics.readiness["status"] == "ready_for_experimentation"
    assert snapshot.snapshot_summary == {
        "totalEdgeCount": 2,
        "candidateCount": 2,
        "rankedCandidateCount": 2,
        "matchedEdgeCount": 2,
        "matchedEvidenceRefCount": 2,
        "readinessStatus": "ready_for_experimentation",
        "relationshipTypeCount": 1,
        "sourceAssetTypeCount": 1,
        "targetAssetTypeCount": 1,
        "assetTypePairCount": 1,
    }
    assert snapshot.retrieval_policy == {
        "graphDepth": 1,
        "searchMode": "edge_filter",
        "explorerOnly": True,
        "answerGenerated": False,
        "reevuRuntimeInvoked": False,
        "rawDataImported": False,
        "trustedReevuSurfaceExpanded": False,
    }


@pytest.mark.asyncio
async def test_graph_edge_rejects_cross_tenant_or_unsupported_edges(
    async_db_session: AsyncSession,
    test_user,
):
    other = Organization(name="Graph Other Org")
    async_db_session.add(other)
    await async_db_session.flush()
    await _fair_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_db_id="IR64",
        title="IR64",
    )
    await _fair_asset(
        async_db_session,
        organization_id=other.id,
        asset_type="trial",
        asset_db_id="TRIAL-FOREIGN",
        title="Foreign trial",
    )
    service = KnowledgeGraphService()

    with pytest.raises(GraphAssetNotFound):
        await service.upsert_edge(
            async_db_session,
            organization_id=test_user.organization_id,
            payload=KnowledgeGraphEdgeCreate(
                source_asset_type="germplasm",
                source_asset_id="IR64",
                relationship_type="evaluated_in",
                target_asset_type="trial",
                target_asset_id="TRIAL-FOREIGN",
            ),
        )

    with pytest.raises(UnsupportedGraphRelationshipType):
        await service.upsert_edge(
            async_db_session,
            organization_id=test_user.organization_id,
            payload=KnowledgeGraphEdgeCreate(
                source_asset_type="germplasm",
                source_asset_id="IR64",
                relationship_type="sort_of_related_to",
                target_asset_type="germplasm",
                target_asset_id="IR64",
            ),
        )

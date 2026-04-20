import pytest

from app.modules.ai.services import (
    ProjectBrainMemoryService,
    ProjectBrainScope,
    ProjectBrainSourceSurface,
    ProjectBrainTrustRank,
    VolatileProjectBrainMemoryRepository,
)


@pytest.mark.asyncio
async def test_project_brain_memory_bootstrap_supports_recall_and_provenance():
    service = ProjectBrainMemoryService(VolatileProjectBrainMemoryRepository())

    charter_source = await service.register_source_artifact(
        source_path=".beingbijmantra/2026-04-03-being-bijmantra-surface-charter.md",
        source_surface=ProjectBrainSourceSurface.BEING,
        source_kind="charter",
        authority_class="constitutional",
        source_artifact_id="source-charter",
    )
    surreal_source = await service.register_source_artifact(
        source_path=".ai/decisions/ADR-010-surrealdb-orchestration-memory-candidate.md",
        source_surface=ProjectBrainSourceSurface.AI,
        source_kind="decision",
        authority_class="accepted_adr",
        source_artifact_id="source-adr010",
    )

    projection = await service.project_from_source(
        source_id=charter_source.id,
        projection_type="summary",
        summary="Defines the project-brain boundary and its relationship to REEVU.",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.GLOBAL_PROJECT,
        projection_id="projection-charter-summary",
    )
    project_brain = await service.upsert_memory_node(
        node_type="concept",
        title="Project Brain",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.GLOBAL_PROJECT,
        source_ids=(charter_source.id,),
        node_id="node-project-brain",
    )
    sidecar = await service.upsert_memory_node(
        node_type="runtime_candidate",
        title="SurrealDB Sidecar",
        trust_rank=ProjectBrainTrustRank.RANK_B,
        scope=ProjectBrainScope.WORKSTREAM,
        source_ids=(surreal_source.id,),
        node_id="node-surrealdb-sidecar",
    )
    edge = await service.link_memory_objects(
        from_node_id=project_brain.id,
        to_node_id=sidecar.id,
        relation_type="candidate_runtime",
        source_id=surreal_source.id,
        confidence=1.0,
        edge_id="edge-project-brain-surrealdb",
    )

    recall = await service.recall(
        "surreal",
        trust_ranks=(ProjectBrainTrustRank.RANK_A, ProjectBrainTrustRank.RANK_B),
    )
    provenance = await service.get_provenance_trail(sidecar.id)
    related = await service.list_related(project_brain.id)

    assert projection.source_id == charter_source.id
    assert [item.id for item in recall.source_artifacts] == [surreal_source.id]
    assert [item.id for item in recall.nodes] == [sidecar.id]
    assert [item.id for item in recall.edges] == [edge.id]
    assert [item.id for item in provenance.source_artifacts] == [surreal_source.id]
    assert [item.id for item in provenance.related_edges] == [edge.id]
    assert [item.id for item in related] == [edge.id]


@pytest.mark.asyncio
async def test_project_from_source_rejects_unknown_source_artifact():
    service = ProjectBrainMemoryService(VolatileProjectBrainMemoryRepository())

    with pytest.raises(ValueError, match="Unknown source artifact"):
        await service.project_from_source(
            source_id="source-missing",
            projection_type="summary",
            summary="Should fail",
            trust_rank=ProjectBrainTrustRank.RANK_A,
            scope=ProjectBrainScope.GLOBAL_PROJECT,
        )


@pytest.mark.asyncio
async def test_link_memory_objects_rejects_unknown_node_and_invalid_confidence():
    service = ProjectBrainMemoryService(VolatileProjectBrainMemoryRepository())
    source = await service.register_source_artifact(
        source_path=".beingbijmantra/2026-04-04-being-bijmantra-project-brain-memory-contract.md",
        source_surface=ProjectBrainSourceSurface.BEING,
        source_kind="memory_contract",
        authority_class="constitutional",
    )
    node = await service.upsert_memory_node(
        node_type="concept",
        title="Authority Boundary",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.GLOBAL_PROJECT,
        source_ids=(source.id,),
    )

    with pytest.raises(ValueError, match="Unknown to_node_id"):
        await service.link_memory_objects(
            from_node_id=node.id,
            to_node_id="node-missing",
            relation_type="constrains",
        )

    with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
        await service.link_memory_objects(
            from_node_id=node.id,
            to_node_id=node.id,
            relation_type="self_test",
            confidence=1.5,
        )


@pytest.mark.asyncio
async def test_mark_invalid_and_forget_session_scope():
    service = ProjectBrainMemoryService(VolatileProjectBrainMemoryRepository())
    source = await service.register_source_artifact(
        source_path=".ai/tasks/2026-04-04-project-brain-contract-inventory-and-adapter-plan.md",
        source_surface=ProjectBrainSourceSurface.AI,
        source_kind="planning_task",
        authority_class="operational",
        source_artifact_id="source-plan",
    )
    projection = await service.project_from_source(
        source_id=source.id,
        projection_type="summary",
        summary="Temporary planning context",
        trust_rank=ProjectBrainTrustRank.RANK_E,
        scope=ProjectBrainScope.SESSION,
        projection_id="projection-session",
    )
    node = await service.upsert_memory_node(
        node_type="draft_context",
        title="Temporary Session Cluster",
        trust_rank=ProjectBrainTrustRank.RANK_E,
        scope=ProjectBrainScope.SESSION,
        source_ids=(source.id,),
        node_id="node-session",
    )

    correction = await service.mark_invalid(
        target_kind="projection",
        target_id=projection.id,
        reason="Session context expired",
    )
    removals = await service.forget_scope(ProjectBrainScope.SESSION)
    recall = await service.recall("temporary", scopes=(ProjectBrainScope.SESSION,))

    assert correction.target_id == projection.id
    assert removals == {"projections_removed": 1, "nodes_removed": 1, "edges_removed": 0}
    assert recall.projections == tuple()
    assert recall.nodes == tuple()



@pytest.mark.asyncio
async def test_recall_respects_trust_rank_and_scope_filters():
    service = ProjectBrainMemoryService(VolatileProjectBrainMemoryRepository())
    source = await service.register_source_artifact(
        source_path="backend/test_reports/reevu_authority_gap_report.json",
        source_surface=ProjectBrainSourceSurface.RUNTIME_EVIDENCE,
        source_kind="evidence_report",
        authority_class="verified_runtime_evidence",
    )
    await service.upsert_memory_node(
        node_type="evidence",
        title="Authority Gap Report",
        trust_rank=ProjectBrainTrustRank.RANK_B,
        scope=ProjectBrainScope.SURFACE,
        source_ids=(source.id,),
        node_id="node-authority-gap",
    )
    await service.upsert_memory_node(
        node_type="derived_hint",
        title="Authority Gap Suggestion",
        trust_rank=ProjectBrainTrustRank.RANK_D,
        scope=ProjectBrainScope.SESSION,
        source_ids=(source.id,),
        node_id="node-authority-gap-suggestion",
    )

    recall = await service.recall(
        "authority gap",
        trust_ranks=(ProjectBrainTrustRank.RANK_B,),
        scopes=(ProjectBrainScope.SURFACE,),
    )

    assert [item.id for item in recall.nodes] == ["node-authority-gap"]

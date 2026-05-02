from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.core.tracing import TRACE_ID_HEADER, trace_context
from app.modules.ai.services import (
    ProjectBrainMemoryService,
    ProjectBrainScope,
    ProjectBrainSourceSurface,
    ProjectBrainTrustRank,
)
from app.modules.ai.services.project_brain_bootstrap import (
    FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS,
    ProjectBrainBootstrapIngestionService,
)
from app.modules.ai.services.project_brain_memory_surreal import (
    ProjectBrainSurrealConnectionConfig,
    SurrealProjectBrainMemoryRepository,
)
from tests.units.services.project_brain_surreal_testkit import (
    MockSurrealHttpServer,
    project_brain_surreal_test_config,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_project_brain_surreal_default_endpoint_uses_dedicated_sidecar_port():
    assert ProjectBrainSurrealConnectionConfig().base_url == "http://127.0.0.1:8083"


@pytest.mark.asyncio
async def test_surreal_repository_supports_project_brain_round_trip_and_provenance():
    config = project_brain_surreal_test_config()
    server = MockSurrealHttpServer(namespace=config.namespace, database=config.database)
    repository = SurrealProjectBrainMemoryRepository(config, transport=httpx.MockTransport(server))
    service = ProjectBrainMemoryService(repository)

    try:
        with trace_context("surreal-trace-12345678"):
            assert await repository.check_health() is True

            charter_source = await service.register_source_artifact(
                source_path=".beingbijmantra/2026-04-03-being-bijmantra-surface-charter.md",
                source_surface=ProjectBrainSourceSurface.BEING,
                source_kind="charter",
                authority_class="constitutional",
                source_artifact_id="source-charter",
            )
            surreal_source = await service.register_source_artifact(
                source_path=".beingbijmantra/2026-04-04-being-bijmantra-surrealdb-sidecar-direction.md",
                source_surface=ProjectBrainSourceSurface.BEING,
                source_kind="surrealdb_sidecar_direction",
                authority_class="constitutional",
                source_artifact_id="source-sidecar-direction",
            )

            await service.project_from_source(
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
                title="Being Bijmantra SurrealDB Sidecar",
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

            recall = await service.recall("surrealdb")
            provenance = await service.get_provenance_trail(sidecar.id)

        assert [item.id for item in recall.source_artifacts] == [surreal_source.id]
        assert [item.id for item in recall.nodes] == [sidecar.id]
        assert [item.id for item in recall.edges] == [edge.id]
        assert [item.id for item in provenance.source_artifacts] == [surreal_source.id]
        assert any(request.headers.get("Authorization", "").startswith("Basic ") for request in server.requests)
        assert all(request.headers.get("Surreal-NS") == config.namespace for request in server.requests)
        assert all(request.headers.get("Surreal-DB") == config.database for request in server.requests)
        assert all(request.headers.get(TRACE_ID_HEADER) == "surreal-trace-12345678" for request in server.requests)
    finally:
        await repository.aclose()


@pytest.mark.asyncio
async def test_surreal_repository_supports_first_wave_bootstrap_round_trip():
    config = project_brain_surreal_test_config()
    server = MockSurrealHttpServer(namespace=config.namespace, database=config.database)
    repository = SurrealProjectBrainMemoryRepository(config, transport=httpx.MockTransport(server))
    service = ProjectBrainMemoryService(repository)
    bootstrap = ProjectBrainBootstrapIngestionService(service)

    try:
        report = await bootstrap.bootstrap_first_wave(_repo_root())
        recall = await service.recall("beingbijmantra_surrealdb")

        assert report.missing_paths == tuple()
        assert report.source_count == len(FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS)
        assert report.projection_count == len(FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS)
        assert report.node_count == len(FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS)
        assert any(
            artifact.source_path == ".beingbijmantra/2026-04-04-being-bijmantra-surrealdb-sidecar-direction.md"
            for artifact in recall.source_artifacts
        )
        assert len(server.tables[config.source_artifact_table]) == len(FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS)
    finally:
        await repository.aclose()

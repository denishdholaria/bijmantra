from pathlib import Path

import httpx
import pytest

from app.modules.ai.services import ProjectBrainMemoryService
from app.modules.ai.services.project_brain_bootstrap import ProjectBrainBootstrapIngestionService
from app.modules.ai.services.project_brain_query import ProjectBrainQueryService
from app.modules.ai.services.project_brain_memory_surreal import SurrealProjectBrainMemoryRepository
from tests.units.services.project_brain_surreal_testkit import (
    MockSurrealHttpServer,
    project_brain_surreal_test_config,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


@pytest.mark.asyncio
async def test_surreal_query_service_returns_sidecar_recall_and_provenance():
    config = project_brain_surreal_test_config()
    server = MockSurrealHttpServer(namespace=config.namespace, database=config.database)
    repository = SurrealProjectBrainMemoryRepository(config, transport=httpx.MockTransport(server))
    memory_service = ProjectBrainMemoryService(repository)
    bootstrap = ProjectBrainBootstrapIngestionService(memory_service)
    query_service = ProjectBrainQueryService(memory_service)

    try:
        report = await bootstrap.bootstrap_first_wave(_repo_root())
        result = await query_service.query("beingbijmantra_surrealdb", include_provenance=True)

        assert report.missing_paths == tuple()
        assert any(
            artifact.source_path == ".beingbijmantra/2026-04-04-being-bijmantra-surrealdb-sidecar-direction.md"
            for artifact in result.recall_view.source_artifacts
        )
        assert any(
            trail.node.title == "Being Bijmantra SurrealDB Sidecar Direction"
            for trail in result.provenance_trails
        )
    finally:
        await repository.aclose()

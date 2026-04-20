from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest

import app.api.v2.developer_control_plane_project_brain as developer_control_plane_project_brain_api
from app.main import app
from app.modules.ai.services import ProjectBrainMemoryService, ProjectBrainQueryService
from app.modules.ai.services.project_brain_bootstrap import ProjectBrainBootstrapIngestionService
from app.modules.ai.services.project_brain_memory_surreal import (
    ProjectBrainSurrealConnectionConfig,
    ProjectBrainSurrealRepositoryError,
    SurrealProjectBrainMemoryRepository,
)
from tests.units.services.project_brain_surreal_testkit import (
    MockSurrealHttpServer,
    project_brain_surreal_test_config,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@pytest.fixture
async def project_brain_query_runtime_override() -> AsyncIterator[tuple[MockSurrealHttpServer, ProjectBrainSurrealConnectionConfig]]:
    config = project_brain_surreal_test_config()
    server = MockSurrealHttpServer(namespace=config.namespace, database=config.database)
    repository = SurrealProjectBrainMemoryRepository(config, transport=httpx.MockTransport(server))
    memory_service = ProjectBrainMemoryService(repository)
    bootstrap = ProjectBrainBootstrapIngestionService(memory_service)
    query_service = ProjectBrainQueryService(memory_service)
    await bootstrap.bootstrap_first_wave(_repo_root())

    async def override_runtime() -> AsyncIterator[developer_control_plane_project_brain_api.ProjectBrainQueryRuntime]:
        yield developer_control_plane_project_brain_api.ProjectBrainQueryRuntime(
            config=config,
            query_service=query_service,
        )

    app.dependency_overrides[
        developer_control_plane_project_brain_api.get_project_brain_query_runtime
    ] = override_runtime
    try:
        yield server, config
    finally:
        app.dependency_overrides.pop(
            developer_control_plane_project_brain_api.get_project_brain_query_runtime,
            None,
        )
        await repository.aclose()


async def test_project_brain_query_requires_superuser(authenticated_client):
    response = await authenticated_client.post(
        "/api/v2/developer-control-plane/project-brain/query",
        json={"query": "surrealdb"},
    )

    assert response.status_code == 403


async def test_project_brain_query_returns_sidecar_backed_recall_with_provenance(
    superuser_client,
    project_brain_query_runtime_override,
):
    _server, config = project_brain_query_runtime_override

    response = await superuser_client.post(
        "/api/v2/developer-control-plane/project-brain/query",
        json={
            "query": "beingbijmantra_surrealdb",
            "include_provenance": True,
            "trust_ranks": ["rank_a"],
            "scopes": ["global_project"],
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["query"] == "beingbijmantra_surrealdb"
    assert payload["sidecar"] == {
        "base_url": config.base_url,
        "namespace": config.namespace,
        "database": config.database,
        "is_optional": True,
        "is_non_authoritative": True,
    }
    assert payload["recall_view"]["query"] == "beingbijmantra_surrealdb"
    assert payload["recall_view"]["nodes"]
    assert all(item["trust_rank"] == "rank_a" for item in payload["recall_view"]["nodes"])
    assert all(item["scope"] == "global_project" for item in payload["recall_view"]["nodes"])
    assert payload["provenance_trails"]
    assert any(
        trail["node"]["title"] == "Being Bijmantra SurrealDB Sidecar Direction"
        for trail in payload["provenance_trails"]
    )
    assert any(
        source_artifact["source_path"]
        == ".beingbijmantra/2026-04-04-being-bijmantra-surrealdb-sidecar-direction.md"
        for trail in payload["provenance_trails"]
        for source_artifact in trail["source_artifacts"]
    )


async def test_project_brain_query_returns_service_unavailable_when_query_fails(superuser_client):
    class BrokenQueryService:
        async def query(self, *args, **kwargs):
            raise ProjectBrainSurrealRepositoryError("simulated sidecar outage")

    async def override_runtime() -> AsyncIterator[developer_control_plane_project_brain_api.ProjectBrainQueryRuntime]:
        yield developer_control_plane_project_brain_api.ProjectBrainQueryRuntime(
            config=ProjectBrainSurrealConnectionConfig(base_url="http://127.0.0.1:8083"),
            query_service=BrokenQueryService(),
        )

    app.dependency_overrides[
        developer_control_plane_project_brain_api.get_project_brain_query_runtime
    ] = override_runtime
    try:
        response = await superuser_client.post(
            "/api/v2/developer-control-plane/project-brain/query",
            json={"query": "surrealdb"},
        )
    finally:
        app.dependency_overrides.pop(
            developer_control_plane_project_brain_api.get_project_brain_query_runtime,
            None,
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Being Bijmantra project-brain sidecar is unavailable at http://127.0.0.1:8083. "
        "Start it with make dev-beingbijmantra, then bootstrap the schema and first-wave project-brain data before querying. "
        "Reason: simulated sidecar outage"
    )
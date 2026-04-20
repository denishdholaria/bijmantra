from pathlib import Path

import pytest

from app.modules.ai.services import (
    FileBackedProjectBrainMemoryRepository,
    ProjectBrainMemoryService,
)
from app.modules.ai.services.project_brain_bootstrap import ProjectBrainBootstrapIngestionService
from app.modules.ai.services.project_brain_snapshot_query import ProjectBrainSnapshotQueryService


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


@pytest.mark.asyncio
async def test_snapshot_query_service_supports_curated_keyword_queries(tmp_path: Path):
    snapshot_path = tmp_path / "project_brain_snapshot.json"
    bootstrap_repository = FileBackedProjectBrainMemoryRepository(snapshot_path)
    bootstrap_service = ProjectBrainMemoryService(bootstrap_repository)
    bootstrap = ProjectBrainBootstrapIngestionService(bootstrap_service)

    report = await bootstrap.bootstrap_first_wave(_repo_root())
    query_service = ProjectBrainSnapshotQueryService(snapshot_path)
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

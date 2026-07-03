from pathlib import Path

import pytest

from app.modules.ai.services import (
    FileBackedProjectBrainMemoryRepository,
    ProjectBrainMemoryService,
    VolatileProjectBrainMemoryRepository,
)
from app.modules.ai.services.project_brain_bootstrap import (
    FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS,
    ProjectBrainBootstrapIngestionService,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


@pytest.mark.asyncio
async def test_bootstrap_first_wave_ingests_real_repo_sources():
    service = ProjectBrainMemoryService(VolatileProjectBrainMemoryRepository())
    bootstrap = ProjectBrainBootstrapIngestionService(service)

    report = await bootstrap.bootstrap_first_wave(_repo_root())
    recall = await service.recall("surrealdb")
    roadmap_recall = await service.recall("surrealdb_sidecar")

    assert report.missing_paths == tuple()
    assert report.source_count == len(FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS)
    assert report.projection_count == len(FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS)
    assert report.node_count == len(FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS)
    assert any(
        artifact.source_path == ".ai/decisions/ADR-010-surrealdb-orchestration-memory-candidate.md"
        for artifact in recall.source_artifacts
    )
    assert any("SurrealDB" in node.title for node in recall.nodes)
    assert any(
        artifact.source_path == ".beingbijmantra/2026-04-04-being-bijmantra-project-brain-roadmap.md"
        for artifact in roadmap_recall.source_artifacts
    )
    roadmap_artifact = next(
        artifact
        for artifact in roadmap_recall.source_artifacts
        if artifact.source_path == ".beingbijmantra/2026-04-04-being-bijmantra-project-brain-roadmap.md"
    )
    assert roadmap_artifact.metadata["focus_heading"] == "Where SurrealDB Fits"
    assert "surrealdb_sidecar" in roadmap_artifact.metadata["keywords"]


@pytest.mark.asyncio
async def test_file_backed_repository_persists_bootstrap_snapshot_round_trip(tmp_path: Path):
    snapshot_path = tmp_path / "project_brain_snapshot.json"
    repository = FileBackedProjectBrainMemoryRepository(snapshot_path)
    service = ProjectBrainMemoryService(repository)
    bootstrap = ProjectBrainBootstrapIngestionService(service)

    report = await bootstrap.bootstrap_first_wave(_repo_root())

    reloaded_repository = FileBackedProjectBrainMemoryRepository(snapshot_path)
    reloaded_service = ProjectBrainMemoryService(reloaded_repository)
    charter_recall = await reloaded_service.recall("charter")

    assert report.missing_paths == tuple()
    assert snapshot_path.exists()
    assert len(await reloaded_repository.list_source_artifacts()) == len(FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS)
    assert any(
        artifact.source_path == ".beingbijmantra/2026-04-03-being-bijmantra-surface-charter.md"
        for artifact in charter_recall.source_artifacts
    )

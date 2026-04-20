from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from sqlalchemy import delete

import app.api.v2.developer_control_plane_indigenous_brain as indigenous_brain_api
from app.main import app
from app.core.config import settings
from app.models.developer_control_plane import (
    DeveloperControlPlaneActiveBoard,
    DeveloperControlPlaneApprovalReceipt,
    DeveloperControlPlaneBoardRevision,
    DeveloperControlPlaneLearningEntry,
)
from app.models.orchestrator_state import (
    OrchestratorAssignment,
    OrchestratorBlocker,
    OrchestratorDecisionNote,
    OrchestratorEvidenceItem,
    OrchestratorMission,
    OrchestratorSubtask,
    OrchestratorVerificationRun,
)
from app.modules.ai.services.project_brain_bootstrap import ProjectBrainBootstrapIngestionService
from app.modules.ai.services.project_brain_memory import ProjectBrainMemoryService
from app.modules.ai.services.project_brain_memory_surreal import (
    ProjectBrainSurrealConnectionConfig,
    SurrealProjectBrainMemoryRepository,
)
from app.modules.ai.services.project_brain_query import ProjectBrainQueryService
from tests.units.services.project_brain_surreal_testkit import (
    MockSurrealHttpServer,
    project_brain_surreal_test_config,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _board_json_with_lanes() -> str:
    return json.dumps(
        {
            "version": "1.2.0",
            "board_id": "bijmantra-app-development-master-board",
            "title": "BijMantra Developer Control Plane",
            "visibility": "internal-superuser",
            "intent": "Keep planning in one canonical board.",
            "continuous_operation_goal": "Operate from one canonical board.",
            "orchestration_contract": {
                "canonical_inputs": ["human vision"],
                "canonical_outputs": ["execution lanes"],
                "execution_loop": ["interpret vision into concrete system objectives"],
                "coordination_rules": ["human input is limited to vision and optional constraints"],
            },
            "lanes": [
                {
                    "id": "control-plane",
                    "title": "Control Plane",
                    "objective": "Make the native control plane operational.",
                    "status": "active",
                    "owners": ["OmShriMaatreNamaha"],
                    "inputs": ["active-board"],
                    "outputs": ["world-model brief"],
                    "dependencies": [],
                    "completion_criteria": ["The world model can name the next safe focus."],
                    "review_state": {
                        "spec_review": {
                            "reviewed_by": "OmVishnaveNamah",
                            "summary": "Spec review current.",
                            "evidence": ["frontend/src/features/dev-control-plane/contracts/board.test.ts"],
                            "reviewed_at": "2026-04-05T10:00:00Z",
                        },
                        "risk_review": {
                            "reviewed_by": "OmKlimKalikayeiNamah",
                            "summary": "Risk review current.",
                            "evidence": ["frontend/src/features/dev-control-plane/reviewedDispatch.test.ts"],
                            "reviewed_at": "2026-04-05T10:05:00Z",
                        },
                        "verification_evidence": {
                            "reviewed_by": "OmVishnaveNamah",
                            "summary": "Verification evidence current.",
                            "evidence": ["frontend/src/features/dev-control-plane/autonomy.test.ts"],
                            "reviewed_at": "2026-04-05T10:10:00Z",
                        },
                    },
                    "subplans": [],
                },
                {
                    "id": "platform-runtime",
                    "title": "Platform Runtime",
                    "objective": "Reconnect runtime surfaces.",
                    "status": "blocked",
                    "owners": ["OmNamahShivaya"],
                    "inputs": ["runtime-watchdog"],
                    "outputs": ["stable runtime"],
                    "dependencies": ["control-plane"],
                    "completion_criteria": ["Runtime state is stable."],
                    "subplans": [],
                },
            ],
            "agent_roles": [
                {
                    "agent": "OmShriMaatreNamaha",
                    "role": "Primary orchestrator",
                    "reads": ["board"],
                    "writes": ["dispatch"],
                    "escalation": ["destructive actions"],
                }
            ],
            "control_plane": {
                "primary_orchestrator": "OmShriMaatreNamaha",
                "evidence_sources": ["metrics.json"],
                "operating_cadence": ["inspect board before work begins"],
            },
        }
    )


def _write_queue_file(path: Path) -> None:
    payload = {
        "version": 1,
        "updatedAt": "2026-04-05T10:15:00Z",
        "language": "en",
        "vocabularyPolicy": "english-technical-only",
        "defaults": {
            "window": "nightly",
            "stateRefreshRequired": True,
            "closeoutCommands": ["make update-state"],
            "maxJobsPerRun": 2,
        },
        "jobs": [
            {
                "jobId": "overnight-lane-control-plane-token1234",
                "title": "Control Plane",
                "status": "queued",
                "priority": "p2",
                "primaryAgent": "OmShriMaatreNamaha",
                "supportAgents": ["OmVishnaveNamah"],
                "executionMode": "same-control-plane",
                "autonomousTrigger": {
                    "type": "overnight-window",
                    "window": "nightly",
                    "enabled": True,
                },
                "dependsOn": [],
                "goal": "Materialize the native world model.",
                "lane": {
                    "objective": "Materialize the native world model.",
                    "inputs": ["active-board"],
                    "outputs": ["world-model brief"],
                    "dependencies": [],
                    "completion_criteria": ["Brief is available."],
                },
                "successCriteria": ["Brief is available."],
                "verification": {
                    "commands": [],
                    "stateRefreshRequired": True,
                },
            }
        ],
    }
    path.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")


@pytest.fixture(autouse=True)
async def clear_developer_control_plane_rows(async_db_session):
    await async_db_session.execute(delete(OrchestratorAssignment))
    await async_db_session.execute(delete(OrchestratorVerificationRun))
    await async_db_session.execute(delete(OrchestratorDecisionNote))
    await async_db_session.execute(delete(OrchestratorBlocker))
    await async_db_session.execute(delete(OrchestratorEvidenceItem))
    await async_db_session.execute(delete(OrchestratorSubtask))
    await async_db_session.execute(delete(OrchestratorMission))
    await async_db_session.execute(delete(DeveloperControlPlaneLearningEntry))
    await async_db_session.execute(delete(DeveloperControlPlaneApprovalReceipt))
    await async_db_session.execute(delete(DeveloperControlPlaneBoardRevision))
    await async_db_session.execute(delete(DeveloperControlPlaneActiveBoard))
    await async_db_session.commit()


@pytest.fixture
async def project_brain_runtime_override() -> AsyncIterator[ProjectBrainSurrealConnectionConfig]:
    config = project_brain_surreal_test_config()
    server = MockSurrealHttpServer(namespace=config.namespace, database=config.database)
    repository = SurrealProjectBrainMemoryRepository(config, transport=httpx.MockTransport(server))
    memory_service = ProjectBrainMemoryService(repository)
    bootstrap = ProjectBrainBootstrapIngestionService(memory_service)
    await bootstrap.bootstrap_first_wave(_repo_root())
    query_service = ProjectBrainQueryService(memory_service)

    async def override_runtime() -> AsyncIterator[indigenous_brain_api.OptionalProjectBrainQueryRuntime]:
        yield indigenous_brain_api.OptionalProjectBrainQueryRuntime(
            base_url=config.base_url,
            query_service=query_service,
            detail=None,
        )

    app.dependency_overrides[
        indigenous_brain_api.get_optional_project_brain_query_runtime
    ] = override_runtime
    try:
        yield config
    finally:
        app.dependency_overrides.pop(
            indigenous_brain_api.get_optional_project_brain_query_runtime,
            None,
        )
        await repository.aclose()


async def test_indigenous_brain_requires_superuser(authenticated_client):
    response = await authenticated_client.get(
        "/api/v2/developer-control-plane/indigenous-brain/brief"
    )

    assert response.status_code == 403


async def test_indigenous_brain_brief_synthesizes_world_model(
    superuser_client,
    async_db_session,
    tmp_path,
    monkeypatch,
    project_brain_runtime_override,
    test_superuser,
):
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(queue_path)
    monkeypatch.setattr(indigenous_brain_api, "OVERNIGHT_QUEUE_PATH", queue_path)
    monkeypatch.setattr(settings, "MEM0_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "MEM0_API_KEY", "m0-test", raising=False)
    monkeypatch.setattr(settings, "MEM0_HOST", "https://api.mem0.ai", raising=False)
    monkeypatch.setattr(settings, "MEM0_ORG_ID", "org-123", raising=False)
    monkeypatch.setattr(settings, "MEM0_PROJECT_ID", "project-456", raising=False)

    canonical_board_json = _board_json_with_lanes()
    async_db_session.add(
        DeveloperControlPlaneActiveBoard(
            organization_id=test_superuser.organization_id,
            board_id="bijmantra-app-development-master-board",
            schema_version="1.2.0",
            visibility="internal-superuser",
            canonical_board_json=canonical_board_json,
            canonical_board_hash=hashlib.sha256(canonical_board_json.encode("utf-8")).hexdigest(),
            updated_by_user_id=test_superuser.id,
            save_source="test-seed",
            summary_metadata={"lane_count": 2},
        )
    )
    async_db_session.add(
        OrchestratorMission(
            organization_id=test_superuser.organization_id,
            mission_id="mission-control-plane-1",
            objective="Materialize the native control-plane world model.",
            status="active",
            owner="OmShriMaatreNamaha",
            priority="p1",
            producer_key="openclaw-runtime",
            queue_job_id="overnight-lane-control-plane-token1234",
            source_lane_id="control-plane",
            source_board_concurrency_token="token1234",
            source_request="Developer control-plane explicit completion write-back for lane control-plane from queue job overnight-lane-control-plane-token1234. Context: source_board_concurrency_token=token1234.",
            final_summary=None,
        )
    )
    async_db_session.add(
        DeveloperControlPlaneLearningEntry(
            organization_id=test_superuser.organization_id,
            entry_type="pattern",
            source_classification="mission-state",
            title="Control-plane world model needs durable signals",
            summary="A native world model becomes useful only when board, queue, missions, and learnings are read together.",
            confidence_score=0.92,
            recorded_by_user_id=test_superuser.id,
            recorded_by_email="admin@example.com",
            board_id="bijmantra-app-development-master-board",
            source_lane_id="control-plane",
            queue_job_id="overnight-lane-control-plane-token1234",
            linked_mission_id="mission-control-plane-1",
            approval_receipt_id=None,
            source_reference=".ai/tasks/2026-04-05-project-brain-developer-query-api.md",
            evidence_refs=["backend/tests/api/test_developer_control_plane_indigenous_brain_api.py"],
            summary_metadata=None,
        )
    )
    await async_db_session.commit()

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/indigenous-brain/brief",
        params={"project_brain_query": "beingbijmantra_surrealdb"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["indigenous_brain"]["status"] == "bootstrapped"
    assert payload["board"]["available"] is True
    assert payload["board"]["active_lane_count"] == 1
    assert payload["board"]["blocked_lane_count"] == 1
    assert payload["queue"]["exists"] is True
    assert payload["queue"]["job_count"] == 1
    assert payload["missions"]["total_count"] == 1
    assert payload["learnings"]["total_count"] == 1
    assert payload["project_brain"]["available"] is True
    assert payload["project_brain"]["query"] == "beingbijmantra_surrealdb"
    assert payload["mem0"]["enabled"] is True
    assert payload["mem0"]["ready"] is True
    assert payload["mem0"]["project_scoped"] is True
    assert payload["recommended_focus"]["lane_id"] == "control-plane"
    assert any(
        blocker["key"] == "blocked-lanes-present" for blocker in payload["blockers"]
    )
    assert any(
        path == ".beingbijmantra/2026-04-04-being-bijmantra-surrealdb-sidecar-direction.md"
        for path in payload["project_brain"]["notable_source_paths"]
    )
    assert "native control-plane world model" in payload["worldview_summary"].lower()


async def test_indigenous_brain_brief_degrades_safely_when_surfaces_are_missing(
    superuser_client,
    tmp_path,
    monkeypatch,
):
    queue_path = tmp_path / "missing-overnight-queue.json"
    monkeypatch.setattr(indigenous_brain_api, "OVERNIGHT_QUEUE_PATH", queue_path)
    monkeypatch.setattr(settings, "MEM0_ENABLED", False, raising=False)
    monkeypatch.setattr(settings, "MEM0_API_KEY", None, raising=False)
    monkeypatch.setattr(settings, "MEM0_ORG_ID", None, raising=False)
    monkeypatch.setattr(settings, "MEM0_PROJECT_ID", None, raising=False)

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/indigenous-brain/brief"
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["board"]["available"] is False
    assert payload["queue"]["exists"] is False
    assert payload["missions"]["total_count"] == 0
    assert payload["learnings"]["total_count"] == 0
    assert payload["project_brain"]["available"] is False
    assert payload["mem0"]["enabled"] is False
    assert payload["mem0"]["ready"] is False
    assert payload["recommended_focus"] is None
    assert any(
        blocker["key"] == "active-board-missing" for blocker in payload["blockers"]
    )
    assert any(
        blocker["key"] == "mission-state-empty" for blocker in payload["blockers"]
    )
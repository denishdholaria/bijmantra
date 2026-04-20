from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import delete

import app.api.v2.developer_control_plane as developer_control_plane_api
import app.api.v2.developer_control_plane_mem0 as developer_control_plane_mem0_api
from app.main import app
from app.models.developer_control_plane import DeveloperControlPlaneLearningEntry
from app.modules.ai.services.mem0_service import Mem0DisabledError


@pytest.fixture
def restore_mem0_dependency_override() -> AsyncIterator[None]:
    try:
        yield
    finally:
        app.dependency_overrides.pop(
            developer_control_plane_mem0_api.get_developer_mem0_service,
            None,
        )


async def test_developer_control_plane_mem0_requires_superuser(authenticated_client):
    response = await authenticated_client.get("/api/v2/developer-control-plane/mem0/status")

    assert response.status_code == 403


async def test_developer_control_plane_mem0_status_returns_backend_state(
    superuser_client,
    restore_mem0_dependency_override,
):
    class FakeMem0Service:
        def status(self):
            return {
                "enabled": True,
                "configured": True,
                "host": "https://api.mem0.ai",
                "project_scoped": False,
                "org_project_pair_valid": True,
            }

    app.dependency_overrides[developer_control_plane_mem0_api.get_developer_mem0_service] = (
        lambda: FakeMem0Service()
    )

    response = await superuser_client.get("/api/v2/developer-control-plane/mem0/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == {
        "enabled": True,
        "configured": True,
        "host": "https://api.mem0.ai",
        "project_scoped": False,
        "org_project_pair_valid": True,
        "is_optional": True,
        "is_canonical_authority": False,
    }
    assert payload["purpose"].startswith("Developer-only cloud memory")


async def test_developer_control_plane_mem0_health_returns_probe_result(
    superuser_client,
    restore_mem0_dependency_override,
):
    captured: dict[str, object] = {}

    class FakeMem0Service:
        async def health_check(self, **kwargs):
            captured.update(kwargs)
            return {
                "reachable": True,
                "checked_at": "2026-04-05T12:00:00Z",
                "latency_ms": 12.5,
                "result_count": 0,
                "detail": "Mem0 cloud probe succeeded with the configured backend credentials.",
            }

    app.dependency_overrides[developer_control_plane_mem0_api.get_developer_mem0_service] = (
        lambda: FakeMem0Service()
    )

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/mem0/health",
        params={
            "user_id": "bijmantra-dev",
            "app_id": "bijmantra-dev",
            "run_id": "probe-1",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "scope": {
            "user_id": "bijmantra-dev",
            "app_id": "bijmantra-dev",
            "run_id": "probe-1",
        },
        "reachable": True,
        "checked_at": "2026-04-05T12:00:00Z",
        "latency_ms": 12.5,
        "result_count": 0,
        "detail": "Mem0 cloud probe succeeded with the configured backend credentials.",
    }
    assert captured == {
        "user_id": "bijmantra-dev",
        "agent_id": "developer-control-plane",
        "app_id": "bijmantra-dev",
        "run_id": "probe-1",
    }


async def test_developer_control_plane_mem0_add_routes_developer_memory(
    superuser_client,
    restore_mem0_dependency_override,
):
    captured: dict[str, object] = {}

    class FakeMem0Service:
        async def add_messages(self, message, **kwargs):
            captured["message"] = message
            captured["kwargs"] = kwargs
            return {"results": [{"memory": message, "id": "mem-1"}]}

    app.dependency_overrides[developer_control_plane_mem0_api.get_developer_mem0_service] = (
        lambda: FakeMem0Service()
    )

    response = await superuser_client.post(
        "/api/v2/developer-control-plane/mem0/memories",
        json={
            "text": "Keep .beingbijmantra constitutional and keep REEVU separate.",
            "user_id": "denish-dev",
            "app_id": "bijmantra-dev",
            "run_id": "session-1",
            "category": "architecture",
            "metadata": {"source_note": "autonomous-next-step"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == {
        "user_id": "denish-dev",
        "app_id": "bijmantra-dev",
        "run_id": "session-1",
    }
    assert payload["result"]["results"][0]["id"] == "mem-1"
    assert captured == {
        "message": "Keep .beingbijmantra constitutional and keep REEVU separate.",
        "kwargs": {
            "user_id": "denish-dev",
            "agent_id": "developer-control-plane",
            "app_id": "bijmantra-dev",
            "run_id": "session-1",
            "metadata": {
                "source_note": "autonomous-next-step",
                "source_surface": "developer_control_plane",
                "memory_class": "developer_micro_memory",
                "app_context": "bijmantra-dev",
                "category": "architecture",
            },
        },
    }


async def test_developer_control_plane_mem0_search_routes_developer_query(
    superuser_client,
    restore_mem0_dependency_override,
):
    captured: dict[str, object] = {}

    class FakeMem0Service:
        async def search(self, query, **kwargs):
            captured["query"] = query
            captured["kwargs"] = kwargs
            return {"results": [{"memory": "Keep REEVU separate", "score": 0.91}]}

    app.dependency_overrides[developer_control_plane_mem0_api.get_developer_mem0_service] = (
        lambda: FakeMem0Service()
    )

    response = await superuser_client.post(
        "/api/v2/developer-control-plane/mem0/search",
        json={
            "query": "How should Mem0 relate to REEVU?",
            "user_id": "denish-dev",
            "app_id": "bijmantra-dev",
            "run_id": "session-2",
            "limit": 3,
            "filters": {"category": "architecture"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "How should Mem0 relate to REEVU?"
    assert payload["limit"] == 3
    assert payload["result"]["results"][0]["score"] == 0.91
    assert captured == {
        "query": "How should Mem0 relate to REEVU?",
        "kwargs": {
            "user_id": "denish-dev",
            "agent_id": "developer-control-plane",
            "app_id": "bijmantra-dev",
            "run_id": "session-2",
            "limit": 3,
            "filters": {"category": "architecture"},
        },
    }


async def test_developer_control_plane_mem0_add_returns_service_unavailable_when_disabled(
    superuser_client,
    restore_mem0_dependency_override,
):
    class FakeMem0Service:
        async def add_messages(self, *args, **kwargs):
            raise Mem0DisabledError("Mem0 is disabled. Set MEM0_ENABLED=true before using the Mem0 service.")

    app.dependency_overrides[developer_control_plane_mem0_api.get_developer_mem0_service] = (
        lambda: FakeMem0Service()
    )

    response = await superuser_client.post(
        "/api/v2/developer-control-plane/mem0/memories",
        json={"text": "test memory"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Mem0 is disabled. Set MEM0_ENABLED=true before using the Mem0 service."
    )


async def test_developer_control_plane_mem0_health_returns_service_unavailable_when_disabled(
    superuser_client,
    restore_mem0_dependency_override,
):
    class FakeMem0Service:
        async def health_check(self, **kwargs):
            raise Mem0DisabledError("Mem0 is disabled. Set MEM0_ENABLED=true before using the Mem0 service.")

    app.dependency_overrides[developer_control_plane_mem0_api.get_developer_mem0_service] = (
        lambda: FakeMem0Service()
    )

    response = await superuser_client.get("/api/v2/developer-control-plane/mem0/health")

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Mem0 is disabled. Set MEM0_ENABLED=true before using the Mem0 service."
    )


@pytest.fixture(autouse=True)
async def clear_learning_entries(async_db_session):
    await async_db_session.execute(delete(DeveloperControlPlaneLearningEntry))
    await async_db_session.commit()


async def test_developer_control_plane_mem0_capture_learning_entry(
    superuser_client,
    async_db_session,
    restore_mem0_dependency_override,
    test_superuser,
):
    captured: dict[str, object] = {}

    entry = DeveloperControlPlaneLearningEntry(
        organization_id=test_superuser.organization_id,
        entry_type="pattern",
        source_classification="mission-state",
        title="Keep cloud recall outside REEVU",
        summary="Developer cloud recall should remain a separate optional memory lane.",
        confidence_score=0.93,
        recorded_by_user_id=test_superuser.id,
        recorded_by_email=test_superuser.email,
        board_id="bijmantra-app-development-master-board",
        source_lane_id="control-plane",
        queue_job_id="job-1",
        linked_mission_id="mission-1",
        approval_receipt_id=None,
        source_reference=".ai/tasks/mem0-learning.md",
        evidence_refs=["backend/tests/api/test_developer_control_plane_mem0_api.py"],
        summary_metadata={"focus": "boundary"},
    )
    async_db_session.add(entry)
    await async_db_session.commit()
    await async_db_session.refresh(entry)

    class FakeMem0Service:
        async def add_messages(self, message, **kwargs):
            captured["message"] = message
            captured["kwargs"] = kwargs
            return {"results": [{"id": "mem-learn-1"}]}

    app.dependency_overrides[developer_control_plane_mem0_api.get_developer_mem0_service] = (
        lambda: FakeMem0Service()
    )

    response = await superuser_client.post(
        f"/api/v2/developer-control-plane/mem0/learnings/{entry.id}/capture",
        json={
            "user_id": "bijmantra-dev",
            "app_id": "bijmantra-dev",
            "run_id": "mem0-capture-1",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"]["learning_entry_id"] == entry.id
    assert payload["result"]["results"][0]["id"] == "mem-learn-1"
    assert "Keep cloud recall outside REEVU" in payload["memory_text"]
    assert captured == {
        "message": (
            "Developer control plane learning [pattern] Keep cloud recall outside REEVU. "
            "Summary: Developer cloud recall should remain a separate optional memory lane. "
            "Source classification: mission-state. Source lane: control-plane. Queue job: job-1. Mission: mission-1."
        ),
        "kwargs": {
            "user_id": "bijmantra-dev",
            "agent_id": "developer-control-plane",
            "app_id": "bijmantra-dev",
            "run_id": "mem0-capture-1",
            "metadata": {
                "source_surface": "developer_control_plane_learning_ledger",
                "memory_class": "developer_learning_recall",
                "learning_entry_id": entry.id,
                "entry_type": "pattern",
                "source_classification": "mission-state",
                "board_id": "bijmantra-app-development-master-board",
                "source_lane_id": "control-plane",
                "queue_job_id": "job-1",
                "linked_mission_id": "mission-1",
                "source_reference": ".ai/tasks/mem0-learning.md",
                "evidence_refs": ["backend/tests/api/test_developer_control_plane_mem0_api.py"],
                "confidence_score": 0.93,
            },
        },
    }


async def test_developer_control_plane_mem0_capture_learning_entry_returns_not_found(
    superuser_client,
    restore_mem0_dependency_override,
):
    response = await superuser_client.post(
        "/api/v2/developer-control-plane/mem0/learnings/999999/capture",
        json={"user_id": "bijmantra-dev"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Learning entry 999999 was not found for this organization."


async def test_developer_control_plane_mem0_capture_mission(
    superuser_client,
    restore_mem0_dependency_override,
    monkeypatch,
):
    captured: dict[str, object] = {}

    async def fake_ensure_mission_state_schema_ready(db):
        return None

    async def fake_load_runtime_mission_snapshot(db, organization_id, mission_id):
        assert mission_id == "mission-1"
        return object()

    mission_detail = developer_control_plane_api.DeveloperControlPlaneMissionDetailResponse(
        mission_id="mission-1",
        objective="Capture canonical mission outcomes into Mem0 explicitly",
        status="completed",
        owner="OmShriMaatreNamaha",
        priority="high",
        producer_key="OmShriMaatreNamaha",
        queue_job_id="job-1",
        source_lane_id="control-plane",
        source_board_concurrency_token="token-1",
        created_at="2026-04-05T10:00:00Z",
        updated_at="2026-04-05T10:30:00Z",
        subtask_total=3,
        subtask_completed=3,
        assignment_total=3,
        evidence_count=2,
        blocker_count=0,
        escalation_needed=False,
        verification=developer_control_plane_api.DeveloperControlPlaneMissionVerificationSummaryResponse(
            passed=2,
            warned=0,
            failed=0,
            last_verified_at="2026-04-05T10:25:00Z",
        ),
        final_summary="Mission closeout evidence is now available for explicit developer recall.",
        subtasks=[],
        assignments=[],
        evidence_items=[
            developer_control_plane_api.DeveloperControlPlaneMissionEvidenceResponse(
                id="evidence-1",
                mission_id="mission-1",
                subtask_id=None,
                kind="artifact",
                evidence_class="verification",
                summary="Focused backend and frontend tests passed.",
                source_path="frontend/src/features/dev-control-plane/ui/mem0/Mem0Tab.test.tsx",
                recorded_at="2026-04-05T10:25:00Z",
            )
        ],
        verification_runs=[],
        decision_notes=[],
        blockers=[],
    )

    closeout_receipt = developer_control_plane_api.DeveloperControlPlaneCloseoutReceiptResponse(
        exists=True,
        queue_job_id="job-1",
        mission_id="mission-1",
        closeout_status="succeeded",
        state_refresh_required=False,
        receipt_recorded_at="2026-04-05T10:31:00Z",
        started_at="2026-04-05T10:00:00Z",
        finished_at="2026-04-05T10:30:00Z",
        verification_evidence_ref=".agent/runtime/missions/job-1/verify.json",
        queue_sha256_at_closeout="sha-1",
        closeout_commands=[
            developer_control_plane_api.DeveloperControlPlaneCloseoutCommandResultResponse(
                command="make test",
                passed=True,
                exit_code=0,
                started_at="2026-04-05T10:15:00Z",
                finished_at="2026-04-05T10:20:00Z",
                stdout_tail="tests passed",
                stderr_tail=None,
            )
        ],
        artifacts=[
            developer_control_plane_api.DeveloperControlPlaneCloseoutArtifactResponse(
                path=".agent/runtime/missions/job-1/closeout.json",
                exists=True,
                sha256="abc123",
                modified_at="2026-04-05T10:31:00Z",
            )
        ],
    )

    monkeypatch.setattr(
        developer_control_plane_mem0_api,
        "_ensure_mission_state_schema_ready",
        fake_ensure_mission_state_schema_ready,
    )
    monkeypatch.setattr(
        developer_control_plane_mem0_api,
        "_load_runtime_mission_snapshot",
        fake_load_runtime_mission_snapshot,
    )
    monkeypatch.setattr(
        developer_control_plane_mem0_api,
        "_mission_detail_response",
        lambda snapshot: mission_detail,
    )
    monkeypatch.setattr(
        developer_control_plane_mem0_api,
        "_load_closeout_receipt",
        lambda queue_job_id: {"data": {"status": "succeeded"}},
    )
    monkeypatch.setattr(
        developer_control_plane_mem0_api,
        "_closeout_receipt_response",
        lambda queue_job_id, receipt: closeout_receipt,
    )

    class FakeMem0Service:
        async def add_messages(self, message, **kwargs):
            captured["message"] = message
            captured["kwargs"] = kwargs
            return {"results": [{"id": "mem-mission-1"}]}

    app.dependency_overrides[developer_control_plane_mem0_api.get_developer_mem0_service] = (
        lambda: FakeMem0Service()
    )

    response = await superuser_client.post(
        "/api/v2/developer-control-plane/mem0/missions/mission-1/capture",
        json={
            "user_id": "bijmantra-dev",
            "app_id": "bijmantra-dev",
            "run_id": "mission-capture-1",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"]["mission_id"] == "mission-1"
    assert payload["closeout_receipt"]["closeout_status"] == "succeeded"
    assert payload["result"]["results"][0]["id"] == "mem-mission-1"
    assert "Capture canonical mission outcomes into Mem0 explicitly" in payload["memory_text"]
    assert captured["kwargs"] == {
        "user_id": "bijmantra-dev",
        "agent_id": "developer-control-plane",
        "app_id": "bijmantra-dev",
        "run_id": "mission-capture-1",
        "metadata": {
            "source_surface": "developer_control_plane_mission_state",
            "memory_class": "developer_mission_recall",
            "mission_id": "mission-1",
            "status": "completed",
            "owner": "OmShriMaatreNamaha",
            "priority": "high",
            "producer_key": "OmShriMaatreNamaha",
            "queue_job_id": "job-1",
            "source_lane_id": "control-plane",
            "source_board_concurrency_token": "token-1",
            "final_summary": "Mission closeout evidence is now available for explicit developer recall.",
            "subtask_total": 3,
            "subtask_completed": 3,
            "assignment_total": 3,
            "evidence_count": 2,
            "blocker_count": 0,
            "escalation_needed": False,
            "verification": {
                "passed": 2,
                "warned": 0,
                "failed": 0,
                "last_verified_at": "2026-04-05T10:25:00Z",
            },
            "evidence_refs": [
                "frontend/src/features/dev-control-plane/ui/mem0/Mem0Tab.test.tsx"
            ],
            "decision_note_count": 0,
            "closeout_receipt_exists": True,
            "closeout_status": "succeeded",
            "closeout_verification_evidence_ref": ".agent/runtime/missions/job-1/verify.json",
            "closeout_artifact_paths": [".agent/runtime/missions/job-1/closeout.json"],
            "closeout_command_count": 1,
        },
    }


async def test_developer_control_plane_mem0_capture_mission_returns_not_found(
    superuser_client,
    restore_mem0_dependency_override,
    monkeypatch,
):
    async def fake_ensure_mission_state_schema_ready(db):
        return None

    async def fake_load_runtime_mission_snapshot(db, organization_id, mission_id):
        return None

    monkeypatch.setattr(
        developer_control_plane_mem0_api,
        "_ensure_mission_state_schema_ready",
        fake_ensure_mission_state_schema_ready,
    )
    monkeypatch.setattr(
        developer_control_plane_mem0_api,
        "_load_runtime_mission_snapshot",
        fake_load_runtime_mission_snapshot,
    )

    response = await superuser_client.post(
        "/api/v2/developer-control-plane/mem0/missions/missing-mission/capture",
        json={"user_id": "bijmantra-dev"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Mission not found"
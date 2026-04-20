import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import delete, select

from app.models.core import Organization
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
from app.modules.ai.services.orchestrator_state import (
    OrchestratorMissionStateService,
    SubtaskStatus,
    VerificationResult,
)
from app.modules.ai.services.orchestrator_state_postgres import PostgresMissionStateRepository
from app.schemas.developer_control_plane import DEVELOPER_MASTER_BOARD_SCHEMA_VERSION
import app.api.v2.developer_control_plane as developer_control_plane_api


DEFAULT_REVIEW_STATE = object()
DEFAULT_QUEUE_PROVENANCE = object()


def _normalize_timestamp(value: str | datetime) -> str:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed.isoformat()


def _board_json(title: str = "BijMantra App Development Master Board") -> str:
    return json.dumps(
        {
            "version": "1.0.0",
            "board_id": "bijmantra-app-development-master-board",
            "title": title,
            "visibility": "internal-superuser",
            "intent": "Keep planning in one canonical board.",
            "continuous_operation_goal": "Operate from one canonical board.",
            "orchestration_contract": {
                "canonical_inputs": [],
                "canonical_outputs": [],
                "execution_loop": [],
                "coordination_rules": [],
            },
            "lanes": [],
            "agent_roles": [],
            "control_plane": {
                "primary_orchestrator": "OmShriMaatreNamaha",
                "evidence_sources": [],
                "operating_cadence": [],
            },
        }
    )

def _board_json_with_lane(
    *,
    title: str = "BijMantra App Development Master Board",
    lane_id: str = "control-plane",
    lane_status: str = "active",
    validation_basis: dict | None = None,
    review_state: dict | None | object = DEFAULT_REVIEW_STATE,
    closure: dict | None = None,
    version: str = "1.0.0",
) -> str:
    lane_payload = {
        "id": lane_id,
        "title": "Control Plane Lane",
        "objective": "Own completion write-back state.",
        "status": lane_status,
        "owners": ["OmShriMaatreNamaha"],
        "inputs": ["board"],
        "outputs": ["closure evidence"],
        "dependencies": [],
        "completion_criteria": ["Closure evidence is written back manually"],
        "subplans": [],
    }
    if validation_basis is not None:
        lane_payload["validation_basis"] = validation_basis
    if review_state is DEFAULT_REVIEW_STATE:
        lane_payload["review_state"] = {
            "spec_review": {
                "reviewed_by": "OmVishnaveNamah",
                "summary": "Spec review is current.",
                "evidence": ["frontend/src/features/dev-control-plane/contracts/board.test.ts"],
                "reviewed_at": "2026-03-31T09:00:00Z",
            },
            "risk_review": {
                "reviewed_by": "OmKlimKalikayeiNamah",
                "summary": "Risk review is current.",
                "evidence": ["frontend/src/features/dev-control-plane/reviewedDispatch.test.ts"],
                "reviewed_at": "2026-03-31T09:05:00Z",
            },
            "verification_evidence": {
                "reviewed_by": "OmVishnaveNamah",
                "summary": "Verification evidence is current.",
                "evidence": ["frontend/src/features/dev-control-plane/autonomy.test.ts"],
                "reviewed_at": "2026-03-31T09:10:00Z",
            },
        }
    elif review_state is not None:
        lane_payload["review_state"] = review_state
    if closure is not None:
        lane_payload["closure"] = closure

    return json.dumps(
        {
            "version": version,
            "board_id": "bijmantra-app-development-master-board",
            "title": title,
            "visibility": "internal-superuser",
            "intent": "Keep planning in one canonical board.",
            "continuous_operation_goal": "Operate from one canonical board.",
            "orchestration_contract": {
                "canonical_inputs": [],
                "canonical_outputs": [],
                "execution_loop": [],
                "coordination_rules": [],
            },
            "lanes": [lane_payload],
            "agent_roles": [],
            "control_plane": {
                "primary_orchestrator": "OmShriMaatreNamaha",
                "evidence_sources": [],
                "operating_cadence": [],
            },
        }
    )


def _queue_payload(
    *,
    job_id: str = "existing-job",
    include_job: bool = True,
    status: str = "queued",
) -> dict:
    jobs = []
    if include_job:
        jobs.append(
            {
                "jobId": job_id,
                "title": "Existing queued job",
                "status": status,
                "priority": "p1",
                "primaryAgent": "OmShriMaatreNamaha",
                "supportAgents": ["OmVishnaveNamah"],
                "executionMode": "same-control-plane",
                "autonomousTrigger": {
                    "type": "overnight-window",
                    "window": "nightly",
                    "enabled": True,
                },
                "dependsOn": [],
                "goal": "Existing queue baseline goal",
                "lane": {
                    "objective": "Existing queue baseline objective",
                    "inputs": ["input-a"],
                    "outputs": ["output-a"],
                    "dependencies": [],
                    "completion_criteria": ["Complete the baseline job"],
                },
                "successCriteria": ["Complete the baseline job"],
                "verification": {
                    "commands": ["echo verify"],
                    "stateRefreshRequired": True,
                },
            }
        )

    return {
        "version": 1,
        "updatedAt": "2026-03-18T00:00:00Z",
        "language": "en",
        "vocabularyPolicy": "english-technical-only",
        "defaults": {
            "window": "nightly",
            "stateRefreshRequired": True,
            "closeoutCommands": ["make update-state"],
            "maxJobsPerRun": 2,
        },
        "jobs": jobs,
    }


def _queue_entry_provenance(
    *,
    source_token: str,
    lane_id: str = "control-plane",
    board_title: str = "Queue Writer",
) -> dict:
    return {
        "candidateVersion": "1.0.0",
        "exportedAt": "2026-03-19T00:00:00Z",
        "boardId": "bijmantra-app-development-master-board",
        "boardTitle": board_title,
        "sourceBoardConcurrencyToken": source_token,
        "sourceLaneId": lane_id,
        "precedence": {
            "canonicalPlanningSource": "active-board",
            "derivedExecutionSurface": "overnight-queue",
            "exportDisposition": "manual-candidate-only",
            "conflictResolution": "board-wins-no-silent-overwrite",
            "staleIfSourceBoardChanges": True,
        },
    }


def _queue_entry_payload(
    *,
    job_id: str,
    depends_on: list[str] | None = None,
    provenance: dict | None = None,
) -> dict:
    payload = {
        "jobId": job_id,
        "title": "Slice 7C queue write",
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
        "dependsOn": depends_on or [],
        "goal": "Write one reviewed queue entry",
        "lane": {
            "objective": "Persist reviewed queue-native entry",
            "inputs": ["input-a"],
            "outputs": ["output-a"],
            "dependencies": [],
            "completion_criteria": ["Queue file reflects the reviewed entry"],
        },
        "successCriteria": ["Queue file reflects the reviewed entry"],
        "verification": {
            "commands": [],
            "stateRefreshRequired": True,
        },
    }

    if provenance is not None:
        payload["provenance"] = provenance

    return payload


def _write_queue_file(path: Path, payload: dict) -> None:
    path.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")


def _queue_write_request(
    *,
    source_token: str,
    expected_queue_sha256: str,
    job_id: str,
    depends_on: list[str] | None = None,
    provenance: dict | None | object = DEFAULT_QUEUE_PROVENANCE,
) -> dict:
    if provenance is DEFAULT_QUEUE_PROVENANCE:
        provenance = _queue_entry_provenance(source_token=source_token)

    return {
        "source_board_concurrency_token": source_token,
        "expected_queue_sha256": expected_queue_sha256,
        "operator_intent": "write-reviewed-queue-entry",
        "queue_entry": _queue_entry_payload(
            job_id=job_id,
            depends_on=depends_on,
            provenance=provenance,
        ),
    }


def _completion_write_request(
    *,
    source_token: str,
    expected_queue_sha256: str,
    lane_id: str,
    queue_job_id: str,
    closure_summary: str = "Completion evidence was reviewed and accepted.",
    evidence: list[str] | None = None,
    closeout_receipt: dict | None = None,
) -> dict:
    return {
        "source_board_concurrency_token": source_token,
        "expected_queue_sha256": expected_queue_sha256,
        "operator_intent": "write-reviewed-lane-completion",
        "completion": {
            "source_lane_id": lane_id,
            "queue_job_id": queue_job_id,
            "closure_summary": closure_summary,
            "evidence": evidence or ["Focused tests passed", "Queue job completed"],
            "closeout_receipt": closeout_receipt,
        },
    }


def _completion_closeout_receipt_payload(queue_job_id: str) -> dict:
    return {
        "queue_job_id": queue_job_id,
        "artifact_paths": ["metrics.json"],
        "mission_id": "runtime-mission-control-plane-token1234",
        "producer_key": "openclaw-runtime",
        "source_lane_id": "control-plane",
        "source_board_concurrency_token": "token-1234",
        "runtime_profile_id": "bijmantra-bca-local-verify",
        "runtime_policy_sha256": "policy-sha-1234",
        "closeout_status": "passed",
        "state_refresh_required": True,
        "receipt_recorded_at": "2026-03-19T12:05:00Z",
        "verification_evidence_ref": "runtime-artifacts/mission-evidence/job/verification_1.json",
        "queue_sha256_at_closeout": "queue-sha-closeout-77",
    }


def _write_closeout_receipt_file(mission_dir: Path, queue_job_id: str) -> None:
    receipt_dir = mission_dir / queue_job_id
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / "closeout.json").write_text(
        json.dumps(
            {
                "jobId": queue_job_id,
                "type": "closeout",
                "timestamp": "2026-03-19T12:05:00Z",
                "data": {
                    "version": 1,
                    "receiptType": "closeout",
                    "queueJobId": queue_job_id,
                    "missionId": "runtime-mission-control-plane-token1234",
                    "producerKey": "openclaw-runtime",
                    "sourceLaneId": "control-plane",
                    "sourceBoardConcurrencyToken": "token-1234",
                    "runtimeProfileId": "bijmantra-bca-local-verify",
                    "runtimePolicySha256": "policy-sha-1234",
                    "queueSha256AtWrite": "queue-sha-closeout-77",
                    "stateRefreshRequired": True,
                    "status": "passed",
                    "startedAt": "2026-03-19T12:03:00Z",
                    "finishedAt": "2026-03-19T12:04:00Z",
                    "verificationEvidenceRef": "runtime-artifacts/mission-evidence/job/verification_1.json",
                    "closeoutCommands": [],
                    "artifacts": [
                        {
                            "path": "metrics.json",
                            "exists": True,
                            "sha256": "abc123",
                            "modifiedAt": "2026-03-19T12:03:50Z",
                        }
                    ],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


@pytest.fixture(autouse=True)
async def clear_active_board_rows(async_db_session):
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


async def _list_approval_receipts(async_db_session):
    result = await async_db_session.execute(
        select(DeveloperControlPlaneApprovalReceipt).order_by(
            DeveloperControlPlaneApprovalReceipt.id.asc()
        )
    )
    return list(result.scalars())


async def test_developer_control_plane_requires_superuser(authenticated_client):
    response = await authenticated_client.get("/api/v2/developer-control-plane/active-board")
    assert response.status_code == 403


async def test_active_board_fetch_returns_no_record_when_empty(superuser_client):
    response = await superuser_client.get("/api/v2/developer-control-plane/active-board")

    assert response.status_code == 200
    assert response.json() == {"exists": False, "record": None}


async def test_active_board_fetch_returns_service_unavailable_when_schema_is_partial(
    superuser_client, monkeypatch
):
    async def fake_missing_tables(_db):
        return ["developer_control_plane_board_revisions"]

    monkeypatch.setattr(
        developer_control_plane_api,
        "_get_missing_persistence_tables",
        fake_missing_tables,
    )

    response = await superuser_client.get("/api/v2/developer-control-plane/active-board")

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Developer control-plane persistence schema is not ready; missing table(s): "
        "developer_control_plane_board_revisions. Run backend alembic upgrade through revision 20260318_1500."
    )


async def test_active_board_save_and_fetch_round_trip(superuser_client):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json(),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )

    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["board_id"] == "bijmantra-app-development-master-board"
    assert saved["schema_version"] == "1.0.0"
    assert saved["visibility"] == "internal-superuser"
    assert saved["canonical_board_json"].endswith("\n")
    assert saved["save_source"] == "direct-ui"
    assert saved["summary_metadata"]["lane_count"] == 0
    assert saved["concurrency_token"]

    fetch_response = await superuser_client.get("/api/v2/developer-control-plane/active-board")
    assert fetch_response.status_code == 200
    fetched = fetch_response.json()
    assert fetched["exists"] is True
    assert fetched["record"]["concurrency_token"] == saved["concurrency_token"]
    assert fetched["record"]["canonical_board_json"] == saved["canonical_board_json"]

    versions_response = await superuser_client.get(
        "/api/v2/developer-control-plane/active-board/versions"
    )
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert versions["board_id"] == "bijmantra-app-development-master-board"
    assert versions["current_concurrency_token"] == saved["concurrency_token"]
    assert versions["total_count"] == 1
    assert versions["versions"][0]["concurrency_token"] == saved["concurrency_token"]
    assert versions["versions"][0]["is_current"] is True


async def test_active_board_versions_requires_superuser(authenticated_client):
    response = await authenticated_client.get(
        "/api/v2/developer-control-plane/active-board/versions"
    )
    assert response.status_code == 403


async def test_active_board_restore_requires_superuser(authenticated_client):
    response = await authenticated_client.post(
        "/api/v2/developer-control-plane/active-board/versions/1/restore",
        json={"concurrency_token": None},
    )
    assert response.status_code == 403


async def test_active_board_versions_returns_empty_list_when_no_history(superuser_client):
    response = await superuser_client.get(
        "/api/v2/developer-control-plane/active-board/versions"
    )

    assert response.status_code == 200
    assert response.json() == {
        "board_id": "bijmantra-app-development-master-board",
        "current_concurrency_token": None,
        "total_count": 0,
        "versions": [],
    }


async def test_active_board_is_scoped_to_current_organization(superuser_client, async_db_session):
    foreign_org = Organization(name="Foreign Developer Control Plane Org")
    async_db_session.add(foreign_org)
    await async_db_session.flush()
    async_db_session.add(
        DeveloperControlPlaneActiveBoard(
            organization_id=foreign_org.id,
            board_id="bijmantra-app-development-master-board",
            schema_version="1.0.0",
            visibility="internal-superuser",
            canonical_board_json=f"{_board_json()}\n",
            canonical_board_hash="foreign-hash",
            updated_by_user_id=1,
            save_source="foreign-seed",
            summary_metadata={"title": "Foreign"},
        )
    )
    await async_db_session.commit()

    response = await superuser_client.get("/api/v2/developer-control-plane/active-board")
    assert response.status_code == 200
    assert response.json() == {"exists": False, "record": None}


async def test_active_board_rejects_stale_concurrency_token(superuser_client):
    first_save = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Initial Board"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert first_save.status_code == 200
    stale_token = first_save.json()["concurrency_token"]

    second_save = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Updated Board"),
            "save_source": "direct-ui",
            "concurrency_token": stale_token,
        },
    )
    assert second_save.status_code == 200
    current_token = second_save.json()["concurrency_token"]
    assert current_token != stale_token

    conflict_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Stale Retry"),
            "save_source": "direct-ui",
            "concurrency_token": stale_token,
        },
    )
    assert conflict_response.status_code == 409
    conflict = conflict_response.json()["detail"]
    assert conflict["detail"] == "Active board save conflict; refetch the current board before retrying"
    assert conflict["current_record"]["concurrency_token"] == current_token

    versions_response = await superuser_client.get(
        "/api/v2/developer-control-plane/active-board/versions"
    )
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert versions["total_count"] == 2
    assert versions["versions"][0]["concurrency_token"] == current_token
    assert versions["versions"][0]["is_current"] is True
    assert versions["versions"][1]["concurrency_token"] == stale_token
    assert versions["versions"][1]["is_current"] is False


async def test_active_board_same_hash_resave_does_not_create_duplicate_revision(superuser_client):
    first_save = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Stable Board"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert first_save.status_code == 200
    concurrency_token = first_save.json()["concurrency_token"]

    second_save = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Stable Board"),
            "save_source": "direct-ui",
            "concurrency_token": concurrency_token,
        },
    )
    assert second_save.status_code == 200
    assert second_save.json()["concurrency_token"] == concurrency_token

    versions_response = await superuser_client.get(
        "/api/v2/developer-control-plane/active-board/versions"
    )
    assert versions_response.status_code == 200
    assert versions_response.json()["total_count"] == 1


async def test_active_board_save_preserves_validation_basis_metadata(superuser_client):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(
                validation_basis={
                    "owner": "OmVishnaveNamah",
                    "summary": "Focused route review remains the explicit validation basis.",
                    "evidence": [
                        "frontend/src/features/dev-control-plane/autonomy.test.ts"
                    ],
                    "last_reviewed_at": "2026-03-18T20:00:00Z",
                }
            ),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )

    assert save_response.status_code == 200
    saved_board = json.loads(save_response.json()["canonical_board_json"])
    assert saved_board["lanes"][0]["validation_basis"] == {
        "owner": "OmVishnaveNamah",
        "summary": "Focused route review remains the explicit validation basis.",
        "evidence": [
            "frontend/src/features/dev-control-plane/autonomy.test.ts"
        ],
        "last_reviewed_at": "2026-03-18T20:00:00Z",
    }


async def test_active_board_restore_missing_revision_returns_not_found(superuser_client):
    response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/versions/999/restore",
        json={"concurrency_token": None},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Developer control-plane revision not found"


async def test_active_board_restore_rejects_stale_concurrency_token(superuser_client):
    first_save = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Restore A"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert first_save.status_code == 200
    stale_token = first_save.json()["concurrency_token"]

    second_save = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Restore B"),
            "save_source": "direct-ui",
            "concurrency_token": stale_token,
        },
    )
    assert second_save.status_code == 200
    current_token = second_save.json()["concurrency_token"]
    versions = (
        await superuser_client.get("/api/v2/developer-control-plane/active-board/versions")
    ).json()["versions"]
    revision_id = versions[1]["revision_id"]

    restore_response = await superuser_client.post(
        f"/api/v2/developer-control-plane/active-board/versions/{revision_id}/restore",
        json={"concurrency_token": stale_token},
    )
    assert restore_response.status_code == 409
    conflict = restore_response.json()["detail"]
    assert conflict["current_record"]["concurrency_token"] == current_token

    versions_response = await superuser_client.get(
        "/api/v2/developer-control-plane/active-board/versions"
    )
    assert versions_response.status_code == 200
    assert versions_response.json()["total_count"] == 2


async def test_active_board_restore_previous_revision_updates_head_and_appends_event(
    superuser_client,
    async_db_session,
):
    first_save = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Restore A"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert first_save.status_code == 200
    first_token = first_save.json()["concurrency_token"]

    second_save = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Restore B"),
            "save_source": "direct-ui",
            "concurrency_token": first_token,
        },
    )
    assert second_save.status_code == 200
    second_token = second_save.json()["concurrency_token"]

    versions_before_restore = (
        await superuser_client.get("/api/v2/developer-control-plane/active-board/versions")
    ).json()["versions"]
    restore_revision_id = versions_before_restore[1]["revision_id"]

    restore_response = await superuser_client.post(
        f"/api/v2/developer-control-plane/active-board/versions/{restore_revision_id}/restore",
        json={"concurrency_token": second_token},
    )
    assert restore_response.status_code == 200
    restore_payload = restore_response.json()
    assert restore_payload["restored"] is True
    assert restore_payload["restored_from_revision_id"] == restore_revision_id
    assert restore_payload["record"]["concurrency_token"] == first_token
    assert restore_payload["record"]["save_source"] == "restore-version"
    assert restore_payload["approval_receipt"]["action_type"] == "restore-active-board-version"
    assert restore_payload["approval_receipt"]["target_revision_id"] == restore_revision_id
    assert restore_payload["approval_receipt"]["source_board_concurrency_token"] == second_token
    assert restore_payload["approval_receipt"]["resulting_board_concurrency_token"] == first_token
    assert restore_payload["record"]["summary_metadata"]["restore"]["from_revision_id"] == restore_revision_id
    assert (
        restore_payload["record"]["summary_metadata"]["restore"][
            "previous_active_concurrency_token"
        ]
        == second_token
    )

    approval_receipts = await _list_approval_receipts(async_db_session)
    assert len(approval_receipts) == 1
    assert approval_receipts[0].action_type == "restore-active-board-version"
    assert approval_receipts[0].target_revision_id == restore_revision_id
    assert approval_receipts[0].source_board_concurrency_token == second_token
    assert approval_receipts[0].resulting_board_concurrency_token == first_token

    versions_response = await superuser_client.get(
        "/api/v2/developer-control-plane/active-board/versions"
    )
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert versions["total_count"] == 3
    assert versions["current_concurrency_token"] == first_token
    assert versions["versions"][0]["concurrency_token"] == first_token
    assert versions["versions"][0]["save_source"] == "restore-version"
    assert versions["versions"][0]["is_current"] is True
    assert versions["versions"][1]["concurrency_token"] == second_token
    assert versions["versions"][1]["is_current"] is False


async def test_active_board_restore_current_head_is_noop(superuser_client, async_db_session):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Restore Stable"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    current_token = save_response.json()["concurrency_token"]

    versions_before_restore = (
        await superuser_client.get("/api/v2/developer-control-plane/active-board/versions")
    ).json()
    restore_revision_id = versions_before_restore["versions"][0]["revision_id"]

    restore_response = await superuser_client.post(
        f"/api/v2/developer-control-plane/active-board/versions/{restore_revision_id}/restore",
        json={"concurrency_token": current_token},
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["restored"] is False
    assert restore_response.json()["record"]["concurrency_token"] == current_token
    assert restore_response.json()["approval_receipt"] is None

    assert await _list_approval_receipts(async_db_session) == []

    versions_after_restore = await superuser_client.get(
        "/api/v2/developer-control-plane/active-board/versions"
    )
    assert versions_after_restore.status_code == 200
    assert versions_after_restore.json()["total_count"] == 1


async def test_active_board_save_rejects_invalid_schema_version(superuser_client):
    invalid_board_json = json.dumps(
        {
            **json.loads(_board_json()),
            "version": "0.9.0",
        }
    )

    response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": invalid_board_json,
            "save_source": "import",
            "concurrency_token": None,
        },
    )
    assert response.status_code == 400
    assert "unsupported schema version" in response.json()["detail"]

    versions_response = await superuser_client.get(
        "/api/v2/developer-control-plane/active-board/versions"
    )
    assert versions_response.status_code == 200
    assert versions_response.json()["total_count"] == 0


async def test_active_board_versions_are_scoped_to_current_organization(
    superuser_client, async_db_session
):
    foreign_org = Organization(name="Foreign Revision Org")
    async_db_session.add(foreign_org)
    await async_db_session.flush()
    async_db_session.add(
        DeveloperControlPlaneBoardRevision(
            organization_id=foreign_org.id,
            board_id="bijmantra-app-development-master-board",
            schema_version="1.0.0",
            visibility="internal-superuser",
            canonical_board_json=f"{_board_json()}\n",
            canonical_board_hash="foreign-hash",
            saved_by_user_id=1,
            save_source="foreign-seed",
            summary_metadata={"title": "Foreign"},
        )
    )
    await async_db_session.commit()

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/active-board/versions"
    )
    assert response.status_code == 200
    assert response.json()["total_count"] == 0


async def test_active_board_restore_is_scoped_to_current_organization(
    superuser_client, async_db_session
):
    foreign_org = Organization(name="Foreign Restore Org")
    async_db_session.add(foreign_org)
    await async_db_session.flush()
    foreign_revision = DeveloperControlPlaneBoardRevision(
        organization_id=foreign_org.id,
        board_id="bijmantra-app-development-master-board",
        schema_version="1.0.0",
        visibility="internal-superuser",
        canonical_board_json=f"{_board_json('Foreign Restore')}\n",
        canonical_board_hash="foreign-restore-hash",
        saved_by_user_id=1,
        save_source="foreign-seed",
        summary_metadata={"title": "Foreign Restore"},
    )
    async_db_session.add(foreign_revision)
    await async_db_session.commit()

    response = await superuser_client.post(
        f"/api/v2/developer-control-plane/active-board/versions/{foreign_revision.id}/restore",
        json={"concurrency_token": None},
    )
    assert response.status_code == 404


async def test_active_board_restore_recreates_head_when_missing(
    superuser_client, async_db_session
):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Recoverable Head"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    saved_token = save_response.json()["concurrency_token"]

    versions_before_delete = (
        await superuser_client.get("/api/v2/developer-control-plane/active-board/versions")
    ).json()
    restore_revision_id = versions_before_delete["versions"][0]["revision_id"]

    await async_db_session.execute(delete(DeveloperControlPlaneActiveBoard))
    await async_db_session.commit()

    restore_response = await superuser_client.post(
        f"/api/v2/developer-control-plane/active-board/versions/{restore_revision_id}/restore",
        json={"concurrency_token": None},
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["restored"] is True
    assert restore_response.json()["record"]["concurrency_token"] == saved_token

    versions_after_restore = await superuser_client.get(
        "/api/v2/developer-control-plane/active-board/versions"
    )
    assert versions_after_restore.status_code == 200
    assert versions_after_restore.json()["total_count"] == 2


async def test_active_board_restore_rejects_invalid_revision_payload(
    superuser_client, async_db_session
):
    current_org = (
        await async_db_session.execute(
            select(Organization.id).where(Organization.name == "Test Admin Org")
        )
    ).scalar_one()

    invalid_revision = DeveloperControlPlaneBoardRevision(
        organization_id=current_org,
        board_id="bijmantra-app-development-master-board",
        schema_version="1.0.0",
        visibility="internal-superuser",
        canonical_board_json=json.dumps(
            {
                **json.loads(_board_json("Invalid Revision")),
                "version": "0.9.0",
            }
        ),
        canonical_board_hash="invalid-revision-hash",
        saved_by_user_id=1,
        save_source="seed-invalid",
        summary_metadata={"title": "Invalid Revision"},
    )
    async_db_session.add(invalid_revision)
    await async_db_session.commit()

    response = await superuser_client.post(
        f"/api/v2/developer-control-plane/active-board/versions/{invalid_revision.id}/restore",
        json={"concurrency_token": None},
    )
    assert response.status_code == 400
    assert "Invalid developer master board revision" in response.json()["detail"]

    fetch_response = await superuser_client.get("/api/v2/developer-control-plane/active-board")
    assert fetch_response.status_code == 200
    assert fetch_response.json() == {"exists": False, "record": None}

    versions_response = await superuser_client.get(
        "/api/v2/developer-control-plane/active-board/versions"
    )
    assert versions_response.status_code == 200
    assert versions_response.json()["total_count"] == 1


async def test_overnight_queue_status_requires_superuser(authenticated_client):
    response = await authenticated_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert response.status_code == 403


async def test_overnight_queue_write_requires_superuser(authenticated_client):
    response = await authenticated_client.post(
        "/api/v2/developer-control-plane/overnight-queue/write-entry",
        json={
            "source_board_concurrency_token": "token",
            "expected_queue_sha256": "sha",
            "operator_intent": "write-reviewed-queue-entry",
            "queue_entry": {},
        },
    )
    assert response.status_code == 403


async def test_overnight_queue_write_appends_entry_deterministically(
    superuser_client, tmp_path, monkeypatch, async_db_session
):
    queue_path = tmp_path / "overnight-queue.json"
    queue_payload = _queue_payload(job_id="existing-job", include_job=True)
    _write_queue_file(queue_path, queue_payload)
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(title="Queue Writer"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert status_response.status_code == 200
    queue_sha = status_response.json()["queue_sha256"]

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/overnight-queue/write-entry",
        json=_queue_write_request(
            source_token=board_token,
            expected_queue_sha256=queue_sha,
            job_id="overnight-lane-control-plane-token1234",
            depends_on=["existing-job"],
        ),
    )
    assert write_response.status_code == 200
    payload = write_response.json()
    assert payload["written_job_id"] == "overnight-lane-control-plane-token1234"
    assert payload["replaced"] is False
    assert payload["approval_receipt"]["action_type"] == "write-reviewed-queue-entry"
    assert payload["approval_receipt"]["queue_job_id"] == "overnight-lane-control-plane-token1234"
    assert payload["approval_receipt"]["expected_queue_sha256"] == queue_sha
    assert payload["approval_receipt"]["resulting_queue_sha256"] == payload["queue_sha256"]

    queue_after_write = json.loads(queue_path.read_text(encoding="utf-8"))
    assert list(queue_after_write.keys()) == [
        "version",
        "updatedAt",
        "language",
        "vocabularyPolicy",
        "defaults",
        "jobs",
    ]
    assert queue_after_write["jobs"][0]["jobId"] == "existing-job"
    assert queue_after_write["jobs"][1]["jobId"] == "overnight-lane-control-plane-token1234"

    approval_receipts = await _list_approval_receipts(async_db_session)
    assert len(approval_receipts) == 1
    assert approval_receipts[0].action_type == "write-reviewed-queue-entry"
    assert approval_receipts[0].queue_job_id == "overnight-lane-control-plane-token1234"
    assert approval_receipts[0].source_lane_id == "control-plane"
    assert approval_receipts[0].expected_queue_sha256 == queue_sha
    assert approval_receipts[0].resulting_queue_sha256 == payload["queue_sha256"]


async def test_learning_ledger_lists_accepted_review_patterns_seeded_on_explicit_write(
    superuser_client, async_db_session, tmp_path, monkeypatch
):
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(queue_path, _queue_payload(job_id="existing-job", include_job=True))
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(title="Queue Writer"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert status_response.status_code == 200
    queue_sha = status_response.json()["queue_sha256"]

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/overnight-queue/write-entry",
        json=_queue_write_request(
            source_token=board_token,
            expected_queue_sha256=queue_sha,
            job_id="overnight-lane-control-plane-token1234",
            depends_on=["existing-job"],
        ),
    )
    assert write_response.status_code == 200
    approval_receipt_id = write_response.json()["approval_receipt"]["receipt_id"]

    stored_learning_entries = list(
        (
            await async_db_session.execute(
                select(DeveloperControlPlaneLearningEntry).where(
                    DeveloperControlPlaneLearningEntry.source_lane_id == "control-plane"
                )
            )
        ).scalars()
    )
    assert len(stored_learning_entries) == 1
    assert stored_learning_entries[0].approval_receipt_id == approval_receipt_id

    learnings_response = await superuser_client.get(
        "/api/v2/developer-control-plane/learnings",
        params={"source_lane_id": "control-plane"},
    )
    assert learnings_response.status_code == 200
    learnings_payload = learnings_response.json()
    assert learnings_payload["total_count"] == 1
    learning_entry = learnings_payload["entries"][0]
    assert learning_entry["learning_entry_id"]
    assert learning_entry["organization_id"]
    assert learning_entry["entry_type"] == "pattern"
    assert learning_entry["source_classification"] == "accepted-review"
    assert learning_entry["title"] == "Accepted review enabled queue export for lane control-plane"
    assert learning_entry["summary"] == (
        "Explicit spec_review and risk_review evidence supported queue export for lane "
        "control-plane into queue job overnight-lane-control-plane-token1234 without "
        "weakening board-wins precedence."
    )
    assert learning_entry["confidence_score"] == 0.93
    assert learning_entry["recorded_by_user_id"]
    assert learning_entry["recorded_by_email"] == "admin@example.com"
    assert learning_entry["board_id"] == "bijmantra-app-development-master-board"
    assert learning_entry["source_lane_id"] == "control-plane"
    assert learning_entry["queue_job_id"] == "overnight-lane-control-plane-token1234"
    assert learning_entry["linked_mission_id"] is None
    assert learning_entry["approval_receipt_id"] == approval_receipt_id
    assert learning_entry["source_reference"] == (
        f"approval-receipt:{approval_receipt_id}:accepted-review"
    )
    assert learning_entry["evidence_refs"] == [
        "frontend/src/features/dev-control-plane/contracts/board.test.ts",
        "frontend/src/features/dev-control-plane/reviewedDispatch.test.ts",
    ]
    assert learning_entry["summary_metadata"] == {
        "seed_source": "approval-receipt",
        "approval_receipt_action": "write-reviewed-queue-entry",
        "approval_receipt_outcome": "applied",
        "queue_sha256": write_response.json()["queue_sha256"],
    }
    assert learning_entry["recorded_at"]

    repeated_learnings_response = await superuser_client.get(
        "/api/v2/developer-control-plane/learnings",
        params={"source_lane_id": "control-plane"},
    )
    assert repeated_learnings_response.status_code == 200
    repeated_payload = repeated_learnings_response.json()
    assert repeated_payload["total_count"] == 1
    assert repeated_payload["entries"][0]["approval_receipt_id"] == approval_receipt_id


async def test_overnight_queue_write_preserves_reviewed_provenance(
    superuser_client, tmp_path, monkeypatch
):
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(queue_path, _queue_payload(job_id="existing-job", include_job=True))
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(title="Queue Writer"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert status_response.status_code == 200

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/overnight-queue/write-entry",
        json=_queue_write_request(
            source_token=board_token,
            expected_queue_sha256=status_response.json()["queue_sha256"],
            job_id="overnight-lane-control-plane-token1234",
            depends_on=["existing-job"],
            provenance=_queue_entry_provenance(source_token=board_token),
        ),
    )
    assert write_response.status_code == 200

    queue_after_write = json.loads(queue_path.read_text(encoding="utf-8"))
    written_job = queue_after_write["jobs"][1]
    assert written_job["provenance"] == _queue_entry_provenance(source_token=board_token)


async def test_overnight_queue_write_rejects_missing_canonical_lane_reviews(
    superuser_client, tmp_path, monkeypatch
):
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(queue_path, _queue_payload(job_id="existing-job", include_job=True))
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(review_state=None),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert status_response.status_code == 200

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/overnight-queue/write-entry",
        json=_queue_write_request(
            source_token=board_token,
            expected_queue_sha256=status_response.json()["queue_sha256"],
            job_id="overnight-lane-control-plane-token1234",
            depends_on=["existing-job"],
        ),
    )
    assert write_response.status_code == 409
    detail = write_response.json()["detail"]
    assert detail["conflict_reason"] == "lane-review-missing"
    assert detail["refresh_targets"] == ["active-board"]
    assert detail["retry_permitted_after_refresh"] is False


async def test_overnight_queue_write_rejects_stale_board_token(
    superuser_client, tmp_path, monkeypatch, async_db_session
):
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(queue_path, _queue_payload(job_id="existing-job", include_job=True))
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    first_save = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Queue Writer A"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert first_save.status_code == 200
    stale_token = first_save.json()["concurrency_token"]

    second_save = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Queue Writer B"),
            "save_source": "direct-ui",
            "concurrency_token": stale_token,
        },
    )
    assert second_save.status_code == 200

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert status_response.status_code == 200

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/overnight-queue/write-entry",
        json=_queue_write_request(
            source_token=stale_token,
            expected_queue_sha256=status_response.json()["queue_sha256"],
            job_id="overnight-lane-control-plane-stale",
            depends_on=["existing-job"],
        ),
    )
    assert write_response.status_code == 409
    detail = write_response.json()["detail"]
    assert detail["conflict_reason"] == "stale-board-token"
    assert (
        detail["remediation_message"]
        == "Refresh the shared board state, confirm the selected lane still materializes to the intended queue entry, then retry with the current board token."
    )
    assert detail["refresh_targets"] == ["active-board"]
    assert detail["retry_permitted_after_refresh"] is True

    queue_after_attempt = json.loads(queue_path.read_text(encoding="utf-8"))
    assert len(queue_after_attempt["jobs"]) == 1
    assert await _list_approval_receipts(async_db_session) == []


async def test_overnight_queue_write_rejects_queue_sha_mismatch(superuser_client, tmp_path, monkeypatch):
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(queue_path, _queue_payload(job_id="existing-job", include_job=True))
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Queue Writer"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert status_response.status_code == 200
    stale_queue_sha = status_response.json()["queue_sha256"]

    queue_payload = _queue_payload(job_id="existing-job", include_job=True)
    queue_payload["updatedAt"] = "2026-03-19T00:00:00Z"
    _write_queue_file(queue_path, queue_payload)

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/overnight-queue/write-entry",
        json=_queue_write_request(
            source_token=board_token,
            expected_queue_sha256=stale_queue_sha,
            job_id="overnight-lane-control-plane-stale-sha",
            depends_on=["existing-job"],
        ),
    )
    assert write_response.status_code == 409
    detail = write_response.json()["detail"]
    assert detail["conflict_reason"] == "queue-sha-mismatch"
    assert detail["refresh_targets"] == ["overnight-queue"]
    assert detail["retry_permitted_after_refresh"] is True


async def test_overnight_queue_write_rejects_duplicate_job_id(superuser_client, tmp_path, monkeypatch):
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(queue_path, _queue_payload(job_id="existing-job", include_job=True))
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json("Queue Writer"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert status_response.status_code == 200

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/overnight-queue/write-entry",
        json=_queue_write_request(
            source_token=board_token,
            expected_queue_sha256=status_response.json()["queue_sha256"],
            job_id="existing-job",
            depends_on=[],
        ),
    )
    assert write_response.status_code == 409
    detail = write_response.json()["detail"]
    assert detail["conflict_reason"] == "duplicate-job-id"
    assert detail["refresh_targets"] == ["overnight-queue", "active-board"]
    assert detail["retry_permitted_after_refresh"] is False

    queue_after_attempt = json.loads(queue_path.read_text(encoding="utf-8"))
    assert len(queue_after_attempt["jobs"]) == 1


async def test_completion_write_requires_superuser(authenticated_client):
    response = await authenticated_client.post(
        "/api/v2/developer-control-plane/active-board/write-completion",
        json={
            "source_board_concurrency_token": "token",
            "expected_queue_sha256": "sha",
            "operator_intent": "write-reviewed-lane-completion",
            "completion": {
                "source_lane_id": "control-plane",
                "queue_job_id": "job",
                "closure_summary": "summary",
                "evidence": ["evidence"],
            },
        },
    )
    assert response.status_code == 403


async def test_prepare_completion_write_requires_active_board(superuser_client):
    response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/prepare-completion-write",
        json={"source_lane_id": "control-plane"},
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["conflict_reason"] == "missing-active-board"
    assert detail["refresh_targets"] == ["active-board"]
    assert detail["retry_permitted_after_refresh"] is True


async def test_prepare_completion_write_returns_queue_snapshot_backed_request(
    superuser_client, tmp_path, monkeypatch
):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    queue_job_id = f"overnight-lane-control-plane-{board_token.lower().replace('-', '')[:8]}"
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(
        queue_path,
        _queue_payload(job_id=queue_job_id, include_job=True, status="completed"),
    )
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/prepare-completion-write",
        json={"source_lane_id": "control-plane"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_lane_id"] == "control-plane"
    assert payload["queue_job_id"] == queue_job_id
    assert payload["draft_source"] == "queue-snapshot"
    assert payload["closeout_receipt"]["exists"] is False
    assert payload["prepared_request"]["source_board_concurrency_token"] == board_token
    assert (
        payload["prepared_request"]["expected_queue_sha256"]
        == payload["queue_status"]["queue_sha256"]
    )
    assert payload["prepared_request"]["operator_intent"] == "write-reviewed-lane-completion"
    assert payload["prepared_request"]["completion"] == {
        "source_lane_id": "control-plane",
        "queue_job_id": queue_job_id,
        "closure_summary": "Reviewed closeout for lane control-plane after queue completion and canonical queue refresh.",
        "evidence": [
            f"Reviewed queue job {queue_job_id} before explicit board write-back.",
            f"Queue snapshot hash at reviewed closeout: {payload['queue_status']['queue_sha256']}.",
            f"Board token used for reviewed closeout: {board_token}.",
            f"Queue status reviewed at {payload['queue_status']['updated_at']}.",
        ],
        "closeout_receipt": None,
    }


async def test_prepare_completion_write_returns_receipt_backed_request_when_available(
    superuser_client, tmp_path, monkeypatch
):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    queue_job_id = f"overnight-lane-control-plane-{board_token.lower().replace('-', '')[:8]}"
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(
        queue_path,
        _queue_payload(job_id=queue_job_id, include_job=True, status="completed"),
    )
    mission_dir = tmp_path / "mission-evidence"
    _write_closeout_receipt_file(mission_dir, queue_job_id)
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)
    monkeypatch.setattr(developer_control_plane_api, "MISSION_EVIDENCE_DIR", mission_dir)

    response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/prepare-completion-write",
        json={"source_lane_id": "control-plane"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["draft_source"] == "stable-closeout-receipt"
    assert payload["closeout_receipt"]["exists"] is True
    assert payload["prepared_request"]["completion"]["closure_summary"] == (
        "Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh."
    )
    assert payload["prepared_request"]["completion"]["evidence"] == [
        f"Reviewed queue job {queue_job_id} using watchdog closeout receipt before explicit board write-back.",
        "Watchdog closeout queue hash: queue-sha-closeout-77.",
        f"Board token used for reviewed closeout: {board_token}.",
        "Runtime profile recorded by closeout receipt: bijmantra-bca-local-verify.",
        "Verification evidence referenced by closeout receipt: runtime-artifacts/mission-evidence/job/verification_1.json.",
        "Closeout artifact refreshed: metrics.json.",
        "Stable closeout receipt recorded at 2026-03-19T12:05:00Z.",
    ]
    assert payload["prepared_request"]["completion"]["closeout_receipt"] == (
        _completion_closeout_receipt_payload(queue_job_id)
    )


async def test_completion_write_marks_active_lane_completed(
    superuser_client, tmp_path, monkeypatch, async_db_session
):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    queue_job_id = f"overnight-lane-control-plane-{board_token.lower().replace('-', '')[:8]}"
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(
        queue_path,
        _queue_payload(job_id=queue_job_id, include_job=True, status="completed"),
    )
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert status_response.status_code == 200

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/write-completion",
        json=_completion_write_request(
            source_token=board_token,
            expected_queue_sha256=status_response.json()["queue_sha256"],
            lane_id="control-plane",
            queue_job_id=queue_job_id,
        ),
    )
    assert write_response.status_code == 200
    payload = write_response.json()
    assert payload["no_op"] is False
    assert payload["lane_status"] == "completed"
    assert payload["record"]["schema_version"] == DEVELOPER_MASTER_BOARD_SCHEMA_VERSION
    assert payload["approval_receipt"]["action_type"] == "write-reviewed-lane-completion"
    assert payload["approval_receipt"]["source_lane_id"] == "control-plane"
    assert payload["approval_receipt"]["queue_job_id"] == queue_job_id
    assert payload["approval_receipt"]["source_board_concurrency_token"] == board_token
    assert (
        payload["approval_receipt"]["resulting_board_concurrency_token"]
        == payload["record"]["concurrency_token"]
    )

    board_after_write = json.loads(payload["record"]["canonical_board_json"])
    assert board_after_write["lanes"][0]["status"] == "completed"
    assert board_after_write["lanes"][0]["closure"]["queue_job_id"] == queue_job_id

    approval_receipts = await _list_approval_receipts(async_db_session)
    assert len(approval_receipts) == 1
    assert approval_receipts[0].action_type == "write-reviewed-lane-completion"
    assert approval_receipts[0].source_lane_id == "control-plane"
    assert approval_receipts[0].queue_job_id == queue_job_id
    assert approval_receipts[0].source_board_concurrency_token == board_token
    assert approval_receipts[0].resulting_board_concurrency_token == payload["record"]["concurrency_token"]


async def test_completion_write_rejects_missing_canonical_verification_evidence(
    superuser_client, tmp_path, monkeypatch
):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(
                review_state={
                    "spec_review": {
                        "reviewed_by": "OmVishnaveNamah",
                        "summary": "Spec review is current.",
                        "evidence": [
                            "frontend/src/features/dev-control-plane/contracts/board.test.ts"
                        ],
                        "reviewed_at": "2026-03-31T09:00:00Z",
                    },
                    "risk_review": {
                        "reviewed_by": "OmKlimKalikayeiNamah",
                        "summary": "Risk review is current.",
                        "evidence": [
                            "frontend/src/features/dev-control-plane/reviewedDispatch.test.ts"
                        ],
                        "reviewed_at": "2026-03-31T09:05:00Z",
                    },
                }
            ),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    queue_job_id = f"overnight-lane-control-plane-{board_token.lower().replace('-', '')[:8]}"
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(
        queue_path,
        _queue_payload(job_id=queue_job_id, include_job=True, status="completed"),
    )
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert status_response.status_code == 200

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/write-completion",
        json=_completion_write_request(
            source_token=board_token,
            expected_queue_sha256=status_response.json()["queue_sha256"],
            lane_id="control-plane",
            queue_job_id=queue_job_id,
        ),
    )
    assert write_response.status_code == 409
    detail = write_response.json()["detail"]
    assert detail["conflict_reason"] == "lane-verification-missing"
    assert detail["refresh_targets"] == ["active-board"]
    assert detail["retry_permitted_after_refresh"] is False


async def test_completion_write_persists_validated_closeout_receipt(
    superuser_client, tmp_path, monkeypatch
):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    queue_job_id = f"overnight-lane-control-plane-{board_token.lower().replace('-', '')[:8]}"
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(
        queue_path,
        _queue_payload(job_id=queue_job_id, include_job=True, status="completed"),
    )
    mission_dir = tmp_path / "mission-evidence"
    _write_closeout_receipt_file(mission_dir, queue_job_id)
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)
    monkeypatch.setattr(developer_control_plane_api, "MISSION_EVIDENCE_DIR", mission_dir)

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert status_response.status_code == 200

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/write-completion",
        json=_completion_write_request(
            source_token=board_token,
            expected_queue_sha256=status_response.json()["queue_sha256"],
            lane_id="control-plane",
            queue_job_id=queue_job_id,
            closeout_receipt=_completion_closeout_receipt_payload(queue_job_id),
        ),
    )
    assert write_response.status_code == 200

    board_after_write = json.loads(write_response.json()["record"]["canonical_board_json"])
    assert board_after_write["lanes"][0]["closure"]["closeout_receipt"] == {
        "queue_job_id": queue_job_id,
        "artifact_paths": ["metrics.json"],
        "mission_id": "runtime-mission-control-plane-token1234",
        "producer_key": "openclaw-runtime",
        "source_lane_id": "control-plane",
        "source_board_concurrency_token": "token-1234",
        "runtime_profile_id": "bijmantra-bca-local-verify",
        "runtime_policy_sha256": "policy-sha-1234",
        "closeout_status": "passed",
        "state_refresh_required": True,
        "receipt_recorded_at": "2026-03-19T12:05:00Z",
        "verification_evidence_ref": "runtime-artifacts/mission-evidence/job/verification_1.json",
        "queue_sha256_at_closeout": "queue-sha-closeout-77",
    }
    assert write_response.json()["record"]["summary_metadata"]["completion"] == {
        "lane_id": "control-plane",
        "queue_job_id": queue_job_id,
        "queue_sha256": status_response.json()["queue_sha256"],
        "closeout_receipt_present": True,
        "closeout_receipt_recorded_at": "2026-03-19T12:05:00Z",
        "closeout_receipt_mission_id": "runtime-mission-control-plane-token1234",
        "closeout_receipt_producer_key": "openclaw-runtime",
        "closeout_receipt_runtime_profile_id": "bijmantra-bca-local-verify",
        "closeout_receipt_runtime_policy_sha256": "policy-sha-1234",
    }

    mission_state_response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/mission-state"
    )
    assert mission_state_response.status_code == 200
    mission_state_payload = mission_state_response.json()
    assert mission_state_payload["count"] == 1
    mission_summary = mission_state_payload["missions"][0]
    assert mission_summary["mission_id"] == "runtime-mission-control-plane-token1234"
    assert mission_summary["objective"] == "Reviewed closeout persistence for lane Control Plane Lane"
    assert mission_summary["producer_key"] == "openclaw-runtime"
    assert mission_summary["queue_job_id"] == queue_job_id
    assert mission_summary["source_lane_id"] == "control-plane"
    assert mission_summary["source_board_concurrency_token"] == "token-1234"
    assert mission_summary["subtask_total"] == 1
    assert mission_summary["subtask_completed"] == 1
    assert mission_summary["evidence_count"] == 2
    assert mission_summary["verification"]["passed"] == 1
    assert mission_summary["final_summary"] == (
        "Canonical board closure persisted reviewed runtime provenance for lane control-plane. "
        "Closure summary: Completion evidence was reviewed and accepted."
    )

    mission_detail_response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/mission-state/runtime-mission-control-plane-token1234"
    )
    assert mission_detail_response.status_code == 200
    mission_detail_payload = mission_detail_response.json()
    assert mission_detail_payload["mission_id"] == "runtime-mission-control-plane-token1234"
    assert mission_detail_payload["queue_job_id"] == queue_job_id
    assert mission_detail_payload["source_lane_id"] == "control-plane"
    assert mission_detail_payload["source_board_concurrency_token"] == "token-1234"
    assert mission_detail_payload["subtasks"] == [
        {
            "id": mission_detail_payload["subtasks"][0]["id"],
            "title": "Persist reviewed closeout evidence",
            "status": "completed",
            "owner_role": "OmVishnaveNamah",
            "depends_on": [],
            "updated_at": mission_detail_payload["subtasks"][0]["updated_at"],
        }
    ]
    assert sorted(item["kind"] for item in mission_detail_payload["evidence_items"]) == [
        "closeout_receipt",
        "verification_evidence",
    ]
    assert sorted(item["source_path"] for item in mission_detail_payload["evidence_items"]) == [
        "runtime-artifacts/mission-evidence/job/verification_1.json",
        f"runtime-artifacts/mission-evidence/{queue_job_id}/closeout.json",
    ]
    assert mission_detail_payload["verification_runs"] == [
        {
            "id": mission_detail_payload["verification_runs"][0]["id"],
            "subject_id": mission_detail_payload["subtasks"][0]["id"],
            "verification_type": "closeout_receipt_review",
            "result": "passed",
            "evidence_ref": mission_detail_payload["evidence_items"][0]["id"],
            "executed_at": mission_detail_payload["verification_runs"][0]["executed_at"],
        }
    ]


async def test_completion_write_requires_receipt_contract_when_closeout_receipt_exists(
    superuser_client, tmp_path, monkeypatch
):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    queue_job_id = f"overnight-lane-control-plane-{board_token.lower().replace('-', '')[:8]}"
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(
        queue_path,
        _queue_payload(job_id=queue_job_id, include_job=True, status="completed"),
    )
    mission_dir = tmp_path / "mission-evidence"
    _write_closeout_receipt_file(mission_dir, queue_job_id)
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)
    monkeypatch.setattr(developer_control_plane_api, "MISSION_EVIDENCE_DIR", mission_dir)

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert status_response.status_code == 200

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/write-completion",
        json=_completion_write_request(
            source_token=board_token,
            expected_queue_sha256=status_response.json()["queue_sha256"],
            lane_id="control-plane",
            queue_job_id=queue_job_id,
        ),
    )
    assert write_response.status_code == 409
    assert write_response.json()["detail"]["conflict_reason"] == "closeout-receipt-required"


async def test_completion_write_rejects_stale_board_token(
    superuser_client, tmp_path, monkeypatch, async_db_session
):
    first_save = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(title="Completion A"),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert first_save.status_code == 200
    stale_token = first_save.json()["concurrency_token"]

    second_save = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(title="Completion B"),
            "save_source": "direct-ui",
            "concurrency_token": stale_token,
        },
    )
    assert second_save.status_code == 200

    queue_job_id = f"overnight-lane-control-plane-{stale_token.lower().replace('-', '')[:8]}"
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(
        queue_path,
        _queue_payload(job_id=queue_job_id, include_job=True, status="completed"),
    )
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/write-completion",
        json=_completion_write_request(
            source_token=stale_token,
            expected_queue_sha256=status_response.json()["queue_sha256"],
            lane_id="control-plane",
            queue_job_id=queue_job_id,
        ),
    )
    assert write_response.status_code == 409
    detail = write_response.json()["detail"]
    assert detail["conflict_reason"] == "stale-board-token"
    assert detail["refresh_targets"] == ["active-board"]
    assert detail["retry_permitted_after_refresh"] is True
    assert await _list_approval_receipts(async_db_session) == []


async def test_completion_write_rejects_queue_sha_mismatch(superuser_client, tmp_path, monkeypatch):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    queue_job_id = f"overnight-lane-control-plane-{board_token.lower().replace('-', '')[:8]}"
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(
        queue_path,
        _queue_payload(job_id=queue_job_id, include_job=True, status="completed"),
    )
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    stale_queue_sha = status_response.json()["queue_sha256"]

    _write_queue_file(
        queue_path,
        _queue_payload(job_id=queue_job_id, include_job=True, status="completed"),
    )
    queue_payload = json.loads(queue_path.read_text(encoding="utf-8"))
    queue_payload["updatedAt"] = "2026-03-19T00:00:00Z"
    _write_queue_file(queue_path, queue_payload)

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/write-completion",
        json=_completion_write_request(
            source_token=board_token,
            expected_queue_sha256=stale_queue_sha,
            lane_id="control-plane",
            queue_job_id=queue_job_id,
        ),
    )
    assert write_response.status_code == 409
    detail = write_response.json()["detail"]
    assert detail["conflict_reason"] == "queue-sha-mismatch"
    assert detail["refresh_targets"] == ["overnight-queue"]
    assert detail["retry_permitted_after_refresh"] is True


async def test_completion_write_rejects_missing_queue_job(superuser_client, tmp_path, monkeypatch):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(queue_path, _queue_payload(include_job=False))
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    queue_job_id = f"overnight-lane-control-plane-{board_token.lower().replace('-', '')[:8]}"

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/write-completion",
        json=_completion_write_request(
            source_token=board_token,
            expected_queue_sha256=status_response.json()["queue_sha256"],
            lane_id="control-plane",
            queue_job_id=queue_job_id,
        ),
    )
    assert write_response.status_code == 409
    assert write_response.json()["detail"]["conflict_reason"] == "queue-job-missing"


async def test_completion_write_rejects_lane_job_mismatch(superuser_client, tmp_path, monkeypatch):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(
        queue_path,
        _queue_payload(job_id="overnight-lane-other-token1234", include_job=True, status="completed"),
    )
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/write-completion",
        json=_completion_write_request(
            source_token=board_token,
            expected_queue_sha256=status_response.json()["queue_sha256"],
            lane_id="control-plane",
            queue_job_id="overnight-lane-other-token1234",
        ),
    )
    assert write_response.status_code == 409
    assert write_response.json()["detail"]["conflict_reason"] == "lane-job-mismatch"


async def test_closeout_receipt_returns_exists_false_when_missing(superuser_client, tmp_path, monkeypatch):
    mission_dir = tmp_path / "mission-evidence"
    monkeypatch.setattr(developer_control_plane_api, "MISSION_EVIDENCE_DIR", mission_dir)

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/jobs/overnight-lane-control-plane-token1234/closeout-receipt"
    )

    assert response.status_code == 200
    assert response.json() == {
        "exists": False,
        "queue_job_id": "overnight-lane-control-plane-token1234",
        "mission_id": None,
        "producer_key": None,
        "source_lane_id": None,
        "source_board_concurrency_token": None,
        "runtime_profile_id": None,
        "runtime_policy_sha256": None,
        "closeout_status": None,
        "state_refresh_required": None,
        "receipt_recorded_at": None,
        "started_at": None,
        "finished_at": None,
        "verification_evidence_ref": None,
        "queue_sha256_at_closeout": None,
        "closeout_commands": [],
        "artifacts": [],
    }


async def test_closeout_receipt_returns_stable_runtime_receipt(superuser_client, tmp_path, monkeypatch):
    mission_dir = tmp_path / "mission-evidence"
    receipt_dir = mission_dir / "overnight-lane-control-plane-token1234"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / "closeout.json").write_text(
        json.dumps(
            {
                "jobId": "overnight-lane-control-plane-token1234",
                "type": "closeout",
                "timestamp": "2026-03-19T12:05:00Z",
                "data": {
                    "version": 1,
                    "receiptType": "closeout",
                    "queueJobId": "overnight-lane-control-plane-token1234",
                    "missionId": "runtime-mission-control-plane-token1234",
                    "producerKey": "openclaw-runtime",
                    "sourceLaneId": "control-plane",
                    "sourceBoardConcurrencyToken": "token-1234",
                    "runtimeProfileId": "bijmantra-bca-local-verify",
                    "runtimePolicySha256": "policy-sha-1234",
                    "queueSha256AtWrite": "queue-sha-closeout-77",
                    "stateRefreshRequired": True,
                    "status": "passed",
                    "startedAt": "2026-03-19T12:03:00Z",
                    "finishedAt": "2026-03-19T12:04:00Z",
                    "verificationEvidenceRef": "runtime-artifacts/mission-evidence/job/verification_1.json",
                    "closeoutCommands": [
                        {
                            "command": "make update-state",
                            "passed": True,
                            "exitCode": 0,
                            "startedAt": "2026-03-19T12:03:10Z",
                            "finishedAt": "2026-03-19T12:03:40Z",
                            "stdoutTail": "updated",
                            "stderrTail": "",
                        }
                    ],
                    "artifacts": [
                        {
                            "path": "metrics.json",
                            "exists": True,
                            "sha256": "abc123",
                            "modifiedAt": "2026-03-19T12:03:50Z",
                        }
                    ],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(developer_control_plane_api, "MISSION_EVIDENCE_DIR", mission_dir)

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/jobs/overnight-lane-control-plane-token1234/closeout-receipt"
    )

    assert response.status_code == 200
    assert response.json() == {
        "exists": True,
        "queue_job_id": "overnight-lane-control-plane-token1234",
        "mission_id": "runtime-mission-control-plane-token1234",
        "producer_key": "openclaw-runtime",
        "source_lane_id": "control-plane",
        "source_board_concurrency_token": "token-1234",
        "runtime_profile_id": "bijmantra-bca-local-verify",
        "runtime_policy_sha256": "policy-sha-1234",
        "closeout_status": "passed",
        "state_refresh_required": True,
        "receipt_recorded_at": "2026-03-19T12:05:00Z",
        "started_at": "2026-03-19T12:03:00Z",
        "finished_at": "2026-03-19T12:04:00Z",
        "verification_evidence_ref": "runtime-artifacts/mission-evidence/job/verification_1.json",
        "queue_sha256_at_closeout": "queue-sha-closeout-77",
        "closeout_commands": [
            {
                "command": "make update-state",
                "passed": True,
                "exit_code": 0,
                "started_at": "2026-03-19T12:03:10Z",
                "finished_at": "2026-03-19T12:03:40Z",
                "stdout_tail": "updated",
                "stderr_tail": "",
            }
        ],
        "artifacts": [
            {
                "path": "metrics.json",
                "exists": True,
                "sha256": "abc123",
                "modified_at": "2026-03-19T12:03:50Z",
            }
        ],
    }


async def test_watchdog_status_returns_exists_false_when_missing(superuser_client, tmp_path, monkeypatch):
    watchdog_state_path = tmp_path / "watchdog-state.json"
    mission_dir = tmp_path / "mission-evidence"
    monkeypatch.setattr(developer_control_plane_api, "WATCHDOG_STATE_PATH", watchdog_state_path)
    monkeypatch.setattr(developer_control_plane_api, "MISSION_EVIDENCE_DIR", mission_dir)
    monkeypatch.setattr(
        developer_control_plane_api,
        "runtime_watchdog_state_freshness",
        lambda _last_check: (None, False),
    )

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/watchdog-status"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["exists"] is False
    assert payload["state_path"] == "runtime-artifacts/watchdog-state.json"
    assert payload["auth_store_exists"] is False
    assert payload["auth_store_path"] == "runtime-artifacts/agents/main/agent/auth-profiles.json"
    assert payload["bootstrap_ready"] is False
    assert payload["bootstrap_status"] == "auth-store-missing"
    assert payload["mission_evidence_dir_exists"] is False
    assert payload["mission_evidence_dir_path"] == "runtime-artifacts/mission-evidence"
    assert payload["last_check"] is None
    assert payload["state_age_seconds"] is None
    assert payload["state_is_stale"] is False
    assert payload["gateway_healthy"] is None
    assert payload["total_checks"] == 0
    assert payload["total_alerts"] == 0
    assert payload["job_count"] == 0
    assert payload["jobs"] == []
    assert payload["completion_assist_advisory"] is None


async def test_watchdog_status_returns_live_runtime_projection(superuser_client, tmp_path, monkeypatch):
    watchdog_state_path = tmp_path / "watchdog-state.json"
    auth_store_path = tmp_path / "agents" / "main" / "agent" / "auth-profiles.json"
    mission_dir = tmp_path / "mission-evidence"
    mission_dir.mkdir(parents=True, exist_ok=True)
    auth_store_path.parent.mkdir(parents=True, exist_ok=True)
    auth_store_path.write_text("[]\n", encoding="utf-8")
    watchdog_state_path.write_text(
        json.dumps(
            {
                "lastCheck": "2026-03-20T08:29:26.506880+00:00",
                "gatewayHealthy": True,
                "totalChecks": 3,
                "totalAlerts": 1,
                "jobs": [
                    {
                        "jobId": "overnight-lane-platform-runtime-token1234",
                        "label": "bijmantra:overnight-lane-platform-runtime-token1234",
                        "status": "completed",
                        "startedAt": "2026-03-20T08:00:00+00:00",
                        "durationMinutes": 12.5,
                        "lastError": "",
                        "consecutiveErrors": 0,
                        "branch": "auto/overnight-lane-platform-runtime-token1234",
                        "verificationPassed": True,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(developer_control_plane_api, "WATCHDOG_STATE_PATH", watchdog_state_path)
    monkeypatch.setattr(developer_control_plane_api, "MISSION_EVIDENCE_DIR", mission_dir)
    monkeypatch.setattr(
        developer_control_plane_api,
        "runtime_watchdog_state_freshness",
        lambda _last_check: (30, False),
    )

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/watchdog-status"
    )

    assert response.status_code == 200
    assert response.json() == {
        "exists": True,
        "state_path": "runtime-artifacts/watchdog-state.json",
        "auth_store_exists": True,
        "auth_store_path": "runtime-artifacts/agents/main/agent/auth-profiles.json",
        "bootstrap_ready": True,
        "bootstrap_status": "ready",
        "mission_evidence_dir_exists": True,
        "mission_evidence_dir_path": "runtime-artifacts/mission-evidence",
        "last_check": "2026-03-20T08:29:26.506880+00:00",
        "state_age_seconds": 30,
        "state_is_stale": False,
        "gateway_healthy": True,
        "total_checks": 3,
        "total_alerts": 1,
        "job_count": 1,
        "jobs": [
            {
                "job_id": "overnight-lane-platform-runtime-token1234",
                "label": "bijmantra:overnight-lane-platform-runtime-token1234",
                "status": "completed",
                "started_at": "2026-03-20T08:00:00+00:00",
                "duration_minutes": 12.5,
                "last_error": "",
                "consecutive_errors": 0,
                "branch": "auto/overnight-lane-platform-runtime-token1234",
                "verification_passed": True,
            }
        ],
        "completion_assist_advisory": None,
    }


async def test_watchdog_status_marks_stale_runtime_projection(superuser_client, tmp_path, monkeypatch):
    watchdog_state_path = tmp_path / "watchdog-state.json"
    mission_dir = tmp_path / "mission-evidence"
    mission_dir.mkdir(parents=True, exist_ok=True)
    watchdog_state_path.write_text(
        json.dumps(
            {
                "lastCheck": "2026-03-20T08:29:26.506880+00:00",
                "gatewayHealthy": True,
                "totalChecks": 3,
                "totalAlerts": 1,
                "jobs": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(developer_control_plane_api, "WATCHDOG_STATE_PATH", watchdog_state_path)
    monkeypatch.setattr(developer_control_plane_api, "MISSION_EVIDENCE_DIR", mission_dir)
    monkeypatch.setattr(
        developer_control_plane_api,
        "runtime_watchdog_state_freshness",
        lambda _last_check: (900, True),
    )

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/watchdog-status"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["exists"] is True
    assert payload["last_check"] == "2026-03-20T08:29:26.506880+00:00"
    assert payload["state_age_seconds"] == 900
    assert payload["state_is_stale"] is True
    assert payload["gateway_healthy"] is True
    assert payload["completion_assist_advisory"] is None


async def test_watchdog_status_projects_completion_assist_advisory(
    superuser_client, tmp_path, monkeypatch
):
    watchdog_state_path = tmp_path / "watchdog-state.json"
    mission_dir = tmp_path / "mission-evidence"
    mission_dir.mkdir(parents=True, exist_ok=True)
    watchdog_state_path.write_text(
        json.dumps(
            {
                "lastCheck": "2026-04-06T11:44:45.735514+00:00",
                "gatewayHealthy": False,
                "totalChecks": 2,
                "totalAlerts": 1,
                "jobs": [],
                "advisoryInputs": {
                    "completionAssist": {
                        "authority": "advisory-only-derived",
                        "observedFromPath": ".github/docs/architecture/tracking/current-app-state.json",
                        "available": True,
                        "artifactPath": ".github/docs/architecture/tracking/developer-control-plane-completion-assist.json",
                        "status": "staged",
                        "staged": True,
                        "explicitWriteRequired": True,
                        "message": "Staged reviewed completion assist for lane control-plane. This artifact does not perform explicit board write-back.",
                        "sourceLaneId": "control-plane",
                        "queueJobId": "overnight-lane-control-plane-token1234",
                        "draftSource": "stable-closeout-receipt",
                        "receiptPath": "runtime-artifacts/mission-evidence/control-plane/closeout.json",
                        "sourceEndpoint": "http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
                        "autonomyCycleArtifactPath": ".github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json",
                        "nextActionOrderingSource": "canonical-learning-exact-runtime",
                        "matchedSelectedJobIds": ["overnight-lane-control-plane-token1234"],
                    }
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(developer_control_plane_api, "WATCHDOG_STATE_PATH", watchdog_state_path)
    monkeypatch.setattr(developer_control_plane_api, "MISSION_EVIDENCE_DIR", mission_dir)
    monkeypatch.setattr(
        developer_control_plane_api,
        "runtime_watchdog_state_freshness",
        lambda _last_check: (45, False),
    )

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/watchdog-status"
    )

    assert response.status_code == 200
    assert response.json()["completion_assist_advisory"] == {
        "authority": "advisory-only-derived",
        "observed_from_path": ".github/docs/architecture/tracking/current-app-state.json",
        "available": True,
        "artifact_path": ".github/docs/architecture/tracking/developer-control-plane-completion-assist.json",
        "status": "staged",
        "staged": True,
        "explicit_write_required": True,
        "message": "Staged reviewed completion assist for lane control-plane. This artifact does not perform explicit board write-back.",
        "source_lane_id": "control-plane",
        "queue_job_id": "overnight-lane-control-plane-token1234",
        "draft_source": "stable-closeout-receipt",
        "receipt_path": "runtime-artifacts/mission-evidence/control-plane/closeout.json",
        "source_endpoint": "http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
        "autonomy_cycle_artifact_path": ".github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json",
        "next_action_ordering_source": "canonical-learning-exact-runtime",
        "matched_selected_job_ids": ["overnight-lane-control-plane-token1234"],
    }


async def test_runtime_autonomy_cycle_returns_exists_false_when_missing(
    superuser_client, tmp_path, monkeypatch
):
    autonomy_cycle_path = tmp_path / "developer-control-plane-autonomy-cycle.json"
    monkeypatch.setattr(developer_control_plane_api, "AUTONOMY_CYCLE_PATH", autonomy_cycle_path)

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/autonomy-cycle"
    )

    assert response.status_code == 200
    assert response.json() == {
        "exists": False,
        "artifact_path": str(autonomy_cycle_path),
        "generated_at": None,
        "queue_path": None,
        "window": None,
        "max_jobs_per_run": 0,
        "status_counts": {},
        "selected_job_count": 0,
        "blocked_job_count": 0,
        "closeout_candidate_count": 0,
        "next_action_count": 0,
        "next_action_ordering_source": "artifact",
        "watchdog": {
            "exists": False,
            "state_path": "runtime-artifacts/watchdog-state.json",
            "last_check": None,
            "gateway_healthy": None,
            "state_is_stale": False,
            "total_alerts": 0,
            "job_errors": {},
        },
        "selected_jobs": [],
        "blocked_jobs": [],
        "closeout_candidates": [],
        "next_actions": [],
        "first_actionable_completion_write": None,
    }


async def test_runtime_completion_assist_returns_exists_false_when_missing(
    superuser_client, tmp_path, monkeypatch
):
    completion_assist_path = tmp_path / "developer-control-plane-completion-assist.json"
    monkeypatch.setattr(
        developer_control_plane_api, "COMPLETION_ASSIST_PATH", completion_assist_path
    )

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/completion-assist"
    )

    assert response.status_code == 200
    assert response.json() == {
        "exists": False,
        "artifact_path": str(completion_assist_path),
        "generated_at": None,
        "status": None,
        "staged": False,
        "explicit_write_required": True,
        "message": None,
        "source": None,
        "actionable_completion_write": None,
    }


async def test_runtime_autonomy_cycle_returns_normalized_projection(
    superuser_client, tmp_path, monkeypatch
):
    autonomy_cycle_path = tmp_path / "developer-control-plane-autonomy-cycle.json"
    autonomy_cycle_path.write_text(
        json.dumps(
            {
                "generatedAt": "2026-04-05T11:10:24.399975+00:00",
                "queuePath": ".agent/jobs/overnight-queue.json",
                "window": "nightly",
                "maxJobsPerRun": 2,
                "statusCounts": {"queued": 9},
                "selectedJobCount": 1,
                "blockedJobCount": 1,
                "closeoutCandidateCount": 1,
                "nextActionCount": 4,
                "watchdog": {
                    "exists": True,
                    "statePath": "runtime-artifacts/watchdog-state.json",
                    "lastCheck": "2026-04-05T10:00:00Z",
                    "gatewayHealthy": False,
                    "stateIsStale": True,
                    "totalAlerts": 2,
                    "jobErrors": {
                        "runtime-job": {
                            "lastError": "verification failed",
                            "consecutiveErrors": 3,
                        }
                    },
                },
                "selectedJobs": [
                    {
                        "jobId": "closeout-follow-up",
                        "title": "Closeout Follow Up",
                        "sourceLaneId": "platform-runtime",
                        "priority": "p1",
                        "primaryAgent": "OmShriMaatreNamaha",
                        "triggerReason": "closeout-receipt:runtime-job:passed",
                        "sourceTask": ".ai/tasks/example.md",
                    }
                ],
                "blockedJobs": [
                    {
                        "jobId": "watchdog-remediation",
                        "title": "Watchdog Remediation",
                        "sourceLaneId": "cross-domain-hub",
                        "reason": "trigger-disabled",
                    }
                ],
                "closeoutCandidates": [
                    {
                        "jobId": "runtime-job",
                        "title": "Runtime Job",
                        "sourceLaneId": "control-plane",
                        "queueStatus": "completed",
                        "closeoutStatus": "passed",
                        "missionId": "mission-runtime-job",
                        "verificationEvidenceRef": "runtime-artifacts/mission-evidence/runtime-job/verification_1.json",
                        "path": "runtime-artifacts/mission-evidence/runtime-job/closeout.json",
                    }
                ],
                "nextActions": [
                    {
                        "action": "dispatch-queue-job",
                        "jobId": "closeout-follow-up",
                        "title": "Closeout Follow Up",
                        "sourceLaneId": "platform-runtime",
                        "reason": "closeout-receipt:runtime-job:passed",
                        "primaryAgent": "OmShriMaatreNamaha",
                        "priority": "p1",
                    },
                    {
                        "action": "review-closeout-receipt",
                        "jobId": "runtime-job",
                        "title": "Runtime Job",
                        "sourceLaneId": "control-plane",
                        "reason": "stable closeout receipt observed (passed)",
                        "missionId": "mission-runtime-job",
                        "receiptPath": "runtime-artifacts/mission-evidence/runtime-job/closeout.json",
                    },
                    {
                        "action": "prepare-completion-write-back",
                        "jobId": "runtime-job",
                        "title": "Runtime Job",
                        "sourceLaneId": "control-plane",
                        "reason": "stable closeout ready for explicit board write-back",
                        "missionId": "mission-runtime-job",
                        "receiptPath": "runtime-artifacts/mission-evidence/runtime-job/closeout.json",
                        "detail": {
                            "queueStatus": "completed",
                            "closeoutStatus": "passed",
                            "verificationEvidenceRef": "runtime-artifacts/mission-evidence/runtime-job/verification_1.json",
                        },
                    },
                    {
                        "action": "investigate-watchdog-job",
                        "jobId": "runtime-job",
                        "sourceLaneId": "control-plane",
                        "reason": "watchdog-job-error",
                        "detail": {
                            "lastError": "verification failed",
                            "consecutiveErrors": 3,
                        },
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(developer_control_plane_api, "AUTONOMY_CYCLE_PATH", autonomy_cycle_path)

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/autonomy-cycle"
    )

    assert response.status_code == 200
    assert response.json() == {
        "exists": True,
        "artifact_path": str(autonomy_cycle_path),
        "generated_at": "2026-04-05T11:10:24.399975+00:00",
        "queue_path": ".agent/jobs/overnight-queue.json",
        "window": "nightly",
        "max_jobs_per_run": 2,
        "status_counts": {"queued": 9},
        "selected_job_count": 1,
        "blocked_job_count": 1,
        "closeout_candidate_count": 1,
        "next_action_count": 4,
        "next_action_ordering_source": "artifact",
        "watchdog": {
            "exists": True,
            "state_path": "runtime-artifacts/watchdog-state.json",
            "last_check": "2026-04-05T10:00:00Z",
            "gateway_healthy": False,
            "state_is_stale": True,
            "total_alerts": 2,
            "job_errors": {
                "runtime-job": {
                    "last_error": "verification failed",
                    "consecutive_errors": 3,
                }
            },
        },
        "selected_jobs": [
            {
                "job_id": "closeout-follow-up",
                "title": "Closeout Follow Up",
                "source_lane_id": "platform-runtime",
                "priority": "p1",
                "primary_agent": "OmShriMaatreNamaha",
                "trigger_reason": "closeout-receipt:runtime-job:passed",
                "source_task": ".ai/tasks/example.md",
            }
        ],
        "blocked_jobs": [
            {
                "job_id": "watchdog-remediation",
                "title": "Watchdog Remediation",
                "source_lane_id": "cross-domain-hub",
                "reason": "trigger-disabled",
            }
        ],
        "closeout_candidates": [
            {
                "job_id": "runtime-job",
                "title": "Runtime Job",
                "source_lane_id": "control-plane",
                "queue_status": "completed",
                "closeout_status": "passed",
                "mission_id": "mission-runtime-job",
                "verification_evidence_ref": "runtime-artifacts/mission-evidence/runtime-job/verification_1.json",
                "path": "runtime-artifacts/mission-evidence/runtime-job/closeout.json",
            }
        ],
        "next_actions": [
            {
                "action": "dispatch-queue-job",
                "job_id": "closeout-follow-up",
                "title": "Closeout Follow Up",
                "source_lane_id": "platform-runtime",
                "reason": "closeout-receipt:runtime-job:passed",
                "primary_agent": "OmShriMaatreNamaha",
                "priority": "p1",
                "mission_id": None,
                "receipt_path": None,
                "state_path": None,
                "detail": None,
            },
            {
                "action": "review-closeout-receipt",
                "job_id": "runtime-job",
                "title": "Runtime Job",
                "source_lane_id": "control-plane",
                "reason": "stable closeout receipt observed (passed)",
                "primary_agent": None,
                "priority": None,
                "mission_id": "mission-runtime-job",
                "receipt_path": "runtime-artifacts/mission-evidence/runtime-job/closeout.json",
                "state_path": None,
                "detail": None,
            },
            {
                "action": "prepare-completion-write-back",
                "job_id": "runtime-job",
                "title": "Runtime Job",
                "source_lane_id": "control-plane",
                "reason": "stable closeout ready for explicit board write-back",
                "primary_agent": None,
                "priority": None,
                "mission_id": "mission-runtime-job",
                "receipt_path": "runtime-artifacts/mission-evidence/runtime-job/closeout.json",
                "state_path": None,
                "detail": {
                    "queueStatus": "completed",
                    "closeoutStatus": "passed",
                    "verificationEvidenceRef": "runtime-artifacts/mission-evidence/runtime-job/verification_1.json",
                },
            },
            {
                "action": "investigate-watchdog-job",
                "job_id": "runtime-job",
                "title": None,
                "source_lane_id": "control-plane",
                "reason": "watchdog-job-error",
                "primary_agent": None,
                "priority": None,
                "mission_id": None,
                "receipt_path": None,
                "state_path": None,
                "detail": {
                    "lastError": "verification failed",
                    "consecutiveErrors": 3,
                },
            },
        ],
        "first_actionable_completion_write": None,
    }


async def test_runtime_completion_assist_returns_normalized_projection(
    superuser_client, tmp_path, monkeypatch
):
    completion_assist_path = tmp_path / "developer-control-plane-completion-assist.json"
    completion_assist_path.write_text(
        json.dumps(
            {
                "generatedAt": "2026-04-06T12:05:00+00:00",
                "status": "staged",
                "staged": True,
                "explicitWriteRequired": True,
                "message": "Staged reviewed completion assist for lane control-plane. This artifact does not perform explicit board write-back.",
                "source": {
                    "endpoint": "http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
                    "autonomy_cycle_artifact_path": ".github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json",
                    "autonomy_cycle_generated_at": "2026-04-06T12:00:00+00:00",
                    "next_action_ordering_source": "canonical-learning-exact-runtime",
                },
                "actionableCompletionWrite": {
                    "action": "prepare-completion-write-back",
                    "actionIndex": 0,
                    "jobId": "overnight-lane-control-plane-token1234",
                    "sourceLaneId": "control-plane",
                    "reason": "stable closeout ready for explicit board write-back",
                    "missionId": "runtime-mission-control-plane-token1234",
                    "receiptPath": "runtime-artifacts/mission-evidence/job/closeout.json",
                    "draftSource": "stable-closeout-receipt",
                    "queueStatus": {
                        "queue_path": ".agent/jobs/overnight-queue.json",
                        "queue_sha256": "queue-sha-77",
                        "exists": True,
                        "job_count": 1,
                        "updated_at": "2026-04-06T11:30:00+00:00",
                    },
                    "closeoutReceipt": {
                        "exists": True,
                        "queue_job_id": "overnight-lane-control-plane-token1234",
                    },
                    "preparedRequest": {
                        "source_board_concurrency_token": "token-1234",
                        "expected_queue_sha256": "queue-sha-77",
                        "operator_intent": "write-reviewed-lane-completion",
                    },
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        developer_control_plane_api, "COMPLETION_ASSIST_PATH", completion_assist_path
    )

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/completion-assist"
    )

    assert response.status_code == 200
    assert response.json() == {
        "exists": True,
        "artifact_path": str(completion_assist_path),
        "generated_at": "2026-04-06T12:05:00+00:00",
        "status": "staged",
        "staged": True,
        "explicit_write_required": True,
        "message": "Staged reviewed completion assist for lane control-plane. This artifact does not perform explicit board write-back.",
        "source": {
            "endpoint": "http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
            "autonomy_cycle_artifact_path": ".github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json",
            "autonomy_cycle_generated_at": "2026-04-06T12:00:00+00:00",
            "next_action_ordering_source": "canonical-learning-exact-runtime",
        },
        "actionable_completion_write": {
            "action": "prepare-completion-write-back",
            "actionIndex": 0,
            "jobId": "overnight-lane-control-plane-token1234",
            "sourceLaneId": "control-plane",
            "reason": "stable closeout ready for explicit board write-back",
            "missionId": "runtime-mission-control-plane-token1234",
            "receiptPath": "runtime-artifacts/mission-evidence/job/closeout.json",
            "draftSource": "stable-closeout-receipt",
            "queueStatus": {
                "queue_path": ".agent/jobs/overnight-queue.json",
                "queue_sha256": "queue-sha-77",
                "exists": True,
                "job_count": 1,
                "updated_at": "2026-04-06T11:30:00+00:00",
            },
            "closeoutReceipt": {
                "exists": True,
                "queue_job_id": "overnight-lane-control-plane-token1234",
            },
            "preparedRequest": {
                "source_board_concurrency_token": "token-1234",
                "expected_queue_sha256": "queue-sha-77",
                "operator_intent": "write-reviewed-lane-completion",
            },
        },
    }


async def test_runtime_autonomy_cycle_embeds_completion_write_preparation_when_board_exists(
    superuser_client, tmp_path, monkeypatch
):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    queue_job_id = f"overnight-lane-control-plane-{board_token.lower().replace('-', '')[:8]}"
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(
        queue_path,
        _queue_payload(job_id=queue_job_id, include_job=True, status="completed"),
    )
    mission_dir = tmp_path / "mission-evidence"
    _write_closeout_receipt_file(mission_dir, queue_job_id)

    autonomy_cycle_path = tmp_path / "developer-control-plane-autonomy-cycle.json"
    autonomy_cycle_path.write_text(
        json.dumps(
            {
                "generatedAt": "2026-04-05T11:10:24.399975+00:00",
                "queuePath": ".agent/jobs/overnight-queue.json",
                "window": "nightly",
                "maxJobsPerRun": 2,
                "statusCounts": {"completed": 1},
                "selectedJobCount": 0,
                "blockedJobCount": 0,
                "closeoutCandidateCount": 1,
                "nextActionCount": 1,
                "watchdog": {
                    "exists": True,
                    "statePath": "runtime-artifacts/watchdog-state.json",
                    "lastCheck": "2026-04-05T10:00:00Z",
                    "gatewayHealthy": True,
                    "stateIsStale": False,
                    "totalAlerts": 0,
                    "jobErrors": {},
                },
                "selectedJobs": [],
                "blockedJobs": [],
                "closeoutCandidates": [
                    {
                        "jobId": queue_job_id,
                        "title": "Runtime Job",
                        "sourceLaneId": "control-plane",
                        "queueStatus": "completed",
                        "closeoutStatus": "passed",
                        "missionId": "mission-runtime-job",
                        "verificationEvidenceRef": "runtime-artifacts/mission-evidence/job/verification_1.json",
                        "path": f"runtime-artifacts/mission-evidence/{queue_job_id}/closeout.json",
                    }
                ],
                "nextActions": [
                    {
                        "action": "prepare-completion-write-back",
                        "jobId": queue_job_id,
                        "title": "Runtime Job",
                        "sourceLaneId": "control-plane",
                        "reason": "stable closeout ready for explicit board write-back",
                        "missionId": "mission-runtime-job",
                        "receiptPath": f"runtime-artifacts/mission-evidence/{queue_job_id}/closeout.json",
                        "detail": {
                            "queueStatus": "completed",
                            "closeoutStatus": "passed",
                            "verificationEvidenceRef": "runtime-artifacts/mission-evidence/job/verification_1.json",
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(developer_control_plane_api, "AUTONOMY_CYCLE_PATH", autonomy_cycle_path)
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)
    monkeypatch.setattr(developer_control_plane_api, "MISSION_EVIDENCE_DIR", mission_dir)

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/autonomy-cycle"
    )

    assert response.status_code == 200
    payload = response.json()
    action = payload["next_actions"][0]
    preparation = action["detail"]["completionWritePreparation"]
    resolved = payload["first_actionable_completion_write"]
    assert action["action"] == "prepare-completion-write-back"
    assert action["detail"]["queueStatus"] == "completed"
    assert resolved == {
        "action": "prepare-completion-write-back",
        "action_index": 0,
        "job_id": queue_job_id,
        "source_lane_id": "control-plane",
        "reason": "stable closeout ready for explicit board write-back",
        "mission_id": "mission-runtime-job",
        "receipt_path": f"runtime-artifacts/mission-evidence/{queue_job_id}/closeout.json",
        "preparation": preparation,
    }
    assert preparation["source_lane_id"] == "control-plane"
    assert preparation["queue_job_id"] == queue_job_id
    assert preparation["draft_source"] == "stable-closeout-receipt"
    assert preparation["queue_status"] == {
        "queue_path": str(queue_path),
        "queue_sha256": preparation["queue_status"]["queue_sha256"],
        "exists": True,
        "job_count": 1,
        "updated_at": "2026-03-18T00:00:00Z",
    }
    assert preparation["closeout_receipt"]["exists"] is True
    assert preparation["closeout_receipt"]["queue_job_id"] == queue_job_id
    assert preparation["closeout_receipt"]["source_board_concurrency_token"] == "token-1234"
    assert preparation["closeout_receipt"]["artifacts"] == [
        {
            "path": "metrics.json",
            "exists": True,
            "sha256": "abc123",
            "modified_at": "2026-03-19T12:03:50Z",
        }
    ]
    assert preparation["prepared_request"] == {
        "source_board_concurrency_token": board_token,
        "expected_queue_sha256": preparation["queue_status"]["queue_sha256"],
        "operator_intent": "write-reviewed-lane-completion",
        "completion": {
            "source_lane_id": "control-plane",
            "queue_job_id": queue_job_id,
            "closure_summary": "Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.",
            "evidence": [
                f"Reviewed queue job {queue_job_id} using watchdog closeout receipt before explicit board write-back.",
                "Watchdog closeout queue hash: queue-sha-closeout-77.",
                f"Board token used for reviewed closeout: {board_token}.",
                "Runtime profile recorded by closeout receipt: bijmantra-bca-local-verify.",
                "Verification evidence referenced by closeout receipt: runtime-artifacts/mission-evidence/job/verification_1.json.",
                "Closeout artifact refreshed: metrics.json.",
                "Stable closeout receipt recorded at 2026-03-19T12:05:00Z.",
            ],
            "closeout_receipt": _completion_closeout_receipt_payload(queue_job_id),
        },
    }


async def test_runtime_autonomy_cycle_biases_next_action_order_from_canonical_learnings(
    superuser_client, async_db_session, test_superuser, tmp_path, monkeypatch
):
    autonomy_cycle_path = tmp_path / "developer-control-plane-autonomy-cycle.json"
    autonomy_cycle_path.write_text(
        json.dumps(
            {
                "generatedAt": "2026-04-05T11:10:24.399975+00:00",
                "queuePath": ".agent/jobs/overnight-queue.json",
                "window": "nightly",
                "maxJobsPerRun": 2,
                "statusCounts": {"queued": 9},
                "selectedJobCount": 1,
                "blockedJobCount": 1,
                "closeoutCandidateCount": 1,
                "nextActionCount": 4,
                "watchdog": {
                    "exists": True,
                    "statePath": "runtime-artifacts/watchdog-state.json",
                    "lastCheck": "2026-04-05T10:00:00Z",
                    "gatewayHealthy": False,
                    "stateIsStale": True,
                    "totalAlerts": 2,
                    "jobErrors": {
                        "runtime-job": {
                            "lastError": "verification failed",
                            "consecutiveErrors": 3,
                        }
                    },
                },
                "selectedJobs": [
                    {
                        "jobId": "closeout-follow-up",
                        "title": "Closeout Follow Up",
                        "sourceLaneId": "platform-runtime",
                        "priority": "p1",
                        "primaryAgent": "OmShriMaatreNamaha",
                        "triggerReason": "closeout-receipt:runtime-job:passed",
                        "sourceTask": ".ai/tasks/example.md",
                    }
                ],
                "blockedJobs": [
                    {
                        "jobId": "watchdog-remediation",
                        "title": "Watchdog Remediation",
                        "sourceLaneId": "cross-domain-hub",
                        "reason": "trigger-disabled",
                    }
                ],
                "closeoutCandidates": [
                    {
                        "jobId": "runtime-job",
                        "title": "Runtime Job",
                        "sourceLaneId": "control-plane",
                        "queueStatus": "completed",
                        "closeoutStatus": "passed",
                        "missionId": "mission-runtime-job",
                        "verificationEvidenceRef": "runtime-artifacts/mission-evidence/runtime-job/verification_1.json",
                        "path": "runtime-artifacts/mission-evidence/runtime-job/closeout.json",
                    }
                ],
                "nextActions": [
                    {
                        "action": "dispatch-queue-job",
                        "jobId": "closeout-follow-up",
                        "title": "Closeout Follow Up",
                        "sourceLaneId": "platform-runtime",
                        "reason": "closeout-receipt:runtime-job:passed",
                        "primaryAgent": "OmShriMaatreNamaha",
                        "priority": "p1",
                    },
                    {
                        "action": "review-closeout-receipt",
                        "jobId": "runtime-job",
                        "title": "Runtime Job",
                        "sourceLaneId": "control-plane",
                        "reason": "stable closeout receipt observed (passed)",
                        "missionId": "mission-runtime-job",
                        "receiptPath": "runtime-artifacts/mission-evidence/runtime-job/closeout.json",
                    },
                    {
                        "action": "prepare-completion-write-back",
                        "jobId": "runtime-job",
                        "title": "Runtime Job",
                        "sourceLaneId": "control-plane",
                        "reason": "stable closeout ready for explicit board write-back",
                        "missionId": "mission-runtime-job",
                        "receiptPath": "runtime-artifacts/mission-evidence/runtime-job/closeout.json",
                        "detail": {
                            "queueStatus": "completed",
                            "closeoutStatus": "passed",
                            "verificationEvidenceRef": "runtime-artifacts/mission-evidence/runtime-job/verification_1.json",
                        },
                    },
                    {
                        "action": "investigate-watchdog-job",
                        "jobId": "runtime-job",
                        "sourceLaneId": "control-plane",
                        "reason": "watchdog-job-error",
                        "detail": {
                            "lastError": "verification failed",
                            "consecutiveErrors": 3,
                        },
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(developer_control_plane_api, "AUTONOMY_CYCLE_PATH", autonomy_cycle_path)

    async_db_session.add(
        DeveloperControlPlaneLearningEntry(
            organization_id=test_superuser.organization_id,
            entry_type="pattern",
            source_classification="reviewed-completion-writeback",
            title="Reviewed completion write-back closed lane control-plane",
            summary="Explicit reviewed completion write-back persisted canonical closure for lane control-plane.",
            confidence_score=0.94,
            recorded_by_user_id=test_superuser.id,
            recorded_by_email=test_superuser.email,
            board_id="bijmantra-app-development-master-board",
            source_lane_id="control-plane",
            queue_job_id="runtime-job",
            linked_mission_id="mission-runtime-job",
            approval_receipt_id=77,
            source_reference="approval-receipt:77:reviewed-completion-writeback",
            evidence_refs=["receipt:77"],
            summary_metadata={"seed_source": "approval-receipt"},
        )
    )
    await async_db_session.commit()

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/autonomy-cycle"
    )

    assert response.status_code == 200
    assert response.json()["next_action_ordering_source"] == "canonical-learning-exact-runtime"
    assert [action["action"] for action in response.json()["next_actions"]] == [
        "prepare-completion-write-back",
        "review-closeout-receipt",
        "dispatch-queue-job",
        "investigate-watchdog-job",
    ]
    assert response.json()["first_actionable_completion_write"] is None



async def test_silent_monitors_report_evidence_without_mutating_queue(
    superuser_client, tmp_path, monkeypatch
):
    queue_path = tmp_path / "overnight-queue.json"
    queue_payload = _queue_payload(job_id="overnight-lane-control-plane-token1234")
    queue_payload["updatedAt"] = datetime.now(UTC).isoformat()
    _write_queue_file(queue_path, queue_payload)
    original_queue_contents = queue_path.read_text(encoding="utf-8")

    control_surface_script = tmp_path / "check_control_surfaces.py"
    control_surface_script.write_text("print('ok')\n", encoding="utf-8")

    reevu_real_question_path = tmp_path / "reevu_real_question_local.json"
    reevu_real_question_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-03-31T07:21:06.334144+00:00",
                "runtime_status": "blocked",
                "passed_cases": 3,
                "total_cases": 14,
                "pass_rate": 0.2143,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    reevu_readiness_census_path = tmp_path / "reevu_local_readiness_census.json"
    reevu_readiness_census_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-03-31T07:21:06.364691+00:00",
                "benchmark_ready_organization_ids": [2],
                "organizations": [
                    {
                        "organization_id": 1,
                        "organization_name": "Default Organization",
                        "runtime_status": "blocked",
                        "readiness_blockers": [
                            "observations.empty",
                            "bio_gwas_runs.empty",
                            "bio_qtls.missing_or_inaccessible",
                        ],
                        "readiness_warnings": ["germplasm.sparse", "trials.sparse"],
                    },
                    {
                        "organization_id": 2,
                        "organization_name": "Demo Organization",
                        "runtime_status": "ready",
                        "readiness_blockers": [],
                        "readiness_warnings": ["trials.sparse"],
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    reevu_authority_gap_path = tmp_path / "reevu_authority_gap_report.json"
    reevu_authority_gap_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-03-31T07:21:08.675466+00:00",
                "overall_gap_status": "no_benchmark_ready_local_org",
                "selected_local_org_blockers": [
                    "observations.empty",
                    "bio_gwas_runs.empty",
                    "bio_qtls.missing_or_inaccessible",
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    run_calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_subprocess_run(command, **kwargs):
        run_calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="Control surfaces are structurally valid and aligned with the current repo layout.\n",
            stderr="",
        )

    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)
    monkeypatch.setattr(
        developer_control_plane_api,
        "CONTROL_SURFACE_CHECK_SCRIPT",
        control_surface_script,
    )
    monkeypatch.setattr(
        developer_control_plane_api,
        "REEVU_REAL_QUESTION_REPORT_PATH",
        reevu_real_question_path,
    )
    monkeypatch.setattr(
        developer_control_plane_api,
        "REEVU_READINESS_CENSUS_PATH",
        reevu_readiness_census_path,
    )
    monkeypatch.setattr(
        developer_control_plane_api,
        "REEVU_AUTHORITY_GAP_REPORT_PATH",
        reevu_authority_gap_path,
    )
    monkeypatch.setattr(developer_control_plane_api.subprocess, "run", fake_subprocess_run)

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/silent-monitors"
    )

    assert response.status_code == 200
    payload = response.json()
    monitors = {monitor["monitor_key"]: monitor for monitor in payload["monitors"]}

    assert payload["overall_state"] == "alert"
    assert payload["should_emit"] is True
    assert monitors["queue-staleness"]["state"] == "healthy"
    assert monitors["queue-staleness"]["mutates_authority_surfaces"] is False
    assert monitors["control-surface-drift"]["state"] == "healthy"
    assert monitors["control-surface-drift"]["detail"] == (
        "Control surfaces are structurally valid and aligned with the current repo layout."
    )
    assert monitors["reevu-readiness"]["state"] == "alert"
    assert "ready local orgs: 2 (Demo Organization)" in monitors["reevu-readiness"]["detail"]
    assert monitors["reevu-readiness"]["findings"] == [
        "observations.empty",
        "bio_gwas_runs.empty",
        "bio_qtls.missing_or_inaccessible",
    ]
    assert queue_path.read_text(encoding="utf-8") == original_queue_contents
    assert len(run_calls) == 1
    assert run_calls[0][0][1] == str(control_surface_script)


async def test_runtime_mission_state_returns_empty_when_no_missions(superuser_client):
    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/mission-state"
    )

    assert response.status_code == 200
    assert response.json() == {"count": 0, "missions": []}


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/api/v2/developer-control-plane/runtime/mission-state", None),
        (
            "post",
            "/api/v2/developer-control-plane/runtime/mission-state/bootstrap-closeout-receipt",
            {"queue_job_id": "overnight-lane-control-plane-token1234"},
        ),
        (
            "get",
            "/api/v2/developer-control-plane/runtime/mission-state/runtime-mission-control-plane-token1234",
            None,
        ),
    ],
)
async def test_runtime_mission_state_routes_return_503_when_schema_is_not_ready(
    superuser_client,
    monkeypatch,
    method,
    path,
    payload,
):
    async def _raise_schema_not_ready(_db):
        raise developer_control_plane_api.HTTPException(
            status_code=503,
            detail=(
                "Developer control-plane mission-state schema is not ready; "
                "missing column(s): orchestrator_missions.queue_job_id. "
                "Run backend alembic upgrade through revision 20260323_0100."
            ),
        )

    monkeypatch.setattr(
        developer_control_plane_api,
        "_ensure_mission_state_schema_ready",
        _raise_schema_not_ready,
    )

    request = getattr(superuser_client, method)
    response = await request(path, json=payload) if payload is not None else await request(path)

    assert response.status_code == 503
    assert "mission-state schema is not ready" in response.json()["detail"]


async def test_runtime_mission_state_returns_omshrimaatre_snapshots(
    superuser_client,
    async_db_session,
    test_superuser,
):
    repository = PostgresMissionStateRepository(
        async_db_session,
        organization_id=test_superuser.organization_id,
    )
    service = OrchestratorMissionStateService(repository)

    mission = await service.register_mission(
        objective="Control-plane reviewed dispatch runtime inspection",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="developer control-plane runtime inspection",
        producer_key="chaitanya",
    )
    subtask = await service.add_subtask(
        mission_id=mission.id,
        title="Inspect watchdog and mission evidence alignment",
        owner_role="OmVishnaveNamah",
    )
    await service.update_subtask_status(subtask.id, SubtaskStatus.COMPLETED)
    assignment = await service.assign_subtask(
        subtask_id=subtask.id,
        assigned_role="OmVishnaveNamah",
        handoff_reason="Validate runtime truth before pilot closeout",
    )
    await service.complete_assignment(assignment.id)
    await service.record_evidence(
        mission_id=mission.id,
        kind="runtime_watchdog",
        source_path="runtime-artifacts/watchdog-state.json",
        evidence_class="runtime-status",
        summary="Watchdog completed the reviewed queue job.",
    )
    await service.record_blocker(
        mission_id=mission.id,
        blocker_type="missing_closeout_receipt",
        impact="Stable runtime closeout receipt is not yet present.",
        escalation_needed=True,
    )
    await service.record_verification_run(
        subject_id=mission.id,
        verification_type="runtime_watchdog",
        result=VerificationResult.PASSED,
        evidence_ref="runtime-artifacts/watchdog-state.json",
    )
    mission = await service.complete_mission(
        mission.id,
        "Runtime watchdog and durable mission-state inspection recorded.",
    )
    await async_db_session.commit()

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/mission-state"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    mission_payload = payload["missions"][0]
    assert mission_payload["mission_id"] == mission.id
    assert mission_payload["objective"] == "Control-plane reviewed dispatch runtime inspection"
    assert mission_payload["status"] == "completed"
    assert mission_payload["owner"] == "OmShriMaatreNamaha"
    assert mission_payload["priority"] == "p1"
    assert mission_payload["producer_key"] == "chaitanya"
    assert mission_payload["queue_job_id"] is None
    assert mission_payload["source_lane_id"] is None
    assert mission_payload["source_board_concurrency_token"] is None
    assert _normalize_timestamp(mission_payload["created_at"]) == _normalize_timestamp(
        mission.created_at
    )
    assert _normalize_timestamp(mission_payload["updated_at"]) == _normalize_timestamp(
        mission.updated_at
    )
    assert mission_payload["subtask_total"] == 1
    assert mission_payload["subtask_completed"] == 1
    assert mission_payload["assignment_total"] == 1
    assert mission_payload["evidence_count"] == 1
    assert mission_payload["blocker_count"] == 1
    assert mission_payload["escalation_needed"] is True
    assert mission_payload["verification"] == {
        "passed": 1,
        "warned": 0,
        "failed": 0,
        "last_verified_at": mission_payload["verification"]["last_verified_at"],
    }
    assert mission_payload["final_summary"] == "Runtime watchdog and durable mission-state inspection recorded."


async def test_runtime_mission_state_filters_by_queue_job_and_lane(
    superuser_client,
    async_db_session,
    test_superuser,
):
    repository = PostgresMissionStateRepository(
        async_db_session,
        organization_id=test_superuser.organization_id,
    )
    service = OrchestratorMissionStateService(repository)

    linked_mission = await service.register_mission(
        mission_id="runtime-mission-control-plane-token1234",
        objective="Reviewed closeout persistence for lane Control Plane Lane",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="structured mission linkage",
        producer_key="openclaw-runtime",
        queue_job_id="overnight-lane-control-plane-token1234",
        source_lane_id="control-plane",
        source_board_concurrency_token="token-1234",
    )
    await service.complete_mission(linked_mission.id, "Linked mission is available.")

    other_mission = await service.register_mission(
        mission_id="runtime-mission-other-token9999",
        objective="Reviewed closeout persistence for lane other-lane",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="structured mission linkage",
        producer_key="openclaw-runtime",
        queue_job_id="overnight-lane-other-token9999",
        source_lane_id="other-lane",
    )
    await service.complete_mission(other_mission.id, "Other mission is available.")
    await async_db_session.commit()

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/mission-state"
        "?queue_job_id=overnight-lane-control-plane-token1234&source_lane_id=control-plane"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["missions"][0]["mission_id"] == "runtime-mission-control-plane-token1234"
    assert payload["missions"][0]["queue_job_id"] == "overnight-lane-control-plane-token1234"
    assert payload["missions"][0]["source_lane_id"] == "control-plane"
    assert payload["missions"][0]["source_board_concurrency_token"] == "token-1234"


async def test_runtime_mission_state_filter_falls_back_for_legacy_source_request_linkage(
    superuser_client,
    async_db_session,
    test_superuser,
):
    repository = PostgresMissionStateRepository(
        async_db_session,
        organization_id=test_superuser.organization_id,
    )
    service = OrchestratorMissionStateService(repository)

    legacy_mission = await service.register_mission(
        mission_id="runtime-mission-legacy-token1234",
        objective="Legacy mission linkage",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request=(
            "Developer control-plane explicit completion write-back for lane control-plane "
            "from queue job overnight-lane-control-plane-token1234. "
            "Context: source_board_concurrency_token=token-1234."
        ),
        producer_key="openclaw-runtime",
    )
    await service.complete_mission(legacy_mission.id, "Legacy linkage remains queryable.")
    await async_db_session.commit()

    response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/mission-state"
        "?queue_job_id=overnight-lane-control-plane-token1234&source_lane_id=control-plane"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["missions"][0]["mission_id"] == "runtime-mission-legacy-token1234"
    assert payload["missions"][0]["queue_job_id"] == "overnight-lane-control-plane-token1234"
    assert payload["missions"][0]["source_lane_id"] == "control-plane"
    assert payload["missions"][0]["source_board_concurrency_token"] == "token-1234"


async def test_runtime_mission_state_bootstrap_from_stable_closeout_receipt(
    superuser_client,
    async_db_session,
    tmp_path,
    monkeypatch,
):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200

    queue_job_id = f"overnight-lane-control-plane-{save_response.json()['concurrency_token'].lower().replace('-', '')[:8]}"
    mission_dir = tmp_path / "mission-evidence"
    _write_closeout_receipt_file(mission_dir, queue_job_id)
    monkeypatch.setattr(developer_control_plane_api, "MISSION_EVIDENCE_DIR", mission_dir)

    bootstrap_response = await superuser_client.post(
        "/api/v2/developer-control-plane/runtime/mission-state/bootstrap-closeout-receipt",
        json={"queue_job_id": queue_job_id},
    )

    assert bootstrap_response.status_code == 200
    assert bootstrap_response.json() == {
        "action": "created",
        "mission_id": "runtime-mission-control-plane-token1234",
    }

    mission_detail_response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/mission-state/runtime-mission-control-plane-token1234"
    )
    assert mission_detail_response.status_code == 200
    payload = mission_detail_response.json()
    assert payload["mission_id"] == "runtime-mission-control-plane-token1234"
    assert payload["status"] == "active"
    assert payload["objective"] == "Await canonical board closure for lane Control Plane Lane"
    assert payload["queue_job_id"] == queue_job_id
    assert payload["source_lane_id"] == "control-plane"
    assert payload["source_board_concurrency_token"] == "token-1234"
    assert payload["final_summary"] is None
    assert payload["subtasks"] == []
    assert sorted(item["kind"] for item in payload["evidence_items"]) == [
        "closeout_receipt",
        "verification_evidence",
    ]
    assert payload["verification_runs"] == [
        {
            "id": payload["verification_runs"][0]["id"],
            "subject_id": "runtime-mission-control-plane-token1234",
            "verification_type": "runtime_closeout_receipt_observed",
            "result": "passed",
            "evidence_ref": payload["evidence_items"][0]["id"],
            "executed_at": payload["verification_runs"][0]["executed_at"],
        }
    ]
    assert payload["decision_notes"] == [
        {
            "id": payload["decision_notes"][0]["id"],
            "decision_class": "stable_closeout_receipt_observed",
            "authority_source": "OmShriMaatreNamaha",
            "recorded_at": payload["decision_notes"][0]["recorded_at"],
        }
    ]

    mission_row = await async_db_session.scalar(
        select(OrchestratorMission).where(
            OrchestratorMission.mission_id == "runtime-mission-control-plane-token1234"
        )
    )
    assert mission_row is not None
    assert mission_row.queue_job_id == queue_job_id

    stored_learning_entries = list(
        (
            await async_db_session.execute(
                select(DeveloperControlPlaneLearningEntry).where(
                    DeveloperControlPlaneLearningEntry.linked_mission_id
                    == "runtime-mission-control-plane-token1234"
                )
            )
        ).scalars()
    )
    assert len(stored_learning_entries) == 1
    assert stored_learning_entries[0].source_classification == "stable-closeout-receipt"

    learnings_response = await superuser_client.get(
        "/api/v2/developer-control-plane/learnings",
        params={"linked_mission_id": "runtime-mission-control-plane-token1234"},
    )
    assert learnings_response.status_code == 200
    assert learnings_response.json()["total_count"] == 1

    post_read_learning_entries = list(
        (
            await async_db_session.execute(
                select(DeveloperControlPlaneLearningEntry).where(
                    DeveloperControlPlaneLearningEntry.linked_mission_id
                    == "runtime-mission-control-plane-token1234"
                )
            )
        ).scalars()
    )
    assert len(post_read_learning_entries) == 1
    assert mission_row.source_lane_id == "control-plane"
    assert mission_row.source_board_concurrency_token == "token-1234"


async def test_completion_write_updates_existing_bootstrapped_runtime_mission(
    superuser_client,
    async_db_session,
    tmp_path,
    monkeypatch,
):
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200
    board_token = save_response.json()["concurrency_token"]

    queue_job_id = f"overnight-lane-control-plane-{board_token.lower().replace('-', '')[:8]}"
    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(
        queue_path,
        _queue_payload(job_id=queue_job_id, include_job=True, status="completed"),
    )
    mission_dir = tmp_path / "mission-evidence"
    _write_closeout_receipt_file(mission_dir, queue_job_id)
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)
    monkeypatch.setattr(developer_control_plane_api, "MISSION_EVIDENCE_DIR", mission_dir)

    bootstrap_response = await superuser_client.post(
        "/api/v2/developer-control-plane/runtime/mission-state/bootstrap-closeout-receipt",
        json={"queue_job_id": queue_job_id},
    )
    assert bootstrap_response.status_code == 200
    assert bootstrap_response.json()["action"] == "created"

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    assert status_response.status_code == 200

    write_response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/write-completion",
        json=_completion_write_request(
            source_token=board_token,
            expected_queue_sha256=status_response.json()["queue_sha256"],
            lane_id="control-plane",
            queue_job_id=queue_job_id,
            closeout_receipt=_completion_closeout_receipt_payload(queue_job_id),
        ),
    )
    assert write_response.status_code == 200

    mission_state_response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/mission-state?source_lane_id=control-plane"
    )
    assert mission_state_response.status_code == 200
    mission_state_payload = mission_state_response.json()
    assert mission_state_payload["count"] == 1
    mission_summary = mission_state_payload["missions"][0]
    assert mission_summary["mission_id"] == "runtime-mission-control-plane-token1234"
    assert mission_summary["status"] == "completed"
    assert mission_summary["objective"] == "Reviewed closeout persistence for lane Control Plane Lane"
    assert mission_summary["queue_job_id"] == queue_job_id
    assert mission_summary["source_lane_id"] == "control-plane"
    assert mission_summary["evidence_count"] == 2
    assert mission_summary["subtask_total"] == 1
    assert mission_summary["subtask_completed"] == 1
    assert mission_summary["final_summary"] == (
        "Canonical board closure persisted reviewed runtime provenance for lane control-plane. "
        "Closure summary: Completion evidence was reviewed and accepted."
    )

    mission_detail_response = await superuser_client.get(
        "/api/v2/developer-control-plane/runtime/mission-state/runtime-mission-control-plane-token1234"
    )
    assert mission_detail_response.status_code == 200
    mission_detail_payload = mission_detail_response.json()
    assert sorted(item["decision_class"] for item in mission_detail_payload["decision_notes"]) == [
        "reviewed_completion_writeback",
        "stable_closeout_receipt_observed",
    ]
    assert sorted(item["kind"] for item in mission_detail_payload["evidence_items"]) == [
        "closeout_receipt",
        "verification_evidence",
    ]

    mission_row = await async_db_session.scalar(
        select(OrchestratorMission).where(
            OrchestratorMission.mission_id == "runtime-mission-control-plane-token1234"
        )
    )
    assert mission_row is not None
    assert mission_row.queue_job_id == queue_job_id
    assert mission_row.source_lane_id == "control-plane"
    assert mission_row.source_board_concurrency_token == "token-1234"

    completion_approval_receipt_id = write_response.json()["approval_receipt"]["receipt_id"]
    seeded_completion_learning = await async_db_session.scalar(
        select(DeveloperControlPlaneLearningEntry).where(
            DeveloperControlPlaneLearningEntry.approval_receipt_id
            == completion_approval_receipt_id
        )
    )
    assert seeded_completion_learning is not None
    assert seeded_completion_learning.entry_type == "pattern"
    assert seeded_completion_learning.source_classification == "reviewed-completion-writeback"
    assert seeded_completion_learning.source_lane_id == "control-plane"
    assert seeded_completion_learning.queue_job_id == queue_job_id
    assert (
        seeded_completion_learning.linked_mission_id
        == "runtime-mission-control-plane-token1234"
    )
    assert seeded_completion_learning.source_reference == (
        f"approval-receipt:{completion_approval_receipt_id}:reviewed-completion-writeback"
    )
    assert seeded_completion_learning.summary_metadata == {
        "seed_source": "approval-receipt",
        "approval_receipt_action": "write-reviewed-lane-completion",
        "approval_receipt_outcome": "applied",
        "queue_sha256": status_response.json()["queue_sha256"],
        "closeout_receipt_present": True,
    }

    learnings_response = await superuser_client.get(
        "/api/v2/developer-control-plane/learnings",
        params={"source_lane_id": "control-plane"},
    )
    assert learnings_response.status_code == 200
    completion_learning_payload = next(
        item
        for item in learnings_response.json()["entries"]
        if item["approval_receipt_id"] == completion_approval_receipt_id
    )
    assert completion_learning_payload["title"] == (
        "Reviewed completion write-back closed lane control-plane"
    )
    assert completion_learning_payload["summary"] == (
        "Explicit reviewed completion write-back persisted canonical closure for lane "
        f"control-plane from queue job {queue_job_id} without weakening board-wins "
        "precedence. Runtime closeout receipt evidence stayed attached to the accepted "
        "closure path."
    )


async def test_runtime_mission_state_detail_returns_expanded_latest_snapshot(
    superuser_client,
    async_db_session,
    test_superuser,
):
    repository = PostgresMissionStateRepository(
        async_db_session,
        organization_id=test_superuser.organization_id,
    )
    service = OrchestratorMissionStateService(repository)

    mission = await service.register_mission(
        objective="Control-plane mission detail inspection",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="developer control-plane mission detail inspection",
        producer_key="chaitanya",
    )
    subtask = await service.add_subtask(
        mission_id=mission.id,
        title="Inspect durable mission detail projection",
        owner_role="OmVishnaveNamah",
    )
    await service.update_subtask_status(subtask.id, SubtaskStatus.COMPLETED)
    assignment = await service.assign_subtask(
        subtask_id=subtask.id,
        assigned_role="OmVishnaveNamah",
        handoff_reason="Verify latest mission detail in the control-plane.",
    )
    await service.complete_assignment(assignment.id)
    evidence = await service.record_evidence(
        subtask_id=subtask.id,
        kind="runtime_watchdog",
        source_path="runtime-artifacts/watchdog-state.json",
        evidence_class="runtime-status",
        summary="Watchdog evidence is mirrored into the durable mission detail feed.",
    )
    await service.record_verification_run(
        subject_id=subtask.id,
        verification_type="runtime_watchdog",
        result=VerificationResult.PASSED,
        evidence_ref=evidence.id,
    )
    await service.record_decision_note(
        mission_id=mission.id,
        decision_class="reviewed_dispatch",
        rationale="Mission detail remains read-only in the hidden control-plane.",
        authority_source="OmShriMaatreNamaha",
    )
    await service.record_blocker(
        mission_id=mission.id,
        blocker_type="missing_operator_acceptance",
        impact="Human review is still required before canonical completion write-back.",
        escalation_needed=False,
    )
    await service.complete_mission(
        mission.id,
        "Expanded mission detail is available for the latest durable snapshot.",
    )
    await async_db_session.commit()

    response = await superuser_client.get(
        f"/api/v2/developer-control-plane/runtime/mission-state/{mission.id}"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mission_id"] == mission.id
    assert payload["objective"] == "Control-plane mission detail inspection"
    assert payload["queue_job_id"] is None
    assert payload["source_lane_id"] is None
    assert payload["source_board_concurrency_token"] is None
    assert payload["subtasks"] == [
        {
            "id": subtask.id,
            "title": "Inspect durable mission detail projection",
            "status": "completed",
            "owner_role": "OmVishnaveNamah",
            "depends_on": [],
            "updated_at": payload["subtasks"][0]["updated_at"],
        }
    ]
    assert payload["assignments"] == [
        {
            "id": assignment.id,
            "subtask_id": subtask.id,
            "assigned_role": "OmVishnaveNamah",
            "handoff_reason": "Verify latest mission detail in the control-plane.",
            "started_at": payload["assignments"][0]["started_at"],
            "completed_at": payload["assignments"][0]["completed_at"],
        }
    ]
    assert payload["evidence_items"] == [
        {
            "id": evidence.id,
            "mission_id": mission.id,
            "subtask_id": subtask.id,
            "kind": "runtime_watchdog",
            "evidence_class": "runtime-status",
            "summary": "Watchdog evidence is mirrored into the durable mission detail feed.",
            "source_path": "runtime-artifacts/watchdog-state.json",
            "recorded_at": payload["evidence_items"][0]["recorded_at"],
        }
    ]
    assert payload["verification_runs"] == [
        {
            "id": payload["verification_runs"][0]["id"],
            "subject_id": subtask.id,
            "verification_type": "runtime_watchdog",
            "result": "passed",
            "evidence_ref": evidence.id,
            "executed_at": payload["verification_runs"][0]["executed_at"],
        }
    ]
    assert payload["decision_notes"] == [
        {
            "id": payload["decision_notes"][0]["id"],
            "decision_class": "reviewed_dispatch",
            "authority_source": "OmShriMaatreNamaha",
            "recorded_at": payload["decision_notes"][0]["recorded_at"],
        }
    ]
    assert payload["blockers"] == [
        {
            "id": payload["blockers"][0]["id"],
            "mission_id": mission.id,
            "subtask_id": None,
            "blocker_type": "missing_operator_acceptance",
            "impact": "Human review is still required before canonical completion write-back.",
            "escalation_needed": False,
            "recorded_at": payload["blockers"][0]["recorded_at"],
        }
    ]


async def test_runtime_mission_state_detail_hides_non_orchestrator_missions(
    superuser_client,
    async_db_session,
    test_superuser,
):
    repository = PostgresMissionStateRepository(
        async_db_session,
        organization_id=test_superuser.organization_id,
    )
    service = OrchestratorMissionStateService(repository)

    mission = await service.register_mission(
        objective="Non-orchestrator mission",
        owner="OtherAgent",
        priority="p2",
        source_request="non orchestrator mission",
    )
    await async_db_session.commit()

    response = await superuser_client.get(
        f"/api/v2/developer-control-plane/runtime/mission-state/{mission.id}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Mission not found"


async def test_completion_write_returns_noop_for_identical_repeat(
    superuser_client, tmp_path, monkeypatch, async_db_session
):
    initial_token = "initial-token"
    queue_job_id = f"overnight-lane-control-plane-{initial_token.lower().replace('-', '')[:8]}"
    closure = {
        "queue_job_id": queue_job_id,
        "queue_sha256": "pending-sha",
        "source_board_concurrency_token": initial_token,
        "closure_summary": "Completion evidence was reviewed and accepted.",
        "evidence": ["Focused tests passed", "Queue job completed"],
        "completed_at": "2026-03-18T18:00:00Z",
    }
    save_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": _board_json_with_lane(
                lane_status="completed",
                closure=closure,
                version="1.1.0",
            ),
            "save_source": "direct-ui",
            "concurrency_token": None,
        },
    )
    assert save_response.status_code == 200

    queue_path = tmp_path / "overnight-queue.json"
    _write_queue_file(
        queue_path,
        _queue_payload(job_id=queue_job_id, include_job=True, status="completed"),
    )
    monkeypatch.setattr(developer_control_plane_api, "OVERNIGHT_QUEUE_PATH", queue_path)

    status_response = await superuser_client.get(
        "/api/v2/developer-control-plane/overnight-queue/status"
    )
    queue_sha = status_response.json()["queue_sha256"]

    active_board = json.loads(save_response.json()["canonical_board_json"])
    active_board["lanes"][0]["closure"]["queue_sha256"] = queue_sha
    resave_response = await superuser_client.put(
        "/api/v2/developer-control-plane/active-board",
        json={
            "canonical_board_json": json.dumps(active_board),
            "save_source": "direct-ui",
            "concurrency_token": save_response.json()["concurrency_token"],
        },
    )
    assert resave_response.status_code == 200

    noop_response = await superuser_client.post(
        "/api/v2/developer-control-plane/active-board/write-completion",
        json=_completion_write_request(
            source_token=initial_token,
            expected_queue_sha256=queue_sha,
            lane_id="control-plane",
            queue_job_id=queue_job_id,
        ),
    )
    assert noop_response.status_code == 200
    assert noop_response.json()["no_op"] is True
    assert noop_response.json()["approval_receipt"] is None
    assert await _list_approval_receipts(async_db_session) == []

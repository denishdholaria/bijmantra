from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts import stage_control_plane_completion_assist as completion_assist


def _autonomy_cycle_payload() -> dict:
    return {
        "exists": True,
        "artifact_path": ".github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json",
        "generated_at": "2026-04-06T12:00:00+00:00",
        "queue_path": ".agent/jobs/overnight-queue.json",
        "window": "nightly",
        "max_jobs_per_run": 2,
        "status_counts": {"completed": 1},
        "selected_job_count": 0,
        "blocked_job_count": 0,
        "closeout_candidate_count": 1,
        "next_action_count": 1,
        "next_action_ordering_source": "canonical-learning-exact-runtime",
        "watchdog": {
            "exists": True,
            "state_path": "runtime-artifacts/watchdog-state.json",
            "last_check": "2026-04-06T11:50:00+00:00",
            "gateway_healthy": True,
            "state_is_stale": False,
            "total_alerts": 0,
            "job_errors": {},
        },
        "selected_jobs": [],
        "blocked_jobs": [],
        "closeout_candidates": [],
        "next_actions": [],
        "first_actionable_completion_write": {
            "action": "prepare-completion-write-back",
            "action_index": 0,
            "job_id": "overnight-lane-control-plane-token1234",
            "source_lane_id": "control-plane",
            "reason": "stable closeout ready for explicit board write-back",
            "mission_id": "runtime-mission-control-plane-token1234",
            "receipt_path": "runtime-artifacts/mission-evidence/job/closeout.json",
            "preparation": {
                "source_lane_id": "control-plane",
                "queue_job_id": "overnight-lane-control-plane-token1234",
                "draft_source": "stable-closeout-receipt",
                "queue_status": {
                    "queue_path": ".agent/jobs/overnight-queue.json",
                    "queue_sha256": "queue-sha-77",
                    "exists": True,
                    "job_count": 1,
                    "updated_at": "2026-04-06T11:30:00+00:00",
                },
                "closeout_receipt": {
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
                    "receipt_recorded_at": "2026-04-06T11:45:00+00:00",
                    "started_at": "2026-04-06T11:40:00+00:00",
                    "finished_at": "2026-04-06T11:44:00+00:00",
                    "verification_evidence_ref": "runtime-artifacts/mission-evidence/job/verification_1.json",
                    "queue_sha256_at_closeout": "queue-sha-closeout-77",
                    "closeout_commands": [],
                    "artifacts": [
                        {
                            "path": "metrics.json",
                            "exists": True,
                            "sha256": "abc123",
                            "modified_at": "2026-04-06T11:44:30+00:00",
                        }
                    ],
                },
                "prepared_request": {
                    "source_board_concurrency_token": "token-1234",
                    "expected_queue_sha256": "queue-sha-77",
                    "operator_intent": "write-reviewed-lane-completion",
                    "completion": {
                        "source_lane_id": "control-plane",
                        "queue_job_id": "overnight-lane-control-plane-token1234",
                        "closure_summary": "Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.",
                        "evidence": [
                            "Reviewed queue job overnight-lane-control-plane-token1234 using watchdog closeout receipt before explicit board write-back.",
                        ],
                        "closeout_receipt": {
                            "queue_job_id": "overnight-lane-control-plane-token1234",
                            "artifact_paths": ["metrics.json"],
                            "mission_id": "runtime-mission-control-plane-token1234",
                            "producer_key": "openclaw-runtime",
                            "source_lane_id": "control-plane",
                            "source_board_concurrency_token": "token-1234",
                            "runtime_profile_id": "bijmantra-bca-local-verify",
                            "runtime_policy_sha256": "policy-sha-1234",
                            "closeout_status": "passed",
                            "state_refresh_required": True,
                            "receipt_recorded_at": "2026-04-06T11:45:00+00:00",
                            "verification_evidence_ref": "runtime-artifacts/mission-evidence/job/verification_1.json",
                            "queue_sha256_at_closeout": "queue-sha-closeout-77",
                        },
                    },
                },
            },
        },
    }


def test_build_completion_assist_artifact_stages_first_actionable_write():
    artifact = completion_assist.build_completion_assist_artifact(
        _autonomy_cycle_payload(),
        endpoint_url="http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
        generated_at="2026-04-06T12:05:00+00:00",
    )

    assert artifact["status"] == "staged"
    assert artifact["staged"] is True
    assert artifact["explicitWriteRequired"] is True
    assert artifact["idleReason"] is None
    assert artifact["readiness"] == {
        "selectedJobCount": 0,
        "nextActionCount": 1,
        "closeoutCandidateCount": 1,
        "reviewActionCount": 0,
        "prepareActionCount": 0,
        "eligibleCloseoutCandidateCount": 0,
        "watchdogExists": True,
        "watchdogStatePath": "runtime-artifacts/watchdog-state.json",
        "watchdogStateIsStale": False,
    }
    assert artifact["source"]["next_action_ordering_source"] == "canonical-learning-exact-runtime"
    assert artifact["actionableCompletionWrite"] == {
        "action": "prepare-completion-write-back",
        "actionIndex": 0,
        "jobId": "overnight-lane-control-plane-token1234",
        "sourceLaneId": "control-plane",
        "reason": "stable closeout ready for explicit board write-back",
        "missionId": "runtime-mission-control-plane-token1234",
        "receiptPath": "runtime-artifacts/mission-evidence/job/closeout.json",
        "draftSource": "stable-closeout-receipt",
        "queueStatus": _autonomy_cycle_payload()["first_actionable_completion_write"]["preparation"]["queue_status"],
        "closeoutReceipt": _autonomy_cycle_payload()["first_actionable_completion_write"]["preparation"]["closeout_receipt"],
        "preparedRequest": _autonomy_cycle_payload()["first_actionable_completion_write"]["preparation"]["prepared_request"],
    }


def test_build_completion_assist_artifact_reports_idle_when_no_actionable_write():
    payload = _autonomy_cycle_payload()
    payload["first_actionable_completion_write"] = None
    payload["closeout_candidate_count"] = 0
    payload["next_action_count"] = 0

    artifact = completion_assist.build_completion_assist_artifact(
        payload,
        endpoint_url="http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
        generated_at="2026-04-06T12:05:00+00:00",
    )

    assert artifact == {
        "generatedAt": "2026-04-06T12:05:00+00:00",
        "status": "idle",
        "staged": False,
        "explicitWriteRequired": True,
        "message": "No actionable reviewed completion write-back packet is present because the runtime autonomy-cycle has no stable closeout candidates.",
        "idleReason": "no-stable-closeout-candidates",
        "readiness": {
            "selectedJobCount": 0,
            "nextActionCount": 0,
            "closeoutCandidateCount": 0,
            "reviewActionCount": 0,
            "prepareActionCount": 0,
            "eligibleCloseoutCandidateCount": 0,
            "watchdogExists": True,
            "watchdogStatePath": "runtime-artifacts/watchdog-state.json",
            "watchdogStateIsStale": False,
        },
        "source": {
            "endpoint": "http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
            "autonomy_cycle_artifact_path": ".github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json",
            "autonomy_cycle_generated_at": "2026-04-06T12:00:00+00:00",
            "next_action_ordering_source": "canonical-learning-exact-runtime",
        },
        "actionableCompletionWrite": None,
    }


def test_build_completion_assist_artifact_reports_not_ready_when_closeout_receipts_exist():
    payload = _autonomy_cycle_payload()
    payload["first_actionable_completion_write"] = None
    payload["closeout_candidates"] = [
        {
            "job_id": "overnight-lane-control-plane-token1234",
            "source_lane_id": "control-plane",
            "queue_status": "running",
            "closeout_status": "passed",
            "path": "runtime-artifacts/mission-evidence/job/closeout.json",
        }
    ]
    payload["next_actions"] = [
        {
            "action": "review-closeout-receipt",
            "job_id": "overnight-lane-control-plane-token1234",
        }
    ]

    artifact = completion_assist.build_completion_assist_artifact(
        payload,
        endpoint_url="http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
        generated_at="2026-04-06T12:05:00+00:00",
    )

    assert artifact["idleReason"] == "closeout-candidates-not-ready"
    assert artifact["message"] == (
        "No actionable reviewed completion write-back packet is present because stable closeout candidates exist but are not yet ready for explicit board write-back."
    )
    assert artifact["readiness"]["closeoutCandidateCount"] == 1
    assert artifact["readiness"]["reviewActionCount"] == 1
    assert artifact["readiness"]["prepareActionCount"] == 0
    assert artifact["readiness"]["eligibleCloseoutCandidateCount"] == 0


def test_build_completion_assist_artifact_reports_missing_embedded_preparation_when_prepare_action_exists():
    payload = _autonomy_cycle_payload()
    payload["first_actionable_completion_write"] = None
    payload["next_actions"] = [
        {
            "action": "prepare-completion-write-back",
            "job_id": "overnight-lane-control-plane-token1234",
        }
    ]

    artifact = completion_assist.build_completion_assist_artifact(
        payload,
        endpoint_url="http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
        generated_at="2026-04-06T12:05:00+00:00",
    )

    assert artifact["idleReason"] == "missing-embedded-preparation"
    assert artifact["message"] == (
        "The runtime autonomy-cycle reported completion write-back actions, but no actionable reviewed completion packet was embedded."
    )
    assert artifact["readiness"]["prepareActionCount"] == 1


def test_resolve_auth_token_uses_env_fallback(monkeypatch):
    monkeypatch.setenv(completion_assist.AUTH_TOKEN_ENV, "token-1234")

    assert completion_assist.resolve_auth_token("") == "token-1234"


def test_main_writes_tracked_completion_assist_artifact(tmp_path, monkeypatch, capsys):
    output_path = tmp_path / "developer-control-plane-completion-assist.json"
    monkeypatch.setattr(
        completion_assist,
        "parse_args",
        lambda: argparse.Namespace(
            base_url="http://127.0.0.1:8000",
            auth_token="token-1234",
            timeout_seconds=5.0,
            output=output_path,
        ),
    )
    monkeypatch.setattr(
        completion_assist,
        "fetch_runtime_autonomy_cycle",
        lambda **_: _autonomy_cycle_payload(),
    )

    result = completion_assist.main()

    assert result == 0
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["status"] == "staged"
    assert written["idleReason"] is None
    assert written["actionableCompletionWrite"]["sourceLaneId"] == "control-plane"
    output = capsys.readouterr().out
    assert f"Wrote {output_path}" in output
    assert "Staged reviewed completion assist for lane control-plane." in output


def test_build_completion_assist_artifact_rejects_malformed_actionable_packet():
    payload = _autonomy_cycle_payload()
    payload["first_actionable_completion_write"] = {"action": "prepare-completion-write-back"}

    with pytest.raises(
        completion_assist.CompletionAssistError,
        match="preparation must be an object",
    ):
        completion_assist.build_completion_assist_artifact(
            payload,
            endpoint_url="http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
            generated_at="2026-04-06T12:05:00+00:00",
        )
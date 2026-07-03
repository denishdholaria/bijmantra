from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.run_control_plane_autonomy_cycle import (
    build_autonomy_cycle,
    load_runtime_context,
    parse_args,
)
import scripts.run_control_plane_autonomy_cycle as autonomy_cycle_script


def _queue_payload() -> dict:
    return {
        "version": 1,
        "updatedAt": "2026-04-05T00:00:00Z",
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
                "jobId": "runtime-job",
                "title": "Runtime Job",
                "status": "running",
                "priority": "p2",
                "primaryAgent": "OmShriMaatreNamaha",
                "supportAgents": [],
                "executionMode": "same-control-plane",
                "autonomousTrigger": {
                    "type": "overnight-window",
                    "window": "nightly",
                    "enabled": True,
                },
                "dependsOn": [],
                "goal": "Produce runtime evidence.",
                "lane": {
                    "objective": "Produce runtime evidence.",
                    "inputs": ["queue"],
                    "outputs": ["closeout receipt"],
                    "dependencies": [],
                    "completion_criteria": ["Closeout receipt exists."],
                },
                "provenance": {
                    "sourceBoardConcurrencyToken": "shared-token-1",
                    "sourceLaneId": "control-plane",
                    "precedence": {
                        "canonicalPlanningSource": "active-board",
                        "derivedExecutionSurface": "overnight-queue",
                    },
                },
                "successCriteria": ["Closeout receipt exists."],
                "verification": {"commands": []},
            },
            {
                "jobId": "closeout-follow-up",
                "title": "Closeout Follow Up",
                "status": "queued",
                "priority": "p1",
                "primaryAgent": "OmShriMaatreNamaha",
                "supportAgents": [],
                "executionMode": "same-control-plane",
                "autonomousTrigger": {
                    "type": "closeout-receipt",
                    "queueJobId": "runtime-job",
                    "closeoutStatus": ["passed"],
                    "enabled": True,
                },
                "dependsOn": [],
                "goal": "React to runtime evidence.",
                "lane": {
                    "objective": "React to runtime evidence.",
                    "inputs": ["closeout receipt"],
                    "outputs": ["follow-up lane"],
                    "dependencies": [],
                    "completion_criteria": ["Follow-up lane is ready."],
                },
                "provenance": {
                    "sourceBoardConcurrencyToken": "shared-token-1",
                    "sourceLaneId": "platform-runtime",
                    "precedence": {
                        "canonicalPlanningSource": "active-board",
                        "derivedExecutionSurface": "overnight-queue",
                    },
                },
                "successCriteria": ["Follow-up lane is ready."],
                "verification": {"commands": []},
            },
        ],
    }


def test_load_runtime_context_reads_watchdog_and_closeout_artifacts(tmp_path):
    mission_evidence_dir = tmp_path / "mission-evidence"
    closeout_dir = mission_evidence_dir / "runtime-job"
    closeout_dir.mkdir(parents=True, exist_ok=True)
    (closeout_dir / "closeout.json").write_text(
        json.dumps(
            {
                "type": "closeout",
                "data": {
                    "status": "passed",
                    "verificationEvidenceRef": "runtime-artifacts/mission-evidence/runtime-job/verification_1.json",
                    "missionId": "mission-runtime-job",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    watchdog_state_path = tmp_path / "watchdog-state.json"
    watchdog_state_path.write_text(
        json.dumps(
            {
                "lastCheck": "2026-04-05T10:00:00Z",
                "gatewayHealthy": False,
                "stateIsStale": True,
                "totalAlerts": 2,
                "jobs": [
                    {
                        "jobId": "runtime-job",
                        "lastError": "verification failed",
                        "consecutiveErrors": 3,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime_context = load_runtime_context(
        _queue_payload(),
        watchdog_state_path=watchdog_state_path,
        mission_evidence_dir=mission_evidence_dir,
    )

    assert runtime_context["watchdog"]["exists"] is True
    assert runtime_context["watchdog"]["stateIsStale"] is True
    assert runtime_context["watchdog"]["gatewayHealthy"] is False
    assert runtime_context["watchdog"]["jobErrors"]["runtime-job"]["consecutiveErrors"] == 3
    assert runtime_context["closeoutReceipts"]["runtime-job"]["exists"] is True
    assert runtime_context["closeoutReceipts"]["runtime-job"]["closeoutStatus"] == "passed"


def test_load_runtime_context_normalizes_shared_runtime_paths(monkeypatch, tmp_path):
    runtime_home = tmp_path / "claw-runtime"
    mission_evidence_dir = runtime_home / "mission-evidence"
    closeout_dir = mission_evidence_dir / "runtime-job"
    closeout_dir.mkdir(parents=True, exist_ok=True)
    (closeout_dir / "closeout.json").write_text(
        json.dumps({"data": {"status": "passed"}}, indent=2),
        encoding="utf-8",
    )

    watchdog_state_path = runtime_home / "watchdog-state.json"
    watchdog_state_path.parent.mkdir(parents=True, exist_ok=True)
    watchdog_state_path.write_text(
        json.dumps({"lastCheck": "2026-04-05T10:00:00Z"}, indent=2),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        autonomy_cycle_script,
        "resolve_runtime_home",
        lambda: runtime_home,
    )

    runtime_context = load_runtime_context(
        _queue_payload(),
        watchdog_state_path=watchdog_state_path,
        mission_evidence_dir=mission_evidence_dir,
    )

    assert runtime_context["watchdog"]["statePath"] == "runtime-artifacts/watchdog-state.json"
    assert runtime_context["closeoutReceipts"]["runtime-job"]["path"] == (
        "runtime-artifacts/mission-evidence/runtime-job/closeout.json"
    )


def test_build_autonomy_cycle_emits_dispatch_and_receipt_actions():
    queue = _queue_payload()
    queue["jobs"][0]["status"] = "completed"

    cycle = build_autonomy_cycle(
        queue,
        window="nightly",
        max_jobs=2,
        runtime_context={
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
            "closeoutReceipts": {
                "runtime-job": {
                    "exists": True,
                    "path": "runtime-artifacts/mission-evidence/runtime-job/closeout.json",
                    "closeoutStatus": "passed",
                    "verificationEvidenceRef": "runtime-artifacts/mission-evidence/runtime-job/verification_1.json",
                    "missionId": "mission-runtime-job",
                },
                "closeout-follow-up": {
                    "exists": False,
                    "path": "runtime-artifacts/mission-evidence/closeout-follow-up/closeout.json",
                },
            },
        },
    )

    assert cycle["selectedJobCount"] == 1
    assert cycle["selectedJobs"][0]["jobId"] == "closeout-follow-up"
    assert cycle["selectedJobs"][0]["sourceLaneId"] == "platform-runtime"
    assert cycle["selectedJobs"][0]["triggerReason"] == "closeout-receipt:runtime-job:passed"
    assert cycle["closeoutCandidateCount"] == 1
    assert cycle["closeoutCandidates"][0]["jobId"] == "runtime-job"
    assert cycle["closeoutCandidates"][0]["sourceLaneId"] == "control-plane"
    assert cycle["nextActions"][0]["sourceLaneId"] == "platform-runtime"
    assert cycle["nextActions"][2]["action"] == "prepare-completion-write-back"
    assert cycle["nextActions"][2]["sourceLaneId"] == "control-plane"
    assert cycle["nextActions"][2]["detail"]["closeoutStatus"] == "passed"
    assert cycle["nextActions"][-1]["sourceLaneId"] == "control-plane"
    assert [action["action"] for action in cycle["nextActions"]] == [
        "dispatch-queue-job",
        "review-closeout-receipt",
        "prepare-completion-write-back",
        "inspect-watchdog-state",
        "inspect-watchdog-state",
        "inspect-watchdog-state",
        "investigate-watchdog-job",
    ]


def test_parse_args_defaults_follow_shared_runtime_home(monkeypatch, tmp_path):
    runtime_home = tmp_path / "external-claw-runtime"
    monkeypatch.setenv("BIJMANTRA_CLAW_RUNTIME_HOME", str(runtime_home))
    monkeypatch.setattr(sys, "argv", ["run_control_plane_autonomy_cycle.py"])

    args = parse_args()

    assert args.watchdog_state == runtime_home / "watchdog-state.json"
    assert args.mission_evidence_dir == runtime_home / "mission-evidence"


def test_maybe_stage_completion_assist_skips_without_token(monkeypatch, tmp_path):
    monkeypatch.setattr(autonomy_cycle_script, "load_local_env", lambda **_: {})
    monkeypatch.delenv(autonomy_cycle_script.AUTH_TOKEN_ENV, raising=False)

    result = autonomy_cycle_script.maybe_stage_completion_assist(
        completion_assist_output_path=tmp_path / "completion-assist.json",
        timeout_seconds=5.0,
    )

    assert result == {
        "status": "skipped",
        "reason": "missing-auth-token",
        "message": (
            f"Skipped completion-assist staging because {autonomy_cycle_script.AUTH_TOKEN_ENV} is not configured."
        ),
    }


def test_maybe_stage_completion_assist_writes_artifact_when_token_present(monkeypatch, tmp_path):
    output_path = tmp_path / "completion-assist.json"
    written: dict[str, object] = {}

    monkeypatch.setenv(autonomy_cycle_script.AUTH_TOKEN_ENV, "token-1234")
    monkeypatch.setenv(autonomy_cycle_script.BASE_URL_ENV, "http://127.0.0.1:8000")
    monkeypatch.setattr(
        autonomy_cycle_script,
        "fetch_runtime_autonomy_cycle",
        lambda **_: {"first_actionable_completion_write": None},
    )
    monkeypatch.setattr(
        autonomy_cycle_script,
        "build_completion_assist_artifact",
        lambda autonomy_cycle, *, endpoint_url, generated_at: {
            "status": "idle",
            "message": "No actionable reviewed completion write-back packet is present in the runtime autonomy-cycle response.",
            "endpoint": endpoint_url,
            "generatedAt": generated_at,
            "payload": autonomy_cycle,
        },
    )
    monkeypatch.setattr(
        autonomy_cycle_script,
        "write_completion_assist_artifact",
        lambda path, artifact: written.update({"path": path, "artifact": artifact}),
    )

    result = autonomy_cycle_script.maybe_stage_completion_assist(
        completion_assist_output_path=output_path,
        timeout_seconds=5.0,
    )

    assert written["path"] == output_path
    assert written["artifact"] == {
        "status": "idle",
        "message": "No actionable reviewed completion write-back packet is present in the runtime autonomy-cycle response.",
        "endpoint": "http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
        "generatedAt": written["artifact"]["generatedAt"],
        "payload": {"first_actionable_completion_write": None},
    }
    assert result == {
        "status": "staged",
        "reason": None,
        "message": "No actionable reviewed completion write-back packet is present in the runtime autonomy-cycle response.",
        "output_path": str(output_path),
    }


def test_maybe_stage_completion_assist_reports_fetch_errors(monkeypatch, tmp_path):
    monkeypatch.setenv(autonomy_cycle_script.AUTH_TOKEN_ENV, "token-1234")

    def _raise_completion_assist_error(**_: object):
        raise autonomy_cycle_script.CompletionAssistError("runtime autonomy-cycle request failed")

    monkeypatch.setattr(
        autonomy_cycle_script,
        "fetch_runtime_autonomy_cycle",
        _raise_completion_assist_error,
    )

    result = autonomy_cycle_script.maybe_stage_completion_assist(
        completion_assist_output_path=tmp_path / "completion-assist.json",
        timeout_seconds=5.0,
    )

    assert result == {
        "status": "error",
        "reason": "assist-fetch-failed",
        "message": "Completion assist staging failed: runtime autonomy-cycle request failed",
    }
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _load_private_ops_module import load_private_ops_module


watchdog = load_private_ops_module(
    "krabi_test_bijmantra_watchdog",
    "ops-private/claw-runtime/scripts/bijmantra_watchdog.py",
)


def _queue_payload(job_id: str) -> dict:
    return {
        "version": 1,
        "updatedAt": "2026-03-19T00:00:00Z",
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
                "jobId": job_id,
                "title": "Platform Runtime",
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
                "goal": "Run the reviewed platform runtime slice.",
                "provenance": {
                    "candidateVersion": "1.0.0",
                    "exportedAt": "2026-03-19T00:00:00Z",
                    "boardId": "bijmantra-app-development-master-board",
                    "boardTitle": "Platform Runtime Board",
                    "sourceBoardConcurrencyToken": "token-1234",
                    "sourceLaneId": "platform-runtime",
                    "precedence": {
                        "canonicalPlanningSource": "active-board",
                        "derivedExecutionSurface": "overnight-queue",
                        "exportDisposition": "manual-candidate-only",
                        "conflictResolution": "board-wins-no-silent-overwrite",
                        "staleIfSourceBoardChanges": True,
                    },
                },
                "lane": {
                    "objective": "Run the platform runtime pilot.",
                    "inputs": ["board"],
                    "outputs": ["runtime evidence"],
                    "dependencies": [],
                    "completion_criteria": ["Evidence is reviewed"],
                },
                "successCriteria": ["Evidence is reviewed"],
                "verification": {
                    "commands": ["echo verify"],
                    "stateRefreshRequired": True,
                },
            }
        ],
    }


def test_run_closeout_commands_collects_artifact_receipt(tmp_path, monkeypatch):
    job_id = "overnight-lane-platform-runtime-token1234"
    queue_path = tmp_path / "overnight-queue.json"
    queue_path.write_text(json.dumps(_queue_payload(job_id), indent=2), encoding="utf-8")

    metrics_path = tmp_path / "metrics.json"
    plan_path = tmp_path / "overnight-dispatch-plan.json"
    state_path = tmp_path / "current-app-state.json"
    metrics_path.write_text('{"lastUpdated":"2026-03-19"}\n', encoding="utf-8")
    plan_path.write_text('{"selectedJobs":[]}\n', encoding="utf-8")
    state_path.write_text('{"status":"ok"}\n', encoding="utf-8")

    monkeypatch.setattr(watchdog, "QUEUE_PATH", queue_path)
    monkeypatch.setattr(
        watchdog,
        "TRACKING_ARTIFACT_PATHS",
        (metrics_path, plan_path, state_path),
    )

    def fake_run(cmd, **kwargs):
        assert cmd == "make update-state"
        return SimpleNamespace(returncode=0, stdout="updated\n", stderr="")

    monkeypatch.setattr(watchdog.subprocess, "run", fake_run)

    passed, receipt = watchdog.run_closeout_commands(
        job_id,
        verification_evidence_ref="runtime-artifacts/mission-evidence/test/verification_1.json",
    )

    assert passed is True
    assert receipt["version"] == 1
    assert receipt["receiptType"] == "closeout"
    assert receipt["queueJobId"] == job_id
    assert receipt["missionId"] == "runtime-mission-platform-runtime-token123"
    assert receipt["producerKey"] == "openclaw-runtime"
    assert receipt["sourceLaneId"] == "platform-runtime"
    assert receipt["sourceBoardConcurrencyToken"] == "token-1234"
    assert receipt["runtimeProfileId"] == "bijmantra-bca-local-verify"
    if receipt["runtimePolicySha256"] is not None:
        assert isinstance(receipt["runtimePolicySha256"], str)
        assert len(receipt["runtimePolicySha256"]) == 64
    assert receipt["status"] == "passed"
    assert receipt["verificationEvidenceRef"] == "runtime-artifacts/mission-evidence/test/verification_1.json"
    assert receipt["closeoutCommands"][0]["command"] == "make update-state"
    assert receipt["closeoutCommands"][0]["passed"] is True
    assert receipt["summary"] == {
        "commandsRun": 1,
        "artifactsRefreshed": 3,
        "verificationPassed": True,
        "notes": "Closeout completed with state refresh.",
    }
    assert [artifact["path"] for artifact in receipt["artifacts"]] == [
        "metrics.json",
        "overnight-dispatch-plan.json",
        "current-app-state.json",
    ]
    assert all(artifact["exists"] is True for artifact in receipt["artifacts"])
    assert all(artifact["sha256"] for artifact in receipt["artifacts"])


def test_run_check_skips_repeated_closeout_when_receipt_exists(tmp_path, monkeypatch):
    job_id = "overnight-lane-platform-runtime-token1234"
    mission_dir = tmp_path / "mission-evidence"
    closeout_dir = mission_dir / job_id
    closeout_dir.mkdir(parents=True, exist_ok=True)
    (closeout_dir / "closeout.json").write_text(
        json.dumps(
            {
                "jobId": job_id,
                "type": "closeout",
                "timestamp": "2026-03-19T00:00:00Z",
                "data": {"status": "passed"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(watchdog, "MISSION_DIR", mission_dir)
    monkeypatch.setattr(watchdog, "check_gateway_health", lambda: (True, "healthy"))
    monkeypatch.setattr(
        watchdog,
        "poll_cron_jobs",
        lambda: [
            {
                "label": f"bijmantra:{job_id}",
                "state": {"lastRunStatus": "ok"},
            }
        ],
    )
    monkeypatch.setattr(watchdog, "check_path_violations", lambda job_id, branch: [])

    verification_calls = []
    monkeypatch.setattr(
        watchdog,
        "run_verification_commands",
        lambda current_job_id: verification_calls.append(current_job_id) or (True, []),
    )

    runtime_status_notes = []
    monkeypatch.setattr(
        watchdog,
        "note_runtime_status",
        lambda current_job_id, status: runtime_status_notes.append((current_job_id, status)),
    )
    monkeypatch.setattr(
        watchdog.WatchdogState,
        "save",
        lambda self, path=watchdog.WATCHDOG_STATE: None,
    )

    state = watchdog.WatchdogState()
    watchdog.run_check(state)

    assert verification_calls == []
    assert runtime_status_notes == [(job_id, "completed")]
    assert len(state.jobs) == 1
    assert state.jobs[0].job_id == job_id
    assert state.jobs[0].verification_passed is True


def test_run_check_persists_completion_assist_advisory_from_current_state(
    tmp_path, monkeypatch
):
    watchdog_state_path = tmp_path / "watchdog-state.json"
    metrics_path = tmp_path / "metrics.json"
    plan_path = tmp_path / "overnight-dispatch-plan.json"
    state_path = tmp_path / "current-app-state.json"
    metrics_path.write_text('{"lastUpdated":"2026-04-06"}\n', encoding="utf-8")
    plan_path.write_text(
        json.dumps(
            {
                "selectedJobs": [],
                "advisoryInputs": {
                    "completionAssist": {
                        "available": False,
                        "status": "idle",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    state_path.write_text(
        json.dumps(
            {
                "application": {
                    "orchestration": {
                        "overnightQueue": {
                            "latestPlan": {
                                "advisoryInputs": {
                                    "completionAssist": {
                                        "authority": "advisory-only-derived",
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
                                }
                            }
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        watchdog,
        "TRACKING_ARTIFACT_PATHS",
        (metrics_path, plan_path, state_path),
    )
    monkeypatch.setattr(watchdog, "check_gateway_health", lambda: (True, "healthy"))
    monkeypatch.setattr(watchdog, "poll_cron_jobs", lambda: [])
    monkeypatch.setattr(
        watchdog.WatchdogState,
        "save",
        lambda self, path=watchdog.WATCHDOG_STATE: None,
    )

    state = watchdog.WatchdogState()
    watchdog.run_check(state)

    assert state.advisory_inputs["completionAssist"] == {
        "authority": "advisory-only-derived",
        "observedFromPath": "current-app-state.json",
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


def test_run_check_falls_back_to_dispatch_plan_completion_assist_advisory(
    tmp_path, monkeypatch
):
    watchdog_state_path = tmp_path / "watchdog-state.json"
    metrics_path = tmp_path / "metrics.json"
    plan_path = tmp_path / "overnight-dispatch-plan.json"
    state_path = tmp_path / "current-app-state.json"
    metrics_path.write_text('{"lastUpdated":"2026-04-06"}\n', encoding="utf-8")
    plan_path.write_text(
        json.dumps(
            {
                "selectedJobs": [],
                "advisoryInputs": {
                    "completionAssist": {
                        "available": True,
                        "artifactPath": ".github/docs/architecture/tracking/developer-control-plane-completion-assist.json",
                        "status": "staged",
                        "staged": True,
                        "explicitWriteRequired": True,
                        "message": "Staged reviewed completion assist for lane platform-runtime. This artifact does not perform explicit board write-back.",
                        "sourceLaneId": "platform-runtime",
                        "queueJobId": "overnight-lane-platform-runtime-token1234",
                        "draftSource": "stable-closeout-receipt",
                        "receiptPath": "runtime-artifacts/mission-evidence/platform-runtime/closeout.json",
                        "sourceEndpoint": "http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
                        "autonomyCycleArtifactPath": ".github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json",
                        "nextActionOrderingSource": "artifact",
                        "matchedSelectedJobIds": ["overnight-lane-platform-runtime-token1234"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        watchdog,
        "TRACKING_ARTIFACT_PATHS",
        (metrics_path, plan_path, state_path),
    )
    monkeypatch.setattr(watchdog, "check_gateway_health", lambda: (True, "healthy"))
    monkeypatch.setattr(watchdog, "poll_cron_jobs", lambda: [])
    monkeypatch.setattr(
        watchdog.WatchdogState,
        "save",
        lambda self, path=watchdog.WATCHDOG_STATE: None,
    )

    state = watchdog.WatchdogState()
    watchdog.run_check(state)

    assert state.advisory_inputs["completionAssist"] == {
        "authority": "advisory-only-derived",
        "observedFromPath": "overnight-dispatch-plan.json",
        "available": True,
        "artifactPath": ".github/docs/architecture/tracking/developer-control-plane-completion-assist.json",
        "status": "staged",
        "staged": True,
        "explicitWriteRequired": True,
        "message": "Staged reviewed completion assist for lane platform-runtime. This artifact does not perform explicit board write-back.",
        "sourceLaneId": "platform-runtime",
        "queueJobId": "overnight-lane-platform-runtime-token1234",
        "draftSource": "stable-closeout-receipt",
        "receiptPath": "runtime-artifacts/mission-evidence/platform-runtime/closeout.json",
        "sourceEndpoint": "http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
        "autonomyCycleArtifactPath": ".github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json",
        "nextActionOrderingSource": "artifact",
        "matchedSelectedJobIds": ["overnight-lane-platform-runtime-token1234"],
    }


def test_resolve_job_branch_omits_auto_branch_for_same_control_plane_jobs(tmp_path, monkeypatch):
    queue_path = tmp_path / "overnight-queue.json"
    queue_path.write_text(
        json.dumps(_queue_payload("overnight-lane-platform-runtime-token1234"), indent=2),
        encoding="utf-8",
    )

    monkeypatch.setattr(watchdog, "QUEUE_PATH", queue_path)

    assert watchdog.resolve_job_branch("overnight-lane-platform-runtime-token1234") == ""


def test_run_check_accepts_gateway_name_field(monkeypatch):
    monkeypatch.setattr(watchdog, "check_gateway_health", lambda: (True, "healthy"))
    monkeypatch.setattr(
        watchdog,
        "poll_cron_jobs",
        lambda: [
            {
                "name": "bijmantra:overnight-lane-platform-runtime-token1234",
                "state": {
                    "lastRunStatus": "error",
                    "lastError": "auth missing",
                    "consecutiveErrors": 1,
                },
            }
        ],
    )
    monkeypatch.setattr(
        watchdog.WatchdogState,
        "save",
        lambda self, path=watchdog.WATCHDOG_STATE: None,
    )

    state = watchdog.WatchdogState()
    watchdog.run_check(state)

    assert len(state.jobs) == 1
    assert state.jobs[0].job_id == "overnight-lane-platform-runtime-token1234"
    assert state.jobs[0].status == "failed"
    assert state.jobs[0].last_error == "auth missing"
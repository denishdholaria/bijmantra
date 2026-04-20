from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.run_overnight_queue import build_plan, load_completion_assist, validate_queue


def test_build_plan_projects_reviewed_queue_provenance():
    queue = {
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
                "jobId": "overnight-lane-platform-runtime-token1234",
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
                    "boardTitle": "Queue Writer",
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

    plan = build_plan(queue, "nightly", 1)

    assert plan["selectedJobCount"] == 1
    assert plan["selectedJobs"][0]["provenance"] == queue["jobs"][0]["provenance"]


def test_build_plan_prefers_reviewed_entries_within_priority_band():
    queue = {
        "version": 1,
        "updatedAt": "2026-03-25T00:00:00Z",
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
                "jobId": "overnight-lane-alpha-priority-job",
                "title": "Higher Priority Generic Job",
                "status": "queued",
                "priority": "p1",
                "primaryAgent": "OmShriMaatreNamaha",
                "supportAgents": [],
                "executionMode": "same-control-plane",
                "autonomousTrigger": {
                    "type": "overnight-window",
                    "window": "nightly",
                    "enabled": True,
                },
                "dependsOn": [],
                "goal": "Run the higher priority generic slice.",
                "lane": {
                    "objective": "Run the higher priority generic slice.",
                    "inputs": ["queue"],
                    "outputs": ["evidence"],
                    "dependencies": [],
                    "completion_criteria": ["Evidence is recorded"],
                },
                "successCriteria": ["Evidence is recorded"],
                "verification": {
                    "commands": ["echo verify alpha"],
                    "stateRefreshRequired": True,
                },
            },
            {
                "jobId": "overnight-lane-beta-generic-job",
                "title": "Same Priority Generic Job",
                "status": "queued",
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
                "goal": "Run the same-priority generic slice.",
                "lane": {
                    "objective": "Run the same-priority generic slice.",
                    "inputs": ["queue"],
                    "outputs": ["evidence"],
                    "dependencies": [],
                    "completion_criteria": ["Evidence is recorded"],
                },
                "successCriteria": ["Evidence is recorded"],
                "verification": {
                    "commands": ["echo verify beta"],
                    "stateRefreshRequired": True,
                },
            },
            {
                "jobId": "overnight-lane-platform-runtime-token1234",
                "title": "Reviewed Platform Runtime",
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
                    "exportedAt": "2026-03-25T00:00:00Z",
                    "boardId": "bijmantra-app-development-master-board",
                    "boardTitle": "Queue Writer",
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
                    "objective": "Run the reviewed platform runtime slice.",
                    "inputs": ["board"],
                    "outputs": ["runtime evidence"],
                    "dependencies": [],
                    "completion_criteria": ["Evidence is reviewed"],
                },
                "successCriteria": ["Evidence is reviewed"],
                "verification": {
                    "commands": ["echo verify runtime"],
                    "stateRefreshRequired": True,
                },
            },
        ],
    }

    plan = build_plan(queue, "nightly", 2)

    assert plan["selectedJobCount"] == 2
    assert [job["jobId"] for job in plan["selectedJobs"]] == [
        "overnight-lane-alpha-priority-job",
        "overnight-lane-platform-runtime-token1234",
    ]


def test_validate_queue_accepts_closeout_and_watchdog_triggers():
    queue = {
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
                "jobId": "closeout-follow-up",
                "title": "Closeout Follow Up",
                "status": "queued",
                "priority": "p2",
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
                "goal": "React to stable closeout evidence.",
                "lane": {
                    "objective": "React to stable closeout evidence.",
                    "inputs": ["closeout receipt"],
                    "outputs": ["follow-up decision"],
                    "dependencies": [],
                    "completion_criteria": ["A follow-up decision exists."],
                },
                "successCriteria": ["A follow-up decision exists."],
                "verification": {"commands": []},
            },
            {
                "jobId": "watchdog-remediation",
                "title": "Watchdog Remediation",
                "status": "queued",
                "priority": "p1",
                "primaryAgent": "OmShriMaatreNamaha",
                "supportAgents": [],
                "executionMode": "same-control-plane",
                "autonomousTrigger": {
                    "type": "watchdog-alert",
                    "state": "job-error",
                    "jobId": "runtime-job",
                    "enabled": True,
                },
                "dependsOn": [],
                "goal": "Investigate watchdog job failure.",
                "lane": {
                    "objective": "Investigate watchdog job failure.",
                    "inputs": ["watchdog state"],
                    "outputs": ["remediation plan"],
                    "dependencies": [],
                    "completion_criteria": ["A remediation plan exists."],
                },
                "successCriteria": ["A remediation plan exists."],
                "verification": {"commands": []},
            },
        ],
    }

    assert validate_queue(queue) == queue


def test_build_plan_selects_closeout_triggered_job_when_receipt_exists():
    queue = {
        "version": 1,
        "updatedAt": "2026-04-05T00:00:00Z",
        "language": "en",
        "vocabularyPolicy": "english-technical-only",
        "defaults": {
            "window": "nightly",
            "stateRefreshRequired": True,
            "closeoutCommands": ["make update-state"],
            "maxJobsPerRun": 1,
        },
        "jobs": [
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
                "goal": "React to runtime closeout evidence.",
                "lane": {
                    "objective": "React to runtime closeout evidence.",
                    "inputs": ["closeout receipt"],
                    "outputs": ["follow-up work"],
                    "dependencies": [],
                    "completion_criteria": ["Follow-up work is staged."],
                },
                "successCriteria": ["Follow-up work is staged."],
                "verification": {"commands": []},
            }
        ],
    }

    plan = build_plan(
        queue,
        "nightly",
        1,
        runtime_context={
            "closeoutReceipts": {
                "runtime-job": {
                    "exists": True,
                    "closeoutStatus": "passed",
                }
            }
        },
    )

    assert plan["selectedJobCount"] == 1
    assert plan["selectedJobs"][0]["jobId"] == "closeout-follow-up"
    assert plan["selectedJobs"][0]["triggerReason"] == "closeout-receipt:runtime-job:passed"


def test_build_plan_selects_watchdog_alert_job_when_job_error_exists():
    queue = {
        "version": 1,
        "updatedAt": "2026-04-05T00:00:00Z",
        "language": "en",
        "vocabularyPolicy": "english-technical-only",
        "defaults": {
            "window": "nightly",
            "stateRefreshRequired": True,
            "closeoutCommands": ["make update-state"],
            "maxJobsPerRun": 1,
        },
        "jobs": [
            {
                "jobId": "watchdog-remediation",
                "title": "Watchdog Remediation",
                "status": "queued",
                "priority": "p1",
                "primaryAgent": "OmShriMaatreNamaha",
                "supportAgents": [],
                "executionMode": "same-control-plane",
                "autonomousTrigger": {
                    "type": "watchdog-alert",
                    "state": "job-error",
                    "jobId": "runtime-job",
                    "enabled": True,
                },
                "dependsOn": [],
                "goal": "React to watchdog job error.",
                "lane": {
                    "objective": "React to watchdog job error.",
                    "inputs": ["watchdog state"],
                    "outputs": ["remediation work"],
                    "dependencies": [],
                    "completion_criteria": ["Remediation work is staged."],
                },
                "successCriteria": ["Remediation work is staged."],
                "verification": {"commands": []},
            }
        ],
    }

    plan = build_plan(
        queue,
        "nightly",
        1,
        runtime_context={
            "watchdog": {
                "exists": True,
                "stateIsStale": False,
                "gatewayHealthy": True,
                "totalAlerts": 1,
                "jobErrors": {
                    "runtime-job": {
                        "lastError": "verification failed",
                        "consecutiveErrors": 2,
                    }
                },
            }
        },
    )

    assert plan["selectedJobCount"] == 1
    assert plan["selectedJobs"][0]["jobId"] == "watchdog-remediation"
    assert plan["selectedJobs"][0]["triggerReason"] == "watchdog-alert:job-error:runtime-job"


def test_load_completion_assist_returns_none_when_missing(tmp_path):
    assert load_completion_assist(tmp_path / "missing-completion-assist.json") is None


def test_build_plan_surfaces_completion_assist_as_advisory_input_without_changing_selection():
    queue = {
        "version": 1,
        "updatedAt": "2026-04-06T00:00:00Z",
        "language": "en",
        "vocabularyPolicy": "english-technical-only",
        "defaults": {
            "window": "nightly",
            "stateRefreshRequired": True,
            "closeoutCommands": ["make update-state"],
            "maxJobsPerRun": 1,
        },
        "jobs": [
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
                    "queueJobId": "overnight-lane-control-plane-token1234",
                    "closeoutStatus": ["passed"],
                    "enabled": True,
                },
                "dependsOn": [],
                "goal": "React to runtime closeout evidence.",
                "lane": {
                    "objective": "React to runtime closeout evidence.",
                    "inputs": ["closeout receipt"],
                    "outputs": ["follow-up work"],
                    "dependencies": [],
                    "completion_criteria": ["Follow-up work is staged."],
                },
                "successCriteria": ["Follow-up work is staged."],
                "verification": {"commands": []},
            }
        ],
    }

    plan = build_plan(
        queue,
        "nightly",
        1,
        runtime_context={
            "closeoutReceipts": {
                "overnight-lane-control-plane-token1234": {
                    "exists": True,
                    "closeoutStatus": "passed",
                }
            },
            "completionAssistPath": ".github/docs/architecture/tracking/developer-control-plane-completion-assist.json",
            "completionAssist": {
                "generatedAt": "2026-04-06T12:05:00+00:00",
                "status": "staged",
                "staged": True,
                "explicitWriteRequired": True,
                "message": (
                    "Staged reviewed completion assist for lane control-plane. "
                    "This artifact does not perform explicit board write-back."
                ),
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
        },
    )

    assert plan["selectedJobCount"] == 1
    assert plan["selectedJobs"][0]["jobId"] == "closeout-follow-up"
    assert plan["selectedJobs"][0]["triggerReason"] == (
        "closeout-receipt:overnight-lane-control-plane-token1234:passed"
    )
    assert plan["advisoryInputs"]["completionAssist"] == {
        "available": True,
        "artifactPath": ".github/docs/architecture/tracking/developer-control-plane-completion-assist.json",
        "status": "staged",
        "staged": True,
        "explicitWriteRequired": True,
        "message": (
            "Staged reviewed completion assist for lane control-plane. "
            "This artifact does not perform explicit board write-back."
        ),
        "sourceLaneId": "control-plane",
        "queueJobId": "overnight-lane-control-plane-token1234",
        "draftSource": "stable-closeout-receipt",
        "receiptPath": "runtime-artifacts/mission-evidence/job/closeout.json",
        "sourceEndpoint": "http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle",
        "autonomyCycleArtifactPath": ".github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json",
        "nextActionOrderingSource": "canonical-learning-exact-runtime",
        "matchedSelectedJobIds": ["closeout-follow-up"],
    }
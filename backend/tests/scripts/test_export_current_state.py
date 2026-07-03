import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import scripts.export_current_state as export_current_state


def test_overnight_queue_summary_surfaces_completion_assist_advisory(
    tmp_path, monkeypatch
):
    repo_root = tmp_path
    queue_path = repo_root / ".agent" / "jobs" / "overnight-queue.json"
    plan_path = (
        repo_root
        / ".github"
        / "docs"
        / "architecture"
        / "tracking"
        / "overnight-dispatch-plan.json"
    )
    completion_assist_path = (
        repo_root
        / ".github"
        / "docs"
        / "architecture"
        / "tracking"
        / "developer-control-plane-completion-assist.json"
    )
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.parent.mkdir(parents=True, exist_ok=True)

    queue_path.write_text(
        json.dumps(
            {
                "language": "en",
                "vocabularyPolicy": "english-technical-only",
                "jobs": [
                    {
                        "jobId": "overnight-lane-control-plane-token1234",
                        "title": "Control Plane Runtime",
                        "status": "queued",
                        "priority": "p1",
                        "primaryAgent": "OmShriMaatreNamaha",
                        "executionMode": "same-control-plane",
                        "lane": {"objective": "Inspect control-plane runtime state."},
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    plan_path.write_text(
        json.dumps(
            {
                "generatedAt": "2026-04-06T13:05:00+00:00",
                "language": "en",
                "vocabularyPolicy": "english-technical-only",
                "window": "nightly",
                "selectedJobCount": 1,
                "blockedJobCount": 0,
                "selectedJobs": [{"jobId": "overnight-lane-control-plane-token1234"}],
                "advisoryInputs": {
                    "completionAssist": {
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

    monkeypatch.setattr(export_current_state, "ROOT", repo_root)
    monkeypatch.setattr(export_current_state, "OVERNIGHT_QUEUE_PATH", queue_path)
    monkeypatch.setattr(export_current_state, "OVERNIGHT_PLAN_PATH", plan_path)
    monkeypatch.setattr(
        export_current_state,
        "COMPLETION_ASSIST_PATH",
        completion_assist_path,
    )

    summary = export_current_state.overnight_queue_summary()

    assert summary["latestPlan"]["selectedJobIds"] == [
        "overnight-lane-control-plane-token1234"
    ]
    assert summary["latestPlan"]["advisoryInputs"]["completionAssist"] == {
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
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _load_private_ops_module import load_private_ops_module


ctl = load_private_ops_module(
    "krabi_test_bijmantra_ctl",
    "ops-private/claw-runtime/scripts/bijmantra_ctl.py",
)


def test_summarize_evidence_for_review_marks_closeout_status():
    summary = ctl.summarize_evidence_for_review(
        Path("closeout.json"),
        {
            "type": "closeout",
            "timestamp": "2026-03-19T12:00:00Z",
            "data": {
                "status": "passed",
                "artifacts": [{"path": "metrics.json"}, {"path": "current-app-state.json"}],
            },
        },
    )

    assert summary == "✓ closeout (passed) at 2026-03-19T12:00:00Z [2 artifacts]"


def test_render_evidence_detail_lines_expands_closeout_receipt():
    lines = ctl.render_evidence_detail_lines(
        Path("closeout.json"),
        {
            "type": "closeout",
            "timestamp": "2026-03-19T12:00:00Z",
            "data": {
                "status": "passed",
                "queueJobId": "overnight-lane-platform-runtime-token1234",
                "queueSha256AtWrite": "abc123def456",
                "verificationEvidenceRef": "runtime-artifacts/mission-evidence/job/verification_1.json",
                "closeoutCommands": [
                    {"command": "make update-state", "passed": True, "exitCode": 0}
                ],
                "artifacts": [
                    {"path": "metrics.json", "exists": True, "sha256": "1122334455667788"},
                    {
                        "path": "confidential-docs/architecture/tracking/current-app-state.json",
                        "exists": True,
                        "sha256": "aabbccddeeff0011",
                    },
                ],
            },
        },
    )

    assert "  Status:    passed" in lines
    assert "  Queue Job: overnight-lane-platform-runtime-token1234" in lines
    assert "  closeoutCommands:" in lines
    assert "    • ✓ make update-state (exit=0)" in lines
    assert "  artifacts:" in lines
    assert "    • metrics.json exists=True sha256=112233445566" in lines


def test_cmd_sync_runs_canonical_private_bridge(monkeypatch, tmp_path):
    pause_file = tmp_path / ".paused"
    monkeypatch.setattr(ctl, "PAUSE_FILE", pause_file)

    recorded = {}

    def fake_run(command, **kwargs):
        recorded["command"] = command
        recorded["kwargs"] = kwargs
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(ctl.subprocess, "run", fake_run)

    result = ctl.cmd_sync(argparse.Namespace())

    assert result == 0
    assert recorded["command"][0] == sys.executable
    assert recorded["command"][1].endswith("ops-private/claw-runtime/scripts/bijmantra_cron_bridge.py")
    assert recorded["command"][2:] == ["--apply", "--verbose"]
    assert recorded["kwargs"]["cwd"] == str(ctl.ROOT)
    assert recorded["kwargs"]["text"] is True


def test_resolve_runtime_status_prefers_watchdog_overlay():
    status = ctl.resolve_runtime_status(
        {
            "jobId": "overnight-lane-platform-runtime-token1234",
            "status": "queued",
        },
        {"overnight-lane-platform-runtime-token1234": "completed"},
    )

    assert status == "completed"


def test_cmd_status_marks_stale_watchdog_snapshot(monkeypatch, capsys):
    monkeypatch.setattr(ctl, "PAUSE_FILE", Path("/tmp/does-not-exist"))
    monkeypatch.setattr(
        ctl,
        "load_watchdog_state",
        lambda: {
            "lastCheck": "2026-03-20T08:29:26.506880+00:00",
            "gatewayHealthy": True,
            "totalAlerts": 2,
            "jobs": [],
        },
    )
    monkeypatch.setattr(ctl, "load_queue", lambda: {"jobs": []})
    monkeypatch.setattr(ctl, "watchdog_snapshot_metadata", lambda _state: (900, True))

    result = ctl.cmd_status(argparse.Namespace())

    assert result == 0
    output = capsys.readouterr().out
    assert "Gateway: ! stale watchdog snapshot (last reported healthy)" in output
    assert "Checked: 2026-03-20T08:29:26.506880+00:00 (stale) [900s old]" in output


def test_cmd_queue_ignores_stale_watchdog_overlay(monkeypatch, capsys):
    monkeypatch.setattr(
        ctl,
        "load_queue",
        lambda: {
            "jobs": [
                {
                    "jobId": "overnight-lane-platform-runtime-token1234",
                    "priority": "p2",
                    "status": "queued",
                    "executionMode": "same-control-plane",
                }
            ]
        },
    )
    monkeypatch.setattr(
        ctl,
        "load_watchdog_state",
        lambda: {
            "lastCheck": "2026-03-20T08:29:26.506880+00:00",
            "jobs": [
                {
                    "jobId": "overnight-lane-platform-runtime-token1234",
                    "status": "completed",
                }
            ],
        },
    )
    monkeypatch.setattr(ctl, "watchdog_snapshot_metadata", lambda _state: (900, True))

    result = ctl.cmd_queue(argparse.Namespace())

    assert result == 0
    output = capsys.readouterr().out
    assert "queued" in output
    assert "completed" not in output


def test_resolve_job_branch_omits_auto_branch_for_same_control_plane_jobs(monkeypatch):
    monkeypatch.setattr(
        ctl,
        "load_queue",
        lambda: {
            "jobs": [
                {
                    "jobId": "overnight-lane-platform-runtime-token1234",
                    "executionMode": "same-control-plane",
                }
            ]
        },
    )

    assert ctl.resolve_job_branch("overnight-lane-platform-runtime-token1234") is None


def test_cmd_review_reports_current_checkout_for_branchless_job(monkeypatch, capsys):
    monkeypatch.setattr(
        ctl,
        "load_queue",
        lambda: {
            "jobs": [
                {
                    "jobId": "overnight-lane-platform-runtime-token1234",
                    "executionMode": "same-control-plane",
                }
            ]
        },
    )
    monkeypatch.setattr(ctl, "load_job_evidence", lambda _job_id: [])

    def fake_git(*args, **kwargs):
        if args == ("status", "--short"):
            return SimpleNamespace(returncode=0, stdout=" M ops-private/claw-runtime/scripts/bijmantra_cron_bridge.py\n", stderr="")
        if args == ("diff", "--stat"):
            return SimpleNamespace(returncode=0, stdout=" ops-private/claw-runtime/scripts/bijmantra_cron_bridge.py | 4 +++-\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(ctl, "git", fake_git)

    result = ctl.cmd_review(argparse.Namespace(job_id="overnight-lane-platform-runtime-token1234"))

    assert result == 0
    output = capsys.readouterr().out
    assert "Workspace: current checkout (no branch)" in output
    assert "git diff" in output
    assert "no isolated branch is available" in output
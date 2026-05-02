#!/usr/bin/env python3
"""bijmantra-ctl — Human-in-the-loop control for BijMantra autonomous development.

This is the "stop anything that seems off" tool. It gives you full visibility
and control over the autonomous build system.

Usage:
    python ops-private/claw-runtime/scripts/bijmantra_ctl.py status          # What's happening right now
    python ops-private/claw-runtime/scripts/bijmantra_ctl.py queue           # Tonight's job queue
    python ops-private/claw-runtime/scripts/bijmantra_ctl.py stop <jobId>    # Stop a job immediately
    python ops-private/claw-runtime/scripts/bijmantra_ctl.py pause           # Pause all autonomous work
    python ops-private/claw-runtime/scripts/bijmantra_ctl.py resume          # Resume autonomous work
    python ops-private/claw-runtime/scripts/bijmantra_ctl.py review <jobId>  # Review changes from a job
    python ops-private/claw-runtime/scripts/bijmantra_ctl.py approve <jobId> # Approve and merge changes
    python ops-private/claw-runtime/scripts/bijmantra_ctl.py reject <jobId>  # Reject and revert changes
    python ops-private/claw-runtime/scripts/bijmantra_ctl.py logs <jobId>    # View job execution logs
    python ops-private/claw-runtime/scripts/bijmantra_ctl.py sync            # Sync job queue to OpenClaw
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import timedelta
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
QUEUE_PATH = ROOT / ".agent" / "jobs" / "overnight-queue.json"
sys.path.insert(0, str(ROOT / "backend" / "app" / "modules" / "ai" / "services"))

from claw_runtime_contract import (  # noqa: E402
    resolve_claw_runtime_home,
    runtime_cron_sync_state_path,
    runtime_mission_evidence_dir,
    runtime_pause_file_path,
    runtime_watchdog_state_path,
)

RUNTIME_HOME = resolve_claw_runtime_home(ROOT)
WATCHDOG_STATE = runtime_watchdog_state_path(RUNTIME_HOME)
CRON_SYNC_STATE = runtime_cron_sync_state_path(RUNTIME_HOME)
MISSION_DIR = runtime_mission_evidence_dir(RUNTIME_HOME)
PAUSE_FILE = runtime_pause_file_path(RUNTIME_HOME)
WATCHDOG_STATE_STALE_AFTER = timedelta(minutes=10)

logger = logging.getLogger("bijmantra-ctl")


# ── Helpers ──────────────────────────────────────────────────────────

def load_queue() -> dict:
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def load_queue_job(job_id: str) -> dict[str, Any] | None:
    try:
        queue = load_queue()
    except (FileNotFoundError, json.JSONDecodeError):
        return None

    for job in queue.get("jobs", []):
        if isinstance(job, dict) and job.get("jobId") == job_id:
            return job
    return None


def resolve_job_branch(job_id: str) -> str | None:
    job = load_queue_job(job_id)
    if job is None:
        return f"auto/{job_id}"
    if job.get("executionMode") == "same-control-plane":
        return None
    return f"auto/{job_id}"


def load_watchdog_state() -> dict:
    if WATCHDOG_STATE.exists():
        try:
            return json.loads(WATCHDOG_STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {
                "malformed_artifact": True,
                "error": str(exc),
                "gatewayHealthy": None,
                "lastCheck": "malformed",
            }
    return {}


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        capture_output=True, text=True, cwd=str(ROOT),
        check=check, timeout=60,
    )


def print_header(title: str) -> None:
    width = 60
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}")


def print_table(rows: list[list[str]], headers: list[str]) -> None:
    """Print a simple aligned table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))

    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(f"  {header_line}")
    print(f"  {'─' * len(header_line)}")
    for row in rows:
        line = "  ".join(
            (row[i] if i < len(row) else "").ljust(widths[i])
            for i in range(len(headers))
        )
        print(f"  {line}")


def load_job_evidence(job_id: str) -> list[tuple[Path, dict[str, Any]]]:
    """Load all evidence records for a job in stable sorted order."""
    evidence_dir = MISSION_DIR / job_id
    if not evidence_dir.exists():
        return []

    evidence_records: list[tuple[Path, dict[str, Any]]] = []
    for evidence_path in sorted(evidence_dir.iterdir()):
        try:
            data = json.loads(evidence_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            evidence_records.append((evidence_path, data))
    return evidence_records


def write_job_evidence(
    job_id: str,
    evidence_type: str,
    payload: dict[str, Any],
    *,
    filename: str,
) -> Path:
    """Persist a stable evidence record for a control-plane action."""
    evidence = {
        "jobId": job_id,
        "type": evidence_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "data": payload,
    }
    evidence_file = MISSION_DIR / job_id / filename
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    evidence_file.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence_file


def watchdog_job_status_map(watchdog_state: dict[str, Any]) -> dict[str, str]:
    """Build a runtime-status overlay for immutable reviewed queue entries."""
    jobs = watchdog_state.get("jobs", [])
    if not isinstance(jobs, list):
        return {}

    status_map: dict[str, str] = {}
    for job in jobs:
        if not isinstance(job, dict):
            continue
        job_id = job.get("jobId")
        status = job.get("status")
        if isinstance(job_id, str) and isinstance(status, str):
            status_map[job_id] = status
    return status_map


def resolve_runtime_status(job: dict[str, Any], runtime_statuses: dict[str, str]) -> str:
    """Prefer runtime-observed state over the reviewed queue snapshot."""
    job_id = job.get("jobId")
    if isinstance(job_id, str) and job_id in runtime_statuses:
        return runtime_statuses[job_id]
    status = job.get("status", "unknown")
    return status if isinstance(status, str) else "unknown"


def watchdog_snapshot_metadata(watchdog_state: dict[str, Any]) -> tuple[int | None, bool]:
    last_check = watchdog_state.get("lastCheck")
    if not watchdog_state:
        return None, False
    if not isinstance(last_check, str):
        return None, True
    normalized = last_check.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None, True

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    else:
        parsed = parsed.astimezone(UTC)

    age_seconds = max(0, int((datetime.now(UTC) - parsed).total_seconds()))
    return age_seconds, age_seconds > int(WATCHDOG_STATE_STALE_AFTER.total_seconds())


def summarize_evidence_for_review(evidence_path: Path, data: dict[str, Any]) -> str:
    """Build a concise one-line review summary for a mission evidence item."""
    evidence_type = data.get("type", "unknown")
    timestamp = data.get("timestamp", "")
    payload = data.get("data", {}) if isinstance(data.get("data"), dict) else {}

    if evidence_type == "verification":
        passed = payload.get("passed", False)
        symbol = "✓" if passed else "✗"
        return f"{symbol} verification at {timestamp}"

    if evidence_type == "closeout":
        status = payload.get("status", "unknown")
        artifacts = payload.get("artifacts", [])
        artifact_count = len(artifacts) if isinstance(artifacts, list) else 0
        symbol = "✓" if status in {"passed", "skipped"} else "✗"
        return f"{symbol} closeout ({status}) at {timestamp} [{artifact_count} artifacts]"

    return f"• {evidence_type} at {timestamp} ({evidence_path.name})"


def render_evidence_detail_lines(evidence_path: Path, data: dict[str, Any]) -> list[str]:
    """Render evidence details for the logs command with special handling for closeout receipts."""
    lines = [
        f"  Type:      {data.get('type', '?')}",
        f"  Timestamp: {data.get('timestamp', '?')}",
    ]
    payload = data.get("data", {}) if isinstance(data.get("data"), dict) else {}

    if data.get("type") == "closeout":
        lines.extend(
            [
                f"  Status:    {payload.get('status', '?')}",
                f"  Queue Job: {payload.get('queueJobId', '?')}",
                f"  Queue SHA: {payload.get('queueSha256AtWrite', '?')}",
                f"  Verified:  {payload.get('verificationEvidenceRef', '?')}",
            ]
        )

        closeout_commands = payload.get("closeoutCommands", [])
        if isinstance(closeout_commands, list) and closeout_commands:
            lines.append("  closeoutCommands:")
            for command in closeout_commands[:5]:
                if isinstance(command, dict):
                    cmd = command.get("command", "?")
                    passed = command.get("passed", False)
                    exit_code = command.get("exitCode", "?")
                    symbol = "✓" if passed else "✗"
                    lines.append(f"    • {symbol} {cmd} (exit={exit_code})")

        artifacts = payload.get("artifacts", [])
        if isinstance(artifacts, list) and artifacts:
            lines.append("  artifacts:")
            for artifact in artifacts[:5]:
                if isinstance(artifact, dict):
                    path = artifact.get("path", "?")
                    exists = artifact.get("exists", False)
                    sha256 = artifact.get("sha256", "")
                    lines.append(
                        f"    • {path} exists={exists} sha256={(sha256 or '')[:12]}"
                    )
        return lines

    for key, value in payload.items():
        if isinstance(value, list):
            lines.append(f"  {key}:")
            for item in value[:5]:
                if isinstance(item, dict):
                    lines.append(f"    • {json.dumps(item)[:80]}")
                else:
                    lines.append(f"    • {item}")
        else:
            lines.append(f"  {key}: {value}")

    if data.get("type") not in {"verification", "closeout", "approval", "rejection"}:
        lines.append(f"  Source:    {evidence_path.name}")
    return lines


# ── Commands ─────────────────────────────────────────────────────────

def cmd_status(_args: argparse.Namespace) -> int:
    """Show current system status."""
    print_header("BijMantra Autonomous Build — Status")

    # Pause state
    paused = PAUSE_FILE.exists()
    print(f"\n  System:  {'⏸  PAUSED' if paused else '▶  ACTIVE'}")

    # Gateway health
    wdog = load_watchdog_state()
    gw_healthy = wdog.get("gatewayHealthy", None)
    state_age_seconds, state_is_stale = watchdog_snapshot_metadata(wdog)
    
    if wdog.get("malformed_artifact"):
        print(f"  Gateway: ! Malformed watchdog artifact ({wdog.get('error', 'parse failed')})")
    elif state_is_stale:
        if gw_healthy is True:
            print("  Gateway: ! stale watchdog snapshot (last reported healthy)")
        elif gw_healthy is False:
            print("  Gateway: ! stale watchdog snapshot (last reported unhealthy)")
        else:
            print("  Gateway: ! stale watchdog snapshot")
    elif gw_healthy is True:
        print("  Gateway: ✓ healthy")
    elif gw_healthy is False:
        print("  Gateway: ✗ unhealthy")
    else:
        print("  Gateway: ? unknown (run watchdog first)")

    last_check = wdog.get("lastCheck", "never")
    stale_suffix = " (stale)" if state_is_stale else ""
    age_suffix = f" [{state_age_seconds}s old]" if state_age_seconds is not None else ""
    print(f"  Checked: {last_check}{stale_suffix}{age_suffix}")
    print(f"  Alerts:  {wdog.get('totalAlerts', 0)} total")

    # Job summary from queue
    try:
        queue = load_queue()
        jobs = queue.get("jobs", [])
        runtime_statuses = watchdog_job_status_map(wdog)
        counts = {}
        for j in jobs:
            s = resolve_runtime_status(j, runtime_statuses)
            counts[s] = counts.get(s, 0) + 1
        parts = [f"{v} {k}" for k, v in sorted(counts.items())]
        print(f"  Jobs:    {', '.join(parts) or 'none'}")
    except (FileNotFoundError, json.JSONDecodeError):
        print("  Jobs:    (queue not found)")

    # Active jobs from watchdog
    wdog_jobs = wdog.get("jobs", [])
    if wdog_jobs:
        section_title = "Watchdog Snapshot Jobs (stale):" if state_is_stale else "Active Jobs:"
        print(f"\n  {section_title}")
        rows = []
        for j in wdog_jobs:
            sym = {
                "running": "▶", "completed": "✓", "failed": "✗",
                "timed-out": "⏰", "stuck": "⏳",
            }.get(j.get("status", ""), "?")
            rows.append([
                f"{sym} {j.get('jobId', '?')}",
                j.get("status", "?"),
                f"{j.get('durationMinutes', 0):.0f}m",
                j.get("branch", ""),
            ])
        print_table(rows, ["Job", "Status", "Duration", "Branch"])

    print()
    return 0


def cmd_queue(_args: argparse.Namespace) -> int:
    """Show the job queue."""
    print_header("Job Queue")
    try:
        queue = load_queue()
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"\n  ✗ Failed to load queue: {exc}")
        return 1

    rows = []
    watchdog_state = load_watchdog_state()
    _, state_is_stale = watchdog_snapshot_metadata(watchdog_state)
    runtime_statuses = {} if state_is_stale else watchdog_job_status_map(watchdog_state)
    for j in queue.get("jobs", []):
        runtime_status = resolve_runtime_status(j, runtime_statuses)
        sym = {
            "queued": "○", "running": "▶", "completed": "✓",
            "failed": "✗", "cancelled": "⊘", "blocked": "◆",
        }.get(runtime_status, "?")
        rows.append([
            f"{sym} {j['jobId'][:40]}",
            j.get("priority", "?"),
            runtime_status,
            j.get("executionMode", "?")[:20],
        ])

    print()
    print_table(rows, ["Job ID", "Pri", "Status", "Mode"])
    print()
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    """Stop a specific job."""
    job_id = args.job_id
    print(f"Stopping job: {job_id}...")

    # Try to stop via OpenClaw CLI
    try:
        result = subprocess.run(
            ["openclaw", "cron", "disable", f"bijmantra:{job_id}"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            print(f"  ✓ Cron job disabled")
        else:
            print(f"  ⚠ Could not disable cron job: {result.stderr.strip()}")
    except FileNotFoundError:
        print("  ⚠ openclaw CLI not found")

    write_job_evidence(
        job_id,
        "control-action",
        {
            "action": "stop",
            "requestedBy": "bijmantra-ctl",
            "queueImmutable": True,
        },
        filename="stop-request.json",
    )
    print("  ✓ Stop request recorded as evidence")
    print("  ✓ Reviewed queue left unchanged")

    print(f"  Done. Job {job_id} has been stopped.")
    return 0


def cmd_pause(_args: argparse.Namespace) -> int:
    """Pause all autonomous execution."""
    PAUSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PAUSE_FILE.write_text(
        json.dumps({
            "pausedAt": datetime.now(UTC).isoformat(),
            "pausedBy": "bijmantra-ctl",
        }),
        encoding="utf-8",
    )

    # Disable all bijmantra cron jobs
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            jobs = json.loads(result.stdout)
            jobs = jobs.get("jobs", jobs) if isinstance(jobs, dict) else jobs
            for j in jobs:
                label = j.get("label", "")
                if label.startswith("bijmantra:"):
                    subprocess.run(
                        ["openclaw", "cron", "disable", label],
                        capture_output=True, timeout=15,
                    )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    print("⏸  All autonomous execution PAUSED")
    print("  Run `bijmantra-ctl resume` to restart")
    return 0


def cmd_resume(_args: argparse.Namespace) -> int:
    """Resume autonomous execution."""
    if PAUSE_FILE.exists():
        PAUSE_FILE.unlink()

    # Re-enable all bijmantra cron jobs
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            jobs = json.loads(result.stdout)
            jobs = jobs.get("jobs", jobs) if isinstance(jobs, dict) else jobs
            for j in jobs:
                label = j.get("label", "")
                if label.startswith("bijmantra:"):
                    subprocess.run(
                        ["openclaw", "cron", "enable", label],
                        capture_output=True, timeout=15,
                    )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    print("▶  Autonomous execution RESUMED")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    """Review changes from a completed job."""
    job_id = args.job_id
    branch = resolve_job_branch(job_id)

    print_header(f"Review: {job_id}")

    if not branch:
        print("\n  Workspace: current checkout (no branch)")
        result = git("status", "--short", check=False)
        if result.stdout.strip():
            print("\n  Working tree:")
            for line in result.stdout.strip().split("\n"):
                print(f"    {line}")

        result = git("diff", "--stat", check=False)
        if result.stdout.strip():
            print("\n  Changed files:")
            for line in result.stdout.strip().split("\n"):
                print(f"    {line}")

        evidence_records = load_job_evidence(job_id)
        if evidence_records:
            print("\n  Evidence:")
            for evidence_path, data in evidence_records:
                print(f"    {summarize_evidence_for_review(evidence_path, data)}")

        print("\n  To see full diff:")
        print("    git diff")
        print("\n  This job used the current checkout, so no isolated branch is available for automatic merge/reject.")
        print()
        return 0

    # Check if branch exists
    result = git("branch", "--list", branch, check=False)
    if not result.stdout.strip():
        # Try remote
        result = git("branch", "-r", "--list", f"origin/{branch}", check=False)
        if not result.stdout.strip():
            print(f"\n  ✗ Branch '{branch}' not found (local or remote)")
            return 1
        # Fetch and checkout
        git("fetch", "origin", branch, check=False)
        git("checkout", "-b", branch, f"origin/{branch}", check=False)

    # Show diff summary
    print(f"\n  Branch: {branch}")
    result = git("log", "--oneline", f"main..{branch}", check=False)
    commits = result.stdout.strip().split("\n") if result.stdout.strip() else []
    print(f"  Commits: {len(commits)}")
    for c in commits[:10]:
        print(f"    {c}")
    if len(commits) > 10:
        print(f"    ... and {len(commits) - 10} more")

    # Show changed files
    result = git("diff", "--stat", f"main...{branch}", check=False)
    if result.stdout:
        print(f"\n  Changed files:")
        for line in result.stdout.strip().split("\n"):
            print(f"    {line}")

    # Show verification evidence
    evidence_records = load_job_evidence(job_id)
    if evidence_records:
        print(f"\n  Evidence:")
        for evidence_path, data in evidence_records:
            print(f"    {summarize_evidence_for_review(evidence_path, data)}")

    print(f"\n  To see full diff:")
    print(f"    git diff main...{branch}")
    print(f"\n  To approve:")
    print(f"    python ops-private/claw-runtime/scripts/bijmantra_ctl.py approve {job_id}")
    print(f"\n  To reject:")
    print(f"    python ops-private/claw-runtime/scripts/bijmantra_ctl.py reject {job_id}")
    print()
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    """Approve and merge changes from a completed job."""
    job_id = args.job_id
    branch = resolve_job_branch(job_id)

    print(f"Approving job: {job_id}")

    if not branch:
        write_job_evidence(
            job_id,
            "approval",
            {
                "approvedBy": "human",
                "reviewMode": "working-tree",
                "queueImmutable": True,
            },
            filename="approval.json",
        )
        print("  ✓ Approval evidence recorded")
        print("  ✓ No isolated branch was used for this job")
        print("  Review and keep or discard the current working-tree changes manually")
        return 0

    # Ensure we're on main
    git("checkout", "main", check=False)
    git("pull", "--rebase", "origin", "main", check=False)

    # Merge the branch
    result = git("merge", "--no-ff", "-m", f"[auto] Merge {branch}: {job_id}", branch, check=False)
    if result.returncode != 0:
        print(f"  ✗ Merge failed:\n{result.stderr}")
        print(f"  Resolve conflicts manually, then commit.")
        return 1

    print(f"  ✓ Merged {branch} → main")

    write_job_evidence(
        job_id,
        "approval",
        {
            "approvedBy": "human",
            "branch": branch,
            "queueImmutable": True,
        },
        filename="approval.json",
    )

    print(f"  ✓ Evidence recorded")
    print(f"  ✓ Reviewed queue left unchanged")
    print(f"\n  Don't forget to push: git push origin main")
    return 0


def cmd_reject(args: argparse.Namespace) -> int:
    """Reject changes from a job (does NOT delete the branch)."""
    job_id = args.job_id
    branch = resolve_job_branch(job_id)

    print(f"Rejecting job: {job_id}")

    write_job_evidence(
        job_id,
        "rejection",
        {
            "rejectedBy": "human",
            "branch": branch,
            "reviewMode": "isolated-branch" if branch else "working-tree",
            "reason": args.reason or "",
            "queueImmutable": True,
        },
        filename="rejection.json",
    )

    print(f"  ✓ Evidence recorded")
    print(f"  ✓ Reviewed queue left unchanged")

    if not branch:
        print("  No isolated branch exists for automatic discard")
        print("  Revert the current working-tree changes manually if needed")
        return 0

    print(f"  Branch '{branch}' preserved for reference (delete manually if needed)")
    return 0


def cmd_logs(args: argparse.Namespace) -> int:
    """View execution logs for a job."""
    job_id = args.job_id

    # Check evidence directory
    evidence_records = load_job_evidence(job_id)
    if evidence_records:
        print_header(f"Evidence: {job_id}")
        for evidence_path, data in evidence_records:
            print(f"\n  ── {evidence_path.name} ──")
            for line in render_evidence_detail_lines(evidence_path, data):
                print(line)
    else:
        print(f"No evidence found for {job_id}")

    # Show git log for the branch
    branch = resolve_job_branch(job_id)
    if branch:
        result = git("log", "--oneline", "-10", branch, check=False)
        if result.stdout:
            print(f"\n  Git log ({branch}):")
            for line in result.stdout.strip().split("\n"):
                print(f"    {line}")

    print()
    return 0


def cmd_sync(_args: argparse.Namespace) -> int:
    """Sync job queue to OpenClaw cron."""
    if PAUSE_FILE.exists():
        print("⏸  System is PAUSED. Resume first with: bijmantra-ctl resume")
        return 1

    bridge = Path(__file__).resolve().with_name("bijmantra_cron_bridge.py")
    result = subprocess.run(
        [sys.executable, str(bridge), "--apply", "--verbose"],
        text=True, cwd=str(ROOT),
    )
    return result.returncode


# ── Main ─────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bijmantra-ctl",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show system status")
    sub.add_parser("queue", help="Show job queue")

    stop_p = sub.add_parser("stop", help="Stop a running job")
    stop_p.add_argument("job_id", help="Job ID to stop")

    sub.add_parser("pause", help="Pause all autonomous execution")
    sub.add_parser("resume", help="Resume autonomous execution")

    review_p = sub.add_parser("review", help="Review changes from a job")
    review_p.add_argument("job_id", help="Job ID to review")

    approve_p = sub.add_parser("approve", help="Approve and merge changes")
    approve_p.add_argument("job_id", help="Job ID to approve")

    reject_p = sub.add_parser("reject", help="Reject changes from a job")
    reject_p.add_argument("job_id", help="Job ID to reject")
    reject_p.add_argument("--reason", help="Rejection reason", default="")

    logs_p = sub.add_parser("logs", help="View job logs and evidence")
    logs_p.add_argument("job_id", help="Job ID")

    sub.add_parser("sync", help="Sync queue to OpenClaw cron")

    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    commands = {
        "status": cmd_status,
        "queue": cmd_queue,
        "stop": cmd_stop,
        "pause": cmd_pause,
        "resume": cmd_resume,
        "review": cmd_review,
        "approve": cmd_approve,
        "reject": cmd_reject,
        "logs": cmd_logs,
        "sync": cmd_sync,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())

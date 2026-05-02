#!/usr/bin/env python3
"""BijMantra Watchdog — monitors autonomous agent execution 24/7.

Watches the OpenClaw Gateway for:
 - Job health (stuck, failed, timed out)
 - Path violations (agents touching restricted files)
 - Verification failures
 - Gateway health

Provides a kill switch to stop any job immediately.

Usage:
    # Start the watchdog (foreground)
    python ops-private/claw-runtime/scripts/bijmantra_watchdog.py

    # Start with custom check interval
    python ops-private/claw-runtime/scripts/bijmantra_watchdog.py --interval 60

    # Single check (no loop)
    python ops-private/claw-runtime/scripts/bijmantra_watchdog.py --once
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend" / "app" / "modules" / "ai" / "services"))

from claw_runtime_contract import (  # noqa: E402
    display_runtime_artifact_path,
    normalize_runtime_reference,
    resolve_claw_runtime_home,
    runtime_cron_sync_state_path,
    runtime_mission_evidence_dir,
    runtime_watchdog_log_path,
    runtime_watchdog_state_path,
)

RUNTIME_HOME = resolve_claw_runtime_home(ROOT)
CRON_SYNC_STATE = runtime_cron_sync_state_path(RUNTIME_HOME)
WATCHDOG_LOG = runtime_watchdog_log_path(RUNTIME_HOME)
WATCHDOG_STATE = runtime_watchdog_state_path(RUNTIME_HOME)
OPENCLAW_GATEWAY_CONTAINER_NAME = "bijmantra-openclaw-gateway"
OPENCLAW_CONTAINER_RUNTIME_HOME = "/home/node/.openclaw"
QUEUE_PATH = ROOT / ".agent" / "jobs" / "overnight-queue.json"
MISSION_DIR = runtime_mission_evidence_dir(RUNTIME_HOME)
TRACKING_DIR = ROOT / ".github" / "docs" / "architecture" / "tracking"
TRACKING_ARTIFACT_PATHS = (
    ROOT / "metrics.json",
    TRACKING_DIR / "overnight-dispatch-plan.json",
    TRACKING_DIR / "current-app-state.json",
)
BIJMANTRA_RUNTIME_PROFILE_ID_ENV = "BIJMANTRA_RUNTIME_PROFILE_ID"
DEFAULT_RUNTIME_PROFILE_ID = "bijmantra-bca-local-verify"
DEFAULT_RUNTIME_PRODUCER_KEY = "openclaw-runtime"
RUNTIME_POLICY_PROFILE_PATHS = {
    "bijmantra-bca-observe": ROOT / "ops-private" / "claw-runtime" / "policies" / "bijmantra-bca-observe.yaml",
    "bijmantra-bca-edit": ROOT / "ops-private" / "claw-runtime" / "policies" / "bijmantra-bca-edit.yaml",
    "bijmantra-bca-local-verify": ROOT / "ops-private" / "claw-runtime" / "policies" / "bijmantra-bca-local-verify.yaml",
}

logger = logging.getLogger("bijmantra-watchdog")

# Import PathGuard for file restriction checking from the staged private-ops boundary.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from sandbox_policy_manager import PathGuard
except ImportError:
    PathGuard = None  # type: ignore[assignment, misc]


# ── Data Types ───────────────────────────────────────────────────────

@dataclass
class JobStatus:
    job_id: str
    label: str
    status: str  # running, completed, failed, stuck, timed-out
    started_at: str = ""
    duration_minutes: float = 0.0
    last_error: str = ""
    consecutive_errors: int = 0
    branch: str = ""
    verification_passed: bool | None = None


@dataclass
class WatchdogState:
    last_check: str = ""
    gateway_healthy: bool = True
    jobs: list[JobStatus] = field(default_factory=list)
    alerts_sent: list[dict[str, Any]] = field(default_factory=list)
    total_checks: int = 0
    total_alerts: int = 0
    advisory_inputs: dict[str, Any] = field(default_factory=dict)
    ide_presence: dict[str, Any] = field(default_factory=dict)

    def save(self, path: Path = WATCHDOG_STATE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "lastCheck": self.last_check,
            "gatewayHealthy": self.gateway_healthy,
            "totalChecks": self.total_checks,
            "totalAlerts": self.total_alerts,
            "jobs": [
                {
                    "jobId": j.job_id,
                    "label": j.label,
                    "status": j.status,
                    "startedAt": j.started_at,
                    "durationMinutes": j.duration_minutes,
                    "lastError": j.last_error,
                    "consecutiveErrors": j.consecutive_errors,
                    "branch": j.branch,
                    "verificationPassed": j.verification_passed,
                }
                for j in self.jobs
            ],
            "recentAlerts": self.alerts_sent[-20:],
            "advisoryInputs": self.advisory_inputs,
            "idePresence": self.ide_presence,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = WATCHDOG_STATE) -> WatchdogState:
        if not path.exists():
            return cls()
        raw = json.loads(path.read_text(encoding="utf-8"))
        state = cls(
            last_check=raw.get("lastCheck", ""),
            gateway_healthy=raw.get("gatewayHealthy", True),
            total_checks=raw.get("totalChecks", 0),
            total_alerts=raw.get("totalAlerts", 0),
            advisory_inputs=(
                raw.get("advisoryInputs")
                if isinstance(raw.get("advisoryInputs"), dict)
                else {}
            ),
            ide_presence=(
                raw.get("idePresence")
                if isinstance(raw.get("idePresence"), dict)
                else {}
            ),
        )
        return state


# ── Gateway Health ───────────────────────────────────────────────────

def check_gateway_health(gateway_url: str = "http://127.0.0.1:18789") -> tuple[bool, str]:
    """Check if the OpenClaw Gateway is healthy."""
    try:
        import urllib.request
        req = urllib.request.Request(f"{gateway_url}/healthz", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                return True, "healthy"
            return False, f"unhealthy: status {resp.status}"
    except Exception as exc:
        return False, f"unreachable: {exc}"


# ── Cron Job Status Poller ───────────────────────────────────────────

def poll_cron_jobs() -> list[dict[str, Any]]:
    """Poll OpenClaw Gateway for cron job statuses via CLI."""
    try:
        result = subprocess.run(
            [
                "podman",
                "exec",
                "--env",
                f"OPENCLAW_CONFIG_DIR={OPENCLAW_CONTAINER_RUNTIME_HOME}",
                "--env",
                f"OPENCLAW_STATE_DIR={OPENCLAW_CONTAINER_RUNTIME_HOME}",
                "--env",
                f"OPENCLAW_CONFIG_PATH={OPENCLAW_CONTAINER_RUNTIME_HOME}/openclaw.json",
                OPENCLAW_GATEWAY_CONTAINER_NAME,
                "node",
                "openclaw.mjs",
                "cron",
                "list",
                "--json",
            ],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("jobs", []) if isinstance(data, dict) else data
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    # Fallback: read from sync state file
    if CRON_SYNC_STATE.exists():
        sync = json.loads(CRON_SYNC_STATE.read_text(encoding="utf-8"))
        return [
            {
                "label": j.get("label", ""),
                "status": "synced",
                "source": "file",
            }
            for j in sync.get("jobs", [])
        ]
    return []


# ── Git Change Monitoring ────────────────────────────────────────────

def get_changed_files_on_branch(branch: str) -> list[str]:
    """Get files changed on a branch compared to main."""
    if not branch:
        return []

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"main...{branch}"],
            capture_output=True, text=True, timeout=30,
            cwd=str(ROOT),
        )
        if result.returncode == 0:
            return [f for f in result.stdout.strip().split("\n") if f]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return []


def check_path_violations(job_id: str, branch: str) -> list[str]:
    """Check if an agent modified files outside its allowed paths."""
    if PathGuard is None or not branch:
        return []

    # Load job card to get allowed/blocked paths
    try:
        queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        job = next((j for j in queue["jobs"] if j["jobId"] == job_id), None)
        if not job:
            return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    guard = PathGuard.from_job_card(job)
    changed = get_changed_files_on_branch(branch)
    violations = []
    for filepath in changed:
        allowed, reason = guard.is_allowed(filepath)
        if not allowed:
            violations.append(f"{filepath}: {reason}")

    return violations


def resolve_job_branch(job_id: str) -> str:
    """Return the isolated review branch for jobs that use one."""
    try:
        queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return f"auto/{job_id}"

    for job in queue.get("jobs", []):
        if not isinstance(job, dict) or job.get("jobId") != job_id:
            continue
        if job.get("executionMode") == "same-control-plane":
            return ""
        return f"auto/{job_id}"

    return f"auto/{job_id}"


def _queue_token_suffix(source_board_concurrency_token: str) -> str:
    normalized = "".join(
        character
        for character in source_board_concurrency_token.lower()
        if character.isascii() and character.isalnum()
    )[:8]
    return normalized or "unknown000"


def _job_provenance(job: dict[str, Any]) -> dict[str, Any]:
    provenance = job.get("provenance")
    return provenance if isinstance(provenance, dict) else {}


def _resolve_runtime_profile_id() -> str:
    configured = os.getenv(BIJMANTRA_RUNTIME_PROFILE_ID_ENV, "").strip()
    return configured or DEFAULT_RUNTIME_PROFILE_ID


def _resolve_runtime_policy_sha256(profile_id: str) -> str | None:
    policy_path = RUNTIME_POLICY_PROFILE_PATHS.get(profile_id)
    if policy_path is None or not policy_path.exists():
        return None
    return hashlib.sha256(policy_path.read_bytes()).hexdigest()


def _derive_runtime_mission_id(
    job_id: str,
    source_lane_id: str | None,
    source_board_concurrency_token: str | None,
) -> str:
    if source_lane_id and source_board_concurrency_token:
        return f"runtime-mission-{source_lane_id}-{_queue_token_suffix(source_board_concurrency_token)}"
    return f"runtime-mission-{job_id}"


def _build_closeout_summary(
    *,
    closeout_commands: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    status: str,
    state_refresh_required: bool,
) -> dict[str, Any]:
    notes = "Closeout skipped because state refresh was not required."
    if state_refresh_required:
        notes = (
            "Closeout completed with state refresh."
            if status == "passed"
            else "Closeout attempted state refresh but one or more commands failed."
        )

    return {
        "commandsRun": len(closeout_commands),
        "artifactsRefreshed": sum(1 for artifact in artifacts if artifact.get("exists") is True),
        "verificationPassed": status in {"passed", "skipped"},
        "notes": notes,
    }


def _tracking_artifact_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def _tracking_artifact_path(*names: str) -> Path | None:
    allowed = set(names)
    for artifact_path in TRACKING_ARTIFACT_PATHS:
        if artifact_path.name in allowed:
            return artifact_path
    return None


def _load_json_object(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _optional_text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _normalize_completion_assist_advisory(
    payload: dict[str, Any],
    *,
    observed_from_path: Path,
) -> dict[str, Any]:
    return {
        "authority": _optional_text(payload.get("authority")) or "advisory-only-derived",
        "observedFromPath": _tracking_artifact_label(observed_from_path),
        "available": payload.get("available") is True,
        "artifactPath": _optional_text(payload.get("artifactPath")),
        "status": _optional_text(payload.get("status")),
        "staged": payload.get("staged") is True,
        "explicitWriteRequired": payload.get("explicitWriteRequired") is not False,
        "message": _optional_text(payload.get("message")),
        "sourceLaneId": _optional_text(payload.get("sourceLaneId")),
        "queueJobId": _optional_text(payload.get("queueJobId")),
        "draftSource": _optional_text(payload.get("draftSource")),
        "receiptPath": _optional_text(payload.get("receiptPath")),
        "sourceEndpoint": _optional_text(payload.get("sourceEndpoint")),
        "autonomyCycleArtifactPath": _optional_text(payload.get("autonomyCycleArtifactPath")),
        "nextActionOrderingSource": _optional_text(payload.get("nextActionOrderingSource")),
        "matchedSelectedJobIds": _text_list(payload.get("matchedSelectedJobIds")),
    }


def load_completion_assist_advisory() -> dict[str, Any] | None:
    current_state_path = _tracking_artifact_path("current-app-state.json")
    current_state = _load_json_object(current_state_path)
    if current_state is not None:
        application = current_state.get("application")
        orchestration = application.get("orchestration") if isinstance(application, dict) else None
        overnight_queue = (
            orchestration.get("overnightQueue") if isinstance(orchestration, dict) else None
        )
        latest_plan = overnight_queue.get("latestPlan") if isinstance(overnight_queue, dict) else None
        advisory_inputs = latest_plan.get("advisoryInputs") if isinstance(latest_plan, dict) else None
        completion_assist = (
            advisory_inputs.get("completionAssist")
            if isinstance(advisory_inputs, dict)
            else None
        )
        if isinstance(completion_assist, dict) and current_state_path is not None:
            return _normalize_completion_assist_advisory(
                completion_assist,
                observed_from_path=current_state_path,
            )

    dispatch_plan_path = _tracking_artifact_path("overnight-dispatch-plan.json")
    dispatch_plan = _load_json_object(dispatch_plan_path)
    if dispatch_plan is None:
        return None

    advisory_inputs = dispatch_plan.get("advisoryInputs")
    completion_assist = (
        advisory_inputs.get("completionAssist")
        if isinstance(advisory_inputs, dict)
        else None
    )
    if not isinstance(completion_assist, dict) or dispatch_plan_path is None:
        return None

    return _normalize_completion_assist_advisory(
        completion_assist,
        observed_from_path=dispatch_plan_path,
    )


def load_ide_presence() -> dict[str, Any]:
    """Parse the local bridge file to respect the active VS Code extension's authority."""
    presence_path = ROOT / ".agent" / "state" / "ide-presence.json"
    return _load_json_object(presence_path) or {}


def notify_ide(message: str, urgency: str) -> None:
    """Yield notification handling exclusively to the active IDE shell."""
    wakeup_path = ROOT / ".agent" / "state" / "wakeup.json"
    wakeup_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "message": message,
        "urgency": urgency
    }
    wakeup_path.write_text(json.dumps(payload, indent=2))


# ── Verification Runner ──────────────────────────────────────────────

def run_verification_commands(job_id: str) -> tuple[bool, list[dict[str, Any]]]:
    """Run verification commands from a job card and return results."""
    try:
        queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        job = next((j for j in queue["jobs"] if j["jobId"] == job_id), None)
        if not job:
            return False, [{"error": f"Job not found: {job_id}"}]
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return False, [{"error": str(exc)}]

    commands = job.get("verification", {}).get("commands", [])
    results = []
    all_passed = True

    for cmd in commands:
        try:
            proc = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=300, cwd=str(ROOT),
            )
            passed = proc.returncode == 0
            results.append({
                "command": cmd,
                "passed": passed,
                "returnCode": proc.returncode,
                "stdout": proc.stdout[-500:] if proc.stdout else "",
                "stderr": proc.stderr[-500:] if proc.stderr else "",
            })
            if not passed:
                all_passed = False
        except subprocess.TimeoutExpired:
            results.append({
                "command": cmd,
                "passed": False,
                "error": "timed out after 300s",
            })
            all_passed = False

    return all_passed, results


def run_closeout_commands(
    job_id: str,
    *,
    verification_evidence_ref: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    """Run post-verification closeout commands and build a stable closeout receipt."""
    try:
        queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        job = next((j for j in queue["jobs"] if j["jobId"] == job_id), None)
        if not job:
            return False, {"status": "failed", "error": f"Job not found: {job_id}"}
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return False, {"status": "failed", "error": str(exc)}

    defaults = queue.get("defaults", {}) if isinstance(queue, dict) else {}
    provenance = _job_provenance(job)
    source_lane_id = provenance.get("sourceLaneId") if isinstance(provenance.get("sourceLaneId"), str) else None
    source_board_concurrency_token = (
        provenance.get("sourceBoardConcurrencyToken")
        if isinstance(provenance.get("sourceBoardConcurrencyToken"), str)
        else None
    )
    runtime_profile_id = _resolve_runtime_profile_id()
    runtime_policy_sha256 = _resolve_runtime_policy_sha256(runtime_profile_id)
    normalized_verification_ref = normalize_runtime_reference(
        ROOT,
        RUNTIME_HOME,
        verification_evidence_ref,
    )
    state_refresh_required = bool(
        job.get("verification", {}).get(
            "stateRefreshRequired",
            defaults.get("stateRefreshRequired", True),
        )
    )
    commands = list(defaults.get("closeoutCommands", ["make update-state"]))
    queue_sha256_at_write = hashlib.sha256(
        json.dumps(queue, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    started_at = datetime.now(UTC).isoformat()
    mission_id = _derive_runtime_mission_id(job_id, source_lane_id, source_board_concurrency_token)

    if not state_refresh_required:
        finished_at = datetime.now(UTC).isoformat()
        artifacts = collect_tracking_artifacts()
        status = "skipped"
        return True, {
            "version": 1,
            "receiptType": "closeout",
            "queueJobId": job_id,
            "missionId": mission_id,
            "producerKey": DEFAULT_RUNTIME_PRODUCER_KEY,
            "sourceLaneId": source_lane_id,
            "sourceBoardConcurrencyToken": source_board_concurrency_token,
            "runtimeProfileId": runtime_profile_id,
            "runtimePolicySha256": runtime_policy_sha256,
            "queueSha256AtWrite": queue_sha256_at_write,
            "stateRefreshRequired": False,
            "status": status,
            "startedAt": started_at,
            "finishedAt": finished_at,
            "verificationEvidenceRef": normalized_verification_ref,
            "closeoutCommands": [],
            "artifacts": artifacts,
            "summary": _build_closeout_summary(
                closeout_commands=[],
                artifacts=artifacts,
                status=status,
                state_refresh_required=False,
            ),
        }

    results = []
    passed = True
    for cmd in commands:
        command_started_at = datetime.now(UTC).isoformat()
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(ROOT),
            )
            command_finished_at = datetime.now(UTC).isoformat()
            command_passed = proc.returncode == 0
            results.append(
                {
                    "command": cmd,
                    "exitCode": proc.returncode,
                    "passed": command_passed,
                    "stdoutTail": proc.stdout[-500:] if proc.stdout else "",
                    "stderrTail": proc.stderr[-500:] if proc.stderr else "",
                    "startedAt": command_started_at,
                    "finishedAt": command_finished_at,
                }
            )
            if not command_passed:
                passed = False
        except subprocess.TimeoutExpired:
            command_finished_at = datetime.now(UTC).isoformat()
            results.append(
                {
                    "command": cmd,
                    "exitCode": None,
                    "passed": False,
                    "stdoutTail": "",
                    "stderrTail": "timed out after 300s",
                    "startedAt": command_started_at,
                    "finishedAt": command_finished_at,
                }
            )
            passed = False

    finished_at = datetime.now(UTC).isoformat()
    status = "passed" if passed else "failed"
    artifacts = collect_tracking_artifacts()
    return passed, {
        "version": 1,
        "receiptType": "closeout",
        "queueJobId": job_id,
        "missionId": mission_id,
        "producerKey": DEFAULT_RUNTIME_PRODUCER_KEY,
        "sourceLaneId": source_lane_id,
        "sourceBoardConcurrencyToken": source_board_concurrency_token,
        "runtimeProfileId": runtime_profile_id,
        "runtimePolicySha256": runtime_policy_sha256,
        "queueSha256AtWrite": queue_sha256_at_write,
        "stateRefreshRequired": True,
        "status": status,
        "startedAt": started_at,
        "finishedAt": finished_at,
        "verificationEvidenceRef": normalized_verification_ref,
        "closeoutCommands": results,
        "artifacts": artifacts,
        "summary": _build_closeout_summary(
            closeout_commands=results,
            artifacts=artifacts,
            status=status,
            state_refresh_required=True,
        ),
    }


# ── Alert System ─────────────────────────────────────────────────────

def send_alert(
    level: str,
    title: str,
    details: str,
    state: WatchdogState,
) -> None:
    """Send an alert. Currently logs to file; can be extended to Telegram/Discord."""
    alert = {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": level,
        "title": title,
        "details": details,
    }

    state.alerts_sent.append(alert)
    state.total_alerts += 1

    # Supervisor Demotion: If IDE is active, pipe alert strictly to the bridge instead of isolated handlers
    if state.ide_presence.get("is_vscode_open") is True:
        logger.info("Supervisor demoting alert to IDE via wakeup bridge")
        notify_ide(f"[{level.upper()}] {title}\n{details}", urgency=level)
        return

    # Log to watchdog log file
    WATCHDOG_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(WATCHDOG_LOG, "a", encoding="utf-8") as fh:
        fh.write(f"[{alert['timestamp']}] [{level.upper()}] {title}\n")
        if details:
            for line in details.split("\n"):
                fh.write(f"  {line}\n")
        fh.write("\n")

    # Console output
    symbols = {"info": "ℹ", "warning": "⚠", "error": "✗", "critical": "🚨"}
    print(f"{symbols.get(level, '?')} [{level.upper()}] {title}")
    if details:
        print(f"  {details}")


# ── Mission Evidence Recording ───────────────────────────────────────

def record_evidence(
    job_id: str,
    evidence_type: str,
    data: dict[str, Any],
) -> Path:
    """Record verification evidence for a job in mission-state format."""
    evidence_dir = MISSION_DIR / job_id
    evidence_dir.mkdir(parents=True, exist_ok=True)

    evidence = {
        "jobId": job_id,
        "type": evidence_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "data": data,
    }

    filename = f"{evidence_type}_{int(time.time())}.json"
    evidence_path = evidence_dir / filename
    evidence_path.write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    return evidence_path


def write_stable_evidence(
    job_id: str,
    evidence_type: str,
    data: dict[str, Any],
    *,
    filename: str,
) -> Path:
    """Write a canonical evidence receipt with a stable filename."""
    evidence_dir = MISSION_DIR / job_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence = {
        "jobId": job_id,
        "type": evidence_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "data": data,
    }
    evidence_path = evidence_dir / filename
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence_path


def load_stable_evidence(job_id: str, filename: str) -> dict[str, Any] | None:
    """Load a canonical evidence receipt if it exists."""
    evidence_path = MISSION_DIR / job_id / filename
    if not evidence_path.exists():
        return None
    try:
        loaded = json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def collect_tracking_artifacts() -> list[dict[str, Any]]:
    """Capture the refreshed tracking artifacts that closeout is expected to update."""
    artifacts: list[dict[str, Any]] = []
    for artifact_path in TRACKING_ARTIFACT_PATHS:
        exists = artifact_path.exists()
        artifact = {
            "path": _tracking_artifact_label(artifact_path),
            "exists": exists,
            "sha256": None,
            "modifiedAt": None,
        }
        if exists:
            artifact["sha256"] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            artifact["modifiedAt"] = datetime.fromtimestamp(
                artifact_path.stat().st_mtime,
                tz=UTC,
            ).isoformat()
        artifacts.append(artifact)
    return artifacts


def note_runtime_status(job_id: str, new_status: str) -> None:
    """Record runtime lifecycle transitions without mutating the reviewed queue."""
    logger.info(
        "Runtime status for %s -> %s recorded via watchdog state and evidence; reviewed queue remains immutable",
        job_id,
        new_status,
    )


# ── IDE Mission Bridge ───────────────────────────────────────────────

try:
    from ide_mission_bridge import IdeMissionBridge
    _ide_bridge = IdeMissionBridge(ROOT)
except ImportError:
    _ide_bridge = None  # type: ignore[assignment]


def check_ide_mission_results(state: WatchdogState) -> None:
    """Check if the IDE has completed any dispatched missions and process results."""
    if _ide_bridge is None:
        return

    result = _ide_bridge._read_json(_ide_bridge.result_path)
    if not result or not isinstance(result.get("job_id"), str):
        return

    job_id = result["job_id"]
    status = result.get("status", "unknown")
    summary = result.get("summary", "")
    verification_results = result.get("verification_results", [])

    logger.info("IDE mission result for %s: %s", job_id, status)

    # Record as watchdog evidence
    record_evidence(job_id, "ide-mission-result", {
        "status": status,
        "summary": summary,
        "executor": result.get("executor", "vscode-copilot"),
        "iterations": result.get("iterations", 0),
        "verificationResults": verification_results,
        "completedAt": result.get("completed_at"),
    })

    if status == "completed":
        # Run closeout commands since the IDE verified successfully
        closeout_passed, closeout_receipt = run_closeout_commands(job_id)
        write_stable_evidence(
            job_id, "closeout", closeout_receipt, filename="closeout.json",
        )
        if closeout_passed:
            send_alert("info", f"IDE mission completed: {job_id}", summary, state)
            note_runtime_status(job_id, "completed")
        else:
            send_alert("warning", f"IDE mission closeout failed: {job_id}",
                       json.dumps(closeout_receipt, indent=2)[:500], state)
    elif status in ("failed", "stopped", "iteration-limit", "verification-failed"):
        send_alert("warning", f"IDE mission {status}: {job_id}", summary, state)
        record_evidence(job_id, "ide-mission-failure", {
            "status": status,
            "summary": summary,
        })
    else:
        logger.info("IDE mission %s has unrecognized status: %s", job_id, status)

    # Consume the result
    _ide_bridge.clear_result()


def dispatch_queued_jobs_to_ide(state: WatchdogState) -> list[str]:
    """If the IDE is active, dispatch eligible queued jobs via the bridge.

    Returns list of job IDs that were dispatched.
    """
    if _ide_bridge is None or not _ide_bridge.ide_is_active():
        return []

    # Don't dispatch if there's already a pending or in-progress dispatch
    pending = _ide_bridge.get_pending_dispatch()
    if pending is not None:
        return []

    try:
        queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    dispatched: list[str] = []
    for job in queue.get("jobs", []):
        if not isinstance(job, dict):
            continue
        job_id = job.get("jobId")
        if not isinstance(job_id, str):
            continue

        # Skip jobs that already have closeout evidence
        existing_closeout = load_stable_evidence(job_id, "closeout.json")
        if existing_closeout:
            continue

        # Skip jobs that already have an IDE result recorded
        existing_ide_result = load_stable_evidence(job_id, "ide-mission-result.json")
        if existing_ide_result:
            continue

        # Dispatch the first eligible job
        if _ide_bridge.dispatch_mission(job):
            dispatched.append(job_id)
            logger.info("Dispatched job %s to IDE via mission bridge", job_id)
            send_alert("info", f"Mission dispatched to IDE: {job_id}",
                       job.get("title", job_id), state)
            break  # One at a time

    return dispatched


# ── Main Check Loop ─────────────────────────────────────────────────

def run_check(state: WatchdogState, max_duration_minutes: int = 120) -> None:
    """Run a single watchdog check cycle."""
    state.total_checks += 1
    state.last_check = datetime.now(UTC).isoformat()
    completion_assist_advisory = load_completion_assist_advisory()
    state.advisory_inputs = (
        {"completionAssist": completion_assist_advisory}
        if completion_assist_advisory is not None
        else {}
    )

    # Reload local bridge presence
    state.ide_presence = load_ide_presence()

    # 0. Check for IDE mission results before anything else
    check_ide_mission_results(state)

    # 0b. Dispatch queued jobs to IDE if it's active
    dispatch_queued_jobs_to_ide(state)

    # 1. Gateway health
    healthy, reason = check_gateway_health()
    if not healthy and state.gateway_healthy:
        send_alert("critical", "Gateway unhealthy", reason, state)
    elif healthy and not state.gateway_healthy:
        send_alert("info", "Gateway recovered", "Gateway is healthy again", state)
    state.gateway_healthy = healthy

    if not healthy:
        state.save()
        return

    # 2. Poll cron jobs
    cron_jobs = poll_cron_jobs()
    state.jobs = []

    for cj in cron_jobs:
        label = cj.get("label") or cj.get("name") or ""
        if not label.startswith("bijmantra:"):
            continue

        job_id = label.removeprefix("bijmantra:")
        cron_state = cj.get("state", {})
        branch = resolve_job_branch(job_id)

        status = "unknown"
        duration = 0.0

        if cron_state.get("runningAtMs"):
            running_since = cron_state["runningAtMs"] / 1000
            duration = (time.time() - running_since) / 60
            status = "running"

            # Check for stuck jobs
            if duration > max_duration_minutes:
                status = "timed-out"
                send_alert(
                    "error",
                    f"Job timed out: {job_id}",
                    f"Running for {duration:.0f} min (limit: {max_duration_minutes} min)",
                    state,
                )

        elif cron_state.get("lastRunStatus") == "ok":
            status = "completed"
        elif cron_state.get("lastRunStatus") == "error":
            status = "failed"
            errors = cron_state.get("consecutiveErrors", 0)
            if errors >= 3:
                send_alert(
                    "error",
                    f"Job failing repeatedly: {job_id}",
                    f"{errors} consecutive errors. Last: {cron_state.get('lastError', 'unknown')}",
                    state,
                )

        job_status = JobStatus(
            job_id=job_id,
            label=label,
            status=status,
            duration_minutes=duration,
            last_error=cron_state.get("lastError", ""),
            consecutive_errors=cron_state.get("consecutiveErrors", 0),
            branch=branch,
        )

        # 3. Path violation check (only for running/completed jobs)
        if status in ("running", "completed"):
            violations = check_path_violations(job_id, branch)
            if violations:
                send_alert(
                    "warning",
                    f"Path violation in {job_id}",
                    "\n".join(violations),
                    state,
                )
                record_evidence(job_id, "path-violation", {"violations": violations})

        # 4. Verification check (only for completed jobs)
        if status == "completed" and job_status.verification_passed is None:
            existing_closeout = load_stable_evidence(job_id, "closeout.json")
            if existing_closeout and existing_closeout.get("data", {}).get("status") == "passed":
                job_status.verification_passed = True
                note_runtime_status(job_id, "completed")
                state.jobs.append(job_status)
                continue

            passed, results = run_verification_commands(job_id)
            job_status.verification_passed = passed
            verification_evidence_path = record_evidence(
                job_id,
                "verification",
                {
                    "passed": passed,
                    "results": results,
                },
            )
            if passed:
                closeout_passed, closeout_receipt = run_closeout_commands(
                    job_id,
                    verification_evidence_ref=display_runtime_artifact_path(
                        ROOT,
                        RUNTIME_HOME,
                        verification_evidence_path,
                    ),
                )
                write_stable_evidence(
                    job_id,
                    "closeout",
                    closeout_receipt,
                    filename="closeout.json",
                )
                if closeout_passed:
                    send_alert(
                        "info",
                        f"Job verified and closed out: {job_id}",
                        "Verification and state refresh checks passed",
                        state,
                    )
                    note_runtime_status(job_id, "completed")
                else:
                    send_alert(
                        "warning",
                        f"Closeout failed: {job_id}",
                        json.dumps(closeout_receipt, indent=2)[:500],
                        state,
                    )
            else:
                send_alert(
                    "warning",
                    f"Verification failed: {job_id}",
                    json.dumps(results, indent=2)[:500],
                    state,
                )

        state.jobs.append(job_status)

    state.save()


# ── Kill Switch ──────────────────────────────────────────────────────

def kill_job(job_id: str) -> bool:
    """Stop a running job immediately."""
    label = f"bijmantra:{job_id}"
    try:
        result = subprocess.run(
            ["openclaw", "cron", "disable", label],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            logger.info("Killed job %s", job_id)
            note_runtime_status(job_id, "cancelled")
            return True
        logger.warning("Failed to kill %s: %s", job_id, result.stderr)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


def kill_all() -> int:
    """Stop all BijMantra cron jobs."""
    killed = 0
    cron_jobs = poll_cron_jobs()
    for cj in cron_jobs:
        label = cj.get("label") or cj.get("name") or ""
        if label.startswith("bijmantra:"):
            job_id = label.removeprefix("bijmantra:")
            if kill_job(job_id):
                killed += 1
    return killed


# ── CLI ──────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=int, default=120, help="Check interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run single check and exit")
    parser.add_argument("--max-duration", type=int, default=120, help="Max job duration in minutes")
    parser.add_argument("--kill", type=str, help="Kill a specific job by ID")
    parser.add_argument("--kill-all", action="store_true", help="Kill all BijMantra jobs")
    parser.add_argument("--status", action="store_true", help="Show current watchdog state")
    return parser.parse_args()


def cmd_status() -> int:
    state = WatchdogState.load()
    print(f"Last check:     {state.last_check or 'never'}")
    print(f"Gateway:        {'✓ healthy' if state.gateway_healthy else '✗ unhealthy'}")
    print(f"Total checks:   {state.total_checks}")
    print(f"Total alerts:   {state.total_alerts}")
    if state.jobs:
        print(f"\nJobs ({len(state.jobs)}):")
        for j in state.jobs:
            sym = {"running": "▶", "completed": "✓", "failed": "✗", "stuck": "⏳"}.get(j.status, "?")
            print(f"  {sym} {j.job_id}: {j.status} ({j.duration_minutes:.0f}m)")
    return 0


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    args = parse_args()

    if args.status:
        return cmd_status()

    if args.kill:
        ok = kill_job(args.kill)
        print(f"{'✓' if ok else '✗'} kill {args.kill}: {'done' if ok else 'failed'}")
        return 0 if ok else 1

    if args.kill_all:
        killed = kill_all()
        print(f"Killed {killed} job(s)")
        return 0

    state = WatchdogState.load()

    # Handle graceful shutdown
    running = True

    def handle_signal(signum: int, _: Any) -> None:
        nonlocal running
        logger.info("Received signal %d, shutting down...", signum)
        running = False

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    print(f"BijMantra Watchdog started (interval={args.interval}s, max_duration={args.max_duration}m)")

    if args.once:
        run_check(state, args.max_duration)
        return 0

    while running:
        try:
            run_check(state, args.max_duration)
            logger.info(
                "Check #%d complete. Next in %ds.",
                state.total_checks,
                args.interval,
            )
        except Exception:
            logger.exception("Check failed")

        # Sleep in short intervals so we can respond to signals
        for _ in range(args.interval):
            if not running:
                break
            time.sleep(1)

    print("Watchdog stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

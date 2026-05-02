"""Telemetry service for developer control plane.

Handles closeout receipts, watchdog status, completion assist, and queue status.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.modules.ai.services.claw_runtime_contract import (
    normalize_runtime_reference,
    runtime_auth_store_path,
)
from app.modules.ai.services.claw_runtime_surface import (
    display_runtime_artifact_path,
    runtime_watchdog_state_freshness,
)
from app.modules.ai.services.developer_control_plane_autonomy_cycle import (
    load_developer_control_plane_autonomy_cycle,
)
from app.modules.ai.services.developer_control_plane_completion_assist import (
    load_developer_control_plane_completion_assist,
)


def load_closeout_receipt(
    queue_job_id: str,
    mission_evidence_dir: Path,
) -> dict[str, Any] | None:
    """Load closeout receipt from filesystem.
    
    Args:
        queue_job_id: Queue job identifier
        mission_evidence_dir: Path to mission evidence directory
        
    Returns:
        Closeout receipt payload or None if not found
    """
    closeout_path = mission_evidence_dir / queue_job_id / "closeout.json"
    if not closeout_path.exists():
        return None

    try:
        payload = json.loads(closeout_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"malformed_artifact": True, "error": str(exc)}

    if not isinstance(payload, dict):
        return {"malformed_artifact": True, "error": "Closeout receipt must be a JSON object"}

    return payload


def load_watchdog_state_payload(watchdog_state_path: Path) -> dict[str, Any] | None:
    """Load watchdog state from filesystem.
    
    Args:
        watchdog_state_path: Path to watchdog state file
        
    Returns:
        Watchdog state payload or None if not found
    """
    if not watchdog_state_path.exists():
        return None

    try:
        payload = json.loads(watchdog_state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"malformed_artifact": True, "error": str(exc)}

    if not isinstance(payload, dict):
        return {"malformed_artifact": True, "error": "Watchdog state payload must be a JSON object"}

    return payload


def load_autonomy_cycle_payload(autonomy_cycle_path: Path) -> dict[str, Any] | None:
    """Load autonomy cycle artifact from filesystem.
    
    Args:
        autonomy_cycle_path: Path to autonomy cycle artifact
        
    Returns:
        Autonomy cycle payload or None if error
    """
    try:
        return load_developer_control_plane_autonomy_cycle(autonomy_cycle_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {"malformed_artifact": True, "error": str(exc)}


def load_completion_assist_payload(completion_assist_path: Path) -> dict[str, Any] | None:
    """Load completion assist artifact from filesystem.
    
    Args:
        completion_assist_path: Path to completion assist artifact
        
    Returns:
        Completion assist payload or None if error
    """
    try:
        return load_developer_control_plane_completion_assist(completion_assist_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {"malformed_artifact": True, "error": str(exc)}


def build_overnight_queue_status_response(
    queue_payload: dict[str, Any],
    exists: bool,
    queue_sha256: str,
    overnight_queue_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Build overnight queue status response.
    
    Args:
        queue_payload: Queue payload
        exists: Whether queue file exists
        queue_sha256: SHA256 hash of queue
        overnight_queue_path: Path to queue file
        repo_root: Repository root path
        
    Returns:
        Queue status response dict
    """
    jobs = queue_payload.get("jobs", [])
    try:
        queue_path = str(overnight_queue_path.relative_to(repo_root))
    except ValueError:
        queue_path = str(overnight_queue_path)

    return {
        "queue_path": queue_path,
        "queue_sha256": queue_sha256,
        "exists": exists,
        "job_count": len(jobs),
        "updated_at": queue_payload.get("updatedAt"),
    }


def build_closeout_receipt_response(
    queue_job_id: str,
    receipt: dict[str, Any] | None,
    mission_evidence_dir: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Build closeout receipt response.
    
    Args:
        queue_job_id: Queue job identifier
        receipt: Closeout receipt payload
        mission_evidence_dir: Path to mission evidence directory
        repo_root: Repository root path
        
    Returns:
        Closeout receipt response dict
    """
    if receipt is None:
        return {"exists": False, "queue_job_id": queue_job_id}

    data = receipt.get("data") if isinstance(receipt.get("data"), dict) else {}
    normalized_commands: list[dict[str, Any]] = []
    closeout_commands = data.get("closeoutCommands")
    if isinstance(closeout_commands, list):
        for item in closeout_commands:
            if isinstance(item, dict) and isinstance(item.get("command"), str):
                normalized_commands.append({
                    "command": item["command"],
                    "passed": item.get("passed") is True,
                    "exit_code": item.get("exitCode")
                    if isinstance(item.get("exitCode"), int) or item.get("exitCode") is None
                    else None,
                    "started_at": item.get("startedAt") if isinstance(item.get("startedAt"), str) else None,
                    "finished_at": item.get("finishedAt") if isinstance(item.get("finishedAt"), str) else None,
                    "stdout_tail": item.get("stdoutTail") if isinstance(item.get("stdoutTail"), str) else None,
                    "stderr_tail": item.get("stderrTail") if isinstance(item.get("stderrTail"), str) else None,
                })

    normalized_artifacts: list[dict[str, Any]] = []
    artifacts = data.get("artifacts")
    if isinstance(artifacts, list):
        for item in artifacts:
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                normalized_artifacts.append({
                    "path": item["path"],
                    "exists": item.get("exists") is True,
                    "sha256": item.get("sha256") if isinstance(item.get("sha256"), str) else None,
                    "modified_at": item.get("modifiedAt") if isinstance(item.get("modifiedAt"), str) else None,
                })

    runtime_root = mission_evidence_dir.parent

    return {
        "exists": True,
        "queue_job_id": queue_job_id,
        "mission_id": data.get("missionId") if isinstance(data.get("missionId"), str) else None,
        "producer_key": data.get("producerKey") if isinstance(data.get("producerKey"), str) else None,
        "source_lane_id": data.get("sourceLaneId") if isinstance(data.get("sourceLaneId"), str) else None,
        "source_board_concurrency_token": data.get("sourceBoardConcurrencyToken")
        if isinstance(data.get("sourceBoardConcurrencyToken"), str)
        else None,
        "runtime_profile_id": data.get("runtimeProfileId")
        if isinstance(data.get("runtimeProfileId"), str)
        else None,
        "runtime_policy_sha256": data.get("runtimePolicySha256")
        if isinstance(data.get("runtimePolicySha256"), str)
        else None,
        "closeout_status": data.get("status") if isinstance(data.get("status"), str) else None,
        "state_refresh_required": data.get("stateRefreshRequired")
        if isinstance(data.get("stateRefreshRequired"), bool)
        else None,
        "receipt_recorded_at": receipt.get("timestamp") if isinstance(receipt.get("timestamp"), str) else None,
        "started_at": data.get("startedAt") if isinstance(data.get("startedAt"), str) else None,
        "finished_at": data.get("finishedAt") if isinstance(data.get("finishedAt"), str) else None,
        "verification_evidence_ref": normalize_runtime_reference(
            repo_root,
            runtime_root,
            data.get("verificationEvidenceRef") if isinstance(data.get("verificationEvidenceRef"), str) else None,
        ),
        "queue_sha256_at_closeout": data.get("queueSha256AtWrite")
        if isinstance(data.get("queueSha256AtWrite"), str)
        else None,
        "closeout_commands": normalized_commands,
        "artifacts": normalized_artifacts,
    }


def build_watchdog_status_response(
    watchdog_state: dict[str, Any] | None,
    watchdog_state_path: Path,
    mission_evidence_dir: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Build watchdog status response.
    
    Args:
        watchdog_state: Watchdog state payload
        watchdog_state_path: Path to watchdog state file
        mission_evidence_dir: Path to mission evidence directory
        repo_root: Repository root path
        
    Returns:
        Watchdog status response dict
    """
    auth_store_path = runtime_auth_store_path(watchdog_state_path.parent)
    auth_store_exists = auth_store_path.exists()
    bootstrap_status = "ready" if auth_store_exists else "auth-store-missing"
    auth_store_display_path = normalize_runtime_reference(
        repo_root,
        watchdog_state_path.parent,
        auth_store_path,
    ) or "runtime-artifacts/agents/main/agent/auth-profiles.json"

    if watchdog_state is None:
        return {
            "exists": False,
            "state_path": display_runtime_artifact_path(repo_root, watchdog_state_path),
            "auth_store_exists": auth_store_exists,
            "auth_store_path": auth_store_display_path,
            "bootstrap_ready": auth_store_exists,
            "bootstrap_status": bootstrap_status,
            "mission_evidence_dir_exists": mission_evidence_dir.exists(),
            "mission_evidence_dir_path": display_runtime_artifact_path(repo_root, mission_evidence_dir),
            "completion_assist_advisory": None,
        }

    state_age_seconds, state_is_stale = runtime_watchdog_state_freshness(
        watchdog_state.get("lastCheck") if isinstance(watchdog_state.get("lastCheck"), str) else None
    )

    normalized_jobs: list[dict[str, Any]] = []
    jobs = watchdog_state.get("jobs")
    if isinstance(jobs, list):
        for item in jobs:
            if isinstance(item, dict) and isinstance(item.get("jobId"), str):
                duration_minutes = item.get("durationMinutes")
                normalized_jobs.append({
                    "job_id": item["jobId"],
                    "label": item.get("label") if isinstance(item.get("label"), str) else None,
                    "status": item.get("status") if isinstance(item.get("status"), str) else None,
                    "started_at": item.get("startedAt") if isinstance(item.get("startedAt"), str) else None,
                    "duration_minutes": float(duration_minutes)
                    if isinstance(duration_minutes, (int, float))
                    else None,
                    "last_error": item.get("lastError") if isinstance(item.get("lastError"), str) else None,
                    "consecutive_errors": item.get("consecutiveErrors")
                    if isinstance(item.get("consecutiveErrors"), int)
                    else None,
                    "branch": item.get("branch") if isinstance(item.get("branch"), str) else None,
                    "verification_passed": item.get("verificationPassed")
                    if isinstance(item.get("verificationPassed"), bool)
                    else None,
                })

    total_checks = watchdog_state.get("totalChecks")
    total_alerts = watchdog_state.get("totalAlerts")
    advisory_inputs = watchdog_state.get("advisoryInputs")
    completion_assist = (
        advisory_inputs.get("completionAssist")
        if isinstance(advisory_inputs, dict)
        else None
    )
    completion_assist_advisory = None
    if isinstance(completion_assist, dict):
        matched_selected_job_ids = completion_assist.get("matchedSelectedJobIds")
        completion_assist_advisory = {
            "authority": completion_assist.get("authority")
            if isinstance(completion_assist.get("authority"), str)
            else "advisory-only-derived",
            "observed_from_path": completion_assist.get("observedFromPath")
            if isinstance(completion_assist.get("observedFromPath"), str)
            else None,
            "available": completion_assist.get("available") is True,
            "artifact_path": completion_assist.get("artifactPath")
            if isinstance(completion_assist.get("artifactPath"), str)
            else None,
            "status": completion_assist.get("status")
            if isinstance(completion_assist.get("status"), str)
            else None,
            "staged": completion_assist.get("staged") is True,
            "explicit_write_required": completion_assist.get("explicitWriteRequired") is not False,
            "message": completion_assist.get("message")
            if isinstance(completion_assist.get("message"), str)
            else None,
            "source_lane_id": completion_assist.get("sourceLaneId")
            if isinstance(completion_assist.get("sourceLaneId"), str)
            else None,
            "queue_job_id": completion_assist.get("queueJobId")
            if isinstance(completion_assist.get("queueJobId"), str)
            else None,
            "draft_source": completion_assist.get("draftSource")
            if isinstance(completion_assist.get("draftSource"), str)
            else None,
            "receipt_path": completion_assist.get("receiptPath")
            if isinstance(completion_assist.get("receiptPath"), str)
            else None,
            "source_endpoint": completion_assist.get("sourceEndpoint")
            if isinstance(completion_assist.get("sourceEndpoint"), str)
            else None,
            "autonomy_cycle_artifact_path": completion_assist.get("autonomyCycleArtifactPath")
            if isinstance(completion_assist.get("autonomyCycleArtifactPath"), str)
            else None,
            "next_action_ordering_source": completion_assist.get("nextActionOrderingSource")
            if isinstance(completion_assist.get("nextActionOrderingSource"), str)
            else None,
            "matched_selected_job_ids": [
                item
                for item in matched_selected_job_ids
                if isinstance(item, str)
            ]
            if isinstance(matched_selected_job_ids, list)
            else [],
        }

    return {
        "exists": True,
        "state_path": display_runtime_artifact_path(repo_root, watchdog_state_path),
        "auth_store_exists": auth_store_exists,
        "auth_store_path": auth_store_display_path,
        "bootstrap_ready": auth_store_exists,
        "bootstrap_status": bootstrap_status,
        "mission_evidence_dir_exists": mission_evidence_dir.exists(),
        "mission_evidence_dir_path": display_runtime_artifact_path(repo_root, mission_evidence_dir),
        "last_check": watchdog_state.get("lastCheck")
        if isinstance(watchdog_state.get("lastCheck"), str)
        else None,
        "state_age_seconds": state_age_seconds,
        "state_is_stale": state_is_stale,
        "gateway_healthy": watchdog_state.get("gatewayHealthy")
        if isinstance(watchdog_state.get("gatewayHealthy"), bool)
        else None,
        "total_checks": total_checks if isinstance(total_checks, int) else 0,
        "total_alerts": total_alerts if isinstance(total_alerts, int) else 0,
        "job_count": len(normalized_jobs),
        "jobs": normalized_jobs,
        "completion_assist_advisory": completion_assist_advisory,
    }


def build_completion_assist_response(
    payload: dict[str, Any] | None,
    completion_assist_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Build completion assist response.
    
    Args:
        payload: Completion assist payload
        completion_assist_path: Path to completion assist artifact
        repo_root: Repository root path
        
    Returns:
        Completion assist response dict
    """
    artifact_path = (
        str(completion_assist_path.relative_to(repo_root))
        if completion_assist_path.is_relative_to(repo_root)
        else str(completion_assist_path)
    )

    if payload is None:
        return {
            "exists": False,
            "artifact_path": artifact_path,
        }

    return {
        "exists": True,
        "artifact_path": artifact_path,
        "generated_at": payload.get("generatedAt") if isinstance(payload.get("generatedAt"), str) else None,
        "status": payload.get("status") if isinstance(payload.get("status"), str) else None,
        "staged": payload.get("staged") is True,
        "explicit_write_required": payload.get("explicitWriteRequired") is not False,
        "message": payload.get("message") if isinstance(payload.get("message"), str) else None,
        "source": payload.get("source") if isinstance(payload.get("source"), dict) else None,
        "actionable_completion_write": (
            payload.get("actionableCompletionWrite")
            if isinstance(payload.get("actionableCompletionWrite"), dict)
            else None
        ),
    }

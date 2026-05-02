#!/usr/bin/env python3
"""Evaluate one bounded developer control-plane autonomy cycle."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "app" / "modules" / "ai" / "services"))

from claw_runtime_contract import (
    display_runtime_artifact_path,
    resolve_claw_runtime_home,
    runtime_mission_evidence_dir,
    runtime_watchdog_state_path,
)

try:
    from scripts.local_env import load_local_env
    from scripts.run_overnight_queue import QUEUE_PATH, build_plan, load_queue, validate_queue
    from scripts.stage_control_plane_completion_assist import (
        AUTH_TOKEN_ENV,
        BASE_URL_ENV,
        DEFAULT_BASE_URL as COMPLETION_ASSIST_DEFAULT_BASE_URL,
        OUTPUT_PATH as COMPLETION_ASSIST_OUTPUT_PATH,
        CompletionAssistError,
        build_completion_assist_artifact,
        fetch_runtime_autonomy_cycle,
        write_completion_assist_artifact,
    )
except ImportError:
    from local_env import load_local_env
    from run_overnight_queue import QUEUE_PATH, build_plan, load_queue, validate_queue
    from stage_control_plane_completion_assist import (
        AUTH_TOKEN_ENV,
        BASE_URL_ENV,
        DEFAULT_BASE_URL as COMPLETION_ASSIST_DEFAULT_BASE_URL,
        OUTPUT_PATH as COMPLETION_ASSIST_OUTPUT_PATH,
        CompletionAssistError,
        build_completion_assist_artifact,
        fetch_runtime_autonomy_cycle,
        write_completion_assist_artifact,
    )


OUTPUT_PATH = (
    ROOT / ".github" / "docs" / "architecture" / "tracking" / "developer-control-plane-autonomy-cycle.json"
)


def resolve_runtime_home() -> Path:
    return resolve_claw_runtime_home(ROOT)


def resolve_runtime_paths() -> tuple[Path, Path]:
    runtime_home = resolve_runtime_home()
    return (
        runtime_watchdog_state_path(runtime_home),
        runtime_mission_evidence_dir(runtime_home),
    )


def display_path(path: Path) -> str:
    return display_runtime_artifact_path(ROOT, resolve_runtime_home(), path)


def load_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON payload at {path} must be an object")
    return payload


def load_watchdog_context(path: Path) -> dict[str, Any]:
    payload = load_json_object(path)
    if payload is None:
        return {
            "exists": False,
            "statePath": display_path(path),
            "lastCheck": None,
            "gatewayHealthy": None,
            "stateIsStale": True,
            "totalAlerts": 0,
            "jobErrors": {},
        }

    jobs = payload.get("jobs") if isinstance(payload.get("jobs"), list) else []
    job_errors: dict[str, dict[str, Any]] = {}
    for item in jobs:
        if not isinstance(item, dict):
            continue
        job_id = item.get("jobId") or item.get("job_id")
        if not isinstance(job_id, str) or not job_id:
            continue

        last_error = item.get("lastError") or item.get("last_error")
        consecutive_errors = item.get("consecutiveErrors") or item.get("consecutive_errors")
        if isinstance(last_error, str) and last_error:
            job_errors[job_id] = {
                "lastError": last_error,
                "consecutiveErrors": consecutive_errors if isinstance(consecutive_errors, int) else None,
            }

    last_check = payload.get("lastCheck") or payload.get("last_check")
    gateway_healthy = payload.get("gatewayHealthy")
    if not isinstance(gateway_healthy, bool):
        gateway_healthy = payload.get("gateway_healthy") if isinstance(payload.get("gateway_healthy"), bool) else None

    total_alerts = payload.get("totalAlerts")
    if not isinstance(total_alerts, int):
        total_alerts = payload.get("total_alerts") if isinstance(payload.get("total_alerts"), int) else 0

    state_is_stale = payload.get("stateIsStale")
    if not isinstance(state_is_stale, bool):
        state_is_stale = payload.get("state_is_stale") is True

    return {
        "exists": True,
        "statePath": display_path(path),
        "lastCheck": last_check if isinstance(last_check, str) else None,
        "gatewayHealthy": gateway_healthy,
        "stateIsStale": state_is_stale,
        "totalAlerts": total_alerts,
        "jobErrors": job_errors,
    }


def load_closeout_receipts(queue: dict, mission_evidence_dir: Path) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for job in queue.get("jobs", []):
        if not isinstance(job, dict):
            continue
        job_id = job.get("jobId")
        if not isinstance(job_id, str) or not job_id:
            continue

        receipt_path = mission_evidence_dir / job_id / "closeout.json"
        payload = load_json_object(receipt_path)
        if payload is None:
            receipts[job_id] = {
                "exists": False,
                "path": display_path(receipt_path),
            }
            continue

        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        closeout_status = data.get("status") or data.get("closeoutStatus") or data.get("closeout_status")
        verification_evidence_ref = (
            data.get("verificationEvidenceRef") or data.get("verification_evidence_ref")
        )
        mission_id = data.get("missionId") or data.get("mission_id")

        receipts[job_id] = {
            "exists": True,
            "path": display_path(receipt_path),
            "closeoutStatus": closeout_status if isinstance(closeout_status, str) else None,
            "verificationEvidenceRef": (
                verification_evidence_ref if isinstance(verification_evidence_ref, str) else None
            ),
            "missionId": mission_id if isinstance(mission_id, str) else None,
        }

    return receipts


def load_runtime_context(
    queue: dict,
    *,
    watchdog_state_path: Path,
    mission_evidence_dir: Path,
) -> dict[str, Any]:
    return {
        "watchdog": load_watchdog_context(watchdog_state_path),
        "closeoutReceipts": load_closeout_receipts(queue, mission_evidence_dir),
    }


def get_source_lane_id(job: dict[str, Any] | None) -> str | None:
    if not isinstance(job, dict):
        return None

    provenance = job.get("provenance")
    if not isinstance(provenance, dict):
        return None

    source_lane_id = provenance.get("sourceLaneId") or provenance.get("source_lane_id")
    if isinstance(source_lane_id, str) and source_lane_id:
        return source_lane_id

    return None


def is_closeout_candidate_ready_for_completion_write_back(candidate: dict[str, Any]) -> bool:
    source_lane_id = candidate.get("sourceLaneId")
    if not isinstance(source_lane_id, str) or not source_lane_id:
        return False

    if candidate.get("queueStatus") != "completed":
        return False

    return candidate.get("closeoutStatus") in {"passed", "completed", "succeeded"}


def build_autonomy_cycle(
    queue: dict,
    *,
    window: str,
    max_jobs: int,
    runtime_context: dict[str, Any],
) -> dict[str, Any]:
    plan = build_plan(queue, window, max_jobs, runtime_context=runtime_context)
    closeout_receipts = runtime_context["closeoutReceipts"]
    watchdog = runtime_context["watchdog"]
    job_by_id = {
        job.get("jobId"): job
        for job in queue.get("jobs", [])
        if isinstance(job, dict) and isinstance(job.get("jobId"), str)
    }

    selected_jobs: list[dict[str, Any]] = []
    for selected_job in plan["selectedJobs"]:
        if not isinstance(selected_job, dict):
            continue
        projected_selected_job = dict(selected_job)
        projected_selected_job["sourceLaneId"] = get_source_lane_id(selected_job)
        selected_jobs.append(projected_selected_job)

    blocked_jobs: list[dict[str, Any]] = []
    for blocked_job in plan["blockedJobs"]:
        if not isinstance(blocked_job, dict):
            continue
        projected_blocked_job = dict(blocked_job)
        projected_blocked_job["sourceLaneId"] = get_source_lane_id(
            job_by_id.get(projected_blocked_job.get("jobId"))
        )
        blocked_jobs.append(projected_blocked_job)

    closeout_candidates: list[dict[str, Any]] = []
    for job in queue.get("jobs", []):
        if not isinstance(job, dict):
            continue
        job_id = job.get("jobId")
        if not isinstance(job_id, str):
            continue

        receipt = closeout_receipts.get(job_id)
        if not isinstance(receipt, dict) or receipt.get("exists") is not True:
            continue

        closeout_candidates.append(
            {
                "jobId": job_id,
                "title": job.get("title"),
                "sourceLaneId": get_source_lane_id(job),
                "queueStatus": job.get("status"),
                "closeoutStatus": receipt.get("closeoutStatus"),
                "missionId": receipt.get("missionId"),
                "verificationEvidenceRef": receipt.get("verificationEvidenceRef"),
                "path": receipt["path"],
            }
        )

    next_actions: list[dict[str, Any]] = []
    for selected_job in selected_jobs:
        next_actions.append(
            {
                "action": "dispatch-queue-job",
                "jobId": selected_job["jobId"],
                "title": selected_job["title"],
                "sourceLaneId": selected_job.get("sourceLaneId"),
                "reason": selected_job.get("triggerReason"),
                "primaryAgent": selected_job["primaryAgent"],
                "priority": selected_job["priority"],
            }
        )

    for candidate in closeout_candidates:
        next_actions.append(
            {
                "action": "review-closeout-receipt",
                "jobId": candidate["jobId"],
                "title": candidate["title"],
                "sourceLaneId": candidate.get("sourceLaneId"),
                "reason": f"stable closeout receipt observed ({candidate['closeoutStatus'] or 'observed'})",
                "missionId": candidate["missionId"],
                "receiptPath": candidate["path"],
            }
        )

        if is_closeout_candidate_ready_for_completion_write_back(candidate):
            next_actions.append(
                {
                    "action": "prepare-completion-write-back",
                    "jobId": candidate["jobId"],
                    "title": candidate["title"],
                    "sourceLaneId": candidate.get("sourceLaneId"),
                    "reason": "stable closeout ready for explicit board write-back",
                    "missionId": candidate["missionId"],
                    "receiptPath": candidate["path"],
                    "detail": {
                        "queueStatus": candidate.get("queueStatus"),
                        "closeoutStatus": candidate.get("closeoutStatus"),
                        "verificationEvidenceRef": candidate.get("verificationEvidenceRef"),
                    },
                }
            )

    if watchdog["exists"]:
        if watchdog["stateIsStale"] is True:
            next_actions.append(
                {
                    "action": "inspect-watchdog-state",
                    "reason": "watchdog-state-stale",
                    "statePath": watchdog["statePath"],
                }
            )
        if watchdog["gatewayHealthy"] is False:
            next_actions.append(
                {
                    "action": "inspect-watchdog-state",
                    "reason": "gateway-unhealthy",
                    "statePath": watchdog["statePath"],
                }
            )
        if watchdog["totalAlerts"] > 0:
            next_actions.append(
                {
                    "action": "inspect-watchdog-state",
                    "reason": f"alerts-present:{watchdog['totalAlerts']}",
                    "statePath": watchdog["statePath"],
                }
            )
        for job_id, detail in sorted(watchdog["jobErrors"].items()):
            next_actions.append(
                {
                    "action": "investigate-watchdog-job",
                    "jobId": job_id,
                    "sourceLaneId": get_source_lane_id(job_by_id.get(job_id)),
                    "reason": "watchdog-job-error",
                    "detail": detail,
                }
            )

    return {
        "generatedAt": datetime.now(UTC).isoformat(),
        "queuePath": display_path(QUEUE_PATH),
        "window": window,
        "maxJobsPerRun": max_jobs,
        "statusCounts": plan["statusCounts"],
        "selectedJobCount": plan["selectedJobCount"],
        "blockedJobCount": plan["blockedJobCount"],
        "closeoutCandidateCount": len(closeout_candidates),
        "nextActionCount": len(next_actions),
        "watchdog": watchdog,
        "selectedJobs": selected_jobs,
        "blockedJobs": blocked_jobs,
        "closeoutCandidates": closeout_candidates,
        "nextActions": next_actions,
    }


def parse_args() -> argparse.Namespace:
    default_watchdog_state_path, default_mission_evidence_dir = resolve_runtime_paths()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=QUEUE_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--window", default="nightly")
    parser.add_argument("--max-jobs", type=int, default=0)
    parser.add_argument("--watchdog-state", type=Path, default=default_watchdog_state_path)
    parser.add_argument("--mission-evidence-dir", type=Path, default=default_mission_evidence_dir)
    parser.add_argument(
        "--completion-assist-output",
        type=Path,
        default=COMPLETION_ASSIST_OUTPUT_PATH,
        help="Tracked output path for the optional headless completion-assist artifact",
    )
    parser.add_argument(
        "--completion-assist-timeout-seconds",
        type=float,
        default=10.0,
        help="HTTP timeout for the optional runtime completion-assist fetch",
    )
    return parser.parse_args()


def maybe_stage_completion_assist(
    *,
    completion_assist_output_path: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    load_local_env(keys=[AUTH_TOKEN_ENV, BASE_URL_ENV])
    auth_token = os.getenv(AUTH_TOKEN_ENV, "").strip()
    if not auth_token:
        return {
            "status": "skipped",
            "reason": "missing-auth-token",
            "message": (
                f"Skipped completion-assist staging because {AUTH_TOKEN_ENV} is not configured."
            ),
        }

    base_url = os.getenv(BASE_URL_ENV, COMPLETION_ASSIST_DEFAULT_BASE_URL)
    endpoint_url = f"{base_url.rstrip('/')}/api/v2/developer-control-plane/runtime/autonomy-cycle"
    try:
        autonomy_cycle = fetch_runtime_autonomy_cycle(
            base_url=base_url,
            auth_token=auth_token,
            timeout_seconds=timeout_seconds,
        )
        artifact = build_completion_assist_artifact(
            autonomy_cycle,
            endpoint_url=endpoint_url,
            generated_at=datetime.now(UTC).isoformat(),
        )
        write_completion_assist_artifact(completion_assist_output_path, artifact)
    except CompletionAssistError as exc:
        return {
            "status": "error",
            "reason": "assist-fetch-failed",
            "message": f"Completion assist staging failed: {exc}",
        }

    return {
        "status": "staged",
        "reason": None,
        "message": artifact["message"],
        "output_path": str(completion_assist_output_path),
    }


def main() -> int:
    args = parse_args()
    load_local_env(keys=[AUTH_TOKEN_ENV, BASE_URL_ENV])
    queue = validate_queue(load_queue(args.queue))
    max_jobs = args.max_jobs or queue.get("defaults", {}).get("maxJobsPerRun", 2)
    runtime_context = load_runtime_context(
        queue,
        watchdog_state_path=args.watchdog_state,
        mission_evidence_dir=args.mission_evidence_dir,
    )
    cycle = build_autonomy_cycle(
        queue,
        window=args.window,
        max_jobs=max_jobs,
        runtime_context=runtime_context,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(cycle, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")
    assist_result = maybe_stage_completion_assist(
        completion_assist_output_path=args.completion_assist_output,
        timeout_seconds=args.completion_assist_timeout_seconds,
    )
    if assist_result["status"] == "staged":
        print(f"Wrote {assist_result['output_path']}")
        print(assist_result["message"])
    elif assist_result["status"] == "error":
        print(assist_result["message"], file=sys.stderr)
    else:
        print(assist_result["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
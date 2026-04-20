#!/usr/bin/env python3
"""Stage a headless developer control-plane completion assist artifact."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from scripts.local_env import load_local_env
except ImportError:
    from local_env import load_local_env


ROOT = Path(__file__).resolve().parents[1]
AUTONOMY_CYCLE_ENDPOINT = "/api/v2/developer-control-plane/runtime/autonomy-cycle"
AUTH_TOKEN_ENV = "BIJMANTRA_DEVELOPER_CONTROL_PLANE_AUTH_TOKEN"
BASE_URL_ENV = "BIJMANTRA_DEVELOPER_CONTROL_PLANE_BASE_URL"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
OUTPUT_PATH = (
    ROOT
    / ".github"
    / "docs"
    / "architecture"
    / "tracking"
    / "developer-control-plane-completion-assist.json"
)
FINAL_CLOSEOUT_STATUSES = {"passed", "completed", "succeeded"}


class CompletionAssistError(RuntimeError):
    """Raised when the headless completion assist cannot be staged."""


def _action_count(autonomy_cycle: dict[str, Any], action_name: str) -> int:
    next_actions = autonomy_cycle.get("next_actions")
    if not isinstance(next_actions, list):
        return 0

    return sum(
        1
        for action in next_actions
        if isinstance(action, dict) and action.get("action") == action_name
    )


def build_completion_assist_readiness(autonomy_cycle: dict[str, Any]) -> dict[str, Any]:
    closeout_candidates = autonomy_cycle.get("closeout_candidates")
    closeout_candidate_count = autonomy_cycle.get("closeout_candidate_count")
    if not isinstance(closeout_candidate_count, int):
        closeout_candidate_count = (
            len(closeout_candidates) if isinstance(closeout_candidates, list) else 0
        )

    watchdog = autonomy_cycle.get("watchdog")
    watchdog_exists = watchdog.get("exists") is True if isinstance(watchdog, dict) else False
    watchdog_state_path = (
        watchdog.get("state_path")
        if isinstance(watchdog, dict) and isinstance(watchdog.get("state_path"), str)
        else None
    )
    watchdog_state_is_stale = (
        watchdog.get("state_is_stale")
        if isinstance(watchdog, dict) and isinstance(watchdog.get("state_is_stale"), bool)
        else None
    )

    eligible_closeout_candidate_count = 0
    if isinstance(closeout_candidates, list):
        for candidate in closeout_candidates:
            if not isinstance(candidate, dict):
                continue
            source_lane_id = candidate.get("source_lane_id") or candidate.get("sourceLaneId")
            queue_status = candidate.get("queue_status") or candidate.get("queueStatus")
            closeout_status = candidate.get("closeout_status") or candidate.get(
                "closeoutStatus"
            )
            if (
                isinstance(source_lane_id, str)
                and source_lane_id
                and queue_status == "completed"
                and isinstance(closeout_status, str)
                and closeout_status in FINAL_CLOSEOUT_STATUSES
            ):
                eligible_closeout_candidate_count += 1

    return {
        "selectedJobCount": autonomy_cycle.get("selected_job_count")
        if isinstance(autonomy_cycle.get("selected_job_count"), int)
        else 0,
        "nextActionCount": autonomy_cycle.get("next_action_count")
        if isinstance(autonomy_cycle.get("next_action_count"), int)
        else 0,
        "closeoutCandidateCount": closeout_candidate_count,
        "reviewActionCount": _action_count(autonomy_cycle, "review-closeout-receipt"),
        "prepareActionCount": _action_count(
            autonomy_cycle, "prepare-completion-write-back"
        ),
        "eligibleCloseoutCandidateCount": eligible_closeout_candidate_count,
        "watchdogExists": watchdog_exists,
        "watchdogStatePath": watchdog_state_path,
        "watchdogStateIsStale": watchdog_state_is_stale,
    }


def resolve_completion_assist_idle_state(
    readiness: dict[str, Any],
) -> tuple[str, str]:
    prepare_action_count = readiness.get("prepareActionCount")
    closeout_candidate_count = readiness.get("closeoutCandidateCount")
    review_action_count = readiness.get("reviewActionCount")

    if isinstance(prepare_action_count, int) and prepare_action_count > 0:
        return (
            "missing-embedded-preparation",
            "The runtime autonomy-cycle reported completion write-back actions, but no actionable reviewed completion packet was embedded.",
        )

    if (
        isinstance(closeout_candidate_count, int)
        and closeout_candidate_count > 0
        or isinstance(review_action_count, int)
        and review_action_count > 0
    ):
        return (
            "closeout-candidates-not-ready",
            "No actionable reviewed completion write-back packet is present because stable closeout candidates exist but are not yet ready for explicit board write-back.",
        )

    return (
        "no-stable-closeout-candidates",
        "No actionable reviewed completion write-back packet is present because the runtime autonomy-cycle has no stable closeout candidates.",
    )


def _normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip()
    if not normalized:
        raise CompletionAssistError("base URL must not be empty")
    return normalized.rstrip("/")


def _autonomy_cycle_url(base_url: str) -> str:
    return f"{_normalize_base_url(base_url)}{AUTONOMY_CYCLE_ENDPOINT}"


def resolve_auth_token(explicit_token: str | None) -> str:
    token = explicit_token or os.getenv(AUTH_TOKEN_ENV, "")
    token = token.strip()
    if not token:
        raise CompletionAssistError(
            "developer control-plane auth token is required. "
            f"Set {AUTH_TOKEN_ENV} or pass --auth-token."
        )
    if any(character.isspace() for character in token):
        raise CompletionAssistError("developer control-plane auth token must not contain whitespace")
    return token


def fetch_runtime_autonomy_cycle(
    *,
    base_url: str,
    auth_token: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    endpoint_url = _autonomy_cycle_url(base_url)
    request = Request(
        endpoint_url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {auth_token}",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise CompletionAssistError(
            f"runtime autonomy-cycle request failed with HTTP {exc.code}: {detail or exc.reason}"
        ) from exc
    except URLError as exc:
        raise CompletionAssistError(
            f"runtime autonomy-cycle request failed: {exc.reason}"
        ) from exc

    if not isinstance(payload, dict):
        raise CompletionAssistError("runtime autonomy-cycle response must be a JSON object")
    return payload


def build_completion_assist_artifact(
    autonomy_cycle: dict[str, Any],
    *,
    endpoint_url: str,
    generated_at: str,
) -> dict[str, Any]:
    actionable = autonomy_cycle.get("first_actionable_completion_write")
    readiness = build_completion_assist_readiness(autonomy_cycle)
    source = {
        "endpoint": endpoint_url,
        "autonomy_cycle_artifact_path": autonomy_cycle.get("artifact_path"),
        "autonomy_cycle_generated_at": autonomy_cycle.get("generated_at"),
        "next_action_ordering_source": autonomy_cycle.get("next_action_ordering_source"),
    }

    if actionable is None:
        idle_reason, message = resolve_completion_assist_idle_state(readiness)
        return {
            "generatedAt": generated_at,
            "status": "idle",
            "staged": False,
            "explicitWriteRequired": True,
            "message": message,
            "idleReason": idle_reason,
            "readiness": readiness,
            "source": source,
            "actionableCompletionWrite": None,
        }

    if not isinstance(actionable, dict):
        raise CompletionAssistError(
            "runtime autonomy-cycle first_actionable_completion_write must be an object when present"
        )

    preparation = actionable.get("preparation")
    if not isinstance(preparation, dict):
        raise CompletionAssistError(
            "runtime autonomy-cycle first_actionable_completion_write.preparation must be an object"
        )

    prepared_request = preparation.get("prepared_request")
    if not isinstance(prepared_request, dict):
        raise CompletionAssistError(
            "runtime autonomy-cycle first_actionable_completion_write.preparation.prepared_request must be an object"
        )

    queue_status = preparation.get("queue_status")
    closeout_receipt = preparation.get("closeout_receipt")
    if not isinstance(queue_status, dict) or not isinstance(closeout_receipt, dict):
        raise CompletionAssistError(
            "runtime autonomy-cycle first_actionable completion packet is missing queue or closeout context"
        )

    source_lane_id = actionable.get("source_lane_id")
    job_id = actionable.get("job_id")
    if not isinstance(source_lane_id, str) or not source_lane_id:
        raise CompletionAssistError(
            "runtime autonomy-cycle first_actionable_completion_write.source_lane_id must be a non-empty string"
        )
    if not isinstance(job_id, str) or not job_id:
        raise CompletionAssistError(
            "runtime autonomy-cycle first_actionable_completion_write.job_id must be a non-empty string"
        )

    return {
        "generatedAt": generated_at,
        "status": "staged",
        "staged": True,
        "explicitWriteRequired": True,
        "message": (
            f"Staged reviewed completion assist for lane {source_lane_id}. "
            "This artifact does not perform explicit board write-back."
        ),
        "idleReason": None,
        "readiness": readiness,
        "source": source,
        "actionableCompletionWrite": {
            "action": actionable.get("action"),
            "actionIndex": actionable.get("action_index"),
            "jobId": job_id,
            "sourceLaneId": source_lane_id,
            "reason": actionable.get("reason"),
            "missionId": actionable.get("mission_id"),
            "receiptPath": actionable.get("receipt_path"),
            "draftSource": preparation.get("draft_source"),
            "queueStatus": queue_status,
            "closeoutReceipt": closeout_receipt,
            "preparedRequest": prepared_request,
        },
    }


def write_completion_assist_artifact(output_path: Path, artifact: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"{json.dumps(artifact, indent=2)}\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="",
        help=f"Base URL for the local BijMantra backend (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--auth-token",
        default="",
        help=f"Bearer token for the hidden developer-control-plane runtime endpoint (default: ${AUTH_TOKEN_ENV})",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="HTTP timeout for the runtime autonomy-cycle request",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="Path to the tracked headless completion-assist artifact",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_local_env(keys=[AUTH_TOKEN_ENV, BASE_URL_ENV])
    auth_token = resolve_auth_token(args.auth_token)
    base_url = args.base_url.strip() or os.getenv(BASE_URL_ENV, DEFAULT_BASE_URL)
    endpoint_url = _autonomy_cycle_url(base_url)
    autonomy_cycle = fetch_runtime_autonomy_cycle(
        base_url=base_url,
        auth_token=auth_token,
        timeout_seconds=args.timeout_seconds,
    )
    generated_at = datetime.now(UTC).isoformat()
    artifact = build_completion_assist_artifact(
        autonomy_cycle,
        endpoint_url=endpoint_url,
        generated_at=generated_at,
    )
    write_completion_assist_artifact(args.output, artifact)
    print(f"Wrote {args.output}")
    print(artifact["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
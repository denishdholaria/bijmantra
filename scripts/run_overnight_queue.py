#!/usr/bin/env python3
"""Build the overnight dispatch plan for OmShriMaatreNamaha job cards."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / ".agent" / "jobs" / "overnight-queue.json"
OUTPUT_PATH = ROOT / ".github" / "docs" / "architecture" / "tracking" / "overnight-dispatch-plan.json"
COMPLETION_ASSIST_PATH = (
    ROOT
    / ".github"
    / "docs"
    / "architecture"
    / "tracking"
    / "developer-control-plane-completion-assist.json"
)

ALLOWED_STATUSES = {"queued", "blocked", "running", "completed", "cancelled"}
ALLOWED_EXECUTION_MODES = {"same-control-plane", "isolated-sub-lane"}
ALLOWED_TRIGGER_TYPES = {"overnight-window", "closeout-receipt", "watchdog-alert"}
ALLOWED_WATCHDOG_TRIGGER_STATES = {
    "alerts-present",
    "gateway-unhealthy",
    "job-error",
    "state-stale",
}
PRIORITY_ORDER = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}
ENGLISH_LANGUAGE = "en"
ENGLISH_VOCABULARY_POLICY = "english-technical-only"


class QueueValidationError(ValueError):
    """Raised when the overnight queue file is malformed."""


def require_ascii_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise QueueValidationError(f"{field_name} must be a non-empty string")
    if not value.isascii():
        raise QueueValidationError(
            f"{field_name} must use ASCII-only English technical vocabulary"
        )


def validate_text_list(values: object, field_name: str, *, min_items: int = 0) -> None:
    if not isinstance(values, list) or len(values) < min_items:
        minimum = f" with at least {min_items} item(s)" if min_items else ""
        raise QueueValidationError(f"{field_name} must be a list{minimum}")
    for index, item in enumerate(values):
        require_ascii_text(item, f"{field_name}[{index}]")


def validate_lane(job: dict, job_id: str) -> dict:
    lane = job.get("lane")
    if not isinstance(lane, dict):
        raise QueueValidationError(f"lane must be an object for {job_id}")

    required_keys = (
        "objective",
        "inputs",
        "outputs",
        "dependencies",
        "completion_criteria",
    )
    for key in required_keys:
        if key not in lane:
            raise QueueValidationError(f"lane is missing required key {key} for {job_id}")

    require_ascii_text(lane["objective"], f"lane.objective for {job_id}")
    validate_text_list(lane["inputs"], f"lane.inputs for {job_id}")
    validate_text_list(lane["outputs"], f"lane.outputs for {job_id}")
    validate_text_list(lane["dependencies"], f"lane.dependencies for {job_id}")
    validate_text_list(
        lane["completion_criteria"],
        f"lane.completion_criteria for {job_id}",
        min_items=1,
    )
    return lane


def load_queue(queue_path: Path) -> dict:
    if not queue_path.exists():
        raise QueueValidationError(f"Queue file not found: {queue_path}")
    return json.loads(queue_path.read_text(encoding="utf-8"))


def load_completion_assist(completion_assist_path: Path) -> dict | None:
    if not completion_assist_path.exists():
        return None

    payload = json.loads(completion_assist_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QueueValidationError(
            f"Completion assist payload must be a JSON object: {completion_assist_path}"
        )
    return payload


def _normalize_trigger_statuses(statuses: object, field_name: str) -> list[str] | None:
    if statuses is None:
        return None
    if isinstance(statuses, str):
        require_ascii_text(statuses, field_name)
        return [statuses]
    validate_text_list(statuses, field_name, min_items=1)
    return list(statuses)


def validate_autonomous_trigger(job_id: str, trigger: object) -> dict:
    if not isinstance(trigger, dict):
        raise QueueValidationError(f"autonomousTrigger must be an object for {job_id}")

    trigger_type = trigger.get("type")
    if trigger_type not in ALLOWED_TRIGGER_TYPES:
        allowed_types = ", ".join(sorted(ALLOWED_TRIGGER_TYPES))
        raise QueueValidationError(
            f"autonomousTrigger.type must be one of {allowed_types} for {job_id}"
        )

    if not isinstance(trigger.get("enabled"), bool):
        raise QueueValidationError(f"autonomousTrigger.enabled must be a boolean for {job_id}")

    if trigger_type == "overnight-window":
        require_ascii_text(trigger.get("window"), f"autonomousTrigger.window for {job_id}")
        return trigger

    if trigger_type == "closeout-receipt":
        require_ascii_text(
            trigger.get("queueJobId"), f"autonomousTrigger.queueJobId for {job_id}"
        )
        _normalize_trigger_statuses(
            trigger.get("closeoutStatus"),
            f"autonomousTrigger.closeoutStatus for {job_id}",
        )
        return trigger

    state = trigger.get("state")
    if state not in ALLOWED_WATCHDOG_TRIGGER_STATES:
        allowed_states = ", ".join(sorted(ALLOWED_WATCHDOG_TRIGGER_STATES))
        raise QueueValidationError(
            f"autonomousTrigger.state must be one of {allowed_states} for {job_id}"
        )
    if state == "job-error":
        require_ascii_text(trigger.get("jobId"), f"autonomousTrigger.jobId for {job_id}")
    return trigger


def evaluate_trigger(
    job: dict,
    *,
    window: str,
    runtime_context: dict | None = None,
) -> tuple[bool, str]:
    trigger = job["autonomousTrigger"]
    if not trigger.get("enabled", False):
        return False, "trigger-disabled"

    trigger_type = trigger["type"]
    if trigger_type == "overnight-window":
        if trigger.get("window") != window:
            return False, f"window-mismatch:{trigger.get('window')}"
        return True, f"overnight-window:{window}"

    context = runtime_context or {}
    if trigger_type == "closeout-receipt":
        receipt_job_id = trigger["queueJobId"]
        receipts = context.get("closeoutReceipts")
        if not isinstance(receipts, dict):
            return False, f"closeout-receipt-missing:{receipt_job_id}"

        receipt = receipts.get(receipt_job_id)
        if not isinstance(receipt, dict) or receipt.get("exists") is not True:
            return False, f"closeout-receipt-missing:{receipt_job_id}"

        allowed_statuses = _normalize_trigger_statuses(
            trigger.get("closeoutStatus"),
            f"autonomousTrigger.closeoutStatus for {job['jobId']}",
        )
        observed_status = receipt.get("closeoutStatus")
        if allowed_statuses is not None and observed_status not in allowed_statuses:
            return (
                False,
                f"closeout-status-mismatch:{receipt_job_id}:{observed_status or 'unknown'}",
            )
        return True, f"closeout-receipt:{receipt_job_id}:{observed_status or 'observed'}"

    watchdog = context.get("watchdog")
    if not isinstance(watchdog, dict) or watchdog.get("exists") is not True:
        return False, "watchdog-state-missing"

    state = trigger["state"]
    if state == "state-stale":
        if watchdog.get("stateIsStale") is True:
            return True, "watchdog-alert:state-stale"
        return False, "watchdog-state-fresh"

    if state == "gateway-unhealthy":
        if watchdog.get("gatewayHealthy") is False:
            return True, "watchdog-alert:gateway-unhealthy"
        return False, "gateway-healthy"

    if state == "alerts-present":
        total_alerts = watchdog.get("totalAlerts")
        if isinstance(total_alerts, int) and total_alerts > 0:
            return True, f"watchdog-alert:alerts-present:{total_alerts}"
        return False, "watchdog-alerts-absent"

    job_errors = watchdog.get("jobErrors")
    job_id = trigger["jobId"]
    if isinstance(job_errors, dict) and job_id in job_errors:
        return True, f"watchdog-alert:job-error:{job_id}"
    return False, f"watchdog-job-healthy:{job_id}"


def validate_queue(queue: dict) -> dict:
    if not isinstance(queue, dict):
        raise QueueValidationError("Queue payload must be a JSON object")

    if queue.get("language") != ENGLISH_LANGUAGE:
        raise QueueValidationError("Queue payload must declare language=en")
    if queue.get("vocabularyPolicy") != ENGLISH_VOCABULARY_POLICY:
        raise QueueValidationError(
            "Queue payload must declare vocabularyPolicy=english-technical-only"
        )

    jobs = queue.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise QueueValidationError("Queue payload must contain a non-empty jobs array")

    seen_ids: set[str] = set()
    job_map: dict[str, dict] = {}

    for job in jobs:
        for key in (
            "jobId",
            "title",
            "status",
            "priority",
            "primaryAgent",
            "supportAgents",
            "executionMode",
            "autonomousTrigger",
            "dependsOn",
            "goal",
            "successCriteria",
            "verification",
        ):
            if key not in job:
                raise QueueValidationError(f"Job is missing required key: {key}")

        job_id = job["jobId"]
        if job_id in seen_ids:
            raise QueueValidationError(f"Duplicate jobId: {job_id}")
        seen_ids.add(job_id)

        if job["status"] not in ALLOWED_STATUSES:
            raise QueueValidationError(f"Invalid status for {job_id}: {job['status']}")
        if job["executionMode"] not in ALLOWED_EXECUTION_MODES:
            raise QueueValidationError(
                f"Invalid executionMode for {job_id}: {job['executionMode']}"
            )
        if job["priority"] not in PRIORITY_ORDER:
            raise QueueValidationError(f"Invalid priority for {job_id}: {job['priority']}")
        if not isinstance(job["supportAgents"], list):
            raise QueueValidationError(f"supportAgents must be a list for {job_id}")
        if not isinstance(job["dependsOn"], list):
            raise QueueValidationError(f"dependsOn must be a list for {job_id}")
        if not isinstance(job["successCriteria"], list) or not job["successCriteria"]:
            raise QueueValidationError(f"successCriteria must be a non-empty list for {job_id}")

        require_ascii_text(job["title"], f"title for {job_id}")
        require_ascii_text(job["goal"], f"goal for {job_id}")
        validate_text_list(job["successCriteria"], f"successCriteria for {job_id}", min_items=1)
        validate_lane(job, job_id)

        trigger = validate_autonomous_trigger(job_id, job["autonomousTrigger"])
        verification = job["verification"]
        if not isinstance(verification, dict) or not isinstance(
            verification.get("commands"), list
        ):
            raise QueueValidationError(
                f"verification.commands must be a list for {job_id}"
            )

        job_map[job_id] = job

    for job in jobs:
        for dependency in job["dependsOn"]:
            if dependency not in job_map:
                raise QueueValidationError(
                    f"Unknown dependency {dependency} referenced by {job['jobId']}"
                )

    return queue


def is_ready(
    job: dict,
    job_map: dict[str, dict],
    window: str,
    runtime_context: dict | None = None,
) -> tuple[bool, str | None]:
    if job["status"] != "queued":
        return False, f"status={job['status']}"

    trigger_ready, trigger_reason = evaluate_trigger(
        job,
        window=window,
        runtime_context=runtime_context,
    )
    if not trigger_ready:
        return False, trigger_reason

    incomplete_dependencies = [
        dependency
        for dependency in job["dependsOn"]
        if job_map[dependency]["status"] != "completed"
    ]
    if incomplete_dependencies:
        return False, f"waiting-on:{','.join(incomplete_dependencies)}"

    return True, trigger_reason


def has_complete_reviewed_provenance(job: dict) -> bool:
    provenance = job.get("provenance")
    if not isinstance(provenance, dict):
        return False

    precedence = provenance.get("precedence")
    return (
        isinstance(provenance.get("sourceBoardConcurrencyToken"), str)
        and bool(provenance["sourceBoardConcurrencyToken"])
        and isinstance(provenance.get("sourceLaneId"), str)
        and bool(provenance["sourceLaneId"])
        and isinstance(precedence, dict)
        and precedence.get("canonicalPlanningSource") == "active-board"
        and precedence.get("derivedExecutionSurface") == "overnight-queue"
    )


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _matches_completion_assist(job: dict, source_lane_id: str | None, queue_job_id: str | None) -> bool:
    if queue_job_id and job.get("jobId") == queue_job_id:
        return True

    trigger = job.get("autonomousTrigger")
    if isinstance(trigger, dict) and queue_job_id and trigger.get("queueJobId") == queue_job_id:
        return True

    provenance = job.get("provenance")
    if isinstance(provenance, dict) and source_lane_id and provenance.get("sourceLaneId") == source_lane_id:
        return True

    return False


def build_completion_assist_advisory(
    runtime_context: dict | None,
    selected_jobs: list[tuple[dict, str | None]],
) -> dict:
    context = runtime_context or {}
    payload = context.get("completionAssist")
    artifact_path = context.get("completionAssistPath")
    advisory: dict[str, object] = {
        "available": isinstance(payload, dict),
        "artifactPath": artifact_path if isinstance(artifact_path, str) else _display_path(COMPLETION_ASSIST_PATH),
        "status": None,
        "staged": False,
        "explicitWriteRequired": True,
        "message": None,
        "sourceLaneId": None,
        "queueJobId": None,
        "draftSource": None,
        "receiptPath": None,
        "sourceEndpoint": None,
        "autonomyCycleArtifactPath": None,
        "nextActionOrderingSource": None,
        "matchedSelectedJobIds": [],
    }

    if not isinstance(payload, dict):
        return advisory

    actionable = payload.get("actionableCompletionWrite")
    source = payload.get("source")
    source_lane_id = actionable.get("sourceLaneId") if isinstance(actionable, dict) else None
    queue_job_id = actionable.get("jobId") if isinstance(actionable, dict) else None
    matched_job_ids = [
        job["jobId"]
        for job, _ in selected_jobs
        if _matches_completion_assist(job, source_lane_id, queue_job_id)
    ]

    advisory.update(
        {
            "status": payload.get("status") if isinstance(payload.get("status"), str) else None,
            "staged": payload.get("staged") is True,
            "explicitWriteRequired": payload.get("explicitWriteRequired") is not False,
            "message": payload.get("message") if isinstance(payload.get("message"), str) else None,
            "sourceLaneId": source_lane_id if isinstance(source_lane_id, str) else None,
            "queueJobId": queue_job_id if isinstance(queue_job_id, str) else None,
            "draftSource": (
                actionable.get("draftSource")
                if isinstance(actionable, dict) and isinstance(actionable.get("draftSource"), str)
                else None
            ),
            "receiptPath": (
                actionable.get("receiptPath")
                if isinstance(actionable, dict) and isinstance(actionable.get("receiptPath"), str)
                else None
            ),
            "sourceEndpoint": (
                source.get("endpoint")
                if isinstance(source, dict) and isinstance(source.get("endpoint"), str)
                else None
            ),
            "autonomyCycleArtifactPath": (
                source.get("autonomy_cycle_artifact_path")
                if isinstance(source, dict)
                and isinstance(source.get("autonomy_cycle_artifact_path"), str)
                else None
            ),
            "nextActionOrderingSource": (
                source.get("next_action_ordering_source")
                if isinstance(source, dict)
                and isinstance(source.get("next_action_ordering_source"), str)
                else None
            ),
            "matchedSelectedJobIds": matched_job_ids,
        }
    )
    return advisory


def build_plan(
    queue: dict,
    window: str,
    max_jobs: int,
    runtime_context: dict | None = None,
) -> dict:
    jobs = queue["jobs"]
    defaults = queue.get("defaults", {})
    job_map = {job["jobId"]: job for job in jobs}
    status_counts = Counter(job["status"] for job in jobs)

    ready_jobs: list[tuple[dict, str | None]] = []
    blocked_jobs: list[dict] = []

    for job in jobs:
        ready, reason = is_ready(job, job_map, window, runtime_context=runtime_context)
        if ready:
            ready_jobs.append((job, reason))
        else:
            blocked_jobs.append(
                {
                    "jobId": job["jobId"],
                    "title": job["title"],
                    "reason": reason,
                }
            )

    ready_jobs.sort(
        key=lambda item: (
            PRIORITY_ORDER[item[0]["priority"]],
            0 if has_complete_reviewed_provenance(item[0]) else 1,
            item[0]["jobId"],
        )
    )
    selected_jobs = ready_jobs[:max_jobs]

    def project(job: dict, trigger_reason: str | None) -> dict:
        projected_job = {
            "jobId": job["jobId"],
            "title": job["title"],
            "language": queue["language"],
            "vocabularyPolicy": queue["vocabularyPolicy"],
            "priority": job["priority"],
            "primaryAgent": job["primaryAgent"],
            "supportAgents": job["supportAgents"],
            "executionMode": job["executionMode"],
            "sourceTask": job.get("sourceTask"),
            "goal": job["goal"],
            "lane": job["lane"],
            "successCriteria": job["successCriteria"],
            "dependsOn": job["dependsOn"],
            "verificationCommands": job["verification"]["commands"],
            "stateRefreshRequired": job["verification"].get(
                "stateRefreshRequired", defaults.get("stateRefreshRequired", True)
            ),
            "closeoutCommands": defaults.get("closeoutCommands", ["make update-state"]),
            "triggerReason": trigger_reason,
        }

        if isinstance(job.get("provenance"), dict):
            projected_job["provenance"] = job["provenance"]

        if isinstance(job.get("autonomousTrigger"), dict):
            projected_job["autonomousTrigger"] = job["autonomousTrigger"]

        return projected_job

    return {
        "generatedAt": datetime.now(UTC).isoformat(),
        "queuePath": str(QUEUE_PATH.relative_to(ROOT)),
        "language": queue["language"],
        "vocabularyPolicy": queue["vocabularyPolicy"],
        "window": window,
        "maxJobsPerRun": max_jobs,
        "statusCounts": dict(sorted(status_counts.items())),
        "selectedJobCount": len(selected_jobs),
        "blockedJobCount": len(blocked_jobs),
        "selectedJobs": [project(job, trigger_reason) for job, trigger_reason in selected_jobs],
        "blockedJobs": blocked_jobs,
        "advisoryInputs": {
            "completionAssist": build_completion_assist_advisory(runtime_context, selected_jobs),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=QUEUE_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--completion-assist", type=Path, default=COMPLETION_ASSIST_PATH)
    parser.add_argument("--window", default="nightly")
    parser.add_argument("--max-jobs", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    queue = validate_queue(load_queue(args.queue))
    max_jobs = args.max_jobs or queue.get("defaults", {}).get("maxJobsPerRun", 2)
    completion_assist = load_completion_assist(args.completion_assist)
    plan = build_plan(
        queue,
        args.window,
        max_jobs,
        runtime_context={
            "completionAssist": completion_assist,
            "completionAssistPath": _display_path(args.completion_assist),
        },
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
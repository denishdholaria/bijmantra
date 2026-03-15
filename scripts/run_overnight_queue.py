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
OUTPUT_PATH = ROOT / "docs-private" / "architecture" / "tracking" / "overnight-dispatch-plan.json"

ALLOWED_STATUSES = {"queued", "blocked", "running", "completed", "cancelled"}
ALLOWED_EXECUTION_MODES = {"same-control-plane", "isolated-sub-lane"}
PRIORITY_ORDER = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}


class QueueValidationError(ValueError):
    """Raised when the overnight queue file is malformed."""


def load_queue(queue_path: Path) -> dict:
    if not queue_path.exists():
        raise QueueValidationError(f"Queue file not found: {queue_path}")
    return json.loads(queue_path.read_text(encoding="utf-8"))


def validate_queue(queue: dict) -> dict:
    if not isinstance(queue, dict):
        raise QueueValidationError("Queue payload must be a JSON object")

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

        trigger = job["autonomousTrigger"]
        verification = job["verification"]
        if not isinstance(trigger, dict) or trigger.get("type") != "overnight-window":
            raise QueueValidationError(
                f"autonomousTrigger.type must be overnight-window for {job_id}"
            )
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


def is_ready(job: dict, job_map: dict[str, dict], window: str) -> tuple[bool, str | None]:
    if job["status"] != "queued":
        return False, f"status={job['status']}"

    trigger = job["autonomousTrigger"]
    if not trigger.get("enabled", False):
        return False, "trigger-disabled"
    if trigger.get("window") != window:
        return False, f"window-mismatch:{trigger.get('window')}"

    incomplete_dependencies = [
        dependency
        for dependency in job["dependsOn"]
        if job_map[dependency]["status"] != "completed"
    ]
    if incomplete_dependencies:
        return False, f"waiting-on:{','.join(incomplete_dependencies)}"

    return True, None


def build_plan(queue: dict, window: str, max_jobs: int) -> dict:
    jobs = queue["jobs"]
    defaults = queue.get("defaults", {})
    job_map = {job["jobId"]: job for job in jobs}
    status_counts = Counter(job["status"] for job in jobs)

    ready_jobs: list[dict] = []
    blocked_jobs: list[dict] = []

    for job in jobs:
        ready, reason = is_ready(job, job_map, window)
        if ready:
            ready_jobs.append(job)
        else:
            blocked_jobs.append(
                {
                    "jobId": job["jobId"],
                    "title": job["title"],
                    "reason": reason,
                }
            )

    ready_jobs.sort(key=lambda item: (PRIORITY_ORDER[item["priority"]], item["jobId"]))
    selected_jobs = ready_jobs[:max_jobs]

    def project(job: dict) -> dict:
        return {
            "jobId": job["jobId"],
            "title": job["title"],
            "priority": job["priority"],
            "primaryAgent": job["primaryAgent"],
            "supportAgents": job["supportAgents"],
            "executionMode": job["executionMode"],
            "sourceTask": job.get("sourceTask"),
            "goal": job["goal"],
            "successCriteria": job["successCriteria"],
            "dependsOn": job["dependsOn"],
            "verificationCommands": job["verification"]["commands"],
            "stateRefreshRequired": job["verification"].get(
                "stateRefreshRequired", defaults.get("stateRefreshRequired", True)
            ),
            "closeoutCommands": defaults.get("closeoutCommands", ["make update-state"]),
        }

    return {
        "generatedAt": datetime.now(UTC).isoformat(),
        "queuePath": str(QUEUE_PATH.relative_to(ROOT)),
        "window": window,
        "maxJobsPerRun": max_jobs,
        "statusCounts": dict(sorted(status_counts.items())),
        "selectedJobCount": len(selected_jobs),
        "blockedJobCount": len(blocked_jobs),
        "selectedJobs": [project(job) for job in selected_jobs],
        "blockedJobs": blocked_jobs,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=QUEUE_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--window", default="nightly")
    parser.add_argument("--max-jobs", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    queue = validate_queue(load_queue(args.queue))
    max_jobs = args.max_jobs or queue.get("defaults", {}).get("maxJobsPerRun", 2)
    plan = build_plan(queue, args.window, max_jobs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
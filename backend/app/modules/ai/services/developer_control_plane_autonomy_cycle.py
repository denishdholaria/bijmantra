"""Helpers for the tracked developer control-plane autonomy-cycle artifact."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


COMPLETION_LEARNING_CLASSIFICATIONS = {
    "reviewed-completion-writeback",
    "stable-closeout-receipt",
    "mission-state",
}
DISPATCH_LEARNING_CLASSIFICATIONS = {"accepted-review"}


def resolve_developer_control_plane_autonomy_cycle_path(repo_root: Path) -> Path:
    return (
        repo_root
        / ".github"
        / "docs"
        / "architecture"
        / "tracking"
        / "developer-control-plane-autonomy-cycle.json"
    )


def load_developer_control_plane_autonomy_cycle(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Developer control-plane autonomy-cycle payload must be a JSON object")
    return payload


def build_developer_control_plane_learning_queries(
    *,
    source_lane_id: str | None,
    queue_job_id: str | None,
    linked_mission_id: str | None,
    limit: int = 3,
) -> list[tuple[str, dict[str, Any]]]:
    queries: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()

    def push(match_mode: str, **query: Any) -> None:
        normalized_query = {
            key: value
            for key, value in query.items()
            if value is not None
        }
        query_key = json.dumps(normalized_query, sort_keys=True)
        if query_key in seen:
            return
        seen.add(query_key)
        queries.append((match_mode, normalized_query))

    push(
        "exact-runtime",
        limit=limit,
        source_lane_id=source_lane_id,
        queue_job_id=queue_job_id,
        linked_mission_id=linked_mission_id,
    )

    if source_lane_id and queue_job_id and linked_mission_id:
        push(
            "lane-and-mission",
            limit=limit,
            source_lane_id=source_lane_id,
            linked_mission_id=linked_mission_id,
        )

    if source_lane_id:
        push(
            "lane-only",
            limit=limit,
            source_lane_id=source_lane_id,
        )

    if not source_lane_id and linked_mission_id:
        push(
            "mission-only",
            limit=limit,
            linked_mission_id=linked_mission_id,
        )

    if not source_lane_id and queue_job_id:
        push(
            "queue-only",
            limit=limit,
            queue_job_id=queue_job_id,
        )

    return queries


def score_developer_control_plane_autonomy_action(
    *,
    action_type: str,
    priority: str | None,
    learning_entries: Iterable[Any],
    match_mode: str,
    primary_match_mode: str,
) -> int:
    source_classifications = {
        source_classification
        for source_classification in (
            getattr(entry, "source_classification", None) for entry in learning_entries
        )
        if isinstance(source_classification, str) and source_classification
    }
    if not source_classifications:
        return 0

    fallback_used = (
        primary_match_mode not in {"", "none"}
        and match_mode not in {"", "none"}
        and match_mode != primary_match_mode
    )

    score = 0
    if (
        action_type == "prepare-completion-write-back"
        and source_classifications & COMPLETION_LEARNING_CLASSIFICATIONS
    ):
        score += 8 if not fallback_used else 5
    elif (
        action_type == "review-closeout-receipt"
        and source_classifications & COMPLETION_LEARNING_CLASSIFICATIONS
    ):
        score += 7 if not fallback_used else 4
    elif (
        action_type == "dispatch-queue-job"
        and source_classifications & DISPATCH_LEARNING_CLASSIFICATIONS
    ):
        score += 6 if not fallback_used else 3

    if score > 0 and priority == "p1":
        score += 1

    return score
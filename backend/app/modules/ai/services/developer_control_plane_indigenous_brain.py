"""Native world-model synthesis for the hidden developer control plane.

primary_domain = "ai_orchestration"
secondary_domains = ["developer_experience", "knowledge_management", "operations"]
assumptions = [
    "The Indigenous Brain should be implemented as a native world-model layer over canonical control-plane surfaces rather than as a second hidden authority store.",
    "The canonical active board, reviewed queue, durable mission state, learning ledger, and optional project-brain sidecar together provide enough grounded signals for a first situational-awareness brief.",
    "The control plane should degrade safely when one substrate is unavailable instead of failing the whole brief."
]
limitations = [
    "This slice synthesizes current state, blockers, and recommended focus, but it does not yet implement a backend planner-critic loop.",
    "Project-brain recall remains optional enrichment and is only as strong as the current bootstrap source set.",
    "The world model currently reads canonical persisted state only; unsaved local UI edits are intentionally out of scope."
]
uncertainty_handling = "The Indigenous Brain brief favors explicit surfaced gaps and safe degradation over pretending every substrate is always available or complete."
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models.developer_control_plane import (
    DeveloperControlPlaneActiveBoard,
    DeveloperControlPlaneLearningEntry,
)
from app.models.orchestrator_state import OrchestratorMission
from app.modules.ai.services.mem0_service import get_mem0_service
from app.modules.ai.services.project_brain_query import ProjectBrainQueryService
from app.schemas.developer_control_plane import (
    DeveloperMasterBoard,
    canonicalize_developer_master_board_json,
)


DEFAULT_PROJECT_BRAIN_QUERY = (
    "developer control plane world model mission state learning queue project brain"
)
QUEUE_STALE_THRESHOLD_HOURS = 18.0


def _parse_iso_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _status_counts(board: DeveloperMasterBoard) -> dict[str, int]:
    counts = Counter(lane.status for lane in board.lanes)
    return {
        key: counts.get(key, 0)
        for key in ("active", "planned", "blocked", "watch", "completed")
    }


def _board_signal(
    active_board_record: DeveloperControlPlaneActiveBoard | None,
    board_error: str | None,
) -> tuple[dict[str, Any], DeveloperMasterBoard | None]:
    if board_error is not None:
        return (
            {
                "available": False,
                "board_id": None,
                "title": None,
                "lane_count": 0,
                "status_counts": {},
                "active_lane_count": 0,
                "blocked_lane_count": 0,
                "active_lane_ids": [],
                "blocked_lane_ids": [],
                "lanes_missing_review": [],
                "lanes_pending_closure": [],
                "primary_orchestrator": None,
                "updated_at": None,
                "detail": board_error,
            },
            None,
        )

    if active_board_record is None:
        return (
            {
                "available": False,
                "board_id": None,
                "title": None,
                "lane_count": 0,
                "status_counts": {},
                "active_lane_count": 0,
                "blocked_lane_count": 0,
                "active_lane_ids": [],
                "blocked_lane_ids": [],
                "lanes_missing_review": [],
                "lanes_pending_closure": [],
                "primary_orchestrator": None,
                "updated_at": None,
                "detail": "No shared active board is persisted yet.",
            },
            None,
        )

    try:
        _canonical_json, board = canonicalize_developer_master_board_json(
            active_board_record.canonical_board_json
        )
    except ValueError as exc:
        return (
            {
                "available": False,
                "board_id": active_board_record.board_id,
                "title": None,
                "lane_count": 0,
                "status_counts": {},
                "active_lane_count": 0,
                "blocked_lane_count": 0,
                "active_lane_ids": [],
                "blocked_lane_ids": [],
                "lanes_missing_review": [],
                "lanes_pending_closure": [],
                "primary_orchestrator": None,
                "updated_at": active_board_record.updated_at.isoformat(),
                "detail": f"Canonical active board is invalid: {exc}",
            },
            None,
        )

    status_counts = _status_counts(board)
    active_lane_ids = [lane.id for lane in board.lanes if lane.status == "active"]
    blocked_lane_ids = [lane.id for lane in board.lanes if lane.status == "blocked"]
    lanes_missing_review = [
        lane.id
        for lane in board.lanes
        if lane.review_state is None
        or lane.review_state.spec_review is None
        or lane.review_state.risk_review is None
        or lane.review_state.verification_evidence is None
    ]
    lanes_pending_closure = [
        lane.id for lane in board.lanes if lane.status == "active" and lane.closure is None
    ]

    return (
        {
            "available": True,
            "board_id": board.board_id,
            "title": board.title,
            "lane_count": len(board.lanes),
            "status_counts": status_counts,
            "active_lane_count": status_counts["active"],
            "blocked_lane_count": status_counts["blocked"],
            "active_lane_ids": active_lane_ids,
            "blocked_lane_ids": blocked_lane_ids,
            "lanes_missing_review": lanes_missing_review,
            "lanes_pending_closure": lanes_pending_closure,
            "primary_orchestrator": board.control_plane.primary_orchestrator,
            "updated_at": active_board_record.updated_at.isoformat(),
            "detail": None,
        },
        board,
    )


def _queue_signal(queue_path: Path) -> dict[str, Any]:
    if not queue_path.exists():
        return {
            "exists": False,
            "queue_path": str(queue_path),
            "queue_sha256": None,
            "job_count": 0,
            "updated_at": None,
            "age_hours": None,
            "is_stale": False,
            "stale_threshold_hours": QUEUE_STALE_THRESHOLD_HOURS,
            "top_job_ids": [],
            "detail": "Reviewed overnight queue file is not present.",
        }

    raw_queue = queue_path.read_text(encoding="utf-8")
    queue_payload = json.loads(raw_queue)
    jobs = queue_payload.get("jobs", [])
    updated_at = _parse_iso_timestamp(queue_payload.get("updatedAt"))
    if updated_at is None:
        updated_at = datetime.fromtimestamp(queue_path.stat().st_mtime, tz=UTC)

    age_hours = max(
        0.0,
        round((datetime.now(UTC) - updated_at).total_seconds() / 3600, 2),
    )

    return {
        "exists": True,
        "queue_path": str(queue_path),
        "queue_sha256": hashlib.sha256(raw_queue.encode("utf-8")).hexdigest(),
        "job_count": len(jobs),
        "updated_at": updated_at.isoformat(),
        "age_hours": age_hours,
        "is_stale": age_hours >= QUEUE_STALE_THRESHOLD_HOURS,
        "stale_threshold_hours": QUEUE_STALE_THRESHOLD_HOURS,
        "top_job_ids": [job.get("jobId") for job in jobs[:5] if isinstance(job, dict)],
        "detail": None,
    }


def _mission_signal(
    mission_records: Sequence[OrchestratorMission],
    mission_total_count: int,
    mission_error: str | None,
) -> dict[str, Any]:
    if mission_error is not None:
        return {
            "available": False,
            "total_count": 0,
            "active_count": 0,
            "blocked_count": 0,
            "escalation_count": 0,
            "recent": [],
            "detail": mission_error,
        }

    active_count = sum(
        1 for mission in mission_records if mission.status not in {"completed", "cancelled"}
    )
    blocked_count = sum(1 for mission in mission_records if mission.status == "blocked")
    escalation_count = sum(
        1 for mission in mission_records if getattr(mission, "escalation_needed", False)
    )

    return {
        "available": True,
        "total_count": mission_total_count,
        "active_count": active_count,
        "blocked_count": blocked_count,
        "escalation_count": escalation_count,
        "recent": [
            {
                "mission_id": mission.mission_id,
                "objective": mission.objective,
                "status": mission.status,
                "queue_job_id": mission.queue_job_id,
                "source_lane_id": mission.source_lane_id,
                "updated_at": mission.updated_at.isoformat(),
            }
            for mission in mission_records[:5]
        ],
        "detail": None,
    }


def _learning_signal(
    learning_entries: Sequence[DeveloperControlPlaneLearningEntry],
    learning_total_count: int,
    learning_error: str | None,
) -> dict[str, Any]:
    if learning_error is not None:
        return {
            "available": False,
            "total_count": 0,
            "recent": [],
            "detail": learning_error,
        }

    return {
        "available": True,
        "total_count": learning_total_count,
        "recent": [
            {
                "learning_entry_id": entry.id,
                "entry_type": entry.entry_type,
                "source_classification": entry.source_classification,
                "title": entry.title,
                "summary": entry.summary,
                "source_lane_id": entry.source_lane_id,
                "queue_job_id": entry.queue_job_id,
                "recorded_at": entry.created_at.isoformat(),
            }
            for entry in learning_entries[:5]
        ],
        "detail": None,
    }


async def _project_brain_signal(
    project_brain_query_service: ProjectBrainQueryService | None,
    *,
    project_brain_base_url: str,
    project_brain_query: str,
    project_brain_detail: str | None,
) -> dict[str, Any]:
    if project_brain_query_service is None:
        return {
            "available": False,
            "base_url": project_brain_base_url,
            "query": project_brain_query,
            "source_match_count": 0,
            "projection_match_count": 0,
            "node_match_count": 0,
            "provenance_trail_count": 0,
            "notable_source_paths": [],
            "notable_node_titles": [],
            "detail": project_brain_detail or "Project-brain sidecar is not currently reachable.",
        }

    try:
        result = await project_brain_query_service.query(
            project_brain_query,
            include_provenance=True,
        )
    except Exception as exc:
        return {
            "available": False,
            "base_url": project_brain_base_url,
            "query": project_brain_query,
            "source_match_count": 0,
            "projection_match_count": 0,
            "node_match_count": 0,
            "provenance_trail_count": 0,
            "notable_source_paths": [],
            "notable_node_titles": [],
            "detail": f"Project-brain recall failed: {exc}",
        }

    return {
        "available": True,
        "base_url": project_brain_base_url,
        "query": project_brain_query,
        "source_match_count": len(result.recall_view.source_artifacts),
        "projection_match_count": len(result.recall_view.projections),
        "node_match_count": len(result.recall_view.nodes),
        "provenance_trail_count": len(result.provenance_trails),
        "notable_source_paths": [
            item.source_path for item in result.recall_view.source_artifacts[:3]
        ],
        "notable_node_titles": [item.title for item in result.recall_view.nodes[:3]],
        "detail": None,
    }


def _mem0_signal() -> dict[str, Any]:
    status = get_mem0_service().status()
    ready = status["configured"] and status["org_project_pair_valid"]

    if not status["enabled"]:
        detail = (
            "Mem0 is disabled. It remains an optional external episodic-memory adapter, "
            "not part of the canonical self-building loop yet."
        )
    elif not status["configured"]:
        detail = "Mem0 is enabled in intent but MEM0_API_KEY is not configured."
    elif not status["org_project_pair_valid"]:
        detail = "MEM0_ORG_ID and MEM0_PROJECT_ID must be configured together when project scoping is used."
    else:
        detail = "Mem0 is ready as an optional external episodic-memory adapter."

    return {
        "enabled": status["enabled"],
        "configured": status["configured"],
        "ready": ready,
        "host": status["host"],
        "project_scoped": status["project_scoped"],
        "org_project_pair_valid": status["org_project_pair_valid"],
        "detail": detail,
    }


def _recommended_focus(
    board: DeveloperMasterBoard | None,
    board_signal: dict[str, Any],
    mission_signal: dict[str, Any],
    queue_signal: dict[str, Any],
) -> dict[str, Any] | None:
    if board is None:
        return None

    lane_by_id = {lane.id: lane for lane in board.lanes}

    for lane in board.lanes:
        if lane.status != "active" or lane.closure is not None:
            continue

        blocked_dependencies = [
            dependency
            for dependency in lane.dependencies
            if dependency in lane_by_id and lane_by_id[dependency].status == "blocked"
        ]
        if blocked_dependencies:
            continue

        if lane.id in board_signal["lanes_missing_review"]:
            reason = (
                "This active lane is the next safe focus because its reviewed governance is incomplete in the canonical board."
            )
        elif mission_signal["available"] and mission_signal["total_count"] == 0:
            reason = (
                "This active lane has no durable mission-state context yet, so it is the strongest candidate for the next native execution link."
            )
        elif queue_signal["exists"] and queue_signal["job_count"] == 0:
            reason = (
                "The canonical board has active work but the reviewed overnight queue is empty, so this lane is the next export candidate."
            )
        else:
            reason = (
                "This is the first active canonical lane without closure evidence and without blocked dependencies."
            )

        return {
            "source": "active-board",
            "lane_id": lane.id,
            "title": lane.title,
            "status": lane.status,
            "objective": lane.objective,
            "reason": reason,
            "dependencies": list(lane.dependencies),
        }

    return None


def _blockers(
    board_signal: dict[str, Any],
    queue_signal: dict[str, Any],
    mission_signal: dict[str, Any],
    learning_signal: dict[str, Any],
    project_brain_signal: dict[str, Any],
    mem0_signal: dict[str, Any],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []

    if not board_signal["available"]:
        blockers.append(
            {
                "key": "active-board-missing",
                "severity": "blocking",
                "surface": "active-board",
                "summary": "The canonical shared board is missing or unreadable, so autonomous planning lacks a stable source of truth.",
                "recommended_action": "Persist or repair the shared active board before extending autonomous execution.",
            }
        )

    if board_signal["available"] and board_signal["blocked_lane_count"] > 0:
        blockers.append(
            {
                "key": "blocked-lanes-present",
                "severity": "blocking",
                "surface": "board",
                "summary": f"The canonical board currently carries {board_signal['blocked_lane_count']} blocked lane(s).",
                "recommended_action": "Resolve or downgrade blocked lanes so the orchestrator is not forced to reason across stale dependencies.",
            }
        )

    if board_signal["available"] and board_signal["lanes_missing_review"]:
        blockers.append(
            {
                "key": "review-gates-incomplete",
                "severity": "watch",
                "surface": "board",
                "summary": "At least one lane is missing explicit review or verification evidence in the canonical board.",
                "recommended_action": "Fill spec, risk, and verification gates for dispatchable lanes before treating them as autonomous-ready.",
            }
        )

    if not queue_signal["exists"]:
        blockers.append(
            {
                "key": "reviewed-queue-missing",
                "severity": "watch",
                "surface": "overnight-queue",
                "summary": "The reviewed overnight queue file is absent, so the execution surface is not materialized from the canonical board.",
                "recommended_action": "Export at least one reviewed queue entry once the next lane is safe to dispatch.",
            }
        )
    elif queue_signal["is_stale"]:
        blockers.append(
            {
                "key": "reviewed-queue-stale",
                "severity": "blocking",
                "surface": "overnight-queue",
                "summary": f"The reviewed overnight queue is stale at {queue_signal['age_hours']} hours.",
                "recommended_action": "Refresh the queue snapshot before trusting it as the current execution surface.",
            }
        )

    if mission_signal["available"] and mission_signal["total_count"] == 0:
        blockers.append(
            {
                "key": "mission-state-empty",
                "severity": "blocking",
                "surface": "mission-state",
                "summary": "No durable mission-state records are present, so execution memory is still too thin for a self-building loop.",
                "recommended_action": "Link active control-plane work into durable mission-state instead of relying only on board JSON and queue entries.",
            }
        )

    if learning_signal["available"] and learning_signal["total_count"] == 0:
        blockers.append(
            {
                "key": "learning-ledger-empty",
                "severity": "watch",
                "surface": "learning-ledger",
                "summary": "The learning ledger has no retained patterns or incidents, so the reflective loop is still weak.",
                "recommended_action": "Record the first durable learnings from completed or blocked execution slices.",
            }
        )

    if not project_brain_signal["available"]:
        blockers.append(
            {
                "key": "project-brain-offline",
                "severity": "advisory",
                "surface": "project-brain",
                "summary": "Optional project-brain recall enrichment is offline, so cross-surface associative memory remains limited.",
                "recommended_action": "Start the optional sidecar only when deeper cross-surface recall is needed for a developer slice.",
            }
        )

    if mem0_signal["enabled"] and not mem0_signal["ready"]:
        blockers.append(
            {
                "key": "mem0-config-incomplete",
                "severity": "watch",
                "surface": "mem0",
                "summary": "Mem0 has been turned on in intent but is not runtime-ready yet.",
                "recommended_action": "Either finish Mem0 API configuration or disable it until the system is ready to use it deliberately.",
            }
        )

    return blockers


def _missing_capabilities(
    board_signal: dict[str, Any],
    queue_signal: dict[str, Any],
    mission_signal: dict[str, Any],
    learning_signal: dict[str, Any],
    project_brain_signal: dict[str, Any],
    mem0_signal: dict[str, Any],
) -> list[str]:
    missing: list[str] = []

    if not board_signal["available"]:
        missing.append("Shared canonical board persistence is not yet reliably present.")
    if board_signal["available"] and board_signal["lanes_missing_review"]:
        missing.append("Lane review coverage is incomplete for at least one canonical lane.")
    if mission_signal["available"] and mission_signal["total_count"] == 0:
        missing.append("Durable mission-state memory is not yet populated for the active control-plane loop.")
    if learning_signal["available"] and learning_signal["total_count"] == 0:
        missing.append("Reflective learning consolidation has not yet produced durable lessons.")
    if queue_signal["exists"] and queue_signal["job_count"] == 0:
        missing.append("Reviewed queue materialization is still empty even though the board can express active lanes.")
    if not queue_signal["exists"]:
        missing.append("The derived overnight execution surface is not yet materialized on disk.")
    if not project_brain_signal["available"]:
        missing.append("Cross-surface associative recall is still optional and currently offline.")
    if mem0_signal["enabled"] and not mem0_signal["ready"]:
        missing.append("Mem0 is enabled in direction but not configured cleanly enough for trustworthy runtime use.")

    if not missing:
        missing.append(
            "Backend planner-critic execution remains the next higher-order autonomy slice beyond this world-model foundation."
        )

    return missing


def _worldview_summary(
    board_signal: dict[str, Any],
    queue_signal: dict[str, Any],
    mission_signal: dict[str, Any],
    learning_signal: dict[str, Any],
    project_brain_signal: dict[str, Any],
    mem0_signal: dict[str, Any],
    recommended_focus: dict[str, Any] | None,
) -> str:
    segments = [
        "Indigenous Brain is now defined as the native control-plane world model rather than a second authority store.",
    ]

    if board_signal["available"]:
        segments.append(
            f"The shared board currently shows {board_signal['active_lane_count']} active lane(s) and {board_signal['blocked_lane_count']} blocked lane(s)."
        )
    else:
        segments.append("The shared board is not yet available to the world model.")

    if queue_signal["exists"]:
        freshness = "stale" if queue_signal["is_stale"] else "fresh"
        segments.append(
            f"The reviewed queue currently holds {queue_signal['job_count']} job(s) and is {freshness} at {queue_signal['age_hours']} hours."
        )
    else:
        segments.append("The reviewed queue is not materialized yet.")

    if mission_signal["available"]:
        segments.append(
            f"Durable mission state currently reports {mission_signal['total_count']} mission(s) with {mission_signal['escalation_count']} escalation signal(s)."
        )

    if learning_signal["available"]:
        segments.append(
            f"The learning ledger retains {learning_signal['total_count']} recent lesson(s)."
        )

    segments.append(
        "Project-brain enrichment is connected."
        if project_brain_signal["available"]
        else "Project-brain enrichment is currently offline but remains optional."
    )

    if mem0_signal["ready"]:
        segments.append("Mem0 is available as optional external episodic memory.")
    elif mem0_signal["enabled"]:
        segments.append("Mem0 is enabled in direction but not runtime-ready yet.")
    else:
        segments.append("Mem0 remains disabled and outside the current canonical autonomy loop.")

    if recommended_focus is not None:
        segments.append(
            f"The current recommended focus is lane {recommended_focus['lane_id']} ({recommended_focus['title']})."
        )

    return " ".join(segments)


async def build_developer_control_plane_indigenous_brain_brief(
    *,
    active_board_record: DeveloperControlPlaneActiveBoard | None,
    board_error: str | None,
    mission_records: Sequence[OrchestratorMission],
    mission_total_count: int,
    mission_error: str | None,
    learning_entries: Sequence[DeveloperControlPlaneLearningEntry],
    learning_total_count: int,
    learning_error: str | None,
    queue_path: Path,
    project_brain_query_service: ProjectBrainQueryService | None,
    project_brain_base_url: str,
    project_brain_query: str = DEFAULT_PROJECT_BRAIN_QUERY,
    project_brain_detail: str | None = None,
) -> dict[str, Any]:
    board_signal, board = _board_signal(active_board_record, board_error)
    queue_signal = _queue_signal(queue_path)
    mission_signal = _mission_signal(mission_records, mission_total_count, mission_error)
    learning_signal = _learning_signal(
        learning_entries,
        learning_total_count,
        learning_error,
    )
    project_brain_signal = await _project_brain_signal(
        project_brain_query_service,
        project_brain_base_url=project_brain_base_url,
        project_brain_query=project_brain_query,
        project_brain_detail=project_brain_detail,
    )
    mem0_signal = _mem0_signal()
    recommended_focus = _recommended_focus(
        board,
        board_signal,
        mission_signal,
        queue_signal,
    )
    blockers = _blockers(
        board_signal,
        queue_signal,
        mission_signal,
        learning_signal,
        project_brain_signal,
        mem0_signal,
    )
    missing_capabilities = _missing_capabilities(
        board_signal,
        queue_signal,
        mission_signal,
        learning_signal,
        project_brain_signal,
        mem0_signal,
    )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "indigenous_brain": {
            "status": "bootstrapped",
            "summary": "Backend-native world model for the developer control plane.",
            "authority_boundary": "It synthesizes canonical board, queue, mission, learning, and optional project-brain signals without promoting itself into a new authority source.",
            "current_role": "Turn scattered internal control-plane surfaces into one actionable, evidence-backed brief for autonomous development.",
        },
        "worldview_summary": _worldview_summary(
            board_signal,
            queue_signal,
            mission_signal,
            learning_signal,
            project_brain_signal,
            mem0_signal,
            recommended_focus,
        ),
        "board": board_signal,
        "queue": queue_signal,
        "missions": mission_signal,
        "learnings": learning_signal,
        "project_brain": project_brain_signal,
        "mem0": mem0_signal,
        "recommended_focus": recommended_focus,
        "blockers": blockers,
        "missing_capabilities": missing_capabilities,
    }


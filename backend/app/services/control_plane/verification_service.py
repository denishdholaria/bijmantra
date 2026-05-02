"""Verification service for developer control plane.

Handles silent monitors, autonomy cycle, completion assist, and watchdog status queries.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.services.developer_control_plane_autonomy_cycle import (
    build_developer_control_plane_learning_queries,
    score_developer_control_plane_autonomy_action,
)
from app.models.developer_control_plane import DeveloperControlPlaneLearningEntry


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QUEUE_STALENESS_WATCH_HOURS = 18
QUEUE_STALENESS_ALERT_HOURS = 36
SILENT_MONITOR_OUTPUT_ARTIFACT_PREFIX = "developer-control-plane.runtime.silent-monitors"


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def parse_monitor_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO 8601 timestamp string to a UTC-aware datetime."""
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


def trim_monitor_detail(value: str | None, limit: int = 280) -> str | None:
    """Trim and normalize a monitor detail string to at most `limit` characters."""
    if value is None:
        return None

    normalized = " ".join(value.split())
    if not normalized:
        return None

    if len(normalized) <= limit:
        return normalized

    return f"{normalized[: limit - 3].rstrip()}..."


def string_list(value: Any) -> list[str]:
    """Safely coerce a value to a list of strings."""
    if not isinstance(value, list):
        return []

    return [item for item in value if isinstance(item, str)]


def relative_repo_path(path: Path, repo_root: Path) -> str:
    """Return a path relative to repo_root, or the absolute path if not relative."""
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def load_optional_json_object(
    path: Path,
    repo_root: Path,
) -> tuple[dict[str, Any] | None, str | None]:
    """Load a JSON object from a file, returning (payload, error_message).

    Returns:
        (payload, None) on success, (None, error_message) on failure,
        (None, None) if the file does not exist.
    """
    import json

    if not path.exists():
        return None, None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"Unable to read {relative_repo_path(path, repo_root)}: {exc}"

    if not isinstance(payload, dict):
        return None, f"{relative_repo_path(path, repo_root)} must be a JSON object"

    return payload, None


# ---------------------------------------------------------------------------
# Silent monitor builders
# ---------------------------------------------------------------------------

def build_silent_monitor_response(
    *,
    monitor_key: str,
    label: str,
    state: str,
    summary: str,
    detail: str | None,
    observed_at: str | None,
    refresh_cadence: str,
    evidence_sources: list[dict[str, Any]],
    findings: list[str],
    output_artifact_prefix: str = SILENT_MONITOR_OUTPUT_ARTIFACT_PREFIX,
) -> dict[str, Any]:
    """Build a silent monitor response dict."""
    return {
        "monitor_key": monitor_key,
        "label": label,
        "state": state,
        "should_emit": state != "healthy",
        "summary": summary,
        "detail": detail,
        "observed_at": observed_at,
        "refresh_cadence": refresh_cadence,
        "output_artifact": f"{output_artifact_prefix}.{monitor_key}",
        "mutates_authority_surfaces": False,
        "evidence_sources": evidence_sources,
        "findings": findings,
    }


def queue_staleness_monitor(
    queue_status: dict[str, Any],
    watch_hours: int = QUEUE_STALENESS_WATCH_HOURS,
    alert_hours: int = QUEUE_STALENESS_ALERT_HOURS,
) -> dict[str, Any]:
    """Build the queue staleness silent monitor response.

    Args:
        queue_status: Dict with queue_path, queue_sha256, exists, job_count, updated_at.
        watch_hours: Hours before entering watch state.
        alert_hours: Hours before entering alert state.
    """
    evidence_sources = [
        {
            "label": "Overnight queue status",
            "path": queue_status.get("queue_path", ""),
            "observed_at": queue_status.get("updated_at"),
        }
    ]

    if not queue_status.get("exists"):
        return build_silent_monitor_response(
            monitor_key="queue-staleness",
            label="Queue staleness",
            state="alert",
            summary="The derived overnight queue file is missing.",
            detail="Execution export cannot be sampled until .agent/jobs/overnight-queue.json exists again.",
            observed_at=None,
            refresh_cadence="Nightly and immediately after each reviewed queue export",
            evidence_sources=evidence_sources,
            findings=["overnight-queue.missing"],
        )

    updated_at_str = queue_status.get("updated_at")
    if not updated_at_str:
        return build_silent_monitor_response(
            monitor_key="queue-staleness",
            label="Queue staleness",
            state="watch",
            summary="The overnight queue exists but does not advertise an updatedAt timestamp.",
            detail=(
                f"Queue hash {queue_status.get('queue_sha256', '')}; "
                f"sampled job count {queue_status.get('job_count', 0)}."
            ),
            observed_at=None,
            refresh_cadence="Nightly and immediately after each reviewed queue export",
            evidence_sources=evidence_sources,
            findings=["overnight-queue.updated-at-missing"],
        )

    updated_at = parse_monitor_timestamp(updated_at_str)
    if updated_at is None:
        return build_silent_monitor_response(
            monitor_key="queue-staleness",
            label="Queue staleness",
            state="watch",
            summary="The overnight queue timestamp is present but could not be parsed.",
            detail=(
                f"Queue hash {queue_status.get('queue_sha256', '')}; "
                f"raw updatedAt value {updated_at_str!r}."
            ),
            observed_at=updated_at_str,
            refresh_cadence="Nightly and immediately after each reviewed queue export",
            evidence_sources=evidence_sources,
            findings=["overnight-queue.updated-at-invalid"],
        )

    age_seconds = max(0.0, (datetime.now(UTC) - updated_at).total_seconds())
    age_hours = age_seconds / 3600
    detail = (
        f"Queue hash {queue_status.get('queue_sha256', '')}; "
        f"{queue_status.get('job_count', 0)} sampled jobs; "
        f"age {age_hours:.1f}h."
    )

    if age_hours >= alert_hours:
        return build_silent_monitor_response(
            monitor_key="queue-staleness",
            label="Queue staleness",
            state="alert",
            summary="The overnight queue snapshot is older than the nightly freshness window.",
            detail=detail,
            observed_at=updated_at_str,
            refresh_cadence="Nightly and immediately after each reviewed queue export",
            evidence_sources=evidence_sources,
            findings=[f"overnight-queue.age-hours>={alert_hours}"],
        )

    if age_hours >= watch_hours:
        return build_silent_monitor_response(
            monitor_key="queue-staleness",
            label="Queue staleness",
            state="watch",
            summary="The overnight queue snapshot is aging toward staleness.",
            detail=detail,
            observed_at=updated_at_str,
            refresh_cadence="Nightly and immediately after each reviewed queue export",
            evidence_sources=evidence_sources,
            findings=[f"overnight-queue.age-hours>={watch_hours}"],
        )

    return build_silent_monitor_response(
        monitor_key="queue-staleness",
        label="Queue staleness",
        state="healthy",
        summary="The overnight queue snapshot looks fresh for the current nightly cadence.",
        detail=detail,
        observed_at=updated_at_str,
        refresh_cadence="Nightly and immediately after each reviewed queue export",
        evidence_sources=evidence_sources,
        findings=[],
    )


def control_surface_drift_monitor(
    control_surface_check_script: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Build the control surface drift silent monitor response.

    Runs the check script and reports the result.
    """
    observed_at = datetime.now(UTC).isoformat()
    evidence_sources = [
        {
            "label": "Canonical control-surface checker",
            "path": relative_repo_path(control_surface_check_script, repo_root),
            "observed_at": observed_at,
        }
    ]

    if not control_surface_check_script.exists():
        return build_silent_monitor_response(
            monitor_key="control-surface-drift",
            label="Control-surface drift",
            state="missing",
            summary="The canonical control-surface checker is missing.",
            detail=(
                f"Expected script {relative_repo_path(control_surface_check_script, repo_root)} "
                "could not be found."
            ),
            observed_at=observed_at,
            refresh_cadence="Before operator handoff and after control-plane contract changes",
            evidence_sources=evidence_sources,
            findings=["control-surfaces.check-script-missing"],
        )

    try:
        completed = subprocess.run(
            [sys.executable, str(control_surface_check_script)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return build_silent_monitor_response(
            monitor_key="control-surface-drift",
            label="Control-surface drift",
            state="alert",
            summary="The control-surface checker timed out.",
            detail=trim_monitor_detail(str(exc)),
            observed_at=observed_at,
            refresh_cadence="Before operator handoff and after control-plane contract changes",
            evidence_sources=evidence_sources,
            findings=["control-surfaces.check-timeout"],
        )
    except OSError as exc:
        return build_silent_monitor_response(
            monitor_key="control-surface-drift",
            label="Control-surface drift",
            state="alert",
            summary="The control-surface checker could not be executed.",
            detail=trim_monitor_detail(str(exc)),
            observed_at=observed_at,
            refresh_cadence="Before operator handoff and after control-plane contract changes",
            evidence_sources=evidence_sources,
            findings=["control-surfaces.check-execution-failed"],
        )

    command_output = trim_monitor_detail(completed.stderr or completed.stdout)
    if completed.returncode == 0:
        return build_silent_monitor_response(
            monitor_key="control-surface-drift",
            label="Control-surface drift",
            state="healthy",
            summary="The canonical control-surface checker reports no structural drift.",
            detail=command_output,
            observed_at=observed_at,
            refresh_cadence="Before operator handoff and after control-plane contract changes",
            evidence_sources=evidence_sources,
            findings=[],
        )

    return build_silent_monitor_response(
        monitor_key="control-surface-drift",
        label="Control-surface drift",
        state="alert",
        summary="The canonical control-surface checker detected drift or structural damage.",
        detail=command_output,
        observed_at=observed_at,
        refresh_cadence="Before operator handoff and after control-plane contract changes",
        evidence_sources=evidence_sources,
        findings=["control-surfaces.drift-detected"],
    )


def reevu_readiness_monitor(
    reevu_real_question_report_path: Path,
    reevu_readiness_census_path: Path,
    reevu_authority_gap_report_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Build the REEVU readiness silent monitor response."""
    real_question_report, real_question_error = load_optional_json_object(
        reevu_real_question_report_path, repo_root
    )
    readiness_census, readiness_census_error = load_optional_json_object(
        reevu_readiness_census_path, repo_root
    )
    authority_gap_report, authority_gap_error = load_optional_json_object(
        reevu_authority_gap_report_path, repo_root
    )

    evidence_sources: list[dict[str, Any]] = []
    for label, path, payload in (
        ("REEVU real-question benchmark", reevu_real_question_report_path, real_question_report),
        ("REEVU local readiness census", reevu_readiness_census_path, readiness_census),
        ("REEVU authority gap report", reevu_authority_gap_report_path, authority_gap_report),
    ):
        evidence_sources.append(
            {
                "label": label,
                "path": relative_repo_path(path, repo_root),
                "observed_at": payload.get("generated_at") if isinstance(payload, dict) else None,
            }
        )

    missing_artifacts = [
        relative_repo_path(path, repo_root)
        for path, payload, error in (
            (reevu_real_question_report_path, real_question_report, real_question_error),
            (reevu_readiness_census_path, readiness_census, readiness_census_error),
            (reevu_authority_gap_report_path, authority_gap_report, authority_gap_error),
        )
        if payload is None and error is None
    ]
    artifact_errors = [
        error
        for error in (real_question_error, readiness_census_error, authority_gap_error)
        if error is not None
    ]

    if missing_artifacts:
        return build_silent_monitor_response(
            monitor_key="reevu-readiness",
            label="REEVU readiness",
            state="missing",
            summary="One or more REEVU readiness artifacts are missing.",
            detail="Missing artifacts: " + ", ".join(missing_artifacts),
            observed_at=None,
            refresh_cadence="After REEVU readiness census, benchmark, or authority-gap regeneration",
            evidence_sources=evidence_sources,
            findings=[f"missing:{path}" for path in missing_artifacts],
        )

    if artifact_errors:
        return build_silent_monitor_response(
            monitor_key="reevu-readiness",
            label="REEVU readiness",
            state="alert",
            summary="One or more REEVU readiness artifacts could not be read.",
            detail=trim_monitor_detail("; ".join(artifact_errors)),
            observed_at=None,
            refresh_cadence="After REEVU readiness census, benchmark, or authority-gap regeneration",
            evidence_sources=evidence_sources,
            findings=["reevu.readiness-artifact-read-failed"],
        )

    # Both reports are present — extract key metrics
    runtime_status = (
        real_question_report.get("runtime_status")  # type: ignore[union-attr]
        if isinstance(real_question_report.get("runtime_status"), str)  # type: ignore[union-attr]
        else None
    )
    passed_cases = (
        real_question_report.get("passed_cases")  # type: ignore[union-attr]
        if isinstance(real_question_report.get("passed_cases"), int)  # type: ignore[union-attr]
        else None
    )
    total_cases = (
        real_question_report.get("total_cases")  # type: ignore[union-attr]
        if isinstance(real_question_report.get("total_cases"), int)  # type: ignore[union-attr]
        else None
    )
    pass_rate = (
        float(real_question_report.get("pass_rate"))  # type: ignore[union-attr]
        if isinstance(real_question_report.get("pass_rate"), (int, float))  # type: ignore[union-attr]
        else None
    )
    benchmark_ready_org_ids = string_list(
        readiness_census.get("benchmark_ready_organization_ids")  # type: ignore[union-attr]
    )
    if not benchmark_ready_org_ids and isinstance(
        readiness_census.get("benchmark_ready_organization_ids"), list  # type: ignore[union-attr]
    ):
        benchmark_ready_org_ids = [
            str(item)
            for item in readiness_census.get("benchmark_ready_organization_ids")  # type: ignore[union-attr]
            if isinstance(item, int)
        ]
    overall_gap_status = (
        authority_gap_report.get("overall_gap_status")  # type: ignore[union-attr]
        if isinstance(authority_gap_report.get("overall_gap_status"), str)  # type: ignore[union-attr]
        else None
    )
    blockers = string_list(authority_gap_report.get("selected_local_org_blockers"))  # type: ignore[union-attr]
    if not blockers:
        blockers = string_list(authority_gap_report.get("common_blockers_across_blocked_orgs"))  # type: ignore[union-attr]

    observed_candidates = [
        payload.get("generated_at")
        for payload in (real_question_report, readiness_census, authority_gap_report)
        if isinstance(payload.get("generated_at"), str)  # type: ignore[union-attr]
    ]
    observed_at = max(observed_candidates, default=None)
    benchmark_ready_count = len(benchmark_ready_org_ids)
    ready_local_orgs = [
        organization
        for organization in readiness_census.get("organizations", [])  # type: ignore[union-attr]
        if isinstance(organization, dict)
        and organization.get("runtime_status") == "ready"
        and isinstance(organization.get("organization_id"), int)
    ]
    least_blocked_local_organization = (
        readiness_census.get("least_blocked_local_organization")  # type: ignore[union-attr]
        if isinstance(readiness_census.get("least_blocked_local_organization"), dict)  # type: ignore[union-attr]
        else None
    )
    pass_summary = (
        f"{passed_cases}/{total_cases} real-question cases passed"
        if passed_cases is not None and total_cases is not None
        else "real-question pass rate unavailable"
    )
    detail_parts = [
        pass_summary,
        f"runtime status {runtime_status or 'unknown'}",
        f"benchmark-ready local orgs {benchmark_ready_count}",
        f"gap status {overall_gap_status or 'unknown'}",
    ]
    if blockers:
        detail_parts.append("blockers: " + ", ".join(blockers[:3]))
    if ready_local_orgs:
        ready_org_labels = ", ".join(
            f"{organization.get('organization_id')} ({organization.get('organization_name') or 'unnamed'})"
            for organization in ready_local_orgs[:3]
        )
        detail_parts.append("ready local orgs: " + ready_org_labels)
    if isinstance(least_blocked_local_organization, dict):
        least_blocked_id = least_blocked_local_organization.get("organization_id")
        least_blocked_name = least_blocked_local_organization.get("organization_name") or "unnamed"
        least_blocked_blockers = string_list(
            least_blocked_local_organization.get("readiness_blockers")
        )
        detail_parts.append(
            f"least-blocked local org {least_blocked_id} ({least_blocked_name})"
        )
        if least_blocked_blockers:
            detail_parts.append(
                "least-blocked blockers: " + ", ".join(least_blocked_blockers[:3])
            )
    detail = "; ".join(detail_parts) + "."

    if runtime_status == "ready" and benchmark_ready_count > 0 and overall_gap_status in {
        "ready",
        "benchmark-ready",
        "benchmark_ready",
    }:
        state = "watch" if pass_rate is not None and pass_rate < 0.8 else "healthy"
        summary = (
            "REEVU readiness artifacts are present and benchmark-ready local evidence exists."
            if state == "healthy"
            else "REEVU readiness artifacts are present, but benchmark pass rate still needs attention."
        )
        findings = [] if state == "healthy" else ["reevu.pass-rate-below-target"]
        return build_silent_monitor_response(
            monitor_key="reevu-readiness",
            label="REEVU readiness",
            state=state,
            summary=summary,
            detail=detail,
            observed_at=observed_at,
            refresh_cadence="After REEVU readiness census, benchmark, or authority-gap regeneration",
            evidence_sources=evidence_sources,
            findings=findings,
        )

    return build_silent_monitor_response(
        monitor_key="reevu-readiness",
        label="REEVU readiness",
        state="alert",
        summary="REEVU readiness is degraded for the current local evidence set.",
        detail=detail,
        observed_at=observed_at,
        refresh_cadence="After REEVU readiness census, benchmark, or authority-gap regeneration",
        evidence_sources=evidence_sources,
        findings=blockers[:5],
    )


def derive_silent_monitor_overall_state(monitors: list[dict[str, Any]]) -> str:
    """Derive the overall state from a list of monitor response dicts."""
    state_priority = {
        "alert": 4,
        "missing": 3,
        "watch": 2,
        "healthy": 1,
    }
    highest_state = "healthy"
    highest_priority = 0
    for monitor in monitors:
        priority = state_priority.get(monitor.get("state", ""), 0)
        if priority > highest_priority:
            highest_priority = priority
            highest_state = monitor.get("state", "healthy")

    return highest_state


# ---------------------------------------------------------------------------
# Autonomy cycle next-action ranking
# ---------------------------------------------------------------------------

async def memory_biased_autonomy_cycle_next_actions(
    db: AsyncSession,
    organization_id: int,
    next_actions: list[dict[str, Any]],
    get_learning_entries_fn: Any,
    get_missing_learning_tables_fn: Any,
) -> tuple[list[dict[str, Any]], str]:
    """Re-rank autonomy cycle next actions using learning ledger data.

    Args:
        db: Database session
        organization_id: Organization ID
        next_actions: List of action dicts from the autonomy cycle artifact
        get_learning_entries_fn: Async callable to fetch learning entries
        get_missing_learning_tables_fn: Async callable to check for missing tables

    Returns:
        Tuple of (ranked_actions, ordering_source_string).
    """
    if not next_actions:
        return next_actions, "artifact"

    try:
        if await get_missing_learning_tables_fn(db):
            return next_actions, "artifact"

        ranked_actions: list[tuple[int, int, dict[str, Any]]] = []
        ordering_sources: set[str] = set()
        for index, action in enumerate(next_actions):
            learning_queries = build_developer_control_plane_learning_queries(
                source_lane_id=action.get("source_lane_id"),
                queue_job_id=action.get("job_id"),
                linked_mission_id=action.get("mission_id"),
                limit=3,
            )
            primary_match_mode = learning_queries[0][0] if learning_queries else "none"
            matched_entries: list[DeveloperControlPlaneLearningEntry] = []
            resolved_match_mode = "none"

            for match_mode, query in learning_queries:
                matched_entries = await get_learning_entries_fn(
                    db,
                    organization_id,
                    entry_type=None,
                    source_classification=None,
                    source_lane_id=query.get("source_lane_id"),
                    queue_job_id=query.get("queue_job_id"),
                    linked_mission_id=query.get("linked_mission_id"),
                    limit=query.get("limit", 3),
                )
                if matched_entries:
                    resolved_match_mode = match_mode
                    break

            score = score_developer_control_plane_autonomy_action(
                action_type=action.get("action", ""),
                priority=action.get("priority"),
                learning_entries=matched_entries,
                match_mode=resolved_match_mode,
                primary_match_mode=primary_match_mode,
            )
            if score > 0 and resolved_match_mode != "none":
                ordering_sources.add(
                    "canonical-learning-exact-runtime"
                    if resolved_match_mode == primary_match_mode
                    else "canonical-learning-fallback"
                )
            ranked_actions.append((score, index, action))

        if not any(score > 0 for score, _, _ in ranked_actions):
            return next_actions, "artifact"

        return (
            [
                action
                for _, _, action in sorted(
                    ranked_actions,
                    key=lambda item: (-item[0], item[1]),
                )
            ],
            (
                "canonical-learning-exact-runtime"
                if "canonical-learning-exact-runtime" in ordering_sources
                else "canonical-learning-fallback"
            ),
        )
    except Exception:
        return next_actions, "artifact"

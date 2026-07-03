"""Dispatch planner orchestrator for the Control Plane.

Coordinates queue loading, job selection, and dispatch decision making
for the autonomy cycle.  This module is part of the orchestration layer
and **may** use infrastructure imports (database, filesystem).

Extracted from ``backend/app/api/v2/developer_control_plane.py``.
Requirements: 10.2, 10.4, 10.5
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneAutonomyCycleActionableCompletionWriteResponse,
    DeveloperControlPlaneAutonomyCycleActionResponse,
    DeveloperControlPlaneAutonomyCycleBlockedJobResponse,
    DeveloperControlPlaneAutonomyCycleCloseoutCandidateResponse,
    DeveloperControlPlaneAutonomyCycleJobErrorResponse,
    DeveloperControlPlaneAutonomyCycleResponse,
    DeveloperControlPlaneAutonomyCycleSelectedJobResponse,
    DeveloperControlPlaneAutonomyCycleWatchdogResponse,
)
from app.models.developer_control_plane import DeveloperControlPlaneLearningEntry
from app.modules.ai.services.developer_control_plane_autonomy_cycle import (
    build_developer_control_plane_learning_queries,
    resolve_developer_control_plane_autonomy_cycle_path,
    score_developer_control_plane_autonomy_action,
)
from app.modules.ai.services.developer_control_plane_completion_write import (
    build_developer_control_plane_first_actionable_completion_write_payload,
)
from app.services.control_plane import telemetry_service

# ---------------------------------------------------------------------------
# Path resolution — mirrors the constants in developer_control_plane.py
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[5]
_AUTONOMY_CYCLE_PATH = resolve_developer_control_plane_autonomy_cycle_path(_REPO_ROOT)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _source_lane_id(item: dict[str, Any]) -> str | None:
    """Extract source lane ID from an autonomy cycle item dict."""
    source_lane_id = item.get("sourceLaneId")
    if isinstance(source_lane_id, str) and source_lane_id:
        return source_lane_id
    provenance = item.get("provenance")
    if isinstance(provenance, dict):
        val = provenance.get("sourceLaneId")
        if isinstance(val, str) and val:
            return val
    return None


def _str_or(item: dict[str, Any], key: str, default: str | None = None) -> str | None:
    """Return ``item[key]`` if it is a non-empty string, else *default*."""
    value = item.get(key)
    return value if isinstance(value, str) else default


def _int_or(item: dict[str, Any], key: str, default: int = 0) -> int:
    """Return ``item[key]`` if it is an int, else *default*."""
    value = item.get(key)
    return value if isinstance(value, int) else default


def _bool_or(item: dict[str, Any], key: str) -> bool | None:
    """Return ``item[key]`` if it is a bool, else ``None``."""
    value = item.get(key)
    return value if isinstance(value, bool) else None


# ---------------------------------------------------------------------------
# DispatchPlanner — orchestrator class
# ---------------------------------------------------------------------------


class DispatchPlanner:
    """Orchestrator for autonomy cycle dispatch decisions."""

    # ------------------------------------------------------------------
    # Autonomy cycle loading (filesystem)
    # ------------------------------------------------------------------

    @staticmethod
    def load_autonomy_cycle_payload() -> dict[str, Any] | None:
        """Load the autonomy cycle artifact from the filesystem."""
        return telemetry_service.load_autonomy_cycle_payload(_AUTONOMY_CYCLE_PATH)

    # ------------------------------------------------------------------

    @staticmethod
    def autonomy_cycle_response(
        payload: dict[str, Any] | None,
    ) -> DeveloperControlPlaneAutonomyCycleResponse:
        """Build the autonomy cycle API response from a raw payload."""
        artifact_path = (
            str(_AUTONOMY_CYCLE_PATH.relative_to(_REPO_ROOT))
            if _AUTONOMY_CYCLE_PATH.is_relative_to(_REPO_ROOT)
            else str(_AUTONOMY_CYCLE_PATH)
        )

        if payload is None:
            return DeveloperControlPlaneAutonomyCycleResponse(
                exists=False, artifact_path=artifact_path,
                next_action_ordering_source="artifact",
                watchdog=DeveloperControlPlaneAutonomyCycleWatchdogResponse(
                    exists=False, state_path="runtime-artifacts/watchdog-state.json",
                ),
            )

        # -- Watchdog --
        watchdog_payload = payload.get("watchdog") if isinstance(payload.get("watchdog"), dict) else {}
        normalized_job_errors: dict[str, DeveloperControlPlaneAutonomyCycleJobErrorResponse] = {}
        job_errors = watchdog_payload.get("jobErrors")
        if isinstance(job_errors, dict):
            for job_id, detail in job_errors.items():
                if isinstance(job_id, str) and isinstance(detail, dict):
                    normalized_job_errors[job_id] = DeveloperControlPlaneAutonomyCycleJobErrorResponse(
                        last_error=_str_or(detail, "lastError"),
                        consecutive_errors=(
                            detail.get("consecutiveErrors")
                            if isinstance(detail.get("consecutiveErrors"), int) else None
                        ),
                    )

        # -- Selected jobs --
        selected_jobs: list[DeveloperControlPlaneAutonomyCycleSelectedJobResponse] = []
        if isinstance(payload.get("selectedJobs"), list):
            for item in payload["selectedJobs"]:
                if isinstance(item, dict) and isinstance(item.get("jobId"), str):
                    selected_jobs.append(DeveloperControlPlaneAutonomyCycleSelectedJobResponse(
                        job_id=item["jobId"],
                        title=_str_or(item, "title", item["jobId"]) or item["jobId"],
                        source_lane_id=_source_lane_id(item),
                        priority=_str_or(item, "priority", "p3") or "p3",
                        primary_agent=_str_or(item, "primaryAgent", "Unknown") or "Unknown",
                        trigger_reason=_str_or(item, "triggerReason"),
                        source_task=_str_or(item, "sourceTask"),
                    ))

        # -- Blocked jobs --
        blocked_jobs: list[DeveloperControlPlaneAutonomyCycleBlockedJobResponse] = []
        if isinstance(payload.get("blockedJobs"), list):
            for item in payload["blockedJobs"]:
                if isinstance(item, dict) and isinstance(item.get("jobId"), str):
                    blocked_jobs.append(DeveloperControlPlaneAutonomyCycleBlockedJobResponse(
                        job_id=item["jobId"],
                        title=_str_or(item, "title", item["jobId"]) or item["jobId"],
                        source_lane_id=_source_lane_id(item),
                        reason=_str_or(item, "reason"),
                    ))

        # -- Closeout candidates --
        closeout_candidates: list[DeveloperControlPlaneAutonomyCycleCloseoutCandidateResponse] = []
        if isinstance(payload.get("closeoutCandidates"), list):
            for item in payload["closeoutCandidates"]:
                if isinstance(item, dict) and isinstance(item.get("jobId"), str):
                    closeout_candidates.append(
                        DeveloperControlPlaneAutonomyCycleCloseoutCandidateResponse(
                            job_id=item["jobId"],
                            title=_str_or(item, "title"),
                            source_lane_id=_source_lane_id(item),
                            queue_status=_str_or(item, "queueStatus"),
                            closeout_status=_str_or(item, "closeoutStatus"),
                            mission_id=_str_or(item, "missionId"),
                            verification_evidence_ref=_str_or(item, "verificationEvidenceRef"),
                            path=_str_or(item, "path"),
                        )
                    )

        # -- Next actions --
        next_actions: list[DeveloperControlPlaneAutonomyCycleActionResponse] = []
        if isinstance(payload.get("nextActions"), list):
            for item in payload["nextActions"]:
                if isinstance(item, dict) and isinstance(item.get("action"), str):
                    next_actions.append(DeveloperControlPlaneAutonomyCycleActionResponse(
                        action=item["action"],
                        job_id=_str_or(item, "jobId"),
                        title=_str_or(item, "title"),
                        source_lane_id=_source_lane_id(item),
                        reason=_str_or(item, "reason"),
                        primary_agent=_str_or(item, "primaryAgent"),
                        priority=_str_or(item, "priority"),
                        mission_id=_str_or(item, "missionId"),
                        receipt_path=_str_or(item, "receiptPath"),
                        state_path=_str_or(item, "statePath"),
                        detail=item.get("detail") if isinstance(item.get("detail"), dict) else None,
                    ))

        # -- Status counts --
        status_counts = payload.get("statusCounts") if isinstance(payload.get("statusCounts"), dict) else {}
        normalized_status_counts = {
            k: v for k, v in status_counts.items() if isinstance(k, str) and isinstance(v, int)
        }

        return DeveloperControlPlaneAutonomyCycleResponse(
            exists=True,
            artifact_path=artifact_path,
            generated_at=_str_or(payload, "generatedAt"),
            queue_path=_str_or(payload, "queuePath"),
            window=_str_or(payload, "window"),
            max_jobs_per_run=_int_or(payload, "maxJobsPerRun"),
            status_counts=normalized_status_counts,
            selected_job_count=_int_or(payload, "selectedJobCount"),
            blocked_job_count=_int_or(payload, "blockedJobCount"),
            closeout_candidate_count=_int_or(payload, "closeoutCandidateCount"),
            next_action_count=_int_or(payload, "nextActionCount"),
            next_action_ordering_source=_str_or(payload, "nextActionOrderingSource", "artifact") or "artifact",
            watchdog=DeveloperControlPlaneAutonomyCycleWatchdogResponse(
                exists=watchdog_payload.get("exists") is True,
                state_path=_str_or(watchdog_payload, "statePath", "runtime-artifacts/watchdog-state.json") or "runtime-artifacts/watchdog-state.json",
                last_check=_str_or(watchdog_payload, "lastCheck"),
                gateway_healthy=_bool_or(watchdog_payload, "gatewayHealthy"),
                state_is_stale=watchdog_payload.get("stateIsStale") is True,
                total_alerts=_int_or(watchdog_payload, "totalAlerts"),
                job_errors=normalized_job_errors,
            ),
            selected_jobs=selected_jobs,
            blocked_jobs=blocked_jobs,
            closeout_candidates=closeout_candidates,
            next_actions=next_actions,
        )

    # ------------------------------------------------------------------
    # Memory-biased next action ordering
    # ------------------------------------------------------------------

    @staticmethod
    async def memory_biased_autonomy_cycle_next_actions(
        db: AsyncSession,
        organization_id: int,
        next_actions: list[DeveloperControlPlaneAutonomyCycleActionResponse],
    ) -> tuple[list[DeveloperControlPlaneAutonomyCycleActionResponse], str]:
        """Re-rank autonomy cycle next actions using learning ledger data.

        Returns ``(ranked_actions, ordering_source)``.
        """
        if not next_actions:
            return next_actions, "artifact"

        try:
            # Lazy imports — these helpers still live in developer_control_plane.py
            # and will be fully extracted in a later task.
            from app.api.bijmantra.developer.developer_control_plane import (
                _get_learning_entries,
                _get_missing_learning_tables,
            )

            if await _get_missing_learning_tables(db):
                return next_actions, "artifact"

            ranked_actions: list[tuple[int, int, DeveloperControlPlaneAutonomyCycleActionResponse]] = []
            ordering_sources: set[str] = set()
            for index, action in enumerate(next_actions):
                learning_queries = build_developer_control_plane_learning_queries(
                    source_lane_id=action.source_lane_id,
                    queue_job_id=action.job_id,
                    linked_mission_id=action.mission_id,
                    limit=3,
                )
                primary_match_mode = learning_queries[0][0] if learning_queries else "none"
                matched_entries: list[DeveloperControlPlaneLearningEntry] = []
                resolved_match_mode = "none"

                for match_mode, query in learning_queries:
                    matched_entries = await _get_learning_entries(
                        db, organization_id,
                        entry_type=None, source_classification=None,
                        source_lane_id=query.get("source_lane_id"),
                        queue_job_id=query.get("queue_job_id"),
                        linked_mission_id=query.get("linked_mission_id"),
                        limit=query.get("limit", 3),
                    )
                    if matched_entries:
                        resolved_match_mode = match_mode
                        break

                score = score_developer_control_plane_autonomy_action(
                    action_type=action.action,
                    priority=action.priority,
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
                [action for _, _, action in sorted(ranked_actions, key=lambda t: (-t[0], t[1]))],
                (
                    "canonical-learning-exact-runtime"
                    if "canonical-learning-exact-runtime" in ordering_sources
                    else "canonical-learning-fallback"
                ),
            )
        except Exception:
            return next_actions, "artifact"

    # ------------------------------------------------------------------
    # Completion write preparation hydration
    # ------------------------------------------------------------------

    @staticmethod
    async def hydrate_autonomy_cycle_completion_write_preparations(
        db: AsyncSession,
        organization_id: int,
        next_actions: list[DeveloperControlPlaneAutonomyCycleActionResponse],
    ) -> list[DeveloperControlPlaneAutonomyCycleActionResponse]:
        """Hydrate ``prepare-completion-write-back`` actions with preparation data."""
        if not next_actions:
            return next_actions

        # Lazy imports — these helpers still live in developer_control_plane.py
        # and will be fully extracted in a later task.
        from app.api.bijmantra.developer.developer_control_plane import (
            _build_completion_write_preparation_response,
            _find_board_lane,
            _get_active_board,
            _load_active_board_payload,
        )

        current_record = await _get_active_board(db, organization_id)
        if current_record is None:
            return next_actions

        try:
            board_payload = _load_active_board_payload(current_record)
        except HTTPException:
            return next_actions

        hydrated_actions: list[DeveloperControlPlaneAutonomyCycleActionResponse] = []
        for action in next_actions:
            if action.action != "prepare-completion-write-back" or not action.source_lane_id:
                hydrated_actions.append(action)
                continue

            if _find_board_lane(board_payload, action.source_lane_id) is None:
                hydrated_actions.append(action)
                continue

            try:
                preparation = _build_completion_write_preparation_response(
                    source_lane_id=action.source_lane_id,
                    source_board_concurrency_token=current_record.canonical_board_hash,
                )
            except HTTPException:
                hydrated_actions.append(action)
                continue

            detail = dict(action.detail or {})
            detail["completionWritePreparation"] = preparation.model_dump()
            hydrated_actions.append(action.model_copy(update={"detail": detail}))

        return hydrated_actions

    # ------------------------------------------------------------------
    # First actionable completion write resolution
    # ------------------------------------------------------------------

    @staticmethod
    def resolve_first_actionable_completion_write(
        next_actions: list[DeveloperControlPlaneAutonomyCycleActionResponse],
    ) -> DeveloperControlPlaneAutonomyCycleActionableCompletionWriteResponse | None:
        """Find the first actionable completion write among *next_actions*."""
        payload = build_developer_control_plane_first_actionable_completion_write_payload(next_actions)
        if payload is None:
            return None

        try:
            return DeveloperControlPlaneAutonomyCycleActionableCompletionWriteResponse.model_validate(payload)
        except ValidationError:
            return None

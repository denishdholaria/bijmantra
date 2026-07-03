"""Closeout writer orchestrator for the Control Plane.

Coordinates closeout receipt production, watchdog state loading, completion
assist, and silent monitor operations.  This module is part of the
orchestration layer and **may** use infrastructure imports (filesystem,
subprocess, telemetry service).

Extracted from ``backend/app/api/v2/developer_control_plane.py``.
Requirements: 10.3, 10.4, 10.5
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneOvernightQueueStatusResponse,
    DeveloperControlPlaneRuntimeCompletionAssistResponse,
    DeveloperControlPlaneSilentMonitorEvidenceSourceResponse,
    DeveloperControlPlaneSilentMonitorResponse,
    DeveloperControlPlaneWatchdogStatusResponse,
)
from app.modules.ai.services.claw_runtime_surface import (
    resolve_runtime_mission_evidence_dir,
    resolve_runtime_watchdog_state_path,
)
from app.modules.ai.services.developer_control_plane_completion_assist import (
    resolve_developer_control_plane_completion_assist_path,
)
from app.services.control_plane import telemetry_service

# ---------------------------------------------------------------------------
# Path resolution — mirrors the constants in developer_control_plane.py
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[5]
_MISSION_EVIDENCE_DIR = resolve_runtime_mission_evidence_dir(_REPO_ROOT)
_WATCHDOG_STATE_PATH = resolve_runtime_watchdog_state_path(_REPO_ROOT)
_COMPLETION_ASSIST_PATH = resolve_developer_control_plane_completion_assist_path(
    _REPO_ROOT,
)
_CONTROL_SURFACE_CHECK_SCRIPT = _REPO_ROOT / "scripts" / "check_control_surfaces.py"
_REEVU_REAL_QUESTION_REPORT_PATH = (
    _REPO_ROOT / "backend" / "test_reports" / "reevu_real_question_local.json"
)
_REEVU_READINESS_CENSUS_PATH = (
    _REPO_ROOT / "backend" / "test_reports" / "reevu_local_readiness_census.json"
)
_REEVU_AUTHORITY_GAP_REPORT_PATH = (
    _REPO_ROOT / "backend" / "test_reports" / "reevu_authority_gap_report.json"
)

_QUEUE_STALENESS_WATCH_HOURS = 18
_QUEUE_STALENESS_ALERT_HOURS = 36
_SILENT_MONITOR_OUTPUT_ARTIFACT_PREFIX = (
    "developer-control-plane.runtime.silent-monitors"
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _relative_repo_path(path: Path) -> str:
    """Return *path* relative to the repo root, or the absolute string."""
    try:
        return str(path.relative_to(_REPO_ROOT))
    except ValueError:
        return str(path)


def _parse_monitor_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp, returning ``None`` on failure."""
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


def _trim_monitor_detail(value: str | None, limit: int = 280) -> str | None:
    """Trim a monitor detail string to *limit* characters."""
    if value is None:
        return None

    normalized = " ".join(value.split())
    if not normalized:
        return None

    if len(normalized) <= limit:
        return normalized

    return f"{normalized[: limit - 3].rstrip()}..."


def _string_list(value: Any) -> list[str]:
    """Return a list of strings from *value*, or an empty list."""
    if not isinstance(value, list):
        return []

    return [item for item in value if isinstance(item, str)]


def _load_optional_json_object(
    path: Path,
) -> tuple[dict[str, Any] | None, str | None]:
    """Load a JSON object from *path*, returning ``(payload, error)``."""
    if not path.exists():
        return None, None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"Unable to read {_relative_repo_path(path)}: {exc}"

    if not isinstance(payload, dict):
        return None, f"{_relative_repo_path(path)} must be a JSON object"

    return payload, None


def _build_silent_monitor_response(
    *,
    monitor_key: str,
    label: str,
    state: str,
    summary: str,
    detail: str | None,
    observed_at: str | None,
    refresh_cadence: str,
    evidence_sources: list[DeveloperControlPlaneSilentMonitorEvidenceSourceResponse],
    findings: list[str],
) -> DeveloperControlPlaneSilentMonitorResponse:
    """Build a ``DeveloperControlPlaneSilentMonitorResponse``."""
    return DeveloperControlPlaneSilentMonitorResponse(
        monitor_key=monitor_key,
        label=label,
        state=state,
        should_emit=state != "healthy",
        summary=summary,
        detail=detail,
        observed_at=observed_at,
        refresh_cadence=refresh_cadence,
        output_artifact=f"{_SILENT_MONITOR_OUTPUT_ARTIFACT_PREFIX}.{monitor_key}",
        mutates_authority_surfaces=False,
        evidence_sources=evidence_sources,
        findings=findings,
    )


# ---------------------------------------------------------------------------
# CloseoutWriter — orchestrator class
# ---------------------------------------------------------------------------


class CloseoutWriter:
    """Orchestrator for closeout production, watchdog, and silent monitors.

    All methods are intentionally ``@staticmethod`` so that the class acts
    as a namespace grouping related closeout and monitoring operations.
    Infrastructure dependencies (filesystem paths, subprocess) are resolved
    at module level.
    """

    # ------------------------------------------------------------------
    # Watchdog state (filesystem)
    # ------------------------------------------------------------------

    @staticmethod
    def load_watchdog_state_payload() -> dict[str, Any] | None:
        """Load the watchdog state from the filesystem."""
        return telemetry_service.load_watchdog_state_payload(_WATCHDOG_STATE_PATH)

    @staticmethod
    def watchdog_status_response(
        watchdog_state: dict[str, Any] | None,
    ) -> DeveloperControlPlaneWatchdogStatusResponse:
        """Build the watchdog status API response from raw state."""
        response_dict = telemetry_service.build_watchdog_status_response(
            watchdog_state,
            _WATCHDOG_STATE_PATH,
            _MISSION_EVIDENCE_DIR,
            _REPO_ROOT,
        )
        return DeveloperControlPlaneWatchdogStatusResponse(**response_dict)

    # ------------------------------------------------------------------
    # Completion assist (filesystem)
    # ------------------------------------------------------------------

    @staticmethod
    def load_completion_assist_payload() -> dict[str, Any] | None:
        """Load the completion assist artifact from the filesystem."""
        return telemetry_service.load_completion_assist_payload(
            _COMPLETION_ASSIST_PATH,
        )

    @staticmethod
    def completion_assist_response(
        payload: dict[str, Any] | None,
    ) -> DeveloperControlPlaneRuntimeCompletionAssistResponse:
        """Build the completion assist API response from a raw payload."""
        response_dict = telemetry_service.build_completion_assist_response(
            payload,
            _COMPLETION_ASSIST_PATH,
            _REPO_ROOT,
        )
        return DeveloperControlPlaneRuntimeCompletionAssistResponse(**response_dict)

    # ------------------------------------------------------------------
    # Silent monitors
    # ------------------------------------------------------------------

    @staticmethod
    def queue_staleness_monitor(
        queue_status: DeveloperControlPlaneOvernightQueueStatusResponse,
    ) -> DeveloperControlPlaneSilentMonitorResponse:
        """Check queue staleness and return a silent monitor response."""
        evidence_sources = [
            DeveloperControlPlaneSilentMonitorEvidenceSourceResponse(
                label="Overnight queue status",
                path=queue_status.queue_path,
                observed_at=queue_status.updated_at,
            )
        ]

        if not queue_status.exists:
            return _build_silent_monitor_response(
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

        if not queue_status.updated_at:
            return _build_silent_monitor_response(
                monitor_key="queue-staleness",
                label="Queue staleness",
                state="watch",
                summary="The overnight queue exists but does not advertise an updatedAt timestamp.",
                detail=f"Queue hash {queue_status.queue_sha256}; sampled job count {queue_status.job_count}.",
                observed_at=None,
                refresh_cadence="Nightly and immediately after each reviewed queue export",
                evidence_sources=evidence_sources,
                findings=["overnight-queue.updated-at-missing"],
            )

        updated_at = _parse_monitor_timestamp(queue_status.updated_at)
        if updated_at is None:
            return _build_silent_monitor_response(
                monitor_key="queue-staleness",
                label="Queue staleness",
                state="watch",
                summary="The overnight queue timestamp is present but could not be parsed.",
                detail=f"Queue hash {queue_status.queue_sha256}; raw updatedAt value {queue_status.updated_at!r}.",
                observed_at=queue_status.updated_at,
                refresh_cadence="Nightly and immediately after each reviewed queue export",
                evidence_sources=evidence_sources,
                findings=["overnight-queue.updated-at-invalid"],
            )

        age_seconds = max(0.0, (datetime.now(UTC) - updated_at).total_seconds())
        age_hours = age_seconds / 3600
        detail = (
            f"Queue hash {queue_status.queue_sha256}; {queue_status.job_count} sampled jobs; "
            f"age {age_hours:.1f}h."
        )

        if age_hours >= _QUEUE_STALENESS_ALERT_HOURS:
            return _build_silent_monitor_response(
                monitor_key="queue-staleness",
                label="Queue staleness",
                state="alert",
                summary="The overnight queue snapshot is older than the nightly freshness window.",
                detail=detail,
                observed_at=queue_status.updated_at,
                refresh_cadence="Nightly and immediately after each reviewed queue export",
                evidence_sources=evidence_sources,
                findings=[f"overnight-queue.age-hours>={_QUEUE_STALENESS_ALERT_HOURS}"],
            )

        if age_hours >= _QUEUE_STALENESS_WATCH_HOURS:
            return _build_silent_monitor_response(
                monitor_key="queue-staleness",
                label="Queue staleness",
                state="watch",
                summary="The overnight queue snapshot is aging toward staleness.",
                detail=detail,
                observed_at=queue_status.updated_at,
                refresh_cadence="Nightly and immediately after each reviewed queue export",
                evidence_sources=evidence_sources,
                findings=[f"overnight-queue.age-hours>={_QUEUE_STALENESS_WATCH_HOURS}"],
            )

        return _build_silent_monitor_response(
            monitor_key="queue-staleness",
            label="Queue staleness",
            state="healthy",
            summary="The overnight queue snapshot looks fresh for the current nightly cadence.",
            detail=detail,
            observed_at=queue_status.updated_at,
            refresh_cadence="Nightly and immediately after each reviewed queue export",
            evidence_sources=evidence_sources,
            findings=[],
        )

    @staticmethod
    def control_surface_drift_monitor() -> DeveloperControlPlaneSilentMonitorResponse:
        """Check control surface drift and return a silent monitor response."""
        observed_at = datetime.now(UTC).isoformat()
        evidence_sources = [
            DeveloperControlPlaneSilentMonitorEvidenceSourceResponse(
                label="Canonical control-surface checker",
                path=_relative_repo_path(_CONTROL_SURFACE_CHECK_SCRIPT),
                observed_at=observed_at,
            )
        ]

        if not _CONTROL_SURFACE_CHECK_SCRIPT.exists():
            return _build_silent_monitor_response(
                monitor_key="control-surface-drift",
                label="Control-surface drift",
                state="missing",
                summary="The canonical control-surface checker is missing.",
                detail=f"Expected script {_relative_repo_path(_CONTROL_SURFACE_CHECK_SCRIPT)} could not be found.",
                observed_at=observed_at,
                refresh_cadence="Before operator handoff and after control-plane contract changes",
                evidence_sources=evidence_sources,
                findings=["control-surfaces.check-script-missing"],
            )

        try:
            completed = subprocess.run(
                [sys.executable, str(_CONTROL_SURFACE_CHECK_SCRIPT)],
                cwd=str(_REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return _build_silent_monitor_response(
                monitor_key="control-surface-drift",
                label="Control-surface drift",
                state="alert",
                summary="The control-surface checker timed out.",
                detail=_trim_monitor_detail(str(exc)),
                observed_at=observed_at,
                refresh_cadence="Before operator handoff and after control-plane contract changes",
                evidence_sources=evidence_sources,
                findings=["control-surfaces.check-timeout"],
            )
        except OSError as exc:
            return _build_silent_monitor_response(
                monitor_key="control-surface-drift",
                label="Control-surface drift",
                state="alert",
                summary="The control-surface checker could not be executed.",
                detail=_trim_monitor_detail(str(exc)),
                observed_at=observed_at,
                refresh_cadence="Before operator handoff and after control-plane contract changes",
                evidence_sources=evidence_sources,
                findings=["control-surfaces.check-execution-failed"],
            )

        command_output = _trim_monitor_detail(completed.stderr or completed.stdout)
        if completed.returncode == 0:
            return _build_silent_monitor_response(
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

        return _build_silent_monitor_response(
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

    @staticmethod
    def reevu_readiness_monitor() -> DeveloperControlPlaneSilentMonitorResponse:
        """Check REEVU readiness and return a silent monitor response."""
        real_question_report, real_question_error = _load_optional_json_object(
            _REEVU_REAL_QUESTION_REPORT_PATH
        )
        readiness_census, readiness_census_error = _load_optional_json_object(
            _REEVU_READINESS_CENSUS_PATH
        )
        authority_gap_report, authority_gap_error = _load_optional_json_object(
            _REEVU_AUTHORITY_GAP_REPORT_PATH
        )

        evidence_sources: list[DeveloperControlPlaneSilentMonitorEvidenceSourceResponse] = []
        for label, path, payload in (
            ("REEVU real-question benchmark", _REEVU_REAL_QUESTION_REPORT_PATH, real_question_report),
            ("REEVU local readiness census", _REEVU_READINESS_CENSUS_PATH, readiness_census),
            ("REEVU authority gap report", _REEVU_AUTHORITY_GAP_REPORT_PATH, authority_gap_report),
        ):
            evidence_sources.append(
                DeveloperControlPlaneSilentMonitorEvidenceSourceResponse(
                    label=label,
                    path=_relative_repo_path(path),
                    observed_at=payload.get("generated_at") if isinstance(payload, dict) else None,
                )
            )

        missing_artifacts = [
            _relative_repo_path(path)
            for path, payload, error in (
                (_REEVU_REAL_QUESTION_REPORT_PATH, real_question_report, real_question_error),
                (_REEVU_READINESS_CENSUS_PATH, readiness_census, readiness_census_error),
                (_REEVU_AUTHORITY_GAP_REPORT_PATH, authority_gap_report, authority_gap_error),
            )
            if payload is None and error is None
        ]
        artifact_errors = [
            error
            for error in (real_question_error, readiness_census_error, authority_gap_error)
            if error is not None
        ]

        if missing_artifacts:
            return _build_silent_monitor_response(
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
            return _build_silent_monitor_response(
                monitor_key="reevu-readiness",
                label="REEVU readiness",
                state="alert",
                summary="One or more REEVU readiness artifacts could not be read.",
                detail=_trim_monitor_detail("; ".join(artifact_errors)),
                observed_at=None,
                refresh_cadence="After REEVU readiness census, benchmark, or authority-gap regeneration",
                evidence_sources=evidence_sources,
                findings=["reevu.readiness-artifact-read-failed"],
            )

        runtime_status = (
            real_question_report.get("runtime_status")
            if isinstance(real_question_report.get("runtime_status"), str)
            else None
        )
        passed_cases = (
            real_question_report.get("passed_cases")
            if isinstance(real_question_report.get("passed_cases"), int)
            else None
        )
        total_cases = (
            real_question_report.get("total_cases")
            if isinstance(real_question_report.get("total_cases"), int)
            else None
        )
        pass_rate = (
            float(real_question_report.get("pass_rate"))
            if isinstance(real_question_report.get("pass_rate"), (int, float))
            else None
        )
        benchmark_ready_org_ids = _string_list(readiness_census.get("benchmark_ready_organization_ids"))
        if not benchmark_ready_org_ids and isinstance(
            readiness_census.get("benchmark_ready_organization_ids"), list
        ):
            benchmark_ready_org_ids = [
                str(item) for item in readiness_census.get("benchmark_ready_organization_ids") if isinstance(item, int)
            ]
        overall_gap_status = (
            authority_gap_report.get("overall_gap_status")
            if isinstance(authority_gap_report.get("overall_gap_status"), str)
            else None
        )
        blockers = _string_list(authority_gap_report.get("selected_local_org_blockers"))
        if not blockers:
            blockers = _string_list(authority_gap_report.get("common_blockers_across_blocked_orgs"))

        observed_candidates = [
            payload.get("generated_at")
            for payload in (real_question_report, readiness_census, authority_gap_report)
            if isinstance(payload.get("generated_at"), str)
        ]
        observed_at = max(observed_candidates, default=None)
        benchmark_ready_count = len(benchmark_ready_org_ids)
        ready_local_orgs = [
            organization
            for organization in readiness_census.get("organizations", [])
            if isinstance(organization, dict)
            and organization.get("runtime_status") == "ready"
            and isinstance(organization.get("organization_id"), int)
        ]
        least_blocked_local_organization = (
            readiness_census.get("least_blocked_local_organization")
            if isinstance(readiness_census.get("least_blocked_local_organization"), dict)
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
            least_blocked_blockers = _string_list(
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
            return _build_silent_monitor_response(
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

        return _build_silent_monitor_response(
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

    # ------------------------------------------------------------------
    # Overall state derivation
    # ------------------------------------------------------------------

    @staticmethod
    def derive_silent_monitor_overall_state(
        monitors: list[DeveloperControlPlaneSilentMonitorResponse],
    ) -> str:
        """Derive the overall state from a list of silent monitor responses."""
        state_priority = {
            "alert": 4,
            "missing": 3,
            "watch": 2,
            "healthy": 1,
        }
        highest_state = "healthy"
        highest_priority = 0
        for monitor in monitors:
            priority = state_priority.get(monitor.state, 0)
            if priority > highest_priority:
                highest_priority = priority
                highest_state = monitor.state

        return highest_state

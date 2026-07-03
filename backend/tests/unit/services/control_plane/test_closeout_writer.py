"""
Unit tests for Control Plane closeout writer orchestrator.

Tests watchdog state loading, completion assist, silent monitor functions,
overall state derivation, and internal helper functions in
``app.control_plane.orchestration.closeout_writer``.

**Validates: Requirements 10.3, 7.3**
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneOvernightQueueStatusResponse,
    DeveloperControlPlaneRuntimeCompletionAssistResponse,
    DeveloperControlPlaneSilentMonitorResponse,
    DeveloperControlPlaneWatchdogStatusResponse,
)
from app.control_plane.orchestration.closeout_writer import (
    CloseoutWriter,
    _parse_monitor_timestamp,
    _string_list,
    _trim_monitor_detail,
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


class TestParseMonitorTimestamp:
    """Tests for _parse_monitor_timestamp helper."""

    def test_returns_none_for_none(self):
        assert _parse_monitor_timestamp(None) is None

    def test_returns_none_for_empty_string(self):
        assert _parse_monitor_timestamp("") is None

    def test_parses_iso_with_z_suffix(self):
        result = _parse_monitor_timestamp("2026-04-15T10:00:00Z")
        assert result is not None
        assert result.tzinfo is not None
        assert result.year == 2026
        assert result.month == 4
        assert result.day == 15

    def test_parses_iso_with_offset(self):
        result = _parse_monitor_timestamp("2026-04-15T10:00:00+05:30")
        assert result is not None
        assert result.tzinfo is not None

    def test_naive_timestamp_gets_utc(self):
        result = _parse_monitor_timestamp("2026-04-15T10:00:00")
        assert result is not None
        assert result.tzinfo == UTC

    def test_returns_none_for_invalid_string(self):
        assert _parse_monitor_timestamp("not-a-timestamp") is None

    def test_result_is_utc(self):
        result = _parse_monitor_timestamp("2026-04-15T10:00:00+02:00")
        assert result is not None
        assert result.utcoffset() == timedelta(0)


class TestTrimMonitorDetail:
    """Tests for _trim_monitor_detail helper."""

    def test_returns_none_for_none(self):
        assert _trim_monitor_detail(None) is None

    def test_returns_none_for_whitespace_only(self):
        assert _trim_monitor_detail("   ") is None

    def test_returns_short_string_unchanged(self):
        assert _trim_monitor_detail("hello world") == "hello world"

    def test_normalizes_whitespace(self):
        assert _trim_monitor_detail("hello   world\n\tfoo") == "hello world foo"

    def test_trims_long_string(self):
        long_text = "a" * 300
        result = _trim_monitor_detail(long_text)
        assert result is not None
        assert len(result) <= 280
        assert result.endswith("...")

    def test_custom_limit(self):
        result = _trim_monitor_detail("a" * 50, limit=20)
        assert result is not None
        assert len(result) <= 20
        assert result.endswith("...")


class TestStringList:
    """Tests for _string_list helper."""

    def test_returns_empty_for_non_list(self):
        assert _string_list("not-a-list") == []
        assert _string_list(42) == []
        assert _string_list(None) == []

    def test_filters_non_strings(self):
        assert _string_list(["a", 1, "b", None, "c"]) == ["a", "b", "c"]

    def test_returns_all_strings(self):
        assert _string_list(["x", "y", "z"]) == ["x", "y", "z"]

    def test_returns_empty_for_empty_list(self):
        assert _string_list([]) == []


# ---------------------------------------------------------------------------
# load_watchdog_state_payload
# ---------------------------------------------------------------------------


class TestLoadWatchdogStatePayload:
    """Tests for CloseoutWriter.load_watchdog_state_payload."""

    @patch("app.control_plane.orchestration.closeout_writer.telemetry_service")
    def test_delegates_to_telemetry_service(self, mock_telemetry):
        expected = {"lastCheck": "2026-04-15T10:00:00Z", "jobs": []}
        mock_telemetry.load_watchdog_state_payload.return_value = expected

        result = CloseoutWriter.load_watchdog_state_payload()

        assert result == expected
        mock_telemetry.load_watchdog_state_payload.assert_called_once()

    @patch("app.control_plane.orchestration.closeout_writer.telemetry_service")
    def test_returns_none_when_telemetry_returns_none(self, mock_telemetry):
        mock_telemetry.load_watchdog_state_payload.return_value = None

        result = CloseoutWriter.load_watchdog_state_payload()

        assert result is None


# ---------------------------------------------------------------------------
# watchdog_status_response
# ---------------------------------------------------------------------------


class TestWatchdogStatusResponse:
    """Tests for CloseoutWriter.watchdog_status_response."""

    @patch("app.control_plane.orchestration.closeout_writer.telemetry_service")
    def test_builds_response_from_state(self, mock_telemetry):
        mock_telemetry.build_watchdog_status_response.return_value = {
            "exists": True,
            "state_path": "runtime-artifacts/watchdog-state.json",
            "auth_store_exists": True,
            "auth_store_path": "runtime-artifacts/agents/main/agent/auth-profiles.json",
            "bootstrap_ready": True,
            "bootstrap_status": "ready",
            "mission_evidence_dir_exists": True,
            "mission_evidence_dir_path": "runtime-artifacts/mission-evidence",
            "last_check": "2026-04-15T10:00:00Z",
            "state_age_seconds": 60,
            "state_is_stale": False,
            "gateway_healthy": True,
            "total_checks": 10,
            "total_alerts": 0,
            "job_count": 1,
            "jobs": [],
            "completion_assist_advisory": None,
        }

        result = CloseoutWriter.watchdog_status_response({"some": "state"})

        assert isinstance(result, DeveloperControlPlaneWatchdogStatusResponse)
        assert result.exists is True
        assert result.bootstrap_ready is True
        mock_telemetry.build_watchdog_status_response.assert_called_once()

    @patch("app.control_plane.orchestration.closeout_writer.telemetry_service")
    def test_builds_response_from_none_state(self, mock_telemetry):
        mock_telemetry.build_watchdog_status_response.return_value = {
            "exists": False,
            "state_path": "runtime-artifacts/watchdog-state.json",
            "auth_store_exists": False,
            "auth_store_path": "runtime-artifacts/agents/main/agent/auth-profiles.json",
            "bootstrap_ready": False,
            "bootstrap_status": "auth-store-missing",
            "mission_evidence_dir_exists": False,
            "mission_evidence_dir_path": "runtime-artifacts/mission-evidence",
            "completion_assist_advisory": None,
        }

        result = CloseoutWriter.watchdog_status_response(None)

        assert isinstance(result, DeveloperControlPlaneWatchdogStatusResponse)
        assert result.exists is False


# ---------------------------------------------------------------------------
# load_completion_assist_payload
# ---------------------------------------------------------------------------


class TestLoadCompletionAssistPayload:
    """Tests for CloseoutWriter.load_completion_assist_payload."""

    @patch("app.control_plane.orchestration.closeout_writer.telemetry_service")
    def test_delegates_to_telemetry_service(self, mock_telemetry):
        expected = {"status": "ready", "staged": True}
        mock_telemetry.load_completion_assist_payload.return_value = expected

        result = CloseoutWriter.load_completion_assist_payload()

        assert result == expected
        mock_telemetry.load_completion_assist_payload.assert_called_once()

    @patch("app.control_plane.orchestration.closeout_writer.telemetry_service")
    def test_returns_none_when_telemetry_returns_none(self, mock_telemetry):
        mock_telemetry.load_completion_assist_payload.return_value = None

        result = CloseoutWriter.load_completion_assist_payload()

        assert result is None


# ---------------------------------------------------------------------------
# completion_assist_response
# ---------------------------------------------------------------------------


class TestCompletionAssistResponse:
    """Tests for CloseoutWriter.completion_assist_response."""

    @patch("app.control_plane.orchestration.closeout_writer.telemetry_service")
    def test_builds_response_from_payload(self, mock_telemetry):
        mock_telemetry.build_completion_assist_response.return_value = {
            "exists": True,
            "artifact_path": "runtime-artifacts/completion-assist.json",
            "generated_at": "2026-04-15T10:00:00Z",
            "status": "ready",
            "staged": True,
            "explicit_write_required": True,
            "message": "Completion assist ready",
            "source": None,
            "actionable_completion_write": None,
        }

        result = CloseoutWriter.completion_assist_response({"status": "ready"})

        assert isinstance(result, DeveloperControlPlaneRuntimeCompletionAssistResponse)
        assert result.exists is True
        assert result.status == "ready"
        mock_telemetry.build_completion_assist_response.assert_called_once()

    @patch("app.control_plane.orchestration.closeout_writer.telemetry_service")
    def test_builds_response_from_none_payload(self, mock_telemetry):
        mock_telemetry.build_completion_assist_response.return_value = {
            "exists": False,
            "artifact_path": "runtime-artifacts/completion-assist.json",
        }

        result = CloseoutWriter.completion_assist_response(None)

        assert isinstance(result, DeveloperControlPlaneRuntimeCompletionAssistResponse)
        assert result.exists is False


# ---------------------------------------------------------------------------
# queue_staleness_monitor
# ---------------------------------------------------------------------------


class TestQueueStalenessMonitor:
    """Tests for CloseoutWriter.queue_staleness_monitor."""

    def _make_queue_status(self, **overrides) -> DeveloperControlPlaneOvernightQueueStatusResponse:
        defaults = {
            "queue_path": ".agent/jobs/overnight-queue.json",
            "queue_sha256": "abc123",
            "exists": True,
            "job_count": 3,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        defaults.update(overrides)
        return DeveloperControlPlaneOvernightQueueStatusResponse(**defaults)

    def test_healthy_when_fresh(self):
        """Queue updated recently should be healthy."""
        status = self._make_queue_status(
            updated_at=datetime.now(UTC).isoformat(),
        )
        result = CloseoutWriter.queue_staleness_monitor(status)

        assert isinstance(result, DeveloperControlPlaneSilentMonitorResponse)
        assert result.state == "healthy"
        assert result.monitor_key == "queue-staleness"
        assert result.should_emit is False
        assert result.findings == []

    def test_watch_when_aging(self):
        """Queue older than 18h but under 36h should be 'watch'."""
        aged = datetime.now(UTC) - timedelta(hours=20)
        status = self._make_queue_status(updated_at=aged.isoformat())

        result = CloseoutWriter.queue_staleness_monitor(status)

        assert result.state == "watch"
        assert result.should_emit is True
        assert any("age-hours>=18" in f for f in result.findings)

    def test_alert_when_stale(self):
        """Queue older than 36h should be 'alert'."""
        stale = datetime.now(UTC) - timedelta(hours=40)
        status = self._make_queue_status(updated_at=stale.isoformat())

        result = CloseoutWriter.queue_staleness_monitor(status)

        assert result.state == "alert"
        assert result.should_emit is True
        assert any("age-hours>=36" in f for f in result.findings)

    def test_alert_when_missing(self):
        """Queue file missing should be 'alert'."""
        status = self._make_queue_status(exists=False)

        result = CloseoutWriter.queue_staleness_monitor(status)

        assert result.state == "alert"
        assert result.should_emit is True
        assert "overnight-queue.missing" in result.findings

    def test_watch_when_updated_at_missing(self):
        """Queue exists but no updated_at should be 'watch'."""
        status = self._make_queue_status(updated_at=None)

        result = CloseoutWriter.queue_staleness_monitor(status)

        assert result.state == "watch"
        assert "overnight-queue.updated-at-missing" in result.findings

    def test_watch_when_updated_at_unparseable(self):
        """Queue with unparseable updated_at should be 'watch'."""
        status = self._make_queue_status(updated_at="not-a-date")

        result = CloseoutWriter.queue_staleness_monitor(status)

        assert result.state == "watch"
        assert "overnight-queue.updated-at-invalid" in result.findings

    def test_evidence_sources_populated(self):
        """Evidence sources should always be populated."""
        status = self._make_queue_status()
        result = CloseoutWriter.queue_staleness_monitor(status)

        assert len(result.evidence_sources) == 1
        assert result.evidence_sources[0].label == "Overnight queue status"


# ---------------------------------------------------------------------------
# control_surface_drift_monitor
# ---------------------------------------------------------------------------


class TestControlSurfaceDriftMonitor:
    """Tests for CloseoutWriter.control_surface_drift_monitor."""

    @patch("app.control_plane.orchestration.closeout_writer._CONTROL_SURFACE_CHECK_SCRIPT")
    @patch("app.control_plane.orchestration.closeout_writer.subprocess")
    def test_healthy_when_script_passes(self, mock_subprocess, mock_script_path):
        mock_script_path.exists.return_value = True
        mock_subprocess.run.return_value = type("Result", (), {
            "returncode": 0,
            "stdout": "All checks passed",
            "stderr": "",
        })()
        mock_subprocess.TimeoutExpired = TimeoutError

        result = CloseoutWriter.control_surface_drift_monitor()

        assert isinstance(result, DeveloperControlPlaneSilentMonitorResponse)
        assert result.state == "healthy"
        assert result.monitor_key == "control-surface-drift"
        assert result.findings == []

    @patch("app.control_plane.orchestration.closeout_writer._CONTROL_SURFACE_CHECK_SCRIPT")
    @patch("app.control_plane.orchestration.closeout_writer.subprocess")
    def test_alert_when_script_fails(self, mock_subprocess, mock_script_path):
        mock_script_path.exists.return_value = True
        mock_subprocess.run.return_value = type("Result", (), {
            "returncode": 1,
            "stdout": "",
            "stderr": "Drift detected in 2 surfaces",
        })()
        mock_subprocess.TimeoutExpired = TimeoutError

        result = CloseoutWriter.control_surface_drift_monitor()

        assert result.state == "alert"
        assert result.should_emit is True
        assert "control-surfaces.drift-detected" in result.findings

    @patch("app.control_plane.orchestration.closeout_writer._CONTROL_SURFACE_CHECK_SCRIPT")
    def test_missing_when_script_absent(self, mock_script_path):
        mock_script_path.exists.return_value = False

        result = CloseoutWriter.control_surface_drift_monitor()

        assert result.state == "missing"
        assert "control-surfaces.check-script-missing" in result.findings

    @patch("app.control_plane.orchestration.closeout_writer._CONTROL_SURFACE_CHECK_SCRIPT")
    @patch("app.control_plane.orchestration.closeout_writer.subprocess")
    def test_alert_when_script_times_out(self, mock_subprocess, mock_script_path):
        import subprocess as real_subprocess

        mock_script_path.exists.return_value = True
        mock_subprocess.run.side_effect = real_subprocess.TimeoutExpired(
            cmd="check", timeout=30
        )
        mock_subprocess.TimeoutExpired = real_subprocess.TimeoutExpired

        result = CloseoutWriter.control_surface_drift_monitor()

        assert result.state == "alert"
        assert "control-surfaces.check-timeout" in result.findings

    @patch("app.control_plane.orchestration.closeout_writer._CONTROL_SURFACE_CHECK_SCRIPT")
    @patch("app.control_plane.orchestration.closeout_writer.subprocess")
    def test_alert_when_os_error(self, mock_subprocess, mock_script_path):
        mock_script_path.exists.return_value = True
        mock_subprocess.run.side_effect = OSError("Permission denied")
        mock_subprocess.TimeoutExpired = TimeoutError

        result = CloseoutWriter.control_surface_drift_monitor()

        assert result.state == "alert"
        assert "control-surfaces.check-execution-failed" in result.findings


# ---------------------------------------------------------------------------
# reevu_readiness_monitor
# ---------------------------------------------------------------------------


class TestReevuReadinessMonitor:
    """Tests for CloseoutWriter.reevu_readiness_monitor."""

    @patch("app.control_plane.orchestration.closeout_writer._load_optional_json_object")
    def test_missing_when_artifacts_absent(self, mock_load):
        """Returns 'missing' when one or more artifacts are absent."""
        mock_load.return_value = (None, None)

        result = CloseoutWriter.reevu_readiness_monitor()

        assert isinstance(result, DeveloperControlPlaneSilentMonitorResponse)
        assert result.state == "missing"
        assert result.monitor_key == "reevu-readiness"
        assert any("missing:" in f for f in result.findings)

    @patch("app.control_plane.orchestration.closeout_writer._load_optional_json_object")
    def test_alert_when_artifacts_have_errors(self, mock_load):
        """Returns 'alert' when artifacts cannot be read."""
        mock_load.return_value = (None, "Unable to read file: corrupt")

        result = CloseoutWriter.reevu_readiness_monitor()

        assert result.state == "alert"
        assert "reevu.readiness-artifact-read-failed" in result.findings

    @patch("app.control_plane.orchestration.closeout_writer._load_optional_json_object")
    def test_alert_when_degraded(self, mock_load):
        """Returns 'alert' when runtime_status is not 'ready'."""
        real_question = {
            "runtime_status": "degraded",
            "passed_cases": 5,
            "total_cases": 10,
            "pass_rate": 0.5,
            "generated_at": "2026-04-15T10:00:00Z",
        }
        readiness_census = {
            "benchmark_ready_organization_ids": [],
            "organizations": [],
            "generated_at": "2026-04-15T10:00:00Z",
        }
        authority_gap = {
            "overall_gap_status": "blocked",
            "selected_local_org_blockers": ["blocker-1"],
            "generated_at": "2026-04-15T10:00:00Z",
        }

        mock_load.side_effect = [
            (real_question, None),
            (readiness_census, None),
            (authority_gap, None),
        ]

        result = CloseoutWriter.reevu_readiness_monitor()

        assert result.state == "alert"

    @patch("app.control_plane.orchestration.closeout_writer._load_optional_json_object")
    def test_healthy_when_all_ready(self, mock_load):
        """Returns 'healthy' when all artifacts are present and ready."""
        real_question = {
            "runtime_status": "ready",
            "passed_cases": 9,
            "total_cases": 10,
            "pass_rate": 0.9,
            "generated_at": "2026-04-15T10:00:00Z",
        }
        readiness_census = {
            "benchmark_ready_organization_ids": [1],
            "organizations": [
                {"organization_id": 1, "organization_name": "Org1", "runtime_status": "ready"},
            ],
            "generated_at": "2026-04-15T10:00:00Z",
        }
        authority_gap = {
            "overall_gap_status": "ready",
            "selected_local_org_blockers": [],
            "generated_at": "2026-04-15T10:00:00Z",
        }

        mock_load.side_effect = [
            (real_question, None),
            (readiness_census, None),
            (authority_gap, None),
        ]

        result = CloseoutWriter.reevu_readiness_monitor()

        assert result.state == "healthy"
        assert result.findings == []


# ---------------------------------------------------------------------------
# derive_silent_monitor_overall_state
# ---------------------------------------------------------------------------


class TestDeriveSilentMonitorOverallState:
    """Tests for CloseoutWriter.derive_silent_monitor_overall_state."""

    def _make_monitor(self, state: str) -> DeveloperControlPlaneSilentMonitorResponse:
        return DeveloperControlPlaneSilentMonitorResponse(
            monitor_key="test",
            label="Test",
            state=state,
            summary="Test monitor",
            refresh_cadence="manual",
            output_artifact="test.artifact",
        )

    def test_returns_healthy_for_empty_list(self):
        assert CloseoutWriter.derive_silent_monitor_overall_state([]) == "healthy"

    def test_returns_healthy_when_all_healthy(self):
        monitors = [self._make_monitor("healthy"), self._make_monitor("healthy")]
        assert CloseoutWriter.derive_silent_monitor_overall_state(monitors) == "healthy"

    def test_returns_alert_as_highest_priority(self):
        monitors = [
            self._make_monitor("healthy"),
            self._make_monitor("watch"),
            self._make_monitor("alert"),
        ]
        assert CloseoutWriter.derive_silent_monitor_overall_state(monitors) == "alert"

    def test_returns_missing_over_watch(self):
        monitors = [
            self._make_monitor("healthy"),
            self._make_monitor("watch"),
            self._make_monitor("missing"),
        ]
        assert CloseoutWriter.derive_silent_monitor_overall_state(monitors) == "missing"

    def test_returns_watch_over_healthy(self):
        monitors = [self._make_monitor("healthy"), self._make_monitor("watch")]
        assert CloseoutWriter.derive_silent_monitor_overall_state(monitors) == "watch"

    def test_alert_beats_missing(self):
        monitors = [self._make_monitor("missing"), self._make_monitor("alert")]
        assert CloseoutWriter.derive_silent_monitor_overall_state(monitors) == "alert"

    def test_single_monitor_returns_its_state(self):
        assert CloseoutWriter.derive_silent_monitor_overall_state(
            [self._make_monitor("watch")]
        ) == "watch"

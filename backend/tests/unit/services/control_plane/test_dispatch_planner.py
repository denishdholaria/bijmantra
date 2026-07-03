"""
Unit tests for Control Plane dispatch planner orchestrator.

Tests autonomy cycle loading, response building, memory-biased action
ordering, and first actionable completion write resolution in
``app.control_plane.orchestration.dispatch_planner``.

**Validates: Requirements 10.2, 16.4**
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneAutonomyCycleActionableCompletionWriteResponse,
    DeveloperControlPlaneAutonomyCycleActionResponse,
    DeveloperControlPlaneAutonomyCycleResponse,
)
from app.control_plane.orchestration.dispatch_planner import (
    DispatchPlanner,
    _bool_or,
    _int_or,
    _source_lane_id,
    _str_or,
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


class TestSourceLaneId:
    """Tests for _source_lane_id helper."""

    def test_returns_top_level_source_lane_id(self):
        assert _source_lane_id({"sourceLaneId": "lane-1"}) == "lane-1"

    def test_returns_provenance_source_lane_id(self):
        item = {"provenance": {"sourceLaneId": "lane-2"}}
        assert _source_lane_id(item) == "lane-2"

    def test_top_level_takes_precedence_over_provenance(self):
        item = {"sourceLaneId": "lane-top", "provenance": {"sourceLaneId": "lane-prov"}}
        assert _source_lane_id(item) == "lane-top"

    def test_returns_none_when_missing(self):
        assert _source_lane_id({}) is None

    def test_returns_none_for_empty_string(self):
        assert _source_lane_id({"sourceLaneId": ""}) is None

    def test_returns_none_for_non_string(self):
        assert _source_lane_id({"sourceLaneId": 42}) is None

    def test_returns_none_for_non_dict_provenance(self):
        assert _source_lane_id({"provenance": "not-a-dict"}) is None


class TestStrOr:
    """Tests for _str_or helper."""

    def test_returns_string_value(self):
        assert _str_or({"key": "value"}, "key") == "value"

    def test_returns_default_for_missing_key(self):
        assert _str_or({}, "key", "default") == "default"

    def test_returns_default_for_non_string(self):
        assert _str_or({"key": 42}, "key", "fallback") == "fallback"

    def test_returns_none_default(self):
        assert _str_or({}, "key") is None


class TestIntOr:
    """Tests for _int_or helper."""

    def test_returns_int_value(self):
        assert _int_or({"key": 5}, "key") == 5

    def test_returns_default_for_missing_key(self):
        assert _int_or({}, "key", 10) == 10

    def test_returns_default_for_non_int(self):
        assert _int_or({"key": "not-int"}, "key", 7) == 7

    def test_default_is_zero(self):
        assert _int_or({}, "key") == 0


class TestBoolOr:
    """Tests for _bool_or helper."""

    def test_returns_true(self):
        assert _bool_or({"key": True}, "key") is True

    def test_returns_false(self):
        assert _bool_or({"key": False}, "key") is False

    def test_returns_none_for_missing_key(self):
        assert _bool_or({}, "key") is None

    def test_returns_none_for_non_bool(self):
        assert _bool_or({"key": "yes"}, "key") is None


# ---------------------------------------------------------------------------
# load_autonomy_cycle_payload
# ---------------------------------------------------------------------------


class TestLoadAutonomyCyclePayload:
    """Tests for DispatchPlanner.load_autonomy_cycle_payload."""

    @patch("app.control_plane.orchestration.dispatch_planner.telemetry_service")
    def test_delegates_to_telemetry_service(self, mock_telemetry):
        """load_autonomy_cycle_payload delegates to telemetry_service."""
        expected = {"selectedJobs": [], "nextActions": []}
        mock_telemetry.load_autonomy_cycle_payload.return_value = expected

        result = DispatchPlanner.load_autonomy_cycle_payload()

        assert result == expected
        mock_telemetry.load_autonomy_cycle_payload.assert_called_once()

    @patch("app.control_plane.orchestration.dispatch_planner.telemetry_service")
    def test_returns_none_when_telemetry_returns_none(self, mock_telemetry):
        """Returns None when telemetry_service returns None."""
        mock_telemetry.load_autonomy_cycle_payload.return_value = None

        result = DispatchPlanner.load_autonomy_cycle_payload()

        assert result is None


# ---------------------------------------------------------------------------
# autonomy_cycle_response — None payload
# ---------------------------------------------------------------------------


class TestAutonomyCycleResponseNone:
    """Tests for DispatchPlanner.autonomy_cycle_response with None payload."""

    def test_returns_exists_false(self):
        """When payload is None, exists is False."""
        response = DispatchPlanner.autonomy_cycle_response(None)
        assert response.exists is False

    def test_returns_artifact_path(self):
        """When payload is None, artifact_path is still populated."""
        response = DispatchPlanner.autonomy_cycle_response(None)
        assert isinstance(response.artifact_path, str)
        assert len(response.artifact_path) > 0

    def test_ordering_source_is_artifact(self):
        """When payload is None, ordering source defaults to 'artifact'."""
        response = DispatchPlanner.autonomy_cycle_response(None)
        assert response.next_action_ordering_source == "artifact"

    def test_watchdog_exists_false(self):
        """When payload is None, watchdog.exists is False."""
        response = DispatchPlanner.autonomy_cycle_response(None)
        assert response.watchdog.exists is False

    def test_empty_lists(self):
        """When payload is None, all list fields are empty."""
        response = DispatchPlanner.autonomy_cycle_response(None)
        assert response.selected_jobs == []
        assert response.blocked_jobs == []
        assert response.closeout_candidates == []
        assert response.next_actions == []


# ---------------------------------------------------------------------------
# autonomy_cycle_response — valid payload
# ---------------------------------------------------------------------------


class TestAutonomyCycleResponseValid:
    """Tests for DispatchPlanner.autonomy_cycle_response with valid payload."""

    def _make_payload(self, **overrides):
        """Build a minimal valid autonomy cycle payload."""
        base = {
            "generatedAt": "2026-04-15T10:00:00Z",
            "queuePath": ".agent/jobs/overnight-queue.json",
            "window": "nightly",
            "maxJobsPerRun": 2,
            "statusCounts": {"selected": 1, "blocked": 0},
            "selectedJobCount": 1,
            "blockedJobCount": 0,
            "closeoutCandidateCount": 0,
            "nextActionCount": 1,
            "watchdog": {
                "exists": True,
                "statePath": "runtime-artifacts/watchdog-state.json",
                "lastCheck": "2026-04-15T09:55:00Z",
                "gatewayHealthy": True,
                "stateIsStale": False,
                "totalAlerts": 0,
                "jobErrors": {},
            },
            "selectedJobs": [
                {
                    "jobId": "job-1",
                    "title": "First Job",
                    "sourceLaneId": "lane-a",
                    "priority": "p1",
                    "primaryAgent": "OmShriMaatreNamaha",
                    "triggerReason": "nightly-dispatch",
                    "sourceTask": "task-1",
                },
            ],
            "blockedJobs": [
                {
                    "jobId": "job-blocked",
                    "title": "Blocked Job",
                    "sourceLaneId": "lane-b",
                    "reason": "dependency-unmet",
                },
            ],
            "closeoutCandidates": [
                {
                    "jobId": "job-close",
                    "title": "Closeout Job",
                    "sourceLaneId": "lane-c",
                    "queueStatus": "completed",
                    "closeoutStatus": "ready",
                    "missionId": "mission-1",
                    "verificationEvidenceRef": "ref-1",
                    "path": "/path/to/closeout",
                },
            ],
            "nextActions": [
                {
                    "action": "execute-job",
                    "jobId": "job-1",
                    "title": "Execute First Job",
                    "sourceLaneId": "lane-a",
                    "reason": "highest-priority",
                    "primaryAgent": "OmShriMaatreNamaha",
                    "priority": "p1",
                },
            ],
        }
        base.update(overrides)
        return base

    def test_exists_is_true(self):
        response = DispatchPlanner.autonomy_cycle_response(self._make_payload())
        assert response.exists is True

    def test_selected_jobs_parsed(self):
        response = DispatchPlanner.autonomy_cycle_response(self._make_payload())
        assert len(response.selected_jobs) == 1
        job = response.selected_jobs[0]
        assert job.job_id == "job-1"
        assert job.title == "First Job"
        assert job.source_lane_id == "lane-a"
        assert job.priority == "p1"
        assert job.primary_agent == "OmShriMaatreNamaha"

    def test_blocked_jobs_parsed(self):
        response = DispatchPlanner.autonomy_cycle_response(self._make_payload())
        assert len(response.blocked_jobs) == 1
        job = response.blocked_jobs[0]
        assert job.job_id == "job-blocked"
        assert job.reason == "dependency-unmet"

    def test_closeout_candidates_parsed(self):
        response = DispatchPlanner.autonomy_cycle_response(self._make_payload())
        assert len(response.closeout_candidates) == 1
        candidate = response.closeout_candidates[0]
        assert candidate.job_id == "job-close"
        assert candidate.closeout_status == "ready"
        assert candidate.mission_id == "mission-1"

    def test_next_actions_parsed(self):
        response = DispatchPlanner.autonomy_cycle_response(self._make_payload())
        assert len(response.next_actions) == 1
        action = response.next_actions[0]
        assert action.action == "execute-job"
        assert action.job_id == "job-1"
        assert action.priority == "p1"

    def test_watchdog_parsed(self):
        response = DispatchPlanner.autonomy_cycle_response(self._make_payload())
        assert response.watchdog.exists is True
        assert response.watchdog.gateway_healthy is True
        assert response.watchdog.state_is_stale is False

    def test_status_counts_parsed(self):
        response = DispatchPlanner.autonomy_cycle_response(self._make_payload())
        assert response.status_counts == {"selected": 1, "blocked": 0}

    def test_scalar_fields_parsed(self):
        response = DispatchPlanner.autonomy_cycle_response(self._make_payload())
        assert response.generated_at == "2026-04-15T10:00:00Z"
        assert response.window == "nightly"
        assert response.max_jobs_per_run == 2

    def test_returns_response_model_type(self):
        response = DispatchPlanner.autonomy_cycle_response(self._make_payload())
        assert isinstance(response, DeveloperControlPlaneAutonomyCycleResponse)


# ---------------------------------------------------------------------------
# autonomy_cycle_response — malformed / missing fields
# ---------------------------------------------------------------------------


class TestAutonomyCycleResponseMalformed:
    """Tests for DispatchPlanner.autonomy_cycle_response with missing/malformed fields."""

    def test_empty_payload_returns_exists_true(self):
        """An empty dict is still a valid (but sparse) payload."""
        response = DispatchPlanner.autonomy_cycle_response({})
        assert response.exists is True
        assert response.selected_jobs == []
        assert response.blocked_jobs == []
        assert response.closeout_candidates == []
        assert response.next_actions == []

    def test_non_list_selected_jobs_ignored(self):
        """selectedJobs that is not a list is safely ignored."""
        response = DispatchPlanner.autonomy_cycle_response({"selectedJobs": "not-a-list"})
        assert response.selected_jobs == []

    def test_non_dict_items_in_selected_jobs_skipped(self):
        """Non-dict items in selectedJobs are skipped."""
        response = DispatchPlanner.autonomy_cycle_response({
            "selectedJobs": ["not-a-dict", 42, {"jobId": "valid", "title": "Valid"}],
        })
        assert len(response.selected_jobs) == 1
        assert response.selected_jobs[0].job_id == "valid"

    def test_selected_job_without_job_id_skipped(self):
        """Selected job entries without a jobId string are skipped."""
        response = DispatchPlanner.autonomy_cycle_response({
            "selectedJobs": [{"title": "No ID"}, {"jobId": 123}],
        })
        assert response.selected_jobs == []

    def test_non_dict_watchdog_handled(self):
        """Non-dict watchdog field is handled gracefully."""
        response = DispatchPlanner.autonomy_cycle_response({"watchdog": "not-a-dict"})
        assert response.watchdog.exists is False

    def test_non_dict_status_counts_handled(self):
        """Non-dict statusCounts is handled gracefully."""
        response = DispatchPlanner.autonomy_cycle_response({"statusCounts": [1, 2]})
        assert response.status_counts == {}

    def test_status_counts_filters_non_int_values(self):
        """statusCounts entries with non-int values are filtered out."""
        response = DispatchPlanner.autonomy_cycle_response({
            "statusCounts": {"valid": 5, "invalid": "not-int", "also_bad": None},
        })
        assert response.status_counts == {"valid": 5}

    def test_next_action_without_action_string_skipped(self):
        """Next action entries without an 'action' string are skipped."""
        response = DispatchPlanner.autonomy_cycle_response({
            "nextActions": [{"jobId": "j1"}, {"action": 42}],
        })
        assert response.next_actions == []

    def test_watchdog_job_errors_non_dict_skipped(self):
        """Non-dict job error entries in watchdog are skipped."""
        response = DispatchPlanner.autonomy_cycle_response({
            "watchdog": {
                "exists": True,
                "statePath": "path",
                "jobErrors": {"job-1": "not-a-dict", "job-2": {"lastError": "err"}},
            },
        })
        assert "job-2" in response.watchdog.job_errors
        assert "job-1" not in response.watchdog.job_errors


# ---------------------------------------------------------------------------
# memory_biased_autonomy_cycle_next_actions
# ---------------------------------------------------------------------------


class TestMemoryBiasedNextActions:
    """Tests for DispatchPlanner.memory_biased_autonomy_cycle_next_actions."""

    @pytest.mark.asyncio
    @patch("app.api.bijmantra.developer_control_plane._get_learning_entries", new_callable=AsyncMock)
    @patch("app.api.bijmantra.developer_control_plane._get_missing_learning_tables", new_callable=AsyncMock)
    async def test_returns_original_when_no_learning_data(
        self, mock_missing_tables, mock_learning_entries
    ):
        """Returns original actions when learning queries return no entries."""
        mock_missing_tables.return_value = []
        mock_learning_entries.return_value = []

        actions = [
            DeveloperControlPlaneAutonomyCycleActionResponse(
                action="execute-job", job_id="j1", priority="p1",
            ),
            DeveloperControlPlaneAutonomyCycleActionResponse(
                action="execute-job", job_id="j2", priority="p2",
            ),
        ]

        db = AsyncMock()
        result, source = await DispatchPlanner.memory_biased_autonomy_cycle_next_actions(
            db, organization_id=1, next_actions=actions,
        )

        assert source == "artifact"
        assert len(result) == len(actions)

    @pytest.mark.asyncio
    async def test_returns_empty_list_unchanged(self):
        """Empty action list is returned as-is with 'artifact' source."""
        db = AsyncMock()
        result, source = await DispatchPlanner.memory_biased_autonomy_cycle_next_actions(
            db, organization_id=1, next_actions=[],
        )

        assert result == []
        assert source == "artifact"

    @pytest.mark.asyncio
    @patch("app.api.bijmantra.developer_control_plane._get_learning_entries", new_callable=AsyncMock)
    @patch("app.api.bijmantra.developer_control_plane._get_missing_learning_tables", new_callable=AsyncMock)
    async def test_returns_artifact_when_tables_missing(
        self, mock_missing_tables, mock_learning_entries
    ):
        """Returns original actions with 'artifact' source when learning tables are missing."""
        mock_missing_tables.return_value = ["missing_table"]

        actions = [
            DeveloperControlPlaneAutonomyCycleActionResponse(
                action="execute-job", job_id="j1", priority="p1",
            ),
        ]

        db = AsyncMock()
        result, source = await DispatchPlanner.memory_biased_autonomy_cycle_next_actions(
            db, organization_id=1, next_actions=actions,
        )

        assert source == "artifact"
        assert result == actions
        mock_learning_entries.assert_not_called()


# ---------------------------------------------------------------------------
# resolve_first_actionable_completion_write
# ---------------------------------------------------------------------------


class TestResolveFirstActionableCompletionWrite:
    """Tests for DispatchPlanner.resolve_first_actionable_completion_write."""

    def test_returns_none_when_no_actionable_writes(self):
        """Returns None when no actions are prepare-completion-write-back."""
        actions = [
            DeveloperControlPlaneAutonomyCycleActionResponse(
                action="execute-job", job_id="j1",
            ),
            DeveloperControlPlaneAutonomyCycleActionResponse(
                action="review-closeout", job_id="j2",
            ),
        ]
        result = DispatchPlanner.resolve_first_actionable_completion_write(actions)
        assert result is None

    def test_returns_none_for_empty_list(self):
        """Returns None for an empty action list."""
        result = DispatchPlanner.resolve_first_actionable_completion_write([])
        assert result is None

    def test_returns_response_when_actionable_write_found(self):
        """Returns a valid response when a prepare-completion-write-back action has preparation data."""
        preparation = {
            "source_lane_id": "lane-x",
            "queue_job_id": "job-x",
            "draft_source": "closeout-receipt",
            "queue_status": {
                "queue_path": "path",
                "queue_sha256": "abc",
                "exists": True,
                "job_count": 1,
                "updated_at": "2026-04-15",
            },
            "closeout_receipt": {
                "exists": True,
                "queue_job_id": "job-x",
            },
            "prepared_request": {
                "source_board_concurrency_token": "token",
                "expected_queue_sha256": "abc",
                "operator_intent": "complete-lane",
                "completion": {
                    "source_lane_id": "lane-x",
                    "queue_job_id": "job-x",
                    "closure_summary": "Done",
                    "evidence": ["evidence-1"],
                },
            },
        }
        actions = [
            DeveloperControlPlaneAutonomyCycleActionResponse(
                action="prepare-completion-write-back",
                job_id="job-x",
                source_lane_id="lane-x",
                reason="closeout-ready",
                detail={"completionWritePreparation": preparation},
            ),
        ]
        result = DispatchPlanner.resolve_first_actionable_completion_write(actions)
        assert result is not None
        assert isinstance(
            result,
            DeveloperControlPlaneAutonomyCycleActionableCompletionWriteResponse,
        )
        assert result.job_id == "job-x"
        assert result.source_lane_id == "lane-x"

    def test_returns_none_when_preparation_missing(self):
        """Returns None when action is prepare-completion-write-back but has no preparation detail."""
        actions = [
            DeveloperControlPlaneAutonomyCycleActionResponse(
                action="prepare-completion-write-back",
                job_id="job-y",
                source_lane_id="lane-y",
            ),
        ]
        result = DispatchPlanner.resolve_first_actionable_completion_write(actions)
        assert result is None

"""
Characterization tests for developer_control_plane.py.

These tests capture the current JSON response shapes for all 17 endpoints so that
the upcoming extraction (Tasks 2–5) cannot silently break the API contract that the
BeingBijMantra VS Code extension depends on.

Organised by the 4 responsibility domains that will become separate routers:
  - Lanes  (active-board CRUD, versions, restore, completion)
  - Missions (runtime/mission-state)
  - Verification (runtime/silent-monitors, runtime/autonomy-cycle,
                  runtime/completion-assist, runtime/watchdog-status)
  - Telemetry (overnight-queue/status, overnight-queue/write-entry,
               overnight-queue/jobs/{id}/closeout-receipt, learnings)

Validates: AC-1, NFR-1
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient

BASE = "/api/v2/developer-control-plane"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_keys(data: dict, *required_keys: str) -> None:
    """Assert that every required key is present in the response dict."""
    missing = [k for k in required_keys if k not in data]
    assert not missing, f"Missing keys in response: {missing}\nGot: {list(data.keys())}"


# ---------------------------------------------------------------------------
# Auth guard — all endpoints require superuser
# ---------------------------------------------------------------------------

class TestAuthGuard:
    """Every endpoint must reject unauthenticated requests with 401/403."""

    @pytest.mark.asyncio
    async def test_active_board_requires_auth(self, authenticated_client: AsyncClient):
        # authenticated_client is a regular user, not superuser — should get 403
        response = await authenticated_client.get(f"{BASE}/active-board")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_queue_status_requires_auth(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get(f"{BASE}/overnight-queue/status")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_watchdog_status_requires_auth(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get(f"{BASE}/runtime/watchdog-status")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_autonomy_cycle_requires_auth(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get(f"{BASE}/runtime/autonomy-cycle")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_silent_monitors_requires_auth(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get(f"{BASE}/runtime/silent-monitors")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_learnings_requires_auth(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get(f"{BASE}/learnings")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_mission_state_requires_auth(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get(f"{BASE}/runtime/mission-state")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_completion_assist_requires_auth(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get(f"{BASE}/runtime/completion-assist")
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Domain 1: Lanes — active-board CRUD, versions, restore, completion
# ---------------------------------------------------------------------------

class TestLanesEndpoints:
    """Characterization tests for lane/board management endpoints."""

    @pytest.mark.asyncio
    async def test_get_active_board_returns_200(self, superuser_client: AsyncClient):
        """GET /active-board must return 200 with exists field."""
        response = await superuser_client.get(f"{BASE}/active-board")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_active_board_response_shape(self, superuser_client: AsyncClient):
        """GET /active-board must return {exists: bool, record: ...}."""
        response = await superuser_client.get(f"{BASE}/active-board")
        assert response.status_code == 200
        data = response.json()

        _assert_keys(data, "exists")
        assert isinstance(data["exists"], bool)
        # record is either None (no board saved yet) or a dict with required fields
        assert "record" in data
        if data["record"] is not None:
            record = data["record"]
            _assert_keys(
                record,
                "id",
                "organization_id",
                "board_id",
                "schema_version",
                "visibility",
                "canonical_board_json",
                "concurrency_token",
                "updated_by_user_id",
                "updated_at",
                "save_source",
                "created_at",
            )
            assert isinstance(record["id"], int)
            assert isinstance(record["organization_id"], int)
            assert isinstance(record["board_id"], str)
            assert isinstance(record["concurrency_token"], str)
            assert len(record["concurrency_token"]) == 64  # SHA-256 hex

    @pytest.mark.asyncio
    async def test_get_active_board_versions_returns_200(self, superuser_client: AsyncClient):
        """GET /active-board/versions must return 200."""
        response = await superuser_client.get(f"{BASE}/active-board/versions")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_active_board_versions_response_shape(self, superuser_client: AsyncClient):
        """GET /active-board/versions must return {board_id, total_count, versions}."""
        response = await superuser_client.get(f"{BASE}/active-board/versions")
        assert response.status_code == 200
        data = response.json()

        _assert_keys(data, "board_id", "total_count", "versions")
        assert isinstance(data["board_id"], str)
        assert isinstance(data["total_count"], int)
        assert isinstance(data["versions"], list)

        if data["versions"]:
            version = data["versions"][0]
            _assert_keys(
                version,
                "revision_id",
                "schema_version",
                "visibility",
                "concurrency_token",
                "created_at",
                "saved_by_user_id",
                "save_source",
                "is_current",
            )

    @pytest.mark.asyncio
    async def test_put_active_board_rejects_invalid_json(self, superuser_client: AsyncClient):
        """PUT /active-board with invalid board JSON must return 400."""
        response = await superuser_client.put(
            f"{BASE}/active-board",
            json={
                "canonical_board_json": "not-valid-json",
                "save_source": "test",
                "concurrency_token": None,
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_restore_board_version_404_for_missing_revision(
        self, superuser_client: AsyncClient
    ):
        """POST /active-board/versions/{id}/restore with unknown id must return 404."""
        response = await superuser_client.post(
            f"{BASE}/active-board/versions/999999/restore",
            json={"concurrency_token": "a" * 64},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_prepare_completion_write_404_for_missing_lane(
        self, superuser_client: AsyncClient
    ):
        """POST /active-board/prepare-completion-write with unknown lane must return 404 or 409."""
        response = await superuser_client.post(
            f"{BASE}/active-board/prepare-completion-write",
            json={"source_lane_id": "nonexistent-lane-id-xyz"},
        )
        # 409 if no active board exists, 404 if board exists but lane is missing
        assert response.status_code in (404, 409)

    @pytest.mark.asyncio
    async def test_write_completion_rejects_wrong_operator_intent(
        self, superuser_client: AsyncClient
    ):
        """POST /active-board/write-completion with wrong operator_intent must return 400."""
        response = await superuser_client.post(
            f"{BASE}/active-board/write-completion",
            json={
                "source_board_concurrency_token": "a" * 64,
                "expected_queue_sha256": "b" * 64,
                "operator_intent": "wrong-intent",
                "completion": {
                    "source_lane_id": "test-lane",
                    "queue_job_id": "test-job",
                    "closure_summary": "done",
                    "evidence": ["ref1"],
                },
            },
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Domain 2: Missions — runtime/mission-state
# ---------------------------------------------------------------------------

class TestMissionsEndpoints:
    """Characterization tests for mission state endpoints."""

    @pytest.mark.asyncio
    async def test_get_mission_state_returns_200(self, superuser_client: AsyncClient):
        """GET /runtime/mission-state must return 200."""
        response = await superuser_client.get(f"{BASE}/runtime/mission-state")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_mission_state_response_shape(self, superuser_client: AsyncClient):
        """GET /runtime/mission-state must return {count, missions}."""
        response = await superuser_client.get(f"{BASE}/runtime/mission-state")
        assert response.status_code == 200
        data = response.json()

        _assert_keys(data, "count", "missions")
        assert isinstance(data["count"], int)
        assert isinstance(data["missions"], list)

        if data["missions"]:
            mission = data["missions"][0]
            _assert_keys(
                mission,
                "mission_id",
                "objective",
                "status",
                "owner",
                "priority",
                "created_at",
                "updated_at",
                "subtask_total",
                "subtask_completed",
                "assignment_total",
                "evidence_count",
                "blocker_count",
                "escalation_needed",
                "verification",
            )
            verification = mission["verification"]
            _assert_keys(verification, "passed", "warned", "failed")

    @pytest.mark.asyncio
    async def test_get_mission_state_respects_limit_param(self, superuser_client: AsyncClient):
        """GET /runtime/mission-state?limit=1 must return at most 1 mission."""
        response = await superuser_client.get(f"{BASE}/runtime/mission-state?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["missions"]) <= 1

    @pytest.mark.asyncio
    async def test_get_mission_detail_404_for_unknown_mission(
        self, superuser_client: AsyncClient
    ):
        """GET /runtime/mission-state/{id} with unknown id must return 404."""
        response = await superuser_client.get(
            f"{BASE}/runtime/mission-state/nonexistent-mission-id-xyz"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_bootstrap_mission_from_closeout_receipt_shape(
        self, superuser_client: AsyncClient
    ):
        """POST /runtime/mission-state/bootstrap-closeout-receipt must return {action, mission_id}."""
        response = await superuser_client.post(
            f"{BASE}/runtime/mission-state/bootstrap-closeout-receipt",
            json={"queue_job_id": "nonexistent-job-for-characterization-test"},
        )
        # Either 200 (action=no-receipt) or 200 (action=created/existing)
        assert response.status_code == 200
        data = response.json()
        _assert_keys(data, "action")
        assert isinstance(data["action"], str)
        # mission_id may be None if no receipt found
        assert "mission_id" in data


# ---------------------------------------------------------------------------
# Domain 3: Verification — silent-monitors, autonomy-cycle,
#                          completion-assist, watchdog-status
# ---------------------------------------------------------------------------

class TestVerificationEndpoints:
    """Characterization tests for verification and monitoring endpoints."""

    @pytest.mark.asyncio
    async def test_get_watchdog_status_returns_200(self, superuser_client: AsyncClient):
        """GET /runtime/watchdog-status must return 200."""
        response = await superuser_client.get(f"{BASE}/runtime/watchdog-status")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_watchdog_status_response_shape(self, superuser_client: AsyncClient):
        """GET /runtime/watchdog-status must return the full watchdog schema."""
        response = await superuser_client.get(f"{BASE}/runtime/watchdog-status")
        assert response.status_code == 200
        data = response.json()

        _assert_keys(
            data,
            "exists",
            "state_path",
            "auth_store_exists",
            "auth_store_path",
            "bootstrap_ready",
            "bootstrap_status",
            "mission_evidence_dir_exists",
            "mission_evidence_dir_path",
            "total_checks",
            "total_alerts",
            "job_count",
            "jobs",
        )
        assert isinstance(data["exists"], bool)
        assert isinstance(data["auth_store_exists"], bool)
        assert isinstance(data["bootstrap_ready"], bool)
        assert isinstance(data["total_checks"], int)
        assert isinstance(data["total_alerts"], int)
        assert isinstance(data["job_count"], int)
        assert isinstance(data["jobs"], list)

        for job in data["jobs"]:
            _assert_keys(job, "job_id")
            assert isinstance(job["job_id"], str)

    @pytest.mark.asyncio
    async def test_get_autonomy_cycle_returns_200(self, superuser_client: AsyncClient):
        """GET /runtime/autonomy-cycle must return 200."""
        response = await superuser_client.get(f"{BASE}/runtime/autonomy-cycle")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_autonomy_cycle_response_shape(self, superuser_client: AsyncClient):
        """GET /runtime/autonomy-cycle must return the full autonomy cycle schema."""
        response = await superuser_client.get(f"{BASE}/runtime/autonomy-cycle")
        assert response.status_code == 200
        data = response.json()

        _assert_keys(
            data,
            "exists",
            "artifact_path",
            "selected_job_count",
            "blocked_job_count",
            "closeout_candidate_count",
            "next_action_count",
            "next_action_ordering_source",
            "watchdog",
            "selected_jobs",
            "blocked_jobs",
            "closeout_candidates",
            "next_actions",
        )
        assert isinstance(data["exists"], bool)
        assert isinstance(data["artifact_path"], str)
        assert isinstance(data["selected_job_count"], int)
        assert isinstance(data["blocked_job_count"], int)
        assert isinstance(data["closeout_candidate_count"], int)
        assert isinstance(data["next_action_count"], int)
        assert isinstance(data["next_action_ordering_source"], str)
        assert isinstance(data["selected_jobs"], list)
        assert isinstance(data["blocked_jobs"], list)
        assert isinstance(data["closeout_candidates"], list)
        assert isinstance(data["next_actions"], list)

        # Watchdog sub-object
        watchdog = data["watchdog"]
        _assert_keys(watchdog, "exists", "state_path", "total_alerts")
        assert isinstance(watchdog["exists"], bool)
        assert isinstance(watchdog["total_alerts"], int)

    @pytest.mark.asyncio
    async def test_get_silent_monitors_returns_200(self, superuser_client: AsyncClient):
        """GET /runtime/silent-monitors must return 200."""
        response = await superuser_client.get(f"{BASE}/runtime/silent-monitors")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_silent_monitors_response_shape(self, superuser_client: AsyncClient):
        """GET /runtime/silent-monitors must return {generated_at, overall_state, monitors}."""
        response = await superuser_client.get(f"{BASE}/runtime/silent-monitors")
        assert response.status_code == 200
        data = response.json()

        _assert_keys(data, "generated_at", "overall_state", "should_emit", "monitors")
        assert isinstance(data["generated_at"], str)
        assert isinstance(data["overall_state"], str)
        assert isinstance(data["should_emit"], bool)
        assert isinstance(data["monitors"], list)

        for monitor in data["monitors"]:
            _assert_keys(
                monitor,
                "monitor_key",
                "label",
                "state",
                "should_emit",
                "summary",
                "refresh_cadence",
                "output_artifact",
            )

    @pytest.mark.asyncio
    async def test_get_completion_assist_returns_200(self, superuser_client: AsyncClient):
        """GET /runtime/completion-assist must return 200."""
        response = await superuser_client.get(f"{BASE}/runtime/completion-assist")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_completion_assist_response_shape(self, superuser_client: AsyncClient):
        """GET /runtime/completion-assist must return {exists, artifact_path}."""
        response = await superuser_client.get(f"{BASE}/runtime/completion-assist")
        assert response.status_code == 200
        data = response.json()

        _assert_keys(data, "exists", "artifact_path")
        assert isinstance(data["exists"], bool)
        assert isinstance(data["artifact_path"], str)


# ---------------------------------------------------------------------------
# Domain 4: Telemetry — overnight-queue/status, write-entry,
#                       closeout-receipt, learnings
# ---------------------------------------------------------------------------

class TestTelemetryEndpoints:
    """Characterization tests for telemetry and receipt endpoints."""

    @pytest.mark.asyncio
    async def test_get_queue_status_returns_200(self, superuser_client: AsyncClient):
        """GET /overnight-queue/status must return 200."""
        response = await superuser_client.get(f"{BASE}/overnight-queue/status")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_queue_status_response_shape(self, superuser_client: AsyncClient):
        """GET /overnight-queue/status must return the queue status schema."""
        response = await superuser_client.get(f"{BASE}/overnight-queue/status")
        assert response.status_code == 200
        data = response.json()

        _assert_keys(data, "queue_path", "queue_sha256", "exists", "job_count", "updated_at")
        assert isinstance(data["queue_path"], str)
        assert isinstance(data["queue_sha256"], str)
        assert len(data["queue_sha256"]) == 64  # SHA-256 hex
        assert isinstance(data["exists"], bool)
        assert isinstance(data["job_count"], int)
        # updated_at is str or None
        assert data["updated_at"] is None or isinstance(data["updated_at"], str)

    @pytest.mark.asyncio
    async def test_get_closeout_receipt_returns_200_for_unknown_job(
        self, superuser_client: AsyncClient
    ):
        """GET /overnight-queue/jobs/{id}/closeout-receipt must return 200 even for unknown jobs."""
        response = await superuser_client.get(
            f"{BASE}/overnight-queue/jobs/nonexistent-job-xyz/closeout-receipt"
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_closeout_receipt_response_shape(self, superuser_client: AsyncClient):
        """GET /overnight-queue/jobs/{id}/closeout-receipt must return the closeout schema."""
        response = await superuser_client.get(
            f"{BASE}/overnight-queue/jobs/nonexistent-job-xyz/closeout-receipt"
        )
        assert response.status_code == 200
        data = response.json()

        _assert_keys(data, "exists", "queue_job_id")
        assert isinstance(data["exists"], bool)
        assert data["queue_job_id"] == "nonexistent-job-xyz"

        if data["exists"]:
            # When a receipt exists, these fields must be present
            _assert_keys(data, "closeout_commands", "artifacts")
            assert isinstance(data["closeout_commands"], list)
            assert isinstance(data["artifacts"], list)

            for cmd in data["closeout_commands"]:
                _assert_keys(cmd, "command", "passed")
                assert isinstance(cmd["passed"], bool)

            for artifact in data["artifacts"]:
                _assert_keys(artifact, "path", "exists")
                assert isinstance(artifact["exists"], bool)

    @pytest.mark.asyncio
    async def test_get_learnings_returns_200(self, superuser_client: AsyncClient):
        """GET /learnings must return 200."""
        response = await superuser_client.get(f"{BASE}/learnings")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_learnings_response_shape(self, superuser_client: AsyncClient):
        """GET /learnings must return {total_count, entries}."""
        response = await superuser_client.get(f"{BASE}/learnings")
        assert response.status_code == 200
        data = response.json()

        _assert_keys(data, "total_count", "entries")
        assert isinstance(data["total_count"], int)
        assert isinstance(data["entries"], list)

        if data["entries"]:
            entry = data["entries"][0]
            _assert_keys(
                entry,
                "learning_entry_id",
                "organization_id",
                "entry_type",
                "source_classification",
                "title",
                "summary",
                "recorded_at",
                "evidence_refs",
            )
            assert isinstance(entry["learning_entry_id"], int)
            assert isinstance(entry["entry_type"], str)
            assert isinstance(entry["evidence_refs"], list)

    @pytest.mark.asyncio
    async def test_get_learnings_with_limit(self, superuser_client: AsyncClient):
        """GET /learnings?limit=5 must return at most 5 entries."""
        response = await superuser_client.get(f"{BASE}/learnings?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) <= 5

    @pytest.mark.asyncio
    async def test_get_learnings_rejects_invalid_entry_type(
        self, superuser_client: AsyncClient
    ):
        """GET /learnings?entry_type=invalid must return 400."""
        response = await superuser_client.get(f"{BASE}/learnings?entry_type=not-a-valid-type")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_post_queue_write_entry_rejects_wrong_operator_intent(
        self, superuser_client: AsyncClient
    ):
        """POST /overnight-queue/write-entry with wrong operator_intent must return 400."""
        response = await superuser_client.post(
            f"{BASE}/overnight-queue/write-entry",
            json={
                "source_board_concurrency_token": "a" * 64,
                "expected_queue_sha256": "b" * 64,
                "operator_intent": "wrong-intent",
                "queue_entry": {"jobId": "test-job"},
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_post_queue_write_entry_rejects_stale_board_token(
        self, superuser_client: AsyncClient
    ):
        """POST /overnight-queue/write-entry with stale board token must return 409."""
        # Get current queue sha256 so that's correct, but use a fake board token
        queue_response = await superuser_client.get(f"{BASE}/overnight-queue/status")
        current_sha256 = queue_response.json()["queue_sha256"]

        response = await superuser_client.post(
            f"{BASE}/overnight-queue/write-entry",
            json={
                "source_board_concurrency_token": "0" * 64,  # stale/fake token
                "expected_queue_sha256": current_sha256,
                "operator_intent": "write-reviewed-queue-entry",
                "queue_entry": {
                    "jobId": "test-job-characterization",
                    "title": "Test Job",
                    "priority": "p3",
                    "primaryAgent": "TestAgent",
                    "provenance": {
                        "sourceLaneId": "test-lane",
                        "sourceBoardConcurrencyToken": "0" * 64,
                    },
                },
            },
        )
        # 409 because board token is stale (or 409 because no active board)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_post_queue_write_entry_rejects_stale_queue_sha(
        self, superuser_client: AsyncClient
    ):
        """POST /overnight-queue/write-entry with stale queue sha must return 409."""
        # Get current board token so that's correct, but use a fake queue sha
        board_response = await superuser_client.get(f"{BASE}/active-board")
        board_data = board_response.json()

        if not board_data["exists"]:
            pytest.skip("No active board — cannot test stale queue sha conflict")

        board_token = board_data["record"]["concurrency_token"]

        response = await superuser_client.post(
            f"{BASE}/overnight-queue/write-entry",
            json={
                "source_board_concurrency_token": board_token,
                "expected_queue_sha256": "0" * 64,  # stale/fake sha
                "operator_intent": "write-reviewed-queue-entry",
                "queue_entry": {
                    "jobId": "test-job-characterization-sha",
                    "title": "Test Job",
                    "priority": "p3",
                    "primaryAgent": "TestAgent",
                    "provenance": {
                        "sourceLaneId": "test-lane",
                        "sourceBoardConcurrencyToken": board_token,
                    },
                },
            },
        )
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# Endpoint inventory smoke test — all 17 routes must be reachable
# ---------------------------------------------------------------------------

class TestEndpointInventory:
    """
    Verify all 17 endpoints are registered and return non-500 responses.
    This is the baseline that must hold before and after extraction.
    """

    @pytest.mark.asyncio
    async def test_all_get_endpoints_are_reachable(self, superuser_client: AsyncClient):
        """All GET endpoints must return 2xx or 4xx (never 500)."""
        get_endpoints = [
            f"{BASE}/active-board",
            f"{BASE}/active-board/versions",
            f"{BASE}/overnight-queue/status",
            f"{BASE}/overnight-queue/jobs/probe-job/closeout-receipt",
            f"{BASE}/runtime/watchdog-status",
            f"{BASE}/runtime/autonomy-cycle",
            f"{BASE}/runtime/completion-assist",
            f"{BASE}/runtime/silent-monitors",
            f"{BASE}/runtime/mission-state",
            f"{BASE}/learnings",
        ]
        for path in get_endpoints:
            response = await superuser_client.get(path)
            assert response.status_code < 500, (
                f"Endpoint {path} returned {response.status_code}: {response.text[:200]}"
            )

    @pytest.mark.asyncio
    async def test_mission_detail_endpoint_is_reachable(self, superuser_client: AsyncClient):
        """GET /runtime/mission-state/{id} must return 404 for unknown id (not 500)."""
        response = await superuser_client.get(
            f"{BASE}/runtime/mission-state/probe-mission-id"
        )
        assert response.status_code in (404, 200)

    @pytest.mark.asyncio
    async def test_post_endpoints_reject_empty_body(self, superuser_client: AsyncClient):
        """POST endpoints must return 4xx for empty/invalid bodies (not 500)."""
        post_endpoints = [
            f"{BASE}/runtime/mission-state/bootstrap-closeout-receipt",
            f"{BASE}/active-board/prepare-completion-write",
            f"{BASE}/active-board/write-completion",
            f"{BASE}/overnight-queue/write-entry",
        ]
        for path in post_endpoints:
            response = await superuser_client.post(path, json={})
            assert response.status_code < 500, (
                f"POST {path} with empty body returned {response.status_code}: {response.text[:200]}"
            )

    @pytest.mark.asyncio
    async def test_put_active_board_endpoint_is_reachable(self, superuser_client: AsyncClient):
        """PUT /active-board must return 4xx for invalid body (not 500)."""
        response = await superuser_client.put(f"{BASE}/active-board", json={})
        assert response.status_code < 500

    @pytest.mark.asyncio
    async def test_restore_version_endpoint_is_reachable(self, superuser_client: AsyncClient):
        """POST /active-board/versions/{id}/restore must return 4xx for unknown id (not 500)."""
        response = await superuser_client.post(
            f"{BASE}/active-board/versions/999999/restore",
            json={"concurrency_token": "a" * 64},
        )
        assert response.status_code < 500

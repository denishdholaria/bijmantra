"""Extension integration verification tests for the BeingBijMantra VS Code extension.

These tests verify that the API contract the BeingBijMantra extension depends on
is preserved after the control-plane kernel extraction.  They are **schema
verification tests** — no running server is required.

What is verified:
1. The router has all expected endpoint paths registered.
2. All API schema models the extension imports are available with expected fields.
3. Critical response schemas have the exact field structure the extension expects.
4. Request schemas (queue write, completion write) have the expected fields.
5. Optimistic locking fields (concurrency_token, queue_sha256) are present.

Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
"""

from __future__ import annotations

import pytest

from app.control_plane.contracts.api_schema import (
    # Critical response schemas the extension depends on
    DeveloperControlPlaneActiveBoardFetchResponse,
    DeveloperControlPlaneActiveBoardRecordResponse,
    DeveloperControlPlaneAutonomyCycleResponse,
    DeveloperControlPlaneAutonomyCycleWatchdogResponse,
    DeveloperControlPlaneCloseoutReceiptResponse,
    DeveloperControlPlaneLearningEntryResponse,
    DeveloperControlPlaneLearningLedgerResponse,
    DeveloperControlPlaneOvernightQueueStatusResponse,
    DeveloperControlPlaneWatchdogStatusResponse,
    # Request schemas the extension sends
    DeveloperControlPlaneOvernightQueueWriteRequest,
    DeveloperControlPlaneCompletionWriteRequest,
    DeveloperControlPlaneLaneCompletionPayload,
    # Write response schemas
    DeveloperControlPlaneOvernightQueueWriteResponse,
    DeveloperControlPlaneCompletionWriteResponse,
)


# ===================================================================
# 1. Router endpoint path verification
# ===================================================================


class TestRouterEndpointPaths:
    """Verify the router has all endpoint paths the extension depends on.

    Validates: Requirements 14.1
    """

    @pytest.fixture(scope="class")
    def route_paths(self) -> set[str]:
        """Collect all registered route paths from the composed router."""
        from app.control_plane.api.developer_control_plane_router import router

        return {route.path for route in router.routes if hasattr(route, "path")}

    def test_active_board_endpoint_registered(self, route_paths: set[str]):
        assert "/developer-control-plane/active-board" in route_paths

    def test_queue_status_endpoint_registered(self, route_paths: set[str]):
        assert "/developer-control-plane/overnight-queue/status" in route_paths

    def test_queue_write_entry_endpoint_registered(self, route_paths: set[str]):
        assert "/developer-control-plane/overnight-queue/write-entry" in route_paths

    def test_watchdog_status_endpoint_registered(self, route_paths: set[str]):
        assert "/developer-control-plane/runtime/watchdog-status" in route_paths

    def test_autonomy_cycle_endpoint_registered(self, route_paths: set[str]):
        assert "/developer-control-plane/runtime/autonomy-cycle" in route_paths

    def test_learnings_endpoint_registered(self, route_paths: set[str]):
        assert "/developer-control-plane/learnings" in route_paths

    def test_closeout_receipt_endpoint_registered(self, route_paths: set[str]):
        matching = [
            p for p in route_paths
            if "overnight-queue/jobs/" in p and "closeout-receipt" in p
        ]
        assert len(matching) >= 1, (
            "Expected at least one closeout-receipt endpoint, "
            f"found: {route_paths}"
        )


# ===================================================================
# 2. Schema importability and field structure
# ===================================================================


class TestActiveBoardSchemaContract:
    """Verify the active-board response schema the extension reads.

    Validates: Requirements 14.1, 14.2
    """

    def test_fetch_response_has_expected_fields(self):
        fields = set(DeveloperControlPlaneActiveBoardFetchResponse.model_fields.keys())
        assert {"exists", "record"} == fields

    def test_record_response_has_expected_fields(self):
        fields = set(DeveloperControlPlaneActiveBoardRecordResponse.model_fields.keys())
        expected = {
            "id", "organization_id", "board_id", "schema_version",
            "visibility", "canonical_board_json", "concurrency_token",
            "updated_by_user_id", "updated_at", "save_source",
            "summary_metadata", "created_at",
        }
        assert expected.issubset(fields), (
            f"Missing fields: {expected - fields}"
        )

    def test_record_has_concurrency_token_field(self):
        """The extension uses concurrency_token for optimistic locking."""
        fields = DeveloperControlPlaneActiveBoardRecordResponse.model_fields
        assert "concurrency_token" in fields
        assert fields["concurrency_token"].annotation is str


# ===================================================================
# 3. Critical response schema field structures
# ===================================================================


class TestQueueStatusSchemaContract:
    """Verify the queue-status response schema.

    Validates: Requirements 14.3
    """

    def test_has_expected_fields(self):
        fields = set(DeveloperControlPlaneOvernightQueueStatusResponse.model_fields.keys())
        expected = {"queue_path", "queue_sha256", "exists", "job_count", "updated_at"}
        assert expected == fields

    def test_has_queue_sha256_for_optimistic_locking(self):
        """The extension uses queue_sha256 for optimistic locking on writes."""
        fields = DeveloperControlPlaneOvernightQueueStatusResponse.model_fields
        assert "queue_sha256" in fields


class TestWatchdogStatusSchemaContract:
    """Verify the watchdog-status response schema (IDE presence heartbeat).

    Validates: Requirements 14.4
    """

    def test_has_expected_fields(self):
        fields = set(DeveloperControlPlaneWatchdogStatusResponse.model_fields.keys())
        expected = {
            "exists", "state_path", "auth_store_exists", "auth_store_path",
            "bootstrap_ready", "bootstrap_status",
            "mission_evidence_dir_exists", "mission_evidence_dir_path",
            "last_check", "state_age_seconds", "state_is_stale",
            "gateway_healthy", "total_checks", "total_alerts",
            "job_count", "jobs", "completion_assist_advisory",
        }
        assert expected == fields

    def test_has_heartbeat_fields(self):
        """The extension checks these fields for IDE presence heartbeat."""
        fields = DeveloperControlPlaneWatchdogStatusResponse.model_fields
        for field_name in ("exists", "last_check", "state_is_stale", "gateway_healthy"):
            assert field_name in fields, f"Missing heartbeat field: {field_name}"


class TestAutonomyCycleSchemaContract:
    """Verify the autonomy-cycle response schema.

    Validates: Requirements 14.5
    """

    def test_has_expected_fields(self):
        fields = set(DeveloperControlPlaneAutonomyCycleResponse.model_fields.keys())
        expected = {
            "exists", "artifact_path", "generated_at", "queue_path",
            "window", "max_jobs_per_run", "status_counts",
            "selected_job_count", "blocked_job_count",
            "closeout_candidate_count", "next_action_count",
            "next_action_ordering_source", "watchdog",
            "selected_jobs", "blocked_jobs", "closeout_candidates",
            "next_actions", "first_actionable_completion_write",
        }
        assert expected == fields

    def test_has_next_actions_list(self):
        """The extension reads next_actions for ordering."""
        fields = DeveloperControlPlaneAutonomyCycleResponse.model_fields
        assert "next_actions" in fields
        assert "next_action_ordering_source" in fields

    def test_watchdog_subschema_has_expected_fields(self):
        fields = set(DeveloperControlPlaneAutonomyCycleWatchdogResponse.model_fields.keys())
        expected = {
            "exists", "state_path", "last_check",
            "gateway_healthy", "state_is_stale", "total_alerts", "job_errors",
        }
        assert expected == fields


class TestLearningsSchemaContract:
    """Verify the learning-ledger response schema.

    Validates: Requirements 14.5
    """

    def test_ledger_has_expected_fields(self):
        fields = set(DeveloperControlPlaneLearningLedgerResponse.model_fields.keys())
        assert {"total_count", "entries"} == fields

    def test_entry_has_expected_fields(self):
        fields = set(DeveloperControlPlaneLearningEntryResponse.model_fields.keys())
        expected = {
            "learning_entry_id", "organization_id", "entry_type",
            "source_classification", "title", "summary",
            "confidence_score", "recorded_by_user_id", "recorded_by_email",
            "board_id", "source_lane_id", "queue_job_id",
            "linked_mission_id", "approval_receipt_id",
            "source_reference", "evidence_refs", "summary_metadata",
            "recorded_at",
        }
        assert expected == fields


class TestCloseoutReceiptSchemaContract:
    """Verify the closeout-receipt response schema.

    Validates: Requirements 14.3
    """

    def test_has_expected_fields(self):
        fields = set(DeveloperControlPlaneCloseoutReceiptResponse.model_fields.keys())
        expected = {
            "exists", "queue_job_id", "mission_id", "producer_key",
            "source_lane_id", "source_board_concurrency_token",
            "runtime_profile_id", "runtime_policy_sha256",
            "closeout_status", "state_refresh_required",
            "receipt_recorded_at", "started_at", "finished_at",
            "verification_evidence_ref", "queue_sha256_at_closeout",
            "closeout_commands", "artifacts",
        }
        assert expected == fields

    def test_has_provenance_fields(self):
        """The extension uses these to trace provenance back to the board."""
        fields = DeveloperControlPlaneCloseoutReceiptResponse.model_fields
        assert "source_lane_id" in fields
        assert "source_board_concurrency_token" in fields
        assert "queue_sha256_at_closeout" in fields


# ===================================================================
# 4. Queue write request schema
# ===================================================================


class TestQueueWriteRequestSchemaContract:
    """Verify the queue write request schema the extension sends.

    Validates: Requirements 14.3
    """

    def test_has_expected_fields(self):
        fields = set(DeveloperControlPlaneOvernightQueueWriteRequest.model_fields.keys())
        expected = {
            "source_board_concurrency_token",
            "expected_queue_sha256",
            "operator_intent",
            "queue_entry",
        }
        assert expected == fields

    def test_has_optimistic_locking_fields(self):
        """The extension sends these for optimistic locking."""
        fields = DeveloperControlPlaneOvernightQueueWriteRequest.model_fields
        assert "source_board_concurrency_token" in fields
        assert "expected_queue_sha256" in fields

    def test_write_response_has_expected_fields(self):
        fields = set(DeveloperControlPlaneOvernightQueueWriteResponse.model_fields.keys())
        expected = {
            "queue_sha256", "queue_updated_at", "written_job_id",
            "replaced", "approval_receipt",
        }
        assert expected == fields

    def test_write_response_has_queue_sha256(self):
        """The extension reads queue_sha256 from the response for subsequent locking."""
        fields = DeveloperControlPlaneOvernightQueueWriteResponse.model_fields
        assert "queue_sha256" in fields


# ===================================================================
# 5. Completion write request schema
# ===================================================================


class TestCompletionWriteRequestSchemaContract:
    """Verify the completion write request schema the extension sends.

    Validates: Requirements 14.3
    """

    def test_request_has_expected_fields(self):
        fields = set(DeveloperControlPlaneCompletionWriteRequest.model_fields.keys())
        expected = {
            "source_board_concurrency_token",
            "expected_queue_sha256",
            "operator_intent",
            "completion",
        }
        assert expected == fields

    def test_completion_payload_has_expected_fields(self):
        fields = set(DeveloperControlPlaneLaneCompletionPayload.model_fields.keys())
        expected = {
            "source_lane_id", "queue_job_id", "closure_summary",
            "evidence", "closeout_receipt",
        }
        assert expected == fields

    def test_request_has_optimistic_locking_fields(self):
        """The extension sends these for optimistic locking on completion writes."""
        fields = DeveloperControlPlaneCompletionWriteRequest.model_fields
        assert "source_board_concurrency_token" in fields
        assert "expected_queue_sha256" in fields

    def test_write_response_has_expected_fields(self):
        fields = set(DeveloperControlPlaneCompletionWriteResponse.model_fields.keys())
        expected = {
            "no_op", "lane_id", "lane_status", "queue_job_id",
            "queue_sha256", "record", "approval_receipt",
        }
        assert expected == fields

    def test_write_response_has_queue_sha256(self):
        """The extension reads queue_sha256 from the completion response."""
        fields = DeveloperControlPlaneCompletionWriteResponse.model_fields
        assert "queue_sha256" in fields


# ===================================================================
# 6. Optimistic locking fields across schemas
# ===================================================================


class TestOptimisticLockingFieldsPresent:
    """Verify that optimistic locking fields are present in all schemas
    that participate in the concurrency control protocol.

    Validates: Requirements 14.3
    """

    def test_board_record_has_concurrency_token(self):
        fields = DeveloperControlPlaneActiveBoardRecordResponse.model_fields
        assert "concurrency_token" in fields

    def test_queue_status_has_queue_sha256(self):
        fields = DeveloperControlPlaneOvernightQueueStatusResponse.model_fields
        assert "queue_sha256" in fields

    def test_queue_write_request_has_expected_queue_sha256(self):
        fields = DeveloperControlPlaneOvernightQueueWriteRequest.model_fields
        assert "expected_queue_sha256" in fields

    def test_queue_write_response_has_queue_sha256(self):
        fields = DeveloperControlPlaneOvernightQueueWriteResponse.model_fields
        assert "queue_sha256" in fields

    def test_completion_write_request_has_board_token_and_queue_sha(self):
        fields = DeveloperControlPlaneCompletionWriteRequest.model_fields
        assert "source_board_concurrency_token" in fields
        assert "expected_queue_sha256" in fields

    def test_completion_write_response_has_queue_sha256(self):
        fields = DeveloperControlPlaneCompletionWriteResponse.model_fields
        assert "queue_sha256" in fields

    def test_closeout_receipt_has_provenance_tokens(self):
        fields = DeveloperControlPlaneCloseoutReceiptResponse.model_fields
        assert "source_board_concurrency_token" in fields
        assert "queue_sha256_at_closeout" in fields

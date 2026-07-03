"""Contract tests for the developer control-plane frozen API schemas.

These tests verify the Pydantic models in
``app.control_plane.contracts.api_schema`` at the **schema level** — no HTTP
server is involved.  They ensure:

1. Each critical response schema can be instantiated with valid data.
2. Each critical request schema validates correctly (accepts valid, rejects
   invalid).
3. Error / conflict response schemas are correct.
4. Schema field names, types, and nesting match expectations.

Requirements: 13.1, 13.2, 13.3
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.control_plane.contracts.api_schema import (
    # Response schemas for the 7 critical endpoints
    DeveloperControlPlaneActiveBoardFetchResponse,
    DeveloperControlPlaneActiveBoardRecordResponse,
    DeveloperControlPlaneAutonomyCycleResponse,
    DeveloperControlPlaneAutonomyCycleWatchdogResponse,
    DeveloperControlPlaneCloseoutReceiptResponse,
    DeveloperControlPlaneLearningEntryResponse,
    DeveloperControlPlaneLearningLedgerResponse,
    DeveloperControlPlaneOvernightQueueStatusResponse,
    DeveloperControlPlaneOvernightQueueWriteResponse,
    DeveloperControlPlaneWatchdogStatusResponse,
    # Request schemas
    DeveloperControlPlaneActiveBoardSaveRequest,
    DeveloperControlPlaneCompletionWriteRequest,
    DeveloperControlPlaneLaneCompletionPayload,
    DeveloperControlPlaneOvernightQueueWriteRequest,
    DeveloperControlPlaneMissionBootstrapRequest,
    DeveloperControlPlaneBoardRestoreRequest,
    DeveloperControlPlaneCompletionWritePreparationRequest,
    # Error / conflict schemas
    DeveloperControlPlaneActiveBoardConflictResponse,
    # Nested schemas used in responses
    DeveloperControlPlaneApprovalReceiptResponse,
    DeveloperControlPlaneCompletionWriteResponse,
    DeveloperControlPlaneMissionStateResponse,
    DeveloperControlPlaneSilentMonitorsResponse,
)


# ---------------------------------------------------------------------------
# Helpers — minimal valid data factories
# ---------------------------------------------------------------------------

_NOW = datetime.now(timezone.utc)


def _active_board_record_data() -> dict:
    return {
        "id": 1,
        "organization_id": 1,
        "board_id": "bijmantra-app-development-master-board",
        "schema_version": "1.0.0",
        "visibility": "internal-superuser",
        "canonical_board_json": '{"version":"1.0.0","lanes":[]}',
        "concurrency_token": "sha256-abc123",
        "updated_by_user_id": 1,
        "updated_at": _NOW,
        "save_source": "direct-ui",
        "summary_metadata": {"lane_count": 0},
        "created_at": _NOW,
    }


def _approval_receipt_data() -> dict:
    return {
        "receipt_id": 1,
        "organization_id": 1,
        "action_type": "write-reviewed-queue-entry",
        "outcome": "approved",
        "authority_actor_user_id": 1,
        "authority_source": "superuser",
        "board_id": "bijmantra-app-development-master-board",
        "rationale": "Reviewed and approved",
        "recorded_at": _NOW,
    }


# ===================================================================
# 1. Critical response schemas — valid instantiation
# ===================================================================


class TestActiveBoardFetchResponseContract:
    """GET /api/v2/developer-control-plane/active-board"""

    def test_instantiate_with_no_record(self):
        resp = DeveloperControlPlaneActiveBoardFetchResponse(
            exists=False, record=None
        )
        assert resp.exists is False
        assert resp.record is None

    def test_instantiate_with_record(self):
        resp = DeveloperControlPlaneActiveBoardFetchResponse(
            exists=True,
            record=DeveloperControlPlaneActiveBoardRecordResponse(
                **_active_board_record_data()
            ),
        )
        assert resp.exists is True
        assert resp.record is not None
        assert resp.record.board_id == "bijmantra-app-development-master-board"
        assert resp.record.concurrency_token == "sha256-abc123"

    def test_field_names_and_types(self):
        fields = DeveloperControlPlaneActiveBoardFetchResponse.model_fields
        assert "exists" in fields
        assert "record" in fields

    def test_record_field_names(self):
        fields = DeveloperControlPlaneActiveBoardRecordResponse.model_fields
        expected = {
            "id", "organization_id", "board_id", "schema_version",
            "visibility", "canonical_board_json", "concurrency_token",
            "updated_by_user_id", "updated_at", "save_source",
            "summary_metadata", "created_at",
        }
        assert expected.issubset(set(fields.keys()))


class TestOvernightQueueStatusResponseContract:
    """GET /api/v2/developer-control-plane/overnight-queue/status"""

    def test_instantiate_with_valid_data(self):
        resp = DeveloperControlPlaneOvernightQueueStatusResponse(
            queue_path="/tmp/queue.json",
            queue_sha256="abc123",
            exists=True,
            job_count=3,
            updated_at="2026-03-18T00:00:00Z",
        )
        assert resp.exists is True
        assert resp.job_count == 3

    def test_instantiate_empty_queue(self):
        resp = DeveloperControlPlaneOvernightQueueStatusResponse(
            queue_path="/tmp/queue.json",
            queue_sha256="empty-sha",
            exists=False,
            job_count=0,
            updated_at=None,
        )
        assert resp.exists is False
        assert resp.updated_at is None

    def test_field_names(self):
        fields = DeveloperControlPlaneOvernightQueueStatusResponse.model_fields
        expected = {"queue_path", "queue_sha256", "exists", "job_count", "updated_at"}
        assert expected == set(fields.keys())


class TestOvernightQueueWriteResponseContract:
    """POST /api/v2/developer-control-plane/overnight-queue/write-entry"""

    def test_instantiate_without_receipt(self):
        resp = DeveloperControlPlaneOvernightQueueWriteResponse(
            queue_sha256="new-sha",
            queue_updated_at="2026-03-18T01:00:00Z",
            written_job_id="job-1",
            replaced=False,
        )
        assert resp.replaced is False
        assert resp.approval_receipt is None

    def test_instantiate_with_receipt(self):
        resp = DeveloperControlPlaneOvernightQueueWriteResponse(
            queue_sha256="new-sha",
            queue_updated_at="2026-03-18T01:00:00Z",
            written_job_id="job-1",
            replaced=True,
            approval_receipt=DeveloperControlPlaneApprovalReceiptResponse(
                **_approval_receipt_data()
            ),
        )
        assert resp.replaced is True
        assert resp.approval_receipt is not None
        assert resp.approval_receipt.action_type == "write-reviewed-queue-entry"

    def test_field_names(self):
        fields = DeveloperControlPlaneOvernightQueueWriteResponse.model_fields
        expected = {
            "queue_sha256", "queue_updated_at", "written_job_id",
            "replaced", "approval_receipt",
        }
        assert expected == set(fields.keys())


class TestWatchdogStatusResponseContract:
    """GET /api/v2/developer-control-plane/runtime/watchdog-status"""

    def test_instantiate_minimal(self):
        resp = DeveloperControlPlaneWatchdogStatusResponse(
            exists=False,
            state_path="/tmp/watchdog.json",
            auth_store_exists=False,
            auth_store_path="/tmp/auth.json",
            bootstrap_ready=False,
            bootstrap_status="not-ready",
            mission_evidence_dir_exists=False,
            mission_evidence_dir_path="/tmp/evidence",
        )
        assert resp.exists is False
        assert resp.jobs == []
        assert resp.total_checks == 0

    def test_instantiate_full(self):
        resp = DeveloperControlPlaneWatchdogStatusResponse(
            exists=True,
            state_path="/tmp/watchdog.json",
            auth_store_exists=True,
            auth_store_path="/tmp/auth.json",
            bootstrap_ready=True,
            bootstrap_status="ready",
            mission_evidence_dir_exists=True,
            mission_evidence_dir_path="/tmp/evidence",
            last_check="2026-03-18T00:00:00Z",
            state_age_seconds=120,
            state_is_stale=False,
            gateway_healthy=True,
            total_checks=10,
            total_alerts=0,
            job_count=2,
            jobs=[],
        )
        assert resp.bootstrap_ready is True
        assert resp.job_count == 2

    def test_field_names(self):
        fields = DeveloperControlPlaneWatchdogStatusResponse.model_fields
        expected = {
            "exists", "state_path", "auth_store_exists", "auth_store_path",
            "bootstrap_ready", "bootstrap_status", "mission_evidence_dir_exists",
            "mission_evidence_dir_path", "last_check", "state_age_seconds",
            "state_is_stale", "gateway_healthy", "total_checks", "total_alerts",
            "job_count", "jobs", "completion_assist_advisory",
        }
        assert expected == set(fields.keys())


class TestAutonomyCycleResponseContract:
    """GET /api/v2/developer-control-plane/runtime/autonomy-cycle"""

    def test_instantiate_minimal(self):
        resp = DeveloperControlPlaneAutonomyCycleResponse(
            exists=False,
            artifact_path="/tmp/autonomy.json",
            next_action_ordering_source="default",
            watchdog=DeveloperControlPlaneAutonomyCycleWatchdogResponse(
                exists=False,
                state_path="/tmp/watchdog.json",
            ),
        )
        assert resp.exists is False
        assert resp.selected_jobs == []
        assert resp.next_actions == []
        assert resp.first_actionable_completion_write is None

    def test_field_names(self):
        fields = DeveloperControlPlaneAutonomyCycleResponse.model_fields
        expected = {
            "exists", "artifact_path", "generated_at", "queue_path",
            "window", "max_jobs_per_run", "status_counts",
            "selected_job_count", "blocked_job_count",
            "closeout_candidate_count", "next_action_count",
            "next_action_ordering_source", "watchdog",
            "selected_jobs", "blocked_jobs", "closeout_candidates",
            "next_actions", "first_actionable_completion_write",
        }
        assert expected == set(fields.keys())


class TestLearningLedgerResponseContract:
    """GET /api/v2/developer-control-plane/learnings"""

    def test_instantiate_empty(self):
        resp = DeveloperControlPlaneLearningLedgerResponse(
            total_count=0, entries=[]
        )
        assert resp.total_count == 0
        assert resp.entries == []

    def test_instantiate_with_entries(self):
        entry = DeveloperControlPlaneLearningEntryResponse(
            learning_entry_id=1,
            organization_id=1,
            entry_type="conflict",
            source_classification="queue-write",
            title="Stale token conflict",
            summary="Board token was stale during queue write",
            recorded_at=_NOW,
        )
        resp = DeveloperControlPlaneLearningLedgerResponse(
            total_count=1, entries=[entry]
        )
        assert resp.total_count == 1
        assert resp.entries[0].entry_type == "conflict"

    def test_field_names(self):
        fields = DeveloperControlPlaneLearningLedgerResponse.model_fields
        assert {"total_count", "entries"} == set(fields.keys())

    def test_entry_field_names(self):
        fields = DeveloperControlPlaneLearningEntryResponse.model_fields
        expected = {
            "learning_entry_id", "organization_id", "entry_type",
            "source_classification", "title", "summary",
            "confidence_score", "recorded_by_user_id", "recorded_by_email",
            "board_id", "source_lane_id", "queue_job_id",
            "linked_mission_id", "approval_receipt_id",
            "source_reference", "evidence_refs", "summary_metadata",
            "recorded_at",
        }
        assert expected == set(fields.keys())


class TestCloseoutReceiptResponseContract:
    """GET /api/v2/developer-control-plane/overnight-queue/jobs/{job_id}/closeout-receipt"""

    def test_instantiate_not_found(self):
        resp = DeveloperControlPlaneCloseoutReceiptResponse(
            exists=False, queue_job_id="missing-job"
        )
        assert resp.exists is False
        assert resp.closeout_commands == []
        assert resp.artifacts == []

    def test_instantiate_full(self):
        resp = DeveloperControlPlaneCloseoutReceiptResponse(
            exists=True,
            queue_job_id="job-1",
            mission_id="mission-1",
            producer_key="openclaw-runtime",
            source_lane_id="control-plane",
            source_board_concurrency_token="token-abc",
            closeout_status="passed",
            started_at="2026-03-18T00:00:00Z",
            finished_at="2026-03-18T00:05:00Z",
        )
        assert resp.exists is True
        assert resp.closeout_status == "passed"

    def test_field_names(self):
        fields = DeveloperControlPlaneCloseoutReceiptResponse.model_fields
        expected = {
            "exists", "queue_job_id", "mission_id", "producer_key",
            "source_lane_id", "source_board_concurrency_token",
            "runtime_profile_id", "runtime_policy_sha256",
            "closeout_status", "state_refresh_required",
            "receipt_recorded_at", "started_at", "finished_at",
            "verification_evidence_ref", "queue_sha256_at_closeout",
            "closeout_commands", "artifacts",
        }
        assert expected == set(fields.keys())


# ===================================================================
# 2. Request schema validation — accepts valid, rejects invalid
# ===================================================================


class TestOvernightQueueWriteRequestValidation:
    """Request validation for POST /overnight-queue/write-entry"""

    def test_accepts_valid_request(self):
        req = DeveloperControlPlaneOvernightQueueWriteRequest(
            source_board_concurrency_token="token-abc",
            expected_queue_sha256="sha-123",
            operator_intent="write-reviewed-queue-entry",
            queue_entry={"jobId": "job-1", "title": "Test"},
        )
        assert req.source_board_concurrency_token == "token-abc"

    def test_rejects_empty_token(self):
        with pytest.raises(ValidationError) as exc_info:
            DeveloperControlPlaneOvernightQueueWriteRequest(
                source_board_concurrency_token="",
                expected_queue_sha256="sha-123",
                operator_intent="write",
                queue_entry={},
            )
        errors = exc_info.value.errors()
        field_names = [e["loc"][-1] for e in errors]
        assert "source_board_concurrency_token" in field_names

    def test_rejects_missing_required_fields(self):
        with pytest.raises(ValidationError):
            DeveloperControlPlaneOvernightQueueWriteRequest()  # type: ignore[call-arg]

    def test_rejects_oversized_token(self):
        with pytest.raises(ValidationError):
            DeveloperControlPlaneOvernightQueueWriteRequest(
                source_board_concurrency_token="x" * 200,
                expected_queue_sha256="sha-123",
                operator_intent="write",
                queue_entry={},
            )


class TestActiveBoardSaveRequestValidation:
    """Request validation for PUT /active-board"""

    def test_accepts_valid_request(self):
        req = DeveloperControlPlaneActiveBoardSaveRequest(
            canonical_board_json='{"version":"1.0.0"}',
            save_source="direct-ui",
        )
        assert req.concurrency_token is None

    def test_accepts_with_concurrency_token(self):
        req = DeveloperControlPlaneActiveBoardSaveRequest(
            canonical_board_json='{"version":"1.0.0"}',
            save_source="direct-ui",
            concurrency_token="sha256-abc",
        )
        assert req.concurrency_token == "sha256-abc"

    def test_rejects_empty_board_json(self):
        with pytest.raises(ValidationError):
            DeveloperControlPlaneActiveBoardSaveRequest(
                canonical_board_json="",
                save_source="direct-ui",
            )

    def test_rejects_single_char_board_json(self):
        with pytest.raises(ValidationError):
            DeveloperControlPlaneActiveBoardSaveRequest(
                canonical_board_json="{",
                save_source="direct-ui",
            )

    def test_rejects_empty_save_source(self):
        with pytest.raises(ValidationError):
            DeveloperControlPlaneActiveBoardSaveRequest(
                canonical_board_json='{"version":"1.0.0"}',
                save_source="",
            )


class TestCompletionWriteRequestValidation:
    """Request validation for POST /active-board/write-completion"""

    def test_accepts_valid_request(self):
        req = DeveloperControlPlaneCompletionWriteRequest(
            source_board_concurrency_token="token-abc",
            expected_queue_sha256="sha-123",
            operator_intent="write-reviewed-lane-completion",
            completion=DeveloperControlPlaneLaneCompletionPayload(
                source_lane_id="control-plane",
                queue_job_id="job-1",
                closure_summary="Lane completed successfully",
                evidence=["tests passed"],
            ),
        )
        assert req.completion.source_lane_id == "control-plane"

    def test_rejects_empty_evidence_list(self):
        with pytest.raises(ValidationError):
            DeveloperControlPlaneCompletionWriteRequest(
                source_board_concurrency_token="token-abc",
                expected_queue_sha256="sha-123",
                operator_intent="write",
                completion=DeveloperControlPlaneLaneCompletionPayload(
                    source_lane_id="control-plane",
                    queue_job_id="job-1",
                    closure_summary="Lane completed",
                    evidence=[],
                ),
            )

    def test_rejects_missing_completion(self):
        with pytest.raises(ValidationError):
            DeveloperControlPlaneCompletionWriteRequest(
                source_board_concurrency_token="token-abc",
                expected_queue_sha256="sha-123",
                operator_intent="write",
            )  # type: ignore[call-arg]


class TestMissionBootstrapRequestValidation:
    """Request validation for POST /missions/bootstrap"""

    def test_accepts_valid_request(self):
        req = DeveloperControlPlaneMissionBootstrapRequest(
            queue_job_id="job-1",
        )
        assert req.queue_job_id == "job-1"

    def test_rejects_empty_job_id(self):
        with pytest.raises(ValidationError):
            DeveloperControlPlaneMissionBootstrapRequest(queue_job_id="")

    def test_rejects_oversized_job_id(self):
        with pytest.raises(ValidationError):
            DeveloperControlPlaneMissionBootstrapRequest(
                queue_job_id="x" * 300
            )


class TestBoardRestoreRequestValidation:
    """Request validation for POST /active-board/versions/{id}/restore"""

    def test_accepts_null_token(self):
        req = DeveloperControlPlaneBoardRestoreRequest(concurrency_token=None)
        assert req.concurrency_token is None

    def test_accepts_valid_token(self):
        req = DeveloperControlPlaneBoardRestoreRequest(
            concurrency_token="sha256-abc"
        )
        assert req.concurrency_token == "sha256-abc"

    def test_rejects_empty_token(self):
        with pytest.raises(ValidationError):
            DeveloperControlPlaneBoardRestoreRequest(concurrency_token="")


class TestCompletionWritePreparationRequestValidation:
    """Request validation for POST /active-board/prepare-completion-write"""

    def test_accepts_valid_request(self):
        req = DeveloperControlPlaneCompletionWritePreparationRequest(
            source_lane_id="control-plane"
        )
        assert req.source_lane_id == "control-plane"

    def test_rejects_empty_lane_id(self):
        with pytest.raises(ValidationError):
            DeveloperControlPlaneCompletionWritePreparationRequest(
                source_lane_id=""
            )


# ===================================================================
# 3. Error / conflict response schemas
# ===================================================================


class TestActiveBoardConflictResponseContract:
    """Conflict response for stale concurrency token on board save."""

    def test_instantiate(self):
        resp = DeveloperControlPlaneActiveBoardConflictResponse(
            detail="Active board save conflict; refetch the current board before retrying",
            current_record=DeveloperControlPlaneActiveBoardRecordResponse(
                **_active_board_record_data()
            ),
        )
        assert "conflict" in resp.detail.lower()
        assert resp.current_record.concurrency_token == "sha256-abc123"

    def test_field_names(self):
        fields = DeveloperControlPlaneActiveBoardConflictResponse.model_fields
        assert {"detail", "current_record"} == set(fields.keys())


class TestCompletionWriteResponseContract:
    """Response for POST /active-board/write-completion"""

    def test_instantiate(self):
        resp = DeveloperControlPlaneCompletionWriteResponse(
            no_op=False,
            lane_id="control-plane",
            lane_status="completed",
            queue_job_id="job-1",
            queue_sha256="sha-after",
            record=DeveloperControlPlaneActiveBoardRecordResponse(
                **_active_board_record_data()
            ),
        )
        assert resp.no_op is False
        assert resp.lane_status == "completed"

    def test_field_names(self):
        fields = DeveloperControlPlaneCompletionWriteResponse.model_fields
        expected = {
            "no_op", "lane_id", "lane_status", "queue_job_id",
            "queue_sha256", "record", "approval_receipt",
        }
        assert expected == set(fields.keys())


class TestMissionStateResponseContract:
    """Response for GET /missions/state"""

    def test_instantiate_empty(self):
        resp = DeveloperControlPlaneMissionStateResponse(
            count=0, missions=[]
        )
        assert resp.count == 0

    def test_field_names(self):
        fields = DeveloperControlPlaneMissionStateResponse.model_fields
        assert {"count", "missions"} == set(fields.keys())


class TestSilentMonitorsResponseContract:
    """Response for GET /runtime/silent-monitors"""

    def test_instantiate(self):
        resp = DeveloperControlPlaneSilentMonitorsResponse(
            generated_at="2026-03-18T00:00:00Z",
            overall_state="healthy",
        )
        assert resp.overall_state == "healthy"
        assert resp.monitors == []

    def test_field_names(self):
        fields = DeveloperControlPlaneSilentMonitorsResponse.model_fields
        expected = {"generated_at", "overall_state", "should_emit", "monitors"}
        assert expected == set(fields.keys())


# ===================================================================
# 4. Approval receipt schema (shared across multiple responses)
# ===================================================================


class TestApprovalReceiptResponseContract:
    """Approval receipt is embedded in queue write and completion responses."""

    def test_instantiate_minimal(self):
        resp = DeveloperControlPlaneApprovalReceiptResponse(
            **_approval_receipt_data()
        )
        assert resp.receipt_id == 1
        assert resp.evidence_refs == []

    def test_instantiate_full(self):
        data = _approval_receipt_data()
        data.update(
            authority_actor_email="admin@example.com",
            source_board_concurrency_token="token-before",
            resulting_board_concurrency_token="token-after",
            source_lane_id="control-plane",
            queue_job_id="job-1",
            expected_queue_sha256="sha-before",
            resulting_queue_sha256="sha-after",
            linked_mission_id="mission-1",
            evidence_refs=["evidence-1.json"],
            summary_metadata={"lane_count": 5},
        )
        resp = DeveloperControlPlaneApprovalReceiptResponse(**data)
        assert resp.source_lane_id == "control-plane"
        assert resp.evidence_refs == ["evidence-1.json"]

    def test_field_names(self):
        fields = DeveloperControlPlaneApprovalReceiptResponse.model_fields
        expected = {
            "receipt_id", "organization_id", "action_type", "outcome",
            "authority_actor_user_id", "authority_actor_email",
            "authority_source", "board_id",
            "source_board_concurrency_token",
            "resulting_board_concurrency_token",
            "source_lane_id", "queue_job_id",
            "expected_queue_sha256", "resulting_queue_sha256",
            "target_revision_id",
            "previous_active_concurrency_token",
            "linked_mission_id", "rationale",
            "evidence_refs", "summary_metadata", "recorded_at",
        }
        assert expected == set(fields.keys())

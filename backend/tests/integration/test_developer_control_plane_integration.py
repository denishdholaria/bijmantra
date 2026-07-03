"""Integration tests for the extracted Control Plane layers.

These tests verify that the domain, application, and orchestration layers
work together correctly after extraction from the monolithic
``developer_control_plane.py``.  They do NOT require a running database —
filesystem operations are mocked where needed.

Requirements: 13.1, 13.4
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from app.control_plane.application.board_service import BoardService
from app.control_plane.application.execution_service import ExecutionService
from app.control_plane.application.lane_service import (
    LaneService,
    build_lane_completion,
    is_same_lane_completion,
)
from app.control_plane.domain.board import hash_canonical_board_json
from app.control_plane.domain.lane import (
    find_board_lane,
    has_complete_review_gate,
    lane_has_completion_verification_evidence,
    lane_has_queue_export_reviews,
)
from app.control_plane.domain.mission import (
    MissionLinkage,
    parse_completion_source_request,
)
from app.control_plane.domain.validation import (
    DomainValidationError,
    DuplicateJobIdError,
    validate_queue_entry,
    validate_queue_payload_shape,
)
from app.control_plane.orchestration.queue_materializer import QueueMaterializer


# ---------------------------------------------------------------------------
# Helpers — reusable test data builders
# ---------------------------------------------------------------------------


def _make_valid_queue_entry(
    *,
    job_id: str = "overnight-lane-test-lane-1-abc12345",
    source_lane_id: str = "test-lane-1",
    board_token: str = "abc12345def67890",
) -> dict[str, Any]:
    """Build a minimal valid queue entry with provenance."""
    return {
        "jobId": job_id,
        "title": "Test lane extraction task",
        "status": "queued",
        "priority": "p2",
        "primaryAgent": "OmShriMaatreNamaha",
        "supportAgents": ["OmNamoNarayanaya"],
        "executionMode": "same-control-plane",
        "autonomousTrigger": {
            "type": "overnight-window",
            "window": "nightly",
            "enabled": True,
        },
        "dependsOn": [],
        "goal": "Extract and verify control plane kernel",
        "lane": {
            "objective": "Complete kernel extraction",
            "inputs": ["developer_control_plane.py"],
            "outputs": ["control_plane/domain/board.py"],
            "dependencies": ["board schema"],
            "completion_criteria": ["All tests pass"],
        },
        "successCriteria": ["Tests pass", "No regressions"],
        "verification": {
            "commands": ["make test"],
            "stateRefreshRequired": True,
        },
        "provenance": {
            "candidateVersion": "v1",
            "exportedAt": "2026-04-20T00:00:00Z",
            "boardId": "developer-master-board",
            "boardTitle": "Developer Master Board",
            "sourceBoardConcurrencyToken": board_token,
            "sourceLaneId": source_lane_id,
            "precedence": {
                "canonicalPlanningSource": "active-board",
                "derivedExecutionSurface": "overnight-queue",
                "exportDisposition": "manual-candidate-only",
                "conflictResolution": "board-wins-no-silent-overwrite",
                "staleIfSourceBoardChanges": True,
            },
        },
    }


def _make_board_payload_with_lanes(
    lanes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a board payload containing the given lanes."""
    return {
        "board_id": "developer-master-board",
        "title": "Developer Master Board",
        "version": "1.0",
        "visibility": "internal-superuser",
        "lanes": lanes,
    }


def _make_lane_with_reviews(
    lane_id: str = "lane-1",
    status: str = "active",
    *,
    has_spec_review: bool = True,
    has_risk_review: bool = True,
    has_verification: bool = False,
) -> dict[str, Any]:
    """Build a lane dict with optional review gates."""
    review_state: dict[str, Any] = {}
    if has_spec_review:
        review_state["spec_review"] = {
            "reviewed_by": "developer@example.com",
            "summary": "Spec review passed",
            "reviewed_at": "2026-04-20T00:00:00Z",
            "evidence": ["spec-review-evidence-1"],
        }
    if has_risk_review:
        review_state["risk_review"] = {
            "reviewed_by": "developer@example.com",
            "summary": "Risk review passed",
            "reviewed_at": "2026-04-20T00:00:00Z",
            "evidence": ["risk-review-evidence-1"],
        }
    if has_verification:
        review_state["verification_evidence"] = {
            "reviewed_by": "developer@example.com",
            "summary": "Verification passed",
            "reviewed_at": "2026-04-20T00:00:00Z",
            "evidence": ["verification-evidence-1"],
        }

    return {
        "id": lane_id,
        "title": f"Lane {lane_id}",
        "status": status,
        "review_state": review_state,
    }


def _make_mock_board_record(**overrides: Any) -> SimpleNamespace:
    """Build a mock board record (duck-typed for BoardService.record_response)."""
    defaults = {
        "id": 1,
        "organization_id": 1,
        "board_id": "developer-master-board",
        "schema_version": "1.0",
        "visibility": "internal-superuser",
        "canonical_board_json": '{"board_id":"developer-master-board"}',
        "canonical_board_hash": "abc123",
        "updated_by_user_id": 1,
        "updated_at": datetime(2026, 4, 20, tzinfo=UTC),
        "save_source": "manual",
        "summary_metadata": {"lane_count": 3},
        "created_at": datetime(2026, 4, 20, tzinfo=UTC),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_mock_approval_receipt(**overrides: Any) -> SimpleNamespace:
    """Build a mock approval receipt record."""
    defaults = {
        "id": 1,
        "organization_id": 1,
        "action_type": "queue-export",
        "outcome": "approved",
        "authority_actor_user_id": 1,
        "authority_actor_email": "dev@example.com",
        "authority_source": "developer-control-plane-api",
        "board_id": "developer-master-board",
        "source_board_concurrency_token": "abc123",
        "resulting_board_concurrency_token": None,
        "source_lane_id": "lane-1",
        "queue_job_id": "overnight-lane-lane-1-abc12345",
        "expected_queue_sha256": "sha256-before",
        "resulting_queue_sha256": "sha256-after",
        "target_revision_id": None,
        "previous_active_concurrency_token": None,
        "linked_mission_id": None,
        "rationale": "Lane reviewed and approved for queue export",
        "evidence_refs": ["developer-control-plane:lane:lane-1"],
        "summary_metadata": None,
        "created_at": datetime(2026, 4, 20, tzinfo=UTC),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ===========================================================================
# Test: Queue write with approval receipt (cross-layer integration)
# ===========================================================================


class TestQueueWriteWithApprovalReceipt:
    """Verify that QueueMaterializer and LaneService work together for
    the queue write workflow: load queue, validate entry, compute SHA256,
    and produce an approval receipt response.

    Requirements: 13.1, 13.4
    """

    def test_queue_load_validate_and_hash(self):
        """QueueMaterializer can load a default payload, validate its shape,
        and compute a deterministic SHA256 hash."""
        payload = QueueMaterializer.default_queue_payload()
        validated = validate_queue_payload_shape(payload)
        sha256 = QueueMaterializer.queue_sha256(validated)

        assert isinstance(sha256, str)
        assert len(sha256) == 64  # SHA-256 hex digest length
        # Hash should be deterministic
        assert sha256 == QueueMaterializer.queue_sha256(validated)

    def test_queue_entry_validation_with_provenance(self):
        """validate_queue_entry accepts a well-formed entry with provenance
        and returns a validated dict preserving provenance fields."""
        entry = _make_valid_queue_entry()
        validated = validate_queue_entry(entry, existing_job_ids=set())

        assert validated["jobId"] == entry["jobId"]
        assert "provenance" in validated
        assert validated["provenance"]["sourceLaneId"] == "test-lane-1"
        assert validated["provenance"]["sourceBoardConcurrencyToken"] == "abc12345def67890"
        assert validated["provenance"]["precedence"]["canonicalPlanningSource"] == "active-board"

    def test_queue_sha256_changes_after_entry_added(self):
        """Adding a validated entry to the queue changes the SHA256 hash,
        enabling optimistic locking."""
        payload = QueueMaterializer.default_queue_payload()
        sha_before = QueueMaterializer.queue_sha256(payload)

        entry = _make_valid_queue_entry()
        validated_entry = validate_queue_entry(entry, existing_job_ids=set())
        payload["jobs"].append(validated_entry)

        sha_after = QueueMaterializer.queue_sha256(payload)
        assert sha_before != sha_after

    def test_approval_receipt_response_from_record(self):
        """LaneService.approval_receipt_response produces a valid API
        response from a mock approval receipt record."""
        record = _make_mock_approval_receipt()
        response = LaneService.approval_receipt_response(record)

        assert response.receipt_id == 1
        assert response.action_type == "queue-export"
        assert response.outcome == "approved"
        assert response.source_lane_id == "lane-1"
        assert response.evidence_refs == ["developer-control-plane:lane:lane-1"]

    def test_queue_write_and_serialize_roundtrip(self):
        """Queue payload survives serialize → parse → re-hash without
        changing the SHA256 (deterministic serialization)."""
        payload = QueueMaterializer.default_queue_payload()
        entry = _make_valid_queue_entry()
        validated_entry = validate_queue_entry(entry, existing_job_ids=set())
        payload["jobs"].append(validated_entry)

        serialized = QueueMaterializer.serialize_queue_payload(payload)
        reparsed = json.loads(serialized)

        # The reparsed payload should produce the same SHA256 as the original
        # when re-serialized through the same deterministic path
        sha_original = QueueMaterializer.queue_sha256(payload)
        sha_reparsed = QueueMaterializer.queue_sha256(reparsed)
        assert sha_original == sha_reparsed


# ===========================================================================
# Test: Completion write-back (cross-layer integration)
# ===========================================================================


class TestCompletionWriteBack:
    """Verify that build_lane_completion and BoardService.record_response
    work together for the completion write-back workflow.

    Requirements: 13.1, 13.4
    """

    def test_board_record_response_produces_valid_api_response(self):
        """BoardService.record_response maps a board record to a valid
        API response with all required fields."""
        record = _make_mock_board_record()
        response = BoardService.record_response(record)

        assert response.id == 1
        assert response.board_id == "developer-master-board"
        assert response.concurrency_token == "abc123"
        assert response.save_source == "manual"
        assert response.summary_metadata == {"lane_count": 3}

    def test_build_lane_completion_produces_valid_closure(self):
        """build_lane_completion produces a closure dict with all required
        fields for board persistence."""
        completion = build_lane_completion(
            queue_job_id="overnight-lane-lane-1-abc12345",
            queue_sha256="sha256hash",
            source_board_concurrency_token="abc123",
            closure_summary="Lane completed successfully",
            evidence=["evidence-1", "evidence-2"],
            closeout_receipt={"queue_job_id": "overnight-lane-lane-1-abc12345"},
        )

        assert completion["queue_job_id"] == "overnight-lane-lane-1-abc12345"
        assert completion["queue_sha256"] == "sha256hash"
        assert completion["source_board_concurrency_token"] == "abc123"
        assert completion["closure_summary"] == "Lane completed successfully"
        assert len(completion["evidence"]) == 2
        assert "completed_at" in completion
        assert "closeout_receipt" in completion

    def test_is_same_lane_completion_detects_match(self):
        """is_same_lane_completion returns True when the existing closure
        matches the new completion fields."""
        completion = build_lane_completion(
            queue_job_id="job-1",
            queue_sha256="sha256",
            source_board_concurrency_token="token-1",
            closure_summary="Done",
            evidence=["ev-1"],
            closeout_receipt={"queue_job_id": "job-1"},
        )

        assert is_same_lane_completion(
            completion,
            queue_job_id="job-1",
            queue_sha256="sha256",
            source_board_concurrency_token="token-1",
            closure_summary="Done",
            evidence=["ev-1"],
            closeout_receipt={"queue_job_id": "job-1"},
        )

    def test_is_same_lane_completion_detects_mismatch(self):
        """is_same_lane_completion returns False when any field differs."""
        completion = build_lane_completion(
            queue_job_id="job-1",
            queue_sha256="sha256",
            source_board_concurrency_token="token-1",
            closure_summary="Done",
            evidence=["ev-1"],
            closeout_receipt=None,
        )

        assert not is_same_lane_completion(
            completion,
            queue_job_id="job-1",
            queue_sha256="DIFFERENT",
            source_board_concurrency_token="token-1",
            closure_summary="Done",
            evidence=["ev-1"],
            closeout_receipt=None,
        )

    def test_board_hash_serves_as_concurrency_token(self):
        """hash_canonical_board_json produces a SHA256 that can serve as
        a concurrency token for optimistic locking."""
        board_json = '{"board_id":"developer-master-board","lanes":[]}'
        token = hash_canonical_board_json(board_json)

        assert isinstance(token, str)
        assert len(token) == 64
        # Same input always produces same token
        assert token == hash_canonical_board_json(board_json)
        # Different input produces different token
        different_json = '{"board_id":"developer-master-board","lanes":[{"id":"lane-1"}]}'
        assert token != hash_canonical_board_json(different_json)


# ===========================================================================
# Test: Mission bootstrap (cross-layer integration)
# ===========================================================================


class TestMissionBootstrap:
    """Verify that MissionLinkage.from_mission works with
    parse_completion_source_request for mission bootstrap.

    Requirements: 13.1, 13.4
    """

    def test_mission_linkage_from_direct_columns(self):
        """MissionLinkage.from_mission resolves linkage from direct
        mission columns (queue_job_id, source_lane_id, etc.)."""
        mission = SimpleNamespace(
            queue_job_id="overnight-lane-lane-1-abc12345",
            source_lane_id="lane-1",
            source_board_concurrency_token="abc123",
            source_request="",
        )
        linkage = MissionLinkage.from_mission(mission)

        assert linkage is not None
        assert linkage.queue_job_id == "overnight-lane-lane-1-abc12345"
        assert linkage.source_lane_id == "lane-1"
        assert linkage.source_board_concurrency_token == "abc123"
        assert linkage.is_resolved

    def test_mission_linkage_from_source_request_fallback(self):
        """MissionLinkage.from_mission falls back to parsing source_request
        when direct columns are empty."""
        mission = SimpleNamespace(
            queue_job_id=None,
            source_lane_id=None,
            source_board_concurrency_token=None,
            source_request=(
                "Developer control-plane explicit completion write-back "
                "for lane lane-42 from queue job overnight-lane-lane-42-def789. "
                "Context: source_board_concurrency_token=token123."
            ),
        )
        linkage = MissionLinkage.from_mission(mission)

        assert linkage is not None
        assert linkage.source_lane_id == "lane-42"
        assert linkage.queue_job_id == "overnight-lane-lane-42-def789"
        assert linkage.source_board_concurrency_token == "token123"

    def test_mission_linkage_none_when_no_data(self):
        """MissionLinkage.from_mission returns None when no linkage data
        is available from either columns or source_request."""
        mission = SimpleNamespace(
            queue_job_id=None,
            source_lane_id=None,
            source_board_concurrency_token=None,
            source_request="",
        )
        linkage = MissionLinkage.from_mission(mission)
        assert linkage is None

    def test_parse_completion_source_request_roundtrip(self):
        """parse_completion_source_request correctly extracts fields from
        a structured source request string."""
        source_request = (
            "Developer control-plane stable closeout receipt observed "
            "for lane my-lane from queue job my-job-id. "
            "Context: source_board_concurrency_token=my-token."
        )
        parsed = parse_completion_source_request(source_request)

        assert parsed is not None
        assert parsed["source_lane_id"] == "my-lane"
        assert parsed["queue_job_id"] == "my-job-id"
        assert parsed["source_board_concurrency_token"] == "my-token"

    def test_mission_linkage_to_dict_and_from_dict_roundtrip(self):
        """MissionLinkage serializes to dict and deserializes back."""
        original = MissionLinkage(
            queue_job_id="job-1",
            source_lane_id="lane-1",
            source_board_concurrency_token="token-1",
        )
        as_dict = original.to_dict()
        restored = MissionLinkage.from_dict(as_dict)

        assert restored.queue_job_id == original.queue_job_id
        assert restored.source_lane_id == original.source_lane_id
        assert restored.source_board_concurrency_token == original.source_board_concurrency_token


# ===========================================================================
# Test: Conflict learning (cross-layer integration)
# ===========================================================================


class TestConflictLearning:
    """Verify that domain validation correctly detects conflicts that would
    trigger conflict learning in the lane service.

    Requirements: 13.1, 13.4
    """

    def test_duplicate_job_id_raises_conflict(self):
        """validate_queue_entry raises DuplicateJobIdError when the job ID
        already exists, which triggers conflict learning."""
        entry = _make_valid_queue_entry(job_id="existing-job")
        existing_ids = {"existing-job"}

        with pytest.raises(DuplicateJobIdError) as exc_info:
            validate_queue_entry(entry, existing_job_ids=existing_ids)

        assert exc_info.value.job_id == "existing-job"

    def test_stale_queue_sha_detectable_via_hash(self):
        """Queue SHA256 mismatch is detectable by comparing hashes,
        enabling the conflict learning path for stale queue state."""
        payload = QueueMaterializer.default_queue_payload()
        sha_before = QueueMaterializer.queue_sha256(payload)

        # Simulate another writer modifying the queue
        payload["jobs"].append(
            validate_queue_entry(
                _make_valid_queue_entry(job_id="other-job"),
                existing_job_ids=set(),
            )
        )
        sha_after = QueueMaterializer.queue_sha256(payload)

        # A client holding sha_before would detect the conflict
        assert sha_before != sha_after

    def test_lane_review_missing_detectable(self):
        """A lane without queue export reviews is detectable by the domain
        layer, which would trigger a lane-review-missing conflict."""
        lane_no_reviews = _make_lane_with_reviews(
            "lane-1", has_spec_review=False, has_risk_review=False
        )
        assert not lane_has_queue_export_reviews(lane_no_reviews)

        lane_partial = _make_lane_with_reviews(
            "lane-2", has_spec_review=True, has_risk_review=False
        )
        assert not lane_has_queue_export_reviews(lane_partial)

        lane_complete = _make_lane_with_reviews(
            "lane-3", has_spec_review=True, has_risk_review=True
        )
        assert lane_has_queue_export_reviews(lane_complete)

    def test_lane_verification_missing_detectable(self):
        """A lane without verification evidence is detectable by the domain
        layer, which would trigger a lane-verification-missing conflict."""
        lane_no_verification = _make_lane_with_reviews("lane-1", has_verification=False)
        assert not lane_has_completion_verification_evidence(lane_no_verification)

        lane_with_verification = _make_lane_with_reviews("lane-1", has_verification=True)
        assert lane_has_completion_verification_evidence(lane_with_verification)


# ===========================================================================
# Test: Domain validation end-to-end
# ===========================================================================


class TestDomainValidationEndToEnd:
    """Verify that domain validation functions work end-to-end across
    the queue entry validation pipeline with provenance.

    Requirements: 13.1, 13.4
    """

    def test_validate_queue_entry_preserves_provenance_chain(self):
        """validate_queue_entry preserves the full provenance chain from
        board to queue, maintaining the board-is-canonical invariant."""
        entry = _make_valid_queue_entry(
            source_lane_id="extraction-lane",
            board_token="concurrency-token-abc",
        )
        validated = validate_queue_entry(entry, existing_job_ids=set())

        provenance = validated["provenance"]
        assert provenance["sourceLaneId"] == "extraction-lane"
        assert provenance["sourceBoardConcurrencyToken"] == "concurrency-token-abc"
        assert provenance["precedence"]["canonicalPlanningSource"] == "active-board"
        assert provenance["precedence"]["derivedExecutionSurface"] == "overnight-queue"
        assert provenance["precedence"]["staleIfSourceBoardChanges"] is True

    def test_validate_queue_entry_rejects_invalid_status(self):
        """validate_queue_entry rejects entries with non-queued status."""
        entry = _make_valid_queue_entry()
        entry["status"] = "running"

        with pytest.raises(DomainValidationError) as exc_info:
            validate_queue_entry(entry, existing_job_ids=set())
        assert exc_info.value.status_code == 400

    def test_validate_queue_payload_shape_rejects_bad_language(self):
        """validate_queue_payload_shape rejects payloads with wrong language."""
        payload = QueueMaterializer.default_queue_payload()
        payload["language"] = "fr"

        with pytest.raises(DomainValidationError) as exc_info:
            validate_queue_payload_shape(payload)
        assert exc_info.value.status_code == 500

    def test_find_board_lane_integration(self):
        """find_board_lane locates a lane within a board payload, enabling
        the queue write workflow to validate lane state."""
        board = _make_board_payload_with_lanes([
            _make_lane_with_reviews("lane-1"),
            _make_lane_with_reviews("lane-2"),
            _make_lane_with_reviews("lane-3"),
        ])

        found = find_board_lane(board, "lane-2")
        assert found is not None
        assert found["id"] == "lane-2"

        not_found = find_board_lane(board, "nonexistent")
        assert not_found is None

    def test_queue_job_id_creation_is_deterministic(self):
        """QueueMaterializer.create_lane_queue_job_id produces the same
        job ID for the same lane + board token pair."""
        job_id_1 = QueueMaterializer.create_lane_queue_job_id("lane-1", "token-abc")
        job_id_2 = QueueMaterializer.create_lane_queue_job_id("lane-1", "token-abc")
        assert job_id_1 == job_id_2

        # Different lane or token produces different ID
        job_id_3 = QueueMaterializer.create_lane_queue_job_id("lane-2", "token-abc")
        assert job_id_1 != job_id_3

    def test_find_queue_job_after_entry_added(self):
        """QueueMaterializer.find_queue_job locates a job by ID after it
        has been added to the queue payload."""
        payload = QueueMaterializer.default_queue_payload()
        entry = _make_valid_queue_entry(job_id="my-test-job")
        validated = validate_queue_entry(entry, existing_job_ids=set())
        payload["jobs"].append(validated)

        found = QueueMaterializer.find_queue_job(payload, "my-test-job")
        assert found is not None
        assert found["jobId"] == "my-test-job"

        not_found = QueueMaterializer.find_queue_job(payload, "nonexistent")
        assert not_found is None


# ===========================================================================
# Test: ExecutionService closeout receipt response
# ===========================================================================


class TestExecutionServiceCloseoutReceipt:
    """Verify that ExecutionService.closeout_receipt_response produces
    valid API responses and that build_closeout_receipt_contract works.

    Requirements: 13.1, 13.4
    """

    def test_build_closeout_receipt_contract_minimal(self):
        """ExecutionService.build_closeout_receipt_contract produces a
        valid contract dict with minimal required fields."""
        contract = ExecutionService.build_closeout_receipt_contract(
            queue_job_id="job-1",
            artifact_paths=["path/to/artifact.json"],
        )

        assert contract["queue_job_id"] == "job-1"
        assert contract["artifact_paths"] == ["path/to/artifact.json"]

    def test_build_closeout_receipt_contract_full(self):
        """ExecutionService.build_closeout_receipt_contract includes all
        optional fields when provided."""
        contract = ExecutionService.build_closeout_receipt_contract(
            queue_job_id="job-1",
            artifact_paths=["artifact.json"],
            mission_id="mission-1",
            producer_key="developer-control-plane",
            source_lane_id="lane-1",
            source_board_concurrency_token="token-abc",
            closeout_status="completed",
            state_refresh_required=True,
        )

        assert contract["queue_job_id"] == "job-1"
        assert contract["mission_id"] == "mission-1"
        assert contract["source_lane_id"] == "lane-1"
        assert contract["source_board_concurrency_token"] == "token-abc"
        assert contract["closeout_status"] == "completed"


# ===========================================================================
# Test: build_lane_completion + is_same_lane_completion together
# ===========================================================================


class TestLaneCompletionRoundtrip:
    """Verify that build_lane_completion and is_same_lane_completion work
    together as a pair for the completion write-back workflow.

    Requirements: 13.1, 13.4
    """

    def test_build_then_verify_same(self):
        """A completion built by build_lane_completion is recognized as
        the same by is_same_lane_completion with identical inputs."""
        kwargs = {
            "queue_job_id": "job-abc",
            "queue_sha256": "sha256-value",
            "source_board_concurrency_token": "token-xyz",
            "closure_summary": "Lane completed with all tests passing",
            "evidence": ["test-report.json", "coverage.json"],
            "closeout_receipt": {"queue_job_id": "job-abc", "status": "completed"},
        }
        completion = build_lane_completion(**kwargs)
        assert is_same_lane_completion(completion, **kwargs)

    def test_build_then_detect_different_receipt(self):
        """is_same_lane_completion detects when the closeout receipt differs."""
        kwargs = {
            "queue_job_id": "job-abc",
            "queue_sha256": "sha256-value",
            "source_board_concurrency_token": "token-xyz",
            "closure_summary": "Done",
            "evidence": ["ev-1"],
            "closeout_receipt": {"queue_job_id": "job-abc"},
        }
        completion = build_lane_completion(**kwargs)

        modified_kwargs = {**kwargs, "closeout_receipt": {"queue_job_id": "DIFFERENT"}}
        assert not is_same_lane_completion(completion, **modified_kwargs)

    def test_build_without_closeout_receipt(self):
        """build_lane_completion omits closeout_receipt key when None."""
        completion = build_lane_completion(
            queue_job_id="job-1",
            queue_sha256="sha",
            source_board_concurrency_token="tok",
            closure_summary="Done",
            evidence=["ev"],
            closeout_receipt=None,
        )
        assert "closeout_receipt" not in completion

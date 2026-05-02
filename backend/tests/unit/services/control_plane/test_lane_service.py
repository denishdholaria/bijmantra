"""
Unit tests for Control Plane lane application service.

Tests completion workflow, approval receipt creation, and conflict learning
persistence in ``app.control_plane.application.lane_service``.

**Validates: Requirements 9.2**
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.control_plane.application.lane_service import (
    APPROVAL_RECEIPT_AUTHORITY_SOURCE,
    LaneService,
    _deduplicate_strings,
    build_lane_completion,
    is_same_lane_completion,
)
from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneApprovalReceiptResponse,
)


# ---------------------------------------------------------------------------
# Helpers — lightweight fakes
# ---------------------------------------------------------------------------


def _make_approval_receipt_record(**overrides) -> MagicMock:
    """Build a fake DeveloperControlPlaneApprovalReceipt row."""
    now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=timezone.utc)
    defaults = dict(
        id=1,
        organization_id=10,
        action_type="queue-write",
        outcome="approved",
        authority_actor_user_id=42,
        authority_actor_email="dev@bijmantra.com",
        authority_source=APPROVAL_RECEIPT_AUTHORITY_SOURCE,
        board_id="bijmantra-app-development-master-board",
        source_board_concurrency_token="token-abc",
        resulting_board_concurrency_token="token-def",
        source_lane_id="lane-1",
        queue_job_id="job-001",
        expected_queue_sha256="sha-expected",
        resulting_queue_sha256="sha-resulting",
        target_revision_id=5,
        previous_active_concurrency_token="token-prev",
        linked_mission_id="mission-001",
        rationale="Approved queue write for lane-1",
        evidence_refs=["ref-1", "ref-2"],
        summary_metadata={"key": "value"},
        created_at=now,
    )
    defaults.update(overrides)
    record = MagicMock()
    for k, v in defaults.items():
        setattr(record, k, v)
    return record


def _make_user(user_id: int = 42, email: str = "dev@bijmantra.com") -> MagicMock:
    """Build a fake User object."""
    user = MagicMock()
    user.id = user_id
    user.email = email
    return user


# ---------------------------------------------------------------------------
# _deduplicate_strings (pure helper)
# ---------------------------------------------------------------------------


class TestDeduplicateStrings:
    """Tests for _deduplicate_strings — removes duplicates and blanks, preserves order."""

    def test_removes_duplicates(self):
        assert _deduplicate_strings(["a", "b", "a", "c"]) == ["a", "b", "c"]

    def test_removes_blank_entries(self):
        assert _deduplicate_strings(["a", "", "  ", "b"]) == ["a", "b"]

    def test_preserves_order(self):
        assert _deduplicate_strings(["c", "b", "a"]) == ["c", "b", "a"]

    def test_strips_whitespace(self):
        assert _deduplicate_strings(["  a  ", "a", " b "]) == ["a", "b"]

    def test_empty_list(self):
        assert _deduplicate_strings([]) == []

    def test_all_blanks(self):
        assert _deduplicate_strings(["", "  ", "\t"]) == []


# ---------------------------------------------------------------------------
# build_lane_completion (pure function)
# ---------------------------------------------------------------------------


class TestBuildLaneCompletion:
    """Tests for build_lane_completion — builds correct dict with all fields."""

    def test_builds_correct_dict_with_all_fields(self):
        result = build_lane_completion(
            queue_job_id="job-001",
            queue_sha256="sha256-abc",
            source_board_concurrency_token="token-xyz",
            closure_summary="Lane completed successfully",
            evidence=["evidence-1", "evidence-2"],
        )

        assert result["queue_job_id"] == "job-001"
        assert result["queue_sha256"] == "sha256-abc"
        assert result["source_board_concurrency_token"] == "token-xyz"
        assert result["closure_summary"] == "Lane completed successfully"
        assert result["evidence"] == ["evidence-1", "evidence-2"]
        assert "completed_at" in result
        assert result["completed_at"].endswith("Z")
        assert "closeout_receipt" not in result

    def test_includes_closeout_receipt_when_provided(self):
        receipt = {"queue_job_id": "job-001", "status": "completed"}
        result = build_lane_completion(
            queue_job_id="job-001",
            queue_sha256="sha256-abc",
            source_board_concurrency_token="token-xyz",
            closure_summary="Done",
            evidence=["ev-1"],
            closeout_receipt=receipt,
        )

        assert result["closeout_receipt"] == receipt

    def test_omits_closeout_receipt_when_none(self):
        result = build_lane_completion(
            queue_job_id="job-001",
            queue_sha256="sha256-abc",
            source_board_concurrency_token="token-xyz",
            closure_summary="Done",
            evidence=["ev-1"],
            closeout_receipt=None,
        )

        assert "closeout_receipt" not in result

    def test_completed_at_is_iso_format_utc(self):
        result = build_lane_completion(
            queue_job_id="job-001",
            queue_sha256="sha",
            source_board_concurrency_token="tok",
            closure_summary="Done",
            evidence=["ev"],
        )

        completed_at = result["completed_at"]
        # Should be parseable and end with Z (UTC)
        assert completed_at.endswith("Z")
        # Should not contain microseconds
        assert "." not in completed_at


# ---------------------------------------------------------------------------
# is_same_lane_completion (pure function)
# ---------------------------------------------------------------------------


class TestIsSameLaneCompletion:
    """Tests for is_same_lane_completion — equality check for lane closures."""

    def _base_kwargs(self) -> dict[str, Any]:
        return dict(
            queue_job_id="job-001",
            queue_sha256="sha256-abc",
            source_board_concurrency_token="token-xyz",
            closure_summary="Lane completed",
            evidence=["ev-1", "ev-2"],
            closeout_receipt=None,
        )

    def _matching_closure(self) -> dict[str, Any]:
        return {
            "queue_job_id": "job-001",
            "queue_sha256": "sha256-abc",
            "source_board_concurrency_token": "token-xyz",
            "closure_summary": "Lane completed",
            "evidence": ["ev-1", "ev-2"],
            "closeout_receipt": None,
        }

    def test_returns_true_when_all_fields_match(self):
        assert is_same_lane_completion(
            self._matching_closure(), **self._base_kwargs()
        ) is True

    def test_returns_false_when_queue_job_id_differs(self):
        kwargs = self._base_kwargs()
        kwargs["queue_job_id"] = "different-job"
        assert is_same_lane_completion(self._matching_closure(), **kwargs) is False

    def test_returns_false_when_queue_sha256_differs(self):
        kwargs = self._base_kwargs()
        kwargs["queue_sha256"] = "different-sha"
        assert is_same_lane_completion(self._matching_closure(), **kwargs) is False

    def test_returns_false_when_token_differs(self):
        kwargs = self._base_kwargs()
        kwargs["source_board_concurrency_token"] = "different-token"
        assert is_same_lane_completion(self._matching_closure(), **kwargs) is False

    def test_returns_false_when_summary_differs(self):
        kwargs = self._base_kwargs()
        kwargs["closure_summary"] = "Different summary"
        assert is_same_lane_completion(self._matching_closure(), **kwargs) is False

    def test_returns_false_when_evidence_differs(self):
        kwargs = self._base_kwargs()
        kwargs["evidence"] = ["different-ev"]
        assert is_same_lane_completion(self._matching_closure(), **kwargs) is False

    def test_returns_false_when_closeout_receipt_differs(self):
        kwargs = self._base_kwargs()
        kwargs["closeout_receipt"] = {"some": "receipt"}
        assert is_same_lane_completion(self._matching_closure(), **kwargs) is False

    def test_returns_false_when_existing_is_not_dict(self):
        assert is_same_lane_completion("not-a-dict", **self._base_kwargs()) is False

    def test_returns_false_when_existing_is_none(self):
        assert is_same_lane_completion(None, **self._base_kwargs()) is False


# ---------------------------------------------------------------------------
# approval_receipt_response (static method)
# ---------------------------------------------------------------------------


class TestApprovalReceiptResponse:
    """Tests for LaneService.approval_receipt_response — maps DB record to API response."""

    def test_maps_all_fields_correctly(self):
        record = _make_approval_receipt_record()
        resp = LaneService.approval_receipt_response(record)

        assert isinstance(resp, DeveloperControlPlaneApprovalReceiptResponse)
        assert resp.receipt_id == 1
        assert resp.organization_id == 10
        assert resp.action_type == "queue-write"
        assert resp.outcome == "approved"
        assert resp.authority_actor_user_id == 42
        assert resp.authority_actor_email == "dev@bijmantra.com"
        assert resp.authority_source == APPROVAL_RECEIPT_AUTHORITY_SOURCE
        assert resp.board_id == "bijmantra-app-development-master-board"
        assert resp.source_board_concurrency_token == "token-abc"
        assert resp.resulting_board_concurrency_token == "token-def"
        assert resp.source_lane_id == "lane-1"
        assert resp.queue_job_id == "job-001"
        assert resp.expected_queue_sha256 == "sha-expected"
        assert resp.resulting_queue_sha256 == "sha-resulting"
        assert resp.target_revision_id == 5
        assert resp.previous_active_concurrency_token == "token-prev"
        assert resp.linked_mission_id == "mission-001"
        assert resp.rationale == "Approved queue write for lane-1"
        assert resp.evidence_refs == ["ref-1", "ref-2"]
        assert resp.summary_metadata == {"key": "value"}

    def test_recorded_at_maps_from_created_at(self):
        ts = datetime(2026, 1, 15, 8, 30, 0, tzinfo=timezone.utc)
        record = _make_approval_receipt_record(created_at=ts)
        resp = LaneService.approval_receipt_response(record)
        assert resp.recorded_at == ts

    def test_handles_none_optional_fields(self):
        record = _make_approval_receipt_record(
            authority_actor_email=None,
            source_board_concurrency_token=None,
            resulting_board_concurrency_token=None,
            source_lane_id=None,
            queue_job_id=None,
            expected_queue_sha256=None,
            resulting_queue_sha256=None,
            target_revision_id=None,
            previous_active_concurrency_token=None,
            linked_mission_id=None,
            summary_metadata=None,
        )
        resp = LaneService.approval_receipt_response(record)
        assert resp.authority_actor_email is None
        assert resp.source_board_concurrency_token is None
        assert resp.summary_metadata is None


# ---------------------------------------------------------------------------
# get_latest_approval_receipt (async DB query)
# ---------------------------------------------------------------------------


class TestGetLatestApprovalReceipt:
    """Tests for LaneService.get_latest_approval_receipt — async DB query."""

    @pytest.mark.asyncio
    async def test_returns_record_when_found(self):
        record = _make_approval_receipt_record()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record

        db = AsyncMock()
        db.execute.return_value = mock_result

        service = LaneService(db)
        result = await service.get_latest_approval_receipt(organization_id=10)

        assert result is record
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        service = LaneService(db)
        result = await service.get_latest_approval_receipt(organization_id=999)

        assert result is None

    @pytest.mark.asyncio
    async def test_executes_single_query(self):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        service = LaneService(db)
        await service.get_latest_approval_receipt(organization_id=10)

        assert db.execute.await_count == 1


# ---------------------------------------------------------------------------
# record_approval_receipt (async DB write)
# ---------------------------------------------------------------------------


class TestRecordApprovalReceipt:
    """Tests for LaneService.record_approval_receipt — creates receipt and flushes."""

    @pytest.mark.asyncio
    async def test_creates_receipt_and_flushes(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = LaneService(db)
        user = _make_user()

        result = await service.record_approval_receipt(
            organization_id=10,
            current_user=user,
            action_type="queue-write",
            outcome="approved",
            board_id="board-1",
            rationale="Approved",
            evidence_refs=["ref-1"],
        )

        db.add.assert_called_once()
        db.flush.assert_awaited_once()

        # The returned object is the receipt that was added
        added_receipt = db.add.call_args[0][0]
        assert result is added_receipt

    @pytest.mark.asyncio
    async def test_receipt_has_correct_fields(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = LaneService(db)
        user = _make_user(user_id=99, email="admin@bijmantra.com")

        await service.record_approval_receipt(
            organization_id=10,
            current_user=user,
            action_type="completion-write",
            outcome="approved",
            board_id="board-1",
            rationale="Completion approved",
            evidence_refs=["ref-1", "ref-2"],
            source_lane_id="lane-5",
            queue_job_id="job-010",
            summary_metadata={"detail": "test"},
        )

        receipt = db.add.call_args[0][0]
        assert receipt.organization_id == 10
        assert receipt.action_type == "completion-write"
        assert receipt.outcome == "approved"
        assert receipt.authority_actor_user_id == 99
        assert receipt.authority_actor_email == "admin@bijmantra.com"
        assert receipt.authority_source == APPROVAL_RECEIPT_AUTHORITY_SOURCE
        assert receipt.board_id == "board-1"
        assert receipt.rationale == "Completion approved"
        assert receipt.source_lane_id == "lane-5"
        assert receipt.queue_job_id == "job-010"
        assert receipt.summary_metadata == {"detail": "test"}

    @pytest.mark.asyncio
    async def test_evidence_refs_are_deduplicated(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = LaneService(db)
        user = _make_user()

        await service.record_approval_receipt(
            organization_id=10,
            current_user=user,
            action_type="queue-write",
            outcome="approved",
            board_id="board-1",
            rationale="Test",
            evidence_refs=["ref-1", "ref-1", "", "ref-2"],
        )

        receipt = db.add.call_args[0][0]
        assert receipt.evidence_refs == ["ref-1", "ref-2"]


# ---------------------------------------------------------------------------
# persist_conflict_learning (async DB write with lazy import)
# ---------------------------------------------------------------------------


class TestPersistConflictLearning:
    """Tests for LaneService.persist_conflict_learning — conflict learning persistence."""

    @pytest.mark.asyncio
    @patch("app.control_plane.application.lane_service._record_learning_entry", new_callable=AsyncMock, create=True)
    async def test_persists_learning_entry_and_commits(self, mock_record):
        """When conflict_reason and summary are present, a learning entry is persisted."""
        # Patch the lazy import inside persist_conflict_learning
        mock_record.return_value = (MagicMock(), True)

        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()

        service = LaneService(db)
        user = _make_user()

        with patch(
            "app.api.bijmantra.developer_control_plane._record_learning_entry",
            new_callable=AsyncMock,
        ) as mock_entry:
            mock_entry.return_value = (MagicMock(), True)

            await service.persist_conflict_learning(
                organization_id=10,
                current_user=user,
                scope="queue-export",
                conflict_detail={
                    "conflict_reason": "stale-board-token",
                    "detail": "Board token is stale",
                    "remediation_message": "Refresh board state",
                },
                board_id="board-1",
                source_lane_id="lane-1",
                queue_job_id="job-001",
                source_board_concurrency_token="token-abc",
            )

            mock_entry.assert_awaited_once()
            db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_silently_returns_when_conflict_reason_missing(self):
        """When conflict_reason is absent, no learning entry is created."""
        db = AsyncMock()
        db.commit = AsyncMock()

        service = LaneService(db)
        user = _make_user()

        await service.persist_conflict_learning(
            organization_id=10,
            current_user=user,
            scope="queue-export",
            conflict_detail={"detail": "Some detail without reason"},
            board_id="board-1",
            source_lane_id=None,
            queue_job_id=None,
            source_board_concurrency_token=None,
        )

        # No commit should have been called since we returned early
        db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_silently_returns_when_conflict_reason_is_empty(self):
        """When conflict_reason is an empty string, no learning entry is created."""
        db = AsyncMock()
        db.commit = AsyncMock()

        service = LaneService(db)
        user = _make_user()

        await service.persist_conflict_learning(
            organization_id=10,
            current_user=user,
            scope="queue-export",
            conflict_detail={"conflict_reason": ""},
            board_id="board-1",
            source_lane_id=None,
            queue_job_id=None,
            source_board_concurrency_token=None,
        )

        db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_silently_returns_when_summary_is_empty(self):
        """When detail and remediation_message are both absent, summary is empty and we return."""
        db = AsyncMock()
        db.commit = AsyncMock()

        service = LaneService(db)
        user = _make_user()

        await service.persist_conflict_learning(
            organization_id=10,
            current_user=user,
            scope="queue-export",
            conflict_detail={"conflict_reason": "stale-board-token"},
            board_id="board-1",
            source_lane_id=None,
            queue_job_id=None,
            source_board_concurrency_token=None,
        )

        db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_rolls_back_on_exception(self):
        """When _record_learning_entry raises, the transaction is rolled back."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()

        service = LaneService(db)
        user = _make_user()

        with patch(
            "app.api.bijmantra.developer_control_plane._record_learning_entry",
            new_callable=AsyncMock,
        ) as mock_entry:
            mock_entry.side_effect = RuntimeError("DB error")

            await service.persist_conflict_learning(
                organization_id=10,
                current_user=user,
                scope="queue-export",
                conflict_detail={
                    "conflict_reason": "stale-board-token",
                    "detail": "Token mismatch",
                },
                board_id="board-1",
                source_lane_id="lane-1",
                queue_job_id=None,
                source_board_concurrency_token="token-abc",
            )

            db.rollback.assert_awaited_once()
            db.commit.assert_not_awaited()

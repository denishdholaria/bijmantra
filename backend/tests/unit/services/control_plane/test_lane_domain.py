"""
Unit tests for Control Plane lane domain module.

Tests pure functions and immutable entities in
``app.control_plane.domain.lane``.

**Validates: Requirements 8.2**
"""

from __future__ import annotations

import dataclasses

import pytest

from app.control_plane.domain.lane import (
    LaneClosure,
    LaneEntity,
    ReviewGate,
    find_board_lane,
    has_complete_review_gate,
    has_meaningful_text,
    has_meaningful_text_list,
    lane_has_completion_verification_evidence,
    lane_has_queue_export_reviews,
)
from app.control_plane.domain.validation import DomainValidationError


# ---------------------------------------------------------------------------
# has_meaningful_text
# ---------------------------------------------------------------------------


class TestHasMeaningfulText:
    """Tests for the has_meaningful_text helper."""

    def test_non_empty_string_returns_true(self):
        assert has_meaningful_text("hello") is True

    def test_string_with_spaces_returns_true(self):
        assert has_meaningful_text("  hello  ") is True

    def test_empty_string_returns_false(self):
        assert has_meaningful_text("") is False

    def test_whitespace_only_returns_false(self):
        assert has_meaningful_text("   ") is False

    def test_tab_only_returns_false(self):
        assert has_meaningful_text("\t\n") is False

    def test_none_returns_false(self):
        assert has_meaningful_text(None) is False

    def test_integer_returns_false(self):
        assert has_meaningful_text(42) is False

    def test_list_returns_false(self):
        assert has_meaningful_text(["text"]) is False

    def test_dict_returns_false(self):
        assert has_meaningful_text({"key": "val"}) is False

    def test_boolean_returns_false(self):
        assert has_meaningful_text(True) is False


# ---------------------------------------------------------------------------
# has_meaningful_text_list
# ---------------------------------------------------------------------------


class TestHasMeaningfulTextList:
    """Tests for the has_meaningful_text_list helper."""

    def test_list_with_meaningful_string_returns_true(self):
        assert has_meaningful_text_list(["evidence-1"]) is True

    def test_list_with_multiple_meaningful_strings_returns_true(self):
        assert has_meaningful_text_list(["a", "b", "c"]) is True

    def test_list_with_one_meaningful_among_empty_returns_true(self):
        assert has_meaningful_text_list(["", "  ", "valid"]) is True

    def test_empty_list_returns_false(self):
        assert has_meaningful_text_list([]) is False

    def test_list_of_empty_strings_returns_false(self):
        assert has_meaningful_text_list(["", "  ", "\t"]) is False

    def test_none_returns_false(self):
        assert has_meaningful_text_list(None) is False

    def test_string_returns_false(self):
        assert has_meaningful_text_list("not a list") is False

    def test_integer_returns_false(self):
        assert has_meaningful_text_list(123) is False

    def test_list_of_non_strings_returns_false(self):
        assert has_meaningful_text_list([1, 2, 3]) is False


# ---------------------------------------------------------------------------
# has_complete_review_gate
# ---------------------------------------------------------------------------


def _complete_gate() -> dict:
    """Return a minimal complete review gate dict."""
    return {
        "reviewed_by": "dev-user",
        "summary": "Looks good",
        "reviewed_at": "2026-04-15T12:00:00Z",
        "evidence": ["commit-abc123"],
    }


class TestHasCompleteReviewGate:
    """Tests for has_complete_review_gate validation."""

    def test_complete_gate_returns_true(self):
        assert has_complete_review_gate(_complete_gate()) is True

    def test_missing_reviewed_by_returns_false(self):
        gate = _complete_gate()
        gate["reviewed_by"] = ""
        assert has_complete_review_gate(gate) is False

    def test_missing_summary_returns_false(self):
        gate = _complete_gate()
        gate["summary"] = ""
        assert has_complete_review_gate(gate) is False

    def test_missing_reviewed_at_returns_false(self):
        gate = _complete_gate()
        gate["reviewed_at"] = ""
        assert has_complete_review_gate(gate) is False

    def test_empty_evidence_list_returns_false(self):
        gate = _complete_gate()
        gate["evidence"] = []
        assert has_complete_review_gate(gate) is False

    def test_evidence_with_only_empty_strings_returns_false(self):
        gate = _complete_gate()
        gate["evidence"] = ["", "  "]
        assert has_complete_review_gate(gate) is False

    def test_none_returns_false(self):
        assert has_complete_review_gate(None) is False

    def test_string_returns_false(self):
        assert has_complete_review_gate("not a dict") is False

    def test_integer_returns_false(self):
        assert has_complete_review_gate(42) is False

    def test_empty_dict_returns_false(self):
        assert has_complete_review_gate({}) is False


# ---------------------------------------------------------------------------
# lane_has_queue_export_reviews
# ---------------------------------------------------------------------------


def _lane_with_reviews(*, spec_review=None, risk_review=None) -> dict:
    """Build a lane dict with the given review gates."""
    review_state = {}
    if spec_review is not None:
        review_state["spec_review"] = spec_review
    if risk_review is not None:
        review_state["risk_review"] = risk_review
    return {"review_state": review_state}


class TestLaneHasQueueExportReviews:
    """Tests for lane_has_queue_export_reviews."""

    def test_both_reviews_complete_returns_true(self):
        lane = _lane_with_reviews(
            spec_review=_complete_gate(),
            risk_review=_complete_gate(),
        )
        assert lane_has_queue_export_reviews(lane) is True

    def test_missing_spec_review_returns_false(self):
        lane = _lane_with_reviews(risk_review=_complete_gate())
        assert lane_has_queue_export_reviews(lane) is False

    def test_missing_risk_review_returns_false(self):
        lane = _lane_with_reviews(spec_review=_complete_gate())
        assert lane_has_queue_export_reviews(lane) is False

    def test_no_review_state_returns_false(self):
        assert lane_has_queue_export_reviews({}) is False

    def test_review_state_not_dict_returns_false(self):
        assert lane_has_queue_export_reviews({"review_state": "bad"}) is False

    def test_incomplete_spec_review_returns_false(self):
        incomplete = _complete_gate()
        incomplete["reviewed_by"] = ""
        lane = _lane_with_reviews(
            spec_review=incomplete,
            risk_review=_complete_gate(),
        )
        assert lane_has_queue_export_reviews(lane) is False


# ---------------------------------------------------------------------------
# lane_has_completion_verification_evidence
# ---------------------------------------------------------------------------


class TestLaneHasCompletionVerificationEvidence:
    """Tests for lane_has_completion_verification_evidence."""

    def test_with_verification_evidence_returns_true(self):
        lane = {"review_state": {"verification_evidence": _complete_gate()}}
        assert lane_has_completion_verification_evidence(lane) is True

    def test_missing_verification_evidence_returns_false(self):
        lane = {"review_state": {}}
        assert lane_has_completion_verification_evidence(lane) is False

    def test_no_review_state_returns_false(self):
        assert lane_has_completion_verification_evidence({}) is False

    def test_review_state_not_dict_returns_false(self):
        assert lane_has_completion_verification_evidence({"review_state": 123}) is False

    def test_incomplete_verification_evidence_returns_false(self):
        incomplete = _complete_gate()
        incomplete["evidence"] = []
        lane = {"review_state": {"verification_evidence": incomplete}}
        assert lane_has_completion_verification_evidence(lane) is False


# ---------------------------------------------------------------------------
# find_board_lane
# ---------------------------------------------------------------------------


class TestFindBoardLane:
    """Tests for find_board_lane lookup."""

    def test_finds_matching_lane(self):
        board = {"lanes": [{"id": "lane-1", "title": "First"}, {"id": "lane-2", "title": "Second"}]}
        result = find_board_lane(board, "lane-2")
        assert result is not None
        assert result["id"] == "lane-2"
        assert result["title"] == "Second"

    def test_returns_none_when_no_match(self):
        board = {"lanes": [{"id": "lane-1"}]}
        assert find_board_lane(board, "nonexistent") is None

    def test_returns_none_for_empty_lanes_list(self):
        board = {"lanes": []}
        assert find_board_lane(board, "lane-1") is None

    def test_raises_when_lanes_missing(self):
        with pytest.raises(DomainValidationError) as exc_info:
            find_board_lane({}, "lane-1")
        assert exc_info.value.status_code == 500

    def test_raises_when_lanes_not_list(self):
        with pytest.raises(DomainValidationError) as exc_info:
            find_board_lane({"lanes": "not-a-list"}, "lane-1")
        assert exc_info.value.status_code == 500

    def test_skips_non_dict_entries(self):
        board = {"lanes": ["not-a-dict", {"id": "lane-1"}]}
        result = find_board_lane(board, "lane-1")
        assert result is not None
        assert result["id"] == "lane-1"

    def test_returns_first_match(self):
        board = {"lanes": [{"id": "dup", "n": 1}, {"id": "dup", "n": 2}]}
        result = find_board_lane(board, "dup")
        assert result["n"] == 1


# ---------------------------------------------------------------------------
# ReviewGate dataclass
# ---------------------------------------------------------------------------


class TestReviewGate:
    """Tests for the ReviewGate frozen dataclass."""

    def test_frozen_immutable(self):
        gate = ReviewGate(
            reviewed_by="user",
            summary="ok",
            reviewed_at="2026-01-01T00:00:00Z",
            evidence=["e1"],
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            gate.reviewed_by = "other"

    def test_is_complete_with_all_fields(self):
        gate = ReviewGate(
            reviewed_by="user",
            summary="ok",
            reviewed_at="2026-01-01T00:00:00Z",
            evidence=["e1"],
        )
        assert gate.is_complete is True

    def test_is_complete_false_empty_reviewed_by(self):
        gate = ReviewGate(
            reviewed_by="",
            summary="ok",
            reviewed_at="2026-01-01T00:00:00Z",
            evidence=["e1"],
        )
        assert gate.is_complete is False

    def test_is_complete_false_whitespace_summary(self):
        gate = ReviewGate(
            reviewed_by="user",
            summary="   ",
            reviewed_at="2026-01-01T00:00:00Z",
            evidence=["e1"],
        )
        assert gate.is_complete is False

    def test_is_complete_false_empty_evidence(self):
        gate = ReviewGate(
            reviewed_by="user",
            summary="ok",
            reviewed_at="2026-01-01T00:00:00Z",
            evidence=[],
        )
        assert gate.is_complete is False

    def test_is_complete_false_evidence_only_empty_strings(self):
        gate = ReviewGate(
            reviewed_by="user",
            summary="ok",
            reviewed_at="2026-01-01T00:00:00Z",
            evidence=["", "  "],
        )
        assert gate.is_complete is False

    def test_default_evidence_is_empty_list(self):
        gate = ReviewGate(reviewed_by="u", summary="s", reviewed_at="t")
        assert gate.evidence == []

    def test_from_dict_valid(self):
        data = {
            "reviewed_by": "user",
            "summary": "ok",
            "reviewed_at": "2026-01-01T00:00:00Z",
            "evidence": ["e1"],
        }
        gate = ReviewGate.from_dict(data)
        assert gate is not None
        assert gate.reviewed_by == "user"
        assert gate.summary == "ok"
        assert gate.reviewed_at == "2026-01-01T00:00:00Z"
        assert gate.evidence == ["e1"]

    def test_from_dict_returns_none_for_non_dict(self):
        assert ReviewGate.from_dict("not a dict") is None
        assert ReviewGate.from_dict(42) is None
        assert ReviewGate.from_dict(None) is None

    def test_from_dict_defaults_missing_fields(self):
        gate = ReviewGate.from_dict({})
        assert gate is not None
        assert gate.reviewed_by == ""
        assert gate.summary == ""
        assert gate.reviewed_at == ""
        assert gate.evidence == []

    def test_from_dict_coerces_non_string_fields(self):
        data = {
            "reviewed_by": 123,
            "summary": True,
            "reviewed_at": None,
            "evidence": ["valid", 42],
        }
        gate = ReviewGate.from_dict(data)
        assert gate is not None
        assert gate.reviewed_by == ""
        assert gate.summary == ""
        assert gate.reviewed_at == ""
        # Non-string evidence items are filtered out
        assert gate.evidence == ["valid"]

    def test_from_dict_non_list_evidence_becomes_empty(self):
        data = {"evidence": "not-a-list"}
        gate = ReviewGate.from_dict(data)
        assert gate is not None
        assert gate.evidence == []


# ---------------------------------------------------------------------------
# LaneClosure dataclass
# ---------------------------------------------------------------------------


class TestLaneClosure:
    """Tests for the LaneClosure frozen dataclass."""

    def test_frozen_immutable(self):
        closure = LaneClosure(closure_summary="done")
        with pytest.raises(dataclasses.FrozenInstanceError):
            closure.closure_summary = "changed"

    def test_defaults(self):
        closure = LaneClosure(closure_summary="done")
        assert closure.evidence == []
        assert closure.queue_job_id == ""
        assert closure.closeout_receipt == {}

    def test_all_fields(self):
        closure = LaneClosure(
            closure_summary="Lane completed",
            evidence=["e1", "e2"],
            queue_job_id="job-123",
            closeout_receipt={"status": "ok"},
        )
        assert closure.closure_summary == "Lane completed"
        assert closure.evidence == ["e1", "e2"]
        assert closure.queue_job_id == "job-123"
        assert closure.closeout_receipt == {"status": "ok"}


# ---------------------------------------------------------------------------
# LaneEntity dataclass
# ---------------------------------------------------------------------------


class TestLaneEntity:
    """Tests for the LaneEntity frozen dataclass."""

    def test_frozen_immutable(self):
        entity = LaneEntity(lane_id="l1", title="Lane 1", status="active")
        with pytest.raises(dataclasses.FrozenInstanceError):
            entity.status = "completed"

    def test_defaults(self):
        entity = LaneEntity(lane_id="l1", title="Lane 1", status="active")
        assert entity.has_queue_export_reviews is False
        assert entity.has_verification_evidence is False
        assert entity.closure is None

    def test_from_dict_active_lane(self):
        lane = {
            "id": "lane-1",
            "title": "My Lane",
            "status": "active",
        }
        entity = LaneEntity.from_dict(lane)
        assert entity.lane_id == "lane-1"
        assert entity.title == "My Lane"
        assert entity.status == "active"
        assert entity.has_queue_export_reviews is False
        assert entity.has_verification_evidence is False
        assert entity.closure is None

    def test_from_dict_with_reviews(self):
        lane = {
            "id": "lane-2",
            "title": "Reviewed Lane",
            "status": "active",
            "review_state": {
                "spec_review": _complete_gate(),
                "risk_review": _complete_gate(),
            },
        }
        entity = LaneEntity.from_dict(lane)
        assert entity.has_queue_export_reviews is True
        assert entity.has_verification_evidence is False

    def test_from_dict_with_verification_evidence(self):
        lane = {
            "id": "lane-3",
            "title": "Verified Lane",
            "status": "completed",
            "review_state": {
                "verification_evidence": _complete_gate(),
            },
        }
        entity = LaneEntity.from_dict(lane)
        assert entity.has_verification_evidence is True

    def test_from_dict_with_closure(self):
        lane = {
            "id": "lane-4",
            "title": "Closed Lane",
            "status": "completed",
            "closure": {
                "closure_summary": "All done",
                "evidence": ["e1"],
                "queue_job_id": "job-99",
                "closeout_receipt": {"status": "ok"},
            },
        }
        entity = LaneEntity.from_dict(lane)
        assert entity.closure is not None
        assert entity.closure.closure_summary == "All done"
        assert entity.closure.evidence == ["e1"]
        assert entity.closure.queue_job_id == "job-99"
        assert entity.closure.closeout_receipt == {"status": "ok"}

    def test_from_dict_closure_not_dict_is_none(self):
        lane = {
            "id": "lane-5",
            "title": "Bad Closure",
            "status": "active",
            "closure": "not-a-dict",
        }
        entity = LaneEntity.from_dict(lane)
        assert entity.closure is None

    def test_from_dict_missing_fields_use_defaults(self):
        entity = LaneEntity.from_dict({})
        assert entity.lane_id == ""
        assert entity.title == ""
        assert entity.status == ""

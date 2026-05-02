"""
Unit tests for Control Plane mission domain module.

Tests pure functions and immutable entities in
``app.control_plane.domain.mission``.

**Validates: Requirements 8.3**
"""

from __future__ import annotations

import dataclasses
from types import SimpleNamespace

import pytest

from app.control_plane.domain.mission import (
    MissionEntity,
    MissionLinkage,
    mission_linkage,
    parse_completion_source_request,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mission(**overrides) -> SimpleNamespace:
    """Build a minimal duck-typed mission object."""
    defaults = dict(
        queue_job_id=None,
        source_lane_id=None,
        source_board_concurrency_token=None,
        source_request=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# parse_completion_source_request
# ---------------------------------------------------------------------------


class TestParseCompletionSourceRequest:
    """Tests for parsing structured source_request strings."""

    def test_valid_with_board_token(self):
        """Full source request with board concurrency token."""
        sr = (
            "Developer control-plane explicit completion write-back "
            "for lane lane-42 from queue job job-abc123. "
            "Context: source_board_concurrency_token=tok-xyz."
        )
        result = parse_completion_source_request(sr)
        assert result is not None
        assert result["source_lane_id"] == "lane-42"
        assert result["queue_job_id"] == "job-abc123"
        assert result["source_board_concurrency_token"] == "tok-xyz"

    def test_valid_without_board_token(self):
        """Source request without the optional board token context."""
        sr = (
            "Developer control-plane stable closeout receipt observed "
            "for lane my-lane from queue job qj-99."
        )
        result = parse_completion_source_request(sr)
        assert result is not None
        assert result["source_lane_id"] == "my-lane"
        assert result["queue_job_id"] == "qj-99"
        assert result["source_board_concurrency_token"] is None

    def test_none_returns_none(self):
        assert parse_completion_source_request(None) is None

    def test_empty_string_returns_none(self):
        assert parse_completion_source_request("") is None

    def test_non_matching_string_returns_none(self):
        assert parse_completion_source_request("random text") is None

    def test_whitespace_only_returns_none(self):
        assert parse_completion_source_request("   ") is None

    def test_strips_surrounding_whitespace(self):
        """Leading/trailing whitespace is stripped before matching."""
        sr = (
            "  Developer control-plane explicit completion write-back "
            "for lane lane-1 from queue job job-1.  "
        )
        result = parse_completion_source_request(sr)
        assert result is not None
        assert result["source_lane_id"] == "lane-1"

    def test_partial_match_returns_none(self):
        """A string that starts like the pattern but is incomplete."""
        sr = "Developer control-plane explicit completion write-back for lane"
        assert parse_completion_source_request(sr) is None

    def test_event_type_explicit_completion(self):
        """Explicit completion write-back event type is captured."""
        sr = (
            "Developer control-plane explicit completion write-back "
            "for lane L1 from queue job J1."
        )
        result = parse_completion_source_request(sr)
        assert result is not None
        assert result["source_lane_id"] == "L1"

    def test_event_type_stable_closeout(self):
        """Stable closeout receipt observed event type is captured."""
        sr = (
            "Developer control-plane stable closeout receipt observed "
            "for lane L2 from queue job J2."
        )
        result = parse_completion_source_request(sr)
        assert result is not None
        assert result["source_lane_id"] == "L2"


# ---------------------------------------------------------------------------
# mission_linkage
# ---------------------------------------------------------------------------


class TestMissionLinkage:
    """Tests for resolving linkage from a mission object."""

    def test_direct_columns_all_populated(self):
        """When all direct columns are set, they are returned."""
        m = _make_mission(
            queue_job_id="job-1",
            source_lane_id="lane-1",
            source_board_concurrency_token="tok-1",
        )
        result = mission_linkage(m)
        assert result == {
            "queue_job_id": "job-1",
            "source_lane_id": "lane-1",
            "source_board_concurrency_token": "tok-1",
        }

    def test_direct_columns_partial(self):
        """When only some direct columns are set, they are returned."""
        m = _make_mission(queue_job_id="job-2")
        result = mission_linkage(m)
        assert result is not None
        assert result["queue_job_id"] == "job-2"
        assert result["source_lane_id"] is None
        assert result["source_board_concurrency_token"] is None

    def test_direct_columns_only_lane_id(self):
        """Only source_lane_id populated."""
        m = _make_mission(source_lane_id="lane-x")
        result = mission_linkage(m)
        assert result is not None
        assert result["source_lane_id"] == "lane-x"
        assert result["queue_job_id"] is None

    def test_direct_columns_only_board_token(self):
        """Only source_board_concurrency_token populated."""
        m = _make_mission(source_board_concurrency_token="tok-only")
        result = mission_linkage(m)
        assert result is not None
        assert result["source_board_concurrency_token"] == "tok-only"

    def test_fallback_to_source_request_parsing(self):
        """When direct columns are empty, falls back to source_request."""
        sr = (
            "Developer control-plane explicit completion write-back "
            "for lane lane-fb from queue job job-fb. "
            "Context: source_board_concurrency_token=tok-fb."
        )
        m = _make_mission(source_request=sr)
        result = mission_linkage(m)
        assert result is not None
        assert result["source_lane_id"] == "lane-fb"
        assert result["queue_job_id"] == "job-fb"
        assert result["source_board_concurrency_token"] == "tok-fb"

    def test_no_linkage_returns_none(self):
        """When no direct columns and no parseable source_request."""
        m = _make_mission()
        result = mission_linkage(m)
        assert result is None

    def test_non_string_direct_columns_ignored(self):
        """Non-string values in direct columns are treated as None."""
        m = _make_mission(
            queue_job_id=123,
            source_lane_id=["not", "a", "string"],
            source_board_concurrency_token=True,
        )
        result = mission_linkage(m)
        assert result is None

    def test_empty_string_direct_columns_are_still_strings(self):
        """Empty strings are valid strings, so direct columns path is taken."""
        m = _make_mission(queue_job_id="")
        result = mission_linkage(m)
        assert result is not None
        assert result["queue_job_id"] == ""

    def test_direct_columns_take_precedence_over_source_request(self):
        """Direct columns are preferred even when source_request is valid."""
        sr = (
            "Developer control-plane explicit completion write-back "
            "for lane sr-lane from queue job sr-job."
        )
        m = _make_mission(
            queue_job_id="direct-job",
            source_request=sr,
        )
        result = mission_linkage(m)
        assert result is not None
        assert result["queue_job_id"] == "direct-job"
        # source_request is not parsed when direct columns are present
        assert result["source_lane_id"] is None


# ---------------------------------------------------------------------------
# MissionLinkage dataclass
# ---------------------------------------------------------------------------


class TestMissionLinkageDataclass:
    """Tests for the MissionLinkage frozen dataclass."""

    def test_frozen_immutable(self):
        ml = MissionLinkage(queue_job_id="j1")
        with pytest.raises(dataclasses.FrozenInstanceError):
            ml.queue_job_id = "changed"

    def test_defaults_are_none(self):
        ml = MissionLinkage()
        assert ml.queue_job_id is None
        assert ml.source_lane_id is None
        assert ml.source_board_concurrency_token is None

    def test_is_resolved_true_when_any_field_set(self):
        assert MissionLinkage(queue_job_id="j").is_resolved is True
        assert MissionLinkage(source_lane_id="l").is_resolved is True
        assert MissionLinkage(source_board_concurrency_token="t").is_resolved is True

    def test_is_resolved_false_when_all_none(self):
        assert MissionLinkage().is_resolved is False

    def test_to_dict(self):
        ml = MissionLinkage(
            queue_job_id="j1",
            source_lane_id="l1",
            source_board_concurrency_token="t1",
        )
        assert ml.to_dict() == {
            "queue_job_id": "j1",
            "source_lane_id": "l1",
            "source_board_concurrency_token": "t1",
        }

    def test_to_dict_with_nones(self):
        ml = MissionLinkage()
        assert ml.to_dict() == {
            "queue_job_id": None,
            "source_lane_id": None,
            "source_board_concurrency_token": None,
        }

    def test_from_dict(self):
        data = {
            "queue_job_id": "j2",
            "source_lane_id": "l2",
            "source_board_concurrency_token": "t2",
        }
        ml = MissionLinkage.from_dict(data)
        assert ml.queue_job_id == "j2"
        assert ml.source_lane_id == "l2"
        assert ml.source_board_concurrency_token == "t2"

    def test_from_dict_missing_keys_default_to_none(self):
        ml = MissionLinkage.from_dict({})
        assert ml.queue_job_id is None
        assert ml.source_lane_id is None
        assert ml.source_board_concurrency_token is None

    def test_round_trip_to_dict_from_dict(self):
        original = MissionLinkage(
            queue_job_id="j-rt",
            source_lane_id="l-rt",
            source_board_concurrency_token="t-rt",
        )
        restored = MissionLinkage.from_dict(original.to_dict())
        assert restored == original

    def test_from_mission_with_direct_columns(self):
        m = _make_mission(
            queue_job_id="j-fm",
            source_lane_id="l-fm",
            source_board_concurrency_token="t-fm",
        )
        ml = MissionLinkage.from_mission(m)
        assert ml is not None
        assert ml.queue_job_id == "j-fm"
        assert ml.source_lane_id == "l-fm"
        assert ml.source_board_concurrency_token == "t-fm"

    def test_from_mission_with_source_request_fallback(self):
        sr = (
            "Developer control-plane explicit completion write-back "
            "for lane lane-fm from queue job job-fm. "
            "Context: source_board_concurrency_token=tok-fm."
        )
        m = _make_mission(source_request=sr)
        ml = MissionLinkage.from_mission(m)
        assert ml is not None
        assert ml.source_lane_id == "lane-fm"
        assert ml.queue_job_id == "job-fm"
        assert ml.source_board_concurrency_token == "tok-fm"

    def test_from_mission_returns_none_when_no_linkage(self):
        m = _make_mission()
        ml = MissionLinkage.from_mission(m)
        assert ml is None


# ---------------------------------------------------------------------------
# MissionEntity dataclass
# ---------------------------------------------------------------------------


class TestMissionEntity:
    """Tests for the MissionEntity frozen dataclass."""

    def test_frozen_immutable(self):
        entity = MissionEntity(mission_id="m1")
        with pytest.raises(dataclasses.FrozenInstanceError):
            entity.mission_id = "changed"

    def test_defaults(self):
        entity = MissionEntity(mission_id="m-defaults")
        assert entity.objective == ""
        assert entity.owner == ""
        assert entity.priority == "p2"
        assert entity.status == "active"
        assert entity.linkage is None
        assert entity.producer_key == "developer-control-plane"
        assert entity.source_request == ""
        assert entity.verification_passed == 0
        assert entity.verification_warned == 0
        assert entity.verification_failed == 0
        assert entity.blocker_count == 0
        assert entity.subtask_count == 0
        assert entity.subtask_completed == 0
        assert entity.evidence_count == 0
        assert entity.decision_count == 0

    def test_all_fields(self):
        linkage = MissionLinkage(queue_job_id="j1", source_lane_id="l1")
        entity = MissionEntity(
            mission_id="m-full",
            objective="Build feature X",
            owner="OmShriMaatreNamaha",
            priority="p1",
            status="completed",
            linkage=linkage,
            producer_key="custom-producer",
            source_request="some request",
            verification_passed=3,
            verification_warned=1,
            verification_failed=0,
            blocker_count=2,
            subtask_count=10,
            subtask_completed=8,
            evidence_count=5,
            decision_count=4,
        )
        assert entity.mission_id == "m-full"
        assert entity.objective == "Build feature X"
        assert entity.owner == "OmShriMaatreNamaha"
        assert entity.priority == "p1"
        assert entity.status == "completed"
        assert entity.linkage is linkage
        assert entity.linkage.is_resolved is True
        assert entity.producer_key == "custom-producer"
        assert entity.source_request == "some request"
        assert entity.verification_passed == 3
        assert entity.verification_warned == 1
        assert entity.verification_failed == 0
        assert entity.blocker_count == 2
        assert entity.subtask_count == 10
        assert entity.subtask_completed == 8
        assert entity.evidence_count == 5
        assert entity.decision_count == 4

    def test_linkage_none_by_default(self):
        entity = MissionEntity(mission_id="m-no-link")
        assert entity.linkage is None

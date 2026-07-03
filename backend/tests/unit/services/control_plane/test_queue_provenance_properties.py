"""
Property-based tests for Queue Derivation Provenance.

Uses Hypothesis to validate that queue entries derived from board lanes
with active status and complete review gates always include correct
provenance referencing the source lane ID and board concurrency token.

Feature: control-plane-kernel-extraction
Property 2: Queue Derivation Provenance

**Validates: Requirements 5.4, 6.1, 6.2**
"""

from __future__ import annotations

import string

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.control_plane.domain.lane import (
    lane_has_queue_export_reviews,
)
from app.control_plane.domain.validation import (
    DomainValidationError,
    validate_queue_entry,
)
from app.control_plane.orchestration.queue_materializer import QueueMaterializer


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Non-empty ASCII printable strings suitable for IDs and text fields
_ascii_text_st = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S", "Z"),
        whitelist_characters=" ",
        max_codepoint=127,
    ),
    min_size=1,
    max_size=80,
).filter(lambda s: s.strip() != "" and s.isascii())

# Lane IDs: short alphanumeric identifiers
_lane_id_st = st.text(
    alphabet=string.ascii_lowercase + string.digits + "-",
    min_size=1,
    max_size=30,
).filter(lambda s: s.strip() != "" and s[0].isalnum())

# Board concurrency tokens: hex-like strings simulating SHA256 tokens
_board_token_st = st.text(
    alphabet=string.hexdigits.lower(),
    min_size=8,
    max_size=64,
).filter(lambda s: len(s) >= 8)


def _complete_review_gate_st():
    """Strategy producing a complete review gate dict."""
    return st.fixed_dictionaries({
        "reviewed_by": _ascii_text_st,
        "summary": _ascii_text_st,
        "reviewed_at": _ascii_text_st,
        "evidence": st.lists(_ascii_text_st, min_size=1, max_size=3),
    })


def _lane_with_reviews_st():
    """Strategy producing a lane dict with active status and complete reviews."""
    return st.fixed_dictionaries({
        "id": _lane_id_st,
        "title": _ascii_text_st,
        "status": st.just("active"),
        "review_state": st.fixed_dictionaries({
            "spec_review": _complete_review_gate_st(),
            "risk_review": _complete_review_gate_st(),
        }),
    })


def _provenance_st(source_lane_id_st, source_board_token_st):
    """Strategy producing a valid provenance dict for a queue entry."""
    return st.fixed_dictionaries({
        "candidateVersion": _ascii_text_st,
        "exportedAt": _ascii_text_st,
        "boardId": _ascii_text_st,
        "boardTitle": _ascii_text_st,
        "sourceBoardConcurrencyToken": source_board_token_st,
        "sourceLaneId": source_lane_id_st,
        "precedence": st.just({
            "canonicalPlanningSource": "active-board",
            "derivedExecutionSurface": "overnight-queue",
            "exportDisposition": "manual-candidate-only",
            "conflictResolution": "board-wins-no-silent-overwrite",
            "staleIfSourceBoardChanges": True,
        }),
    })


def _queue_entry_with_provenance_st(
    source_lane_id_st=None,
    source_board_token_st=None,
):
    """Strategy producing a valid queue entry dict with provenance."""
    lane_id = source_lane_id_st or _lane_id_st
    board_token = source_board_token_st or _board_token_st

    return st.fixed_dictionaries({
        "jobId": _ascii_text_st,
        "title": _ascii_text_st,
        "status": st.just("queued"),
        "priority": st.just("p2"),
        "primaryAgent": _ascii_text_st,
        "supportAgents": st.lists(_ascii_text_st, min_size=0, max_size=2),
        "executionMode": st.just("same-control-plane"),
        "autonomousTrigger": st.just({
            "type": "overnight-window",
            "window": "nightly",
            "enabled": True,
        }),
        "dependsOn": st.just([]),
        "goal": _ascii_text_st,
        "lane": st.fixed_dictionaries({
            "objective": _ascii_text_st,
            "inputs": st.lists(_ascii_text_st, min_size=0, max_size=2),
            "outputs": st.lists(_ascii_text_st, min_size=0, max_size=2),
            "dependencies": st.lists(_ascii_text_st, min_size=0, max_size=2),
            "completion_criteria": st.lists(_ascii_text_st, min_size=1, max_size=2),
        }),
        "successCriteria": st.lists(_ascii_text_st, min_size=1, max_size=2),
        "verification": st.fixed_dictionaries({
            "commands": st.lists(_ascii_text_st, min_size=0, max_size=2),
            "stateRefreshRequired": st.just(True),
        }),
        "provenance": _provenance_st(lane_id, board_token),
    })


# ---------------------------------------------------------------------------
# Property 2: Queue Derivation Provenance
# ---------------------------------------------------------------------------


class TestCreateLaneQueueJobIdEncoding:
    """Property 2a: create_lane_queue_job_id encodes the source lane ID.

    **Validates: Requirements 5.4, 6.1, 6.2**
    """

    @given(lane_id=_lane_id_st, board_token=_board_token_st)
    @settings(max_examples=100)
    def test_job_id_encodes_source_lane_id(
        self, lane_id: str, board_token: str
    ):
        """**Validates: Requirements 5.4, 6.1, 6.2**

        For any lane ID and board token, the derived job ID SHALL contain
        the source lane ID, making provenance traceable from the job ID alone.
        """
        job_id = QueueMaterializer.create_lane_queue_job_id(lane_id, board_token)
        assert lane_id in job_id, (
            f"Job ID '{job_id}' must encode source lane ID '{lane_id}'"
        )

    @given(lane_id=_lane_id_st, board_token=_board_token_st)
    @settings(max_examples=100)
    def test_job_id_has_overnight_lane_prefix(
        self, lane_id: str, board_token: str
    ):
        """**Validates: Requirements 5.4, 6.1, 6.2**

        The derived job ID SHALL start with the 'overnight-lane-' prefix,
        identifying it as a lane-derived queue job.
        """
        job_id = QueueMaterializer.create_lane_queue_job_id(lane_id, board_token)
        assert job_id.startswith("overnight-lane-"), (
            f"Job ID '{job_id}' must start with 'overnight-lane-'"
        )

    @given(lane_id=_lane_id_st, board_token=_board_token_st)
    @settings(max_examples=100)
    def test_job_id_is_deterministic(
        self, lane_id: str, board_token: str
    ):
        """**Validates: Requirements 5.4, 6.1, 6.2**

        The same lane ID and board token SHALL always produce the same job ID.
        """
        job_id_1 = QueueMaterializer.create_lane_queue_job_id(lane_id, board_token)
        job_id_2 = QueueMaterializer.create_lane_queue_job_id(lane_id, board_token)
        assert job_id_1 == job_id_2


class TestQueueEntryProvenanceValidation:
    """Property 2b: Queue entries with provenance reference source lane and board token.

    **Validates: Requirements 5.4, 6.1, 6.2**
    """

    @given(
        lane_id=_lane_id_st,
        board_token=_board_token_st,
    )
    @settings(max_examples=100)
    def test_validated_provenance_contains_source_lane_id(
        self, lane_id: str, board_token: str
    ):
        """**Validates: Requirements 5.4, 6.1, 6.2**

        For any queue entry with provenance, validate_queue_entry SHALL
        preserve the sourceLaneId in the validated output.
        """
        entry = _build_queue_entry_with_provenance(lane_id, board_token)
        result = validate_queue_entry(entry, existing_job_ids=set())
        assert "provenance" in result
        assert result["provenance"]["sourceLaneId"] == lane_id

    @given(
        lane_id=_lane_id_st,
        board_token=_board_token_st,
    )
    @settings(max_examples=100)
    def test_validated_provenance_contains_source_board_token(
        self, lane_id: str, board_token: str
    ):
        """**Validates: Requirements 5.4, 6.1, 6.2**

        For any queue entry with provenance, validate_queue_entry SHALL
        preserve the sourceBoardConcurrencyToken in the validated output.
        """
        entry = _build_queue_entry_with_provenance(lane_id, board_token)
        result = validate_queue_entry(entry, existing_job_ids=set())
        assert "provenance" in result
        assert result["provenance"]["sourceBoardConcurrencyToken"] == board_token

    @given(entry=_queue_entry_with_provenance_st())
    @settings(max_examples=100)
    def test_provenance_always_has_required_keys(self, entry: dict):
        """**Validates: Requirements 5.4, 6.1, 6.2**

        For any valid queue entry with provenance, the validated provenance
        SHALL always contain both sourceLaneId and sourceBoardConcurrencyToken.
        """
        result = validate_queue_entry(entry, existing_job_ids=set())
        provenance = result.get("provenance")
        assert provenance is not None, "Validated entry must include provenance"
        assert "sourceLaneId" in provenance, (
            "Provenance must contain sourceLaneId"
        )
        assert "sourceBoardConcurrencyToken" in provenance, (
            "Provenance must contain sourceBoardConcurrencyToken"
        )


class TestLaneReviewGateQueueExportEligibility:
    """Property 2c: Lanes with complete spec_review and risk_review are queue-export eligible.

    **Validates: Requirements 5.4, 6.1, 6.2**
    """

    @given(lane=_lane_with_reviews_st())
    @settings(max_examples=100)
    def test_lane_with_complete_reviews_is_export_eligible(
        self, lane: dict
    ):
        """**Validates: Requirements 5.4, 6.1, 6.2**

        For any lane with active status and complete spec_review and
        risk_review gates, lane_has_queue_export_reviews SHALL return True,
        confirming the lane is eligible for queue derivation.
        """
        assert lane_has_queue_export_reviews(lane) is True

    @given(lane=_lane_with_reviews_st())
    @settings(max_examples=50)
    def test_lane_without_spec_review_is_not_export_eligible(
        self, lane: dict
    ):
        """**Validates: Requirements 5.4, 6.1, 6.2**

        Removing spec_review from a lane SHALL make it ineligible for
        queue export.
        """
        del lane["review_state"]["spec_review"]
        assert lane_has_queue_export_reviews(lane) is False

    @given(lane=_lane_with_reviews_st())
    @settings(max_examples=50)
    def test_lane_without_risk_review_is_not_export_eligible(
        self, lane: dict
    ):
        """**Validates: Requirements 5.4, 6.1, 6.2**

        Removing risk_review from a lane SHALL make it ineligible for
        queue export.
        """
        del lane["review_state"]["risk_review"]
        assert lane_has_queue_export_reviews(lane) is False


class TestEndToEndQueueDerivationProvenance:
    """Property 2d: End-to-end queue derivation from lane to validated entry.

    **Validates: Requirements 5.4, 6.1, 6.2**
    """

    @given(
        lane=_lane_with_reviews_st(),
        board_token=_board_token_st,
    )
    @settings(max_examples=100)
    def test_derived_queue_entry_has_provenance_chain(
        self, lane: dict, board_token: str
    ):
        """**Validates: Requirements 5.4, 6.1, 6.2**

        For any board lane with active status and complete reviews, deriving
        a queue job ID and building a queue entry with provenance SHALL
        produce a validated entry where provenance references the original
        source lane ID and board concurrency token.
        """
        source_lane_id = lane["id"]

        # Step 1: Derive job ID (encodes lane ID)
        job_id = QueueMaterializer.create_lane_queue_job_id(
            source_lane_id, board_token
        )
        assert source_lane_id in job_id

        # Step 2: Confirm lane is export-eligible
        assert lane_has_queue_export_reviews(lane) is True

        # Step 3: Build queue entry with provenance
        entry = _build_queue_entry_with_provenance(
            source_lane_id, board_token, job_id=job_id
        )

        # Step 4: Validate the entry
        result = validate_queue_entry(entry, existing_job_ids=set())

        # Step 5: Assert provenance chain is intact
        provenance = result["provenance"]
        assert provenance["sourceLaneId"] == source_lane_id
        assert provenance["sourceBoardConcurrencyToken"] == board_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_queue_entry_with_provenance(
    source_lane_id: str,
    source_board_token: str,
    *,
    job_id: str | None = None,
) -> dict:
    """Build a minimal valid queue entry dict with provenance for testing."""
    if job_id is None:
        job_id = QueueMaterializer.create_lane_queue_job_id(
            source_lane_id, source_board_token
        )
    return {
        "jobId": job_id,
        "title": "test-task",
        "status": "queued",
        "priority": "p2",
        "primaryAgent": "test-agent",
        "supportAgents": [],
        "executionMode": "same-control-plane",
        "autonomousTrigger": {
            "type": "overnight-window",
            "window": "nightly",
            "enabled": True,
        },
        "dependsOn": [],
        "goal": "test-goal",
        "lane": {
            "objective": "test-objective",
            "inputs": [],
            "outputs": [],
            "dependencies": [],
            "completion_criteria": ["done"],
        },
        "successCriteria": ["pass"],
        "verification": {
            "commands": ["make test"],
            "stateRefreshRequired": True,
        },
        "provenance": {
            "candidateVersion": "v1",
            "exportedAt": "2026-01-01T00:00:00Z",
            "boardId": "board-001",
            "boardTitle": "test-board",
            "sourceBoardConcurrencyToken": source_board_token,
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

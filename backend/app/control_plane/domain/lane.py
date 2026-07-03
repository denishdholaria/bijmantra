"""Pure lane domain functions and entities for the Control Plane.

All functions and classes in this module are infrastructure-free: no database,
filesystem, or HTTP imports.  This module encapsulates lane status, review
gates, closure evidence, and lane lookup logic.

Extracted from ``backend/app/api/v2/developer_control_plane.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.control_plane.domain.validation import DomainValidationError


# ---------------------------------------------------------------------------
# Pure helper functions — extracted from developer_control_plane.py
# ---------------------------------------------------------------------------


def has_meaningful_text(value: Any) -> bool:
    """Check if *value* is a non-empty string (after stripping whitespace).

    Returns ``True`` when *value* is a ``str`` with at least one
    non-whitespace character, ``False`` otherwise.
    """
    return isinstance(value, str) and bool(value.strip())


def has_meaningful_text_list(value: Any) -> bool:
    """Check if *value* is a list containing at least one meaningful text.

    Returns ``True`` when *value* is a ``list`` and at least one element
    passes :func:`has_meaningful_text`.
    """
    return isinstance(value, list) and any(has_meaningful_text(item) for item in value)


# ---------------------------------------------------------------------------
# Review gate validation
# ---------------------------------------------------------------------------


def has_complete_review_gate(review_gate: Any) -> bool:
    """Check whether a review gate dict has all required fields populated.

    A complete review gate must be a ``dict`` with meaningful text in
    ``reviewed_by``, ``summary``, ``reviewed_at``, and a meaningful text
    list in ``evidence``.
    """
    return (
        isinstance(review_gate, dict)
        and has_meaningful_text(review_gate.get("reviewed_by"))
        and has_meaningful_text(review_gate.get("summary"))
        and has_meaningful_text(review_gate.get("reviewed_at"))
        and has_meaningful_text_list(review_gate.get("evidence"))
    )


def lane_has_queue_export_reviews(lane: dict[str, Any]) -> bool:
    """Check whether a lane has both spec_review and risk_review completed.

    Returns ``True`` when the lane's ``review_state`` contains complete
    ``spec_review`` and ``risk_review`` gates.
    """
    review_state = lane.get("review_state")
    if not isinstance(review_state, dict):
        return False

    return has_complete_review_gate(
        review_state.get("spec_review")
    ) and has_complete_review_gate(review_state.get("risk_review"))


def lane_has_completion_verification_evidence(lane: dict[str, Any]) -> bool:
    """Check whether a lane has completion verification evidence.

    Returns ``True`` when the lane's ``review_state`` contains a complete
    ``verification_evidence`` gate.
    """
    review_state = lane.get("review_state")
    if not isinstance(review_state, dict):
        return False

    return has_complete_review_gate(review_state.get("verification_evidence"))


# ---------------------------------------------------------------------------
# Lane lookup
# ---------------------------------------------------------------------------


def find_board_lane(
    board_payload: dict[str, Any], lane_id: str
) -> dict[str, Any] | None:
    """Find a lane by ID within a board payload.

    Parameters
    ----------
    board_payload:
        The board payload dict (must contain a ``"lanes"`` list).
    lane_id:
        The lane identifier to search for.

    Returns
    -------
    dict | None
        The matching lane dict, or ``None`` if no lane matches.

    Raises
    ------
    DomainValidationError
        If the board payload is missing a ``"lanes"`` list (status 500).
    """
    lanes = board_payload.get("lanes")
    if not isinstance(lanes, list):
        raise DomainValidationError(
            status_code=500,
            detail="Current active board payload is missing lanes",
        )

    return next(
        (
            entry
            for entry in lanes
            if isinstance(entry, dict) and entry.get("id") == lane_id
        ),
        None,
    )


# ---------------------------------------------------------------------------
# Domain entities — immutable lane state containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReviewGate:
    """Immutable review gate evidence structure.

    Captures the state of a single review gate (e.g. spec_review,
    risk_review, verification_evidence) on a lane.

    Attributes
    ----------
    reviewed_by : str
        Identifier of the reviewer.
    summary : str
        Review summary text.
    reviewed_at : str
        ISO-8601 timestamp of the review.
    evidence : list[str]
        List of evidence references supporting the review.
    """

    reviewed_by: str
    summary: str
    reviewed_at: str
    evidence: list[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Whether this gate has all required fields populated."""
        return (
            bool(self.reviewed_by.strip())
            and bool(self.summary.strip())
            and bool(self.reviewed_at.strip())
            and len(self.evidence) > 0
            and any(
                isinstance(e, str) and bool(e.strip()) for e in self.evidence
            )
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewGate | None:
        """Construct a :class:`ReviewGate` from a dict, or ``None`` if invalid."""
        if not isinstance(data, dict):
            return None
        reviewed_by = data.get("reviewed_by", "")
        summary = data.get("summary", "")
        reviewed_at = data.get("reviewed_at", "")
        evidence = data.get("evidence", [])
        if not isinstance(evidence, list):
            evidence = []
        return cls(
            reviewed_by=reviewed_by if isinstance(reviewed_by, str) else "",
            summary=summary if isinstance(summary, str) else "",
            reviewed_at=reviewed_at if isinstance(reviewed_at, str) else "",
            evidence=[e for e in evidence if isinstance(e, str)],
        )


@dataclass(frozen=True)
class LaneClosure:
    """Immutable closure evidence structure for a completed lane.

    Captures the evidence and metadata associated with lane completion.

    Attributes
    ----------
    closure_summary : str
        Summary of the lane closure.
    evidence : list[str]
        List of evidence references supporting the closure.
    queue_job_id : str
        The queue job ID that produced the closure.
    closeout_receipt : dict[str, Any]
        The closeout receipt associated with the closure.
    """

    closure_summary: str
    evidence: list[str] = field(default_factory=list)
    queue_job_id: str = ""
    closeout_receipt: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LaneEntity:
    """Immutable snapshot of a lane's state within a board.

    This is a domain-layer value object that captures the essential
    identity and status of a lane without any persistence concerns.

    Attributes
    ----------
    lane_id : str
        The unique lane identifier within the board.
    title : str
        Human-readable lane title.
    status : str
        Current lane status (e.g. ``"active"``, ``"completed"``, ``"blocked"``).
    has_queue_export_reviews : bool
        Whether the lane has both spec_review and risk_review completed.
    has_verification_evidence : bool
        Whether the lane has completion verification evidence.
    closure : LaneClosure | None
        Closure evidence if the lane is completed, otherwise ``None``.
    """

    lane_id: str
    title: str
    status: str
    has_queue_export_reviews: bool = False
    has_verification_evidence: bool = False
    closure: LaneClosure | None = None

    @classmethod
    def from_dict(cls, lane: dict[str, Any]) -> LaneEntity:
        """Construct a :class:`LaneEntity` from a lane dict.

        Parameters
        ----------
        lane:
            A lane dict from a board payload.
        """
        closure_data = lane.get("closure")
        closure = None
        if isinstance(closure_data, dict):
            closure = LaneClosure(
                closure_summary=closure_data.get("closure_summary", ""),
                evidence=closure_data.get("evidence", []),
                queue_job_id=closure_data.get("queue_job_id", ""),
                closeout_receipt=closure_data.get("closeout_receipt", {}),
            )

        return cls(
            lane_id=lane.get("id", ""),
            title=lane.get("title", ""),
            status=lane.get("status", ""),
            has_queue_export_reviews=lane_has_queue_export_reviews(lane),
            has_verification_evidence=lane_has_completion_verification_evidence(lane),
            closure=closure,
        )

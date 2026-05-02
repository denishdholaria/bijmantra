"""Internal event schemas for control-plane pub/sub communication.

These models define the event payloads emitted by the control-plane kernel
for internal coordination between layers.  They are NOT part of the external
API contract — the autonomy bridge never sees these directly.

Events follow a consistent envelope: every event carries an ``event_type``
discriminator, an ``organization_id`` scope, and a UTC ``occurred_at``
timestamp so that consumers can filter, route, and order without inspecting
the payload body.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return the current UTC timestamp (test-friendly factory)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Board state changed
# ---------------------------------------------------------------------------


class BoardStateChangedEvent(BaseModel):
    """Emitted when the canonical board state is created, updated, or restored.

    Consumers can use ``previous_concurrency_token`` vs
    ``concurrency_token`` to detect whether the change was a no-op
    (tokens equal) or a real mutation.
    """

    event_type: str = Field(default="board_state_changed", frozen=True)
    organization_id: int
    board_id: str
    concurrency_token: str
    previous_concurrency_token: str | None = None
    change_source: str = Field(
        ...,
        description=(
            "Origin of the change, e.g. 'save', 'restore', "
            "'completion-write-back'."
        ),
    )
    changed_by_user_id: int | None = None
    summary_metadata: dict[str, Any] | None = None
    occurred_at: datetime = Field(default_factory=_utc_now)


# ---------------------------------------------------------------------------
# Queue entry written
# ---------------------------------------------------------------------------


class QueueEntryWrittenEvent(BaseModel):
    """Emitted when a reviewed queue entry is persisted to the overnight queue.

    The ``queue_sha256`` field captures the queue hash *after* the write so
    that downstream consumers can perform optimistic-lock checks without
    re-reading the queue file.
    """

    event_type: str = Field(default="queue_entry_written", frozen=True)
    organization_id: int
    board_id: str
    queue_job_id: str
    source_lane_id: str
    source_board_concurrency_token: str
    queue_sha256: str
    operator_intent: str
    replaced: bool = False
    occurred_at: datetime = Field(default_factory=_utc_now)


# ---------------------------------------------------------------------------
# Lane completion
# ---------------------------------------------------------------------------


class LaneCompletionEvent(BaseModel):
    """Emitted when a lane is marked completed via a completion write-back.

    Carries enough context for the orchestration layer to trigger downstream
    side-effects (mission state update, learning ledger entry, etc.) without
    re-querying the board.
    """

    event_type: str = Field(default="lane_completion", frozen=True)
    organization_id: int
    board_id: str
    source_lane_id: str
    queue_job_id: str
    queue_sha256: str
    concurrency_token: str
    closure_summary: str
    evidence_refs: list[str] = []
    approval_receipt_id: int | None = None
    occurred_at: datetime = Field(default_factory=_utc_now)


# ---------------------------------------------------------------------------
# Mission bootstrap
# ---------------------------------------------------------------------------


class MissionBootstrapEvent(BaseModel):
    """Emitted when a mission is bootstrapped from a closeout receipt.

    The ``action`` field mirrors the bootstrap response vocabulary:
    ``'created'``, ``'existing'``, ``'missing-receipt'``, or
    ``'missing-mission-id'``.
    """

    event_type: str = Field(default="mission_bootstrap", frozen=True)
    organization_id: int
    mission_id: str | None = None
    queue_job_id: str
    source_lane_id: str | None = None
    source_board_concurrency_token: str | None = None
    action: str = Field(
        ...,
        description=(
            "Bootstrap outcome: 'created', 'existing', "
            "'missing-receipt', or 'missing-mission-id'."
        ),
    )
    occurred_at: datetime = Field(default_factory=_utc_now)

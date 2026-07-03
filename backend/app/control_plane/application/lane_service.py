"""Lane application service — completion workflow, approval receipts, conflict learning.

Application-layer home for lane-related write operations requiring
infrastructure (SQLAlchemy ``AsyncSession``).

Extracted from ``backend/app/api/v2/developer_control_plane.py``.
Requirements: 9.2, 9.5, 9.6
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneApprovalReceiptResponse,
)
from app.control_plane.domain.validation import (
    best_effort_ascii_text,
)
from app.models.core import User
from app.models.developer_control_plane import (
    DeveloperControlPlaneApprovalReceipt,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APPROVAL_RECEIPT_AUTHORITY_SOURCE = "developer-control-plane-api"

# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _deduplicate_strings(values: list[str]) -> list[str]:
    """Return *values* with duplicates and blank entries removed, preserving order."""
    deduplicated: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduplicated.append(normalized)
    return deduplicated


def _learning_conflict_entry_type(reason: str) -> str:
    if reason in {"closeout-receipt-mismatch", "completion-overwrite-conflict"}:
        return "incident"
    return "pitfall"


def _learning_conflict_target(
    source_lane_id: str | None,
    queue_job_id: str | None,
) -> str:
    if source_lane_id is not None:
        return f"lane {source_lane_id}"
    if queue_job_id is not None:
        return f"queue job {queue_job_id}"
    return "developer control plane"


def _learning_conflict_title(
    scope: str,
    reason: str,
    source_lane_id: str | None,
    queue_job_id: str | None,
) -> str:
    scope_label = "Queue export" if scope == "queue-export" else "Completion write-back"
    return (
        f"{scope_label} conflict {reason} for "
        f"{_learning_conflict_target(source_lane_id, queue_job_id)}"
    )


def _learning_conflict_summary(conflict_detail: dict[str, Any]) -> str:
    detail_message = conflict_detail.get("detail")
    remediation_message = conflict_detail.get("remediation_message")
    summary_parts: list[str] = []
    if isinstance(detail_message, str) and detail_message.strip():
        summary_parts.append(detail_message.strip().rstrip("."))
    if isinstance(remediation_message, str) and remediation_message.strip():
        summary_parts.append(f"Remediation: {remediation_message.strip()}")
    return " ".join(summary_parts)


def _learning_conflict_evidence_refs(
    *,
    board_id: str | None,
    source_lane_id: str | None,
    queue_job_id: str | None,
    source_board_concurrency_token: str | None,
    conflict_detail: dict[str, Any],
) -> list[str]:
    evidence_refs: list[str] = []
    if board_id is not None:
        evidence_refs.append(f"developer-control-plane:board:{board_id}")
    if source_lane_id is not None:
        evidence_refs.append(f"developer-control-plane:lane:{source_lane_id}")
    if queue_job_id is not None:
        evidence_refs.append(f"developer-control-plane:queue-job:{queue_job_id}")
    if source_board_concurrency_token is not None:
        evidence_refs.append(
            f"developer-control-plane:board-token:{source_board_concurrency_token}"
        )
    current_queue_sha256 = conflict_detail.get("current_queue_sha256")
    if (
        isinstance(current_queue_sha256, str)
        and current_queue_sha256.strip()
        and current_queue_sha256.isascii()
    ):
        evidence_refs.append(
            f"developer-control-plane:queue-sha:{current_queue_sha256}"
        )
    return _deduplicate_strings(evidence_refs)


# ---------------------------------------------------------------------------
# Lane completion builders
# ---------------------------------------------------------------------------


def build_lane_completion(
    *,
    queue_job_id: str,
    queue_sha256: str,
    source_board_concurrency_token: str,
    closure_summary: str,
    evidence: list[str],
    closeout_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a lane completion dict ready for board persistence."""
    completion: dict[str, Any] = {
        "queue_job_id": queue_job_id,
        "queue_sha256": queue_sha256,
        "source_board_concurrency_token": source_board_concurrency_token,
        "closure_summary": closure_summary,
        "evidence": evidence,
        "completed_at": datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
    }
    if closeout_receipt is not None:
        completion["closeout_receipt"] = closeout_receipt
    return completion


def is_same_lane_completion(
    existing_closure: Any,
    *,
    queue_job_id: str,
    queue_sha256: str,
    source_board_concurrency_token: str,
    closure_summary: str,
    evidence: list[str],
    closeout_receipt: dict[str, Any] | None,
) -> bool:
    """Check whether *existing_closure* matches the given completion fields."""
    return (
        isinstance(existing_closure, dict)
        and existing_closure.get("queue_job_id") == queue_job_id
        and existing_closure.get("queue_sha256") == queue_sha256
        and existing_closure.get("source_board_concurrency_token")
        == source_board_concurrency_token
        and existing_closure.get("closure_summary") == closure_summary
        and existing_closure.get("evidence") == evidence
        and existing_closure.get("closeout_receipt") == closeout_receipt
    )


class LaneService:
    """Application service for lane completion workflow and approval receipts.

    Accepts an ``AsyncSession`` as a constructor dependency so that
    callers control transaction boundaries.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Approval receipt operations
    # ------------------------------------------------------------------

    @staticmethod
    def approval_receipt_response(
        record: DeveloperControlPlaneApprovalReceipt,
    ) -> DeveloperControlPlaneApprovalReceiptResponse:
        """Build an API response model from a persisted approval receipt."""
        return DeveloperControlPlaneApprovalReceiptResponse(
            receipt_id=record.id,
            organization_id=record.organization_id,
            action_type=record.action_type,
            outcome=record.outcome,
            authority_actor_user_id=record.authority_actor_user_id,
            authority_actor_email=record.authority_actor_email,
            authority_source=record.authority_source,
            board_id=record.board_id,
            source_board_concurrency_token=record.source_board_concurrency_token,
            resulting_board_concurrency_token=record.resulting_board_concurrency_token,
            source_lane_id=record.source_lane_id,
            queue_job_id=record.queue_job_id,
            expected_queue_sha256=record.expected_queue_sha256,
            resulting_queue_sha256=record.resulting_queue_sha256,
            target_revision_id=record.target_revision_id,
            previous_active_concurrency_token=record.previous_active_concurrency_token,
            linked_mission_id=record.linked_mission_id,
            rationale=record.rationale,
            evidence_refs=record.evidence_refs,
            summary_metadata=record.summary_metadata,
            recorded_at=record.created_at,
        )

    async def get_latest_approval_receipt(
        self,
        organization_id: int,
        *conditions: Any,
    ) -> DeveloperControlPlaneApprovalReceipt | None:
        """Query the latest approval receipt matching *conditions*."""
        result = await self._db.execute(
            select(DeveloperControlPlaneApprovalReceipt)
            .where(
                DeveloperControlPlaneApprovalReceipt.organization_id
                == organization_id,
                *conditions,
            )
            .order_by(
                DeveloperControlPlaneApprovalReceipt.created_at.desc(),
                DeveloperControlPlaneApprovalReceipt.id.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def record_approval_receipt(
        self,
        organization_id: int,
        current_user: User,
        *,
        action_type: str,
        outcome: str,
        board_id: str,
        rationale: str,
        evidence_refs: list[str],
        source_board_concurrency_token: str | None = None,
        resulting_board_concurrency_token: str | None = None,
        source_lane_id: str | None = None,
        queue_job_id: str | None = None,
        expected_queue_sha256: str | None = None,
        resulting_queue_sha256: str | None = None,
        target_revision_id: int | None = None,
        previous_active_concurrency_token: str | None = None,
        linked_mission_id: str | None = None,
        summary_metadata: dict[str, Any] | None = None,
    ) -> DeveloperControlPlaneApprovalReceipt:
        """Create a new approval receipt and flush it to the session."""
        receipt = DeveloperControlPlaneApprovalReceipt(
            organization_id=organization_id,
            action_type=action_type,
            outcome=outcome,
            authority_actor_user_id=current_user.id,
            authority_actor_email=getattr(current_user, "email", None),
            authority_source=APPROVAL_RECEIPT_AUTHORITY_SOURCE,
            board_id=board_id,
            source_board_concurrency_token=source_board_concurrency_token,
            resulting_board_concurrency_token=resulting_board_concurrency_token,
            source_lane_id=source_lane_id,
            queue_job_id=queue_job_id,
            expected_queue_sha256=expected_queue_sha256,
            resulting_queue_sha256=resulting_queue_sha256,
            target_revision_id=target_revision_id,
            previous_active_concurrency_token=previous_active_concurrency_token,
            linked_mission_id=linked_mission_id,
            rationale=rationale,
            evidence_refs=_deduplicate_strings(evidence_refs),
            summary_metadata=summary_metadata,
        )
        self._db.add(receipt)
        await self._db.flush()
        return receipt

    # ------------------------------------------------------------------
    # Conflict learning persistence
    # ------------------------------------------------------------------

    async def persist_conflict_learning(
        self,
        organization_id: int,
        current_user: User,
        *,
        scope: str,
        conflict_detail: dict[str, Any],
        board_id: str | None,
        source_lane_id: str | None,
        queue_job_id: str | None,
        source_board_concurrency_token: str | None,
        linked_mission_id: str | None = None,
    ) -> None:
        """Persist a conflict learning entry to the learning ledger.

        Silently returns when the conflict detail lacks a usable
        ``conflict_reason`` or summary.  Commits or rolls back its own
        transaction.
        """
        reason = conflict_detail.get("conflict_reason")
        if not isinstance(reason, str) or not reason:
            return

        normalized_board_id = best_effort_ascii_text(board_id)
        normalized_source_lane_id = best_effort_ascii_text(source_lane_id)
        normalized_queue_job_id = best_effort_ascii_text(queue_job_id)
        normalized_board_token = best_effort_ascii_text(
            source_board_concurrency_token
        )
        normalized_linked_mission_id = best_effort_ascii_text(linked_mission_id)
        summary = _learning_conflict_summary(conflict_detail)
        if not summary:
            return

        summary_metadata: dict[str, Any] = {
            key: value
            for key, value in conflict_detail.items()
            if key != "detail"
        }
        summary_metadata["conflict_scope"] = scope
        if normalized_board_token is not None:
            summary_metadata["source_board_concurrency_token"] = (
                normalized_board_token
            )

        try:
            # _record_learning_entry is still shared with other callers in
            # developer_control_plane.py and will be fully extracted in a
            # later task.  Use a lazy import to avoid circular dependencies.
            from app.api.bijmantra.developer.developer_control_plane import (
                _record_learning_entry,
            )

            await _record_learning_entry(
                self._db,
                organization_id,
                entry_type=_learning_conflict_entry_type(reason),
                source_classification="queue-conflict",
                title=_learning_conflict_title(
                    scope,
                    reason,
                    normalized_source_lane_id,
                    normalized_queue_job_id,
                ),
                summary=summary,
                confidence_score=(
                    0.95
                    if _learning_conflict_entry_type(reason) == "incident"
                    else 0.9
                ),
                recorded_by_user_id=current_user.id,
                recorded_by_email=getattr(current_user, "email", None),
                board_id=normalized_board_id,
                source_lane_id=normalized_source_lane_id,
                queue_job_id=normalized_queue_job_id,
                linked_mission_id=normalized_linked_mission_id,
                approval_receipt_id=None,
                source_reference=(
                    f"queue-conflict:{scope}:{reason}:"
                    f"{normalized_source_lane_id or '-'}:"
                    f"{normalized_queue_job_id or '-'}:"
                    f"{normalized_board_token or '-'}"
                ),
                evidence_refs=_learning_conflict_evidence_refs(
                    board_id=normalized_board_id,
                    source_lane_id=normalized_source_lane_id,
                    queue_job_id=normalized_queue_job_id,
                    source_board_concurrency_token=normalized_board_token,
                    conflict_detail=conflict_detail,
                ),
                summary_metadata=summary_metadata,
            )
            await self._db.commit()
        except Exception:
            await self._db.rollback()

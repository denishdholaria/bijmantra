"""Lane service for developer control plane.

Handles lane/board CRUD, state transitions, queue management, and completion workflows.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.developer_control_plane import (
    DeveloperControlPlaneActiveBoard,
    DeveloperControlPlaneApprovalReceipt,
    DeveloperControlPlaneBoardRevision,
    DeveloperControlPlaneLearningEntry,
)
from app.models.core import User
from app.schemas.developer_control_plane import (
    DEVELOPER_MASTER_BOARD_ID,
    build_developer_master_board_summary,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QUEUE_LANGUAGE = "en"
QUEUE_VOCABULARY_POLICY = "english-technical-only"
QUEUE_WRITE_OPERATOR_INTENT = "write-reviewed-queue-entry"
COMPLETION_WRITE_OPERATOR_INTENT = "write-reviewed-lane-completion"
APPROVAL_RECEIPT_AUTHORITY_SOURCE = "developer-control-plane-api"


# ---------------------------------------------------------------------------
# Queue helpers
# ---------------------------------------------------------------------------

def default_queue_payload() -> dict[str, Any]:
    """Generate the default overnight queue payload structure."""
    return {
        "version": 1,
        "updatedAt": None,
        "language": QUEUE_LANGUAGE,
        "vocabularyPolicy": QUEUE_VOCABULARY_POLICY,
        "defaults": {
            "window": "nightly",
            "stateRefreshRequired": True,
            "closeoutCommands": ["make update-state"],
            "maxJobsPerRun": 2,
        },
        "jobs": [],
    }


def queue_sha256(payload: dict[str, Any]) -> str:
    """Compute SHA-256 hash of the queue payload."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def load_overnight_queue_payload(overnight_queue_path: Path) -> tuple[dict[str, Any], bool]:
    """Load the overnight queue payload from the filesystem.

    Returns:
        Tuple of (payload, exists) where exists is False if the file was missing or malformed.
    """
    if not overnight_queue_path.exists():
        return default_queue_payload(), False

    try:
        payload = json.loads(overnight_queue_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        malformed = default_queue_payload()
        malformed["malformed_artifact"] = True
        malformed["error"] = str(exc)
        return malformed, False

    if not isinstance(payload, dict):
        malformed = default_queue_payload()
        malformed["malformed_artifact"] = True
        malformed["error"] = "Overnight queue payload must be a JSON object"
        return malformed, False

    return payload, True


def load_active_board_payload(record: DeveloperControlPlaneActiveBoard) -> dict[str, Any]:
    """Load and validate the active board payload from a database record.

    Raises:
        HTTPException: If the board JSON is invalid or missing lanes.
    """
    try:
        payload = json.loads(record.canonical_board_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current active board payload is not valid JSON",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current active board payload must be a JSON object",
        )

    lanes = payload.get("lanes")
    if not isinstance(lanes, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current active board payload is missing lanes",
        )

    return payload


def validate_queue_payload_shape(
    payload: dict[str, Any],
    queue_language: str = QUEUE_LANGUAGE,
    queue_vocabulary_policy: str = QUEUE_VOCABULARY_POLICY,
) -> dict[str, Any]:
    """Validate the structural shape of a queue payload.

    Raises:
        HTTPException: If the payload is structurally invalid.
    """
    defaults = payload.get("defaults")
    jobs = payload.get("jobs")

    if payload.get("language") != queue_language:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Overnight queue payload must declare language=en",
        )
    if payload.get("vocabularyPolicy") != queue_vocabulary_policy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Overnight queue payload must declare vocabularyPolicy=english-technical-only",
        )
    if not isinstance(defaults, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Overnight queue payload defaults must be an object",
        )
    if not isinstance(jobs, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Overnight queue payload jobs must be a list",
        )

    return payload


def serialize_queue_payload(
    payload: dict[str, Any],
    queue_language: str = QUEUE_LANGUAGE,
    queue_vocabulary_policy: str = QUEUE_VOCABULARY_POLICY,
) -> str:
    """Serialize the queue payload to a stable JSON string."""
    stable_payload = {
        "version": payload.get("version", 1),
        "updatedAt": payload.get("updatedAt"),
        "language": payload.get("language", queue_language),
        "vocabularyPolicy": payload.get("vocabularyPolicy", queue_vocabulary_policy),
        "defaults": payload.get("defaults", default_queue_payload()["defaults"]),
        "jobs": payload.get("jobs", []),
    }
    return f"{json.dumps(stable_payload, indent=2, ensure_ascii=True)}\n"


def write_overnight_queue_payload(
    payload: dict[str, Any],
    overnight_queue_path: Path,
) -> None:
    """Write the queue payload to the filesystem.

    Raises:
        HTTPException: If the file cannot be written.
    """
    try:
        overnight_queue_path.parent.mkdir(parents=True, exist_ok=True)
        overnight_queue_path.write_text(serialize_queue_payload(payload), encoding="utf-8")
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to write overnight queue file",
        ) from exc


def find_queue_job(queue_payload: dict[str, Any], queue_job_id: str) -> dict[str, Any] | None:
    """Find a job in the queue payload by job ID."""
    for job in queue_payload.get("jobs", []):
        if isinstance(job, dict) and job.get("jobId") == queue_job_id:
            return job
    return None


def find_board_lane(board_payload: dict[str, Any], lane_id: str) -> dict[str, Any] | None:
    """Find a lane in the board payload by lane ID.

    Raises:
        HTTPException: If the board payload is missing lanes.
    """
    lanes = board_payload.get("lanes")
    if not isinstance(lanes, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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


def queue_token_suffix(source_board_concurrency_token: str) -> str:
    """Derive a short suffix from a board concurrency token for job ID generation."""
    normalized = "".join(
        character
        for character in source_board_concurrency_token.lower()
        if character.isascii() and character.isalnum()
    )[:8]
    return normalized or "unknown000"


def create_lane_queue_job_id(
    source_lane_id: str,
    source_board_concurrency_token: str,
) -> str:
    """Create a deterministic queue job ID from a lane ID and board token."""
    return f"overnight-lane-{source_lane_id}-{queue_token_suffix(source_board_concurrency_token)}"


def build_lane_completion(
    *,
    queue_job_id: str,
    queue_sha256_value: str,
    source_board_concurrency_token: str,
    closure_summary: str,
    evidence: list[str],
    closeout_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a lane completion dict for embedding in the board payload."""
    completion: dict[str, Any] = {
        "queue_job_id": queue_job_id,
        "queue_sha256": queue_sha256_value,
        "source_board_concurrency_token": source_board_concurrency_token,
        "closure_summary": closure_summary,
        "evidence": evidence,
        "completed_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ),
    }
    if closeout_receipt is not None:
        completion["closeout_receipt"] = closeout_receipt
    return completion


def is_same_lane_completion(
    existing_closure: Any,
    *,
    queue_job_id: str,
    queue_sha256_value: str,
    source_board_concurrency_token: str,
    closure_summary: str,
    evidence: list[str],
    closeout_receipt: dict[str, Any] | None,
) -> bool:
    """Check whether an existing closure matches the proposed completion exactly."""
    return (
        isinstance(existing_closure, dict)
        and existing_closure.get("queue_job_id") == queue_job_id
        and existing_closure.get("queue_sha256") == queue_sha256_value
        and existing_closure.get("source_board_concurrency_token") == source_board_concurrency_token
        and existing_closure.get("closure_summary") == closure_summary
        and existing_closure.get("evidence") == evidence
        and existing_closure.get("closeout_receipt") == closeout_receipt
    )


# ---------------------------------------------------------------------------
# Lane review gate helpers
# ---------------------------------------------------------------------------

def has_meaningful_text(value: Any) -> bool:
    """Return True if value is a non-empty string."""
    return isinstance(value, str) and bool(value.strip())


def has_meaningful_text_list(value: Any) -> bool:
    """Return True if value is a list with at least one non-empty string."""
    return isinstance(value, list) and any(has_meaningful_text(item) for item in value)


def has_complete_review_gate(review_gate: Any) -> bool:
    """Return True if a review gate dict has all required fields populated."""
    return (
        isinstance(review_gate, dict)
        and has_meaningful_text(review_gate.get("reviewed_by"))
        and has_meaningful_text(review_gate.get("summary"))
        and has_meaningful_text(review_gate.get("reviewed_at"))
        and has_meaningful_text_list(review_gate.get("evidence"))
    )


def lane_has_queue_export_reviews(lane: dict[str, Any]) -> bool:
    """Return True if the lane has both spec_review and risk_review gates completed."""
    review_state = lane.get("review_state")
    if not isinstance(review_state, dict):
        return False

    return has_complete_review_gate(review_state.get("spec_review")) and has_complete_review_gate(
        review_state.get("risk_review")
    )


def lane_has_completion_verification_evidence(lane: dict[str, Any]) -> bool:
    """Return True if the lane has a completed verification_evidence review gate."""
    review_state = lane.get("review_state")
    if not isinstance(review_state, dict):
        return False

    return has_complete_review_gate(review_state.get("verification_evidence"))


# ---------------------------------------------------------------------------
# Board persistence helpers
# ---------------------------------------------------------------------------

def hash_canonical_board_json(canonical_board_json: str) -> str:
    """Compute SHA-256 hash of the canonical board JSON string."""
    return hashlib.sha256(canonical_board_json.encode("utf-8")).hexdigest()


def build_summary_metadata(
    board: Any,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build summary metadata for a board record."""
    summary_metadata = build_developer_master_board_summary(board)
    if extra_metadata is not None:
        summary_metadata = {**summary_metadata, **extra_metadata}
    return summary_metadata


async def get_active_board(
    db: AsyncSession,
    organization_id: int,
) -> DeveloperControlPlaneActiveBoard | None:
    """Fetch the active board record for an organization."""
    result = await db.execute(
        select(DeveloperControlPlaneActiveBoard).where(
            DeveloperControlPlaneActiveBoard.organization_id == organization_id,
            DeveloperControlPlaneActiveBoard.board_id == DEVELOPER_MASTER_BOARD_ID,
        )
    )
    return result.scalar_one_or_none()


async def get_board_versions(
    db: AsyncSession,
    organization_id: int,
) -> list[DeveloperControlPlaneBoardRevision]:
    """List all board revisions for an organization, newest first."""
    result = await db.execute(
        select(DeveloperControlPlaneBoardRevision)
        .where(
            DeveloperControlPlaneBoardRevision.organization_id == organization_id,
            DeveloperControlPlaneBoardRevision.board_id == DEVELOPER_MASTER_BOARD_ID,
        )
        .order_by(
            DeveloperControlPlaneBoardRevision.created_at.desc(),
            DeveloperControlPlaneBoardRevision.id.desc(),
        )
    )
    return list(result.scalars().all())


async def get_board_revision(
    db: AsyncSession,
    organization_id: int,
    revision_id: int,
) -> DeveloperControlPlaneBoardRevision | None:
    """Fetch a specific board revision by ID."""
    result = await db.execute(
        select(DeveloperControlPlaneBoardRevision).where(
            DeveloperControlPlaneBoardRevision.id == revision_id,
            DeveloperControlPlaneBoardRevision.organization_id == organization_id,
            DeveloperControlPlaneBoardRevision.board_id == DEVELOPER_MASTER_BOARD_ID,
        )
    )
    return result.scalar_one_or_none()


async def apply_active_board_state(
    db: AsyncSession,
    organization_id: int,
    current_user: User,
    current_record: DeveloperControlPlaneActiveBoard | None,
    *,
    canonical_board_json: str,
    board: Any,
    save_source: str,
    summary_metadata: dict[str, Any],
) -> DeveloperControlPlaneActiveBoard:
    """Apply a new board state, creating or updating the active board record and adding a revision.

    Returns:
        The updated or newly created active board record.
    """
    previous_board_hash = current_record.canonical_board_hash if current_record is not None else None
    board_hash = hash_canonical_board_json(canonical_board_json)

    if current_record is None:
        current_record = DeveloperControlPlaneActiveBoard(
            organization_id=organization_id,
            board_id=board.board_id,
            schema_version=board.version,
            visibility=board.visibility,
            canonical_board_json=canonical_board_json,
            canonical_board_hash=board_hash,
            updated_by_user_id=current_user.id,
            save_source=save_source,
            summary_metadata=summary_metadata,
        )
        db.add(current_record)
    else:
        current_record.schema_version = board.version
        current_record.visibility = board.visibility
        current_record.canonical_board_json = canonical_board_json
        current_record.canonical_board_hash = board_hash
        current_record.updated_by_user_id = current_user.id
        current_record.save_source = save_source
        current_record.summary_metadata = summary_metadata

    await db.flush()

    if previous_board_hash != board_hash:
        db.add(
            DeveloperControlPlaneBoardRevision(
                organization_id=organization_id,
                board_id=board.board_id,
                schema_version=board.version,
                visibility=board.visibility,
                canonical_board_json=canonical_board_json,
                canonical_board_hash=board_hash,
                saved_by_user_id=current_user.id,
                save_source=save_source,
                summary_metadata=summary_metadata,
            )
        )

    return current_record


# ---------------------------------------------------------------------------
# Approval receipt helpers
# ---------------------------------------------------------------------------

def deduplicate_strings(values: list[str]) -> list[str]:
    """Deduplicate a list of strings while preserving order."""
    deduplicated: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduplicated.append(normalized)
    return deduplicated


def review_gate_evidence_refs(lane: dict[str, Any], *review_gate_names: str) -> list[str]:
    """Collect evidence refs from named review gates in a lane."""
    review_state = lane.get("review_state")
    if not isinstance(review_state, dict):
        return []

    evidence_refs: list[str] = []
    for review_gate_name in review_gate_names:
        review_gate = review_state.get(review_gate_name)
        if not isinstance(review_gate, dict):
            continue
        gate_evidence = review_gate.get("evidence")
        if not isinstance(gate_evidence, list):
            continue
        evidence_refs.extend(
            item for item in gate_evidence if isinstance(item, str) and item.strip()
        )

    return deduplicate_strings(evidence_refs)


async def get_latest_approval_receipt(
    db: AsyncSession,
    organization_id: int,
    *conditions: Any,
) -> DeveloperControlPlaneApprovalReceipt | None:
    """Fetch the most recent approval receipt matching the given conditions."""
    result = await db.execute(
        select(DeveloperControlPlaneApprovalReceipt)
        .where(
            DeveloperControlPlaneApprovalReceipt.organization_id == organization_id,
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
    db: AsyncSession,
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
    """Create and persist an approval receipt record."""
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
        evidence_refs=deduplicate_strings(evidence_refs),
        summary_metadata=summary_metadata,
    )
    db.add(receipt)
    await db.flush()
    return receipt


# ---------------------------------------------------------------------------
# Conflict detail builders
# ---------------------------------------------------------------------------

def queue_write_conflict_detail(
    reason: str, detail: str, **extra: Any
) -> dict[str, Any]:
    """Build a structured conflict detail dict for queue write failures."""
    remediation_message = {
        "lane-review-missing": (
            "Update the canonical lane with explicit spec_review and risk_review evidence, "
            "save the shared board, then retry queue export from the current board token."
        ),
        "missing-active-board": (
            "Restore or resave the shared active board first. Queue writes stay blocked "
            "until shared board provenance exists."
        ),
        "stale-board-token": (
            "Refresh the shared board state, confirm the selected lane still "
            "materializes to the intended queue entry, then retry with the current "
            "board token."
        ),
        "queue-sha-mismatch": (
            "Refresh queue status, compare the latest queue hash shown here, then retry "
            "only if the reviewed queue entry is still valid."
        ),
        "duplicate-job-id": (
            "Do not overwrite. Inspect whether the existing queued job already "
            "represents this lane and token pair, or regenerate from a newer board token "
            "if the board changed."
        ),
    }[reason]
    refresh_targets = {
        "lane-review-missing": ["active-board"],
        "missing-active-board": ["active-board"],
        "stale-board-token": ["active-board"],
        "queue-sha-mismatch": ["overnight-queue"],
        "duplicate-job-id": ["overnight-queue", "active-board"],
    }[reason]
    retry_permitted_after_refresh = {
        "lane-review-missing": False,
        "missing-active-board": True,
        "stale-board-token": True,
        "queue-sha-mismatch": True,
        "duplicate-job-id": False,
    }[reason]

    return {
        "detail": detail,
        "conflict_reason": reason,
        "remediation_message": remediation_message,
        "refresh_targets": refresh_targets,
        "retry_permitted_after_refresh": retry_permitted_after_refresh,
        **extra,
    }


def completion_write_conflict_detail(
    reason: str, detail: str, **extra: Any
) -> dict[str, Any]:
    """Build a structured conflict detail dict for completion write failures."""
    remediation_message = {
        "lane-verification-missing": (
            "Attach canonical verification_evidence to the lane, save the shared board, "
            "and retry completion write-back only after the reviewed verification gate "
            "is visible."
        ),
        "missing-active-board": (
            "Restore or resave the shared active board first. Completion write-back "
            "stays blocked until shared board provenance exists."
        ),
        "queue-sha-mismatch": (
            "Refresh queue status, confirm the current queue hash and the reviewed "
            "completion target, then retry only if the same job still applies."
        ),
        "queue-job-missing": (
            "The reviewed queue job is no longer present in the current queue snapshot. "
            "Refresh queue status and verify the job id before retrying."
        ),
        "queue-job-not-completed": (
            "Wait until the reviewed queue job reaches completed status before writing "
            "closure evidence back into the board."
        ),
        "closeout-receipt-required": (
            "Refresh the reviewed closeout receipt and retry only after the normalized "
            "receipt is visible in the control plane. Runtime-backed lanes should not be "
            "closed from freeform evidence alone."
        ),
        "closeout-receipt-mismatch": (
            "Refresh the reviewed closeout receipt, compare the latest normalized runtime "
            "evidence, and retry only if the receipt still matches the queue job being "
            "closed."
        ),
        "lane-job-mismatch": (
            "Refresh the shared board state and use the deterministic lane job id for the "
            "selected lane and board token. Do not apply completion evidence to a "
            "mismatched job."
        ),
        "stale-board-token": (
            "Refresh the shared board state, confirm the lane is still the intended "
            "completion target, then retry with the current board token."
        ),
        "lane-status-conflict": (
            "Only active lanes can move to completed in this slice. Review the current "
            "lane status and avoid forcing completion onto a non-active lane."
        ),
        "completion-overwrite-conflict": (
            "This lane already has different closure evidence. Review the current board "
            "record instead of overwriting closure data implicitly."
        ),
    }[reason]
    refresh_targets = {
        "lane-verification-missing": ["active-board"],
        "missing-active-board": ["active-board"],
        "queue-sha-mismatch": ["overnight-queue"],
        "queue-job-missing": ["overnight-queue"],
        "queue-job-not-completed": ["overnight-queue", "closeout-receipt"],
        "closeout-receipt-required": ["closeout-receipt", "overnight-queue"],
        "closeout-receipt-mismatch": ["closeout-receipt", "overnight-queue"],
        "lane-job-mismatch": ["active-board", "overnight-queue"],
        "stale-board-token": ["active-board"],
        "lane-status-conflict": ["active-board"],
        "completion-overwrite-conflict": ["active-board"],
    }[reason]
    retry_permitted_after_refresh = {
        "lane-verification-missing": False,
        "missing-active-board": True,
        "queue-sha-mismatch": True,
        "queue-job-missing": False,
        "queue-job-not-completed": True,
        "closeout-receipt-required": True,
        "closeout-receipt-mismatch": True,
        "lane-job-mismatch": True,
        "stale-board-token": True,
        "lane-status-conflict": False,
        "completion-overwrite-conflict": False,
    }[reason]

    return {
        "detail": detail,
        "conflict_reason": reason,
        "remediation_message": remediation_message,
        "refresh_targets": refresh_targets,
        "retry_permitted_after_refresh": retry_permitted_after_refresh,
        **extra,
    }


# ---------------------------------------------------------------------------
# Schema readiness helpers
# ---------------------------------------------------------------------------

async def get_missing_required_tables(
    db: AsyncSession,
    required_tables: tuple[str, ...],
) -> list[str]:
    """Return a list of required table names that are missing from the database."""
    from sqlalchemy import inspect

    connection = await db.connection()

    def inspect_missing_tables(sync_connection: Any) -> list[str]:
        inspector = inspect(sync_connection)
        return [
            table_name
            for table_name in required_tables
            if not inspector.has_table(table_name)
        ]

    return await connection.run_sync(inspect_missing_tables)

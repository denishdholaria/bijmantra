"""
Learning-ledger helpers for the developer control-plane API.

Extracted from developer_control_plane.py — DB-backed helpers for recording,
querying, and seeding learning entries from approval receipts and mission state.

These functions depend on helpers defined in developer_control_plane.py
(_require_ascii_text, _optional_ascii_text, etc.) and are imported via
deferred imports inside function bodies to avoid circular imports.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.developer_control_plane import (
    DeveloperControlPlaneApprovalReceipt,
    DeveloperControlPlaneLearningEntry,
)
from app.modules.ai.services.orchestrator_state import OrchestratorMissionStateService
from app.modules.ai.services.orchestrator_state_postgres import PostgresMissionStateRepository
from app.schemas.developer_control_plane import DEVELOPER_MASTER_BOARD_ID


def _learning_entry_response(record: DeveloperControlPlaneLearningEntry) -> Any:
    """Convert a DB learning entry record to the API response schema."""
    from app.control_plane.contracts.api_schema import DeveloperControlPlaneLearningEntryResponse
    return DeveloperControlPlaneLearningEntryResponse(
        learning_entry_id=record.id,
        organization_id=record.organization_id,
        entry_type=record.entry_type,
        source_classification=record.source_classification,
        title=record.title,
        summary=record.summary,
        confidence_score=record.confidence_score,
        recorded_by_user_id=record.recorded_by_user_id,
        recorded_by_email=record.recorded_by_email,
        board_id=record.board_id,
        source_lane_id=record.source_lane_id,
        queue_job_id=record.queue_job_id,
        linked_mission_id=record.linked_mission_id,
        approval_receipt_id=record.approval_receipt_id,
        source_reference=record.source_reference,
        evidence_refs=record.evidence_refs,
        summary_metadata=record.summary_metadata,
        recorded_at=record.created_at,
    )


async def _get_learning_entries(
    db: AsyncSession,
    organization_id: int,
    *,
    entry_type: str | None = None,
    source_classification: str | None = None,
    source_lane_id: str | None = None,
    queue_job_id: str | None = None,
    linked_mission_id: str | None = None,
    limit: int = 25,
) -> list[DeveloperControlPlaneLearningEntry]:
    conditions = [DeveloperControlPlaneLearningEntry.organization_id == organization_id]
    if entry_type is not None:
        conditions.append(DeveloperControlPlaneLearningEntry.entry_type == entry_type)
    if source_classification is not None:
        conditions.append(
            DeveloperControlPlaneLearningEntry.source_classification == source_classification
        )
    if source_lane_id is not None:
        conditions.append(DeveloperControlPlaneLearningEntry.source_lane_id == source_lane_id)
    if queue_job_id is not None:
        conditions.append(DeveloperControlPlaneLearningEntry.queue_job_id == queue_job_id)
    if linked_mission_id is not None:
        conditions.append(
            DeveloperControlPlaneLearningEntry.linked_mission_id == linked_mission_id
        )

    result = await db.execute(
        select(DeveloperControlPlaneLearningEntry)
        .where(*conditions)
        .order_by(
            DeveloperControlPlaneLearningEntry.created_at.desc(),
            DeveloperControlPlaneLearningEntry.id.desc(),
        )
        .limit(limit)
    )
    return list(result.scalars().all())


async def _get_existing_learning_entry(
    db: AsyncSession,
    organization_id: int,
    *,
    entry_type: str,
    source_classification: str,
    source_reference: str | None,
    board_id: str | None,
    source_lane_id: str | None,
    queue_job_id: str | None,
    linked_mission_id: str | None,
    approval_receipt_id: int | None,
) -> DeveloperControlPlaneLearningEntry | None:
    conditions = [
        DeveloperControlPlaneLearningEntry.organization_id == organization_id,
        DeveloperControlPlaneLearningEntry.entry_type == entry_type,
        DeveloperControlPlaneLearningEntry.source_classification == source_classification,
    ]

    optional_string_fields = {
        DeveloperControlPlaneLearningEntry.source_reference: source_reference,
        DeveloperControlPlaneLearningEntry.board_id: board_id,
        DeveloperControlPlaneLearningEntry.source_lane_id: source_lane_id,
        DeveloperControlPlaneLearningEntry.queue_job_id: queue_job_id,
        DeveloperControlPlaneLearningEntry.linked_mission_id: linked_mission_id,
    }
    for field, value in optional_string_fields.items():
        if value is None:
            conditions.append(field.is_(None))
        else:
            conditions.append(field == value)

    if approval_receipt_id is None:
        conditions.append(DeveloperControlPlaneLearningEntry.approval_receipt_id.is_(None))
    else:
        conditions.append(
            DeveloperControlPlaneLearningEntry.approval_receipt_id == approval_receipt_id
        )

    result = await db.execute(
        select(DeveloperControlPlaneLearningEntry)
        .where(*conditions)
        .order_by(
            DeveloperControlPlaneLearningEntry.created_at.desc(),
            DeveloperControlPlaneLearningEntry.id.desc(),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _record_learning_entry(
    db: AsyncSession,
    organization_id: int,
    *,
    entry_type: str,
    source_classification: str,
    title: str,
    summary: str,
    confidence_score: float | None,
    recorded_by_user_id: int | None,
    recorded_by_email: str | None,
    board_id: str | None,
    source_lane_id: str | None,
    queue_job_id: str | None,
    linked_mission_id: str | None,
    approval_receipt_id: int | None,
    source_reference: str | None,
    evidence_refs: list[str],
    summary_metadata: dict[str, Any] | None,
) -> tuple[DeveloperControlPlaneLearningEntry, bool]:
    # Deferred import to avoid circular dependency with developer_control_plane.py
    from app.api.bijmantra.developer.developer_control_plane import (
        CONTROL_PLANE_LEARNING_ENTRY_TYPES,
        _deduplicate_strings,
        _optional_ascii_text,
        _require_ascii_text,
        _require_ascii_text_list,
    )

    validated_entry_type = _require_ascii_text(entry_type, "learning.entry_type")
    if validated_entry_type not in CONTROL_PLANE_LEARNING_ENTRY_TYPES:
        allowed_values = ", ".join(CONTROL_PLANE_LEARNING_ENTRY_TYPES)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"learning.entry_type must be one of: {allowed_values}",
        )

    if confidence_score is not None and not 0 <= confidence_score <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="learning.confidence_score must be between 0 and 1",
        )

    validated_source_classification = _require_ascii_text(
        source_classification, "learning.source_classification"
    )
    validated_title = _require_ascii_text(title, "learning.title")
    validated_summary = _require_ascii_text(summary, "learning.summary")
    validated_recorded_by_email = _optional_ascii_text(
        recorded_by_email, "learning.recorded_by_email"
    )
    validated_board_id = _optional_ascii_text(board_id, "learning.board_id")
    validated_source_lane_id = _optional_ascii_text(source_lane_id, "learning.source_lane_id")
    validated_queue_job_id = _optional_ascii_text(queue_job_id, "learning.queue_job_id")
    validated_linked_mission_id = _optional_ascii_text(
        linked_mission_id, "learning.linked_mission_id"
    )
    validated_source_reference = _optional_ascii_text(
        source_reference, "learning.source_reference"
    )
    validated_evidence_refs = _deduplicate_strings(
        _require_ascii_text_list(evidence_refs, "learning.evidence_refs", min_items=0)
    )

    existing_entry = await _get_existing_learning_entry(
        db,
        organization_id,
        entry_type=validated_entry_type,
        source_classification=validated_source_classification,
        source_reference=validated_source_reference,
        board_id=validated_board_id,
        source_lane_id=validated_source_lane_id,
        queue_job_id=validated_queue_job_id,
        linked_mission_id=validated_linked_mission_id,
        approval_receipt_id=approval_receipt_id,
    )
    if existing_entry is not None:
        return existing_entry, False

    entry = DeveloperControlPlaneLearningEntry(
        organization_id=organization_id,
        entry_type=validated_entry_type,
        source_classification=validated_source_classification,
        title=validated_title,
        summary=validated_summary,
        confidence_score=confidence_score,
        recorded_by_user_id=recorded_by_user_id,
        recorded_by_email=validated_recorded_by_email,
        board_id=validated_board_id,
        source_lane_id=validated_source_lane_id,
        queue_job_id=validated_queue_job_id,
        linked_mission_id=validated_linked_mission_id,
        approval_receipt_id=approval_receipt_id,
        source_reference=validated_source_reference,
        evidence_refs=validated_evidence_refs,
        summary_metadata=summary_metadata,
    )
    db.add(entry)
    await db.flush()
    return entry, True


def _mission_learning_evidence_refs(snapshot: Any, *, include_passed_runs: bool) -> list[str]:
    """Collect evidence ref strings from a mission snapshot."""
    from app.api.bijmantra.developer.developer_control_plane import _deduplicate_strings

    evidence_refs: list[str] = []
    for item in snapshot.verification_runs:
        if not include_passed_runs and item.result.value == "passed":
            continue
        if (
            isinstance(item.evidence_ref, str)
            and item.evidence_ref.strip()
            and item.evidence_ref.isascii()
        ):
            evidence_refs.append(item.evidence_ref)
    for item in snapshot.evidence_items:
        if (
            isinstance(item.source_path, str)
            and item.source_path.strip()
            and item.source_path.isascii()
        ):
            evidence_refs.append(item.source_path)
    if not evidence_refs:
        evidence_refs.append(f"developer-control-plane:mission:{snapshot.mission.id}")
    return _deduplicate_strings(evidence_refs)


async def _seed_learning_entries_from_approval_receipts(
    db: AsyncSession,
    organization_id: int,
) -> bool:
    from app.api.bijmantra.developer.developer_control_plane import (
        COMPLETION_WRITE_OPERATOR_INTENT,
        QUEUE_WRITE_OPERATOR_INTENT,
        _get_missing_approval_receipt_tables,
    )

    if await _get_missing_approval_receipt_tables(db):
        return False

    result = await db.execute(
        select(DeveloperControlPlaneApprovalReceipt)
        .where(DeveloperControlPlaneApprovalReceipt.organization_id == organization_id)
        .order_by(
            DeveloperControlPlaneApprovalReceipt.created_at.asc(),
            DeveloperControlPlaneApprovalReceipt.id.asc(),
        )
    )

    created_any = False
    for receipt in result.scalars().all():
        lane_id = receipt.source_lane_id or "unknown-lane"
        queue_job_id = receipt.queue_job_id or "unknown-job"
        if receipt.action_type == QUEUE_WRITE_OPERATOR_INTENT:
            _, created = await _record_learning_entry(
                db,
                organization_id,
                entry_type="pattern",
                source_classification="accepted-review",
                title=f"Accepted review enabled queue export for lane {lane_id}",
                summary=(
                    f"Explicit spec_review and risk_review evidence supported queue export for "
                    f"lane {lane_id} into queue job {queue_job_id} without weakening board-wins precedence."
                ),
                confidence_score=0.93,
                recorded_by_user_id=receipt.authority_actor_user_id,
                recorded_by_email=receipt.authority_actor_email,
                board_id=receipt.board_id,
                source_lane_id=receipt.source_lane_id,
                queue_job_id=receipt.queue_job_id,
                linked_mission_id=receipt.linked_mission_id,
                approval_receipt_id=receipt.id,
                source_reference=f"approval-receipt:{receipt.id}:accepted-review",
                evidence_refs=receipt.evidence_refs,
                summary_metadata={
                    "seed_source": "approval-receipt",
                    "approval_receipt_action": receipt.action_type,
                    "approval_receipt_outcome": receipt.outcome,
                    "queue_sha256": receipt.resulting_queue_sha256,
                },
            )
            created_any = created_any or created
            continue

        if receipt.action_type != COMPLETION_WRITE_OPERATOR_INTENT:
            continue

        receipt_metadata = (
            receipt.summary_metadata if isinstance(receipt.summary_metadata, dict) else {}
        )
        closeout_receipt_present = receipt_metadata.get("closeout_receipt_present") is True
        _, created = await _record_learning_entry(
            db,
            organization_id,
            entry_type="pattern",
            source_classification="reviewed-completion-writeback",
            title=f"Reviewed completion write-back closed lane {lane_id}",
            summary=(
                f"Explicit reviewed completion write-back persisted canonical closure for lane "
                f"{lane_id} from queue job {queue_job_id} without weakening board-wins precedence."
                + (
                    " Runtime closeout receipt evidence stayed attached to the accepted closure path."
                    if closeout_receipt_present
                    else " The canonical board remained the accepted closure authority."
                )
            ),
            confidence_score=0.94,
            recorded_by_user_id=receipt.authority_actor_user_id,
            recorded_by_email=receipt.authority_actor_email,
            board_id=receipt.board_id,
            source_lane_id=receipt.source_lane_id,
            queue_job_id=receipt.queue_job_id,
            linked_mission_id=receipt.linked_mission_id,
            approval_receipt_id=receipt.id,
            source_reference=f"approval-receipt:{receipt.id}:reviewed-completion-writeback",
            evidence_refs=receipt.evidence_refs,
            summary_metadata={
                "seed_source": "approval-receipt",
                "approval_receipt_action": receipt.action_type,
                "approval_receipt_outcome": receipt.outcome,
                "queue_sha256": receipt.resulting_queue_sha256,
                "closeout_receipt_present": closeout_receipt_present,
            },
        )
        created_any = created_any or created

    return created_any


async def _seed_learning_entries_from_mission_state(
    db: AsyncSession,
    organization_id: int,
) -> bool:
    from app.control_plane.application.mission_service import MissionService
    from app.api.bijmantra.developer.developer_control_plane import (
        _get_missing_mission_state_schema_requirements,
    )

    missing_tables, missing_columns = await _get_missing_mission_state_schema_requirements(db)
    if missing_tables or missing_columns:
        return False

    service = OrchestratorMissionStateService(
        PostgresMissionStateRepository(db, organization_id=organization_id)
    )
    missions = await service.repository.list_missions(owner="OmShriMaatreNamaha")

    created_any = False
    for mission in missions:
        snapshot = await service.get_mission_snapshot(mission.id)
        summary = MissionService.mission_summary_response(snapshot)
        mission_evidence_refs = _mission_learning_evidence_refs(
            snapshot, include_passed_runs=True
        )
        regression_evidence_refs = _mission_learning_evidence_refs(
            snapshot, include_passed_runs=False
        )

        if any(
            item.decision_class == "stable_closeout_receipt_observed"
            for item in snapshot.decision_notes
        ):
            _, created = await _record_learning_entry(
                db,
                organization_id,
                entry_type="pattern",
                source_classification="stable-closeout-receipt",
                title=f"Stable closeout receipt observed for mission {snapshot.mission.id}",
                summary=(
                    f"Stable closeout receipt evidence was observed for queue job "
                    f"{summary.queue_job_id or snapshot.mission.id} before canonical board closure, "
                    "so later review can reuse the same runtime provenance."
                ),
                confidence_score=0.88,
                recorded_by_user_id=None,
                recorded_by_email=None,
                board_id=DEVELOPER_MASTER_BOARD_ID,
                source_lane_id=summary.source_lane_id,
                queue_job_id=summary.queue_job_id,
                linked_mission_id=snapshot.mission.id,
                approval_receipt_id=None,
                source_reference=f"mission:{snapshot.mission.id}:stable-closeout-receipt",
                evidence_refs=mission_evidence_refs,
                summary_metadata={
                    "seed_source": "mission-state",
                    "producer_key": summary.producer_key,
                    "mission_status": summary.status,
                    "decision_classes": [
                        item.decision_class for item in snapshot.decision_notes
                    ],
                },
            )
            created_any = created_any or created

        if summary.verification.failed or summary.verification.warned:
            _, created = await _record_learning_entry(
                db,
                organization_id,
                entry_type="verification-learning",
                source_classification="benchmark-regression",
                title=f"Mission verification regression for {snapshot.mission.id}",
                summary=(
                    f"Mission {snapshot.mission.id} currently has {summary.verification.failed} failed "
                    f"and {summary.verification.warned} warning verification runs; reuse this regression "
                    "evidence before promoting similar control-plane changes."
                ),
                confidence_score=0.86,
                recorded_by_user_id=None,
                recorded_by_email=None,
                board_id=DEVELOPER_MASTER_BOARD_ID,
                source_lane_id=summary.source_lane_id,
                queue_job_id=summary.queue_job_id,
                linked_mission_id=snapshot.mission.id,
                approval_receipt_id=None,
                source_reference=(
                    f"mission:{snapshot.mission.id}:verification-regression:"
                    f"{summary.verification.failed}:{summary.verification.warned}"
                ),
                evidence_refs=regression_evidence_refs,
                summary_metadata={
                    "seed_source": "mission-state",
                    "producer_key": summary.producer_key,
                    "mission_status": summary.status,
                    "verification": summary.verification.model_dump(),
                },
            )
            created_any = created_any or created

    return created_any


async def _seed_learning_entries(
    db: AsyncSession,
    organization_id: int,
) -> bool:
    from app.api.bijmantra.developer.developer_control_plane import _get_missing_learning_tables

    if await _get_missing_learning_tables(db):
        return False

    created_from_receipts = await _seed_learning_entries_from_approval_receipts(
        db, organization_id
    )
    created_from_missions = await _seed_learning_entries_from_mission_state(
        db, organization_id
    )
    return created_from_receipts or created_from_missions


async def _seed_approval_receipt_learnings_if_ready(
    db: AsyncSession,
    organization_id: int,
) -> bool:
    from app.api.bijmantra.developer.developer_control_plane import _get_missing_learning_tables

    if await _get_missing_learning_tables(db):
        return False
    return await _seed_learning_entries_from_approval_receipts(db, organization_id)


async def _seed_mission_state_learnings_if_ready(
    db: AsyncSession,
    organization_id: int,
) -> bool:
    from app.api.bijmantra.developer.developer_control_plane import _get_missing_learning_tables

    if await _get_missing_learning_tables(db):
        return False
    return await _seed_learning_entries_from_mission_state(db, organization_id)

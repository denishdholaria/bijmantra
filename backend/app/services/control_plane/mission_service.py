"""Mission service for developer control plane.

Handles mission lifecycle, evidence recording, and closeout receipt bootstrapping.

NOTE: The regex pattern and parse_completion_source_request / mission_linkage
functions are defined in the canonical domain layer:
  app.control_plane.domain.mission

They are re-exported here for backward compatibility with callers that import
from this module. Do not duplicate the implementations.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.services.orchestrator_state import (
    OrchestratorMissionStateService,
    SubtaskStatus,
    VerificationResult,
)
from app.modules.ai.services.orchestrator_state_postgres import PostgresMissionStateRepository
from app.modules.ai.services.claw_runtime_contract import normalize_runtime_reference
from app.schemas.developer_control_plane import DEVELOPER_MASTER_BOARD_ID

# Re-export canonical implementations — do not duplicate here
from app.control_plane.domain.mission import (  # noqa: F401
    MISSION_LINKAGE_SOURCE_REQUEST_PATTERN,
    mission_linkage,
    parse_completion_source_request,
)


# ---------------------------------------------------------------------------
# Mission objective / source request builders
# ---------------------------------------------------------------------------

def completion_mission_objective(lane_id: str, lane_title: str | None) -> str:
    """Build the mission objective string for a completion write-back."""
    if lane_title:
        return f"Reviewed closeout persistence for lane {lane_title}"
    return f"Reviewed closeout persistence for lane {lane_id}"


def bootstrap_mission_objective(lane_id: str, lane_title: str | None) -> str:
    """Build the mission objective string for a closeout receipt bootstrap."""
    if lane_title:
        return f"Await canonical board closure for lane {lane_title}"
    return f"Await canonical board closure for lane {lane_id}"


def mission_link_source_request(
    event: str,
    lane_id: str,
    queue_job_id: str,
    closeout_receipt: dict[str, Any],
) -> str:
    """Build a structured source_request string for mission linkage."""
    source_request = (
        f"Developer control-plane {event} for lane {lane_id} "
        f"from queue job {queue_job_id}."
    )
    source_board_concurrency_token = closeout_receipt.get("source_board_concurrency_token")
    if isinstance(source_board_concurrency_token, str) and source_board_concurrency_token:
        source_request += (
            f" Context: source_board_concurrency_token={source_board_concurrency_token}."
        )
    return source_request


def completion_mission_source_request(
    lane_id: str,
    queue_job_id: str,
    closeout_receipt: dict[str, Any],
) -> str:
    """Build the source_request for an explicit completion write-back mission."""
    return mission_link_source_request(
        "explicit completion write-back",
        lane_id,
        queue_job_id,
        closeout_receipt,
    )


def bootstrap_mission_source_request(
    lane_id: str,
    queue_job_id: str,
    closeout_receipt: dict[str, Any],
) -> str:
    """Build the source_request for a stable closeout receipt bootstrap mission."""
    return mission_link_source_request(
        "stable closeout receipt observed",
        lane_id,
        queue_job_id,
        closeout_receipt,
    )


# ---------------------------------------------------------------------------
# Closeout receipt verification
# ---------------------------------------------------------------------------

def closeout_receipt_verification_result(
    closeout_receipt: dict[str, Any],
) -> VerificationResult:
    """Derive a VerificationResult from a closeout receipt's status field."""
    status_value = closeout_receipt.get("closeout_status")
    if status_value == "failed":
        return VerificationResult.FAILED
    if status_value in {"passed", "skipped"}:
        return VerificationResult.PASSED
    return VerificationResult.WARN


# ---------------------------------------------------------------------------
# Mission state queries
# ---------------------------------------------------------------------------

async def load_runtime_mission_snapshot(
    db: AsyncSession,
    organization_id: int,
    mission_id: str,
) -> Any:
    """Load a mission snapshot for OmShriMaatreNamaha-owned missions.

    Returns:
        Mission snapshot or None if not found or not owned by OmShriMaatreNamaha.
    """
    service = OrchestratorMissionStateService(
        PostgresMissionStateRepository(db, organization_id=organization_id)
    )
    mission = await service.repository.get_mission(mission_id)
    if mission is None or mission.owner != "OmShriMaatreNamaha":
        return None
    return await service.get_mission_snapshot(mission_id)


async def mission_state_query(
    db: AsyncSession,
    organization_id: int,
    *,
    limit: int,
    queue_job_id: str | None = None,
    source_lane_id: str | None = None,
) -> tuple[list[Any], list[Any]]:
    """Query missions and their snapshots for the mission state response.

    Returns:
        Tuple of (missions_list, snapshots_list) for the given filters.
    """
    service = OrchestratorMissionStateService(
        PostgresMissionStateRepository(db, organization_id=organization_id)
    )
    relevant_missions = await service.repository.list_missions(
        owner="OmShriMaatreNamaha",
        queue_job_id=queue_job_id,
        source_lane_id=source_lane_id,
    )

    if (queue_job_id is not None or source_lane_id is not None) and not relevant_missions:
        fallback_missions = await service.repository.list_missions(owner="OmShriMaatreNamaha")
        filtered_missions = []
        for mission in fallback_missions:
            linkage = mission_linkage(mission)
            if linkage is None:
                continue
            if queue_job_id is not None and linkage["queue_job_id"] != queue_job_id:
                continue
            if source_lane_id is not None and linkage["source_lane_id"] != source_lane_id:
                continue
            filtered_missions.append(mission)
        relevant_missions = filtered_missions

    relevant_missions.sort(key=lambda item: (item.updated_at, item.id), reverse=True)

    snapshots = []
    for mission in relevant_missions[:limit]:
        snapshot = await service.get_mission_snapshot(mission.id)
        snapshots.append(snapshot)

    return relevant_missions[:limit], snapshots


# ---------------------------------------------------------------------------
# Mission bootstrap from closeout receipt
# ---------------------------------------------------------------------------

async def bootstrap_closeout_receipt_mission_state(
    db: AsyncSession,
    organization_id: int,
    *,
    queue_job_id: str,
    closeout_receipt: dict[str, Any] | None,
    lookup_lane_title_fn: Any,
) -> dict[str, Any]:
    """Bootstrap mission state from a closeout receipt.

    Args:
        db: Database session
        organization_id: Organization ID
        queue_job_id: Queue job identifier
        closeout_receipt: Closeout receipt payload or None
        lookup_lane_title_fn: Async callable(db, org_id, lane_id) -> str | None

    Returns:
        Dict with action and mission_id keys.
    """
    if closeout_receipt is None:
        return {"action": "missing-receipt", "mission_id": None}

    mission_id = closeout_receipt.get("mission_id")
    if not isinstance(mission_id, str) or not mission_id:
        return {"action": "missing-mission-id", "mission_id": None}

    service = OrchestratorMissionStateService(
        PostgresMissionStateRepository(db, organization_id=organization_id)
    )
    existing = await service.repository.get_mission(mission_id)
    if existing is not None:
        return {"action": "existing", "mission_id": mission_id}

    lane_id = (
        closeout_receipt.get("source_lane_id")
        if isinstance(closeout_receipt.get("source_lane_id"), str) and closeout_receipt.get("source_lane_id")
        else queue_job_id
    )
    lane_title = await lookup_lane_title_fn(db, organization_id, lane_id)
    mission = await service.register_mission(
        mission_id=mission_id,
        objective=bootstrap_mission_objective(lane_id, lane_title),
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request=bootstrap_mission_source_request(lane_id, queue_job_id, closeout_receipt),
        producer_key=(
            closeout_receipt.get("producer_key")
            if isinstance(closeout_receipt.get("producer_key"), str)
            else "developer-control-plane"
        ),
        queue_job_id=queue_job_id,
        source_lane_id=(
            closeout_receipt.get("source_lane_id")
            if isinstance(closeout_receipt.get("source_lane_id"), str)
            else lane_id
        ),
        source_board_concurrency_token=(
            closeout_receipt.get("source_board_concurrency_token")
            if isinstance(closeout_receipt.get("source_board_concurrency_token"), str)
            else None
        ),
    )
    closeout_receipt_path = f"runtime-artifacts/mission-evidence/{queue_job_id}/closeout.json"
    closeout_evidence = await service.record_evidence(
        mission_id=mission.id,
        kind="closeout_receipt",
        source_path=closeout_receipt_path,
        evidence_class="runtime-receipt",
        summary=f"Stable closeout receipt is available for queue job {queue_job_id}.",
    )

    verification_evidence_ref = closeout_receipt.get("verification_evidence_ref")
    if isinstance(verification_evidence_ref, str) and verification_evidence_ref:
        await service.record_evidence(
            mission_id=mission.id,
            kind="verification_evidence",
            source_path=verification_evidence_ref,
            evidence_class="runtime-verification",
            summary=f"Verification evidence is available for queue job {queue_job_id}.",
        )

    await service.record_verification_run(
        subject_id=mission.id,
        verification_type="runtime_closeout_receipt_observed",
        result=closeout_receipt_verification_result(closeout_receipt),
        evidence_ref=closeout_evidence.id,
    )
    await service.record_decision_note(
        mission_id=mission.id,
        decision_class="stable_closeout_receipt_observed",
        rationale=(
            f"Stable runtime closeout receipt was captured for lane {lane_id} "
            f"from queue job {queue_job_id} before canonical board closure."
        ),
        authority_source="OmShriMaatreNamaha",
    )
    return {"action": "created", "mission_id": mission.id}


# ---------------------------------------------------------------------------
# Mission state from completion write-back
# ---------------------------------------------------------------------------

async def record_closeout_backed_mission_state(
    db: AsyncSession,
    organization_id: int,
    *,
    lane_id: str,
    lane_title: str | None,
    queue_job_id: str,
    closure_summary: str,
    closeout_receipt: dict[str, Any] | None,
) -> None:
    """Record or update mission state when a completion write-back is performed.

    This is a no-op if closeout_receipt is None or has no mission_id.
    """
    if closeout_receipt is None:
        return

    mission_id = closeout_receipt.get("mission_id")
    if not isinstance(mission_id, str) or not mission_id:
        return

    service = OrchestratorMissionStateService(
        PostgresMissionStateRepository(db, organization_id=organization_id)
    )
    existing = await service.repository.get_mission(mission_id)
    if existing is None:
        mission = await service.register_mission(
            mission_id=mission_id,
            objective=completion_mission_objective(lane_id, lane_title),
            owner="OmShriMaatreNamaha",
            priority="p1",
            source_request=completion_mission_source_request(
                lane_id,
                queue_job_id,
                closeout_receipt,
            ),
            producer_key=(
                closeout_receipt.get("producer_key")
                if isinstance(closeout_receipt.get("producer_key"), str)
                else "developer-control-plane"
            ),
            queue_job_id=queue_job_id,
            source_lane_id=(
                closeout_receipt.get("source_lane_id")
                if isinstance(closeout_receipt.get("source_lane_id"), str)
                else lane_id
            ),
            source_board_concurrency_token=(
                closeout_receipt.get("source_board_concurrency_token")
                if isinstance(closeout_receipt.get("source_board_concurrency_token"), str)
                else None
            ),
        )
    else:
        mission = await service.repository.save_mission(
            replace(
                existing,
                objective=completion_mission_objective(lane_id, lane_title),
                producer_key=(
                    closeout_receipt.get("producer_key")
                    if isinstance(closeout_receipt.get("producer_key"), str)
                    else existing.producer_key
                ),
                queue_job_id=queue_job_id,
                source_lane_id=(
                    closeout_receipt.get("source_lane_id")
                    if isinstance(closeout_receipt.get("source_lane_id"), str)
                    else existing.source_lane_id or lane_id
                ),
                source_board_concurrency_token=(
                    closeout_receipt.get("source_board_concurrency_token")
                    if isinstance(closeout_receipt.get("source_board_concurrency_token"), str)
                    else existing.source_board_concurrency_token
                ),
                source_request=completion_mission_source_request(
                    lane_id,
                    queue_job_id,
                    closeout_receipt,
                ),
                updated_at=datetime.now(UTC),
            )
        )

    snapshot = await service.get_mission_snapshot(mission.id)
    subtask = await service.add_subtask(
        mission_id=mission.id,
        title="Persist reviewed closeout evidence",
        owner_role="OmVishnaveNamah",
    )
    await service.update_subtask_status(subtask.id, SubtaskStatus.COMPLETED)
    assignment = await service.assign_subtask(
        subtask_id=subtask.id,
        assigned_role="OmVishnaveNamah",
        handoff_reason="Verify reviewed runtime evidence before durable mission closeout.",
    )
    await service.complete_assignment(assignment.id)

    closeout_receipt_path = f"runtime-artifacts/mission-evidence/{queue_job_id}/closeout.json"
    existing_evidence_keys = {
        (item.kind, item.source_path)
        for item in snapshot.evidence_items
    }
    if ("closeout_receipt", closeout_receipt_path) in existing_evidence_keys:
        closeout_evidence = next(
            item
            for item in snapshot.evidence_items
            if item.kind == "closeout_receipt" and item.source_path == closeout_receipt_path
        )
    else:
        closeout_evidence = await service.record_evidence(
            subtask_id=subtask.id,
            kind="closeout_receipt",
            source_path=closeout_receipt_path,
            evidence_class="runtime-receipt",
            summary=f"Stable closeout receipt was reviewed for queue job {queue_job_id}.",
        )

    verification_evidence_ref = closeout_receipt.get("verification_evidence_ref")
    if isinstance(verification_evidence_ref, str) and verification_evidence_ref:
        if ("verification_evidence", verification_evidence_ref) not in existing_evidence_keys:
            await service.record_evidence(
                subtask_id=subtask.id,
                kind="verification_evidence",
                source_path=verification_evidence_ref,
                evidence_class="runtime-verification",
                summary=f"Verification evidence was preserved for queue job {queue_job_id}.",
            )

    await service.record_verification_run(
        subject_id=subtask.id,
        verification_type="closeout_receipt_review",
        result=VerificationResult.PASSED,
        evidence_ref=closeout_evidence.id,
    )
    await service.record_decision_note(
        mission_id=mission.id,
        decision_class="reviewed_completion_writeback",
        rationale=(
            f"Canonical board closure accepted reviewed runtime evidence for lane {lane_id} "
            f"from queue job {queue_job_id}."
        ),
        authority_source="OmShriMaatreNamaha",
    )
    await service.complete_mission(
        mission.id,
        (
            f"Canonical board closure persisted reviewed runtime provenance for lane {lane_id}. "
            f"Closure summary: {closure_summary}"
        ),
    )

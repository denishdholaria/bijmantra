"""Mission application service — state queries and response building.

This module is the application-layer home for mission read operations
that require infrastructure (SQLAlchemy ``AsyncSession``).  It bridges the
pure domain layer (``control_plane.domain.mission``) and the persistence
models (orchestrator mission state).

Extracted from ``backend/app/api/v2/developer_control_plane.py``.

Requirements: 9.3, 9.5, 9.6
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneMissionAssignmentResponse,
    DeveloperControlPlaneMissionBlockerResponse,
    DeveloperControlPlaneMissionDecisionNoteResponse,
    DeveloperControlPlaneMissionDetailResponse,
    DeveloperControlPlaneMissionEvidenceResponse,
    DeveloperControlPlaneMissionStateResponse,
    DeveloperControlPlaneMissionSubtaskResponse,
    DeveloperControlPlaneMissionSummaryResponse,
    DeveloperControlPlaneMissionVerificationRunResponse,
    DeveloperControlPlaneMissionVerificationSummaryResponse,
)
from app.control_plane.domain.mission import mission_linkage
from app.modules.ai.services.claw_runtime_contract import normalize_runtime_reference
from app.modules.ai.services.claw_runtime_surface import (
    resolve_runtime_mission_evidence_dir,
)
from app.modules.ai.services.orchestrator_state import OrchestratorMissionStateService
from app.modules.ai.services.orchestrator_state_postgres import (
    PostgresMissionStateRepository,
)


# ---------------------------------------------------------------------------
# Path constants — resolved once at import time, matching the original module.
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[4]
_MISSION_EVIDENCE_DIR = resolve_runtime_mission_evidence_dir(_REPO_ROOT)


class MissionService:
    """Application service for mission state queries.

    Accepts an ``AsyncSession`` as a constructor dependency so that
    callers control transaction boundaries.

    All public methods mirror the exact behavior of the private helpers
    previously inlined in ``developer_control_plane.py``.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_service(self, organization_id: int) -> OrchestratorMissionStateService:
        """Create an ``OrchestratorMissionStateService`` for *organization_id*."""
        return OrchestratorMissionStateService(
            PostgresMissionStateRepository(self._db, organization_id=organization_id)
        )

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def load_runtime_mission_snapshot(
        self,
        organization_id: int,
        mission_id: str,
    ) -> Any | None:
        """Load a runtime mission snapshot for *mission_id*.

        Returns ``None`` when the mission does not exist or is not owned
        by ``OmShriMaatreNamaha``.
        """
        service = self._build_service(organization_id)
        mission = await service.repository.get_mission(mission_id)
        if mission is None or mission.owner != "OmShriMaatreNamaha":
            return None
        return await service.get_mission_snapshot(mission_id)

    async def mission_state_response(
        self,
        organization_id: int,
        *,
        limit: int,
        queue_job_id: str | None = None,
        source_lane_id: str | None = None,
    ) -> DeveloperControlPlaneMissionStateResponse:
        """Build a paginated mission state response.

        Queries missions owned by ``OmShriMaatreNamaha``.  When
        *queue_job_id* or *source_lane_id* filters are provided but
        yield no direct matches, a fallback search parses the
        ``source_request`` string of all missions to find linkage
        matches.
        """
        service = self._build_service(organization_id)
        relevant_missions = await service.repository.list_missions(
            owner="OmShriMaatreNamaha",
            queue_job_id=queue_job_id,
            source_lane_id=source_lane_id,
        )

        if (queue_job_id is not None or source_lane_id is not None) and not relevant_missions:
            fallback_missions = await service.repository.list_missions(
                owner="OmShriMaatreNamaha",
            )
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

        summaries: list[DeveloperControlPlaneMissionSummaryResponse] = []
        for mission in relevant_missions[:limit]:
            snapshot = await service.get_mission_snapshot(mission.id)
            summaries.append(self.mission_summary_response(snapshot))

        return DeveloperControlPlaneMissionStateResponse(
            count=len(summaries),
            missions=summaries,
        )

    # ------------------------------------------------------------------
    # Response builders
    # ------------------------------------------------------------------

    @staticmethod
    def mission_summary_response(
        snapshot: Any,
    ) -> DeveloperControlPlaneMissionSummaryResponse:
        """Build an API summary response from a mission snapshot.

        This is a pure mapping with no side effects.
        """
        linkage = mission_linkage(snapshot.mission)
        passed = sum(
            1 for item in snapshot.verification_runs if item.result.value == "passed"
        )
        warned = sum(
            1 for item in snapshot.verification_runs if item.result.value == "warn"
        )
        failed = sum(
            1 for item in snapshot.verification_runs if item.result.value == "failed"
        )
        last_verified_at = max(
            (item.executed_at for item in snapshot.verification_runs),
            default=None,
        )
        subtask_completed = sum(
            1 for item in snapshot.subtasks if item.status.value == "completed"
        )
        return DeveloperControlPlaneMissionSummaryResponse(
            mission_id=snapshot.mission.id,
            objective=snapshot.mission.objective,
            status=snapshot.mission.status.value,
            owner=snapshot.mission.owner,
            priority=snapshot.mission.priority,
            producer_key=snapshot.mission.producer_key,
            queue_job_id=linkage["queue_job_id"] if linkage is not None else None,
            source_lane_id=linkage["source_lane_id"] if linkage is not None else None,
            source_board_concurrency_token=(
                linkage["source_board_concurrency_token"] if linkage is not None else None
            ),
            created_at=snapshot.mission.created_at.isoformat(),
            updated_at=snapshot.mission.updated_at.isoformat(),
            subtask_total=len(snapshot.subtasks),
            subtask_completed=subtask_completed,
            assignment_total=len(snapshot.assignments),
            evidence_count=len(snapshot.evidence_items),
            blocker_count=len(snapshot.blockers),
            escalation_needed=any(item.escalation_needed for item in snapshot.blockers),
            verification=DeveloperControlPlaneMissionVerificationSummaryResponse(
                passed=passed,
                warned=warned,
                failed=failed,
                last_verified_at=(
                    last_verified_at.isoformat() if last_verified_at else None
                ),
            ),
            final_summary=snapshot.mission.final_summary,
        )

    @staticmethod
    def mission_detail_response(
        snapshot: Any,
    ) -> DeveloperControlPlaneMissionDetailResponse:
        """Build an API detail response from a mission snapshot.

        Includes all subtasks, assignments, evidence items, verification
        runs, decision notes, and blockers.
        """
        summary = MissionService.mission_summary_response(snapshot)
        runtime_root = _MISSION_EVIDENCE_DIR.parent
        return DeveloperControlPlaneMissionDetailResponse(
            **summary.model_dump(),
            subtasks=[
                DeveloperControlPlaneMissionSubtaskResponse(
                    id=item.id,
                    title=item.title,
                    status=item.status.value,
                    owner_role=item.owner_role,
                    depends_on=list(item.depends_on),
                    updated_at=item.updated_at.isoformat(),
                )
                for item in snapshot.subtasks
            ],
            assignments=[
                DeveloperControlPlaneMissionAssignmentResponse(
                    id=item.id,
                    subtask_id=item.subtask_id,
                    assigned_role=item.assigned_role,
                    handoff_reason=item.handoff_reason,
                    started_at=item.started_at.isoformat(),
                    completed_at=(
                        item.completed_at.isoformat() if item.completed_at else None
                    ),
                )
                for item in snapshot.assignments
            ],
            evidence_items=[
                DeveloperControlPlaneMissionEvidenceResponse(
                    id=item.id,
                    mission_id=item.mission_id,
                    subtask_id=item.subtask_id,
                    kind=item.kind,
                    evidence_class=item.evidence_class,
                    summary=item.summary,
                    source_path=normalize_runtime_reference(
                        _REPO_ROOT, runtime_root, item.source_path
                    )
                    or item.source_path,
                    recorded_at=item.recorded_at.isoformat(),
                )
                for item in snapshot.evidence_items
            ],
            verification_runs=[
                DeveloperControlPlaneMissionVerificationRunResponse(
                    id=item.id,
                    subject_id=item.subject_id,
                    verification_type=item.verification_type,
                    result=item.result.value,
                    evidence_ref=item.evidence_ref,
                    executed_at=item.executed_at.isoformat(),
                )
                for item in snapshot.verification_runs
            ],
            decision_notes=[
                DeveloperControlPlaneMissionDecisionNoteResponse(
                    id=item.id,
                    decision_class=item.decision_class,
                    authority_source=item.authority_source,
                    recorded_at=item.recorded_at.isoformat(),
                )
                for item in snapshot.decision_notes
            ],
            blockers=[
                DeveloperControlPlaneMissionBlockerResponse(
                    id=item.id,
                    mission_id=item.mission_id,
                    subtask_id=item.subtask_id,
                    blocker_type=item.blocker_type,
                    impact=item.impact,
                    escalation_needed=item.escalation_needed,
                    recorded_at=item.recorded_at.isoformat(),
                )
                for item in snapshot.blockers
            ],
        )

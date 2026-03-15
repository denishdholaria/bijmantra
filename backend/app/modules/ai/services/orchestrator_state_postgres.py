"""PostgreSQL-backed repository for durable orchestrator mission state."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orchestrator_state import (
    OrchestratorAssignment,
    OrchestratorBlocker,
    OrchestratorDecisionNote,
    OrchestratorEvidenceItem,
    OrchestratorMission,
    OrchestratorSubtask,
    OrchestratorVerificationRun,
)
from app.modules.ai.services.orchestrator_state import (
    AssignmentRecord,
    BlockerRecord,
    DecisionNoteRecord,
    EvidenceItemRecord,
    MissionRecord,
    MissionStateRepository,
    MissionStatus,
    SubtaskRecord,
    SubtaskStatus,
    VerificationResult,
    VerificationRunRecord,
)


class PostgresMissionStateRepository(MissionStateRepository):
    """SQLAlchemy-backed durable mission-state repository."""

    def __init__(self, db: AsyncSession, organization_id: int) -> None:
        self.db = db
        self.organization_id = organization_id

    async def save_mission(self, mission: MissionRecord) -> MissionRecord:
        instance = await self._get_mission_model(mission.id)
        if instance is None:
            instance = OrchestratorMission(
                organization_id=self.organization_id,
                mission_id=mission.id,
                objective=mission.objective,
                status=mission.status.value,
                owner=mission.owner,
                priority=mission.priority,
                producer_key=mission.producer_key,
                source_request=mission.source_request,
                final_summary=mission.final_summary,
                created_at=mission.created_at,
                updated_at=mission.updated_at,
            )
            self.db.add(instance)
        else:
            instance.objective = mission.objective
            instance.status = mission.status.value
            instance.owner = mission.owner
            instance.priority = mission.priority
            instance.producer_key = mission.producer_key
            instance.source_request = mission.source_request
            instance.final_summary = mission.final_summary
            instance.created_at = mission.created_at
            instance.updated_at = mission.updated_at
        await self.db.flush()
        return self._mission_record(instance)

    async def get_mission(self, mission_id: str) -> MissionRecord | None:
        instance = await self._get_mission_model(mission_id)
        return self._mission_record(instance) if instance is not None else None

    async def list_missions(self) -> list[MissionRecord]:
        stmt = (
            select(OrchestratorMission)
            .where(OrchestratorMission.organization_id == self.organization_id)
            .order_by(OrchestratorMission.created_at.asc(), OrchestratorMission.id.asc())
        )
        result = await self.db.execute(stmt)
        return [self._mission_record(item) for item in result.scalars().all()]

    async def save_subtask(self, subtask: SubtaskRecord) -> SubtaskRecord:
        mission = await self._require_mission_model(subtask.mission_id)
        instance = await self._get_subtask_model(subtask.id)
        if instance is None:
            instance = OrchestratorSubtask(
                organization_id=self.organization_id,
                mission_pk=mission.id,
                subtask_id=subtask.id,
                title=subtask.title,
                status=subtask.status.value,
                owner_role=subtask.owner_role,
                depends_on=list(subtask.depends_on),
                created_at=subtask.created_at,
                updated_at=subtask.updated_at,
            )
            self.db.add(instance)
        else:
            instance.mission_pk = mission.id
            instance.title = subtask.title
            instance.status = subtask.status.value
            instance.owner_role = subtask.owner_role
            instance.depends_on = list(subtask.depends_on)
            instance.created_at = subtask.created_at
            instance.updated_at = subtask.updated_at
        await self.db.flush()
        return self._subtask_record(instance, subtask.mission_id)

    async def get_subtask(self, subtask_id: str) -> SubtaskRecord | None:
        instance = await self._get_subtask_model(subtask_id)
        if instance is None:
            return None
        mission_id = await self._get_mission_public_id(instance.mission_pk)
        return self._subtask_record(instance, mission_id)

    async def list_subtasks(self, mission_id: str) -> list[SubtaskRecord]:
        mission = await self._require_mission_model(mission_id)
        stmt = (
            select(OrchestratorSubtask)
            .where(
                OrchestratorSubtask.organization_id == self.organization_id,
                OrchestratorSubtask.mission_pk == mission.id,
            )
            .order_by(OrchestratorSubtask.created_at.asc(), OrchestratorSubtask.id.asc())
        )
        result = await self.db.execute(stmt)
        return [self._subtask_record(item, mission_id) for item in result.scalars().all()]

    async def save_assignment(self, assignment: AssignmentRecord) -> AssignmentRecord:
        subtask = await self._require_subtask_model(assignment.subtask_id)
        instance = await self._get_assignment_model(assignment.id)
        if instance is None:
            instance = OrchestratorAssignment(
                organization_id=self.organization_id,
                subtask_pk=subtask.id,
                assignment_id=assignment.id,
                assigned_role=assignment.assigned_role,
                handoff_reason=assignment.handoff_reason,
                started_at=assignment.started_at,
                completed_at=assignment.completed_at,
                created_at=assignment.started_at,
                updated_at=assignment.completed_at or assignment.started_at,
            )
            self.db.add(instance)
        else:
            instance.subtask_pk = subtask.id
            instance.assigned_role = assignment.assigned_role
            instance.handoff_reason = assignment.handoff_reason
            instance.started_at = assignment.started_at
            instance.completed_at = assignment.completed_at
            instance.created_at = assignment.started_at
            instance.updated_at = assignment.completed_at or assignment.started_at
        await self.db.flush()
        return self._assignment_record(instance, assignment.subtask_id)

    async def get_assignment(self, assignment_id: str) -> AssignmentRecord | None:
        instance = await self._get_assignment_model(assignment_id)
        if instance is None:
            return None
        subtask_id = await self._get_subtask_public_id(instance.subtask_pk)
        return self._assignment_record(instance, subtask_id)

    async def list_assignments(self, subtask_ids: Sequence[str]) -> list[AssignmentRecord]:
        if not subtask_ids:
            return []
        rows = await self._load_subtasks_by_public_ids(subtask_ids)
        pk_to_public = {row.id: row.subtask_id for row in rows}
        if not pk_to_public:
            return []
        stmt = (
            select(OrchestratorAssignment)
            .where(
                OrchestratorAssignment.organization_id == self.organization_id,
                OrchestratorAssignment.subtask_pk.in_(pk_to_public.keys()),
            )
            .order_by(OrchestratorAssignment.started_at.asc(), OrchestratorAssignment.id.asc())
        )
        result = await self.db.execute(stmt)
        return [self._assignment_record(item, pk_to_public[item.subtask_pk]) for item in result.scalars().all()]

    async def save_evidence_item(self, item: EvidenceItemRecord) -> EvidenceItemRecord:
        mission_pk = await self._resolve_optional_mission_pk(item.mission_id)
        subtask_pk = await self._resolve_optional_subtask_pk(item.subtask_id)
        instance = await self._get_evidence_model(item.id)
        if instance is None:
            instance = OrchestratorEvidenceItem(
                organization_id=self.organization_id,
                mission_pk=mission_pk,
                subtask_pk=subtask_pk,
                evidence_item_id=item.id,
                kind=item.kind,
                source_path=item.source_path,
                evidence_class=item.evidence_class,
                summary=item.summary,
                recorded_at=item.recorded_at,
                created_at=item.recorded_at,
                updated_at=item.recorded_at,
            )
            self.db.add(instance)
        else:
            instance.mission_pk = mission_pk
            instance.subtask_pk = subtask_pk
            instance.kind = item.kind
            instance.source_path = item.source_path
            instance.evidence_class = item.evidence_class
            instance.summary = item.summary
            instance.recorded_at = item.recorded_at
            instance.created_at = item.recorded_at
            instance.updated_at = item.recorded_at
        await self.db.flush()
        return self._evidence_record(instance, item.mission_id, item.subtask_id)

    async def list_evidence_items(
        self,
        mission_id: str,
        subtask_ids: Sequence[str],
    ) -> list[EvidenceItemRecord]:
        mission = await self._require_mission_model(mission_id)
        subtask_rows = await self._load_subtasks_by_public_ids(subtask_ids)
        pk_to_public = {row.id: row.subtask_id for row in subtask_rows}
        stmt = select(OrchestratorEvidenceItem).where(
            OrchestratorEvidenceItem.organization_id == self.organization_id,
            (OrchestratorEvidenceItem.mission_pk == mission.id)
            | (OrchestratorEvidenceItem.subtask_pk.in_(pk_to_public.keys()) if pk_to_public else False),
        ).order_by(OrchestratorEvidenceItem.recorded_at.asc(), OrchestratorEvidenceItem.id.asc())
        result = await self.db.execute(stmt)
        items: list[EvidenceItemRecord] = []
        for row in result.scalars().all():
            items.append(
                self._evidence_record(
                    row,
                    mission_id if row.mission_pk is not None else None,
                    pk_to_public.get(row.subtask_pk),
                )
            )
        return items

    async def save_verification_run(self, verification: VerificationRunRecord) -> VerificationRunRecord:
        mission_pk, subtask_pk = await self._resolve_subject_pks(verification.subject_id)
        instance = await self._get_verification_model(verification.id)
        if instance is None:
            instance = OrchestratorVerificationRun(
                organization_id=self.organization_id,
                mission_pk=mission_pk,
                subtask_pk=subtask_pk,
                verification_run_id=verification.id,
                verification_type=verification.verification_type,
                result=verification.result.value,
                evidence_ref=verification.evidence_ref,
                executed_at=verification.executed_at,
                created_at=verification.executed_at,
                updated_at=verification.executed_at,
            )
            self.db.add(instance)
        else:
            instance.mission_pk = mission_pk
            instance.subtask_pk = subtask_pk
            instance.verification_type = verification.verification_type
            instance.result = verification.result.value
            instance.evidence_ref = verification.evidence_ref
            instance.executed_at = verification.executed_at
            instance.created_at = verification.executed_at
            instance.updated_at = verification.executed_at
        await self.db.flush()
        return self._verification_record(verification.subject_id, instance)

    async def list_verification_runs(self, subject_ids: Sequence[str]) -> list[VerificationRunRecord]:
        if not subject_ids:
            return []
        mission_rows = await self._load_missions_by_public_ids(subject_ids)
        subtask_rows = await self._load_subtasks_by_public_ids(subject_ids)
        mission_pk_to_public = {row.id: row.mission_id for row in mission_rows}
        subtask_pk_to_public = {row.id: row.subtask_id for row in subtask_rows}
        if not mission_pk_to_public and not subtask_pk_to_public:
            return []
        stmt = select(OrchestratorVerificationRun).where(
            OrchestratorVerificationRun.organization_id == self.organization_id,
            (OrchestratorVerificationRun.mission_pk.in_(mission_pk_to_public.keys()) if mission_pk_to_public else False)
            | (OrchestratorVerificationRun.subtask_pk.in_(subtask_pk_to_public.keys()) if subtask_pk_to_public else False),
        ).order_by(OrchestratorVerificationRun.executed_at.asc(), OrchestratorVerificationRun.id.asc())
        result = await self.db.execute(stmt)
        items: list[VerificationRunRecord] = []
        for row in result.scalars().all():
            subject_id = mission_pk_to_public.get(row.mission_pk) or subtask_pk_to_public.get(row.subtask_pk)
            items.append(self._verification_record(subject_id, row))
        return items

    async def save_decision_note(self, note: DecisionNoteRecord) -> DecisionNoteRecord:
        mission = await self._require_mission_model(note.mission_id)
        instance = await self._get_decision_model(note.id)
        if instance is None:
            instance = OrchestratorDecisionNote(
                organization_id=self.organization_id,
                mission_pk=mission.id,
                decision_note_id=note.id,
                decision_class=note.decision_class,
                rationale=note.rationale,
                authority_source=note.authority_source,
                recorded_at=note.recorded_at,
                created_at=note.recorded_at,
                updated_at=note.recorded_at,
            )
            self.db.add(instance)
        else:
            instance.mission_pk = mission.id
            instance.decision_class = note.decision_class
            instance.rationale = note.rationale
            instance.authority_source = note.authority_source
            instance.recorded_at = note.recorded_at
            instance.created_at = note.recorded_at
            instance.updated_at = note.recorded_at
        await self.db.flush()
        return self._decision_record(instance, note.mission_id)

    async def list_decision_notes(self, mission_id: str) -> list[DecisionNoteRecord]:
        mission = await self._require_mission_model(mission_id)
        stmt = (
            select(OrchestratorDecisionNote)
            .where(
                OrchestratorDecisionNote.organization_id == self.organization_id,
                OrchestratorDecisionNote.mission_pk == mission.id,
            )
            .order_by(OrchestratorDecisionNote.recorded_at.asc(), OrchestratorDecisionNote.id.asc())
        )
        result = await self.db.execute(stmt)
        return [self._decision_record(item, mission_id) for item in result.scalars().all()]

    async def save_blocker(self, blocker: BlockerRecord) -> BlockerRecord:
        mission_pk = await self._resolve_optional_mission_pk(blocker.mission_id)
        subtask_pk = await self._resolve_optional_subtask_pk(blocker.subtask_id)
        instance = await self._get_blocker_model(blocker.id)
        if instance is None:
            instance = OrchestratorBlocker(
                organization_id=self.organization_id,
                mission_pk=mission_pk,
                subtask_pk=subtask_pk,
                blocker_id=blocker.id,
                blocker_type=blocker.blocker_type,
                impact=blocker.impact,
                escalation_needed=blocker.escalation_needed,
                recorded_at=blocker.recorded_at,
                created_at=blocker.recorded_at,
                updated_at=blocker.recorded_at,
            )
            self.db.add(instance)
        else:
            instance.mission_pk = mission_pk
            instance.subtask_pk = subtask_pk
            instance.blocker_type = blocker.blocker_type
            instance.impact = blocker.impact
            instance.escalation_needed = blocker.escalation_needed
            instance.recorded_at = blocker.recorded_at
            instance.created_at = blocker.recorded_at
            instance.updated_at = blocker.recorded_at
        await self.db.flush()
        return self._blocker_record(instance, blocker.mission_id, blocker.subtask_id)

    async def list_blockers(self, mission_id: str, subtask_ids: Sequence[str]) -> list[BlockerRecord]:
        mission = await self._require_mission_model(mission_id)
        subtask_rows = await self._load_subtasks_by_public_ids(subtask_ids)
        pk_to_public = {row.id: row.subtask_id for row in subtask_rows}
        stmt = select(OrchestratorBlocker).where(
            OrchestratorBlocker.organization_id == self.organization_id,
            (OrchestratorBlocker.mission_pk == mission.id)
            | (OrchestratorBlocker.subtask_pk.in_(pk_to_public.keys()) if pk_to_public else False),
        ).order_by(OrchestratorBlocker.recorded_at.asc(), OrchestratorBlocker.id.asc())
        result = await self.db.execute(stmt)
        return [
            self._blocker_record(item, mission_id if item.mission_pk is not None else None, pk_to_public.get(item.subtask_pk))
            for item in result.scalars().all()
        ]

    async def _get_mission_model(self, mission_id: str) -> OrchestratorMission | None:
        stmt = select(OrchestratorMission).where(
            OrchestratorMission.organization_id == self.organization_id,
            OrchestratorMission.mission_id == mission_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_subtask_model(self, subtask_id: str) -> OrchestratorSubtask | None:
        stmt = select(OrchestratorSubtask).where(
            OrchestratorSubtask.organization_id == self.organization_id,
            OrchestratorSubtask.subtask_id == subtask_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_assignment_model(self, assignment_id: str) -> OrchestratorAssignment | None:
        stmt = select(OrchestratorAssignment).where(
            OrchestratorAssignment.organization_id == self.organization_id,
            OrchestratorAssignment.assignment_id == assignment_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_evidence_model(self, evidence_item_id: str) -> OrchestratorEvidenceItem | None:
        stmt = select(OrchestratorEvidenceItem).where(
            OrchestratorEvidenceItem.organization_id == self.organization_id,
            OrchestratorEvidenceItem.evidence_item_id == evidence_item_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_verification_model(self, verification_run_id: str) -> OrchestratorVerificationRun | None:
        stmt = select(OrchestratorVerificationRun).where(
            OrchestratorVerificationRun.organization_id == self.organization_id,
            OrchestratorVerificationRun.verification_run_id == verification_run_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_decision_model(self, decision_note_id: str) -> OrchestratorDecisionNote | None:
        stmt = select(OrchestratorDecisionNote).where(
            OrchestratorDecisionNote.organization_id == self.organization_id,
            OrchestratorDecisionNote.decision_note_id == decision_note_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_blocker_model(self, blocker_id: str) -> OrchestratorBlocker | None:
        stmt = select(OrchestratorBlocker).where(
            OrchestratorBlocker.organization_id == self.organization_id,
            OrchestratorBlocker.blocker_id == blocker_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _require_mission_model(self, mission_id: str) -> OrchestratorMission:
        instance = await self._get_mission_model(mission_id)
        if instance is None:
            raise ValueError(f"Unknown mission: {mission_id}")
        return instance

    async def _require_subtask_model(self, subtask_id: str) -> OrchestratorSubtask:
        instance = await self._get_subtask_model(subtask_id)
        if instance is None:
            raise ValueError(f"Unknown subtask: {subtask_id}")
        return instance

    async def _get_mission_public_id(self, mission_pk: int) -> str:
        stmt = select(OrchestratorMission.mission_id).where(
            OrchestratorMission.organization_id == self.organization_id,
            OrchestratorMission.id == mission_pk,
        )
        result = await self.db.execute(stmt)
        mission_id = result.scalar_one_or_none()
        if mission_id is None:
            raise ValueError(f"Unknown mission primary key: {mission_pk}")
        return mission_id

    async def _get_subtask_public_id(self, subtask_pk: int) -> str:
        stmt = select(OrchestratorSubtask.subtask_id).where(
            OrchestratorSubtask.organization_id == self.organization_id,
            OrchestratorSubtask.id == subtask_pk,
        )
        result = await self.db.execute(stmt)
        subtask_id = result.scalar_one_or_none()
        if subtask_id is None:
            raise ValueError(f"Unknown subtask primary key: {subtask_pk}")
        return subtask_id

    async def _load_missions_by_public_ids(self, mission_ids: Sequence[str]) -> list[OrchestratorMission]:
        if not mission_ids:
            return []
        stmt = select(OrchestratorMission).where(
            OrchestratorMission.organization_id == self.organization_id,
            OrchestratorMission.mission_id.in_(tuple(mission_ids)),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _load_subtasks_by_public_ids(self, subtask_ids: Sequence[str]) -> list[OrchestratorSubtask]:
        if not subtask_ids:
            return []
        stmt = select(OrchestratorSubtask).where(
            OrchestratorSubtask.organization_id == self.organization_id,
            OrchestratorSubtask.subtask_id.in_(tuple(subtask_ids)),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _resolve_optional_mission_pk(self, mission_id: str | None) -> int | None:
        if mission_id is None:
            return None
        mission = await self._require_mission_model(mission_id)
        return mission.id

    async def _resolve_optional_subtask_pk(self, subtask_id: str | None) -> int | None:
        if subtask_id is None:
            return None
        subtask = await self._require_subtask_model(subtask_id)
        return subtask.id

    async def _resolve_subject_pks(self, subject_id: str) -> tuple[int | None, int | None]:
        mission = await self._get_mission_model(subject_id)
        if mission is not None:
            return mission.id, None
        subtask = await self._get_subtask_model(subject_id)
        if subtask is not None:
            return None, subtask.id
        raise ValueError(f"Unknown mission or subtask subject: {subject_id}")

    def _mission_record(self, instance: OrchestratorMission) -> MissionRecord:
        return MissionRecord(
            id=instance.mission_id,
            objective=instance.objective,
            status=MissionStatus(instance.status),
            owner=instance.owner,
            priority=instance.priority,
            producer_key=instance.producer_key,
            source_request=instance.source_request,
            final_summary=instance.final_summary,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )

    def _subtask_record(self, instance: OrchestratorSubtask, mission_id: str) -> SubtaskRecord:
        return SubtaskRecord(
            id=instance.subtask_id,
            mission_id=mission_id,
            title=instance.title,
            status=SubtaskStatus(instance.status),
            owner_role=instance.owner_role,
            depends_on=tuple(instance.depends_on or []),
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )

    def _assignment_record(self, instance: OrchestratorAssignment, subtask_id: str) -> AssignmentRecord:
        return AssignmentRecord(
            id=instance.assignment_id,
            subtask_id=subtask_id,
            assigned_role=instance.assigned_role,
            handoff_reason=instance.handoff_reason,
            started_at=instance.started_at,
            completed_at=instance.completed_at,
        )

    def _evidence_record(
        self,
        instance: OrchestratorEvidenceItem,
        mission_id: str | None,
        subtask_id: str | None,
    ) -> EvidenceItemRecord:
        return EvidenceItemRecord(
            id=instance.evidence_item_id,
            mission_id=mission_id,
            subtask_id=subtask_id,
            kind=instance.kind,
            source_path=instance.source_path,
            evidence_class=instance.evidence_class,
            summary=instance.summary,
            recorded_at=instance.recorded_at,
        )

    def _verification_record(
        self,
        subject_id: str,
        instance: OrchestratorVerificationRun,
    ) -> VerificationRunRecord:
        return VerificationRunRecord(
            id=instance.verification_run_id,
            subject_id=subject_id,
            verification_type=instance.verification_type,
            result=VerificationResult(instance.result),
            evidence_ref=instance.evidence_ref,
            executed_at=instance.executed_at,
        )

    def _decision_record(self, instance: OrchestratorDecisionNote, mission_id: str) -> DecisionNoteRecord:
        return DecisionNoteRecord(
            id=instance.decision_note_id,
            mission_id=mission_id,
            decision_class=instance.decision_class,
            rationale=instance.rationale,
            authority_source=instance.authority_source,
            recorded_at=instance.recorded_at,
        )

    def _blocker_record(
        self,
        instance: OrchestratorBlocker,
        mission_id: str | None,
        subtask_id: str | None,
    ) -> BlockerRecord:
        return BlockerRecord(
            id=instance.blocker_id,
            mission_id=mission_id,
            subtask_id=subtask_id,
            blocker_type=instance.blocker_type,
            impact=instance.impact,
            escalation_needed=instance.escalation_needed,
            recorded_at=instance.recorded_at,
        )


__all__ = ["PostgresMissionStateRepository"]
"""Storage-neutral mission-state bootstrap for OmShriMaatreNamaha.

primary_domain = "ai_orchestration"
secondary_domains = ["governance", "validation", "operations"]
assumptions = [
    "The bootstrap slice proves the mission-state contract before any SurrealDB runtime integration.",
    "Async repository interfaces should match the surrounding FastAPI and SQLAlchemy service layer.",
    "Mission evidence may attach directly to a mission or to a subtask within that mission."
]
limitations = [
    "This module ships only a volatile in-process repository adapter.",
    "No public API routes are exposed yet for mission-state management.",
    "Cross-process durability is deferred until the repository interface is exercised by real flows."
]
uncertainty_handling = "Mission-state durability remains storage-neutral in Phase 1; higher-durability adapters are intentionally deferred."
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol
from uuid import uuid4


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


class MissionStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    BLOCKED = "blocked"
    VERIFIED = "verified"
    COMPLETED = "completed"


class SubtaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class VerificationResult(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    WARN = "warn"


@dataclass(frozen=True, slots=True)
class MissionRecord:
    id: str
    objective: str
    status: MissionStatus
    owner: str
    priority: str
    source_request: str
    producer_key: str | None = None
    final_summary: str | None = None
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class SubtaskRecord:
    id: str
    mission_id: str
    title: str
    status: SubtaskStatus
    owner_role: str
    depends_on: tuple[str, ...] = tuple()
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class AssignmentRecord:
    id: str
    subtask_id: str
    assigned_role: str
    handoff_reason: str
    started_at: datetime = field(default_factory=_utc_now)
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class EvidenceItemRecord:
    id: str
    mission_id: str | None
    subtask_id: str | None
    kind: str
    source_path: str
    evidence_class: str
    summary: str
    recorded_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class VerificationRunRecord:
    id: str
    subject_id: str
    verification_type: str
    result: VerificationResult
    evidence_ref: str | None
    executed_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class DecisionNoteRecord:
    id: str
    mission_id: str
    decision_class: str
    rationale: str
    authority_source: str
    recorded_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class BlockerRecord:
    id: str
    mission_id: str | None
    subtask_id: str | None
    blocker_type: str
    impact: str
    escalation_needed: bool
    recorded_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class MissionStateSnapshot:
    mission: MissionRecord
    subtasks: tuple[SubtaskRecord, ...] = tuple()
    assignments: tuple[AssignmentRecord, ...] = tuple()
    evidence_items: tuple[EvidenceItemRecord, ...] = tuple()
    verification_runs: tuple[VerificationRunRecord, ...] = tuple()
    decision_notes: tuple[DecisionNoteRecord, ...] = tuple()
    blockers: tuple[BlockerRecord, ...] = tuple()

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission": self.mission.to_dict(),
            "subtasks": [item.to_dict() for item in self.subtasks],
            "assignments": [item.to_dict() for item in self.assignments],
            "evidence_items": [item.to_dict() for item in self.evidence_items],
            "verification_runs": [item.to_dict() for item in self.verification_runs],
            "decision_notes": [item.to_dict() for item in self.decision_notes],
            "blockers": [item.to_dict() for item in self.blockers],
        }


class MissionStateRepository(Protocol):
    async def save_mission(self, mission: MissionRecord) -> MissionRecord: ...

    async def get_mission(self, mission_id: str) -> MissionRecord | None: ...

    async def list_missions(self) -> list[MissionRecord]: ...

    async def save_subtask(self, subtask: SubtaskRecord) -> SubtaskRecord: ...

    async def get_subtask(self, subtask_id: str) -> SubtaskRecord | None: ...

    async def list_subtasks(self, mission_id: str) -> list[SubtaskRecord]: ...

    async def save_assignment(self, assignment: AssignmentRecord) -> AssignmentRecord: ...

    async def get_assignment(self, assignment_id: str) -> AssignmentRecord | None: ...

    async def list_assignments(self, subtask_ids: Sequence[str]) -> list[AssignmentRecord]: ...

    async def save_evidence_item(self, item: EvidenceItemRecord) -> EvidenceItemRecord: ...

    async def list_evidence_items(
        self,
        mission_id: str,
        subtask_ids: Sequence[str],
    ) -> list[EvidenceItemRecord]: ...

    async def save_verification_run(self, verification: VerificationRunRecord) -> VerificationRunRecord: ...

    async def list_verification_runs(self, subject_ids: Sequence[str]) -> list[VerificationRunRecord]: ...

    async def save_decision_note(self, note: DecisionNoteRecord) -> DecisionNoteRecord: ...

    async def list_decision_notes(self, mission_id: str) -> list[DecisionNoteRecord]: ...

    async def save_blocker(self, blocker: BlockerRecord) -> BlockerRecord: ...

    async def list_blockers(self, mission_id: str, subtask_ids: Sequence[str]) -> list[BlockerRecord]: ...


class VolatileMissionStateRepository:
    """In-memory mission-state repository used to prove the bootstrap contract."""

    def __init__(self) -> None:
        self._missions: dict[str, MissionRecord] = {}
        self._subtasks: dict[str, SubtaskRecord] = {}
        self._assignments: dict[str, AssignmentRecord] = {}
        self._evidence_items: dict[str, EvidenceItemRecord] = {}
        self._verification_runs: dict[str, VerificationRunRecord] = {}
        self._decision_notes: dict[str, DecisionNoteRecord] = {}
        self._blockers: dict[str, BlockerRecord] = {}

    async def save_mission(self, mission: MissionRecord) -> MissionRecord:
        self._missions[mission.id] = mission
        return mission

    async def get_mission(self, mission_id: str) -> MissionRecord | None:
        return self._missions.get(mission_id)

    async def list_missions(self) -> list[MissionRecord]:
        return list(self._missions.values())

    async def save_subtask(self, subtask: SubtaskRecord) -> SubtaskRecord:
        self._subtasks[subtask.id] = subtask
        return subtask

    async def get_subtask(self, subtask_id: str) -> SubtaskRecord | None:
        return self._subtasks.get(subtask_id)

    async def list_subtasks(self, mission_id: str) -> list[SubtaskRecord]:
        return [item for item in self._subtasks.values() if item.mission_id == mission_id]

    async def save_assignment(self, assignment: AssignmentRecord) -> AssignmentRecord:
        self._assignments[assignment.id] = assignment
        return assignment

    async def get_assignment(self, assignment_id: str) -> AssignmentRecord | None:
        return self._assignments.get(assignment_id)

    async def list_assignments(self, subtask_ids: Sequence[str]) -> list[AssignmentRecord]:
        subtask_id_set = set(subtask_ids)
        return [item for item in self._assignments.values() if item.subtask_id in subtask_id_set]

    async def save_evidence_item(self, item: EvidenceItemRecord) -> EvidenceItemRecord:
        self._evidence_items[item.id] = item
        return item

    async def list_evidence_items(
        self,
        mission_id: str,
        subtask_ids: Sequence[str],
    ) -> list[EvidenceItemRecord]:
        subtask_id_set = set(subtask_ids)
        return [
            item
            for item in self._evidence_items.values()
            if item.mission_id == mission_id or (item.subtask_id is not None and item.subtask_id in subtask_id_set)
        ]

    async def save_verification_run(self, verification: VerificationRunRecord) -> VerificationRunRecord:
        self._verification_runs[verification.id] = verification
        return verification

    async def list_verification_runs(self, subject_ids: Sequence[str]) -> list[VerificationRunRecord]:
        subject_id_set = set(subject_ids)
        return [item for item in self._verification_runs.values() if item.subject_id in subject_id_set]

    async def save_decision_note(self, note: DecisionNoteRecord) -> DecisionNoteRecord:
        self._decision_notes[note.id] = note
        return note

    async def list_decision_notes(self, mission_id: str) -> list[DecisionNoteRecord]:
        return [item for item in self._decision_notes.values() if item.mission_id == mission_id]

    async def save_blocker(self, blocker: BlockerRecord) -> BlockerRecord:
        self._blockers[blocker.id] = blocker
        return blocker

    async def list_blockers(self, mission_id: str, subtask_ids: Sequence[str]) -> list[BlockerRecord]:
        subtask_id_set = set(subtask_ids)
        return [
            item
            for item in self._blockers.values()
            if item.mission_id == mission_id or (item.subtask_id is not None and item.subtask_id in subtask_id_set)
        ]


class OrchestratorMissionStateService:
    """Mission-state registration and audit flow for the OmShriMaatreNamaha bootstrap."""

    def __init__(self, repository: MissionStateRepository) -> None:
        self.repository = repository

    async def register_mission(
        self,
        *,
        objective: str,
        owner: str,
        priority: str,
        source_request: str,
        producer_key: str | None = None,
        mission_id: str | None = None,
    ) -> MissionRecord:
        mission = MissionRecord(
            id=mission_id or _new_id("mission"),
            objective=objective,
            status=MissionStatus.ACTIVE,
            owner=owner,
            priority=priority,
            producer_key=producer_key,
            source_request=source_request,
        )
        return await self.repository.save_mission(mission)

    async def add_subtask(
        self,
        *,
        mission_id: str,
        title: str,
        owner_role: str,
        depends_on: Sequence[str] = (),
        subtask_id: str | None = None,
    ) -> SubtaskRecord:
        await self._require_mission(mission_id)
        existing_subtasks = await self.repository.list_subtasks(mission_id)
        existing_subtask_ids = {item.id for item in existing_subtasks}
        missing_dependencies = sorted(set(depends_on) - existing_subtask_ids)
        if missing_dependencies:
            raise ValueError(
                f"Unknown subtask dependencies for mission {mission_id}: {', '.join(missing_dependencies)}"
            )

        subtask = SubtaskRecord(
            id=subtask_id or _new_id("subtask"),
            mission_id=mission_id,
            title=title,
            status=SubtaskStatus.TODO,
            owner_role=owner_role,
            depends_on=tuple(depends_on),
        )
        return await self.repository.save_subtask(subtask)

    async def update_subtask_status(self, subtask_id: str, status: SubtaskStatus) -> SubtaskRecord:
        subtask = await self._require_subtask(subtask_id)
        updated = replace(subtask, status=status, updated_at=_utc_now())
        return await self.repository.save_subtask(updated)

    async def assign_subtask(
        self,
        *,
        subtask_id: str,
        assigned_role: str,
        handoff_reason: str,
        assignment_id: str | None = None,
    ) -> AssignmentRecord:
        await self._require_subtask(subtask_id)
        assignment = AssignmentRecord(
            id=assignment_id or _new_id("assignment"),
            subtask_id=subtask_id,
            assigned_role=assigned_role,
            handoff_reason=handoff_reason,
        )
        return await self.repository.save_assignment(assignment)

    async def complete_assignment(self, assignment_id: str) -> AssignmentRecord:
        assignment = await self.repository.get_assignment(assignment_id)
        if assignment is None:
            raise ValueError(f"Unknown assignment: {assignment_id}")
        updated = replace(assignment, completed_at=_utc_now())
        return await self.repository.save_assignment(updated)

    async def record_evidence(
        self,
        *,
        kind: str,
        source_path: str,
        evidence_class: str,
        summary: str,
        mission_id: str | None = None,
        subtask_id: str | None = None,
        evidence_item_id: str | None = None,
    ) -> EvidenceItemRecord:
        mission_ref, subtask_ref = await self._resolve_subject(mission_id=mission_id, subtask_id=subtask_id)
        item = EvidenceItemRecord(
            id=evidence_item_id or _new_id("evidence"),
            mission_id=mission_ref,
            subtask_id=subtask_ref,
            kind=kind,
            source_path=source_path,
            evidence_class=evidence_class,
            summary=summary,
        )
        return await self.repository.save_evidence_item(item)

    async def record_verification_run(
        self,
        *,
        subject_id: str,
        verification_type: str,
        result: VerificationResult,
        evidence_ref: str | None = None,
        verification_id: str | None = None,
    ) -> VerificationRunRecord:
        await self._require_subject(subject_id)
        verification = VerificationRunRecord(
            id=verification_id or _new_id("verification"),
            subject_id=subject_id,
            verification_type=verification_type,
            result=result,
            evidence_ref=evidence_ref,
        )
        return await self.repository.save_verification_run(verification)

    async def record_decision_note(
        self,
        *,
        mission_id: str,
        decision_class: str,
        rationale: str,
        authority_source: str,
        decision_note_id: str | None = None,
    ) -> DecisionNoteRecord:
        await self._require_mission(mission_id)
        note = DecisionNoteRecord(
            id=decision_note_id or _new_id("decision"),
            mission_id=mission_id,
            decision_class=decision_class,
            rationale=rationale,
            authority_source=authority_source,
        )
        return await self.repository.save_decision_note(note)

    async def record_blocker(
        self,
        *,
        blocker_type: str,
        impact: str,
        escalation_needed: bool,
        mission_id: str | None = None,
        subtask_id: str | None = None,
        blocker_id: str | None = None,
    ) -> BlockerRecord:
        mission_ref, subtask_ref = await self._resolve_subject(mission_id=mission_id, subtask_id=subtask_id)
        blocker = BlockerRecord(
            id=blocker_id or _new_id("blocker"),
            mission_id=mission_ref,
            subtask_id=subtask_ref,
            blocker_type=blocker_type,
            impact=impact,
            escalation_needed=escalation_needed,
        )
        return await self.repository.save_blocker(blocker)

    async def complete_mission(self, mission_id: str, final_summary: str) -> MissionRecord:
        mission = await self._require_mission(mission_id)
        updated = replace(
            mission,
            status=MissionStatus.COMPLETED,
            final_summary=final_summary,
            updated_at=_utc_now(),
        )
        return await self.repository.save_mission(updated)

    async def get_mission_snapshot(self, mission_id: str) -> MissionStateSnapshot:
        mission = await self._require_mission(mission_id)
        subtasks = tuple(await self.repository.list_subtasks(mission_id))
        subtask_ids = tuple(item.id for item in subtasks)
        subject_ids = (mission_id, *subtask_ids)
        assignments = tuple(await self.repository.list_assignments(subtask_ids))
        evidence_items = tuple(await self.repository.list_evidence_items(mission_id, subtask_ids))
        verification_runs = tuple(await self.repository.list_verification_runs(subject_ids))
        decision_notes = tuple(await self.repository.list_decision_notes(mission_id))
        blockers = tuple(await self.repository.list_blockers(mission_id, subtask_ids))
        return MissionStateSnapshot(
            mission=mission,
            subtasks=subtasks,
            assignments=assignments,
            evidence_items=evidence_items,
            verification_runs=verification_runs,
            decision_notes=decision_notes,
            blockers=blockers,
        )

    async def _require_mission(self, mission_id: str) -> MissionRecord:
        mission = await self.repository.get_mission(mission_id)
        if mission is None:
            raise ValueError(f"Unknown mission: {mission_id}")
        return mission

    async def _require_subtask(self, subtask_id: str) -> SubtaskRecord:
        subtask = await self.repository.get_subtask(subtask_id)
        if subtask is None:
            raise ValueError(f"Unknown subtask: {subtask_id}")
        return subtask

    async def _require_subject(self, subject_id: str) -> None:
        if await self.repository.get_mission(subject_id) is not None:
            return
        if await self.repository.get_subtask(subject_id) is not None:
            return
        raise ValueError(f"Unknown mission or subtask subject: {subject_id}")

    async def _resolve_subject(
        self,
        *,
        mission_id: str | None,
        subtask_id: str | None,
    ) -> tuple[str | None, str | None]:
        if mission_id and subtask_id:
            subtask = await self._require_subtask(subtask_id)
            if subtask.mission_id != mission_id:
                raise ValueError(
                    f"Subtask {subtask_id} does not belong to mission {mission_id}"
                )
            return mission_id, subtask_id
        if subtask_id:
            subtask = await self._require_subtask(subtask_id)
            return subtask.mission_id, subtask_id
        if mission_id:
            await self._require_mission(mission_id)
            return mission_id, None
        raise ValueError("A mission_id or subtask_id is required")


__all__ = [
    "AssignmentRecord",
    "BlockerRecord",
    "DecisionNoteRecord",
    "EvidenceItemRecord",
    "MissionRecord",
    "MissionStateRepository",
    "MissionStateSnapshot",
    "MissionStatus",
    "OrchestratorMissionStateService",
    "SubtaskRecord",
    "SubtaskStatus",
    "VerificationResult",
    "VerificationRunRecord",
    "VolatileMissionStateRepository",
]
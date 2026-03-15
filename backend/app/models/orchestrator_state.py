"""Durable mission-state models for OmShriMaatreNamaha orchestration.

These tables persist the accepted ADR-012 orchestration objects inside the
existing PostgreSQL and RLS model rather than committing early to a separate
coordination engine.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


if TYPE_CHECKING:
    from app.models.core import Organization


class OrchestratorMission(BaseModel):
    """Mission-level durable state for the orchestrator."""

    __tablename__ = "orchestrator_missions"
    __table_args__ = (
        UniqueConstraint("mission_id", name="uq_orchestrator_mission_public_id"),
        Index("ix_orchestrator_mission_org_status", "organization_id", "status"),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    mission_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    producer_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_request: Mapped[str] = mapped_column(Text, nullable=False)
    final_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship("Organization")
    subtasks: Mapped[list["OrchestratorSubtask"]] = relationship(
        "OrchestratorSubtask",
        back_populates="mission",
        cascade="all, delete-orphan",
    )


class OrchestratorSubtask(BaseModel):
    """Subtask decomposition record for a mission."""

    __tablename__ = "orchestrator_subtasks"
    __table_args__ = (
        UniqueConstraint("subtask_id", name="uq_orchestrator_subtask_public_id"),
        Index("ix_orchestrator_subtask_mission_status", "mission_pk", "status"),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    mission_pk: Mapped[int] = mapped_column(
        Integer, ForeignKey("orchestrator_missions.id"), nullable=False, index=True
    )
    subtask_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    owner_role: Mapped[str] = mapped_column(String(255), nullable=False)
    depends_on: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    organization: Mapped["Organization"] = relationship("Organization")
    mission: Mapped[OrchestratorMission] = relationship("OrchestratorMission", back_populates="subtasks")
    assignments: Mapped[list["OrchestratorAssignment"]] = relationship(
        "OrchestratorAssignment",
        back_populates="subtask",
        cascade="all, delete-orphan",
    )


class OrchestratorAssignment(BaseModel):
    """Delegation record for one subtask handoff."""

    __tablename__ = "orchestrator_assignments"
    __table_args__ = (
        UniqueConstraint("assignment_id", name="uq_orchestrator_assignment_public_id"),
        Index("ix_orchestrator_assignment_subtask_role", "subtask_pk", "assigned_role"),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    subtask_pk: Mapped[int] = mapped_column(
        Integer, ForeignKey("orchestrator_subtasks.id"), nullable=False, index=True
    )
    assignment_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    assigned_role: Mapped[str] = mapped_column(String(255), nullable=False)
    handoff_reason: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship("Organization")
    subtask: Mapped[OrchestratorSubtask] = relationship("OrchestratorSubtask", back_populates="assignments")


class OrchestratorEvidenceItem(BaseModel):
    """Durable evidence link for mission or subtask state."""

    __tablename__ = "orchestrator_evidence_items"
    __table_args__ = (
        UniqueConstraint("evidence_item_id", name="uq_orchestrator_evidence_public_id"),
        Index("ix_orchestrator_evidence_mission_kind", "mission_pk", "kind"),
        Index("ix_orchestrator_evidence_subtask_kind", "subtask_pk", "kind"),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    mission_pk: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("orchestrator_missions.id"), nullable=True, index=True
    )
    subtask_pk: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("orchestrator_subtasks.id"), nullable=True, index=True
    )
    evidence_item_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_class: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    organization: Mapped["Organization"] = relationship("Organization")


class OrchestratorVerificationRun(BaseModel):
    """Durable verification result for mission or subtask subjects."""

    __tablename__ = "orchestrator_verification_runs"
    __table_args__ = (
        UniqueConstraint("verification_run_id", name="uq_orchestrator_verification_public_id"),
        Index("ix_orchestrator_verification_mission_type", "mission_pk", "verification_type"),
        Index("ix_orchestrator_verification_subtask_type", "subtask_pk", "verification_type"),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    mission_pk: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("orchestrator_missions.id"), nullable=True, index=True
    )
    subtask_pk: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("orchestrator_subtasks.id"), nullable=True, index=True
    )
    verification_run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    verification_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    result: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    evidence_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    organization: Mapped["Organization"] = relationship("Organization")


class OrchestratorDecisionNote(BaseModel):
    """Durable mission-level decision rationale."""

    __tablename__ = "orchestrator_decision_notes"
    __table_args__ = (
        UniqueConstraint("decision_note_id", name="uq_orchestrator_decision_public_id"),
        Index("ix_orchestrator_decision_mission_class", "mission_pk", "decision_class"),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    mission_pk: Mapped[int] = mapped_column(
        Integer, ForeignKey("orchestrator_missions.id"), nullable=False, index=True
    )
    decision_note_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision_class: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    authority_source: Mapped[str] = mapped_column(String(255), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    organization: Mapped["Organization"] = relationship("Organization")


class OrchestratorBlocker(BaseModel):
    """Durable blocker or escalation state."""

    __tablename__ = "orchestrator_blockers"
    __table_args__ = (
        UniqueConstraint("blocker_id", name="uq_orchestrator_blocker_public_id"),
        Index("ix_orchestrator_blocker_mission_type", "mission_pk", "blocker_type"),
        Index("ix_orchestrator_blocker_subtask_type", "subtask_pk", "blocker_type"),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    mission_pk: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("orchestrator_missions.id"), nullable=True, index=True
    )
    subtask_pk: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("orchestrator_subtasks.id"), nullable=True, index=True
    )
    blocker_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    blocker_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    impact: Mapped[str] = mapped_column(Text, nullable=False)
    escalation_needed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    organization: Mapped["Organization"] = relationship("Organization")
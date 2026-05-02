"""Durable active-board persistence for the developer control plane."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


if TYPE_CHECKING:
    from app.models.core import Organization, User


class DeveloperControlPlaneActiveBoard(BaseModel):
    """Organization-scoped durable active board for the hidden control plane."""

    __tablename__ = "developer_control_plane_active_boards"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "board_id",
            name="uq_developer_control_plane_active_board_org_board",
        ),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    board_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    visibility: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_board_json: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_board_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    updated_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    save_source: Mapped[str] = mapped_column(String(64), nullable=False)
    summary_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    organization: Mapped["Organization"] = relationship("Organization")
    updated_by_user: Mapped["User"] = relationship("User")


class DeveloperControlPlaneBoardRevision(BaseModel):
    """Immutable organization-scoped revision ledger for the hidden control plane."""

    __tablename__ = "developer_control_plane_board_revisions"
    __table_args__ = (
        Index(
            "ix_developer_control_plane_board_revisions_org_board_created_at",
            "organization_id",
            "board_id",
            "created_at",
        ),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    board_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    visibility: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_board_json: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_board_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    saved_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    save_source: Mapped[str] = mapped_column(String(64), nullable=False)
    summary_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    organization: Mapped["Organization"] = relationship("Organization")
    saved_by_user: Mapped["User"] = relationship("User")


class DeveloperControlPlaneApprovalReceipt(BaseModel):
    """Immutable audit receipt for risky developer control-plane actions."""

    __tablename__ = "developer_control_plane_approval_receipts"
    __table_args__ = (
        Index(
            "ix_developer_control_plane_approval_receipts_org_action_created_at",
            "organization_id",
            "action_type",
            "created_at",
        ),
        Index(
            "ix_developer_control_plane_approval_receipts_org_board_lane_created_at",
            "organization_id",
            "board_id",
            "source_lane_id",
            "created_at",
        ),
        Index(
            "ix_developer_control_plane_approval_receipts_org_queue_job_created_at",
            "organization_id",
            "queue_job_id",
            "created_at",
        ),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    authority_actor_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    authority_actor_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    authority_source: Mapped[str] = mapped_column(String(64), nullable=False)
    board_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_board_concurrency_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    resulting_board_concurrency_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    source_lane_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    queue_job_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    expected_queue_sha256: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resulting_queue_sha256: Mapped[str | None] = mapped_column(String(128), nullable=True)
    target_revision_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    previous_active_concurrency_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    linked_mission_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_refs: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    summary_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    organization: Mapped["Organization"] = relationship("Organization")
    authority_actor_user: Mapped["User"] = relationship("User")


class DeveloperControlPlaneLearningEntry(BaseModel):
    """Immutable typed learnings ledger for the hidden developer control plane."""

    __tablename__ = "developer_control_plane_learning_entries"
    __table_args__ = (
        Index(
            "ix_developer_control_plane_learning_entries_org_entry_type_created_at",
            "organization_id",
            "entry_type",
            "created_at",
        ),
        Index(
            "ix_developer_control_plane_learning_entries_org_source_classification_created_at",
            "organization_id",
            "source_classification",
            "created_at",
        ),
        Index(
            "ix_developer_control_plane_learning_entries_org_board_lane_created_at",
            "organization_id",
            "board_id",
            "source_lane_id",
            "created_at",
        ),
        Index(
            "ix_developer_control_plane_learning_entries_org_queue_job_created_at",
            "organization_id",
            "queue_job_id",
            "created_at",
        ),
        Index(
            "ix_developer_control_plane_learning_entries_org_mission_created_at",
            "organization_id",
            "linked_mission_id",
            "created_at",
        ),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    entry_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_classification: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    recorded_by_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    board_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source_lane_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    queue_job_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    linked_mission_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    approval_receipt_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("developer_control_plane_approval_receipts.id"),
        nullable=True,
        index=True,
    )
    source_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    evidence_refs: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    summary_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    organization: Mapped["Organization"] = relationship("Organization")
    recorded_by_user: Mapped["User"] = relationship("User")
"""Veena cognitive models for memory, reasoning and personalized context."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VeenaMemory(Base):
    __tablename__ = "veena_memories_v2"
    __table_args__ = (
        Index("ix_veena_memories_v2_user_id", "user_id"),
        Index("ix_veena_memories_v2_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    context_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ttl_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class ReasoningTrace(Base):
    __tablename__ = "veena_reasoning_traces_v2"
    __table_args__ = (
        Index("ix_reasoning_trace_v2_session_step", "session_id", "step_id", unique=True),
        Index("ix_reasoning_trace_v2_session", "session_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False)
    step_id: Mapped[str] = mapped_column(String(128), nullable=False)
    thought: Mapped[str] = mapped_column(Text, nullable=False)
    tool_used: Mapped[str | None] = mapped_column(String(128), nullable=True)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class UserContext(Base):
    __tablename__ = "veena_user_contexts_v2"
    __table_args__ = (
        Index("ix_veena_user_contexts_v2_user_id", "user_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    expertise_level: Mapped[str] = mapped_column(String(64), nullable=False, default="manager")
    active_project: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class VeenaAuditLog(Base):
    __tablename__ = "veena_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    generated_draft: Mapped[str] = mapped_column(Text, nullable=False)
    flagged_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

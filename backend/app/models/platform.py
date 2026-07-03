"""Platform app installation and capability access models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class OrganizationCapabilityInstallation(BaseModel):
    """Tenant-scoped install state for a platform capability app."""

    __tablename__ = "organization_capability_installations"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "capability_id",
            name="uq_org_capability_installation",
        ),
        Index(
            "ix_org_capability_installations_org_enabled",
            "organization_id",
            "enabled",
        ),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    capability_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    lifecycle_state: Mapped[str] = mapped_column(String(32), nullable=False, default="installed")
    granted_permissions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    data_scopes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    installed_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    disabled_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    organization = relationship("Organization")
    installed_by = relationship("User", foreign_keys=[installed_by_user_id])
    disabled_by = relationship("User", foreign_keys=[disabled_by_user_id])

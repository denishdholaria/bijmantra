"""Federated agricultural asset registry models."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class FederatedAssetConnector(BaseModel):
    """Tenant-owned connector manifest for external agricultural metadata sources."""

    __tablename__ = "federated_asset_connectors"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "connector_key",
            name="uq_federated_asset_connectors_org_key",
        ),
        Index("ix_federated_asset_connectors_org_type", "organization_id", "connector_type"),
        Index("ix_federated_asset_connectors_org_enabled", "organization_id", "enabled"),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    connector_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    connector_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint_url: Mapped[str | None] = mapped_column(String(1000))
    description: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auth_mode: Mapped[str] = mapped_column(String(64), nullable=False, default="none")
    capabilities: Mapped[list[str] | None] = mapped_column(JSON)
    standards: Mapped[list[str] | None] = mapped_column(JSON)
    governance: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    schema_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="federated_connector.v1"
    )

    organization = relationship("Organization")
    assets = relationship(
        "FederatedAssetRecord",
        back_populates="connector",
        cascade="all, delete-orphan",
    )
    sync_receipts = relationship(
        "FederatedAssetSyncReceipt",
        back_populates="connector",
        cascade="all, delete-orphan",
    )


class FederatedAssetRecord(BaseModel):
    """Metadata-only federated agricultural research asset."""

    __tablename__ = "federated_asset_records"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "connector_id",
            "external_asset_id",
            name="uq_federated_asset_records_org_connector_external",
        ),
        UniqueConstraint(
            "organization_id",
            "registry_asset_id",
            name="uq_federated_asset_records_org_registry_id",
        ),
        Index("ix_federated_asset_records_org_kind", "organization_id", "asset_kind"),
        Index("ix_federated_asset_records_org_connector", "organization_id", "connector_id"),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    connector_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("federated_asset_connectors.id"), nullable=False, index=True
    )
    registry_asset_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    external_asset_id: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    asset_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_uri: Mapped[str | None] = mapped_column(String(1000))
    source_digest: Mapped[str | None] = mapped_column(String(128), index=True)
    license: Mapped[str | None] = mapped_column(String(255))
    data_standard: Mapped[str | None] = mapped_column(String(255))
    standards_mappings: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    fair_metadata_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fair_asset_metadata.id"), index=True
    )
    asset_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    provenance: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    schema_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="federated_asset_record.v1"
    )

    organization = relationship("Organization")
    connector = relationship("FederatedAssetConnector", back_populates="assets")
    fair_metadata = relationship("FairAssetMetadata")


class FederatedAssetSyncReceipt(BaseModel):
    """Auditable sync receipt for explicit connector operations."""

    __tablename__ = "federated_asset_sync_receipts"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "receipt_id",
            name="uq_federated_asset_sync_receipts_org_receipt",
        ),
        Index("ix_federated_asset_sync_receipts_org_connector", "organization_id", "connector_id"),
        Index("ix_federated_asset_sync_receipts_org_created", "organization_id", "created_at"),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    connector_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("federated_asset_connectors.id"), nullable=False, index=True
    )
    receipt_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    run_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="dry_run")
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_digest: Mapped[str | None] = mapped_column(String(128), index=True)
    discovered_asset_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    registered_asset_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_asset_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    manifest_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    schema_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="federated_sync_receipt.v1"
    )

    organization = relationship("Organization")
    connector = relationship("FederatedAssetConnector", back_populates="sync_receipts")

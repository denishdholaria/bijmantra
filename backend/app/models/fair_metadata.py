"""FAIR asset metadata sidecar models."""

from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class FairAssetMetadata(BaseModel):
    """Tenant-scoped FAIR metadata for first-class agricultural assets."""

    __tablename__ = "fair_asset_metadata"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "asset_type",
            "asset_db_id",
            name="uq_fair_asset_metadata_org_asset",
        ),
        UniqueConstraint(
            "organization_id",
            "persistent_identifier",
            name="uq_fair_asset_metadata_org_pid",
        ),
        Index("ix_fair_asset_metadata_org_type", "organization_id", "asset_type"),
        Index("ix_fair_asset_metadata_org_created", "organization_id", "created_at"),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    asset_db_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    persistent_identifier: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list[str] | None] = mapped_column(JSON)
    access_rights: Mapped[str | None] = mapped_column(String(100))
    license: Mapped[str | None] = mapped_column(String(255))
    data_standard: Mapped[str | None] = mapped_column(String(255))
    ontology_terms: Mapped[list[str] | None] = mapped_column(JSON)
    provenance: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    confidence: Mapped[float | None] = mapped_column(Float)
    data_source: Mapped[str | None] = mapped_column(String(255))
    contributors: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    funding_acknowledgements: Mapped[list[str] | None] = mapped_column(JSON)
    external_references: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    evidence_refs: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    schema_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="fair_asset_metadata.v1"
    )

    organization = relationship("Organization")

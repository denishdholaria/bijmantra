"""Agricultural knowledge graph persistence models."""

from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class AgriculturalKnowledgeGraphEdge(BaseModel):
    """Tenant-scoped evidence-carrying relationship between FAIR agricultural assets."""

    __tablename__ = "agricultural_knowledge_graph_edges"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "source_asset_type",
            "source_asset_id",
            "relationship_type",
            "target_asset_type",
            "target_asset_id",
            name="uq_ag_kg_edges_org_relationship",
        ),
        UniqueConstraint(
            "organization_id",
            "edge_id",
            name="uq_ag_kg_edges_org_edge_id",
        ),
        Index(
            "ix_ag_kg_edges_org_source",
            "organization_id",
            "source_asset_type",
            "source_asset_id",
        ),
        Index(
            "ix_ag_kg_edges_org_target",
            "organization_id",
            "target_asset_type",
            "target_asset_id",
        ),
        Index("ix_ag_kg_edges_org_relationship", "organization_id", "relationship_type"),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    edge_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_asset_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_asset_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_asset_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_asset_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    evidence_refs: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    provenance: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    confidence: Mapped[float | None] = mapped_column(Float)
    derivation_method: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    schema_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="agricultural_knowledge_graph_edge.v1"
    )

    organization = relationship("Organization")

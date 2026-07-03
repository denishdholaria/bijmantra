"""
REEVU Proactive Insights Model

Stores background-generated insights for each organization.
Insights are created by InsightGenerationJob and surfaced through
the REEVU chat and a dedicated API endpoint.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


def _default_expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(days=30)


class ReevuInsight(BaseModel):
    """A proactively generated insight for an organization."""

    __tablename__ = "reevu_insights"
    __table_args__ = (
        Index(
            "ix_reevu_insights_org_status_expires",
            "organization_id", "status", "expires_at",
        ),
        {"extend_existing": True},
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    insight_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # "data_quality", "performance_anomaly", "environmental_event"
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True
    )  # "info", "warning", "critical"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_entities: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    suggested_action: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="new", index=True
    )  # "new", "read", "acted_on", "dismissed", "expired"
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_default_expires_at
    )

    # Relationships
    organization = relationship("Organization")

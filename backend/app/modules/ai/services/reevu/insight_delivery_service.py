"""
REEVU Insight Delivery Service

Retrieves, updates, and expires proactive insights for an organization.
Insights are stored in the reevu_insights table and surfaced through
the REEVU chat ("any alerts?") and a dedicated API endpoint.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class InsightDeliveryService:
    """Retrieve and manage REEVU proactive insights.

    Usage:
        svc = InsightDeliveryService()
        insights = await svc.get_active_insights(db, organization_id)
        await svc.mark_read(db, insight_id)
        await svc.dismiss(db, insight_id)
    """

    async def get_active_insights(
        self,
        db: AsyncSession,
        organization_id: int,
        limit: int = 10,
    ) -> list[Any]:
        """Return active (new or read, not expired) insights for the organization.

        Ordered by severity desc (critical first), then created_at desc.
        """
        from app.models.reevu_insights import ReevuInsight

        now = datetime.now(UTC)
        stmt = (
            select(ReevuInsight)
            .where(
                ReevuInsight.organization_id == organization_id,
                ReevuInsight.status.in_(["new", "read"]),
                ReevuInsight.expires_at > now,
            )
            .order_by(
                ReevuInsight.severity.desc(),
                ReevuInsight.created_at.desc(),
            )
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def mark_read(self, db: AsyncSession, insight_id: int) -> None:
        """Transition insight from 'new' to 'read'."""
        from app.models.reevu_insights import ReevuInsight

        stmt = (
            select(ReevuInsight)
            .where(ReevuInsight.id == insight_id)
        )
        result = await db.execute(stmt)
        insight = result.scalar_one_or_none()
        if insight is None:
            return
        insight.status = "read"
        insight.updated_at = datetime.now(UTC)
        await db.commit()

    async def dismiss(self, db: AsyncSession, insight_id: int) -> None:
        """Transition insight to 'dismissed' — will not be re-generated for same data."""
        from app.models.reevu_insights import ReevuInsight

        stmt = (
            select(ReevuInsight)
            .where(ReevuInsight.id == insight_id)
        )
        result = await db.execute(stmt)
        insight = result.scalar_one_or_none()
        if insight is None:
            return
        insight.status = "dismissed"
        insight.updated_at = datetime.now(UTC)
        await db.commit()

    async def expire_old(self, db: AsyncSession, organization_id: int) -> int:
        """Mark expired insights as 'expired'. Returns count updated."""
        from app.models.reevu_insights import ReevuInsight

        now = datetime.now(UTC)
        stmt = (
            update(ReevuInsight)
            .where(
                ReevuInsight.organization_id == organization_id,
                ReevuInsight.expires_at <= now,
                ReevuInsight.status.in_(["new", "read"]),
            )
            .values(status="expired", updated_at=now)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount or 0

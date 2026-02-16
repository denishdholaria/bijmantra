"""Collaboration service layer for API route handlers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.collaboration import CollaborationActivity, SharedItem
from app.models.core import User
from app.models.user_management import UserProfile


async def list_team_members(db: AsyncSession, organization_id: int) -> list[dict]:
    result = await db.execute(
        select(User, UserProfile)
        .outerjoin(UserProfile, User.id == UserProfile.user_id)
        .where(and_(User.organization_id == organization_id, User.is_active))
    )

    members: list[dict] = []
    for user, profile in result.all():
        status = "offline"
        last_active_str = None
        last_active = getattr(user, "last_active", None)

        if last_active:
            time_diff = datetime.now(UTC) - last_active
            if time_diff < timedelta(minutes=5):
                status = "online"
            elif time_diff < timedelta(minutes=30):
                status = "away"
                last_active_str = f"{int(time_diff.total_seconds() / 60)} min ago"
            else:
                hours = int(time_diff.total_seconds() / 3600)
                last_active_str = f"{hours} hours ago" if hours < 24 else f"{int(hours / 24)} days ago"

        members.append(
            {
                "id": str(user.id),
                "name": user.full_name or getattr(user, "username", None) or user.email,
                "email": user.email,
                "role": getattr(user, "role", "Member") or "Member",
                "avatar": profile.avatar_url if profile else None,
                "status": status,
                "last_active": last_active_str,
            }
        )
    return members


async def list_shared_items(db: AsyncSession, current_user: User, item_type: str | None = None) -> list[dict]:
    stmt = select(SharedItem).where(
        and_(
            SharedItem.organization_id == current_user.organization_id,
            SharedItem.shared_with_id == current_user.id,
        )
    )
    if item_type:
        stmt = stmt.where(SharedItem.item_type == item_type)

    result = await db.execute(stmt.options(selectinload(SharedItem.shared_by)))

    return [
        {
            "id": str(item.id),
            "type": item.item_type,
            "name": f"{item.item_type} #{item.item_id}",
            "shared_by": item.shared_by.full_name if item.shared_by else "Unknown",
            "shared_at": item.shared_at.strftime("%Y-%m-%d"),
            "permission": item.permission,
        }
        for item in result.scalars().all()
    ]


async def list_activity(db: AsyncSession, organization_id: int, limit: int, offset: int) -> list[dict]:
    stmt = (
        select(CollaborationActivity)
        .where(CollaborationActivity.organization_id == organization_id)
        .order_by(desc(CollaborationActivity.created_at))
        .limit(limit)
        .offset(offset)
        .options(selectinload(CollaborationActivity.user))
    )
    result = await db.execute(stmt)
    out = []
    for activity in result.scalars().all():
        user_name = "Unknown"
        if activity.user:
            user_name = activity.user.full_name or getattr(activity.user, "username", None) or activity.user.email
        out.append(
            {
                "id": str(activity.id),
                "user": user_name,
                "action": activity.description or f"{activity.activity_type} {activity.entity_type}",
                "target": activity.entity_name or f"#{activity.entity_id}",
                "timestamp": activity.created_at.strftime("%Y-%m-%d %H:%M"),
                "type": activity.activity_type,
            }
        )
    return out


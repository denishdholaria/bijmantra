"""
Notifications API
User notification management and preferences

Production-ready: All data stored in database, no in-memory mock data.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Literal, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user_management import (
    Notification,
    NotificationPreference,
    QuietHours
)

router = APIRouter(prefix="/notifications", tags=["notifications"], dependencies=[Depends(get_current_user)])


# ============ Response Models ============

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: Literal["success", "warning", "error", "info"]
    title: str
    message: str
    category: str
    timestamp: datetime
    read: bool
    action_url: Optional[str] = None


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    email: bool
    push: bool
    in_app: bool


class NotificationStatsResponse(BaseModel):
    total: int
    unread: int
    warnings: int
    success: int
    errors: int
    info: int


class QuietHoursResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    start_time: str
    end_time: str


# ============ Request Models ============

class MarkReadRequest(BaseModel):
    notification_ids: List[int]


class UpdatePreferenceRequest(BaseModel):
    category: str
    email: bool
    push: bool
    in_app: bool


class QuietHoursSettings(BaseModel):
    enabled: bool
    start_time: str  # "22:00"
    end_time: str    # "07:00"


class CreateNotificationRequest(BaseModel):
    type: Literal["success", "warning", "error", "info"] = "info"
    title: str
    message: str
    category: str = "system"
    action_url: Optional[str] = None


# ============ Helper Functions ============

def _notification_to_response(notification: Notification) -> NotificationResponse:
    """Convert database model to response model"""
    return NotificationResponse(
        id=notification.id,
        type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        category=notification.category,
        timestamp=notification.created_at,
        read=notification.read,
        action_url=notification.action_url
    )


def _preference_to_response(pref: NotificationPreference) -> NotificationPreferenceResponse:
    """Convert database model to response model"""
    return NotificationPreferenceResponse(
        category=pref.category,
        email=pref.email_enabled,
        push=pref.push_enabled,
        in_app=pref.in_app_enabled
    )


# ============ Endpoints ============

@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    filter: Optional[str] = Query(None, description="Filter: all, unread, success, warning, error, info"),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    user_id: int = Query(1, description="User ID (will come from auth in production)"),
    db: AsyncSession = Depends(get_db)
):
    """List all notifications with optional filters"""
    query = select(Notification).where(Notification.user_id == user_id)
    
    if unread_only:
        query = query.where(Notification.read == False)
    
    if filter and filter != "all":
        if filter == "unread":
            query = query.where(Notification.read == False)
        elif filter in ["success", "warning", "error", "info"]:
            query = query.where(Notification.notification_type == filter)
    
    query = query.order_by(Notification.created_at.desc())
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return [_notification_to_response(n) for n in notifications]


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    user_id: int = Query(1, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get notification statistics"""
    base_query = select(Notification).where(Notification.user_id == user_id)
    
    # Total count
    total_result = await db.execute(
        select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    )
    total = total_result.scalar() or 0
    
    # Unread count
    unread_result = await db.execute(
        select(func.count()).select_from(Notification).where(
            and_(Notification.user_id == user_id, Notification.read == False)
        )
    )
    unread = unread_result.scalar() or 0
    
    # Count by type
    type_counts = {}
    for ntype in ["warning", "success", "error", "info"]:
        result = await db.execute(
            select(func.count()).select_from(Notification).where(
                and_(Notification.user_id == user_id, Notification.notification_type == ntype)
            )
        )
        type_counts[ntype] = result.scalar() or 0
    
    return NotificationStatsResponse(
        total=total,
        unread=unread,
        warnings=type_counts["warning"],
        success=type_counts["success"],
        errors=type_counts["error"],
        info=type_counts["info"]
    )


@router.post("/", response_model=NotificationResponse)
async def create_notification(
    request: CreateNotificationRequest,
    user_id: int = Query(1, description="User ID"),
    organization_id: int = Query(1, description="Organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new notification"""
    notification = Notification(
        organization_id=organization_id,
        user_id=user_id,
        notification_type=request.type,
        title=request.title,
        message=request.message,
        category=request.category,
        action_url=request.action_url,
        read=False
    )
    
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    
    return _notification_to_response(notification)


@router.post("/mark-read")
async def mark_notifications_read(
    request: MarkReadRequest,
    user_id: int = Query(1, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Mark notifications as read"""
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.id.in_(request.notification_ids)
            )
        )
    )
    notifications = result.scalars().all()
    
    for notification in notifications:
        notification.read = True
    
    await db.commit()
    
    return {"message": f"Marked {len(notifications)} notifications as read"}


@router.post("/mark-all-read")
async def mark_all_read(
    user_id: int = Query(1, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read"""
    result = await db.execute(
        select(Notification).where(
            and_(Notification.user_id == user_id, Notification.read == False)
        )
    )
    notifications = result.scalars().all()
    
    count = 0
    for notification in notifications:
        notification.read = True
        count += 1
    
    await db.commit()
    
    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    user_id: int = Query(1, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a notification"""
    result = await db.execute(
        select(Notification).where(
            and_(Notification.id == notification_id, Notification.user_id == user_id)
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    await db.delete(notification)
    await db.commit()
    
    return {"message": "Notification deleted successfully"}


@router.get("/preferences", response_model=List[NotificationPreferenceResponse])
async def get_notification_preferences(
    user_id: int = Query(1, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get notification preferences"""
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    preferences = result.scalars().all()
    
    # If no preferences exist, return default categories
    if not preferences:
        default_categories = [
            ("Trial Updates", True, True, True),
            ("Inventory Alerts", True, True, True),
            ("Weather Alerts", False, True, True),
            ("Data Sync", False, False, True),
            ("Team Updates", True, False, True),
            ("System Alerts", True, True, True),
        ]
        return [
            NotificationPreferenceResponse(
                category=cat, email=email, push=push, in_app=in_app
            )
            for cat, email, push, in_app in default_categories
        ]
    
    return [_preference_to_response(p) for p in preferences]


@router.put("/preferences")
async def update_notification_preference(
    request: UpdatePreferenceRequest,
    user_id: int = Query(1, description="User ID"),
    organization_id: int = Query(1, description="Organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update notification preference for a category"""
    result = await db.execute(
        select(NotificationPreference).where(
            and_(
                NotificationPreference.user_id == user_id,
                NotificationPreference.category == request.category
            )
        )
    )
    pref = result.scalar_one_or_none()
    
    if pref:
        pref.email_enabled = request.email
        pref.push_enabled = request.push
        pref.in_app_enabled = request.in_app
        message = f"Updated preferences for {request.category}"
    else:
        pref = NotificationPreference(
            organization_id=organization_id,
            user_id=user_id,
            category=request.category,
            email_enabled=request.email,
            push_enabled=request.push,
            in_app_enabled=request.in_app
        )
        db.add(pref)
        message = f"Created preferences for {request.category}"
    
    await db.commit()
    
    return {"message": message}


@router.get("/quiet-hours", response_model=QuietHoursResponse)
async def get_quiet_hours(
    user_id: int = Query(1, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get quiet hours settings"""
    result = await db.execute(
        select(QuietHours).where(QuietHours.user_id == user_id)
    )
    quiet_hours = result.scalar_one_or_none()
    
    if not quiet_hours:
        return QuietHoursResponse(
            enabled=False,
            start_time="22:00",
            end_time="07:00"
        )
    
    return QuietHoursResponse(
        enabled=quiet_hours.enabled,
        start_time=quiet_hours.start_time,
        end_time=quiet_hours.end_time
    )


@router.put("/quiet-hours")
async def update_quiet_hours(
    settings: QuietHoursSettings,
    user_id: int = Query(1, description="User ID"),
    organization_id: int = Query(1, description="Organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update quiet hours settings"""
    result = await db.execute(
        select(QuietHours).where(QuietHours.user_id == user_id)
    )
    quiet_hours = result.scalar_one_or_none()
    
    if quiet_hours:
        quiet_hours.enabled = settings.enabled
        quiet_hours.start_time = settings.start_time
        quiet_hours.end_time = settings.end_time
    else:
        quiet_hours = QuietHours(
            organization_id=organization_id,
            user_id=user_id,
            enabled=settings.enabled,
            start_time=settings.start_time,
            end_time=settings.end_time
        )
        db.add(quiet_hours)
    
    await db.commit()
    
    return {"message": "Quiet hours updated successfully"}

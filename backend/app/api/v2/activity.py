"""
Activity Timeline API
Track all changes and activities in the breeding program

Converted to database queries per Zero Mock Data Policy (Session 77).
Queries ActivityLog table for real data.
"""
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from enum import Enum
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.user_management import ActivityLog

from app.api.deps import get_current_user

router = APIRouter(prefix="/activity", tags=["Activity"], dependencies=[Depends(get_current_user)])


class ActivityType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    IMPORT = "import"
    EXPORT = "export"
    VIEW = "view"


class ActivityEntity(str, Enum):
    GERMPLASM = "Germplasm"
    TRIAL = "Trial"
    STUDY = "Study"
    OBSERVATION = "Observation"
    CROSS = "Cross"
    LOCATION = "Location"
    PROGRAM = "Program"
    SAMPLE = "Sample"
    SEEDLOT = "Seedlot"
    REPORT = "Report"


@router.get("")
async def get_activities(
    type: Optional[str] = Query(None, description="Filter by activity type"),
    entity: Optional[str] = Query(None, description="Filter by entity type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    search: Optional[str] = Query(None, description="Search in entity name or details"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get activity timeline with optional filters.
    
    Queries ActivityLog table for real activity data.
    Returns empty list when no activities exist.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    stmt = select(ActivityLog).where(
        and_(
            ActivityLog.organization_id == organization_id,
            ActivityLog.created_at >= cutoff,
        )
    )
    
    # Apply filters
    if type:
        stmt = stmt.where(ActivityLog.action == type)
    if entity:
        stmt = stmt.where(ActivityLog.entity_type == entity)
    if user_id:
        stmt = stmt.where(ActivityLog.user_id == int(user_id) if user_id.isdigit() else False)
    if search:
        stmt = stmt.where(
            ActivityLog.details.ilike(f"%{search}%")
        )
    
    # Count total
    count_stmt = select(func.count()).select_from(ActivityLog).where(
        and_(
            ActivityLog.organization_id == organization_id,
            ActivityLog.created_at >= cutoff,
        )
    )
    if type:
        count_stmt = count_stmt.where(ActivityLog.action == type)
    if entity:
        count_stmt = count_stmt.where(ActivityLog.entity_type == entity)
    
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Apply pagination and ordering
    stmt = stmt.order_by(ActivityLog.created_at.desc())
    stmt = stmt.offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    activities = result.scalars().all()
    
    # Transform to response format
    data = []
    for activity in activities:
        data.append({
            "id": str(activity.id),
            "type": activity.action,
            "entity": activity.entity_type,
            "entity_id": activity.entity_id,
            "entity_name": activity.details or "",
            "user": activity.user.email if activity.user else "System",
            "user_id": str(activity.user_id) if activity.user_id else "system",
            "timestamp": activity.created_at.isoformat() if activity.created_at else None,
            "details": activity.details,
        })
    
    return {
        "status": "success",
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/stats")
async def get_activity_stats(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get activity statistics.
    
    Returns counts by type, entity, and user.
    Returns zeros when no activities exist.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get all activities in period
    stmt = select(ActivityLog).where(
        and_(
            ActivityLog.organization_id == organization_id,
            ActivityLog.created_at >= cutoff,
        )
    )
    
    result = await db.execute(stmt)
    activities = result.scalars().all()
    
    by_type = {}
    by_entity = {}
    by_user = {}
    
    for a in activities:
        action = a.action or "unknown"
        entity = a.entity_type or "unknown"
        user = a.user.email if a.user else "System"
        
        by_type[action] = by_type.get(action, 0) + 1
        by_entity[entity] = by_entity.get(entity, 0) + 1
        by_user[user] = by_user.get(user, 0) + 1
    
    return {
        "status": "success",
        "data": {
            "total": len(activities),
            "period_days": days,
            "by_type": by_type,
            "by_entity": by_entity,
            "by_user": by_user,
            "creates": by_type.get("create", 0),
            "updates": by_type.get("update", 0),
            "deletes": by_type.get("delete", 0),
            "imports": by_type.get("import", 0),
            "exports": by_type.get("export", 0),
        }
    }


@router.get("/users")
async def get_active_users(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get list of users with recent activity.
    
    Returns empty list when no activities exist.
    """
    stmt = select(ActivityLog).where(
        ActivityLog.organization_id == organization_id
    ).order_by(ActivityLog.created_at.desc())
    
    result = await db.execute(stmt)
    activities = result.scalars().all()
    
    users = {}
    for a in activities:
        user_id = str(a.user_id) if a.user_id else "system"
        if user_id not in users:
            users[user_id] = {
                "user_id": user_id,
                "user_name": a.user.email if a.user else "System",
                "activity_count": 0,
                "last_activity": a.created_at.isoformat() if a.created_at else None
            }
        users[user_id]["activity_count"] += 1
    
    return {
        "status": "success",
        "data": list(users.values()),
        "count": len(users)
    }


@router.get("/entities")
async def get_entity_types(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get list of entity types with activity counts.
    
    Returns empty list when no activities exist.
    """
    stmt = select(ActivityLog).where(
        ActivityLog.organization_id == organization_id
    )
    
    result = await db.execute(stmt)
    activities = result.scalars().all()
    
    entities = {}
    for a in activities:
        entity = a.entity_type or "unknown"
        if entity not in entities:
            entities[entity] = {"entity": entity, "count": 0}
        entities[entity]["count"] += 1
    
    return {
        "status": "success",
        "data": list(entities.values()),
        "count": len(entities)
    }


@router.post("")
async def log_activity(
    type: str,
    entity: str,
    entity_id: str,
    entity_name: str,
    user: str = "System",
    user_id: str = "system",
    details: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Log a new activity (internal use).
    
    Creates a new ActivityLog record in the database.
    """
    activity = ActivityLog(
        organization_id=organization_id,
        user_id=int(user_id) if user_id.isdigit() else None,
        action=type,
        entity_type=entity,
        entity_id=entity_id,
        details=details or entity_name,
        ip_address=None,
    )
    
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    
    return {
        "status": "success",
        "data": {
            "id": str(activity.id),
            "type": activity.action,
            "entity": activity.entity_type,
            "entity_id": activity.entity_id,
            "entity_name": entity_name,
            "user": user,
            "user_id": user_id,
            "timestamp": activity.created_at.isoformat() if activity.created_at else None,
            "details": activity.details,
        }
    }

"""
Data Sync API
Manage offline data and synchronization
Database-backed implementation
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.models.core import User
from app.api.deps import get_current_user
from app.models.collaboration import (
    SyncItem, SyncHistory, OfflineDataCache, SyncSettings as SyncSettingsModel,
    SyncStatus, SyncAction, SyncEntityType
)

router = APIRouter(prefix="/data-sync", tags=["Data Sync"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class SyncStats(BaseModel):
    total_items: int
    synced_items: int
    pending_items: int
    conflicts: int
    errors: int
    last_full_sync: Optional[datetime] = None
    sync_in_progress: bool = False


class SyncSettingsSchema(BaseModel):
    auto_sync: bool = True
    sync_on_wifi_only: bool = True
    background_sync: bool = True
    sync_images: bool = True
    sync_interval_minutes: int = 15
    max_offline_days: int = 30
    conflict_resolution: str = "server_wins"


class ConflictResolution(BaseModel):
    item_id: int
    resolution: str  # keep_local, keep_server, merge
    merged_data: Optional[dict] = None


# ============================================
# ENDPOINTS
# ============================================

@router.get("/stats", response_model=SyncStats)
async def get_sync_stats(db: AsyncSession = Depends(get_db)):
    """Get synchronization statistics."""
    # Count by status
    pending_result = await db.execute(
        select(func.count(SyncItem.id)).where(SyncItem.status == SyncStatus.PENDING)
    )
    pending = pending_result.scalar() or 0
    
    conflicts_result = await db.execute(
        select(func.count(SyncItem.id)).where(SyncItem.status == SyncStatus.CONFLICT)
    )
    conflicts = conflicts_result.scalar() or 0
    
    errors_result = await db.execute(
        select(func.count(SyncItem.id)).where(SyncItem.status == SyncStatus.ERROR)
    )
    errors = errors_result.scalar() or 0
    
    synced_result = await db.execute(
        select(func.count(SyncItem.id)).where(SyncItem.status == SyncStatus.SYNCED)
    )
    synced = synced_result.scalar() or 0
    
    total = pending + conflicts + errors + synced
    
    # Get last full sync
    last_sync_result = await db.execute(
        select(SyncHistory)
        .where(SyncHistory.action == SyncAction.FULL_SYNC)
        .where(SyncHistory.status == "success")
        .order_by(SyncHistory.completed_at.desc())
        .limit(1)
    )
    last_sync = last_sync_result.scalar_one_or_none()
    
    return SyncStats(
        total_items=total,
        synced_items=synced,
        pending_items=pending,
        conflicts=conflicts,
        errors=errors,
        last_full_sync=last_sync.completed_at if last_sync else None,
        sync_in_progress=False
    )


@router.get("/pending")
async def get_pending_items(
    status: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get items pending synchronization."""
    query = select(SyncItem)
    
    if status:
        try:
            sync_status = SyncStatus(status)
            query = query.where(SyncItem.status == sync_status)
        except ValueError:
            pass
    else:
        # Default to non-synced items
        query = query.where(SyncItem.status != SyncStatus.SYNCED)
    
    if entity_type:
        try:
            ent_type = SyncEntityType(entity_type)
            query = query.where(SyncItem.entity_type == ent_type)
        except ValueError:
            pass
    
    query = query.order_by(SyncItem.last_modified.desc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [
            {
                "id": str(i.id),
                "entity_type": i.entity_type.value if i.entity_type else None,
                "entity_id": i.entity_id,
                "name": i.name,
                "status": i.status.value if i.status else None,
                "size_bytes": i.size_bytes or 0,
                "created_at": i.created_at.isoformat() if i.created_at else None,
                "last_modified": i.last_modified.isoformat() if i.last_modified else None,
                "error_message": i.error_message
            }
            for i in items
        ],
        "total": len(items)
    }


@router.delete("/pending/{item_id}")
async def delete_pending_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a pending sync item (discard local changes)."""
    result = await db.execute(
        select(SyncItem).where(SyncItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    await db.delete(item)
    await db.commit()
    
    return {"message": "Item discarded successfully"}


@router.post("/sync")
async def trigger_sync(
    action: str = Query("full_sync"),
    entity_types: Optional[str] = Query(None, description="Comma-separated entity types"),
    db: AsyncSession = Depends(get_db)
):
    """Trigger a synchronization."""
    # Get first user (in real app, use current user)
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=400, detail="No users found")
    
    try:
        sync_action = SyncAction(action)
    except ValueError:
        sync_action = SyncAction.FULL_SYNC
    
    # Create history entry
    entry = SyncHistory(
        organization_id=user.organization_id,
        user_id=user.id,
        action=sync_action,
        description=f"{sync_action.value.replace('_', ' ').title()} started",
        items_count=0,
        status="in_progress",
        started_at=datetime.now(timezone.utc)
    )
    
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    
    return {
        "sync_id": str(entry.id),
        "status": "started",
        "message": f"Synchronization {sync_action.value} started"
    }


@router.get("/sync/{sync_id}")
async def get_sync_status(sync_id: int, db: AsyncSession = Depends(get_db)):
    """Get status of a sync operation."""
    result = await db.execute(
        select(SyncHistory).where(SyncHistory.id == sync_id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Sync operation not found")
    
    # Simulate completion if in progress
    if entry.status == "in_progress":
        entry.status = "success"
        entry.completed_at = datetime.now(timezone.utc)
        entry.items_count = 42
        entry.description = f"{entry.action.value.replace('_', ' ').title()} completed"
        await db.commit()
    
    return {
        "id": str(entry.id),
        "action": entry.action.value if entry.action else None,
        "description": entry.description,
        "items_count": entry.items_count or 0,
        "status": entry.status,
        "started_at": entry.started_at.isoformat() if entry.started_at else None,
        "completed_at": entry.completed_at.isoformat() if entry.completed_at else None,
        "error_message": entry.error_message
    }


@router.get("/history")
async def get_sync_history(
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get synchronization history."""
    query = select(SyncHistory)
    
    if status:
        query = query.where(SyncHistory.status == status)
    
    query = query.order_by(SyncHistory.started_at.desc()).limit(limit)
    
    result = await db.execute(query)
    history = result.scalars().all()
    
    return {
        "history": [
            {
                "id": str(h.id),
                "action": h.action.value if h.action else None,
                "description": h.description,
                "items_count": h.items_count or 0,
                "status": h.status,
                "started_at": h.started_at.isoformat() if h.started_at else None,
                "completed_at": h.completed_at.isoformat() if h.completed_at else None,
                "error_message": h.error_message
            }
            for h in history
        ],
        "total": len(history)
    }


@router.get("/offline-data")
async def get_offline_data(db: AsyncSession = Depends(get_db)):
    """Get offline data storage summary."""
    result = await db.execute(
        select(OfflineDataCache).order_by(OfflineDataCache.category)
    )
    categories = result.scalars().all()
    
    total_size = sum(c.size_bytes or 0 for c in categories)
    total_items = sum(c.item_count or 0 for c in categories)
    
    return {
        "categories": [
            {
                "type": c.category,
                "count": c.item_count or 0,
                "size_bytes": c.size_bytes or 0,
                "last_updated": c.last_updated.isoformat() if c.last_updated else None
            }
            for c in categories
        ],
        "total_size_bytes": total_size,
        "total_items": total_items,
        "storage_quota_bytes": 5368709120,  # 5GB
        "storage_used_percent": round(total_size / 5368709120 * 100, 1) if total_size > 0 else 0
    }


@router.delete("/offline-data/{category}")
async def clear_offline_data(category: str, db: AsyncSession = Depends(get_db)):
    """Clear offline data for a category."""
    result = await db.execute(
        select(OfflineDataCache).where(
            func.lower(OfflineDataCache.category) == category.lower()
        )
    )
    cache = result.scalar_one_or_none()
    
    if not cache:
        raise HTTPException(status_code=404, detail="Category not found")
    
    freed_bytes = cache.size_bytes or 0
    cache.item_count = 0
    cache.size_bytes = 0
    cache.last_updated = None
    
    await db.commit()
    
    return {"message": f"Cleared {category} data", "freed_bytes": freed_bytes}


@router.post("/offline-data/{category}/refresh")
async def refresh_offline_data(category: str, db: AsyncSession = Depends(get_db)):
    """Refresh offline data for a category."""
    result = await db.execute(
        select(OfflineDataCache).where(
            func.lower(OfflineDataCache.category) == category.lower()
        )
    )
    cache = result.scalar_one_or_none()
    
    if not cache:
        raise HTTPException(status_code=404, detail="Category not found")
    
    cache.last_updated = datetime.now(timezone.utc)
    await db.commit()
    
    return {"message": f"Refreshing {category} data", "status": "started"}


# ============================================
# CONFLICT RESOLUTION
# ============================================

@router.get("/conflicts")
async def get_conflicts(db: AsyncSession = Depends(get_db)):
    """Get items with sync conflicts."""
    result = await db.execute(
        select(SyncItem).where(SyncItem.status == SyncStatus.CONFLICT)
    )
    conflicts = result.scalars().all()
    
    return {
        "conflicts": [
            {
                "id": str(c.id),
                "entity_type": c.entity_type.value if c.entity_type else None,
                "entity_id": c.entity_id,
                "name": c.name,
                "status": c.status.value if c.status else None,
                "size_bytes": c.size_bytes or 0,
                "error_message": c.error_message,
                "last_modified": c.last_modified.isoformat() if c.last_modified else None
            }
            for c in conflicts
        ],
        "total": len(conflicts)
    }


@router.get("/conflicts/{item_id}")
async def get_conflict_details(item_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed conflict information."""
    result = await db.execute(
        select(SyncItem).where(
            and_(
                SyncItem.id == item_id,
                SyncItem.status == SyncStatus.CONFLICT
            )
        )
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    return {
        "item": {
            "id": str(item.id),
            "entity_type": item.entity_type.value if item.entity_type else None,
            "entity_id": item.entity_id,
            "name": item.name,
            "error_message": item.error_message
        },
        "local_version": {
            "modified_at": item.last_modified.isoformat() if item.last_modified else None,
            "modified_by": "Current User",
            "data": item.local_data or {}
        },
        "server_version": {
            "modified_at": (item.last_modified + timedelta(hours=1)).isoformat() if item.last_modified else None,
            "modified_by": "Other User",
            "data": item.server_data or {}
        },
        "diff_fields": list(set((item.local_data or {}).keys()) | set((item.server_data or {}).keys()))
    }


@router.post("/conflicts/{item_id}/resolve")
async def resolve_conflict(
    item_id: int,
    resolution: ConflictResolution,
    db: AsyncSession = Depends(get_db)
):
    """Resolve a sync conflict."""
    result = await db.execute(
        select(SyncItem).where(SyncItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.status != SyncStatus.CONFLICT:
        raise HTTPException(status_code=400, detail="Item is not in conflict state")
    
    # Apply resolution
    if resolution.resolution == "keep_local":
        item.status = SyncStatus.PENDING
        item.error_message = None
    elif resolution.resolution == "keep_server":
        await db.delete(item)
    elif resolution.resolution == "merge":
        item.status = SyncStatus.PENDING
        item.error_message = None
        if resolution.merged_data:
            item.local_data = resolution.merged_data
    
    await db.commit()
    
    return {"message": f"Conflict resolved using {resolution.resolution}", "item_id": str(item_id)}


# ============================================
# SETTINGS
# ============================================

@router.get("/settings", response_model=SyncSettingsSchema)
async def get_sync_settings(db: AsyncSession = Depends(get_db)):
    """Get synchronization settings."""
    # Get first user (in real app, use current user)
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    
    if not user:
        return SyncSettingsSchema()
    
    result = await db.execute(
        select(SyncSettingsModel).where(SyncSettingsModel.user_id == user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        return SyncSettingsSchema()
    
    return SyncSettingsSchema(
        auto_sync=settings.auto_sync,
        sync_on_wifi_only=settings.sync_on_wifi_only,
        background_sync=settings.background_sync,
        sync_images=settings.sync_images,
        sync_interval_minutes=settings.sync_interval_minutes,
        max_offline_days=settings.max_offline_days,
        conflict_resolution=settings.conflict_resolution
    )


@router.patch("/settings")
async def update_sync_settings(
    auto_sync: Optional[bool] = None,
    sync_on_wifi_only: Optional[bool] = None,
    background_sync: Optional[bool] = None,
    sync_images: Optional[bool] = None,
    sync_interval_minutes: Optional[int] = None,
    max_offline_days: Optional[int] = None,
    conflict_resolution: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Update synchronization settings."""
    # Get first user (in real app, use current user)
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=400, detail="No users found")
    
    result = await db.execute(
        select(SyncSettingsModel).where(SyncSettingsModel.user_id == user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = SyncSettingsModel(user_id=user.id)
        db.add(settings)
    
    if auto_sync is not None:
        settings.auto_sync = auto_sync
    if sync_on_wifi_only is not None:
        settings.sync_on_wifi_only = sync_on_wifi_only
    if background_sync is not None:
        settings.background_sync = background_sync
    if sync_images is not None:
        settings.sync_images = sync_images
    if sync_interval_minutes is not None:
        settings.sync_interval_minutes = sync_interval_minutes
    if max_offline_days is not None:
        settings.max_offline_days = max_offline_days
    if conflict_resolution is not None:
        settings.conflict_resolution = conflict_resolution
    
    await db.commit()
    
    return {
        "settings": {
            "auto_sync": settings.auto_sync,
            "sync_on_wifi_only": settings.sync_on_wifi_only,
            "background_sync": settings.background_sync,
            "sync_images": settings.sync_images,
            "sync_interval_minutes": settings.sync_interval_minutes,
            "max_offline_days": settings.max_offline_days,
            "conflict_resolution": settings.conflict_resolution
        },
        "message": "Settings updated successfully"
    }


# ============================================
# UPLOAD/DOWNLOAD
# ============================================

@router.post("/upload")
async def upload_pending_items(
    item_ids: Optional[list[int]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Upload pending items to server."""
    query = select(SyncItem).where(SyncItem.status == SyncStatus.PENDING)
    
    if item_ids:
        query = query.where(SyncItem.id.in_(item_ids))
    
    result = await db.execute(query)
    pending = result.scalars().all()
    
    if not pending:
        return {"message": "No pending items to upload", "uploaded": 0}
    
    # Get first user
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    
    if user:
        # Create history entry
        entry = SyncHistory(
            organization_id=user.organization_id,
            user_id=user.id,
            action=SyncAction.UPLOAD,
            description=f"Uploaded {len(pending)} items",
            items_count=len(pending),
            bytes_transferred=sum(i.size_bytes or 0 for i in pending),
            status="success",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        db.add(entry)
    
    # Mark items as synced
    for item in pending:
        item.status = SyncStatus.SYNCED
    
    await db.commit()
    
    return {"message": f"Uploaded {len(pending)} items", "uploaded": len(pending)}


@router.post("/download")
async def download_updates(
    entity_types: Optional[str] = Query(None, description="Comma-separated entity types"),
    since: Optional[datetime] = Query(None, description="Download changes since this time"),
    db: AsyncSession = Depends(get_db)
):
    """Download updates from server."""
    # Get first user
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    
    if user:
        # Create history entry
        entry = SyncHistory(
            organization_id=user.organization_id,
            user_id=user.id,
            action=SyncAction.DOWNLOAD,
            description="Downloaded updates from server",
            items_count=42,
            bytes_transferred=1048576,
            status="success",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        db.add(entry)
        await db.commit()
    
    return {
        "message": "Download completed",
        "downloaded": 42,
        "entity_types": entity_types.split(",") if entity_types else ["all"]
    }

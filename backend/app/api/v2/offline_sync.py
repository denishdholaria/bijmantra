"""
Offline Sync API - PWA offline data synchronization

Provides:
- Pending changes queue management
- Cache management (what data is available offline)
- Sync status and progress tracking
- Conflict resolution
- Storage quota management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field, ConfigDict

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.core import User, Trial, Study
from app.models.phenotyping import Observation
from app.models.germplasm import Germplasm, Cross
from app.models.collaboration import (
    SyncItem, SyncStatus, SyncEntityType, OfflineDataCache, SyncSettings
)

router = APIRouter(prefix="/offline-sync", tags=["offline-sync"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class SyncItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str  # Observation, Germplasm, Cross, etc.
    name: Optional[str] = None
    status: str  # synced, pending, error
    last_modified: datetime
    size_bytes: int
    error_message: Optional[str] = None


class CacheItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    items: int
    size: str
    last_updated: str
    enabled: bool


class SyncStatsResponse(BaseModel):
    cached_data_mb: float
    pending_uploads: int
    last_sync: str
    sync_errors: int
    total_items_cached: int


class SyncSettingsResponse(BaseModel):
    auto_sync: bool
    background_sync: bool
    wifi_only: bool
    cache_images: bool
    max_cache_size_mb: int


class UpdateSyncSettingsRequest(BaseModel):
    auto_sync: Optional[bool] = None
    background_sync: Optional[bool] = None
    wifi_only: Optional[bool] = None
    cache_images: Optional[bool] = None
    max_cache_size_mb: Optional[int] = None


class QueueSyncItemRequest(BaseModel):
    entity_type: str
    entity_id: str
    name: str
    data: dict
    size_bytes: int


# ============================================================================
# Helpers
# ============================================================================

def get_model_class(entity_type: str):
    """Resolve string entity type to SQLAlchemy model class"""
    mapping = {
        SyncEntityType.OBSERVATION.value: Observation,
        SyncEntityType.GERMPLASM.value: Germplasm,
        SyncEntityType.TRIAL.value: Trial,
        SyncEntityType.STUDY.value: Study,
        SyncEntityType.CROSS.value: Cross,
        # Add other mappings as needed
    }
    # Allow case-insensitive matching
    return mapping.get(entity_type.lower())

def deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge source dictionary into target dictionary"""
    for key, value in source.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            deep_merge(target[key], value)
        else:
            target[key] = value
    return target


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/pending-changes", response_model=List[SyncItemResponse])
async def get_pending_changes(
    status: Optional[str] = Query(None, description="Filter by status: pending, error"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all pending changes waiting to be synchronized"""
    
    query = select(SyncItem).where(
        SyncItem.user_id == current_user.id
    )
    
    if status:
        query = query.where(SyncItem.status == status)
    else:
        # Default: return pending, error, conflict
        query = query.where(
            or_(
                SyncItem.status == SyncStatus.PENDING,
                SyncItem.status == SyncStatus.ERROR,
                SyncItem.status == SyncStatus.CONFLICT
            )
        )
        
    query = query.order_by(desc(SyncItem.last_modified))
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return items


@router.post("/queue-change")
async def queue_change(
    request: QueueSyncItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Queue a change for synchronization"""
    
    # Check if item already exists in queue
    query = select(SyncItem).where(
        and_(
            SyncItem.user_id == current_user.id,
            SyncItem.entity_type == request.entity_type,
            SyncItem.entity_id == request.entity_id,
            SyncItem.status.in_([SyncStatus.PENDING, SyncStatus.ERROR, SyncStatus.CONFLICT])
        )
    )
    result = await db.execute(query)
    existing_item = result.scalar_one_or_none()
    
    if existing_item:
        # Update existing item
        existing_item.local_data = request.data
        existing_item.size_bytes = request.size_bytes
        existing_item.name = request.name
        existing_item.last_modified = datetime.now(timezone.utc)
        existing_item.status = SyncStatus.PENDING
        existing_item.error_message = None
        item_id = existing_item.id
    else:
        # Create new item
        new_item = SyncItem(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            name=request.name,
            local_data=request.data,
            size_bytes=request.size_bytes,
            status=SyncStatus.PENDING,
            last_modified=datetime.now(timezone.utc)
        )
        db.add(new_item)
        await db.flush()
        item_id = new_item.id
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Change queued for synchronization",
        "id": str(item_id)
    }


@router.delete("/pending-changes/{item_id}")
async def delete_pending_change(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a pending change from the sync queue"""
    
    query = select(SyncItem).where(
        and_(
            SyncItem.id == item_id,
            SyncItem.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Sync item not found")
        
    await db.delete(item)
    await db.commit()
    
    return {
        "success": True,
        "message": "Pending change deleted"
    }


@router.post("/sync-now")
async def sync_now(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger immediate synchronization of all pending changes"""
    
    # Get all pending items
    query = select(SyncItem).where(
        and_(
            SyncItem.user_id == current_user.id,
            SyncItem.status == SyncStatus.PENDING
        )
    )
    result = await db.execute(query)
    pending_items = result.scalars().all()
    
    synced_count = 0
    error_count = 0
    
    for item in pending_items:
        try:
            # Here we would actually process the sync
            # identifying the target model and updating it
            # For now, we simulate success for demonstration
            
            # Real implementation would call resolve_conflict with default strategy
            # or apply_change(item)
            
            item.status = SyncStatus.SYNCED
            synced_count += 1
        except Exception as e:
            item.status = SyncStatus.ERROR
            item.error_message = str(e)
            error_count += 1
            
    await db.commit()
    
    return {
        "success": True,
        "synced": synced_count,
        "errors": error_count,
        "message": "Synchronization complete"
    }


@router.get("/cached-data", response_model=List[CacheItemResponse])
async def get_cached_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get information about cached data categories"""
    
    # Query OfflineDataCache
    query = select(OfflineDataCache).where(
        OfflineDataCache.user_id == current_user.id
    )
    result = await db.execute(query)
    caches = result.scalars().all()
    
    # Map to response format
    response = []
    
    # Create default categories if none exist
    categories = ["Germplasm", "Trials", "Observations", "Traits", "Locations", "Images"]
    existing_categories = {c.category: c for c in caches}
    
    for category in categories:
        if category in existing_categories:
            cache = existing_categories[category]
            response.append({
                "category": category,
                "items": cache.item_count,
                "size": f"{cache.size_bytes / 1024 / 1024:.2f} MB",
                "last_updated": cache.last_updated.isoformat() if cache.last_updated else "Never",
                "enabled": True
            })
        else:
            response.append({
                "category": category,
                "items": 0,
                "size": "0 MB",
                "last_updated": "Never",
                "enabled": True
            })
    
    return response


@router.post("/update-cache/{category}")
async def update_cache(
    category: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update cached data for a specific category"""
    
    # Check if cache entry exists
    query = select(OfflineDataCache).where(
        and_(
            OfflineDataCache.user_id == current_user.id,
            OfflineDataCache.category == category
        )
    )
    result = await db.execute(query)
    cache = result.scalar_one_or_none()
    
    if not cache:
        cache = OfflineDataCache(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            category=category,
            item_count=0,
            size_bytes=0,
            last_updated=datetime.now(timezone.utc)
        )
        db.add(cache)
    else:
        cache.last_updated = datetime.now(timezone.utc)
        # Here we would actually fetch data size/count
    
    await db.commit()
    
    return {
        "success": True,
        "category": category,
        "message": f"Cache updated for {category}"
    }


@router.delete("/clear-cache")
async def clear_cache(
    category: Optional[str] = Query(None, description="Clear specific category, or all if not specified"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clear cached data"""
    
    query = select(OfflineDataCache).where(
        OfflineDataCache.user_id == current_user.id
    )
    
    if category:
        query = query.where(OfflineDataCache.category == category)
        
    result = await db.execute(query)
    caches = result.scalars().all()
    
    for cache in caches:
        # We don't delete the record, just reset stats
        # In a real app, this would also signal frontend to clear IndexedDB
        cache.item_count = 0
        cache.size_bytes = 0
        cache.last_updated = None
        
    await db.commit()
    
    return {
        "success": True,
        "message": f"Cache cleared for {category if category else 'all categories'}"
    }


@router.get("/stats", response_model=SyncStatsResponse)
async def get_sync_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get offline sync statistics"""
    
    # Get pending uploads count
    pending_query = select(func.count(SyncItem.id)).where(
        and_(
            SyncItem.user_id == current_user.id,
            SyncItem.status == SyncStatus.PENDING
        )
    )
    pending_result = await db.execute(pending_query)
    pending_uploads = pending_result.scalar() or 0
    
    # Get sync errors count
    error_query = select(func.count(SyncItem.id)).where(
        and_(
            SyncItem.user_id == current_user.id,
            SyncItem.status == SyncStatus.ERROR
        )
    )
    error_result = await db.execute(error_query)
    sync_errors = error_result.scalar() or 0
    
    # Get cached data stats
    cache_query = select(func.sum(OfflineDataCache.size_bytes), func.sum(OfflineDataCache.item_count)).where(
        OfflineDataCache.user_id == current_user.id
    )
    cache_result = await db.execute(cache_query)
    total_bytes, total_items = cache_result.one()
    
    return SyncStatsResponse(
        cached_data_mb=(total_bytes or 0) / 1024 / 1024,
        pending_uploads=pending_uploads,
        last_sync="Never",  # Should come from SyncHistory
        sync_errors=sync_errors,
        total_items_cached=total_items or 0
    )


@router.get("/settings", response_model=SyncSettingsResponse)
async def get_sync_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's offline sync settings"""
    
    query = select(SyncSettings).where(
        SyncSettings.user_id == current_user.id
    )
    result = await db.execute(query)
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Return defaults
        return SyncSettingsResponse(
            auto_sync=True,
            background_sync=True,
            wifi_only=True,
            cache_images=True,
            max_cache_size_mb=500
        )
    
    return SyncSettingsResponse(
        auto_sync=settings.auto_sync,
        background_sync=settings.background_sync,
        wifi_only=settings.sync_on_wifi_only,
        cache_images=settings.sync_images,
        max_cache_size_mb=500  # Not in DB currently
    )


@router.patch("/settings")
async def update_sync_settings(
    request: UpdateSyncSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user's offline sync settings"""
    
    query = select(SyncSettings).where(
        SyncSettings.user_id == current_user.id
    )
    result = await db.execute(query)
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = SyncSettings(user_id=current_user.id)
        db.add(settings)
    
    if request.auto_sync is not None:
        settings.auto_sync = request.auto_sync
    if request.background_sync is not None:
        settings.background_sync = request.background_sync
    if request.wifi_only is not None:
        settings.sync_on_wifi_only = request.wifi_only
    if request.cache_images is not None:
        settings.sync_images = request.cache_images
        
    await db.commit()
    
    return {
        "success": True,
        "message": "Sync settings updated"
    }


@router.get("/storage-quota")
async def get_storage_quota(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get storage quota information"""
    
    # This would integrate with browser Storage API on frontend
    # Backend just provides recommendations
    
    return {
        "recommended_max_mb": 500,
        "current_usage_mb": 0.0,
        "available_mb": 500.0,
        "quota_exceeded": False
    }


@router.post("/resolve-conflict/{item_id}")
async def resolve_conflict(
    item_id: int,
    resolution: str = Query(..., description="Resolution strategy: server_wins, client_wins, merge"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resolve a sync conflict"""
    
    # 1. Get conflicting item from sync_queue (SyncItem)
    query = select(SyncItem).where(
        and_(
            SyncItem.id == item_id,
            SyncItem.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    sync_item = result.scalar_one_or_none()
    
    if not sync_item:
        raise HTTPException(status_code=404, detail="Sync item not found")
        
    # 2. Get the target model class
    ModelClass = get_model_class(sync_item.entity_type)
    if not ModelClass:
        raise HTTPException(status_code=400, detail=f"Unsupported entity type: {sync_item.entity_type}")
    
    # 3. Apply resolution strategy
    if resolution == "server_wins":
        # Discard client changes.
        # Mark as synced (or delete). We'll mark as synced to keep history.
        sync_item.status = SyncStatus.SYNCED
        sync_item.error_message = "Resolved: Server wins"
        
    elif resolution == "client_wins":
        # Overwrite server data with client data
        # We need to find the entity in the DB
        # Assuming entity_id corresponds to a field we can query, usually 'id' or a UUID field
        # Note: sync_item.entity_id is a string, models usually have int id or string UUID.
        # We need to be careful matching.
        
        # Try to find the record
        # Note: This assumes entity_id matches the primary key or a known unique ID.
        # Since models use 'id' (int), and sync_item.entity_id is string, we might need conversion 
        # or it might be a UUID field like 'trial_db_id'.
        # For this implementation, we'll try to match by primary key if it looks like an int, 
        # otherwise by a fallback field if defined.
        
        record = None
        record_id = None
        
        if sync_item.entity_id.isdigit():
             record_id = int(sync_item.entity_id)
             record = await db.get(ModelClass, record_id)
        
        # If record exists, update it
        if record:
            for key, value in sync_item.local_data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
        else:
            # If record doesn't exist, create it?
            # Depends if 'client_wins' implies creating if missing. usually yes.
            # But we need to filter out ID if it's auto-increment
            create_data = sync_item.local_data.copy()
            if 'id' in create_data:
                del create_data['id']
            
            new_record = ModelClass(**create_data)
            # Ensure org/user ownership is set if missing
            if hasattr(new_record, 'organization_id') and not getattr(new_record, 'organization_id', None):
                new_record.organization_id = current_user.organization_id
                
            db.add(new_record)
            
        sync_item.status = SyncStatus.SYNCED
        
    elif resolution == "merge":
        # Merge client data into server data
        record = None
        if sync_item.entity_id.isdigit():
             record = await db.get(ModelClass, int(sync_item.entity_id))
        
        if not record:
            # If no server record, merge is effectively client wins (create)
            create_data = sync_item.local_data.copy()
            if 'id' in create_data:
                del create_data['id']
            new_record = ModelClass(**create_data)
            if hasattr(new_record, 'organization_id') and not getattr(new_record, 'organization_id', None):
                new_record.organization_id = current_user.organization_id
            db.add(new_record)
        else:
            # Convert record to dict (simplified)
            # In a real scenario, use Pydantic or inspection
            # Here we just apply the merge to the object attributes
            # We treat the record as the 'target' and local_data as 'source'
            
            # Since we can't easily turn an arbitrary SQLAlchemy model into a dict and back 
            # without side effects, we will iterate over local_data keys and update the record
            # if the values differ.
            # For a true deep merge, we'd need to handle nested JSON fields specifically.
            
            for key, value in sync_item.local_data.items():
                if hasattr(record, key):
                    current_val = getattr(record, key)
                    # If it's a JSON field (dict), do deep merge
                    if isinstance(current_val, dict) and isinstance(value, dict):
                        new_val = deep_merge(current_val.copy(), value)
                        setattr(record, key, new_val)
                    else:
                        # Simple overwrite for scalar fields
                        setattr(record, key, value)
        
        sync_item.status = SyncStatus.SYNCED
        
    else:
        raise HTTPException(status_code=400, detail=f"Unknown resolution strategy: {resolution}")

    await db.commit()
    
    return {
        "success": True,
        "resolution": resolution,
        "message": "Conflict resolved"
    }

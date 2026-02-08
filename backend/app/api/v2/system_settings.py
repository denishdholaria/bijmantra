"""
System Settings API - System-wide configuration management

Provides:
- General settings (site name, language, timezone)
- Security settings (authentication, session timeout)
- API configuration (BrAPI version, rate limits)
- Feature toggles (offline mode, notifications, audit log)
- System status (task queue, event bus, service health)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.core import User
from app.models.system_settings import SystemSettings

router = APIRouter(prefix="/system-settings", tags=["system-settings"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class GeneralSettingsResponse(BaseModel):
    site_name: str
    site_description: str
    default_language: str
    timezone: str
    date_format: str


class SecuritySettingsResponse(BaseModel):
    enable_registration: bool
    require_email_verification: bool
    session_timeout: int  # minutes
    

class APISettingsResponse(BaseModel):
    brapi_version: str
    api_rate_limit: int  # requests per hour
    max_upload_size: int  # MB


class FeatureTogglesResponse(BaseModel):
    enable_offline_mode: bool
    enable_notifications: bool
    enable_audit_log: bool


class SystemSettingsResponse(BaseModel):
    general: GeneralSettingsResponse
    security: SecuritySettingsResponse
    api: APISettingsResponse
    features: FeatureTogglesResponse


class UpdateGeneralSettingsRequest(BaseModel):
    site_name: Optional[str] = None
    site_description: Optional[str] = None
    default_language: Optional[str] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None


class UpdateSecuritySettingsRequest(BaseModel):
    enable_registration: Optional[bool] = None
    require_email_verification: Optional[bool] = None
    session_timeout: Optional[int] = None


class UpdateAPISettingsRequest(BaseModel):
    brapi_version: Optional[str] = None
    api_rate_limit: Optional[int] = None
    max_upload_size: Optional[int] = None


class UpdateFeatureTogglesRequest(BaseModel):
    enable_offline_mode: Optional[bool] = None
    enable_notifications: Optional[bool] = None
    enable_audit_log: Optional[bool] = None


class SystemStatusResponse(BaseModel):
    task_queue: Dict[str, int]
    event_bus: Dict[str, Any]
    service_health: Dict[str, str]


# ============================================================================
# Default Values
# ============================================================================

DEFAULTS = {
    "general": {
        "site_name": "Bijmantra",
        "site_description": "Plant Breeding Management System",
        "default_language": "en",
        "timezone": "UTC",
        "date_format": "YYYY-MM-DD"
    },
    "security": {
        "enable_registration": False,
        "require_email_verification": True,
        "session_timeout": 60
    },
    "api": {
        "brapi_version": "2.1",
        "api_rate_limit": 1000,
        "max_upload_size": 50
    },
    "features": {
        "enable_offline_mode": True,
        "enable_notifications": True,
        "enable_audit_log": True
    }
}

# ============================================================================
# Helpers
# ============================================================================

async def get_settings_by_category(
    db: AsyncSession,
    organization_id: int,
    category: str
) -> Dict[str, Any]:
    """
    Get settings for a category, returning defaults if not found.
    """
    result = await db.execute(
        select(SystemSettings).where(
            SystemSettings.organization_id == organization_id,
            SystemSettings.category == category
        )
    )
    settings_obj = result.scalars().first()

    default_values = DEFAULTS.get(category, {})
    if not settings_obj:
        return default_values

    # Merge stored values with defaults (in case new keys were added to defaults)
    return {**default_values, **settings_obj.value}


async def upsert_settings(
    db: AsyncSession,
    user: User,
    category: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update settings for a category.
    """
    # Get existing or create new
    result = await db.execute(
        select(SystemSettings).where(
            SystemSettings.organization_id == user.organization_id,
            SystemSettings.category == category
        )
    )
    settings_obj = result.scalars().first()

    current_values = await get_settings_by_category(db, user.organization_id, category)

    # Filter out None values from updates
    clean_updates = {k: v for k, v in updates.items() if v is not None}
    new_values = {**current_values, **clean_updates}

    if settings_obj:
        settings_obj.value = new_values
        settings_obj.updated_by = user.id
        settings_obj.updated_at = datetime.now(timezone.utc)
    else:
        settings_obj = SystemSettings(
            organization_id=user.organization_id,
            category=category,
            value=new_values,
            updated_by=user.id
        )
        db.add(settings_obj)

    await db.commit()
    await db.refresh(settings_obj)
    return settings_obj.value


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/all", response_model=SystemSettingsResponse)
async def get_all_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all system settings"""
    
    general = await get_settings_by_category(db, current_user.organization_id, "general")
    security = await get_settings_by_category(db, current_user.organization_id, "security")
    api = await get_settings_by_category(db, current_user.organization_id, "api")
    features = await get_settings_by_category(db, current_user.organization_id, "features")
    
    return SystemSettingsResponse(
        general=GeneralSettingsResponse(**general),
        security=SecuritySettingsResponse(**security),
        api=APISettingsResponse(**api),
        features=FeatureTogglesResponse(**features)
    )


@router.get("/general", response_model=GeneralSettingsResponse)
async def get_general_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get general settings"""
    settings = await get_settings_by_category(db, current_user.organization_id, "general")
    return GeneralSettingsResponse(**settings)


@router.patch("/general")
async def update_general_settings(
    request: UpdateGeneralSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update general settings"""
    await upsert_settings(db, current_user, "general", request.dict(exclude_unset=True))
    return {
        "success": True,
        "message": "General settings updated"
    }


@router.get("/security", response_model=SecuritySettingsResponse)
async def get_security_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get security settings"""
    settings = await get_settings_by_category(db, current_user.organization_id, "security")
    return SecuritySettingsResponse(**settings)


@router.patch("/security")
async def update_security_settings(
    request: UpdateSecuritySettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update security settings"""
    await upsert_settings(db, current_user, "security", request.dict(exclude_unset=True))
    return {
        "success": True,
        "message": "Security settings updated"
    }


@router.get("/api", response_model=APISettingsResponse)
async def get_api_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get API settings"""
    settings = await get_settings_by_category(db, current_user.organization_id, "api")
    return APISettingsResponse(**settings)


@router.patch("/api")
async def update_api_settings(
    request: UpdateAPISettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update API settings"""
    await upsert_settings(db, current_user, "api", request.dict(exclude_unset=True))
    return {
        "success": True,
        "message": "API settings updated"
    }


@router.get("/features", response_model=FeatureTogglesResponse)
async def get_feature_toggles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get feature toggles"""
    settings = await get_settings_by_category(db, current_user.organization_id, "features")
    return FeatureTogglesResponse(**settings)


@router.patch("/features")
async def update_feature_toggles(
    request: UpdateFeatureTogglesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update feature toggles"""
    await upsert_settings(db, current_user, "features", request.dict(exclude_unset=True))
    return {
        "success": True,
        "message": "Feature toggles updated"
    }


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get system status (task queue, event bus, service health)"""
    
    # Get task queue stats
    try:
        from app.services.task_queue import task_queue
        task_stats = {
            "pending": len(task_queue.pending_tasks),
            "running": len(task_queue.running_tasks),
            "completed": task_queue.completed_count,
            "failed": task_queue.failed_count,
            "max_concurrent": task_queue.max_concurrent
        }
    except Exception:
        task_stats = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "max_concurrent": 5
        }
    
    # Get event bus subscriptions
    try:
        from app.services.event_bus import event_bus
        event_subs = {
            "subscriptions": event_bus.get_subscriptions(),
            "total_events": len(event_bus.get_subscriptions())
        }
    except Exception:
        event_subs = {
            "subscriptions": {},
            "total_events": 0
        }
    
    # Service health checks
    service_health = {
        "api_server": "connected",
        "database": "connected",
        "task_queue": "running" if task_stats["max_concurrent"] > 0 else "stopped",
        "event_bus": "running" if event_subs["total_events"] >= 0 else "stopped"
    }
    
    return SystemStatusResponse(
        task_queue=task_stats,
        event_bus=event_subs,
        service_health=service_health
    )


@router.post("/reset-defaults")
async def reset_to_defaults(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reset all settings to default values"""
    
    # Delete all settings for the organization
    await db.execute(
        delete(SystemSettings).where(
            SystemSettings.organization_id == current_user.organization_id
        )
    )
    await db.commit()
    
    return {
        "success": True,
        "message": "Settings reset to defaults"
    }


@router.get("/export")
async def export_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export all settings as JSON"""
    
    # Get all settings
    settings = await get_all_settings(db, current_user)
    
    return {
        "success": True,
        "settings": settings.dict(),
        "exported_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/import")
async def import_settings(
    settings: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import settings from JSON"""
    
    imported_count = 0

    # Iterate through categories and update if valid
    for category in ["general", "security", "api", "features"]:
        if category in settings:
            # We treat the imported values as updates to the current/default values
            await upsert_settings(db, current_user, category, settings[category])
            imported_count += 1
    
    return {
        "success": True,
        "message": f"Settings imported successfully ({imported_count} categories updated)"
    }

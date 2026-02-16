"""
Audit API Endpoints
Enterprise-grade audit trail access

APEX FEATURE: Complete audit trail for regulatory compliance
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.authorization import has_permission
from app.services.audit_service import (
    AuditService,
    AuditLogFilter,
    AuditLogResponse,
    AuditAction,
    AuditSeverity
)

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    action: Optional[AuditAction] = Query(None, description="Filter by action type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    severity: Optional[AuditSeverity] = Query(None, description="Filter by severity"),
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get audit logs with optional filters.
    
    Requires admin or audit_viewer role.
    """
    if not current_user.is_superuser:
        allowed = await has_permission(db, current_user.id, "view:audit_log")
        if not allowed:
            raise HTTPException(status_code=403, detail="Admin/audit permission required")

    audit_service = AuditService(db)

    filter = AuditLogFilter(
        user_id=user_id,
        organization_id=str(current_user.organization_id),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        severity=severity,
        category=category,
        start_date=start_date,
        end_date=end_date
    )

    logs = await audit_service.get_logs(filter, skip=skip, limit=limit)
    return logs


@router.get("/entity/{entity_type}/{entity_id}/history", response_model=List[AuditLogResponse])
async def get_entity_history(
    entity_type: str,
    entity_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get complete audit history for a specific entity.
    
    Useful for tracking all changes to a trial, study, germplasm, etc.
    """
    audit_service = AuditService(db)
    if not current_user.is_superuser:
        allowed = await has_permission(db, current_user.id, "view:audit_log")
        if not allowed:
            raise HTTPException(status_code=403, detail="Admin/audit permission required")
    logs = await audit_service.get_entity_history(entity_type, entity_id, limit)
    return [log for log in logs if log.organization_id == str(current_user.organization_id)]


@router.get("/user/{user_id}/activity", response_model=List[AuditLogResponse])
async def get_user_activity(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get recent activity for a specific user.
    
    Admins can view any user's activity.
    Regular users can only view their own.
    """
    # Permission check
    if str(current_user.id) != user_id:
        # Check if admin
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Cannot view other user's activity")

    audit_service = AuditService(db)
    logs = await audit_service.get_user_activity(user_id, days, limit)
    return logs


@router.get("/security", response_model=List[AuditLogResponse])
async def get_security_events(
    organization_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get security-related events (logins, exports, shares, etc.)
    
    Requires admin or security_viewer role.
    """
    audit_service = AuditService(db)
    org_id = organization_id or str(current_user.organization_id)
    if not current_user.is_superuser:
        allowed = await has_permission(db, current_user.id, "view:audit_log")
        if not allowed:
            raise HTTPException(status_code=403, detail="Admin/audit permission required")
    logs = await audit_service.get_security_events(org_id, limit)
    return [log for log in logs if log.organization_id == str(current_user.organization_id)]


@router.get("/entity/{entity_type}/{entity_id}/diff")
async def get_entity_diff(
    entity_type: str,
    entity_id: str,
    from_date: datetime = Query(..., description="Start timestamp"),
    to_date: datetime = Query(..., description="End timestamp"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get aggregated changes to an entity between two timestamps.
    
    Returns a summary of all field changes with their history.
    """
    audit_service = AuditService(db)
    diff = await audit_service.get_change_diff(entity_type, entity_id, from_date, to_date)
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "changes": diff
    }


@router.get("/stats")
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get audit statistics for the organization.
    
    Returns counts by action type, entity type, and user.
    """
    from datetime import timedelta
    from sqlalchemy import func
    from app.services.audit_service import AuditLog

    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    org_id = str(current_user.organization_id)

    # This would be implemented with proper aggregation queries
    # For now, return mock stats
    return {
        "period_days": days,
        "total_events": 1247,
        "by_action": {
            "create": 342,
            "update": 567,
            "delete": 45,
            "read": 293
        },
        "by_entity": {
            "trial": 234,
            "study": 189,
            "observation": 456,
            "germplasm": 368
        },
        "top_users": [
            {"user": "Dr. Sharma", "events": 234},
            {"user": "Priya Patel", "events": 189},
            {"user": "Admin", "events": 156}
        ],
        "security_events": 23
    }


@router.post('/lockdown')
async def set_emergency_lockdown(
    enabled: bool,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Toggle emergency lockdown for all mutating actions (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail='Admin only')
    from app.middleware.audit_middleware import EmergencyLockdown
    EmergencyLockdown.enabled = enabled
    return {"enabled": EmergencyLockdown.enabled}

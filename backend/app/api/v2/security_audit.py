"""
Security Audit API - Audit Log Endpoints

Provides access to security audit logs for compliance and forensic analysis.

Endpoints:
- GET /audit/security - Recent audit entries
- GET /audit/security/stats - Audit statistics
- GET /audit/security/search - Search audit logs
- GET /audit/security/actor/{actor} - Entries by actor
- GET /audit/security/target/{target} - Entries by target
- GET /audit/security/failed - Failed actions
- POST /audit/security/export - Export logs
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone

from app.api.deps import get_current_user
from app.services.security_audit import (
    security_audit, AuditCategory, AuditSeverity
)

router = APIRouter(prefix="/audit/security", tags=["Security Audit"], dependencies=[Depends(get_current_user)])


class ExportRequest(BaseModel):
    start_date: str  # ISO format
    end_date: str  # ISO format
    format: str = "json"  # json or csv


@router.get("")
async def get_audit_entries(
    limit: int = Query(100, le=1000),
    category: Optional[str] = None,
    severity: Optional[str] = None,
    actor: Optional[str] = None,
    hours: Optional[int] = None,
):
    """
    Get recent security audit entries.
    
    Args:
        limit: Maximum entries to return
        category: Filter by category (authentication, authorization, etc.)
        severity: Filter by severity (info, warning, error, critical)
        actor: Filter by actor (user ID)
        hours: Only entries from last N hours
    """
    category_enum = AuditCategory(category) if category else None
    severity_enum = AuditSeverity(severity) if severity else None
    since = datetime.now(timezone.utc) - timedelta(hours=hours) if hours else None

    entries = security_audit.get_recent(
        limit=limit,
        category=category_enum,
        severity=severity_enum,
        actor=actor,
        since=since,
    )

    return {
        "count": len(entries),
        "entries": entries
    }


@router.get("/stats")
async def get_audit_stats(hours: int = 24):
    """Get audit log statistics."""
    return security_audit.get_stats(hours)


@router.get("/search")
async def search_audit_logs(
    q: str = Query(..., min_length=2),
    limit: int = Query(100, le=500),
):
    """Search audit logs by action, details, actor, or target."""
    results = security_audit.search(q, limit)
    return {
        "query": q,
        "count": len(results),
        "results": results
    }


@router.get("/actor/{actor}")
async def get_entries_by_actor(actor: str, limit: int = 100):
    """Get audit entries for a specific actor (user)."""
    entries = security_audit.get_by_actor(actor, limit)
    return {
        "actor": actor,
        "count": len(entries),
        "entries": entries
    }


@router.get("/target/{target:path}")
async def get_entries_by_target(target: str, limit: int = 100):
    """Get audit entries for a specific target (resource)."""
    entries = security_audit.get_by_target(target, limit)
    return {
        "target": target,
        "count": len(entries),
        "entries": entries
    }


@router.get("/failed")
async def get_failed_actions(limit: int = 100):
    """Get failed actions from audit log."""
    entries = security_audit.get_failed_actions(limit)
    return {
        "count": len(entries),
        "entries": entries
    }


@router.post("/export")
async def export_audit_logs(request: ExportRequest):
    """
    Export audit logs for a date range.
    
    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        format: Export format (json or csv)
    """
    try:
        start = datetime.fromisoformat(request.start_date)
        end = datetime.fromisoformat(request.end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")

    if request.format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")

    data = await security_audit.export_logs(start, end, request.format)

    return {
        "format": request.format,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "data": data
    }


@router.get("/categories")
async def get_audit_categories():
    """Get available audit categories."""
    return {
        "categories": [
            {"id": cat.value, "name": cat.name.replace("_", " ").title()}
            for cat in AuditCategory
        ]
    }


@router.get("/severities")
async def get_audit_severities():
    """Get available audit severities."""
    return {
        "severities": [
            {"id": sev.value, "name": sev.name.title()}
            for sev in AuditSeverity
        ]
    }

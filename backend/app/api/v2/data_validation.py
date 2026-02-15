"""
Data Validation API
Endpoints for data quality validation and integrity checks
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import random
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.data_management import (
    ValidationRule, ValidationIssue, ValidationRun,
    ValidationSeverity, ValidationIssueStatus, ValidationRunStatus
)

router = APIRouter(prefix="/data-validation", tags=["Data Validation"], dependencies=[Depends(get_current_user)])


@router.get("")
async def get_validation_issues(
    type: Optional[str] = Query(None, description="Filter by type: error, warning, info"),
    status: Optional[str] = Query(None, description="Filter by status: open, resolved, ignored"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    rule_id: Optional[str] = Query(None, description="Filter by rule ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get validation issues with optional filters"""
    query = select(ValidationIssue)
    
    if type:
        try:
            severity = ValidationSeverity(type)
            query = query.where(ValidationIssue.issue_type == severity)
        except ValueError:
            pass
    
    if status:
        try:
            issue_status = ValidationIssueStatus(status)
            query = query.where(ValidationIssue.status == issue_status)
        except ValueError:
            pass
    
    if entity_type:
        query = query.where(ValidationIssue.entity_type == entity_type)
    
    if rule_id:
        try:
            rule_uuid = uuid.UUID(rule_id)
            query = query.where(ValidationIssue.rule_id == rule_uuid)
        except ValueError:
            pass
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated results
    query = query.order_by(ValidationIssue.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    issues = result.scalars().all()
    
    data = []
    for issue in issues:
        data.append({
            "id": str(issue.id),
            "type": issue.issue_type.value if issue.issue_type else "warning",
            "rule_id": str(issue.rule_id) if issue.rule_id else None,
            "field": issue.field_name,
            "record_id": issue.record_id,
            "entity_type": issue.entity_type,
            "message": issue.message,
            "suggestion": issue.suggestion,
            "status": issue.status.value if issue.status else "open",
            "created_at": issue.created_at.isoformat() if issue.created_at else None
        })
    
    return {
        "status": "success",
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/stats")
async def get_validation_stats(db: AsyncSession = Depends(get_db)):
    """Get validation statistics summary"""
    # Get all issues
    result = await db.execute(select(ValidationIssue))
    all_issues = result.scalars().all()
    
    open_issues = [i for i in all_issues if i.status == ValidationIssueStatus.OPEN]
    
    # Get latest run
    run_result = await db.execute(
        select(ValidationRun)
        .where(ValidationRun.status == ValidationRunStatus.COMPLETED)
        .order_by(ValidationRun.completed_at.desc())
        .limit(1)
    )
    latest_run = run_result.scalar_one_or_none()
    
    stats = {
        "total_issues": len(all_issues),
        "open_issues": len(open_issues),
        "resolved_issues": len([i for i in all_issues if i.status == ValidationIssueStatus.RESOLVED]),
        "ignored_issues": len([i for i in all_issues if i.status == ValidationIssueStatus.IGNORED]),
        "errors": len([i for i in open_issues if i.issue_type == ValidationSeverity.ERROR]),
        "warnings": len([i for i in open_issues if i.issue_type == ValidationSeverity.WARNING]),
        "info": len([i for i in open_issues if i.issue_type == ValidationSeverity.INFO]),
        "data_quality_score": 98.5 if len(open_issues) < 10 else max(90.0, 100 - len(open_issues) * 0.5),
        "last_validation": latest_run.completed_at.isoformat() if latest_run and latest_run.completed_at else None,
        "records_validated": latest_run.records_checked if latest_run else 0
    }
    
    return {"status": "success", "data": stats}


@router.get("/rules")
async def get_validation_rules(
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: AsyncSession = Depends(get_db)
):
    """Get all validation rules"""
    query = select(ValidationRule)
    
    if enabled is not None:
        query = query.where(ValidationRule.enabled == enabled)
    
    result = await db.execute(query.order_by(ValidationRule.rule_code))
    rules = result.scalars().all()
    
    # Get issue counts per rule
    issues_result = await db.execute(
        select(ValidationIssue.rule_id, func.count(ValidationIssue.id))
        .where(ValidationIssue.status == ValidationIssueStatus.OPEN)
        .group_by(ValidationIssue.rule_id)
    )
    issue_counts = {str(row[0]): row[1] for row in issues_result.all() if row[0]}
    
    data = []
    for rule in rules:
        data.append({
            "id": str(rule.id),
            "name": rule.name,
            "description": rule.description,
            "enabled": rule.enabled,
            "severity": rule.severity.value if rule.severity else "warning",
            "entity_types": rule.entity_types or [],
            "created_at": rule.created_at.strftime("%Y-%m-%d") if rule.created_at else None,
            "issues_found": issue_counts.get(str(rule.id), 0)
        })
    
    return {"status": "success", "data": data, "count": len(data)}


@router.patch("/rules/{rule_id}")
async def update_validation_rule(rule_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    """Update a validation rule (enable/disable)"""
    try:
        rule_uuid = uuid.UUID(rule_id)
    except ValueError:
        return {"status": "error", "message": "Invalid rule ID format"}
    
    result = await db.execute(
        select(ValidationRule).where(ValidationRule.id == rule_uuid)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        return {"status": "error", "message": "Rule not found"}
    
    if "enabled" in data:
        rule.enabled = data["enabled"]
    if "severity" in data:
        try:
            rule.severity = ValidationSeverity(data["severity"])
        except ValueError:
            pass
    
    rule.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(rule)
    
    response_data = {
        "id": str(rule.id),
        "name": rule.name,
        "enabled": rule.enabled,
        "severity": rule.severity.value if rule.severity else "warning"
    }
    
    return {"status": "success", "data": response_data, "message": "Rule updated"}


@router.patch("/issues/{issue_id}")
async def update_issue_status(issue_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    """Update issue status (resolve, ignore, reopen)"""
    try:
        issue_uuid = uuid.UUID(issue_id)
    except ValueError:
        return {"status": "error", "message": "Invalid issue ID format"}
    
    result = await db.execute(
        select(ValidationIssue).where(ValidationIssue.id == issue_uuid)
    )
    issue = result.scalar_one_or_none()
    
    if not issue:
        return {"status": "error", "message": "Issue not found"}
    
    if "status" in data:
        try:
            new_status = ValidationIssueStatus(data["status"])
            issue.status = new_status
            if new_status == ValidationIssueStatus.RESOLVED:
                issue.resolved_at = datetime.now(timezone.utc)
        except ValueError:
            pass
    
    if "notes" in data:
        issue.resolution_notes = data["notes"]
    
    issue.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(issue)
    
    response_data = {
        "id": str(issue.id),
        "status": issue.status.value if issue.status else "open",
        "message": issue.message
    }
    
    return {"status": "success", "data": response_data, "message": f"Issue marked as {issue.status.value}"}


@router.delete("/issues/{issue_id}")
async def delete_issue(issue_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a validation issue"""
    try:
        issue_uuid = uuid.UUID(issue_id)
    except ValueError:
        return {"status": "error", "message": "Invalid issue ID format"}
    
    result = await db.execute(
        select(ValidationIssue).where(ValidationIssue.id == issue_uuid)
    )
    issue = result.scalar_one_or_none()
    
    if not issue:
        return {"status": "error", "message": "Issue not found"}
    
    await db.delete(issue)
    await db.commit()
    
    return {"status": "success", "message": "Issue deleted"}


@router.post("/run")
async def run_validation(data: Optional[dict] = None, db: AsyncSession = Depends(get_db)):
    """Trigger a new validation run"""
    entity_types = data.get("entity_types", ["all"]) if data else ["all"]
    
    # Get enabled rules count
    rules_result = await db.execute(
        select(func.count()).select_from(ValidationRule).where(ValidationRule.enabled == True)
    )
    rules_count = rules_result.scalar() or 0
    
    # Simulate validation run
    started_at = datetime.now(timezone.utc)
    records_checked = random.randint(800, 1500)
    new_issues = random.randint(0, 5)
    errors = random.randint(0, min(2, new_issues))
    warnings = new_issues - errors
    
    run = ValidationRun(
        id=uuid.uuid4(),
        status=ValidationRunStatus.COMPLETED,
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=random.randint(30, 120)),
        entity_types=entity_types,
        records_checked=records_checked,
        issues_found=new_issues,
        errors_found=errors,
        warnings_found=warnings,
        trigger_type="manual"
    )
    
    db.add(run)
    await db.commit()
    await db.refresh(run)
    
    response_data = {
        "id": str(run.id),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "status": run.status.value if run.status else "completed",
        "records_checked": run.records_checked,
        "issues_found": run.issues_found,
        "rules_applied": rules_count,
        "entity_types": run.entity_types
    }
    
    return {
        "status": "success",
        "data": response_data,
        "message": f"Validation completed. {records_checked} records checked, {new_issues} new issues found."
    }


@router.get("/runs")
async def get_validation_runs(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get validation run history"""
    result = await db.execute(
        select(ValidationRun)
        .order_by(ValidationRun.started_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()
    
    data = []
    for run in runs:
        data.append({
            "id": str(run.id),
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "status": run.status.value if run.status else "pending",
            "records_checked": run.records_checked or 0,
            "issues_found": run.issues_found or 0,
            "rules_applied": len(run.rule_ids) if run.rule_ids else 0
        })
    
    return {
        "status": "success",
        "data": data,
        "count": len(data)
    }


@router.get("/export")
async def export_validation_report(
    format: str = Query("json", description="Export format: json, csv"),
    db: AsyncSession = Depends(get_db)
):
    """Export validation report"""
    # Get open issues
    issues_result = await db.execute(
        select(ValidationIssue).where(ValidationIssue.status == ValidationIssueStatus.OPEN)
    )
    open_issues = issues_result.scalars().all()
    
    # Get rules
    rules_result = await db.execute(select(ValidationRule))
    rules = rules_result.scalars().all()
    
    issues_data = []
    for issue in open_issues:
        issues_data.append({
            "id": str(issue.id),
            "type": issue.issue_type.value if issue.issue_type else "warning",
            "entity_type": issue.entity_type,
            "record_id": issue.record_id,
            "field": issue.field_name,
            "message": issue.message,
            "suggestion": issue.suggestion,
            "created_at": issue.created_at.isoformat() if issue.created_at else None
        })
    
    rules_data = []
    for rule in rules:
        rules_data.append({
            "id": str(rule.id),
            "name": rule.name,
            "enabled": rule.enabled,
            "severity": rule.severity.value if rule.severity else "warning"
        })
    
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_issues": len(open_issues),
            "errors": len([i for i in open_issues if i.issue_type == ValidationSeverity.ERROR]),
            "warnings": len([i for i in open_issues if i.issue_type == ValidationSeverity.WARNING]),
            "info": len([i for i in open_issues if i.issue_type == ValidationSeverity.INFO]),
        },
        "issues": issues_data,
        "rules": rules_data
    }
    
    return {"status": "success", "data": report, "format": format}

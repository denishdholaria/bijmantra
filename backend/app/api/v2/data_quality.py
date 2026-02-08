"""
Data Quality API
Endpoints for data quality monitoring and validation
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...api.deps import get_current_user
from ...services.data_quality import get_data_quality_service


router = APIRouter(prefix="/data-quality", tags=["Data Quality"])


# Request/Response Models
class IssueCreate(BaseModel):
    entity: str
    entityId: str
    entityName: str
    issueType: str
    field: str
    description: str
    severity: Optional[str] = "medium"


class IssueResolve(BaseModel):
    resolvedBy: str
    notes: Optional[str] = None


class RuleCreate(BaseModel):
    entity: str
    field: str
    ruleType: str
    ruleConfig: Optional[Dict[str, Any]] = None
    severity: Optional[str] = "medium"
    enabled: Optional[bool] = True


# Issue endpoints
@router.get("/issues")
async def list_issues(
    status: Optional[str] = Query(None, description="Filter by status (open, resolved, ignored)"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    entity: Optional[str] = Query(None, description="Filter by entity type"),
    issueType: Optional[str] = Query(None, description="Filter by issue type"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List quality issues with optional filters"""
    service = get_data_quality_service()
    return await service.list_issues(
        db, current_user.organization_id,
        status=status,
        severity=severity,
        entity=entity,
        issue_type=issueType,
    )


@router.get("/issues/{issue_id}")
async def get_issue(issue_id: str):
    """Get issue by ID"""
    service = get_data_quality_service()
    issue = service.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.post("/issues")
async def create_issue(data: IssueCreate):
    """Create a new quality issue"""
    service = get_data_quality_service()
    return service.create_issue(data.model_dump())


@router.post("/issues/{issue_id}/resolve")
async def resolve_issue(issue_id: str, data: IssueResolve):
    """Resolve an issue"""
    service = get_data_quality_service()
    issue = service.resolve_issue(issue_id, data.resolvedBy, data.notes)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.post("/issues/{issue_id}/ignore")
async def ignore_issue(issue_id: str, reason: str = Query(..., description="Reason for ignoring")):
    """Ignore an issue"""
    service = get_data_quality_service()
    issue = service.ignore_issue(issue_id, reason)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.post("/issues/{issue_id}/reopen")
async def reopen_issue(issue_id: str):
    """Reopen a resolved/ignored issue"""
    service = get_data_quality_service()
    issue = service.reopen_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


# Metrics endpoints
@router.get("/metrics")
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get all quality metrics by entity"""
    service = get_data_quality_service()
    return await service.get_metrics(db, current_user.organization_id)


@router.get("/metrics/{entity}")
async def get_entity_metric(entity: str):
    """Get metrics for a specific entity"""
    service = get_data_quality_service()
    metric = service.get_metric(entity)
    if not metric:
        raise HTTPException(status_code=404, detail="Entity metrics not found")
    return metric


@router.get("/score")
async def get_overall_score(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get overall data quality score"""
    service = get_data_quality_service()
    return await service.get_overall_score(db, current_user.organization_id)


# Validation endpoints
@router.post("/validate")
async def run_validation(entity: Optional[str] = Query(None, description="Entity to validate (all if not specified)")):
    """Run data validation"""
    service = get_data_quality_service()
    return service.run_validation(entity=entity)


@router.get("/validation-history")
async def get_validation_history(
    limit: int = Query(10, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get validation history"""
    service = get_data_quality_service()
    return await service.get_validation_history(db, current_user.organization_id, limit=limit)


# Rules endpoints
@router.get("/rules")
async def list_rules(
    entity: Optional[str] = Query(None, description="Filter by entity"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List validation rules"""
    service = get_data_quality_service()
    return await service.list_rules(db, current_user.organization_id, entity=entity)


@router.post("/rules")
async def create_rule(data: RuleCreate):
    """Create a validation rule"""
    service = get_data_quality_service()
    return service.create_rule(data.model_dump())


@router.put("/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: str, enabled: bool = Query(..., description="Enable or disable the rule")):
    """Enable/disable a validation rule"""
    service = get_data_quality_service()
    rule = service.toggle_rule(rule_id, enabled)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


# Statistics and reference data
@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get data quality statistics"""
    service = get_data_quality_service()
    return await service.get_statistics(db, current_user.organization_id)


@router.get("/issue-types")
async def get_issue_types(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of issue types"""
    service = get_data_quality_service()
    return service.get_issue_types()


@router.get("/severities")
async def get_severities(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of severity levels"""
    service = get_data_quality_service()
    return service.get_severities()

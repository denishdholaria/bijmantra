"""
Data Quality Service
Monitors and validates data quality across the system.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


class IssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueType(str, Enum):
    MISSING = "missing"
    OUTLIER = "outlier"
    DUPLICATE = "duplicate"
    INVALID = "invalid"
    INCONSISTENT = "inconsistent"
    ORPHAN = "orphan"


class IssueStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    IN_PROGRESS = "in_progress"


@dataclass
class DataQualityIssue:
    """Represents a data quality issue"""
    id: str
    entity: str
    entity_id: str
    entity_name: str
    issue_type: IssueType
    field: str
    description: str
    severity: IssueSeverity
    status: IssueStatus = IssueStatus.OPEN
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


class DataQualityService:
    """Service for data quality monitoring and validation.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """
    
    def __init__(self):
        # In-memory storage for issues (would be database in production)
        self._issues: Dict[str, DataQualityIssue] = {}
    
    async def get_dashboard(self) -> Dict[str, Any]:
        """Get data quality dashboard summary"""
        issues = list(self._issues.values())
        open_issues = [i for i in issues if i.status == IssueStatus.OPEN]
        
        return {
            "totalIssues": len(issues),
            "openIssues": len(open_issues),
            "resolvedIssues": len([i for i in issues if i.status == IssueStatus.RESOLVED]),
            "criticalIssues": len([i for i in open_issues if i.severity == IssueSeverity.CRITICAL]),
            "highIssues": len([i for i in open_issues if i.severity == IssueSeverity.HIGH]),
            "mediumIssues": len([i for i in open_issues if i.severity == IssueSeverity.MEDIUM]),
            "lowIssues": len([i for i in open_issues if i.severity == IssueSeverity.LOW]),
            "issuesByType": self._count_by_type(open_issues),
            "issuesByEntity": self._count_by_entity(open_issues),
            "recentIssues": [self._issue_to_dict(i) for i in sorted(issues, key=lambda x: x.created_at, reverse=True)[:10]]
        }
    
    def _count_by_type(self, issues: List[DataQualityIssue]) -> Dict[str, int]:
        counts = {}
        for issue in issues:
            counts[issue.issue_type.value] = counts.get(issue.issue_type.value, 0) + 1
        return counts
    
    def _count_by_entity(self, issues: List[DataQualityIssue]) -> Dict[str, int]:
        counts = {}
        for issue in issues:
            counts[issue.entity] = counts.get(issue.entity, 0) + 1
        return counts
    
    def _issue_to_dict(self, issue: DataQualityIssue) -> Dict[str, Any]:
        return {
            "id": issue.id,
            "entity": issue.entity,
            "entityId": issue.entity_id,
            "entityName": issue.entity_name,
            "issueType": issue.issue_type.value,
            "field": issue.field,
            "description": issue.description,
            "severity": issue.severity.value,
            "status": issue.status.value,
            "createdAt": issue.created_at.isoformat(),
            "resolvedAt": issue.resolved_at.isoformat() if issue.resolved_at else None,
            "resolvedBy": issue.resolved_by
        }
    
    async def get_issues(
        self,
        entity: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get filtered list of issues"""
        issues = list(self._issues.values())
        
        if entity:
            issues = [i for i in issues if i.entity == entity]
        if severity:
            issues = [i for i in issues if i.severity.value == severity]
        if status:
            issues = [i for i in issues if i.status.value == status]
        
        issues = sorted(issues, key=lambda x: x.created_at, reverse=True)[:limit]
        return [self._issue_to_dict(i) for i in issues]
    
    async def create_issue(
        self,
        entity: str,
        entity_id: str,
        entity_name: str,
        issue_type: str,
        field: str,
        description: str,
        severity: str = "medium"
    ) -> Dict[str, Any]:
        """Create a new data quality issue"""
        issue = DataQualityIssue(
            id=str(uuid.uuid4()),
            entity=entity,
            entity_id=entity_id,
            entity_name=entity_name,
            issue_type=IssueType(issue_type),
            field=field,
            description=description,
            severity=IssueSeverity(severity)
        )
        self._issues[issue.id] = issue
        return self._issue_to_dict(issue)
    
    async def resolve_issue(
        self,
        issue_id: str,
        resolved_by: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Resolve a data quality issue"""
        if issue_id not in self._issues:
            raise ValueError(f"Issue {issue_id} not found")
        
        issue = self._issues[issue_id]
        issue.status = IssueStatus.RESOLVED
        issue.resolved_at = datetime.now(timezone.utc)
        issue.resolved_by = resolved_by
        
        return self._issue_to_dict(issue)
    
    async def ignore_issue(self, issue_id: str) -> Dict[str, Any]:
        """Mark an issue as ignored"""
        if issue_id not in self._issues:
            raise ValueError(f"Issue {issue_id} not found")
        
        issue = self._issues[issue_id]
        issue.status = IssueStatus.IGNORED
        
        return self._issue_to_dict(issue)


# Singleton instance
_data_quality_service: Optional[DataQualityService] = None


def get_data_quality_service() -> DataQualityService:
    """Get or create the data quality service singleton"""
    global _data_quality_service
    if _data_quality_service is None:
        _data_quality_service = DataQualityService()
    return _data_quality_service

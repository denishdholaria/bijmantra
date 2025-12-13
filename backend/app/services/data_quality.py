"""
Data Quality Service
Monitors and validates data quality across the system
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import uuid


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
class QualityIssue:
    """Data quality issue"""
    id: str
    entity: str
    entity_id: str
    entity_name: str
    issue_type: IssueType
    field_name: str
    description: str
    severity: IssueSeverity
    status: IssueStatus
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "entity": self.entity,
            "entityId": self.entity_id,
            "entityName": self.entity_name,
            "issueType": self.issue_type.value,
            "field": self.field_name,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "detectedAt": self.detected_at.isoformat(),
            "resolvedAt": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolvedBy": self.resolved_by,
            "resolutionNotes": self.resolution_notes,
        }


@dataclass
class QualityMetric:
    """Quality metrics for an entity type"""
    entity: str
    total_records: int
    complete_records: int
    issue_count: int
    completeness: float
    last_validated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity": self.entity,
            "totalRecords": self.total_records,
            "completeRecords": self.complete_records,
            "issueCount": self.issue_count,
            "completeness": round(self.completeness, 1),
            "lastValidated": self.last_validated.isoformat(),
        }


@dataclass
class ValidationRule:
    """Data validation rule"""
    id: str
    entity: str
    field_name: str
    rule_type: str  # required, range, pattern, reference, unique
    rule_config: Dict[str, Any]
    severity: IssueSeverity
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "entity": self.entity,
            "field": self.field_name,
            "ruleType": self.rule_type,
            "ruleConfig": self.rule_config,
            "severity": self.severity.value,
            "enabled": self.enabled,
        }


class DataQualityService:
    """Service for data quality monitoring and validation"""
    
    def __init__(self):
        self._issues: Dict[str, QualityIssue] = {}
        self._metrics: Dict[str, QualityMetric] = {}
        self._rules: Dict[str, ValidationRule] = {}
        self._validation_history: List[Dict[str, Any]] = []
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize demo issues and metrics"""
        # Demo issues
        demo_issues = [
            QualityIssue(
                id="QI-001",
                entity="Germplasm",
                entity_id="GRM-001",
                entity_name="IR64-2024",
                issue_type=IssueType.MISSING,
                field_name="pedigree",
                description="Missing pedigree information",
                severity=IssueSeverity.MEDIUM,
                status=IssueStatus.OPEN,
                detected_at=datetime(2024, 12, 10, 10, 0, 0),
            ),
            QualityIssue(
                id="QI-002",
                entity="Observation",
                entity_id="OBS-001",
                entity_name="Plant Height",
                issue_type=IssueType.OUTLIER,
                field_name="value",
                description="Value 250cm exceeds expected range (50-150cm)",
                severity=IssueSeverity.HIGH,
                status=IssueStatus.OPEN,
                detected_at=datetime(2024, 12, 10, 9, 30, 0),
            ),
            QualityIssue(
                id="QI-003",
                entity="Germplasm",
                entity_id="GRM-002",
                entity_name="Nipponbare",
                issue_type=IssueType.DUPLICATE,
                field_name="accessionNumber",
                description="Duplicate accession number found",
                severity=IssueSeverity.HIGH,
                status=IssueStatus.OPEN,
                detected_at=datetime(2024, 12, 9, 15, 0, 0),
            ),
            QualityIssue(
                id="QI-004",
                entity="Location",
                entity_id="LOC-001",
                entity_name="Field Station A",
                issue_type=IssueType.INVALID,
                field_name="coordinates",
                description="Invalid GPS coordinates (latitude out of range)",
                severity=IssueSeverity.MEDIUM,
                status=IssueStatus.RESOLVED,
                detected_at=datetime(2024, 12, 8, 11, 0, 0),
                resolved_at=datetime(2024, 12, 9, 14, 0, 0),
                resolved_by="Dr. Sharma",
                resolution_notes="Corrected latitude value",
            ),
            QualityIssue(
                id="QI-005",
                entity="Sample",
                entity_id="SMP-001",
                entity_name="SAMPLE-001",
                issue_type=IssueType.INCONSISTENT,
                field_name="germplasmDbId",
                description="Referenced germplasm does not exist",
                severity=IssueSeverity.HIGH,
                status=IssueStatus.OPEN,
                detected_at=datetime(2024, 12, 7, 14, 0, 0),
            ),
            QualityIssue(
                id="QI-006",
                entity="Trial",
                entity_id="TRL-005",
                entity_name="Yield Trial 2024",
                issue_type=IssueType.MISSING,
                field_name="endDate",
                description="Trial end date not recorded",
                severity=IssueSeverity.LOW,
                status=IssueStatus.OPEN,
                detected_at=datetime(2024, 12, 6, 10, 0, 0),
            ),
            QualityIssue(
                id="QI-007",
                entity="Observation",
                entity_id="OBS-102",
                entity_name="Grain Yield",
                issue_type=IssueType.OUTLIER,
                field_name="value",
                description="Negative yield value (-5.2 t/ha)",
                severity=IssueSeverity.CRITICAL,
                status=IssueStatus.IN_PROGRESS,
                detected_at=datetime(2024, 12, 5, 16, 0, 0),
            ),
        ]
        
        for issue in demo_issues:
            self._issues[issue.id] = issue
        
        # Demo metrics
        demo_metrics = [
            QualityMetric(
                entity="Germplasm",
                total_records=1250,
                complete_records=1180,
                issue_count=15,
                completeness=94.4,
                last_validated=datetime.now(),
            ),
            QualityMetric(
                entity="Observations",
                total_records=45000,
                complete_records=44500,
                issue_count=23,
                completeness=98.9,
                last_validated=datetime.now(),
            ),
            QualityMetric(
                entity="Samples",
                total_records=500,
                complete_records=485,
                issue_count=8,
                completeness=97.0,
                last_validated=datetime.now(),
            ),
            QualityMetric(
                entity="Locations",
                total_records=25,
                complete_records=24,
                issue_count=2,
                completeness=96.0,
                last_validated=datetime.now(),
            ),
            QualityMetric(
                entity="Trials",
                total_records=15,
                complete_records=15,
                issue_count=0,
                completeness=100.0,
                last_validated=datetime.now(),
            ),
            QualityMetric(
                entity="Studies",
                total_records=42,
                complete_records=40,
                issue_count=3,
                completeness=95.2,
                last_validated=datetime.now(),
            ),
            QualityMetric(
                entity="Programs",
                total_records=8,
                complete_records=8,
                issue_count=0,
                completeness=100.0,
                last_validated=datetime.now(),
            ),
        ]
        
        for metric in demo_metrics:
            self._metrics[metric.entity] = metric
        
        # Demo validation rules
        demo_rules = [
            ValidationRule(
                id="VR-001",
                entity="Germplasm",
                field_name="germplasmName",
                rule_type="required",
                rule_config={},
                severity=IssueSeverity.HIGH,
            ),
            ValidationRule(
                id="VR-002",
                entity="Germplasm",
                field_name="accessionNumber",
                rule_type="unique",
                rule_config={},
                severity=IssueSeverity.HIGH,
            ),
            ValidationRule(
                id="VR-003",
                entity="Observation",
                field_name="value",
                rule_type="range",
                rule_config={"min": 0, "max": 1000},
                severity=IssueSeverity.MEDIUM,
            ),
            ValidationRule(
                id="VR-004",
                entity="Location",
                field_name="latitude",
                rule_type="range",
                rule_config={"min": -90, "max": 90},
                severity=IssueSeverity.MEDIUM,
            ),
            ValidationRule(
                id="VR-005",
                entity="Sample",
                field_name="germplasmDbId",
                rule_type="reference",
                rule_config={"entity": "Germplasm", "field": "germplasmDbId"},
                severity=IssueSeverity.HIGH,
            ),
        ]
        
        for rule in demo_rules:
            self._rules[rule.id] = rule
    
    # Issues CRUD
    def list_issues(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        entity: Optional[str] = None,
        issue_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List quality issues with optional filters"""
        issues = list(self._issues.values())
        
        if status:
            issues = [i for i in issues if i.status.value == status]
        
        if severity:
            issues = [i for i in issues if i.severity.value == severity]
        
        if entity:
            issues = [i for i in issues if i.entity.lower() == entity.lower()]
        
        if issue_type:
            issues = [i for i in issues if i.issue_type.value == issue_type]
        
        # Sort by severity (critical first) then by detected date
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        issues.sort(key=lambda i: (severity_order.get(i.severity.value, 4), -i.detected_at.timestamp()))
        
        return [i.to_dict() for i in issues]
    
    def get_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Get issue by ID"""
        issue = self._issues.get(issue_id)
        return issue.to_dict() if issue else None
    
    def create_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new quality issue"""
        issue_id = f"QI-{uuid.uuid4().hex[:6].upper()}"
        
        issue = QualityIssue(
            id=issue_id,
            entity=data["entity"],
            entity_id=data["entityId"],
            entity_name=data["entityName"],
            issue_type=IssueType(data["issueType"]),
            field_name=data["field"],
            description=data["description"],
            severity=IssueSeverity(data.get("severity", "medium")),
            status=IssueStatus.OPEN,
            detected_at=datetime.now(),
        )
        
        self._issues[issue_id] = issue
        
        # Update metrics
        if issue.entity in self._metrics:
            self._metrics[issue.entity].issue_count += 1
        
        return issue.to_dict()
    
    def resolve_issue(self, issue_id: str, resolved_by: str, notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Resolve an issue"""
        issue = self._issues.get(issue_id)
        if not issue:
            return None
        
        issue.status = IssueStatus.RESOLVED
        issue.resolved_at = datetime.now()
        issue.resolved_by = resolved_by
        issue.resolution_notes = notes
        
        # Update metrics
        if issue.entity in self._metrics:
            self._metrics[issue.entity].issue_count = max(0, self._metrics[issue.entity].issue_count - 1)
        
        return issue.to_dict()
    
    def ignore_issue(self, issue_id: str, reason: str) -> Optional[Dict[str, Any]]:
        """Ignore an issue"""
        issue = self._issues.get(issue_id)
        if not issue:
            return None
        
        issue.status = IssueStatus.IGNORED
        issue.resolution_notes = f"Ignored: {reason}"
        
        return issue.to_dict()
    
    def reopen_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Reopen a resolved/ignored issue"""
        issue = self._issues.get(issue_id)
        if not issue:
            return None
        
        issue.status = IssueStatus.OPEN
        issue.resolved_at = None
        issue.resolved_by = None
        
        return issue.to_dict()
    
    # Metrics
    def get_metrics(self) -> List[Dict[str, Any]]:
        """Get all quality metrics"""
        return [m.to_dict() for m in self._metrics.values()]
    
    def get_metric(self, entity: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific entity"""
        metric = self._metrics.get(entity)
        return metric.to_dict() if metric else None
    
    def get_overall_score(self) -> Dict[str, Any]:
        """Calculate overall data quality score"""
        metrics = list(self._metrics.values())
        
        if not metrics:
            return {"score": 100, "grade": "A", "totalRecords": 0, "totalIssues": 0}
        
        total_records = sum(m.total_records for m in metrics)
        total_complete = sum(m.complete_records for m in metrics)
        total_issues = sum(m.issue_count for m in metrics)
        
        # Calculate weighted completeness
        overall_completeness = (total_complete / total_records * 100) if total_records > 0 else 100
        
        # Adjust score based on issue severity
        open_issues = [i for i in self._issues.values() if i.status == IssueStatus.OPEN]
        severity_penalty = sum(
            {"critical": 5, "high": 2, "medium": 1, "low": 0.5}.get(i.severity.value, 0)
            for i in open_issues
        )
        
        score = max(0, min(100, overall_completeness - severity_penalty))
        
        # Determine grade
        if score >= 95:
            grade = "A"
        elif score >= 85:
            grade = "B"
        elif score >= 75:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "score": round(score, 1),
            "grade": grade,
            "completeness": round(overall_completeness, 1),
            "totalRecords": total_records,
            "totalIssues": total_issues,
            "openIssues": len(open_issues),
            "criticalIssues": len([i for i in open_issues if i.severity == IssueSeverity.CRITICAL]),
            "highIssues": len([i for i in open_issues if i.severity == IssueSeverity.HIGH]),
        }
    
    # Validation
    def run_validation(self, entity: Optional[str] = None) -> Dict[str, Any]:
        """Run data validation (simulated)"""
        validation_id = f"VAL-{uuid.uuid4().hex[:6].upper()}"
        
        # Simulate validation
        entities_validated = [entity] if entity else list(self._metrics.keys())
        new_issues = 0
        
        # In a real implementation, this would scan the database
        # For demo, we just update the last_validated timestamp
        for e in entities_validated:
            if e in self._metrics:
                self._metrics[e].last_validated = datetime.now()
        
        result = {
            "validationId": validation_id,
            "status": "completed",
            "entitiesValidated": entities_validated,
            "recordsScanned": sum(self._metrics[e].total_records for e in entities_validated if e in self._metrics),
            "newIssuesFound": new_issues,
            "completedAt": datetime.now().isoformat(),
        }
        
        self._validation_history.append(result)
        
        return result
    
    def get_validation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get validation history"""
        return self._validation_history[-limit:]
    
    # Rules
    def list_rules(self, entity: Optional[str] = None) -> List[Dict[str, Any]]:
        """List validation rules"""
        rules = list(self._rules.values())
        
        if entity:
            rules = [r for r in rules if r.entity.lower() == entity.lower()]
        
        return [r.to_dict() for r in rules]
    
    def create_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a validation rule"""
        rule_id = f"VR-{uuid.uuid4().hex[:6].upper()}"
        
        rule = ValidationRule(
            id=rule_id,
            entity=data["entity"],
            field_name=data["field"],
            rule_type=data["ruleType"],
            rule_config=data.get("ruleConfig", {}),
            severity=IssueSeverity(data.get("severity", "medium")),
            enabled=data.get("enabled", True),
        )
        
        self._rules[rule_id] = rule
        return rule.to_dict()
    
    def toggle_rule(self, rule_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
        """Enable/disable a validation rule"""
        rule = self._rules.get(rule_id)
        if not rule:
            return None
        
        rule.enabled = enabled
        return rule.to_dict()
    
    # Statistics
    def get_statistics(self) -> Dict[str, Any]:
        """Get data quality statistics"""
        issues = list(self._issues.values())
        open_issues = [i for i in issues if i.status == IssueStatus.OPEN]
        
        # Issues by type
        by_type = {}
        for issue in open_issues:
            by_type[issue.issue_type.value] = by_type.get(issue.issue_type.value, 0) + 1
        
        # Issues by severity
        by_severity = {}
        for issue in open_issues:
            by_severity[issue.severity.value] = by_severity.get(issue.severity.value, 0) + 1
        
        # Issues by entity
        by_entity = {}
        for issue in open_issues:
            by_entity[issue.entity] = by_entity.get(issue.entity, 0) + 1
        
        # Resolution rate
        resolved = len([i for i in issues if i.status == IssueStatus.RESOLVED])
        resolution_rate = (resolved / len(issues) * 100) if issues else 100
        
        return {
            "totalIssues": len(issues),
            "openIssues": len(open_issues),
            "resolvedIssues": resolved,
            "ignoredIssues": len([i for i in issues if i.status == IssueStatus.IGNORED]),
            "resolutionRate": round(resolution_rate, 1),
            "byType": by_type,
            "bySeverity": by_severity,
            "byEntity": by_entity,
            "totalRules": len(self._rules),
            "activeRules": len([r for r in self._rules.values() if r.enabled]),
        }
    
    def get_issue_types(self) -> List[Dict[str, str]]:
        """Get list of issue types"""
        return [
            {"value": "missing", "label": "Missing Data"},
            {"value": "outlier", "label": "Outlier Value"},
            {"value": "duplicate", "label": "Duplicate Record"},
            {"value": "invalid", "label": "Invalid Format"},
            {"value": "inconsistent", "label": "Inconsistent Reference"},
            {"value": "orphan", "label": "Orphan Record"},
        ]
    
    def get_severities(self) -> List[Dict[str, str]]:
        """Get list of severity levels"""
        return [
            {"value": "low", "label": "Low"},
            {"value": "medium", "label": "Medium"},
            {"value": "high", "label": "High"},
            {"value": "critical", "label": "Critical"},
        ]


# Singleton instance
_data_quality_service: Optional[DataQualityService] = None


def get_data_quality_service() -> DataQualityService:
    """Get or create data quality service singleton"""
    global _data_quality_service
    if _data_quality_service is None:
        _data_quality_service = DataQualityService()
    return _data_quality_service

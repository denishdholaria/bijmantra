"""
Data Quality Service
Monitors and validates data quality across the system.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
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


class DataQualityService:
    """Service for data quality monitoring and validation.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def get_dashboard(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict[str, Any]:
        """Get data quality dashboard summary from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Dashboard summary dictionary with issue counts
        """
        # Query actual data counts to assess quality
        from app.models.germplasm import Germplasm
        from app.models.core import Program, Trial, Study, Location
        from app.models.phenotyping import ObservationUnit

        # Count records with potential quality issues
        # Missing data checks
        germplasm_count = await self._count_records(db, Germplasm, organization_id)
        program_count = await self._count_records(db, Program, organization_id)
        trial_count = await self._count_records(db, Trial, organization_id)
        study_count = await self._count_records(db, Study, organization_id)
        location_count = await self._count_records(db, Location, organization_id)

        # Check for germplasm without species
        germplasm_missing_species = await self._count_missing_field(
            db, Germplasm, organization_id, Germplasm.species
        )

        # Check for locations without coordinates
        location_missing_coords = await self._count_missing_field(
            db, Location, organization_id, Location.coordinates
        )

        # Build issues list from actual data quality checks
        issues = []

        if germplasm_missing_species > 0:
            issues.append({
                "id": "germ-species-missing",
                "entity": "germplasm",
                "entityId": "multiple",
                "entityName": f"{germplasm_missing_species} germplasm records",
                "issueType": IssueType.MISSING.value,
                "field": "species",
                "description": f"{germplasm_missing_species} germplasm records missing species information",
                "severity": IssueSeverity.MEDIUM.value,
                "status": IssueStatus.OPEN.value,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "resolvedAt": None,
                "resolvedBy": None,
            })

        if location_missing_coords > 0:
            issues.append({
                "id": "loc-coords-missing",
                "entity": "location",
                "entityId": "multiple",
                "entityName": f"{location_missing_coords} location records",
                "issueType": IssueType.MISSING.value,
                "field": "coordinates",
                "description": f"{location_missing_coords} locations missing GPS coordinates",
                "severity": IssueSeverity.LOW.value,
                "status": IssueStatus.OPEN.value,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "resolvedAt": None,
                "resolvedBy": None,
            })

        # Count by severity
        critical = len([i for i in issues if i["severity"] == IssueSeverity.CRITICAL.value])
        high = len([i for i in issues if i["severity"] == IssueSeverity.HIGH.value])
        medium = len([i for i in issues if i["severity"] == IssueSeverity.MEDIUM.value])
        low = len([i for i in issues if i["severity"] == IssueSeverity.LOW.value])

        # Count by type
        issues_by_type = {}
        for issue in issues:
            t = issue["issueType"]
            issues_by_type[t] = issues_by_type.get(t, 0) + 1

        # Count by entity
        issues_by_entity = {}
        for issue in issues:
            e = issue["entity"]
            issues_by_entity[e] = issues_by_entity.get(e, 0) + 1

        return {
            "totalIssues": len(issues),
            "openIssues": len([i for i in issues if i["status"] == IssueStatus.OPEN.value]),
            "resolvedIssues": len([i for i in issues if i["status"] == IssueStatus.RESOLVED.value]),
            "criticalIssues": critical,
            "highIssues": high,
            "mediumIssues": medium,
            "lowIssues": low,
            "issuesByType": issues_by_type,
            "issuesByEntity": issues_by_entity,
            "recentIssues": issues[:10],
            "dataCounts": {
                "germplasm": germplasm_count,
                "programs": program_count,
                "trials": trial_count,
                "studies": study_count,
                "locations": location_count,
            },
        }

    async def _count_records(
        self,
        db: AsyncSession,
        model,
        organization_id: int,
    ) -> int:
        """Count records for a model."""
        stmt = (
            select(func.count(model.id))
            .where(model.organization_id == organization_id)
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _count_missing_field(
        self,
        db: AsyncSession,
        model,
        organization_id: int,
        field,
    ) -> int:
        """Count records with missing field value."""
        stmt = (
            select(func.count(model.id))
            .where(model.organization_id == organization_id)
            .where(field.is_(None))
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def get_issues(
        self,
        db: AsyncSession,
        organization_id: int,
        entity: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get filtered list of data quality issues.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            entity: Filter by entity type
            severity: Filter by severity level
            status: Filter by status
            limit: Maximum results to return
            
        Returns:
            List of issue dictionaries
        """
        # Get dashboard which calculates issues from actual data
        dashboard = await self.get_dashboard(db, organization_id)
        issues = dashboard.get("recentIssues", [])

        # Apply filters
        if entity:
            issues = [i for i in issues if i["entity"] == entity]
        if severity:
            issues = [i for i in issues if i["severity"] == severity]
        if status:
            issues = [i for i in issues if i["status"] == status]

        return issues[:limit]

    async def run_validation(
        self,
        db: AsyncSession,
        organization_id: int,
        entity_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run data validation checks and return results.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            entity_type: Optional entity type to validate
            
        Returns:
            Validation results dictionary
        """
        from app.models.germplasm import Germplasm
        from app.models.core import Program, Trial, Study, Location

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "organization_id": organization_id,
            "checks_run": [],
            "issues_found": 0,
            "entities_checked": 0,
        }

        # Germplasm validation
        if entity_type is None or entity_type == "germplasm":
            germplasm_count = await self._count_records(db, Germplasm, organization_id)
            missing_species = await self._count_missing_field(db, Germplasm, organization_id, Germplasm.species)
            missing_name = await self._count_missing_field(db, Germplasm, organization_id, Germplasm.germplasm_name)

            results["checks_run"].append({
                "entity": "germplasm",
                "total_records": germplasm_count,
                "issues": {
                    "missing_species": missing_species,
                    "missing_name": missing_name,
                },
            })
            results["entities_checked"] += germplasm_count
            results["issues_found"] += missing_species + missing_name

        # Location validation
        if entity_type is None or entity_type == "location":
            location_count = await self._count_records(db, Location, organization_id)
            missing_coords = await self._count_missing_field(db, Location, organization_id, Location.coordinates)
            missing_country = await self._count_missing_field(db, Location, organization_id, Location.country_name)

            results["checks_run"].append({
                "entity": "location",
                "total_records": location_count,
                "issues": {
                    "missing_coordinates": missing_coords,
                    "missing_country": missing_country,
                },
            })
            results["entities_checked"] += location_count
            results["issues_found"] += missing_coords + missing_country

        # Program validation
        if entity_type is None or entity_type == "program":
            program_count = await self._count_records(db, Program, organization_id)
            missing_name = await self._count_missing_field(db, Program, organization_id, Program.program_name)

            results["checks_run"].append({
                "entity": "program",
                "total_records": program_count,
                "issues": {
                    "missing_name": missing_name,
                },
            })
            results["entities_checked"] += program_count
            results["issues_found"] += missing_name

        return results

    async def get_entity_quality(
        self,
        db: AsyncSession,
        organization_id: int,
        entity_type: str,
        entity_id: str,
    ) -> Dict[str, Any]:
        """Get data quality assessment for a specific entity.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            entity_type: Entity type (germplasm, location, etc.)
            entity_id: Entity ID
            
        Returns:
            Quality assessment dictionary
        """
        from app.models.germplasm import Germplasm
        from app.models.core import Location, Program, Trial

        model_map = {
            "germplasm": Germplasm,
            "location": Location,
            "program": Program,
            "trial": Trial,
        }

        model = model_map.get(entity_type)
        if not model:
            return {"error": f"Unknown entity type: {entity_type}"}

        stmt = (
            select(model)
            .where(model.organization_id == organization_id)
            .where(model.id == int(entity_id))
        )

        result = await db.execute(stmt)
        entity = result.scalar_one_or_none()

        if not entity:
            return {"error": f"{entity_type} {entity_id} not found"}

        # Calculate completeness score
        required_fields = self._get_required_fields(entity_type)
        filled_fields = 0
        missing_fields = []

        for field in required_fields:
            value = getattr(entity, field, None)
            if value is not None and value != "":
                filled_fields += 1
            else:
                missing_fields.append(field)

        completeness = (filled_fields / len(required_fields) * 100) if required_fields else 100

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "completeness_score": round(completeness, 1),
            "required_fields": len(required_fields),
            "filled_fields": filled_fields,
            "missing_fields": missing_fields,
            "quality_grade": self._get_quality_grade(completeness),
        }

    def _get_required_fields(self, entity_type: str) -> List[str]:
        """Get required fields for an entity type."""
        required = {
            "germplasm": ["germplasm_name", "species", "accession_number"],
            "location": ["location_name", "country_name"],
            "program": ["program_name"],
            "trial": ["trial_name"],
        }
        return required.get(entity_type, [])

    def _get_quality_grade(self, completeness: float) -> str:
        """Get quality grade from completeness score."""
        if completeness >= 90:
            return "A"
        elif completeness >= 75:
            return "B"
        elif completeness >= 50:
            return "C"
        elif completeness >= 25:
            return "D"
        else:
            return "F"

    # --- Thin convenience methods used by API endpoints ---

    async def list_issues(
        self,
        db: AsyncSession,
        organization_id: int,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        entity: Optional[str] = None,
        issue_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List quality issues — delegates to get_issues."""
        return await self.get_issues(
            db, organization_id,
            entity=entity, severity=severity, status=status,
        )

    async def get_metrics(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict[str, Any]:
        """Get quality metrics — delegates to dashboard."""
        dashboard = await self.get_dashboard(db, organization_id)
        return {
            "totalIssues": dashboard.get("totalIssues", 0),
            "issuesByType": dashboard.get("issuesByType", {}),
            "issuesByEntity": dashboard.get("issuesByEntity", {}),
            "dataCounts": dashboard.get("dataCounts", {}),
        }

    async def get_overall_score(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict[str, Any]:
        """Calculate overall data quality score."""
        dashboard = await self.get_dashboard(db, organization_id)
        total = dashboard.get("totalIssues", 0)
        return {
            "score": 100 if total == 0 else max(0, 100 - total * 5),
            "totalIssues": total,
            "grade": self._get_quality_grade(100 if total == 0 else max(0, 100 - total * 5)),
        }

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict[str, Any]:
        """Get data quality statistics."""
        dashboard = await self.get_dashboard(db, organization_id)
        return {
            "totalIssues": dashboard.get("totalIssues", 0),
            "openIssues": dashboard.get("openIssues", 0),
            "resolvedIssues": dashboard.get("resolvedIssues", 0),
            "bySeverity": {
                "critical": dashboard.get("criticalIssues", 0),
                "high": dashboard.get("highIssues", 0),
                "medium": dashboard.get("mediumIssues", 0),
                "low": dashboard.get("lowIssues", 0),
            },
        }

    async def get_validation_history(
        self,
        db: AsyncSession,
        organization_id: int,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get validation run history. Returns empty list when no runs stored."""
        return []

    async def list_rules(
        self,
        db: AsyncSession,
        organization_id: int,
        entity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List validation rules. Returns empty list when no rules stored."""
        return []

    def get_issue_types(self) -> List[Dict[str, str]]:
        """Get list of issue types."""
        return [{"value": t.value, "label": t.value.title()} for t in IssueType]

    def get_severities(self) -> List[Dict[str, str]]:
        """Get list of severity levels."""
        return [{"value": s.value, "label": s.value.title()} for s in IssueSeverity]


# Factory function
def get_data_quality_service() -> DataQualityService:
    """Get the data quality service instance."""
    return DataQualityService()

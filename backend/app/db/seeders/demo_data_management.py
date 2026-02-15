"""
Demo Data Management Seeder
Seeds germplasm collections, validation rules/issues, and backups for Demo Organization
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import logging

from app.db.seeders.base import BaseSeeder, register_seeder
from app.models.core import Organization
from app.core.config import settings

logger = logging.getLogger(__name__)


@register_seeder
class DemoDataManagementSeeder(BaseSeeder):
    """Seeds data management demo data"""
    
    name = "demo_data_management"
    priority = 70  # After core and germplasm data
    
    def seed(self) -> int:
        """Seed data management data"""
        from app.models.data_management import (
            GermplasmCollection, ValidationRule, ValidationIssue, 
            ValidationRun, Backup,
            CollectionType, CollectionStatus, ValidationSeverity,
            ValidationIssueStatus, ValidationRunStatus, BackupType, BackupStatus
        )
        
        # Get Demo Organization
        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()
        
        if not demo_org:
            logger.warning("Demo Organization not found, skipping data management seeding")
            return 0
        
        count = 0
        org_id = demo_org.id
        now = datetime.now(timezone.utc)
        
        # Check if already seeded
        existing = self.db.query(GermplasmCollection).filter(
            GermplasmCollection.organization_id == org_id
        ).first()
        if existing:
            logger.info("Data management data already seeded")
            return 0
        
        # ============================================
        # GERMPLASM COLLECTIONS
        # ============================================
        collections_data = [
            {
                "collection_code": "COL001",
                "name": "Core Collection 2024",
                "description": "Representative diversity set",
                "collection_type": CollectionType.CORE,
                "status": CollectionStatus.ACTIVE,
                "accession_count": 250,
                "species": ["Wheat", "Barley"],
                "curator_name": "Dr. Smith",
            },
            {
                "collection_code": "COL002",
                "name": "Working Collection",
                "description": "Active breeding materials",
                "collection_type": CollectionType.WORKING,
                "status": CollectionStatus.ACTIVE,
                "accession_count": 1500,
                "species": ["Wheat"],
            },
        ]
        
        for data in collections_data:
            collection = GermplasmCollection(organization_id=org_id, **data)
            self.db.add(collection)
            count += 1
        
        # ============================================
        # VALIDATION RULES
        # ============================================
        rules_data = [
            {"rule_code": "RULE-001", "name": "Range Check", "severity": ValidationSeverity.ERROR, "rule_type": "range_check", "is_system": True},
            {"rule_code": "RULE-002", "name": "Referential Integrity", "severity": ValidationSeverity.ERROR, "rule_type": "referential", "is_system": True},
            {"rule_code": "RULE-003", "name": "Outlier Detection", "severity": ValidationSeverity.WARNING, "rule_type": "outlier", "is_system": True},
        ]
        
        rule_map = {}
        for data in rules_data:
            rule = ValidationRule(organization_id=org_id, enabled=True, **data)
            self.db.add(rule)
            self.db.flush()
            rule_map[data["rule_code"]] = rule.id
            count += 1
        
        # ============================================
        # VALIDATION RUNS
        # ============================================
        run = ValidationRun(
            organization_id=org_id,
            status=ValidationRunStatus.COMPLETED,
            started_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=2) + timedelta(minutes=5),
            records_checked=1250,
            issues_found=3,
            errors_found=1,
            warnings_found=2,
            trigger_type="scheduled",
        )
        self.db.add(run)
        self.db.flush()
        run_id = run.id
        count += 1
        
        # ============================================
        # VALIDATION ISSUES
        # ============================================
        issue = ValidationIssue(
            organization_id=org_id,
            rule_id=rule_map["RULE-001"],
            run_id=run_id,
            issue_type=ValidationSeverity.ERROR,
            status=ValidationIssueStatus.OPEN,
            entity_type="observation",
            record_id="OBS-2025-001",
            field_name="yield",
            message="Value 150 t/ha exceeds maximum threshold (15)",
        )
        self.db.add(issue)
        count += 1
        
        # ============================================
        # BACKUPS
        # ============================================
        backup = Backup(
            organization_id=org_id,
            backup_name=f"backup_{now.strftime('%Y-%m-%d')}_auto",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            size_bytes=250_000_000,  # 250 MB (Integer max is ~2.1 billion)
            storage_path="/backups/daily/backup.tar.gz",
            started_at=now - timedelta(hours=21),
            completed_at=now - timedelta(hours=21) + timedelta(minutes=15),
        )
        self.db.add(backup)
        count += 1
        
        # Seed crop health data
        count += self._seed_crop_health(org_id)
        
        self.db.commit()
        logger.info(f"Seeded {count} data management records")
        return count
    
    def _seed_crop_health(self, org_id) -> int:
        """Seed crop health data"""
        from app.models.data_management import (
            TrialHealth, HealthAlert,
            DiseaseRiskLevel, AlertType, AlertSeverity
        )
        
        count = 0
        now = datetime.now(timezone.utc)
        
        trial = TrialHealth(
            organization_id=org_id,
            trial_name="Yield Trial 2024-A",
            location="Punjab Station",
            crop="Rice",
            health_score=92.0,
            disease_risk=DiseaseRiskLevel.LOW,
            stress_level=15.0,
            last_scan_at=now - timedelta(hours=2),
            plots_scanned=48,
            total_plots=50,
        )
        self.db.add(trial)
        self.db.flush()
        count += 1
        
        alert = HealthAlert(
            organization_id=org_id,
            trial_health_id=trial.id,
            alert_type=AlertType.WEATHER,
            severity=AlertSeverity.LOW,
            message="Heavy rain forecast - monitor for waterlogging",
            location="Punjab Station",
        )
        self.db.add(alert)
        count += 1
        
        return count
    
    def clear(self) -> int:
        """Clear data management data"""
        from app.models.data_management import (
            GermplasmCollection, GermplasmCollectionMember,
            ValidationRule, ValidationIssue, ValidationRun, Backup,
            TrialHealth, HealthAlert
        )
        
        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()
        
        if not demo_org:
            return 0
        
        count = 0
        
        count += self.db.query(GermplasmCollectionMember).filter(
            GermplasmCollectionMember.collection_id.in_(
                self.db.query(GermplasmCollection.id).filter(
                    GermplasmCollection.organization_id == demo_org.id
                )
            )
        ).delete(synchronize_session=False)
        
        count += self.db.query(GermplasmCollection).filter(
            GermplasmCollection.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(ValidationIssue).filter(
            ValidationIssue.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(ValidationRun).filter(
            ValidationRun.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(ValidationRule).filter(
            ValidationRule.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(Backup).filter(
            Backup.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(HealthAlert).filter(
            HealthAlert.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(TrialHealth).filter(
            TrialHealth.organization_id == demo_org.id
        ).delete()
        
        self.db.commit()
        return count

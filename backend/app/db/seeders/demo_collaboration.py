"""
Demo Collaboration & Reporting Seeder
Seeds report templates, workspaces, tasks, and sync data for Demo Organization
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.db.seeders.base import BaseSeeder, register_seeder
from app.models.core import Organization, User
from app.models.collaboration import (
    ReportTemplate, ReportSchedule, GeneratedReport,
    CollaborationWorkspace, WorkspaceMember, UserPresence,
    CollaborationActivity, CollaborationTask, CollaborationComment,
    SyncItem, SyncHistory, OfflineDataCache, SyncSettings,
    ReportCategory, ReportFormat, ScheduleFrequency, ScheduleStatus,
    ReportStatus, WorkspaceType, MemberRole, MemberStatus,
    CollabActivityType, TaskStatus, TaskPriority,
    SyncStatus, SyncAction, SyncEntityType
)
from app.core.config import settings


@register_seeder
class DemoCollaborationSeeder(BaseSeeder):
    """Seeds collaboration and reporting demo data"""

    name = "demo_collaboration"
    priority = 90  # Run after user management seeder

    def seed(self) -> int:
        count = 0

        # Get Demo Organization
        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()

        if not demo_org:
            print(f"Demo organization '{settings.DEMO_ORG_NAME}' not found")
            return 0

        # Get demo user
        demo_user = self.db.query(User).filter(
            User.organization_id == demo_org.id
        ).first()

        if not demo_user:
            print("No demo user found")
            return 0

        # Check if already seeded
        existing = self.db.query(ReportTemplate).filter(
            ReportTemplate.organization_id == demo_org.id
        ).first()
        if existing:
            print("Collaboration data already seeded")
            return 0

        # Seed Report Templates
        count += self._seed_report_templates(demo_org.id)

        # Seed Workspaces
        count += self._seed_workspaces(demo_org.id, demo_user.id)

        # Seed Sync Data
        count += self._seed_sync_data(demo_org.id, demo_user.id)

        self.db.commit()
        return count

    def _seed_report_templates(self, org_id: int) -> int:
        """Seed report templates"""
        templates = [
            ReportTemplate(
                organization_id=org_id,
                name="Trial Summary Report",
                description="Comprehensive overview of trial performance",
                category=ReportCategory.TRIALS,
                formats=[ReportFormat.PDF.value, ReportFormat.EXCEL.value],
                parameters=[
                    {"name": "trial_id", "type": "string", "required": False},
                    {"name": "include_statistics", "type": "boolean", "default": True}
                ],
                generation_count=45,
                is_system=True,
                is_active=True
            ),
            ReportTemplate(
                organization_id=org_id,
                name="Germplasm Inventory",
                description="Current stock levels and viability status",
                category=ReportCategory.GERMPLASM,
                formats=[ReportFormat.PDF.value, ReportFormat.EXCEL.value],
                parameters=[
                    {"name": "location", "type": "string", "required": False}
                ],
                generation_count=28,
                is_system=True,
                is_active=True
            ),
            ReportTemplate(
                organization_id=org_id,
                name="Breeding Progress",
                description="Pipeline advancement and genetic gain tracking",
                category=ReportCategory.BREEDING,
                formats=[ReportFormat.PDF.value, ReportFormat.POWERPOINT.value],
                parameters=[
                    {"name": "program_id", "type": "string", "required": False}
                ],
                generation_count=12,
                is_system=True,
                is_active=True
            ),
            ReportTemplate(
                organization_id=org_id,
                name="Phenotypic Analysis",
                description="Statistical analysis of trait data",
                category=ReportCategory.PHENOTYPING,
                formats=[ReportFormat.PDF.value, ReportFormat.EXCEL.value, ReportFormat.JSON.value],
                parameters=[
                    {"name": "study_id", "type": "string", "required": False}
                ],
                generation_count=67,
                is_system=True,
                is_active=True
            ),
            ReportTemplate(
                organization_id=org_id,
                name="Genomic Selection Results",
                description="GEBV rankings and selection recommendations",
                category=ReportCategory.GENOMICS,
                formats=[ReportFormat.PDF.value, ReportFormat.EXCEL.value, ReportFormat.CSV.value],
                parameters=[
                    {"name": "model_id", "type": "string", "required": False},
                    {"name": "top_n", "type": "integer", "default": 100}
                ],
                generation_count=34,
                is_system=True,
                is_active=True
            ),
            ReportTemplate(
                organization_id=org_id,
                name="Seed Lot Tracking",
                description="Seed inventory movements and traceability",
                category=ReportCategory.INVENTORY,
                formats=[ReportFormat.PDF.value, ReportFormat.EXCEL.value, ReportFormat.CSV.value],
                parameters=[
                    {"name": "date_from", "type": "date", "required": False},
                    {"name": "date_to", "type": "date", "required": False}
                ],
                generation_count=52,
                is_system=True,
                is_active=True
            ),
        ]

        for template in templates:
            self.db.add(template)
        self.db.flush()

        return len(templates)

    def _seed_workspaces(self, org_id: int, user_id: int) -> int:
        """Seed collaboration workspaces"""
        count = 0

        # Create workspaces
        workspaces = [
            CollaborationWorkspace(
                organization_id=org_id,
                name="Rice Yield Trial 2025",
                description="Multi-location yield trial for new rice varieties",
                type=WorkspaceType.TRIAL,
                owner_id=user_id,
                entity_id="trial-001",
                is_active=True
            ),
            CollaborationWorkspace(
                organization_id=org_id,
                name="Disease Resistance Crossing",
                description="Crossing project for blast resistance introgression",
                type=WorkspaceType.CROSSING_PROJECT,
                owner_id=user_id,
                entity_id="cross-proj-001",
                is_active=True
            ),
            CollaborationWorkspace(
                organization_id=org_id,
                name="GWAS Analysis - Drought",
                description="Genome-wide association study for drought tolerance",
                type=WorkspaceType.ANALYSIS,
                owner_id=user_id,
                is_active=True
            ),
        ]

        for ws in workspaces:
            self.db.add(ws)
        self.db.flush()
        count += len(workspaces)

        # Add workspace members
        for ws in workspaces:
            member = WorkspaceMember(
                workspace_id=ws.id,
                user_id=user_id,
                role=MemberRole.OWNER,
                joined_at=datetime.now(timezone.utc)
            )
            self.db.add(member)
            count += 1

        # Create user presence
        presence = UserPresence(
            user_id=user_id,
            status=MemberStatus.ONLINE,
            current_workspace_id=workspaces[0].id if workspaces else None,
            last_active=datetime.now(timezone.utc),
            last_heartbeat=datetime.now(timezone.utc)
        )
        self.db.add(presence)
        count += 1

        # Create activities
        activities = [
            CollaborationActivity(
                organization_id=org_id,
                workspace_id=workspaces[0].id,
                user_id=user_id,
                activity_type=CollabActivityType.UPDATED,
                entity_type="trial",
                entity_id="trial-001",
                entity_name="Rice Yield Trial 2025",
                description="Updated trial status to 'Active'"
            ),
            CollaborationActivity(
                organization_id=org_id,
                workspace_id=workspaces[1].id,
                user_id=user_id,
                activity_type=CollabActivityType.CREATED,
                entity_type="cross",
                entity_id="cross-042",
                entity_name="IR64 × Kasalath",
                description="Created new crossing plan"
            ),
        ]

        for activity in activities:
            self.db.add(activity)
        count += len(activities)

        # Create tasks
        tasks = [
            CollaborationTask(
                organization_id=org_id,
                workspace_id=workspaces[0].id,
                title="Complete Block B observations",
                description="Finish phenotyping for remaining 50 plots",
                assignee_id=user_id,
                created_by_id=user_id,
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                due_date=datetime.now(timezone.utc) + timedelta(days=2)
            ),
            CollaborationTask(
                organization_id=org_id,
                workspace_id=workspaces[1].id,
                title="Review crossing results",
                description="Analyze F1 seed set data",
                assignee_id=user_id,
                created_by_id=user_id,
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                due_date=datetime.now(timezone.utc) + timedelta(days=5)
            ),
            CollaborationTask(
                organization_id=org_id,
                workspace_id=workspaces[2].id,
                title="Validate GWAS markers",
                description="Check significant markers in validation panel",
                assignee_id=user_id,
                created_by_id=user_id,
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                due_date=datetime.now(timezone.utc) + timedelta(days=7)
            ),
            CollaborationTask(
                organization_id=org_id,
                title="Prepare quarterly report",
                assignee_id=user_id,
                created_by_id=user_id,
                status=TaskStatus.DONE,
                priority=TaskPriority.MEDIUM,
                due_date=datetime.now(timezone.utc) - timedelta(days=1),
                completed_at=datetime.now(timezone.utc) - timedelta(days=1)
            ),
        ]

        for task in tasks:
            self.db.add(task)
        count += len(tasks)

        # Create comments
        comments = [
            CollaborationComment(
                organization_id=org_id,
                workspace_id=workspaces[1].id,
                user_id=user_id,
                entity_type="cross",
                entity_id="cross-042",
                content="Great progress on the crossing! The F1 seed set looks promising."
            ),
            CollaborationComment(
                organization_id=org_id,
                workspace_id=workspaces[0].id,
                user_id=user_id,
                entity_type="trial",
                entity_id="trial-001",
                content="Let's prioritize the high-yielding entries for advancement."
            ),
        ]

        for comment in comments:
            self.db.add(comment)
        count += len(comments)

        return count

    def _seed_sync_data(self, org_id: int, user_id: int) -> int:
        """Seed sync items and history"""
        count = 0

        # Create pending sync items
        sync_items = [
            SyncItem(
                organization_id=org_id,
                user_id=user_id,
                entity_type=SyncEntityType.OBSERVATION,
                entity_id="obs-2025-001",
                name="Plot observations - Block A",
                status=SyncStatus.PENDING,
                size_bytes=24576,
                last_modified=datetime.now(timezone.utc) - timedelta(hours=1)
            ),
            SyncItem(
                organization_id=org_id,
                user_id=user_id,
                entity_type=SyncEntityType.GERMPLASM,
                entity_id="grm-2025-001",
                name="New accession GRM-2025-001",
                status=SyncStatus.PENDING,
                size_bytes=8192,
                last_modified=datetime.now(timezone.utc) - timedelta(hours=2)
            ),
            SyncItem(
                organization_id=org_id,
                user_id=user_id,
                entity_type=SyncEntityType.IMAGE,
                entity_id="img-batch-001",
                name="Field photos (12 images)",
                status=SyncStatus.PENDING,
                size_bytes=47185920,
                last_modified=datetime.now(timezone.utc) - timedelta(hours=3)
            ),
            SyncItem(
                organization_id=org_id,
                user_id=user_id,
                entity_type=SyncEntityType.CROSS,
                entity_id="crs-2025-042",
                name="Cross record CRS-2025-042",
                status=SyncStatus.CONFLICT,
                size_bytes=4096,
                error_message="Server has newer version",
                last_modified=datetime.now(timezone.utc) - timedelta(hours=6)
            ),
        ]

        for item in sync_items:
            self.db.add(item)
        count += len(sync_items)

        # Create sync history
        history = [
            SyncHistory(
                organization_id=org_id,
                user_id=user_id,
                action=SyncAction.FULL_SYNC,
                description="Full sync completed",
                items_count=1247,
                bytes_transferred=52428800,
                status="success",
                started_at=datetime.now(timezone.utc) - timedelta(minutes=15),
                completed_at=datetime.now(timezone.utc) - timedelta(minutes=10)
            ),
            SyncHistory(
                organization_id=org_id,
                user_id=user_id,
                action=SyncAction.UPLOAD,
                description="Uploaded 15 observations",
                items_count=15,
                bytes_transferred=245760,
                status="success",
                started_at=datetime.now(timezone.utc) - timedelta(minutes=30),
                completed_at=datetime.now(timezone.utc) - timedelta(minutes=25)
            ),
            SyncHistory(
                organization_id=org_id,
                user_id=user_id,
                action=SyncAction.DOWNLOAD,
                description="Downloaded germplasm updates",
                items_count=42,
                bytes_transferred=1048576,
                status="success",
                started_at=datetime.now(timezone.utc) - timedelta(hours=1),
                completed_at=datetime.now(timezone.utc) - timedelta(minutes=55)
            ),
        ]

        for h in history:
            self.db.add(h)
        count += len(history)

        # Create offline data cache entries
        cache_entries = [
            OfflineDataCache(
                organization_id=org_id,
                user_id=user_id,
                category="Trials",
                item_count=24,
                size_bytes=2516582,
                last_updated=datetime.now(timezone.utc) - timedelta(hours=1)
            ),
            OfflineDataCache(
                organization_id=org_id,
                user_id=user_id,
                category="Studies",
                item_count=156,
                size_bytes=8598323,
                last_updated=datetime.now(timezone.utc) - timedelta(hours=1)
            ),
            OfflineDataCache(
                organization_id=org_id,
                user_id=user_id,
                category="Germplasm",
                item_count=3420,
                size_bytes=47806873,
                last_updated=datetime.now(timezone.utc) - timedelta(hours=2)
            ),
            OfflineDataCache(
                organization_id=org_id,
                user_id=user_id,
                category="Observations",
                item_count=28450,
                size_bytes=130862489,
                last_updated=datetime.now(timezone.utc) - timedelta(minutes=30)
            ),
            OfflineDataCache(
                organization_id=org_id,
                user_id=user_id,
                category="Images",
                item_count=1240,
                size_bytes=225485783,  # ~225 MB (Integer max is ~2.1 billion)
                last_updated=datetime.now(timezone.utc) - timedelta(hours=3)
            ),
        ]

        for cache in cache_entries:
            self.db.add(cache)
        count += len(cache_entries)

        # Create sync settings
        sync_settings = SyncSettings(
            user_id=user_id,
            auto_sync=True,
            sync_on_wifi_only=True,
            background_sync=True,
            sync_images=True,
            sync_interval_minutes=15,
            max_offline_days=30,
            conflict_resolution="server_wins"
        )
        self.db.add(sync_settings)
        count += 1

        return count

    def clear(self) -> int:
        """Clear seeded collaboration data"""
        count = 0

        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()

        if not demo_org:
            return 0

        # Delete in reverse order of dependencies
        tables = [
            SyncSettings, OfflineDataCache, SyncHistory, SyncItem,
            CollaborationComment, CollaborationTask, CollaborationActivity,
            UserPresence, WorkspaceMember, CollaborationWorkspace,
            GeneratedReport, ReportSchedule, ReportTemplate
        ]

        for table in tables:
            if hasattr(table, 'organization_id'):
                deleted = self.db.query(table).filter(
                    table.organization_id == demo_org.id
                ).delete()
            elif hasattr(table, 'user_id'):
                # For user-specific tables, get demo user
                demo_user = self.db.query(User).filter(
                    User.organization_id == demo_org.id
                ).first()
                if demo_user:
                    deleted = self.db.query(table).filter(
                        table.user_id == demo_user.id
                    ).delete()
                else:
                    deleted = 0
            else:
                deleted = 0
            count += deleted

        self.db.commit()
        return count

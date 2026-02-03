"""
Demo User Management Seeder

Seeds demo data for:
- Notifications
- Notification preferences
- Teams
- Roles
- Team members
- User profiles
- User preferences
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import logging

from app.db.seeders.base import BaseSeeder, register_seeder
from app.core.config import settings
from app.models.core import Organization, User
from app.models.user_management import (
    Notification,
    NotificationPreference,
    QuietHours,
    UserProfile,
    UserPreference,
    Team,
    Role,
    TeamMember,
    TeamInvitation,
    ActivityLog
)

logger = logging.getLogger(__name__)


@register_seeder
class DemoUserManagementSeeder(BaseSeeder):
    """Seeds demo user management data into Demo Organization"""
    
    name = "demo_user_management"
    description = "Demo notifications, teams, roles, and user preferences"
    
    def seed(self) -> int:
        """Seed demo user management data"""
        count = 0
        
        # Get Demo Organization
        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()
        
        if not demo_org:
            logger.warning(f"Demo Organization '{settings.DEMO_ORG_NAME}' not found. Run demo_brapi seeder first.")
            return 0
        
        # Get demo user
        demo_user = self.db.query(User).filter(
            User.email == settings.DEMO_USER_EMAIL
        ).first()
        
        if not demo_user:
            logger.warning(f"Demo user '{settings.DEMO_USER_EMAIL}' not found. Run demo_users seeder first.")
            return 0
        
        # Seed roles
        count += self._seed_roles(demo_org.id)
        
        # Seed teams
        count += self._seed_teams(demo_org.id, demo_user.id)
        
        # Seed user profile and preferences
        count += self._seed_user_profile(demo_org.id, demo_user.id)
        count += self._seed_user_preferences(demo_org.id, demo_user.id)
        count += self._seed_quiet_hours(demo_org.id, demo_user.id)
        
        # Seed notification preferences
        count += self._seed_notification_preferences(demo_org.id, demo_user.id)
        
        # Seed notifications
        count += self._seed_notifications(demo_org.id, demo_user.id)
        
        # Seed activity logs
        count += self._seed_activity_logs(demo_org.id, demo_user.id)
        
        self.db.commit()
        return count
    
    def _seed_roles(self, org_id: int) -> int:
        """Seed default roles"""
        roles = [
            Role(
                organization_id=org_id,
                role_id="admin",
                name="Admin",
                description="Full system access",
                permissions=["full_access", "manage_users", "system_settings", "delete_data", "manage_teams"],
                color="red"
            ),
            Role(
                organization_id=org_id,
                role_id="breeder",
                name="Breeder",
                description="Breeding program management",
                permissions=["create_trials", "edit_germplasm", "run_analyses", "export_data", "manage_crosses"],
                color="blue"
            ),
            Role(
                organization_id=org_id,
                role_id="technician",
                name="Technician",
                description="Field and lab operations",
                permissions=["collect_data", "view_trials", "upload_images", "edit_observations", "manage_samples"],
                color="green"
            ),
            Role(
                organization_id=org_id,
                role_id="viewer",
                name="Viewer",
                description="Read-only access",
                permissions=["view_data", "generate_reports", "export_limited_data"],
                color="gray"
            ),
        ]
        
        for role in roles:
            existing = self.db.query(Role).filter(
                Role.organization_id == org_id,
                Role.role_id == role.role_id
            ).first()
            if not existing:
                self.db.add(role)
        
        self.db.flush()
        return len(roles)
    
    def _seed_teams(self, org_id: int, lead_id: int) -> int:
        """Seed demo teams"""
        teams = [
            Team(
                organization_id=org_id,
                name="Rice Breeding",
                description="Main rice improvement program focusing on yield and disease resistance",
                lead_id=lead_id
            ),
            Team(
                organization_id=org_id,
                name="Wheat Research",
                description="Wheat variety development for drought tolerance",
                lead_id=lead_id
            ),
            Team(
                organization_id=org_id,
                name="Genomics Lab",
                description="Molecular marker analysis and genotyping services",
                lead_id=lead_id
            ),
            Team(
                organization_id=org_id,
                name="Field Operations",
                description="Trial management and data collection",
                lead_id=lead_id
            ),
        ]
        
        for team in teams:
            existing = self.db.query(Team).filter(
                Team.organization_id == org_id,
                Team.name == team.name
            ).first()
            if not existing:
                self.db.add(team)
        
        self.db.flush()
        
        # Add demo user to first team
        rice_team = self.db.query(Team).filter(
            Team.organization_id == org_id,
            Team.name == "Rice Breeding"
        ).first()
        
        if rice_team:
            existing_member = self.db.query(TeamMember).filter(
                TeamMember.team_id == rice_team.id,
                TeamMember.user_id == lead_id
            ).first()
            if not existing_member:
                member = TeamMember(
                    organization_id=org_id,
                    team_id=rice_team.id,
                    user_id=lead_id,
                    role="admin",
                    status="active",
                    joined_at=datetime.now(timezone.utc) - timedelta(days=30),
                    last_active=datetime.now(timezone.utc)
                )
                self.db.add(member)
        
        return len(teams) + 1
    
    def _seed_user_profile(self, org_id: int, user_id: int) -> int:
        """Seed user profile"""
        existing = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not existing:
            profile = UserProfile(
                organization_id=org_id,
                user_id=user_id,
                phone="+91-9876543210",
                bio="Plant breeder specializing in rice improvement. 10+ years experience in marker-assisted selection.",
                location="IRRI, Los Baños, Philippines",
                timezone="Asia/Manila"
            )
            self.db.add(profile)
            return 1
        return 0
    
    def _seed_user_preferences(self, org_id: int, user_id: int) -> int:
        """Seed user preferences"""
        existing = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()
        
        if not existing:
            prefs = UserPreference(
                organization_id=org_id,
                user_id=user_id,
                theme="system",
                language="en",
                density="comfortable",
                email_notifications=True,
                push_notifications=True,
                sound_enabled=True
            )
            self.db.add(prefs)
            return 1
        return 0
    
    def _seed_quiet_hours(self, org_id: int, user_id: int) -> int:
        """Seed quiet hours settings"""
        existing = self.db.query(QuietHours).filter(
            QuietHours.user_id == user_id
        ).first()
        
        if not existing:
            quiet = QuietHours(
                organization_id=org_id,
                user_id=user_id,
                enabled=False,
                start_time="22:00",
                end_time="07:00"
            )
            self.db.add(quiet)
            return 1
        return 0
    
    def _seed_notification_preferences(self, org_id: int, user_id: int) -> int:
        """Seed notification preferences"""
        categories = [
            ("Trial Updates", True, True, True),
            ("Inventory Alerts", True, True, True),
            ("Weather Alerts", False, True, True),
            ("Data Sync", False, False, True),
            ("Team Updates", True, False, True),
            ("System Alerts", True, True, True),
        ]
        
        count = 0
        for category, email, push, in_app in categories:
            existing = self.db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.category == category
            ).first()
            
            if not existing:
                pref = NotificationPreference(
                    organization_id=org_id,
                    user_id=user_id,
                    category=category,
                    email_enabled=email,
                    push_enabled=push,
                    in_app_enabled=in_app
                )
                self.db.add(pref)
                count += 1
        
        return count
    
    def _seed_notifications(self, org_id: int, user_id: int) -> int:
        """Seed demo notifications"""
        now = datetime.now(timezone.utc)
        
        notifications = [
            Notification(
                organization_id=org_id,
                user_id=user_id,
                notification_type="success",
                title="Trial Completed",
                message="Trial YT-2025-001 has been marked as complete. View results now.",
                category="trials",
                read=False,
                action_url="/trials/YT-2025-001"
            ),
            Notification(
                organization_id=org_id,
                user_id=user_id,
                notification_type="warning",
                title="Low Seed Inventory",
                message="Seed lot SL-2024-089 is below minimum threshold (500 seeds remaining).",
                category="inventory",
                read=False,
                action_url="/seedlots/SL-2024-089"
            ),
            Notification(
                organization_id=org_id,
                user_id=user_id,
                notification_type="info",
                title="Weather Alert",
                message="Heavy rain expected tomorrow. Consider rescheduling field activities.",
                category="weather",
                read=False
            ),
            Notification(
                organization_id=org_id,
                user_id=user_id,
                notification_type="success",
                title="Data Sync Complete",
                message="Successfully synced 1,247 observations from mobile devices.",
                category="sync",
                read=True
            ),
            Notification(
                organization_id=org_id,
                user_id=user_id,
                notification_type="error",
                title="Import Failed",
                message="Failed to import germplasm data. Check file format and try again.",
                category="import",
                read=True,
                action_url="/import-export"
            ),
            Notification(
                organization_id=org_id,
                user_id=user_id,
                notification_type="info",
                title="New Team Member",
                message="Dr. Sarah Johnson has joined the Rice Breeding program.",
                category="team",
                read=True
            ),
            Notification(
                organization_id=org_id,
                user_id=user_id,
                notification_type="success",
                title="Variety Released",
                message="BM-Gold-2025 has been officially released. Congratulations!",
                category="releases",
                read=True
            ),
            Notification(
                organization_id=org_id,
                user_id=user_id,
                notification_type="warning",
                title="Disease Detected",
                message="Possible rice blast detected in Field A, Block 3. Immediate inspection recommended.",
                category="alerts",
                read=True,
                action_url="/crop-health"
            ),
        ]
        
        # Check if notifications already exist
        existing_count = self.db.query(Notification).filter(
            Notification.organization_id == org_id,
            Notification.user_id == user_id
        ).count()
        
        if existing_count == 0:
            for notification in notifications:
                self.db.add(notification)
            return len(notifications)
        
        return 0
    
    def _seed_activity_logs(self, org_id: int, user_id: int) -> int:
        """Seed demo activity logs"""
        now = datetime.now(timezone.utc)
        
        activities = [
            ActivityLog(
                organization_id=org_id,
                user_id=user_id,
                action="login",
                details="Logged in from browser",
                ip_address="192.168.1.100"
            ),
            ActivityLog(
                organization_id=org_id,
                user_id=user_id,
                action="update_profile",
                details="Updated profile settings"
            ),
            ActivityLog(
                organization_id=org_id,
                user_id=user_id,
                action="create",
                entity_type="trial",
                entity_id="TRL-2025-001",
                details="Created trial TRL-2025-001"
            ),
        ]
        
        # Check if activity logs already exist
        existing_count = self.db.query(ActivityLog).filter(
            ActivityLog.organization_id == org_id,
            ActivityLog.user_id == user_id
        ).count()
        
        if existing_count == 0:
            for activity in activities:
                self.db.add(activity)
            return len(activities)
        
        return 0
    
    def clear(self) -> int:
        """Clear seeded user management data"""
        count = 0
        
        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()
        
        if not demo_org:
            return 0
        
        # Clear in reverse order of dependencies
        count += self.db.query(ActivityLog).filter(
            ActivityLog.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(TeamInvitation).filter(
            TeamInvitation.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(TeamMember).filter(
            TeamMember.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(Team).filter(
            Team.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(Role).filter(
            Role.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(Notification).filter(
            Notification.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(NotificationPreference).filter(
            NotificationPreference.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(QuietHours).filter(
            QuietHours.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(UserPreference).filter(
            UserPreference.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(UserProfile).filter(
            UserProfile.organization_id == demo_org.id
        ).delete()
        
        self.db.commit()
        return count

"""
Demo Users Seeder

Seeds demo user accounts for development and testing.
This seeder is controlled by SEED_DEMO_DATA setting.

Demo users are placed in the "Demo Organization" which contains
all demo/test data, keeping it separate from production data.

NOTE: Admin user is created by admin_user.py seeder (always runs).
This seeder only creates demo/test users.
"""

import logging

from app.core.config import settings
from app.core.security import get_password_hash

from .base import BaseSeeder, register_seeder
from .demo_germplasm import get_or_create_demo_organization


logger = logging.getLogger(__name__)


# Demo users - go into Demo Organization
# These are for development/testing only
DEMO_USERS = [
    {
        "email": "demo@bijmantra.org",
        "full_name": "Demo User",
        "is_active": True,
        "is_superuser": False,
    },
    {
        "email": "breeder@bijmantra.org",
        "full_name": "Demo Breeder",
        "is_active": True,
        "is_superuser": False,
    },
    {
        "email": "researcher@bijmantra.org",
        "full_name": "Demo Researcher",
        "is_active": True,
        "is_superuser": False,
    },
]


@register_seeder
class DemoUsersSeeder(BaseSeeder):
    """
    Seeds demo user accounts into Demo Organization.

    Controlled by SEED_DEMO_DATA setting - will not run in production.
    """

    name = "demo_users"
    description = "Demo user accounts for development/testing"

    def seed(self) -> int:
        """Seed demo users into the database."""
        from app.models.core import User

        # Get or create Demo Organization
        demo_org = get_or_create_demo_organization(self.db)

        count = 0

        for data in DEMO_USERS:
            existing = self.db.query(User).filter(User.email == data["email"]).first()
            if existing:
                # Update organization if user exists but is in wrong org
                if existing.organization_id != demo_org.id:
                    existing.organization_id = demo_org.id
                    logger.info(f"Moved {data['email']} to Demo Organization")
                    count += 1
                continue

            user = User(
                organization_id=demo_org.id,
                email=data["email"],
                full_name=data["full_name"],
                hashed_password=get_password_hash(settings.FIRST_DEMO_PASSWORD),
                is_active=data["is_active"],
                is_superuser=data["is_superuser"],
            )
            self.db.add(user)
            count += 1
            logger.info(f"Added demo user: {data['email']}")

        self.db.commit()
        logger.info(f"Seeded {count} demo users")
        return count

    def clear(self) -> int:
        """Clear demo users from Demo Organization"""
        from app.models.core import Organization, User
        from sqlalchemy import text

        demo_org = (
            self.db.query(Organization).filter(Organization.name == "Demo Organization").first()
        )

        if not demo_org:
            return 0

        # Only delete users we seeded (by email)
        demo_emails = [u["email"] for u in DEMO_USERS]

        # Get user IDs first so we can clean up FK-referencing tables
        demo_user_ids = [
            row[0]
            for row in self.db.query(User.id).filter(User.email.in_(demo_emails)).all()
        ]

        if not demo_user_ids:
            return 0

        # Get all workspace IDs owned by demo users (to cascade-delete workspace children)
        workspace_ids = [
            row[0]
            for row in self.db.execute(
                text("SELECT id FROM collaboration_workspaces WHERE owner_id = ANY(:ids)"),
                {"ids": demo_user_ids},
            ).fetchall()
        ]

        # Delete workspace child records first
        if workspace_ids:
            # Nullify nullable FKs to workspaces
            self.db.execute(
                text("UPDATE user_presence SET current_workspace_id = NULL WHERE current_workspace_id = ANY(:ids)"),
                {"ids": workspace_ids},
            )
            # Delete non-nullable FK children
            for child_table, child_col in [
                ("collaboration_activities", "workspace_id"),
                ("collaboration_comments", "workspace_id"),
                ("collaboration_tasks", "workspace_id"),
                ("workspace_members", "workspace_id"),
                ("conversations", "workspace_id"),
            ]:
                self.db.execute(
                    text(f"DELETE FROM {child_table} WHERE {child_col} = ANY(:ids)"),
                    {"ids": workspace_ids},
                )

            self.db.execute(
                text("DELETE FROM collaboration_workspaces WHERE owner_id = ANY(:ids)"),
                {"ids": demo_user_ids},
            )

        # Dynamically find all FK constraints referencing users(id) and delete/nullify them
        fk_query = text("""
            SELECT tc.table_name, kcu.column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.referential_constraints AS rc
                ON tc.constraint_name = rc.constraint_name
            JOIN information_schema.key_column_usage AS ccu
                ON rc.unique_constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND ccu.table_name = 'users'
              AND ccu.column_name = 'id'
            ORDER BY tc.table_name
        """)
        fk_refs = self.db.execute(fk_query).fetchall()

        for table_name, col_name in fk_refs:
            if table_name in ("users", "collaboration_workspaces"):
                continue
            try:
                self.db.execute(
                    text(f"DELETE FROM {table_name} WHERE {col_name} = ANY(:ids)"),
                    {"ids": demo_user_ids},
                )
            except Exception:
                try:
                    self.db.rollback()
                    self.db.execute(
                        text(f"UPDATE {table_name} SET {col_name} = NULL WHERE {col_name} = ANY(:ids)"),
                        {"ids": demo_user_ids},
                    )
                except Exception:
                    self.db.rollback()

        deleted = (
            self.db.query(User)
            .filter(User.email.in_(demo_emails))
            .delete(synchronize_session=False)
        )

        self.db.commit()
        logger.info(f"Cleared {deleted} demo users")
        return deleted

"""
Demo Users Seeder

Seeds demo user accounts for development and testing.
This seeder is controlled by SEED_DEMO_DATA setting.

Demo users are placed in the "Demo Organization" which contains
all demo/test data, keeping it separate from production data.

NOTE: Admin user is created by admin_user.py seeder (always runs).
This seeder only creates demo/test users.
"""

from sqlalchemy.orm import Session
from .base import BaseSeeder, register_seeder
from .demo_germplasm import get_or_create_demo_organization
from app.core.security import get_password_hash
import logging

logger = logging.getLogger(__name__)


# Demo users - go into Demo Organization
# These are for development/testing only
DEMO_USERS = [
    {
        "email": "demo@bijmantra.org",
        "full_name": "Demo User",
        "password": "Demo123!",
        "is_active": True,
        "is_superuser": False,
    },
    {
        "email": "breeder@bijmantra.org",
        "full_name": "Demo Breeder",
        "password": "Demo123!",
        "is_active": True,
        "is_superuser": False,
    },
    {
        "email": "researcher@bijmantra.org",
        "full_name": "Demo Researcher",
        "password": "Demo123!",
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
                hashed_password=get_password_hash(data["password"]),
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
        from app.models.core import User, Organization

        demo_org = self.db.query(Organization).filter(
            Organization.name == "Demo Organization"
        ).first()

        if not demo_org:
            return 0

        # Only delete users we seeded (by email)
        demo_emails = [u["email"] for u in DEMO_USERS]
        deleted = self.db.query(User).filter(
            User.email.in_(demo_emails)
        ).delete(synchronize_session=False)

        self.db.commit()
        logger.info(f"Cleared {deleted} demo users")
        return deleted

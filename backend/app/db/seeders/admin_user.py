"""
Admin User Seeder

Seeds the initial admin user for the application.
This seeder ALWAYS runs regardless of SEED_DEMO_DATA setting.

The admin user is required for:
- Initial system setup
- User management
- Organization creation

This is NOT demo data - it's the bootstrap admin account.
Password should be changed immediately after first login in production.
"""

from sqlalchemy.orm import Session
from .base import BaseSeeder, register_seeder
from app.core.security import get_password_hash
import logging
import os

logger = logging.getLogger(__name__)


def get_or_create_production_organization(db: Session):
    """Get or create the Production Organization for admin/real users"""
    from app.models.core import Organization

    org = db.query(Organization).filter(Organization.name == "BijMantra HQ").first()
    if not org:
        org = Organization(
            name="BijMantra HQ",
            description="Production organization for BijMantra administrators and real users.",
            contact_email="admin@bijmantra.org",
            website="https://bijmantra.org",
            is_active=True,
        )
        db.add(org)
        db.flush()
        logger.info(f"Created Production Organization 'BijMantra HQ' with id={org.id}")
    return org


@register_seeder
class AdminUserSeeder(BaseSeeder):
    """
    Seeds the initial admin user.
    
    This seeder ALWAYS runs - it is not controlled by SEED_DEMO_DATA.
    Every deployment needs an admin user for initial setup.
    
    In production, set ADMIN_PASSWORD environment variable.
    Default password is only for development.
    """

    name = "admin_user"
    description = "Initial admin user (always runs)"

    def should_run(self, env: str = "dev") -> bool:
        """
        Admin user should ALWAYS be created, even in production.
        Override base class to ignore SEED_DEMO_DATA setting.
        """
        return True

    def seed(self) -> int:
        """Seed admin user into the database."""
        from app.models.core import User

        # Get or create production organization
        prod_org = get_or_create_production_organization(self.db)

        # Check if admin already exists
        existing = self.db.query(User).filter(User.email == "admin@bijmantra.org").first()
        if existing:
            logger.info("Admin user already exists, skipping")
            return 0

        # Get password from environment or use default (dev only)
        admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")

        if os.environ.get("ENVIRONMENT") == "production" and admin_password == "Admin123!":
            logger.warning(
                "WARNING: Using default admin password in production! "
                "Set ADMIN_PASSWORD environment variable."
            )

        user = User(
            organization_id=prod_org.id,
            email="admin@bijmantra.org",
            full_name="System Administrator",
            hashed_password=get_password_hash(admin_password),
            is_active=True,
            is_superuser=True,
        )
        self.db.add(user)
        self.db.commit()

        logger.info("Created admin user: admin@bijmantra.org")
        return 1

    def clear(self) -> int:
        """
        Clear admin user.
        
        WARNING: This should rarely be called as admin is required.
        """
        from app.models.core import User

        deleted = self.db.query(User).filter(
            User.email == "admin@bijmantra.org"
        ).delete()

        self.db.commit()
        return deleted

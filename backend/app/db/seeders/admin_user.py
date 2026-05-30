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

import logging

import bcrypt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.demo_dataset import is_production_environment
from app.core.security import get_password_hash

from .base import BaseSeeder, register_seeder


logger = logging.getLogger(__name__)


def _password_matches(plain_password: str, hashed_password: str | None) -> bool:
    """Check a password hash without emitting authentication-failure logs from seeders."""
    if not hashed_password:
        return False

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (TypeError, ValueError):
        return False


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


def _ensure_keycloak_admin_identity(db: Session, user, organization) -> bool:
    """Map the configured Keycloak bootstrap admin subject to the local admin user."""
    if not settings.KEYCLOAK_BOOTSTRAP_ADMIN_SUBJECT:
        return False

    from app.models.core import AuthIdentity

    identity = (
        db.query(AuthIdentity)
        .filter(
            AuthIdentity.provider == "keycloak",
            AuthIdentity.issuer == settings.KEYCLOAK_ISSUER,
            AuthIdentity.subject == settings.KEYCLOAK_BOOTSTRAP_ADMIN_SUBJECT,
        )
        .first()
    )

    if not identity:
        db.add(
            AuthIdentity(
                organization_id=organization.id,
                user_id=user.id,
                provider="keycloak",
                issuer=settings.KEYCLOAK_ISSUER,
                subject=settings.KEYCLOAK_BOOTSTRAP_ADMIN_SUBJECT,
                email_at_login=user.email,
            )
        )
        return True

    changed = False
    if identity.organization_id != organization.id:
        identity.organization_id = organization.id
        changed = True
    if identity.user_id != user.id:
        identity.user_id = user.id
        changed = True
    if identity.email_at_login != user.email:
        identity.email_at_login = user.email
        changed = True

    return changed


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
    is_demo_data = False

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
        existing = self.db.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
        if existing:
            if is_production_environment(settings.ENVIRONMENT):
                identity_changed = _ensure_keycloak_admin_identity(self.db, existing, prod_org)
                if identity_changed:
                    self.db.commit()
                    logger.info("Mapped production admin user to configured Keycloak subject")
                    return 1

                logger.info("Admin user already exists, leaving production credentials unchanged")
                return 0

            repaired_fields: list[str] = []
            admin_password = settings.FIRST_SUPERUSER_PASSWORD

            if existing.organization_id != prod_org.id:
                existing.organization_id = prod_org.id
                repaired_fields.append("organization_id")
            if existing.full_name != "System Administrator":
                existing.full_name = "System Administrator"
                repaired_fields.append("full_name")
            if not existing.is_active:
                existing.is_active = True
                repaired_fields.append("is_active")
            if not existing.is_superuser:
                existing.is_superuser = True
                repaired_fields.append("is_superuser")
            if not _password_matches(admin_password, existing.hashed_password):
                existing.hashed_password = get_password_hash(admin_password)
                repaired_fields.append("hashed_password")

            identity_changed = _ensure_keycloak_admin_identity(self.db, existing, prod_org)

            if not repaired_fields and not identity_changed:
                logger.info("Admin user already exists and is usable")
                return 0

            self.db.commit()
            logger.info(
                "Repaired development admin user %s fields: %s",
                settings.FIRST_SUPERUSER,
                ", ".join(repaired_fields or ["keycloak_identity"]),
            )
            return 1

        # Use centralized settings password.
        admin_password = settings.FIRST_SUPERUSER_PASSWORD

        user = User(
            organization_id=prod_org.id,
            email=settings.FIRST_SUPERUSER,
            full_name="System Administrator",
            hashed_password=get_password_hash(admin_password),
            is_active=True,
            is_superuser=True,
        )
        self.db.add(user)
        self.db.flush()
        _ensure_keycloak_admin_identity(self.db, user, prod_org)
        self.db.commit()

        logger.info("Created admin user: %s", settings.FIRST_SUPERUSER)
        return 1

    def clear(self) -> int:
        """
        Clear admin user.

        WARNING: This should rarely be called as admin is required.
        """
        from app.models.core import User

        deleted = self.db.query(User).filter(User.email == settings.FIRST_SUPERUSER).delete()

        self.db.commit()
        return deleted

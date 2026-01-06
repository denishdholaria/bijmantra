"""
Users Seeder

Seeds user accounts into appropriate organizations:
- Demo user (demo@bijmantra.org) → Demo Organization
- Admin user (admin@bijmantra.org) → Production Organization (BijMantra HQ)

This ensures:
- Admin sees REAL data (empty database = empty UI)
- Demo user sees DEMO data (seeded demo records)
- Clear separation for development vs production testing
"""

from sqlalchemy.orm import Session
from .base import BaseSeeder, register_seeder
from .demo_germplasm import get_or_create_demo_organization
from app.core.security import get_password_hash
import logging

logger = logging.getLogger(__name__)


def get_or_create_production_organization(db: Session):
    """Get or create the Production Organization for admin/real users"""
    from app.models.core import Organization
    
    org = db.query(Organization).filter(Organization.name == "BijMantra HQ").first()
    if not org:
        org = Organization(
            name="BijMantra HQ",
            description="Production organization for BijMantra administrators and real users. Data here is production-ready.",
            contact_email="admin@bijmantra.org",
            website="https://bijmantra.org",
            is_active=True,
        )
        db.add(org)
        db.flush()
        logger.info(f"Created Production Organization 'BijMantra HQ' with id={org.id}")
    return org


# Demo users - go into Demo Organization
DEMO_USERS = [
    {
        "email": "demo@bijmantra.org",
        "full_name": "Demo User",
        "password": "demo123",
        "is_active": True,
        "is_superuser": False,
        "organization": "demo",  # Demo Organization
    },
]

# Production users - go into Production Organization
PRODUCTION_USERS = [
    {
        "email": "admin@bijmantra.org",
        "full_name": "System Administrator",
        "password": "admin123",
        "is_active": True,
        "is_superuser": True,
        "organization": "production",  # Production Organization
    },
]


@register_seeder
class DemoUsersSeeder(BaseSeeder):
    """Seeds user accounts into appropriate organizations"""
    
    name = "demo_users"
    description = "User accounts: demo/breeder → Demo Org, admin → Production Org"
    
    def seed(self) -> int:
        """Seed users into the database with proper organization separation."""
        from app.models.core import User
        
        # Get or create both organizations
        demo_org = get_or_create_demo_organization(self.db)
        prod_org = get_or_create_production_organization(self.db)
        
        count = 0
        
        # Seed demo users into Demo Organization
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
            logger.info(f"Added demo user: {data['email']} → Demo Organization")
        
        # Seed production users into Production Organization
        for data in PRODUCTION_USERS:
            existing = self.db.query(User).filter(User.email == data["email"]).first()
            if existing:
                # Update organization if user exists but is in wrong org
                if existing.organization_id != prod_org.id:
                    existing.organization_id = prod_org.id
                    logger.info(f"Moved {data['email']} to Production Organization (BijMantra HQ)")
                    count += 1
                continue
            
            user = User(
                organization_id=prod_org.id,
                email=data["email"],
                full_name=data["full_name"],
                hashed_password=get_password_hash(data["password"]),
                is_active=data["is_active"],
                is_superuser=data["is_superuser"],
            )
            self.db.add(user)
            count += 1
            logger.info(f"Added production user: {data['email']} → Production Organization")
        
        self.db.commit()
        logger.info(f"Seeded {count} users (demo → Demo Org, admin → Production Org)")
        return count
    
    def clear(self) -> int:
        """Clear seeded users (both demo and production)"""
        from app.models.core import User, Organization
        
        count = 0
        
        # Clear demo users
        demo_org = self.db.query(Organization).filter(Organization.name == "Demo Organization").first()
        if demo_org:
            demo_count = self.db.query(User).filter(User.organization_id == demo_org.id).delete()
            count += demo_count
            logger.info(f"Cleared {demo_count} users from Demo Organization")
        
        # Clear production users (but keep the org)
        prod_org = self.db.query(Organization).filter(Organization.name == "BijMantra HQ").first()
        if prod_org:
            prod_count = self.db.query(User).filter(User.organization_id == prod_org.id).delete()
            count += prod_count
            logger.info(f"Cleared {prod_count} users from Production Organization")
        
        self.db.commit()
        return count

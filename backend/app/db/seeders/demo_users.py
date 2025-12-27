"""
Demo Users Seeder

Seeds demo user accounts into the "Demo Organization" for sandboxed demo access.
Demo users can log in and explore Bijmantra without affecting production data.
"""

from sqlalchemy.orm import Session
from .base import BaseSeeder, register_seeder
from .demo_germplasm import get_or_create_demo_organization
from app.core.security import get_password_hash
import logging

logger = logging.getLogger(__name__)

# Demo users data
DEMO_USERS = [
    {
        "email": "demo@bijmantra.org",
        "full_name": "Demo User",
        "password": "demo123",  # Will be hashed
        "is_active": True,
        "is_superuser": False,
    },
    {
        "email": "breeder@bijmantra.org",
        "full_name": "Demo Breeder",
        "password": "breeder123",
        "is_active": True,
        "is_superuser": False,
    },
    {
        "email": "admin@bijmantra.org",
        "full_name": "Demo Admin",
        "password": "admin123",
        "is_active": True,
        "is_superuser": True,
    },
]


@register_seeder
class DemoUsersSeeder(BaseSeeder):
    """Seeds demo user accounts into Demo Organization"""
    
    name = "demo_users"
    description = "Demo user accounts (demo@bijmantra.org, breeder@bijmantra.org, admin@bijmantra.org)"
    
    def seed(self) -> int:
        """Seed demo users into the database."""
        from app.models.core import User
        
        # Get or create demo organization
        org = get_or_create_demo_organization(self.db)
        
        count = 0
        for data in DEMO_USERS:
            # Check if user already exists
            existing = self.db.query(User).filter(
                User.email == data["email"]
            ).first()
            
            if existing:
                logger.debug(f"User {data['email']} already exists, skipping")
                continue
            
            user = User(
                organization_id=org.id,
                email=data["email"],
                full_name=data["full_name"],
                hashed_password=get_password_hash(data["password"]),
                is_active=data["is_active"],
                is_superuser=data["is_superuser"],
            )
            self.db.add(user)
            count += 1
            logger.debug(f"Added user: {data['email']}")
        
        self.db.commit()
        logger.info(f"Seeded {count} demo users into Demo Organization")
        return count
    
    def clear(self) -> int:
        """Clear demo users from Demo Organization only"""
        from app.models.core import User, Organization
        
        # Get demo organization
        org = self.db.query(Organization).filter(Organization.name == "Demo Organization").first()
        if not org:
            return 0
        
        # Delete users from demo organization only
        count = self.db.query(User).filter(
            User.organization_id == org.id
        ).delete()
        
        self.db.commit()
        logger.info(f"Cleared {count} users from Demo Organization")
        return count

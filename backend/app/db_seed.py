"""
Database seed script
Creates initial organization and admin user
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.crud.core import organization as org_crud, user as user_crud
from app.schemas.core import OrganizationCreate, UserCreate


async def seed_database():
    """Seed database with initial data"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if organization already exists
            existing_org = await org_crud.get_by_name(db, "Default Organization")
            
            if not existing_org:
                print("Creating default organization...")
                org = await org_crud.create(
                    db,
                    obj_in=OrganizationCreate(
                        name="Default Organization",
                        description="Default organization for Bijmantra",
                        contact_email="admin@example.org"
                    )
                )
                await db.commit()
                print(f"✓ Created organization: {org.name} (ID: {org.id})")
            else:
                org = existing_org
                print(f"✓ Organization already exists: {org.name} (ID: {org.id})")
            
            # Check if admin user already exists
            existing_user = await user_crud.get_by_email(db, "admin@example.org")
            
            if not existing_user:
                print("Creating admin user...")
                user = await user_crud.create(
                    db,
                    obj_in=UserCreate(
                        email="admin@example.org",
                        password="admin123",  # Change this in production!
                        full_name="Admin User",
                        organization_id=org.id
                    )
                )
                # Make user superuser
                user.is_superuser = True
                db.add(user)
                await db.commit()
                print(f"✓ Created admin user: {user.email}")
                print("  Email: admin@example.org")
                print("  Password: admin123")
                print("  ⚠️  CHANGE THIS PASSWORD IN PRODUCTION!")
            else:
                print(f"✓ Admin user already exists: {existing_user.email}")
            
            print("\n✅ Database seeding completed successfully!")
            
        except Exception as e:
            print(f"❌ Error seeding database: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("🌱 Seeding database...")
    asyncio.run(seed_database())

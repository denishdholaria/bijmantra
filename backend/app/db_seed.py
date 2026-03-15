"""
Database seed script
Creates initial organization and admin user
"""

import asyncio
import secrets

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.crud.core import organization as org_crud
from app.crud.core import user as user_crud
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
                        contact_email=settings.FIRST_SUPERUSER,
                    ),
                )
                await db.commit()
                print(f"✓ Created organization: {org.name} (ID: {org.id})")
            else:
                org = existing_org
                print(f"✓ Organization already exists: {org.name} (ID: {org.id})")

            # Check if admin user already exists
            existing_user = await user_crud.get_by_email(db, settings.FIRST_SUPERUSER)

            if not existing_user:
                print("Creating admin user...")

                # Determine password (security check)
                password = settings.FIRST_SUPERUSER_PASSWORD
                if settings.ENVIRONMENT == "production" and password == "Admin123!":
                    password = secrets.token_urlsafe(16)
                    print("⚠️  Generated secure random password for production admin user")

                user = await user_crud.create(
                    db,
                    obj_in=UserCreate(
                        email=settings.FIRST_SUPERUSER,
                        password=password,
                        full_name="Admin User",
                        organization_id=org.id,
                    ),
                )
                # Make user superuser
                user.is_superuser = True
                db.add(user)
                await db.commit()
                print(f"✓ Created admin user: {user.email}")
                print(f"  Email: {settings.FIRST_SUPERUSER}")
                print(f"  Password: {password}")
                if password == "Admin123!":
                    print("  ⚠️  CHANGE THIS PASSWORD IN PRODUCTION!")
            else:
                print(f"✓ Admin user already exists: {existing_user.email}")

            if settings.SEED_DEMO_DATA:
                # Check if demo user already exists
                existing_demo = await user_crud.get_by_email(db, settings.FIRST_DEMO_USER)

                if not existing_demo:
                    print("Creating demo user...")
                    demo_user = await user_crud.create(
                        db,
                        obj_in=UserCreate(
                            email=settings.FIRST_DEMO_USER,
                            password=settings.FIRST_DEMO_PASSWORD,
                            full_name="Demo User",
                            organization_id=org.id,
                        ),
                    )
                    await db.commit()
                    print(f"✓ Created demo user: {demo_user.email}")
                    print(f"  Email: {settings.FIRST_DEMO_USER}")
                    print(f"  Password: {settings.FIRST_DEMO_PASSWORD}")
                else:
                    print(f"✓ Demo user already exists: {existing_demo.email}")
            else:
                 print("ℹ️  Skipping demo user creation (SEED_DEMO_DATA=False)")

            print("\n✅ Database seeding completed successfully!")

        except Exception as e:
            print(f"❌ Error seeding database: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("🌱 Seeding database...")
    asyncio.run(seed_database())

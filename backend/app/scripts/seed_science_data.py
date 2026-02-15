"""
Science Data Seed Script
Seeds the database with CropModels and Locations for science engine testing.
"""

import asyncio
import sys
import os

# Add parent directory to path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.core import Organization, Location
from app.models.biosimulation import CropModel
# Import environmental models to ensure they are registered for relationships
from app.models.environmental import EnvironmentalUnit, SoilProfile

async def seed_science_data():
    """Seed science engine data"""
    async with AsyncSessionLocal() as db:
        try:
            print("🌱 Seeding science data...")
            
            # 1. Get Organization
            # We assume organization ID 1 exists from db_seed.py,/Users/denish/.gemini/antigravity/brain/d9d9aeec-8823-4a0e-989c-a33d1f43fc5f/task.md but let's fetch it to be safe
            stmt = select(Organization).where(Organization.name == "Default Organization")
            result = await db.execute(stmt)
            org = result.scalar_one_or_none()
            
            if not org:
                # If not found, try ID 1 directly or fail
                org = await db.get(Organization, 1)
                if not org:
                    print("❌ Error: Default Organization not found. Run 'python db_seed.py' first.")
                    return

            print(f"Using Organization: {org.name} (ID: {org.id})")

            # 2. Seed Locations
            locations = [
                {
                    "location_db_id": "LOC_DEMO_001",
                    "location_name": "Demo Field - Punjab",
                    "country_name": "India",
                    "country_code": "IND",
                    "latitude": 30.9010,
                    "longitude": 75.8573,
                    "altitude": "244"
                }
            ]

            for loc_data in locations:
                stmt = select(Location).where(Location.location_db_id == loc_data["location_db_id"])
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    new_loc = Location(
                        organization_id=org.id,
                        location_db_id=loc_data["location_db_id"],
                        location_name=loc_data["location_name"],
                        country_name=loc_data["country_name"],
                        country_code=loc_data["country_code"],
                        altitude=loc_data["altitude"]
                        # Coordinates would need GeoAlchemy2 shape, skipping for basic sync
                    )
                    db.add(new_loc)
                    print(f"✓ Created location: {new_loc.location_name}")
                else:
                    print(f"✓ Location already exists: {existing.location_name}")

            # 3. Seed Crop Models
            crop_models = [
                {
                    "name": "Wheat - PBW 343",
                    "crop_name": "Wheat",
                    "description": "Popular spring wheat variety for North India",
                    "base_temp": 5.0,
                    "opt_temp": 22.0,
                    "max_temp": 35.0,
                    "gdd_emergence": 85.0,
                    "gdd_flowering": 950.0,
                    "gdd_maturity": 1850.0,
                    "rue": 1.4,
                    "harvest_index": 0.45
                },
                {
                    "name": "Rice - IR64",
                    "crop_name": "Rice",
                    "description": "High yielding Indica rice variety",
                    "base_temp": 10.0,
                    "opt_temp": 30.0,
                    "max_temp": 42.0,
                    "gdd_emergence": 100.0,
                    "gdd_flowering": 1100.0,
                    "gdd_maturity": 2100.0,
                    "rue": 1.6,
                    "harvest_index": 0.50
                }
            ]

            for model_data in crop_models:
                stmt = select(CropModel).where(CropModel.name == model_data["name"])
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    new_model = CropModel(
                        organization_id=org.id,
                        **model_data
                    )
                    db.add(new_model)
                    print(f"✓ Created crop model: {new_model.name}")
                else:
                    print(f"✓ Crop model already exists: {existing.name}")

            await db.commit()
            print("\n✅ Science data seeding completed successfully!")

        except Exception as e:
            print(f"❌ Error seeding science data: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_science_data())

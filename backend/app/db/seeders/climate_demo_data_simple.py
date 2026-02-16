"""
Climate-Smart Agriculture Demo Data Seeder (Simplified)

Creates minimal demo data for testing the frontend pages.

Run: python -m app.db.seeders.climate_demo_data_simple
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal


async def create_demo_data():
    """Create demo data using raw SQL for simplicity"""
    print("\n" + "="*60)
    print("Climate-Smart Agriculture Demo Data Seeder (Simplified)")
    print("="*60 + "\n")

    async with AsyncSessionLocal() as db:
        try:
            # Get demo organization ID
            result = await db.execute(
                text("SELECT id FROM organizations WHERE name = 'Demo Organization' LIMIT 1")
            )
            org_row = result.first()

            if not org_row:
                print("❌ Demo Organization not found. Please run main seeder first.")
                return

            org_id = org_row[0]
            print(f"Using organization ID: {org_id}\n")

            # Get location IDs
            result = await db.execute(
                text(f"SELECT id FROM locations WHERE organization_id = {org_id} LIMIT 10")
            )
            location_ids = [row[0] for row in result.fetchall()]

            if not location_ids:
                print("❌ No locations found. Please create locations first.")
                return

            print(f"Found {len(location_ids)} locations\n")

            # Create carbon stocks
            print("Creating carbon stocks...")
            base_date = datetime.now() - timedelta(days=365)
            carbon_count = 0

            for i, loc_id in enumerate(location_ids):
                for month in range(0, 12, 3):
                    measurement_date = (base_date + timedelta(days=month * 30)).date()
                    soil_carbon = 45.0 + (i * 5) + (month * 0.5)
                    veg_carbon = 15.0 + (i * 2) + (month * 0.3)
                    total_carbon = soil_carbon + veg_carbon

                    await db.execute(text(f"""
                        INSERT INTO carbon_stocks 
                        (organization_id, location_id, measurement_date, soil_carbon_stock, 
                         vegetation_carbon_stock, total_carbon_stock, measurement_type, 
                         confidence_level, measurement_depth_cm, created_at, updated_at)
                        VALUES 
                        ({org_id}, {loc_id}, '{measurement_date}', {soil_carbon}, 
                         {veg_carbon}, {total_carbon}, 'field_measured', 
                         0.85, 30, NOW(), NOW())
                    """))
                    carbon_count += 1

            await db.commit()
            print(f"Created {carbon_count} carbon stock records\n")

            # Create emission sources
            print("Creating emission sources...")
            emission_count = 0

            for i, loc_id in enumerate(location_ids[:7]):
                for month in range(0, 12, 4):
                    activity_date = (base_date + timedelta(days=month * 30)).date()

                    # Fertilizer
                    await db.execute(text(f"""
                        INSERT INTO emission_sources 
                        (organization_id, location_id, activity_date, category, source_name,
                         quantity, unit, co2e_emissions, created_at, updated_at)
                        VALUES 
                        ({org_id}, {loc_id}, '{activity_date}', 'fertilizer', 'Urea',
                         {100 + i*10}, 'kg', {587 + i*50}, NOW(), NOW())
                    """))
                    emission_count += 1

                    # Fuel
                    await db.execute(text(f"""
                        INSERT INTO emission_sources 
                        (organization_id, location_id, activity_date, category, source_name,
                         quantity, unit, co2e_emissions, created_at, updated_at)
                        VALUES 
                        ({org_id}, {loc_id}, '{activity_date}', 'fuel', 'Diesel',
                         {50 + i*5}, 'L', {134 + i*20}, NOW(), NOW())
                    """))
                    emission_count += 1

            await db.commit()
            print(f"Created {emission_count} emission source records\n")

            # Create impact metrics
            print("Creating impact metrics...")
            programs = ["Cotton Improvement", "Groundnut Enhancement", "Rice Breeding"]
            metric_count = 0

            for i, program in enumerate(programs):
                for quarter in range(4):
                    metric_date = (base_date + timedelta(days=quarter * 90)).date()
                    hectares = 5000 + (i * 2000) + (quarter * 500)
                    farmers = 500 + (i * 200) + (quarter * 50)
                    yield_imp = 15.0 + (i * 2) + (quarter * 0.5)
                    carbon_seq = 250 + (i * 100) + (quarter * 25)
                    emissions_red = 50000 + (i * 20000) + (quarter * 5000)

                    await db.execute(text(f"""
                        INSERT INTO impact_metrics 
                        (organization_id, program_name, metric_date, hectares_impacted,
                         farmers_reached, yield_improvement_percent, carbon_sequestered_tonnes,
                         emissions_reduced_kg, created_at, updated_at)
                        VALUES 
                        ({org_id}, '{program}', '{metric_date}', {hectares},
                         {farmers}, {yield_imp}, {carbon_seq}, {emissions_red}, NOW(), NOW())
                    """))
                    metric_count += 1

            await db.commit()
            print(f"Created {metric_count} impact metrics\n")

            # Create SDG indicators
            print("Creating SDG indicators...")
            sdg_data = [
                (2, "2.3.1", "Volume of production per labour unit", 5000, 4200, "kg per person"),
                (2, "2.4.1", "Sustainable agricultural practices", 80, 65, "percent"),
                (13, "13.2.1", "Climate change mitigation measures", 100, 72, "percent"),
                (15, "15.3.1", "Land degradation", 10, 15, "percent"),
                (17, "17.6.1", "Science cooperation agreements", 20, 18, "number"),
            ]

            measurement_date = (datetime.now() - timedelta(days=30)).date()

            for goal, code, name, target, current, unit in sdg_data:
                await db.execute(text(f"""
                    INSERT INTO sdg_indicators 
                    (organization_id, program_name, sdg_goal, indicator_code, indicator_name,
                     target_value, current_value, unit, measurement_date, created_at, updated_at)
                    VALUES 
                    ({org_id}, 'Climate-Smart Agriculture Program', {goal}, '{code}', '{name}',
                     {target}, {current}, '{unit}', '{measurement_date}', NOW(), NOW())
                """))

            await db.commit()
            print(f"Created 5 SDG indicators\n")

            # Create variety releases
            print("Creating variety releases...")
            varieties = [
                ("GJ-39", "Cotton", 730, 15000, 3000, 18.5),
                ("GG-2", "Groundnut", 1095, 12000, 2500, 22.3),
                ("GR-11", "Rice", 1460, 25000, 5000, 16.8),
                ("GW-322", "Wheat", 1825, 18000, 3500, 20.1),
                ("GM-6", "Maize", 365, 8000, 1500, 25.4),
            ]

            for name, crop, days_ago, hectares, farmers, yield_imp in varieties:
                release_date = (datetime.now() - timedelta(days=days_ago)).date()
                await db.execute(text(f"""
                    INSERT INTO variety_releases 
                    (organization_id, variety_name, crop_type, release_date, hectares_adopted,
                     farmers_reached, yield_improvement_percent, created_at, updated_at)
                    VALUES 
                    ({org_id}, '{name}', '{crop}', '{release_date}', {hectares},
                     {farmers}, {yield_imp}, NOW(), NOW())
                """))

            await db.commit()
            print(f"Created 5 variety releases\n")

            print("="*60)
            print("✅ Demo data creation complete!")
            print("="*60)
            print("\nSummary:")
            print(f"- {carbon_count} carbon stock records")
            print(f"- {emission_count} emission sources")
            print(f"- {metric_count} impact metrics")
            print("- 5 SDG indicators")
            print("- 5 variety releases")
            print(f"\nTotal: {carbon_count + emission_count + metric_count + 10} records created")
            print("\nYou can now view the data at:")
            print("- http://localhost:5173/earth-systems/carbon")
            print("- http://localhost:5173/earth-systems/sustainability")
            print()

        except Exception as e:
            print(f"\n❌ Error creating demo data: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_demo_data())

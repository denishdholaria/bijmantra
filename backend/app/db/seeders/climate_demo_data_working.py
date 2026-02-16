"""
Climate-Smart Agriculture Demo Data Seeder (Working Version)

Creates demo data using correct ENUM values from database.

Run: python -m app.db.seeders.climate_demo_data_working
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal


async def create_demo_data():
    """Create demo data with correct ENUM casting"""
    print("\n" + "="*60)
    print("Climate-Smart Agriculture Demo Data Seeder")
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
            print(f"✓ Using organization ID: {org_id}\n")

            # Get location IDs
            result = await db.execute(
                text(f"SELECT id FROM locations WHERE organization_id = {org_id} LIMIT 10")
            )
            location_ids = [row[0] for row in result.fetchall()]

            if not location_ids:
                print("❌ No locations found. Please create locations first.")
                return

            print(f"✓ Found {len(location_ids)} locations\n")

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
                    mtype = 'FIELD_MEASURED' if month % 6 == 0 else 'SATELLITE_ESTIMATED'

                    await db.execute(text(f"""
                        INSERT INTO carbon_stocks 
                        (organization_id, location_id, measurement_date, soil_carbon_stock, 
                         vegetation_carbon_stock, total_carbon_stock, measurement_type, 
                         confidence_level, measurement_depth_cm, created_at, updated_at)
                        VALUES 
                        ({org_id}, {loc_id}, '{measurement_date}', {soil_carbon}, 
                         {veg_carbon}, {total_carbon}, '{mtype}'::carbonmeasurementtype, 
                         0.85, 30, NOW(), NOW())
                    """))
                    carbon_count += 1

            await db.commit()
            print(f"✓ Created {carbon_count} carbon stock records\n")

            # Create carbon measurements
            print("Creating carbon measurements...")
            measurement_count = 0

            for i, loc_id in enumerate(location_ids[:5]):
                for day in range(0, 180, 30):
                    measurement_date = (base_date + timedelta(days=day)).date()
                    carbon_value = 2.0 + (i * 0.3) + (day * 0.001)

                    await db.execute(text(f"""
                        INSERT INTO carbon_measurements 
                        (organization_id, location_id, measurement_date, measurement_type,
                         carbon_value, unit, depth_from_cm, depth_to_cm, bulk_density,
                         method, notes, created_at, updated_at)
                        VALUES 
                        ({org_id}, {loc_id}, '{measurement_date}', 'SOIL_ORGANIC'::carbonmeasurementtype,
                         {carbon_value}, 'percent', 0, 30, 1.35,
                         'Walkley-Black', 'Soil organic carbon measurement', NOW(), NOW())
                    """))
                    measurement_count += 1

            await db.commit()
            print(f"✓ Created {measurement_count} carbon measurements\n")

            # Create emission sources
            print("Creating emission sources...")
            emission_count = 0

            emission_data = [
                ('FERTILIZER', 'Urea', 100, 'kg', 587),
                ('FUEL', 'Diesel', 50, 'L', 134),
                ('IRRIGATION', 'Grid Electricity', 1000, 'kWh', 820),
            ]

            for i, loc_id in enumerate(location_ids[:7]):
                for month in range(0, 12, 4):
                    activity_date = (base_date + timedelta(days=month * 30)).date()

                    for category, source_name, quantity, unit, co2e in emission_data:
                        await db.execute(text(f"""
                            INSERT INTO emission_sources 
                            (organization_id, location_id, activity_date, category, source_name,
                             quantity, unit, co2e_emissions, created_at, updated_at)
                            VALUES 
                            ({org_id}, {loc_id}, '{activity_date}', '{category}'::emissioncategory, '{source_name}',
                             {quantity + i*10}, '{unit}', {co2e + i*50}, NOW(), NOW())
                        """))
                        emission_count += 1

            await db.commit()
            print(f"✓ Created {emission_count} emission source records\n")

            # Create emission factors
            print("Creating emission factors...")
            factors = [
                ('Nitrogen Fertilizer', 'FERTILIZER', 5.87, 'kg CO2e per kg N', 'IPCC 2006 Guidelines'),
                ('Phosphorus Fertilizer', 'FERTILIZER', 0.20, 'kg CO2e per kg P2O5', 'IPCC 2006 Guidelines'),
                ('Diesel Combustion', 'FUEL', 2.68, 'kg CO2e per liter', 'IPCC 2006 Guidelines'),
                ('Grid Electricity', 'IRRIGATION', 0.82, 'kg CO2e per kWh', 'CEA India 2023'),
            ]

            for name, category, factor, unit, reference in factors:
                await db.execute(text(f"""
                    INSERT INTO emission_factors 
                    (organization_id, source_name, category, factor_value, unit, source_reference, created_at, updated_at)
                    VALUES 
                    ({org_id}, '{name}', '{category}'::emissioncategory, {factor}, '{unit}', '{reference}', NOW(), NOW())
                """))

            await db.commit()
            print(f"✓ Created 4 emission factors\n")

            # Create impact metrics
            print("Creating impact metrics...")
            metric_types = [
                ('HECTARES', 'Hectares Impacted', 5000, 'hectares'),
                ('FARMERS', 'Farmers Reached', 500, 'farmers'),
                ('YIELD_IMPROVEMENT', 'Yield Improvement', 15.0, 'percent'),
                ('CARBON_SEQUESTERED', 'Carbon Sequestered', 250, 'tonnes'),
            ]
            metric_count = 0

            for i in range(3):  # 3 quarters
                for mtype, mname, base_value, unit in metric_types:
                    metric_date = (base_date + timedelta(days=i * 90)).date()
                    value = base_value + (i * base_value * 0.1)

                    await db.execute(text(f"""
                        INSERT INTO impact_metrics 
                        (organization_id, metric_type, metric_name, metric_value, unit,
                         measurement_date, geographic_scope, beneficiaries, created_at, updated_at)
                        VALUES 
                        ({org_id}, '{mtype}'::metrictype, '{mname}', {value}, '{unit}',
                         '{metric_date}', 'Gujarat State', 500, NOW(), NOW())
                    """))
                    metric_count += 1

            await db.commit()
            print(f"✓ Created {metric_count} impact metrics\n")

            # Create SDG indicators
            print("Creating SDG indicators...")
            sdg_data = [
                ('SDG_2', '2.3.1', 'Volume of production per labour unit', 5000, 'kg per person'),
                ('SDG_2', '2.4.1', 'Sustainable agricultural practices', 80, 'percent'),
                ('SDG_13', '13.2.1', 'Climate change mitigation measures', 100, 'percent'),
                ('SDG_15', '15.3.1', 'Land degradation reduction', 10, 'percent'),
                ('SDG_17', '17.6.1', 'Science cooperation agreements', 20, 'number'),
            ]

            measurement_date = (datetime.now() - timedelta(days=30)).date()

            for goal, code, name, value, unit in sdg_data:
                await db.execute(text(f"""
                    INSERT INTO sdg_indicators 
                    (organization_id, sdg_goal, indicator_code, indicator_name,
                     contribution_value, unit, measurement_date, created_at, updated_at)
                    VALUES 
                    ({org_id}, '{goal}'::sdggoal, '{code}', '{name}',
                     {value}, '{unit}', '{measurement_date}', NOW(), NOW())
                """))

            await db.commit()
            print(f"✓ Created 5 SDG indicators\n")

            # Create germplasm for variety releases
            print("Creating germplasm records...")
            germplasm_data = [
                ('GJ-39', 'Cotton', 'Gossypium hirsutum'),
                ('GG-2', 'Groundnut', 'Arachis hypogaea'),
                ('GR-11', 'Rice', 'Oryza sativa'),
                ('GW-322', 'Wheat', 'Triticum aestivum'),
                ('GM-6', 'Maize', 'Zea mays'),
            ]

            germplasm_ids = []
            for name, common_name, species in germplasm_data:
                result = await db.execute(text(f"""
                    INSERT INTO germplasm 
                    (organization_id, germplasm_name, common_crop_name, species, 
                     created_at, updated_at)
                    VALUES 
                    ({org_id}, '{name}', '{common_name}', '{species}', 
                     NOW(), NOW())
                    RETURNING id
                """))
                germ_id = result.scalar()
                germplasm_ids.append((germ_id, name, common_name))

            await db.commit()
            print(f"✓ Created {len(germplasm_ids)} germplasm records\n")

            # Create variety releases
            print("Creating variety releases...")
            varieties = [
                (germplasm_ids[0], 730, 15000, 3000, 18.5),   # GJ-39 Cotton
                (germplasm_ids[1], 1095, 12000, 2500, 22.3),  # GG-2 Groundnut
                (germplasm_ids[2], 1460, 25000, 5000, 16.8),  # GR-11 Rice
                (germplasm_ids[3], 1825, 18000, 3500, 20.1),  # GW-322 Wheat
                (germplasm_ids[4], 365, 8000, 1500, 25.4),    # GM-6 Maize
            ]

            for (germ_id, name, crop), days_ago, hectares, farmers, yield_imp in zip(germplasm_ids, [730, 1095, 1460, 1825, 365], [15000, 12000, 25000, 18000, 8000], [3000, 2500, 5000, 3500, 1500], [18.5, 22.3, 16.8, 20.1, 25.4]):
                release_date = (datetime.now() - timedelta(days=days_ago)).date()
                await db.execute(text(f"""
                    INSERT INTO variety_releases 
                    (organization_id, germplasm_id, release_name, release_date, release_status,
                     country, releasing_authority, expected_adoption_ha, actual_adoption_ha,
                     created_at, updated_at)
                    VALUES 
                    ({org_id}, {germ_id}, '{name}', '{release_date}', 'RELEASED'::releasestatus,
                     'India', 'Gujarat Agricultural University', {hectares}, {hectares * 0.8},
                     NOW(), NOW())
                """))

            await db.commit()
            print(f"✓ Created 5 variety releases\n")

            # Create policy adoptions
            print("Creating policy adoptions...")
            policies = [
                ('Soil Health Card Scheme', 'NATIONAL', 1095, 'Ministry of Agriculture', 'India', 50000),
                ('PM Fasal Bima Yojana', 'NATIONAL', 1460, 'Ministry of Agriculture', 'India', 75000),
                ('Gujarat Climate Action Plan', 'REGIONAL', 730, 'Gujarat Government', 'India', 25000),
            ]

            for name, level, days_ago, agency, country, farmers in policies:
                adoption_date = (datetime.now() - timedelta(days=days_ago)).date()
                await db.execute(text(f"""
                    INSERT INTO policy_adoptions 
                    (organization_id, policy_name, adoption_date, adoption_level,
                     country, government_body, target_farmers, created_at, updated_at)
                    VALUES 
                    ({org_id}, '{name}', '{adoption_date}', '{level}'::adoptionlevel,
                     '{country}', '{agency}', {farmers}, NOW(), NOW())
                """))

            await db.commit()
            print(f"✓ Created 3 policy adoptions\n")

            print("="*60)
            print("✅ Demo data creation complete!")
            print("="*60)
            print("\nSummary:")
            print(f"- {carbon_count} carbon stock records")
            print(f"- {measurement_count} carbon measurements")
            print(f"- {emission_count} emission sources")
            print("- 4 emission factors")
            print(f"- {metric_count} impact metrics")
            print("- 5 SDG indicators")
            print("- 5 germplasm records")
            print("- 5 variety releases")
            print("- 3 policy adoptions")
            total = carbon_count + measurement_count + emission_count + 4 + metric_count + 5 + 5 + 3
            print(f"\nTotal: {total} records created")
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

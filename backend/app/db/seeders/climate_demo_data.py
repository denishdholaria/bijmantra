"""
Climate-Smart Agriculture Demo Data Seeder

Creates realistic demo data for:
- Carbon stocks and measurements
- Emission sources
- Variety footprints
- Impact metrics
- SDG indicators
- Variety releases
- Policy adoptions

Run: python -m app.db.seeders.climate_demo_data
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.climate.carbon_monitoring import CarbonStock, CarbonMeasurement
from app.models.climate.emissions import EmissionSource, EmissionFactor, VarietyFootprint
from app.models.climate.impact_metrics import (
    ImpactMetric, SDGIndicator, VarietyRelease, PolicyAdoption
)
from app.models.core import Organization, Location


async def get_demo_organization(db: AsyncSession) -> Organization:
    """Get or create Demo Organization"""
    result = await db.execute(
        select(Organization).where(Organization.name == "Demo Organization")
    )
    org = result.scalar_one_or_none()

    if not org:
        org = Organization(
            name="Demo Organization",
            description="Demo organization for Climate-Smart Agriculture",
            contact_email="demo@bijmantra.org",
            website="https://bijmantra.org",
            is_active=True
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)

    return org


async def get_demo_locations(db: AsyncSession, org_id: int, count: int = 10) -> list[Location]:
    """Get or create demo locations"""
    result = await db.execute(
        select(Location)
        .where(Location.organization_id == org_id)
        .limit(count)
    )
    locations = list(result.scalars().all())

    if len(locations) < count:
        # Create additional locations if needed
        location_data = [
            {"name": "Junagadh Research Station", "country": "India"},
            {"name": "Anand Agricultural University", "country": "India"},
            {"name": "Navsari Research Farm", "country": "India"},
            {"name": "Vadodara Experimental Site", "country": "India"},
            {"name": "Rajkot Field Station", "country": "India"},
            {"name": "Bhavnagar Coastal Farm", "country": "India"},
            {"name": "Surat Valley Site", "country": "India"},
            {"name": "Gandhinagar Research Hub", "country": "India"},
            {"name": "Mehsana Dryland Station", "country": "India"},
            {"name": "Kutch Arid Zone Farm", "country": "India"},
        ]

        for i in range(len(locations), count):
            loc_data = location_data[i % len(location_data)]
            location = Location(
                organization_id=org_id,
                location_name=f"{loc_data['name']} {i+1}",
                location_type="research_station",
                country_name=loc_data['country']
            )
            db.add(location)
            locations.append(location)

        await db.commit()
        for loc in locations:
            await db.refresh(loc)

    return locations[:count]


async def create_carbon_stocks(db: AsyncSession, org_id: int, locations: list[Location]):
    """Create carbon stock records"""
    print("Creating carbon stocks...")

    base_date = datetime.now() - timedelta(days=365)

    for i, location in enumerate(locations):
        # Create 4 measurements over the past year for each location
        for month in range(0, 12, 3):
            measurement_date = base_date + timedelta(days=month * 30)

            # Simulate increasing carbon stocks over time
            soil_carbon = 45.0 + (i * 5) + (month * 0.5)
            vegetation_carbon = 15.0 + (i * 2) + (month * 0.3)

            stock = CarbonStock(
                organization_id=org_id,
                location_id=location.id,
                measurement_date=measurement_date.date(),
                soil_carbon_stock=soil_carbon,
                vegetation_carbon_stock=vegetation_carbon,
                total_carbon_stock=soil_carbon + vegetation_carbon,
                measurement_type="field_measured" if month % 6 == 0 else "satellite_estimated",
                confidence_level=0.85 if month % 6 == 0 else 0.70,
                measurement_depth_cm=30
            )
            db.add(stock)

    await db.commit()
    print(f"Created {len(locations) * 4} carbon stock records")


async def create_carbon_measurements(db: AsyncSession, org_id: int, locations: list[Location]):
    """Create detailed carbon measurements"""
    print("Creating carbon measurements...")

    base_date = datetime.now() - timedelta(days=180)

    for i, location in enumerate(locations[:5]):  # First 5 locations
        # Create 10 measurements over past 6 months
        for day in range(0, 180, 18):
            measurement_date = base_date + timedelta(days=day)

            # Soil organic carbon percentage
            soc_percent = 2.0 + (i * 0.3) + (day * 0.001)

            measurement = CarbonMeasurement(
                organization_id=org_id,
                location_id=location.id,
                measurement_date=measurement_date.date(),
                measurement_type="soil_organic",
                carbon_value=soc_percent,
                unit="percent",
                depth_from_cm=0,
                depth_to_cm=30,
                bulk_density=1.35,
                method="Walkley-Black" if day % 36 == 0 else "field_test",
                notes=f"Depth 0-30cm at {location.location_name}"
            )
            db.add(measurement)

    await db.commit()
    print("Created 50 carbon measurements")


async def create_emission_sources(db: AsyncSession, org_id: int, locations: list[Location]):
    """Create emission source records"""
    print("Creating emission sources...")

    base_date = datetime.now() - timedelta(days=365)

    emission_types = [
        ("fertilizer", {"n_kg": 100, "p_kg": 50, "k_kg": 30}),
        ("fuel", {"diesel_liters": 50, "petrol_liters": 20}),
        ("irrigation", {"kwh": 1000, "energy_source": "grid"}),
    ]

    for i, location in enumerate(locations[:7]):  # First 7 locations
        for month in range(0, 12, 4):
            for emission_type, activity_data in emission_types:
                emission_date = base_date + timedelta(days=month * 30)

                # Calculate emissions based on type
                if emission_type == "fertilizer":
                    co2e = (activity_data["n_kg"] * 5.87) + (activity_data["p_kg"] * 0.2) + (activity_data["k_kg"] * 0.15)
                elif emission_type == "fuel":
                    co2e = (activity_data["diesel_liters"] * 2.68) + (activity_data.get("petrol_liters", 0) * 2.31)
                else:  # irrigation
                    co2e = activity_data["kwh"] * 0.82

                source = EmissionSource(
                    organization_id=org_id,
                    location_id=location.id,
                    emission_date=emission_date,
                    source_type=emission_type,
                    activity_data=activity_data,
                    co2e_kg=Decimal(str(co2e)),
                    calculation_method="ipcc_tier1",
                    notes=f"{emission_type.title()} emissions at {location.location_name}"
                )
                db.add(source)

    await db.commit()
    print("Created 63 emission source records")


async def create_emission_factors(db: AsyncSession, org_id: int):
    """Create emission factor reference data"""
    print("Creating emission factors...")

    factors = [
        {
            "factor_name": "Nitrogen Fertilizer",
            "source_type": "fertilizer",
            "emission_factor": Decimal("5.87"),
            "unit": "kg CO2e per kg N",
            "reference": "IPCC 2006 Guidelines",
            "notes": "Includes production and N2O emissions (GWP 298)"
        },
        {
            "factor_name": "Phosphorus Fertilizer",
            "source_type": "fertilizer",
            "emission_factor": Decimal("0.20"),
            "unit": "kg CO2e per kg P2O5",
            "reference": "IPCC 2006 Guidelines",
            "notes": "Production emissions only"
        },
        {
            "factor_name": "Potassium Fertilizer",
            "source_type": "fertilizer",
            "emission_factor": Decimal("0.15"),
            "unit": "kg CO2e per kg K2O",
            "reference": "IPCC 2006 Guidelines",
            "notes": "Production emissions only"
        },
        {
            "factor_name": "Diesel Combustion",
            "source_type": "fuel",
            "emission_factor": Decimal("2.68"),
            "unit": "kg CO2e per liter",
            "reference": "IPCC 2006 Guidelines",
            "notes": "Combustion emissions"
        },
        {
            "factor_name": "Grid Electricity (India)",
            "source_type": "irrigation",
            "emission_factor": Decimal("0.82"),
            "unit": "kg CO2e per kWh",
            "reference": "CEA India 2023",
            "notes": "National grid average"
        },
    ]

    for factor_data in factors:
        factor = EmissionFactor(
            organization_id=org_id,
            **factor_data
        )
        db.add(factor)

    await db.commit()
    print("Created 5 emission factors")


async def create_variety_footprints(db: AsyncSession, org_id: int):
    """Create variety carbon footprint records"""
    print("Creating variety footprints...")

    varieties = [
        {"name": "GJ-39", "crop": "Cotton", "footprint": 450, "yield": 2.5},
        {"name": "GG-2", "crop": "Groundnut", "footprint": 320, "yield": 3.2},
        {"name": "GR-11", "crop": "Rice", "footprint": 580, "yield": 5.8},
        {"name": "GW-322", "crop": "Wheat", "footprint": 420, "yield": 4.5},
        {"name": "GM-6", "crop": "Maize", "footprint": 380, "yield": 6.2},
    ]

    for var_data in varieties:
        footprint = VarietyFootprint(
            organization_id=org_id,
            variety_name=var_data["name"],
            crop_type=var_data["crop"],
            carbon_footprint_kg_co2e=Decimal(str(var_data["footprint"])),
            functional_unit="per hectare",
            system_boundary="cradle_to_farm_gate",
            assessment_year=2024,
            average_yield=Decimal(str(var_data["yield"])),
            yield_unit="tonnes per hectare",
            notes=f"LCA assessment for {var_data['name']}"
        )
        db.add(footprint)

    await db.commit()
    print("Created 5 variety footprints")


async def create_impact_metrics(db: AsyncSession, org_id: int):
    """Create impact metric records"""
    print("Creating impact metrics...")

    base_date = datetime.now() - timedelta(days=365)

    programs = ["Cotton Improvement", "Groundnut Enhancement", "Rice Breeding"]

    for i, program_name in enumerate(programs):
        for quarter in range(4):
            metric_date = base_date + timedelta(days=quarter * 90)

            metric = ImpactMetric(
                organization_id=org_id,
                program_name=program_name,
                metric_date=metric_date,
                hectares_impacted=Decimal(str(5000 + (i * 2000) + (quarter * 500))),
                farmers_reached=500 + (i * 200) + (quarter * 50),
                yield_improvement_percent=Decimal(str(15.0 + (i * 2) + (quarter * 0.5))),
                carbon_sequestered_tonnes=Decimal(str(250 + (i * 100) + (quarter * 25))),
                emissions_reduced_kg=Decimal(str(50000 + (i * 20000) + (quarter * 5000))),
                notes=f"Q{quarter+1} impact for {program_name}"
            )
            db.add(metric)

    await db.commit()
    print("Created 12 impact metrics")


async def create_sdg_indicators(db: AsyncSession, org_id: int):
    """Create SDG indicator records"""
    print("Creating SDG indicators...")

    indicators = [
        {
            "sdg_goal": 2,
            "indicator_code": "2.3.1",
            "indicator_name": "Volume of production per labour unit",
            "target_value": Decimal("5000"),
            "current_value": Decimal("4200"),
            "unit": "kg per person",
            "measurement_date": datetime.now() - timedelta(days=30),
            "notes": "Agricultural productivity indicator"
        },
        {
            "sdg_goal": 2,
            "indicator_code": "2.4.1",
            "indicator_name": "Proportion of agricultural area under sustainable practices",
            "target_value": Decimal("80"),
            "current_value": Decimal("65"),
            "unit": "percent",
            "measurement_date": datetime.now() - timedelta(days=30),
            "notes": "Sustainable agriculture adoption"
        },
        {
            "sdg_goal": 13,
            "indicator_code": "13.2.1",
            "indicator_name": "Climate change mitigation measures",
            "target_value": Decimal("100"),
            "current_value": Decimal("72"),
            "unit": "percent",
            "measurement_date": datetime.now() - timedelta(days=30),
            "notes": "Climate action implementation"
        },
        {
            "sdg_goal": 15,
            "indicator_code": "15.3.1",
            "indicator_name": "Proportion of land that is degraded",
            "target_value": Decimal("10"),
            "current_value": Decimal("15"),
            "unit": "percent",
            "measurement_date": datetime.now() - timedelta(days=30),
            "notes": "Land degradation neutrality"
        },
        {
            "sdg_goal": 17,
            "indicator_code": "17.6.1",
            "indicator_name": "Science and technology cooperation agreements",
            "target_value": Decimal("20"),
            "current_value": Decimal("18"),
            "unit": "number",
            "measurement_date": datetime.now() - timedelta(days=30),
            "notes": "Partnership for sustainable development"
        },
    ]

    for indicator_data in indicators:
        indicator = SDGIndicator(
            organization_id=org_id,
            program_name="Climate-Smart Agriculture Program",
            **indicator_data
        )
        db.add(indicator)

    await db.commit()
    print("Created 5 SDG indicators")


async def create_variety_releases(db: AsyncSession, org_id: int):
    """Create variety release records"""
    print("Creating variety releases...")

    releases = [
        {
            "variety_name": "GJ-39",
            "crop_type": "Cotton",
            "release_date": datetime.now() - timedelta(days=730),
            "hectares_adopted": Decimal("15000"),
            "farmers_reached": 3000,
            "yield_improvement_percent": Decimal("18.5"),
            "notes": "High-yielding Bt cotton variety"
        },
        {
            "variety_name": "GG-2",
            "crop_type": "Groundnut",
            "release_date": datetime.now() - timedelta(days=1095),
            "hectares_adopted": Decimal("12000"),
            "farmers_reached": 2500,
            "yield_improvement_percent": Decimal("22.3"),
            "notes": "Drought-tolerant groundnut"
        },
        {
            "variety_name": "GR-11",
            "crop_type": "Rice",
            "release_date": datetime.now() - timedelta(days=1460),
            "hectares_adopted": Decimal("25000"),
            "farmers_reached": 5000,
            "yield_improvement_percent": Decimal("16.8"),
            "notes": "Salt-tolerant rice variety"
        },
        {
            "variety_name": "GW-322",
            "crop_type": "Wheat",
            "release_date": datetime.now() - timedelta(days=1825),
            "hectares_adopted": Decimal("18000"),
            "farmers_reached": 3500,
            "yield_improvement_percent": Decimal("20.1"),
            "notes": "Heat-tolerant wheat"
        },
        {
            "variety_name": "GM-6",
            "crop_type": "Maize",
            "release_date": datetime.now() - timedelta(days=365),
            "hectares_adopted": Decimal("8000"),
            "farmers_reached": 1500,
            "yield_improvement_percent": Decimal("25.4"),
            "notes": "High-protein maize variety"
        },
    ]

    for release_data in releases:
        release = VarietyRelease(
            organization_id=org_id,
            **release_data
        )
        db.add(release)

    await db.commit()
    print("Created 5 variety releases")


async def create_policy_adoptions(db: AsyncSession, org_id: int):
    """Create policy adoption records"""
    print("Creating policy adoptions...")

    adoptions = [
        {
            "policy_name": "Soil Health Card Scheme",
            "policy_type": "national",
            "adoption_date": datetime.now() - timedelta(days=1095),
            "implementing_agency": "Ministry of Agriculture, Government of India",
            "geographic_scope": "National",
            "farmers_benefited": 50000,
            "notes": "Promotes soil testing and balanced fertilizer use"
        },
        {
            "policy_name": "Pradhan Mantri Fasal Bima Yojana",
            "policy_type": "national",
            "adoption_date": datetime.now() - timedelta(days=1460),
            "implementing_agency": "Ministry of Agriculture, Government of India",
            "geographic_scope": "National",
            "farmers_benefited": 75000,
            "notes": "Crop insurance scheme for climate risk management"
        },
        {
            "policy_name": "Gujarat Climate Change Action Plan",
            "policy_type": "state",
            "adoption_date": datetime.now() - timedelta(days=730),
            "implementing_agency": "Gujarat State Government",
            "geographic_scope": "Gujarat State",
            "farmers_benefited": 25000,
            "notes": "State-level climate adaptation strategies"
        },
    ]

    for adoption_data in adoptions:
        adoption = PolicyAdoption(
            organization_id=org_id,
            **adoption_data
        )
        db.add(adoption)

    await db.commit()
    print("Created 3 policy adoptions")


async def main():
    """Main seeder function"""
    print("\n" + "="*60)
    print("Climate-Smart Agriculture Demo Data Seeder")
    print("="*60 + "\n")

    async with AsyncSessionLocal() as db:
        try:
            # Get demo organization
            org = await get_demo_organization(db)
            print(f"Using organization: {org.name} (ID: {org.id})\n")

            # Get demo locations
            locations = await get_demo_locations(db, org.id, count=10)
            print(f"Using {len(locations)} locations\n")

            # Create all demo data
            await create_carbon_stocks(db, org.id, locations)
            await create_carbon_measurements(db, org.id, locations)
            await create_emission_sources(db, org.id, locations)
            await create_emission_factors(db, org.id)
            await create_variety_footprints(db, org.id)
            await create_impact_metrics(db, org.id)
            await create_sdg_indicators(db, org.id)
            await create_variety_releases(db, org.id)
            await create_policy_adoptions(db, org.id)

            print("\n" + "="*60)
            print("✅ Demo data creation complete!")
            print("="*60)
            print("\nSummary:")
            print("- 40 carbon stock records")
            print("- 50 carbon measurements")
            print("- 63 emission sources")
            print("- 5 emission factors")
            print("- 5 variety footprints")
            print("- 12 impact metrics")
            print("- 5 SDG indicators")
            print("- 5 variety releases")
            print("- 3 policy adoptions")
            print("\nTotal: 188 records created")
            print("\nYou can now view the data at:")
            print("- http://localhost:5173/earth-systems/carbon")
            print("- http://localhost:5173/earth-systems/sustainability")
            print()

        except Exception as e:
            print(f"\n❌ Error creating demo data: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(main())

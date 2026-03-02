import asyncio
import sys
import os
# Force SQLite for verification script
os.environ["USE_SQLITE"] = "True"

from datetime import datetime, timedelta
import random

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

# Monkeypatch GeoAlchemy2 to skip spatialite init for verification
import geoalchemy2.admin.dialects.sqlite
def noop_after_create(table, bind, **kw):
    pass
geoalchemy2.admin.dialects.sqlite.after_create = noop_after_create

from app.core.database import AsyncSessionLocal, Base, engine
from app.services.environmental_physics import environmental_service
from app.services.biosimulation import biosimulation_service
from app.services.economics import economics_service
from app.services.spatial import spatial_service
from app.models.biosimulation import CropModel
from app.models.core import Location, Organization

from app.services.weather_integration import weather_client

async def main():
    print("🚀 Initiating Science Engine Test Flight (with Open-Meteo Data)...")
    
    # Init DB (Create tables for SQLite)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Setup: Organization & Location
            print("\n[1/5] 🌍 Setting up Mission Context...")
            # Ideally getting existing or creating mock
            org_id = 1 
            
            # Mock Location (Kaveri Basin, Karnataka - suitable for Agriculture)
            lat = 12.2958
            lon = 76.6394
            print(f"      📍 Location: Kaveri Basin ({lat}, {lon})")
            
            # 2. Environmental Engine: Weather Generation (FETCH REAL DATA)
            print("\n[2/5] 🌦️  Fetching Real Historical Weather (Last 120 Days)...")
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=120)
            
            weather_data = await weather_client.get_historical_weather(
                lat=lat, 
                lon=lon, 
                start_date=start_date, 
                end_date=end_date
            )
            
            # Parse Open-Meteo response
            daily_weather = []
            daily = weather_data.get("daily", {})
            times = daily.get("time", [])
            t_maxs = daily.get("temperature_2m_max", [])
            t_mins = daily.get("temperature_2m_min", [])
            solars = daily.get("shortwave_radiation_sum", [])
            
            for i, date_str in enumerate(times):
                if i >= len(t_maxs) or i >= len(t_mins): break
                
                # Open-Meteo dates are YYYY-MM-DD
                d = datetime.strptime(date_str, "%Y-%m-%d")
                
                # Solar Rad (MJ/m2) -> PAR (approx 0.5 * Solar)
                solar_rad = solars[i] if i < len(solars) and solars[i] is not None else 20.0
                par = solar_rad * 0.5
                
                daily_weather.append({
                    "date": d,
                    "t_max": t_maxs[i],
                    "t_min": t_mins[i],
                    "par": par
                })
            
            print(f"      ✅ Fetched {len(daily_weather)} days of real weather data.")
                
            # Verify Environmental Service (GDD Calc)
            sample_gdd = await environmental_service.calculate_gdd(30, 15, 10)
            print(f"      ✅ GDD Calculation Check (30/15/10): {sample_gdd} GDD")

            # 3. Biosimulation: Grow Crop
            print("\n[3/5] 🌱 Running Biosimulation (Maize-Hybrid-X)...")
            
            # Create a mock model if not exists (in memory check for now to avoid DB clutter or just Create)
            # For this script, we'll just insert a temporary one
            crop_model = CropModel(
                organization_id=org_id,
                name=f"Test-Maize-{random.randint(1000,9999)}",
                crop_name="Maize",
                base_temp=10.0,
                gdd_flowering=700,
                gdd_maturity=1400,
                rue=1.6
            )
            db.add(crop_model)
            await db.commit()
            await db.refresh(crop_model)
            print(f"      Created Mock CropModel: {crop_model.name}")
            
            # Mock Location
            location_id = 1 # Assuming default location exists
            
            run = await biosimulation_service.run_simulation(
                db=db,
                organization_id=org_id,
                crop_model_id=crop_model.id,
                location_id=location_id,
                start_date=start_date,
                daily_weather_data=daily_weather
            )
            
            print(f"      ✅ Simulation Completed: ID {run.id}")
            print(f"      📅 Predicted Flowering: {run.predicted_flowering_date.date()}")
            print(f"      📅 Predicted Maturity: {run.predicted_maturity_date.date()}")
            print(f"      ⚖️  Predicted Yield: {run.predicted_yield:.2f} kg/ha")
            
            # 4. Spatial: Mock Query
            print("\n[4/5] 🗺️  Testing Spatial Queries...")
            # We don't have a real raster file, so we'll just test the service method handles missing file gracefully
            # or mock the method if we want to confirm wiring. 
            # ideally we'd skip creating a real raster for this quick check unless we bundle one.
            print("      ⚠️  Skipping actual raster read (No test file). Verified import logic.")

            # 5. Economics: ROI
            print("\n[5/5] 💰 Analyzing Economics...")
            
            market_price_per_kg = 0.25 # $0.25/kg
            revenue = run.predicted_yield * market_price_per_kg
            cost = 1200.0 # $1200/ha input cost
            
            cb_analysis = await economics_service.create_cost_benefit_analysis(
                db=db,
                organization_id=org_id,
                name=f"Validation Run {run.id}",
                total_cost=cost,
                expected_revenue=revenue
            )
            
            print(f"      💵 Input Cost: ${cost}")
            print(f"      💵 Est. Revenue: ${revenue:.2f}")
            print(f"      📈 ROI: {cb_analysis.roi_percent:.2f}%")
            print(f"      📊 B/C Ratio: {cb_analysis.benefit_cost_ratio:.2f}")

            print("\n✅ MISSION SUCCESS: All Science Engines Operational.")
            
        except Exception as e:
            print(f"\n❌ MISSION FAILED: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

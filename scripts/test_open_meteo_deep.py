import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.modules.environment.services.weather_integration_service import weather_client

async def main():
    print("=============================================")
    print("📡 Open-Meteo Deep Diagnostic Tool")
    print("=============================================")
    
    # Coordinates: Kaveri Basin (Approx)
    lat = 12.2958
    lon = 76.6394
    print(f"📍 Target Location: Lat {lat}, Lon {lon}")
    
    # ---------------------------------------------------------
    # TEST 1: Current Forecast (Connectivity Check)
    # ---------------------------------------------------------
    print("\n[TEST 1] Testing Forecast Endpoint (Next 3 Days)...")
    try:
        forecast = await weather_client.get_forecast(lat, lon, days=3)
        
        # Check integrity
        if "daily" not in forecast:
            print("❌ FAILED: 'daily' key missing in response.")
            return

        dates = forecast["daily"]["time"]
        t_max = forecast["daily"]["temperature_2m_max"]
        rain = forecast["daily"]["precipitation_sum"]
        
        print("✅ Connection Successful.")
        print("📊 Data Received:")
        for i, d in enumerate(dates):
            print(f"   - {d}: Max Temp {t_max[i]}°C, Rain {rain[i]}mm")
            
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

    # ---------------------------------------------------------
    # TEST 2: Current Season (Feb 2026) - User's Context
    # ---------------------------------------------------------
    print("\n[TEST 2] Testing Current Season (Feb 7-14, 2026)...")
    try:
        # User specified "Today is 14-Feb-2026"
        end = datetime(2026, 2, 14).date()
        start = datetime(2026, 2, 7).date()
        print(f"   Requesting range: {start} to {end}")
        
        history = await weather_client.get_historical_weather(lat, lon, start, end)
        
        if "daily" not in history:
            print("❌ FAILED: 'daily' key missing.")
            return

        dates = history["daily"]["time"]
        t_max = history["daily"]["temperature_2m_max"]
        
        # Extended Variables
        wind = history["daily"].get("wind_speed_10m_max", [])
        rh = history["daily"].get("relative_humidity_2m_mean", [])
        soil_t = history["daily"].get("soil_temperature_0_to_7cm_mean", [])
        vpd = history["daily"].get("vapor_pressure_deficit_max", [])
        soil_m = history["daily"].get("soil_moisture_0_to_7cm_mean", [])
        solar = history["daily"].get("shortwave_radiation_sum", [])
        et0 = history["daily"].get("et0_fao_evapotranspiration", [])

        print("✅ Archive Access Successful.")
        print("📊 Agricultural Data Received:")
        for i, d in enumerate(dates):
            print(f"   - {d}:")
            print(f"     🌡️  Atmosphere: TMax {t_max[i]}°C | RH {rh[i] if i<len(rh) else '-'}% | VPD {vpd[i] if i<len(vpd) else '-'} kPa")
            print(f"     💨 Wind: {wind[i] if i<len(wind) else '-'} km/h")
            if i < len(soil_m): print(f"     🌱 Soil (0-7cm): Moist {soil_m[i]} m³/m³ | Temp {soil_t[i] if i<len(soil_t) else '-'}°C")
            if i < len(solar):  print(f"     ☀️  Energy: Solar {solar[i]} MJ/m² | ET0 {et0[i]} mm")
            print("     -----------------------------")

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------
    print("\n=============================================")
    print("✅ DIAGNOSTIC COMPLETE")
    print("If you see data above, the API is working correctly.")
    print("=============================================")

if __name__ == "__main__":
    asyncio.run(main())

"""
Environmental Physics Service
Calculates environmental indices (GDD, PTU, Soil Moisture)
"""

import math
from typing import Optional, List, Dict
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.environmental import EnvironmentalUnit, SoilProfile
from app.models.core import Location
from app.services.weather_integration import weather_client

class EnvironmentalPhysicsService:
    """
    Service for calculating and storing environmental physics indices.
    """
    
    # Scientific Constants
    Standard_Base_Temps = {
        "Maize": 10.0,
        "Wheat": 0.0,
        "Rice": 10.0,
        "Cotton": 15.6,
        "Sorghum": 10.0
    }

    async def sync_todays_weather(
        self,
        db: AsyncSession,
        location_id: int,
        crop_base_temp: float = 10.0
    ) -> EnvironmentalUnit:
        """
        Fetch today's forecast (Max/Min Temp) from Open-Meteo and record GDD.
        """
        # 1. Get Location
        location = await db.get(Location, location_id)
        if not location:
            raise ValueError(f"Location {location_id} not found")
        
        if not location.latitude or not location.longitude:
             raise ValueError("Location missing coordinates (lat/long)")

        # 2. Fetch Forecast (Open-Meteo)
        # Request 1 day to get today's data
        forecast_data = await weather_client.get_forecast(
            location.latitude, 
            location.longitude, 
            days=1
        )
        
        # 3. Parse Response (Open-Meteo structure)
        # { "daily": { "temperature_2m_max": [25.5], "temperature_2m_min": [15.2], ... } }
        daily = forecast_data.get("daily", {})
        if not daily or "temperature_2m_max" not in daily:
             raise RuntimeError("No daily forecast data returned from Open-Meteo")
        
        # Open-Meteo returns lists. Index 0 is today.
        t_max = daily["temperature_2m_max"][0]
        t_min = daily["temperature_2m_min"][0]
        day_length_s = daily.get("daylight_duration", [None])[0] # Seconds
        
        if t_max is None or t_min is None:
             raise ValueError("Incomplete temperature data from API")

        # Convert day length to hours if available
        day_length_hours = None
        if day_length_s:
            day_length_hours = day_length_s / 3600.0

        # 4. Record
        return await self.record_daily_environment(
            db=db,
            location_id=location_id,
            date_record=date.today(),
            t_max=float(t_max),
            t_min=float(t_min),
            day_length=day_length_hours,
            crop_base_temp=crop_base_temp
        )

    async def calculate_gdd(
        self,
        t_max: float,
        t_min: float,
        t_base: float = 10.0,
        method: str = "standard"
    ) -> float:
        """
        Calculate Growing Degree Days (GDD) for a single day.
        
        Method 'standard':
        GDD = ((Tmax + Tmin) / 2) - Tbase
        Constraints: If T < Tbase, T = Tbase.
        """
        # Constrain temperatures
        if t_min < t_base:
            t_min = t_base
        if t_max < t_base:
            t_max = t_base
            
        mean_temp = (t_max + t_min) / 2
        gdd = mean_temp - t_base
        
        return max(0.0, gdd)

    async def calculate_ptu(
        self,
        gdd: float,
        day_length_hours: float
    ) -> float:
        """
        Calculate Photothermal Units (PTU).
        PTU = GDD * Day Length
        Used for photoperiod-sensitive crops.
        """
        return gdd * day_length_hours

    async def calculate_soil_moisture(
        self,
        soil_profile: SoilProfile,
        matric_potential: float # h (cm, negative for suction)
    ) -> float:
        """
        Calculate Soil Moisture Content (theta) using Van Genuchten (1980) equation.
        
        theta(h) = theta_res + (theta_sat - theta_res) / [1 + (alpha * |h|)^n]^(1-1/n)
        
        Parameters:
        - soil_profile: Database object with hydraulic properties (theta_sat, theta_res, alpha, n)
        - matric_potential: Pressure head (h) in cm. 0 = saturation, large negative = dry.
        """
        if matric_potential >= 0:
            return soil_profile.theta_sat
            
        h = abs(matric_potential)
        alpha = soil_profile.alpha
        n = soil_profile.n_param
        m = 1 - (1 / n)
        
        theta_range = soil_profile.theta_sat - soil_profile.theta_res
        denominator = (1 + (alpha * h) ** n) ** m
        
        theta = soil_profile.theta_res + (theta_range / denominator)
        return theta

    async def record_daily_environment(
        self,
        db: AsyncSession,
        location_id: int,
        date_record: date,
        t_max: float,
        t_min: float,
        day_length: Optional[float] = None,
        crop_base_temp: float = 10.0
    ) -> EnvironmentalUnit:
        """
        Calculate and save environmental indices for a day.
        """
        # Calculate GDD
        gdd = await self.calculate_gdd(t_max, t_min, t_base=crop_base_temp)
        
        # Calculate PTU if day length available
        ptu = None
        if day_length:
            ptu = await self.calculate_ptu(gdd, day_length)
            
        # Create record
        record = EnvironmentalUnit(
            location_id=location_id,
            date_calculated=date_record,
            gdd_accumulated=gdd,
            ptu_accumulated=ptu,
            source_model="standard_physics"
        )
        
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

# Global instance
environmental_service = EnvironmentalPhysicsService()

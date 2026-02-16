import httpx
from datetime import datetime, date
from typing import Dict, Any, Optional, List

class OpenMeteoClient:
    """
    Client for Open-Meteo API (Free, No-Key).
    Provides Historical Weather and Forecasts for agricultural analysis.
    """

    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    HISTORY_URL = "https://archive-api.open-meteo.com/v1/archive"

    async def get_forecast(self, lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
        """
        Fetch weather forecast.
        Variables: Max/Min Temp, Precipitation Sum, Et0.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "et0_fao_evapotranspiration",
                "shortwave_radiation_sum",
                "soil_moisture_0_to_7cm_mean",
                "wind_speed_10m_max",
                "relative_humidity_2m_mean",
                "soil_temperature_0_to_7cm_mean",
                "vapor_pressure_deficit_max"
            ]),
            "timezone": "auto",
            "forecast_days": days
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.FORECAST_URL, params=params)
            response.raise_for_status()
            return response.json()

    async def get_historical_weather(
        self,
        lat: float,
        lon: float,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Fetch historical weather for a date range.
        Useful for model calibration and retrospective analysis.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            # Debugging: Starting with basic variables only
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "et0_fao_evapotranspiration",
                "shortwave_radiation_sum",
                "soil_moisture_0_to_7cm_mean",
                "soil_moisture_7_to_28cm_mean",
                # Extended Ag Variables via User Request:
                "wind_speed_10m_max",
                "relative_humidity_2m_mean",
                "soil_temperature_0_to_7cm_mean",
                "vapor_pressure_deficit_max"
            ]),
            "timezone": "auto"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.HISTORY_URL, params=params)
            response.raise_for_status()
            return response.json()

weather_client = OpenMeteoClient()

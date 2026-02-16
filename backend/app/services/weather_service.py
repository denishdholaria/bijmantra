"""
Weather Intelligence Service
Agricultural weather analysis and impact predictions for Veena AI

Features:
- Weather data integration
- Growing degree day calculations
- Crop-specific impact analysis
- Activity recommendations
- Alert generation
"""

from datetime import datetime, UTC, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
from app.services.weather_integration import weather_client


# ============================================
# ENUMS & TYPES
# ============================================

class WeatherCondition(str, Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    STORM = "storm"
    SNOW = "snow"
    FOG = "fog"
    HEAT = "heat"
    FROST = "frost"


class ImpactSeverity(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActivityType(str, Enum):
    PLANTING = "planting"
    POLLINATION = "pollination"
    SPRAYING = "spraying"
    HARVESTING = "harvesting"
    OBSERVATION = "observation"
    IRRIGATION = "irrigation"


# ============================================
# SCHEMAS
# ============================================

class WeatherData(BaseModel):
    date: datetime
    location_id: str
    location_name: str
    temp_min: float  # Celsius
    temp_max: float
    temp_avg: float
    humidity: float  # Percentage
    precipitation: float  # mm
    wind_speed: float  # km/h
    condition: WeatherCondition
    uv_index: float
    soil_moisture: Optional[float] = None
    solar_radiation: Optional[float] = None
    et0: Optional[float] = None
    soil_temperature: Optional[float] = None
    vapor_pressure_deficit: Optional[float] = None


class GrowingDegreeDays(BaseModel):
    location_id: str
    date: datetime
    gdd_daily: float
    gdd_cumulative: float
    base_temp: float
    crop: str


class WeatherImpact(BaseModel):
    date: datetime
    event: str
    probability: float
    severity: ImpactSeverity
    affected_activities: List[ActivityType]
    recommendation: str
    details: Optional[str] = None


class ActivityWindow(BaseModel):
    activity: ActivityType
    start: datetime
    end: datetime
    confidence: float
    conditions: str


class WeatherForecast(BaseModel):
    location_id: str
    location_name: str
    generated_at: datetime
    forecast_days: int
    daily_forecast: List[WeatherData]
    impacts: List[WeatherImpact]
    optimal_windows: List[ActivityWindow]
    gdd_forecast: List[GrowingDegreeDays]
    alerts: List[str]


# ============================================
# SERVICE
# ============================================

class WeatherService:
    """
    Weather intelligence service for agricultural decision support.
    Integrates with Veena AI for smart recommendations.
    """

    # Crop-specific base temperatures for GDD calculation
    CROP_BASE_TEMPS = {
        "wheat": 0.0,
        "rice": 10.0,
        "maize": 10.0,
        "soybean": 10.0,
        "cotton": 15.5,
        "sorghum": 10.0,
        "barley": 0.0,
        "default": 10.0
    }

    # Activity weather requirements
    ACTIVITY_REQUIREMENTS = {
        ActivityType.PLANTING: {
            "min_temp": 10,
            "max_temp": 30,
            "max_precipitation": 5,
            "max_wind": 20,
            "min_soil_moisture": 30
        },
        ActivityType.POLLINATION: {
            "min_temp": 15,
            "max_temp": 32,
            "max_precipitation": 0,
            "max_wind": 15,
            "min_humidity": 40,
            "max_humidity": 80
        },
        ActivityType.SPRAYING: {
            "min_temp": 10,
            "max_temp": 30,
            "max_precipitation": 0,
            "max_wind": 10,
            "min_humidity": 40,
            "max_humidity": 90
        },
        ActivityType.HARVESTING: {
            "min_temp": 5,
            "max_temp": 35,
            "max_precipitation": 0,
            "max_wind": 25,
            "max_humidity": 70
        },
        ActivityType.OBSERVATION: {
            "max_precipitation": 10,
            "max_wind": 30
        },
        ActivityType.IRRIGATION: {
            "max_precipitation": 5
        }
    }

    def __init__(self):
        pass

    async def get_forecast(
        self,
        location_id: str,
        location_name: str,
        days: int = 14,
        crop: str = "wheat",
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> WeatherForecast:
        """
        Get comprehensive weather forecast with agricultural analysis.
        """
        daily_forecast = []
        if lat is not None and lon is not None:
            try:
                # Fetch real data
                api_data = await weather_client.get_forecast(lat, lon, days)
                daily_forecast = self._map_api_to_weather_data(api_data, location_id, location_name)
            except Exception as e:
                print(f"Weather API failed: {e}. Falling back to mock.")
                daily_forecast = self._generate_mock_forecast(location_id, location_name, days)
        else:
            daily_forecast = self._generate_mock_forecast(location_id, location_name, days)

        # Calculate impacts
        impacts = self._analyze_impacts(daily_forecast)

        # Find optimal activity windows
        optimal_windows = self._find_optimal_windows(daily_forecast)

        # Calculate GDD
        gdd_forecast = await self._calculate_gdd(daily_forecast, crop)

        # Generate alerts
        alerts = self._generate_alerts(impacts)

        return WeatherForecast(
            location_id=location_id,
            location_name=location_name,
            generated_at=datetime.now(UTC),
            forecast_days=days,
            daily_forecast=daily_forecast,
            impacts=impacts,
            optimal_windows=optimal_windows,
            gdd_forecast=gdd_forecast,
            alerts=alerts
        )

    def _map_api_to_weather_data(self, api_data: Dict[str, Any], location_id: str, location_name: str) -> List[WeatherData]:
        """Map Open-Meteo response to WeatherData model."""
        daily = api_data.get("daily", {})
        times = daily.get("time", [])

        forecast = []
        for i, time_str in enumerate(times):
            date_obj = datetime.fromisoformat(time_str).replace(tzinfo=UTC)

            t_max = daily.get("temperature_2m_max", [])[i]
            t_min = daily.get("temperature_2m_min", [])[i]
            t_avg = (t_max + t_min) / 2

            precip = daily.get("precipitation_sum", [])[i]
            wind = daily.get("wind_speed_10m_max", [])[i] if "wind_speed_10m_max" in daily else 0
            rh = daily.get("relative_humidity_2m_mean", [])[i] if "relative_humidity_2m_mean" in daily else 0

            # Determine condition
            condition = WeatherCondition.CLEAR
            if precip > 20: condition = WeatherCondition.HEAVY_RAIN
            elif precip > 0: condition = WeatherCondition.RAIN
            elif t_max > 35: condition = WeatherCondition.HEAT
            elif t_min < 2: condition = WeatherCondition.FROST

            # Extended vars
            soil_m = daily.get("soil_moisture_0_to_7cm_mean", [])[i] if "soil_moisture_0_to_7cm_mean" in daily else None
            solar = daily.get("shortwave_radiation_sum", [])[i] if "shortwave_radiation_sum" in daily else None
            et0 = daily.get("et0_fao_evapotranspiration", [])[i] if "et0_fao_evapotranspiration" in daily else None
            soil_t = daily.get("soil_temperature_0_to_7cm_mean", [])[i] if "soil_temperature_0_to_7cm_mean" in daily else None
            vpd = daily.get("vapor_pressure_deficit_max", [])[i] if "vapor_pressure_deficit_max" in daily else None

            forecast.append(WeatherData(
                date=date_obj,
                location_id=location_id,
                location_name=location_name,
                temp_min=t_min,
                temp_max=t_max,
                temp_avg=t_avg,
                humidity=rh,
                precipitation=precip,
                wind_speed=wind,
                condition=condition,
                uv_index=0,
                soil_moisture=soil_m,
                solar_radiation=solar,
                et0=et0,
                soil_temperature=soil_t,
                vapor_pressure_deficit=vpd
            ))

        return forecast

    def _generate_mock_forecast(
        self,
        location_id: str,
        location_name: str,
        days: int
    ) -> List[WeatherData]:
        """Generate mock weather data for demonstration."""
        import random

        forecast = []
        base_temp = 25  # Base temperature for the season

        for i in range(days):
            date = datetime.now(UTC) + timedelta(days=i)

            # Add some variation
            temp_variation = random.uniform(-5, 5)
            temp_avg = base_temp + temp_variation
            temp_min = temp_avg - random.uniform(3, 8)
            temp_max = temp_avg + random.uniform(3, 8)

            # Precipitation (more likely on some days)
            precipitation = 0
            condition = WeatherCondition.CLEAR

            if random.random() < 0.3:  # 30% chance of rain
                precipitation = random.uniform(5, 50)
                condition = WeatherCondition.HEAVY_RAIN if precipitation > 30 else WeatherCondition.RAIN
            elif random.random() < 0.2:
                condition = WeatherCondition.CLOUDY

            # Heat wave simulation
            if i == 7 and random.random() < 0.5:
                temp_max = 38
                temp_avg = 34
                condition = WeatherCondition.HEAT

            forecast.append(WeatherData(
                date=date,
                location_id=location_id,
                location_name=location_name,
                temp_min=round(temp_min, 1),
                temp_max=round(temp_max, 1),
                temp_avg=round(temp_avg, 1),
                humidity=random.uniform(40, 80),
                precipitation=round(precipitation, 1),
                wind_speed=random.uniform(5, 25),
                condition=condition,
                uv_index=random.uniform(3, 10),
                soil_moisture=random.uniform(30, 70)
            ))

        return forecast

    def _analyze_impacts(self, forecast: List[WeatherData]) -> List[WeatherImpact]:
        """Analyze weather impacts on breeding activities."""
        impacts = []

        for day in forecast:
            # Heavy rain impact
            if day.precipitation > 30:
                impacts.append(WeatherImpact(
                    date=day.date,
                    event="Heavy Rainfall",
                    probability=0.85,
                    severity=ImpactSeverity.HIGH,
                    affected_activities=[
                        ActivityType.POLLINATION,
                        ActivityType.SPRAYING,
                        ActivityType.HARVESTING
                    ],
                    recommendation=f"Avoid field activities on {day.date.strftime('%b %d')}. Complete pollinations before rain event.",
                    details=f"Expected precipitation: {day.precipitation}mm"
                ))

            # Heat stress
            if day.temp_max > 35:
                impacts.append(WeatherImpact(
                    date=day.date,
                    event="Heat Stress Risk",
                    probability=0.75,
                    severity=ImpactSeverity.MEDIUM,
                    affected_activities=[
                        ActivityType.POLLINATION,
                        ActivityType.OBSERVATION
                    ],
                    recommendation="Schedule field work for early morning. Consider irrigation to mitigate heat stress.",
                    details=f"Maximum temperature: {day.temp_max}°C"
                ))

            # Frost risk
            if day.temp_min < 2:
                impacts.append(WeatherImpact(
                    date=day.date,
                    event="Frost Risk",
                    probability=0.70,
                    severity=ImpactSeverity.CRITICAL,
                    affected_activities=[
                        ActivityType.PLANTING,
                        ActivityType.POLLINATION
                    ],
                    recommendation="Protect sensitive crops. Delay planting if possible.",
                    details=f"Minimum temperature: {day.temp_min}°C"
                ))

            # High wind
            if day.wind_speed > 20:
                impacts.append(WeatherImpact(
                    date=day.date,
                    event="High Wind",
                    probability=0.80,
                    severity=ImpactSeverity.LOW,
                    affected_activities=[ActivityType.SPRAYING],
                    recommendation="Avoid spraying operations due to drift risk.",
                    details=f"Wind speed: {day.wind_speed} km/h"
                ))

        return impacts

    def _find_optimal_windows(self, forecast: List[WeatherData]) -> List[ActivityWindow]:
        """Find optimal windows for various activities."""
        windows = []

        for activity, requirements in self.ACTIVITY_REQUIREMENTS.items():
            suitable_days = []

            for day in forecast:
                is_suitable = True

                if "min_temp" in requirements and day.temp_min < requirements["min_temp"]:
                    is_suitable = False
                if "max_temp" in requirements and day.temp_max > requirements["max_temp"]:
                    is_suitable = False
                if "max_precipitation" in requirements and day.precipitation > requirements["max_precipitation"]:
                    is_suitable = False
                if "max_wind" in requirements and day.wind_speed > requirements["max_wind"]:
                    is_suitable = False

                if is_suitable:
                    suitable_days.append(day)

            # Find consecutive suitable days
            if suitable_days:
                # Take first window of suitable days
                start = suitable_days[0].date
                end = suitable_days[min(2, len(suitable_days) - 1)].date

                windows.append(ActivityWindow(
                    activity=activity,
                    start=start,
                    end=end,
                    confidence=min(0.95, 0.7 + len(suitable_days) * 0.05),
                    conditions="Favorable conditions expected"
                ))

        return windows

    async def _calculate_gdd(
        self,
        forecast: List[WeatherData],
        crop: str
    ) -> List[GrowingDegreeDays]:
        """Calculate growing degree days for crop development tracking via EnvironmentalPhysicsService."""
        # Import dynamically to avoid circular imports if any
        from app.services.environmental_physics import environmental_service

        base_temp = self.CROP_BASE_TEMPS.get(crop.lower(), self.CROP_BASE_TEMPS["default"])

        gdd_list = []
        cumulative = 0

        for day in forecast:
            # Delegate calculation to Science Engine
            # Note: calculate_gdd is async but here we are in a loop.
            # Ideally we'd gather, but for simplicity let's await sequentially or adapt.
            # However, calculate_gdd is pure logic in this context, let's check its definition.
            # Checking service definition from prior read: it IS async.

            daily_gdd = await environmental_service.calculate_gdd(
                t_max=day.temp_max,
                t_min=day.temp_min,
                t_base=base_temp
            )

            cumulative += daily_gdd

            gdd_list.append(GrowingDegreeDays(
                location_id=day.location_id,
                date=day.date,
                gdd_daily=round(daily_gdd, 1),
                gdd_cumulative=round(cumulative, 1),
                base_temp=base_temp,
                crop=crop
            ))

        return gdd_list

    def _generate_alerts(self, impacts: List[WeatherImpact]) -> List[str]:
        """Generate alert messages from impacts."""
        alerts = []

        critical_impacts = [i for i in impacts if i.severity == ImpactSeverity.CRITICAL]
        high_impacts = [i for i in impacts if i.severity == ImpactSeverity.HIGH]

        for impact in critical_impacts:
            alerts.append(f"🚨 CRITICAL: {impact.event} on {impact.date.strftime('%b %d')} - {impact.recommendation}")

        for impact in high_impacts[:3]:  # Limit to top 3
            alerts.append(f"⚠️ {impact.event} on {impact.date.strftime('%b %d')} - {impact.recommendation}")

        return alerts

    def get_veena_summary(self, forecast: WeatherForecast) -> str:
        """
        Generate a natural language summary for Veena AI.
        """
        summary_parts = [
            f"🌤️ Weather outlook for {forecast.location_name} ({forecast.forecast_days} days):\n"
        ]

        # Overall conditions
        rain_days = sum(1 for d in forecast.daily_forecast if d.precipitation > 5)
        hot_days = sum(1 for d in forecast.daily_forecast if d.temp_max > 35)

        if rain_days > 0:
            summary_parts.append(f"• {rain_days} day(s) with significant rainfall expected")
        if hot_days > 0:
            summary_parts.append(f"• {hot_days} day(s) with heat stress risk (>35°C)")

        # Alerts
        if forecast.alerts:
            summary_parts.append("\n**Alerts:**")
            for alert in forecast.alerts[:3]:
                summary_parts.append(alert)

        # Recommendations
        if forecast.optimal_windows:
            summary_parts.append("\n**Optimal Activity Windows:**")
            for window in forecast.optimal_windows[:3]:
                summary_parts.append(
                    f"• {window.activity.value.title()}: {window.start.strftime('%b %d')} - {window.end.strftime('%b %d')} ({window.confidence:.0%} confidence)"
                )

        return "\n".join(summary_parts)


# Singleton instance
weather_service = WeatherService()

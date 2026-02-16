"""
Solar & Sun-Earth Systems Service

Provides solar radiation, photoperiod, and space weather data.
Uses calculations and demo data for offline mode.
"""

import math
from datetime import datetime, UTC, date, timedelta
from typing import Optional


class SolarService:
    """Service for solar and sun-earth system calculations."""

    def __init__(self):
        self._cache = {}

    def calculate_photoperiod(
        self,
        latitude: float,
        target_date: Optional[date] = None,
    ) -> dict:
        """
        Calculate day length (photoperiod) for a given latitude and date.
        
        Uses the CBM model (Civil twilight-based method).
        """
        if target_date is None:
            target_date = date.today()

        # Day of year
        doy = target_date.timetuple().tm_yday

        # Solar declination (radians)
        declination = 23.45 * math.sin(math.radians(360 * (284 + doy) / 365))
        declination_rad = math.radians(declination)

        # Latitude in radians
        lat_rad = math.radians(latitude)

        # Hour angle at sunrise/sunset
        # cos(hour_angle) = -tan(lat) * tan(declination)
        cos_hour_angle = -math.tan(lat_rad) * math.tan(declination_rad)

        # Handle polar day/night
        if cos_hour_angle < -1:
            # Polar day (24h daylight)
            day_length = 24.0
            sunrise = "00:00"
            sunset = "24:00"
        elif cos_hour_angle > 1:
            # Polar night (0h daylight)
            day_length = 0.0
            sunrise = "--:--"
            sunset = "--:--"
        else:
            hour_angle = math.degrees(math.acos(cos_hour_angle))
            day_length = 2 * hour_angle / 15  # Convert to hours

            # Calculate sunrise/sunset times (approximate, assuming solar noon at 12:00)
            half_day = day_length / 2
            sunrise_hour = 12 - half_day
            sunset_hour = 12 + half_day

            sunrise = f"{int(sunrise_hour):02d}:{int((sunrise_hour % 1) * 60):02d}"
            sunset = f"{int(sunset_hour):02d}:{int((sunset_hour % 1) * 60):02d}"

        return {
            "date": target_date.isoformat(),
            "latitude": latitude,
            "day_length_hours": round(day_length, 2),
            "sunrise": sunrise,
            "sunset": sunset,
            "solar_declination": round(declination, 2),
            "day_of_year": doy,
            "is_long_day": day_length > 12,
            "photoperiod_class": self._classify_photoperiod(day_length),
        }

    def _classify_photoperiod(self, hours: float) -> str:
        """Classify photoperiod for crop response."""
        if hours >= 14:
            return "Long Day (>14h)"
        elif hours >= 12:
            return "Intermediate (12-14h)"
        elif hours >= 10:
            return "Short Day (10-12h)"
        else:
            return "Very Short (<10h)"

    def get_photoperiod_series(
        self,
        latitude: float,
        start_date: Optional[date] = None,
        days: int = 365,
    ) -> list:
        """Get photoperiod data for a series of dates."""
        if start_date is None:
            start_date = date.today()

        series = []
        for i in range(days):
            d = start_date + timedelta(days=i)
            data = self.calculate_photoperiod(latitude, d)
            series.append({
                "date": data["date"],
                "day_length": data["day_length_hours"],
            })

        return series

    def calculate_solar_radiation(
        self,
        latitude: float,
        target_date: Optional[date] = None,
        cloud_cover: float = 0.3,
    ) -> dict:
        """
        Estimate daily solar radiation (MJ/m²/day).
        
        Uses the Angstrom-Prescott equation with estimated parameters.
        """
        if target_date is None:
            target_date = date.today()

        doy = target_date.timetuple().tm_yday

        # Solar constant (MJ/m²/min)
        Gsc = 0.0820

        # Inverse relative distance Earth-Sun
        dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)

        # Solar declination
        delta = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)

        # Latitude in radians
        phi = math.radians(latitude)

        # Sunset hour angle
        ws = math.acos(-math.tan(phi) * math.tan(delta))

        # Extraterrestrial radiation (Ra)
        Ra = (24 * 60 / math.pi) * Gsc * dr * (
            ws * math.sin(phi) * math.sin(delta) +
            math.cos(phi) * math.cos(delta) * math.sin(ws)
        )

        # Clear sky radiation (Rso)
        # Simplified: Rso = 0.75 * Ra
        Rso = 0.75 * Ra

        # Actual radiation with cloud cover
        # Rs = Rso * (1 - 0.75 * cloud_cover^3.4)
        Rs = Rso * (1 - 0.75 * (cloud_cover ** 3.4))

        return {
            "date": target_date.isoformat(),
            "latitude": latitude,
            "extraterrestrial_radiation": round(Ra, 2),
            "clear_sky_radiation": round(Rso, 2),
            "estimated_radiation": round(Rs, 2),
            "cloud_cover": cloud_cover,
            "unit": "MJ/m²/day",
            "par_estimate": round(Rs * 0.48, 2),  # PAR is ~48% of total
            "par_unit": "MJ/m²/day",
        }

    def get_uv_index(
        self,
        latitude: float,
        target_date: Optional[date] = None,
        elevation: float = 0,
        cloud_cover: float = 0.3,
    ) -> dict:
        """
        Estimate UV index based on location and conditions.
        
        This is a simplified model for demonstration.
        """
        if target_date is None:
            target_date = date.today()

        doy = target_date.timetuple().tm_yday

        # Base UV index varies with latitude and season
        # Higher at equator, peaks in summer
        lat_factor = math.cos(math.radians(latitude))
        season_factor = 1 + 0.3 * math.cos(2 * math.pi * (doy - 172) / 365)  # Peak at summer solstice

        base_uv = 12 * lat_factor * season_factor

        # Elevation adjustment (+4% per 300m)
        elevation_factor = 1 + 0.04 * (elevation / 300)

        # Cloud cover reduction
        cloud_factor = 1 - 0.7 * cloud_cover

        uv_index = base_uv * elevation_factor * cloud_factor
        uv_index = max(0, min(15, uv_index))  # Clamp to realistic range

        return {
            "date": target_date.isoformat(),
            "latitude": latitude,
            "elevation": elevation,
            "cloud_cover": cloud_cover,
            "uv_index": round(uv_index, 1),
            "category": self._uv_category(uv_index),
            "protection_needed": uv_index >= 3,
            "peak_hours": "10:00 - 14:00",
        }

    def _uv_category(self, uv: float) -> str:
        """Categorize UV index."""
        if uv < 3:
            return "Low"
        elif uv < 6:
            return "Moderate"
        elif uv < 8:
            return "High"
        elif uv < 11:
            return "Very High"
        else:
            return "Extreme"

    def get_current_solar_conditions(self) -> dict:
        """
        Get current solar/space weather conditions.
        
        Returns demo data simulating real-time conditions.
        """
        now = datetime.now(UTC)

        # Simulate solar cycle (11-year cycle)
        # We're currently near solar maximum (2024-2025)
        cycle_phase = 0.8  # 0-1, where 1 is solar maximum

        # Sunspot number varies with cycle
        base_sunspots = 50 + 150 * cycle_phase
        sunspots = int(base_sunspots + 20 * math.sin(now.timestamp() / 86400))

        # Solar flux (F10.7) correlates with sunspots
        solar_flux = 70 + sunspots * 0.8

        return {
            "timestamp": now.isoformat() + "Z",
            "sunspot_number": sunspots,
            "solar_flux_f107": round(solar_flux, 1),
            "solar_flux_unit": "sfu",
            "solar_wind_speed": 350 + int(50 * math.sin(now.timestamp() / 3600)),
            "solar_wind_unit": "km/s",
            "kp_index": round(2 + 2 * cycle_phase * abs(math.sin(now.timestamp() / 7200)), 1),
            "geomagnetic_storm": False,
            "solar_flare_probability": {
                "C_class": round(0.3 + 0.4 * cycle_phase, 2),
                "M_class": round(0.1 + 0.2 * cycle_phase, 2),
                "X_class": round(0.01 + 0.05 * cycle_phase, 2),
            },
            "cycle_phase": "Solar Maximum" if cycle_phase > 0.7 else "Rising Phase",
            "cycle_number": 25,
        }

    def get_solar_forecast(self, days: int = 7) -> list:
        """Get solar activity forecast for upcoming days."""
        forecast = []
        base_conditions = self.get_current_solar_conditions()

        for i in range(days):
            d = date.today() + timedelta(days=i)
            # Add some variation
            variation = math.sin(i * 0.5) * 0.2

            forecast.append({
                "date": d.isoformat(),
                "sunspot_number": base_conditions["sunspot_number"] + int(10 * variation),
                "kp_index_forecast": round(base_conditions["kp_index"] + variation, 1),
                "geomagnetic_activity": "Quiet" if base_conditions["kp_index"] < 4 else "Active",
                "aurora_probability": round(0.1 + 0.3 * (base_conditions["kp_index"] / 9), 2),
            })

        return forecast

    def get_geomagnetic_data(self) -> dict:
        """Get current geomagnetic field data."""
        now = datetime.now(UTC)

        # Simulate Kp index (0-9 scale)
        kp = 2 + 2 * abs(math.sin(now.timestamp() / 10800))

        return {
            "timestamp": now.isoformat() + "Z",
            "kp_index": round(kp, 1),
            "kp_category": self._kp_category(kp),
            "dst_index": -10 - int(20 * (kp / 9)),  # Disturbance Storm Time
            "dst_unit": "nT",
            "bz_component": round(-2 + 4 * math.sin(now.timestamp() / 3600), 1),
            "bz_unit": "nT",
            "aurora_oval": "Normal" if kp < 4 else "Expanded",
            "radio_blackout_risk": "Low" if kp < 5 else "Moderate",
        }

    def _kp_category(self, kp: float) -> str:
        """Categorize Kp index."""
        if kp < 2:
            return "Quiet"
        elif kp < 4:
            return "Unsettled"
        elif kp < 5:
            return "Active"
        elif kp < 6:
            return "Minor Storm"
        elif kp < 7:
            return "Moderate Storm"
        elif kp < 8:
            return "Strong Storm"
        else:
            return "Severe Storm"


# Singleton instance
_solar_service: Optional[SolarService] = None


def get_solar_service() -> SolarService:
    """Get or create the solar service singleton."""
    global _solar_service
    if _solar_service is None:
        _solar_service = SolarService()
    return _solar_service

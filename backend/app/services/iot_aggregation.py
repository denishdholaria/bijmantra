"""
IoT Aggregation Service

Generates breeding-relevant environmental summaries from sensor telemetry.
Implements Phase 4 of BrAPI IoT Extension.

Key Features:
- Daily, weekly, seasonal aggregations
- Growing Degree Days (GDD) calculation
- Stress indices (heat, drought, frost)
- BrAPI environment integration
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import math


class AggregationPeriod(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEASONAL = "seasonal"


class ParameterCategory(str, Enum):
    TEMPERATURE = "temperature"
    PRECIPITATION = "precipitation"
    HUMIDITY = "humidity"
    SOIL = "soil"
    RADIATION = "radiation"
    STRESS = "stress"
    PLANT = "plant"


@dataclass
class AggregateResult:
    """Result of an aggregation calculation."""
    parameter: str
    value: float
    unit: str
    period: str
    start_time: datetime
    end_time: datetime
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    std_dev: Optional[float] = None
    sample_count: Optional[int] = None
    quality_score: Optional[float] = None
    calculation_method: Optional[str] = None


class IoTAggregationService:
    """
    Service for aggregating IoT sensor data into breeding-relevant summaries.
    
    Aggregation Types:
    - Temperature: mean, min, max, GDD
    - Rainfall: total, days, intensity
    - Humidity: mean, min, max
    - Soil Moisture: mean, stress days
    - Solar Radiation: total, mean PAR
    - Wind: mean speed, max gust
    """

    # Default base temperatures for GDD calculation (°C)
    GDD_BASE_TEMPS = {
        "rice": 10,
        "wheat": 0,
        "maize": 10,
        "soybean": 10,
        "cotton": 15.5,
        "default": 10,
    }

    # Stress thresholds
    HEAT_STRESS_THRESHOLD = 35  # °C
    FROST_THRESHOLD = 0  # °C
    DROUGHT_THRESHOLD = 30  # % soil moisture

    def __init__(self):
        self.aggregation_methods = {
            "air_temperature_mean": self._calc_mean,
            "air_temperature_max": self._calc_max,
            "air_temperature_min": self._calc_min,
            "growing_degree_days": self._calc_gdd,
            "heat_stress_days": self._calc_heat_stress_days,
            "frost_days": self._calc_frost_days,
            "precipitation_total": self._calc_sum,
            "precipitation_days": self._calc_rain_days,
            "relative_humidity_mean": self._calc_mean,
            "soil_moisture_mean": self._calc_mean,
            "drought_stress_days": self._calc_drought_days,
            "solar_radiation_total": self._calc_sum,
            "leaf_wetness_hours": self._calc_leaf_wetness_hours,
            "wind_speed_mean": self._calc_mean,
            "wind_speed_max": self._calc_max,
        }

    # ===========================================
    # Core Aggregation Methods
    # ===========================================

    def _calc_mean(self, values: List[float]) -> float:
        """Calculate arithmetic mean."""
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _calc_sum(self, values: List[float]) -> float:
        """Calculate sum."""
        return sum(values) if values else 0.0

    def _calc_max(self, values: List[float]) -> float:
        """Calculate maximum."""
        return max(values) if values else 0.0

    def _calc_min(self, values: List[float]) -> float:
        """Calculate minimum."""
        return min(values) if values else 0.0

    def _calc_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = self._calc_mean(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    # ===========================================
    # Growing Degree Days (GDD)
    # ===========================================

    def _calc_gdd(
        self,
        values: List[float],
        base_temp: float = 10,
        max_temp: float = 30
    ) -> float:
        """
        Calculate Growing Degree Days using single sine method.
        
        GDD = max(0, (T_avg - T_base))
        
        Args:
            values: List of temperature readings
            base_temp: Base temperature for crop (default 10°C)
            max_temp: Maximum temperature cap (default 30°C)
        
        Returns:
            GDD value for the period
        """
        if not values:
            return 0.0

        # Get daily min/max
        temp_min = min(values)
        temp_max = max(values)

        # Cap at max temp
        temp_max = min(temp_max, max_temp)

        # Calculate average
        temp_avg = (temp_min + temp_max) / 2

        # GDD calculation
        if temp_avg < base_temp:
            return 0.0

        return temp_avg - base_temp

    def calculate_gdd_accumulation(
        self,
        daily_temps: List[Dict[str, float]],
        crop: str = "default",
        start_date: Optional[date] = None,
    ) -> List[Dict]:
        """
        Calculate cumulative GDD over a growing season.
        
        Args:
            daily_temps: List of {date, min_temp, max_temp}
            crop: Crop name for base temperature lookup
            start_date: Start of accumulation (default: first date)
        
        Returns:
            List of {date, daily_gdd, cumulative_gdd}
        """
        base_temp = self.GDD_BASE_TEMPS.get(crop, self.GDD_BASE_TEMPS["default"])

        results = []
        cumulative = 0.0

        for day_data in daily_temps:
            daily_gdd = self._calc_gdd(
                [day_data.get("min_temp", 15), day_data.get("max_temp", 25)],
                base_temp=base_temp
            )
            cumulative += daily_gdd

            results.append({
                "date": day_data.get("date"),
                "daily_gdd": round(daily_gdd, 1),
                "cumulative_gdd": round(cumulative, 1),
            })

        return results

    # ===========================================
    # Stress Indices
    # ===========================================

    def _calc_heat_stress_days(
        self,
        values: List[float],
        threshold: float = None
    ) -> int:
        """Count days with max temperature above threshold."""
        threshold = threshold or self.HEAT_STRESS_THRESHOLD
        if not values:
            return 0
        return 1 if max(values) > threshold else 0

    def _calc_frost_days(
        self,
        values: List[float],
        threshold: float = None
    ) -> int:
        """Count days with min temperature below threshold."""
        threshold = threshold or self.FROST_THRESHOLD
        if not values:
            return 0
        return 1 if min(values) < threshold else 0

    def _calc_drought_days(
        self,
        values: List[float],
        threshold: float = None
    ) -> int:
        """Count days with soil moisture below threshold."""
        threshold = threshold or self.DROUGHT_THRESHOLD
        if not values:
            return 0
        return 1 if self._calc_mean(values) < threshold else 0

    def _calc_rain_days(
        self,
        values: List[float],
        threshold: float = 0.1
    ) -> int:
        """Count days with rainfall above threshold."""
        if not values:
            return 0
        return 1 if sum(values) > threshold else 0

    def _calc_leaf_wetness_hours(
        self,
        values: List[float],
        threshold: float = 50
    ) -> float:
        """Calculate hours with leaf wetness above threshold."""
        if not values:
            return 0.0
        # Assuming readings are at regular intervals
        wet_readings = sum(1 for v in values if v > threshold)
        # Convert to hours (assuming 5-min intervals)
        return wet_readings * (5 / 60)

    # ===========================================
    # Aggregate Generation
    # ===========================================

    def generate_daily_aggregates(
        self,
        environment_id: str,
        telemetry_data: Dict[str, List[Dict]],
        target_date: date,
    ) -> List[AggregateResult]:
        """
        Generate daily aggregates for an environment.
        
        Args:
            environment_id: BrAPI environment ID
            telemetry_data: Dict of sensor_type -> list of readings
            target_date: Date to aggregate
        
        Returns:
            List of AggregateResult objects
        """
        results = []
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())

        # Temperature aggregates
        if "air_temperature" in telemetry_data:
            temps = [r["value"] for r in telemetry_data["air_temperature"]]

            results.extend([
                AggregateResult(
                    parameter="air_temperature_mean",
                    value=round(self._calc_mean(temps), 1),
                    unit="°C",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    min_value=round(min(temps), 1) if temps else None,
                    max_value=round(max(temps), 1) if temps else None,
                    sample_count=len(temps),
                    calculation_method="arithmetic_mean",
                ),
                AggregateResult(
                    parameter="air_temperature_max",
                    value=round(self._calc_max(temps), 1),
                    unit="°C",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    sample_count=len(temps),
                    calculation_method="max",
                ),
                AggregateResult(
                    parameter="air_temperature_min",
                    value=round(self._calc_min(temps), 1),
                    unit="°C",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    sample_count=len(temps),
                    calculation_method="min",
                ),
                AggregateResult(
                    parameter="growing_degree_days",
                    value=round(self._calc_gdd(temps), 1),
                    unit="°C·day",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    calculation_method="single_sine_gdd",
                ),
                AggregateResult(
                    parameter="heat_stress_days",
                    value=self._calc_heat_stress_days(temps),
                    unit="days",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    calculation_method=f"count_above_{self.HEAT_STRESS_THRESHOLD}C",
                ),
                AggregateResult(
                    parameter="frost_days",
                    value=self._calc_frost_days(temps),
                    unit="days",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    calculation_method=f"count_below_{self.FROST_THRESHOLD}C",
                ),
            ])

        # Precipitation aggregates
        if "rainfall" in telemetry_data:
            rain = [r["value"] for r in telemetry_data["rainfall"]]

            results.extend([
                AggregateResult(
                    parameter="precipitation_total",
                    value=round(self._calc_sum(rain), 1),
                    unit="mm",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    sample_count=len(rain),
                    calculation_method="sum",
                ),
                AggregateResult(
                    parameter="precipitation_days",
                    value=self._calc_rain_days(rain),
                    unit="days",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    calculation_method="count_above_0.1mm",
                ),
            ])

        # Humidity aggregates
        if "relative_humidity" in telemetry_data:
            humidity = [r["value"] for r in telemetry_data["relative_humidity"]]

            results.append(
                AggregateResult(
                    parameter="relative_humidity_mean",
                    value=round(self._calc_mean(humidity), 1),
                    unit="%",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    min_value=round(min(humidity), 1) if humidity else None,
                    max_value=round(max(humidity), 1) if humidity else None,
                    sample_count=len(humidity),
                    calculation_method="arithmetic_mean",
                )
            )

        # Soil moisture aggregates
        if "soil_moisture" in telemetry_data:
            soil = [r["value"] for r in telemetry_data["soil_moisture"]]

            results.extend([
                AggregateResult(
                    parameter="soil_moisture_mean",
                    value=round(self._calc_mean(soil), 1),
                    unit="%",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    min_value=round(min(soil), 1) if soil else None,
                    max_value=round(max(soil), 1) if soil else None,
                    sample_count=len(soil),
                    calculation_method="arithmetic_mean",
                ),
                AggregateResult(
                    parameter="drought_stress_days",
                    value=self._calc_drought_days(soil),
                    unit="days",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    calculation_method=f"count_below_{self.DROUGHT_THRESHOLD}%",
                ),
            ])

        # Solar radiation aggregates
        if "par" in telemetry_data:
            par = [r["value"] for r in telemetry_data["par"]]
            # Convert PAR (µmol/m²/s) to daily MJ/m²
            # Approximate: 1 MJ/m² ≈ 2.02 mol/m² for PAR
            daily_mol = self._calc_mean(par) * 3600 * 12 / 1e6  # 12 daylight hours
            daily_mj = daily_mol / 2.02

            results.append(
                AggregateResult(
                    parameter="solar_radiation_total",
                    value=round(daily_mj, 1),
                    unit="MJ/m²",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    sample_count=len(par),
                    calculation_method="par_to_mj_conversion",
                )
            )

        # Leaf wetness aggregates
        if "leaf_wetness" in telemetry_data:
            lw = [r["value"] for r in telemetry_data["leaf_wetness"]]

            results.append(
                AggregateResult(
                    parameter="leaf_wetness_hours",
                    value=round(self._calc_leaf_wetness_hours(lw), 1),
                    unit="hours",
                    period="daily",
                    start_time=start_time,
                    end_time=end_time,
                    sample_count=len(lw),
                    calculation_method="count_above_50%",
                )
            )

        return results

    def generate_weekly_aggregates(
        self,
        daily_aggregates: List[AggregateResult],
        week_start: date,
    ) -> List[AggregateResult]:
        """
        Generate weekly aggregates from daily aggregates.
        
        Args:
            daily_aggregates: List of daily AggregateResult objects
            week_start: Start date of the week
        
        Returns:
            List of weekly AggregateResult objects
        """
        week_end = week_start + timedelta(days=6)
        start_time = datetime.combine(week_start, datetime.min.time())
        end_time = datetime.combine(week_end, datetime.max.time())

        # Group by parameter
        by_param: Dict[str, List[AggregateResult]] = {}
        for agg in daily_aggregates:
            if agg.parameter not in by_param:
                by_param[agg.parameter] = []
            by_param[agg.parameter].append(agg)

        results = []

        for param, daily_values in by_param.items():
            values = [d.value for d in daily_values]

            # Determine aggregation method based on parameter
            if param.endswith("_total") or param.endswith("_days") or param == "growing_degree_days":
                # Sum for totals and counts
                agg_value = sum(values)
                method = "sum"
            else:
                # Mean for averages
                agg_value = self._calc_mean(values)
                method = "mean_of_daily"

            results.append(
                AggregateResult(
                    parameter=param,
                    value=round(agg_value, 1),
                    unit=daily_values[0].unit,
                    period="weekly",
                    start_time=start_time,
                    end_time=end_time,
                    min_value=round(min(values), 1) if values else None,
                    max_value=round(max(values), 1) if values else None,
                    sample_count=len(values),
                    calculation_method=method,
                )
            )

        return results

    def generate_seasonal_aggregates(
        self,
        daily_aggregates: List[AggregateResult],
        season_start: date,
        season_end: date,
        season_name: str = "growing_season",
    ) -> List[AggregateResult]:
        """
        Generate seasonal aggregates from daily aggregates.
        
        Args:
            daily_aggregates: List of daily AggregateResult objects
            season_start: Start date of the season
            season_end: End date of the season
            season_name: Name of the season (e.g., "kharif", "rabi")
        
        Returns:
            List of seasonal AggregateResult objects
        """
        start_time = datetime.combine(season_start, datetime.min.time())
        end_time = datetime.combine(season_end, datetime.max.time())

        # Group by parameter
        by_param: Dict[str, List[AggregateResult]] = {}
        for agg in daily_aggregates:
            if agg.parameter not in by_param:
                by_param[agg.parameter] = []
            by_param[agg.parameter].append(agg)

        results = []

        for param, daily_values in by_param.items():
            values = [d.value for d in daily_values]

            # Determine aggregation method
            if param.endswith("_total") or param.endswith("_days") or param == "growing_degree_days":
                agg_value = sum(values)
                method = "sum"
            else:
                agg_value = self._calc_mean(values)
                method = "mean_of_daily"

            results.append(
                AggregateResult(
                    parameter=param,
                    value=round(agg_value, 1),
                    unit=daily_values[0].unit,
                    period="seasonal",
                    start_time=start_time,
                    end_time=end_time,
                    min_value=round(min(values), 1) if values else None,
                    max_value=round(max(values), 1) if values else None,
                    std_dev=round(self._calc_std_dev(values), 2) if len(values) > 1 else None,
                    sample_count=len(values),
                    calculation_method=method,
                )
            )

        return results

    # ===========================================
    # Quality Scoring
    # ===========================================

    def calculate_quality_score(
        self,
        expected_samples: int,
        actual_samples: int,
        outlier_count: int = 0,
    ) -> float:
        """
        Calculate data quality score (0-1).
        
        Args:
            expected_samples: Expected number of samples for period
            actual_samples: Actual number of samples received
            outlier_count: Number of outlier/suspect readings
        
        Returns:
            Quality score between 0 and 1
        """
        if expected_samples == 0:
            return 0.0

        completeness = min(actual_samples / expected_samples, 1.0)
        outlier_penalty = outlier_count / max(actual_samples, 1)

        return max(0, completeness - outlier_penalty)


# Singleton instance
iot_aggregation_service = IoTAggregationService()

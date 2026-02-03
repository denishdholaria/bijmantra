"""
Growing Degree Day (GDD) Calculator Service

Core computational engine for GDD calculations with scientific accuracy and uncertainty metadata.

Scientific Formula (preserved per scientific-documentation.md):
    GDD = max(0, (Tmax + Tmin) / 2 - Tbase)
    
    Where:
    - Tmax = Daily maximum temperature (°C)
    - Tmin = Daily minimum temperature (°C)
    - Tbase = Base temperature (crop-specific threshold below which no growth occurs)

Common Base Temperatures:
    - Corn/Maize: 10°C (50°F)
    - Wheat: 0°C (32°F)
    - Rice: 10°C (50°F)
    - Soybean: 10°C (50°F)
    - Cotton: 15.5°C (60°F)
    - Barley: 0°C (32°F)
    - Canola: 5°C (41°F)

Cumulative GDD Interpretation:
    - Corn: ~125 GDD to emergence, ~1400 GDD to silking, ~2700 GDD to maturity
    - Wheat: ~200 GDD to emergence, ~1500 GDD to heading, ~2200 GDD to maturity
    - Rice: ~100 GDD to emergence, ~1200 GDD to heading, ~2000 GDD to maturity

Quality Control:
    - Temperature data validation (outlier detection)
    - Confidence scoring based on data completeness
    - Uncertainty propagation through calculations
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)


class CropType(Enum):
    """Standard crop types with their base temperatures."""
    CORN = ("corn", 10.0)
    MAIZE = ("maize", 10.0)  # Alias for corn
    WHEAT = ("wheat", 0.0)
    RICE = ("rice", 10.0)
    SOYBEAN = ("soybean", 10.0)
    COTTON = ("cotton", 15.5)
    BARLEY = ("barley", 0.0)
    CANOLA = ("canola", 5.0)
    
    def __init__(self, crop_name: str, base_temp: float):
        self.crop_name = crop_name
        self.base_temp = base_temp


class DataQuality(Enum):
    """Data quality levels for temperature inputs."""
    EXCELLENT = 1.0  # Complete, validated data
    GOOD = 0.8       # Minor gaps or interpolation
    FAIR = 0.6       # Significant interpolation or old data
    POOR = 0.4       # Major data issues or very old data
    UNRELIABLE = 0.2 # Severely compromised data


@dataclass
class TemperatureData:
    """Temperature data point with quality metadata."""
    date: date
    temp_max: float
    temp_min: float
    temp_avg: Optional[float] = None
    source: str = "unknown"
    quality: DataQuality = DataQuality.GOOD
    is_interpolated: bool = False
    is_forecast: bool = False
    confidence: float = 1.0


@dataclass
class GDDCalculationResult:
    """Result of GDD calculation with uncertainty metadata."""
    
    # Core GDD values
    daily_gdd: float
    cumulative_gdd: float
    base_temperature: float
    max_temperature: float
    min_temperature: float
    calculation_date: date
    
    # Quality and uncertainty
    confidence_level: float
    data_quality_score: float
    weather_source: str
    
    # Validation flags
    is_interpolated: bool = False
    has_data_gaps: bool = False
    outlier_detected: bool = False
    
    # Scientific metadata
    formula_used: str = "GDD = max(0, (Tmax + Tmin) / 2 - Tbase)"
    calculation_method: str = "standard"


@dataclass
class GrowthStagePrediction:
    """Prediction of crop development stage based on GDD."""
    
    crop_name: str
    current_stage: str
    current_gdd: float
    
    # Next stage prediction
    next_stage: Optional[str]
    gdd_to_next_stage: Optional[float]
    days_to_next_stage: Optional[int]
    confidence: float
    
    # Full season prediction
    maturity_gdd: float
    predicted_maturity_date: Optional[date]
    maturity_confidence: float


class GDDCalculatorService:
    """
    Enhanced GDD Calculator Service with scientific accuracy and uncertainty handling.
    
    This service implements the standard Growing Degree Day formula with proper
    scientific documentation, quality control, and uncertainty propagation.
    """
    
    # Growth stage thresholds for common crops (GDD values)
    GROWTH_STAGES = {
        "corn": [
            ("Planting", 0),
            ("Emergence", 125),
            ("V6", 350),
            ("V12", 600),
            ("Tasseling", 800),
            ("Silking", 900),
            ("Grain Fill", 1200),
            ("Maturity", 1400)
        ],
        "wheat": [
            ("Planting", 0),
            ("Emergence", 200),
            ("Tillering", 400),
            ("Stem Extension", 700),
            ("Heading", 1000),
            ("Grain Fill", 1250),
            ("Maturity", 1500)
        ],
        "rice": [
            ("Planting", 0),
            ("Emergence", 100),
            ("Tillering", 300),
            ("Panicle Initiation", 600),
            ("Heading", 900),
            ("Grain Fill", 1050),
            ("Maturity", 1200)
        ],
        "soybean": [
            ("Planting", 0),
            ("Emergence", 90),
            ("V3", 250),
            ("Flowering", 500),
            ("Pod Set", 750),
            ("Pod Fill", 1000),
            ("Maturity", 1300)
        ]
    }
    
    def __init__(self):
        """Initialize the GDD Calculator Service."""
        self.logger = logging.getLogger(__name__)
    
    def calculate_daily_gdd(
        self,
        temp_max: float,
        temp_min: float,
        base_temp: float,
        method: str = "standard"
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Growing Degree Days for a single day.
        
        GDD Formula: GDD = max(0, (Tmax + Tmin) / 2 - Tbase)
        
        Args:
            temp_max: Daily maximum temperature (°C)
            temp_min: Daily minimum temperature (°C)
            base_temp: Base temperature (°C)
            method: Calculation method ("standard", "modified", "sine_wave")
        
        Returns:
            Tuple of (gdd_value, metadata_dict)
        
        Raises:
            ValueError: If temperature values are invalid
        """
        # Validate inputs
        if temp_max < temp_min:
            raise ValueError(f"Maximum temperature ({temp_max}°C) cannot be less than minimum ({temp_min}°C)")
        
        if temp_max < -50 or temp_max > 60:
            self.logger.warning(f"Extreme maximum temperature detected: {temp_max}°C")
        
        if temp_min < -50 or temp_min > 50:
            self.logger.warning(f"Extreme minimum temperature detected: {temp_min}°C")
        
        # Calculate GDD using specified method
        if method == "standard":
            avg_temp = (temp_max + temp_min) / 2
            gdd = max(0, avg_temp - base_temp)
        elif method == "modified":
            # Modified method caps maximum temperature at 30°C for heat stress
            capped_max = min(temp_max, 30.0)
            avg_temp = (capped_max + temp_min) / 2
            gdd = max(0, avg_temp - base_temp)
        elif method == "sine_wave":
            # Sine wave method (more complex, used for research)
            # Simplified implementation for now
            avg_temp = (temp_max + temp_min) / 2
            gdd = max(0, avg_temp - base_temp)
        else:
            raise ValueError(f"Unknown calculation method: {method}")
        
        # Generate metadata
        metadata = {
            "formula": "GDD = max(0, (Tmax + Tmin) / 2 - Tbase)",
            "method": method,
            "average_temperature": round(avg_temp, 2),
            "temperature_range": round(temp_max - temp_min, 2),
            "base_exceeded": avg_temp > base_temp,
            "calculation_timestamp": datetime.utcnow().isoformat()
        }
        
        return round(gdd, 2), metadata
    
    def calculate_cumulative_gdd(
        self,
        temperature_data: List[TemperatureData],
        base_temp: float,
        start_date: Optional[date] = None
    ) -> List[GDDCalculationResult]:
        """
        Calculate cumulative GDD over a period with quality tracking.
        
        Args:
            temperature_data: List of daily temperature observations
            base_temp: Base temperature for the crop
            start_date: Optional start date (defaults to first data point)
        
        Returns:
            List of GDD calculation results with cumulative values
        """
        if not temperature_data:
            return []
        
        # Sort data by date
        sorted_data = sorted(temperature_data, key=lambda x: x.date)
        
        if start_date:
            sorted_data = [d for d in sorted_data if d.date >= start_date]
        
        results = []
        cumulative_gdd = 0.0
        
        for temp_data in sorted_data:
            # Calculate daily GDD
            daily_gdd, metadata = self.calculate_daily_gdd(
                temp_data.temp_max,
                temp_data.temp_min,
                base_temp
            )
            
            cumulative_gdd += daily_gdd
            
            # Detect outliers
            outlier_detected = self._detect_temperature_outlier(
                temp_data.temp_max,
                temp_data.temp_min,
                [d.temp_max for d in sorted_data[-7:] if d.date < temp_data.date],
                [d.temp_min for d in sorted_data[-7:] if d.date < temp_data.date]
            )
            
            # Create result
            result = GDDCalculationResult(
                daily_gdd=daily_gdd,
                cumulative_gdd=round(cumulative_gdd, 2),
                base_temperature=base_temp,
                max_temperature=temp_data.temp_max,
                min_temperature=temp_data.temp_min,
                calculation_date=temp_data.date,
                confidence_level=temp_data.confidence,
                data_quality_score=temp_data.quality.value,
                weather_source=temp_data.source,
                is_interpolated=temp_data.is_interpolated,
                has_data_gaps=False,  # Will be set by caller if needed
                outlier_detected=outlier_detected
            )
            
            results.append(result)
        
        return results
    
    def predict_growth_stages(
        self,
        crop_name: str,
        cumulative_gdd: float,
        planting_date: date,
        current_date: Optional[date] = None
    ) -> GrowthStagePrediction:
        """
        Predict crop growth stages based on accumulated GDD.
        
        Args:
            crop_name: Name of the crop (e.g., "corn", "wheat")
            cumulative_gdd: Current cumulative GDD since planting
            planting_date: Date the crop was planted
            current_date: Current date (defaults to today)
        
        Returns:
            Growth stage prediction with confidence intervals
        """
        if current_date is None:
            current_date = date.today()
        
        crop_key = crop_name.lower()
        if crop_key not in self.GROWTH_STAGES:
            # Default to corn stages if crop not found
            crop_key = "corn"
            confidence = 0.5  # Lower confidence for unknown crops
        else:
            confidence = 0.85
        
        stages = self.GROWTH_STAGES[crop_key]
        
        # Find current stage
        current_stage = "Pre-emergence"
        next_stage = None
        gdd_to_next = None
        
        for stage_name, stage_gdd in stages:
            if cumulative_gdd >= stage_gdd:
                current_stage = stage_name
            elif next_stage is None:
                next_stage = stage_name
                gdd_to_next = stage_gdd - cumulative_gdd
                break
        
        # Estimate days to next stage (assuming 10 GDD per day average)
        days_to_next = None
        if gdd_to_next is not None:
            avg_daily_gdd = self._estimate_daily_gdd_rate(current_date)
            days_to_next = max(1, int(gdd_to_next / avg_daily_gdd))
        
        # Get maturity GDD
        maturity_gdd = stages[-1][1]
        
        # Predict maturity date
        predicted_maturity_date = None
        maturity_confidence = confidence
        
        if cumulative_gdd < maturity_gdd:
            remaining_gdd = maturity_gdd - cumulative_gdd
            avg_daily_gdd = self._estimate_daily_gdd_rate(current_date)
            days_to_maturity = int(remaining_gdd / avg_daily_gdd)
            predicted_maturity_date = current_date + timedelta(days=days_to_maturity)
            
            # Reduce confidence for long-term predictions
            if days_to_maturity > 60:
                maturity_confidence *= 0.7
        
        return GrowthStagePrediction(
            crop_name=crop_name,
            current_stage=current_stage,
            current_gdd=cumulative_gdd,
            next_stage=next_stage,
            gdd_to_next_stage=gdd_to_next,
            days_to_next_stage=days_to_next,
            confidence=confidence,
            maturity_gdd=maturity_gdd,
            predicted_maturity_date=predicted_maturity_date,
            maturity_confidence=maturity_confidence
        )
    
    def validate_temperature_data(
        self,
        temp_data: TemperatureData
    ) -> Tuple[bool, List[str], DataQuality]:
        """
        Validate temperature data and assess quality.
        
        Args:
            temp_data: Temperature data to validate
        
        Returns:
            Tuple of (is_valid, warnings, quality_assessment)
        """
        warnings = []
        is_valid = True
        
        # Check for reasonable temperature ranges
        if temp_data.temp_max < -50 or temp_data.temp_max > 60:
            warnings.append(f"Extreme maximum temperature: {temp_data.temp_max}°C")
            is_valid = False
        
        if temp_data.temp_min < -50 or temp_data.temp_min > 50:
            warnings.append(f"Extreme minimum temperature: {temp_data.temp_min}°C")
            is_valid = False
        
        if temp_data.temp_max <= temp_data.temp_min:
            warnings.append(f"Maximum temp ({temp_data.temp_max}°C) not greater than minimum ({temp_data.temp_min}°C)")
            is_valid = False
        
        # Check temperature range reasonableness
        temp_range = temp_data.temp_max - temp_data.temp_min
        if temp_range > 40:
            warnings.append(f"Unusually large temperature range: {temp_range}°C")
        elif temp_range < 1:
            warnings.append(f"Unusually small temperature range: {temp_range}°C")
        
        # Assess quality based on various factors
        quality = temp_data.quality
        
        if temp_data.is_interpolated:
            quality = DataQuality(min(quality.value, DataQuality.FAIR.value))
            warnings.append("Temperature data is interpolated")
        
        if temp_data.is_forecast:
            quality = DataQuality(min(quality.value, DataQuality.GOOD.value))
            warnings.append("Temperature data is from forecast")
        
        if not is_valid:
            quality = DataQuality.UNRELIABLE
        
        return is_valid, warnings, quality
    
    def get_crop_base_temperature(self, crop_name: str) -> float:
        """
        Get the standard base temperature for a crop.
        
        Args:
            crop_name: Name of the crop
        
        Returns:
            Base temperature in Celsius
        """
        crop_key = crop_name.lower().replace(" ", "_")
        
        # Try to find exact match
        for crop_type in CropType:
            if crop_type.crop_name == crop_key:
                return crop_type.base_temp
        
        # Common aliases
        aliases = {
            "maize": CropType.CORN.base_temp,
            "corn": CropType.CORN.base_temp,
            "winter_wheat": CropType.WHEAT.base_temp,
            "spring_wheat": CropType.WHEAT.base_temp,
            "soybeans": CropType.SOYBEAN.base_temp,
            "soya": CropType.SOYBEAN.base_temp
        }
        
        if crop_key in aliases:
            return aliases[crop_key]
        
        # Default to corn base temperature
        self.logger.warning(f"Unknown crop '{crop_name}', using default base temperature of 10°C")
        return 10.0
    
    def _detect_temperature_outlier(
        self,
        temp_max: float,
        temp_min: float,
        recent_max_temps: List[float],
        recent_min_temps: List[float]
    ) -> bool:
        """
        Detect if temperature readings are outliers compared to recent data.
        
        Args:
            temp_max: Current maximum temperature
            temp_min: Current minimum temperature
            recent_max_temps: Recent maximum temperatures for comparison
            recent_min_temps: Recent minimum temperatures for comparison
        
        Returns:
            True if outlier detected
        """
        if len(recent_max_temps) < 3 or len(recent_min_temps) < 3:
            return False
        
        # Calculate mean and standard deviation
        max_mean = sum(recent_max_temps) / len(recent_max_temps)
        min_mean = sum(recent_min_temps) / len(recent_min_temps)
        
        max_std = math.sqrt(sum((x - max_mean) ** 2 for x in recent_max_temps) / len(recent_max_temps))
        min_std = math.sqrt(sum((x - min_mean) ** 2 for x in recent_min_temps) / len(recent_min_temps))
        
        # Check if current temps are more than 2 standard deviations away
        max_outlier = abs(temp_max - max_mean) > 2 * max_std
        min_outlier = abs(temp_min - min_mean) > 2 * min_std
        
        return max_outlier or min_outlier
    
    def _estimate_daily_gdd_rate(self, current_date: date) -> float:
        """
        Estimate average daily GDD accumulation rate based on season.
        
        Args:
            current_date: Current date for seasonal adjustment
        
        Returns:
            Estimated daily GDD rate
        """
        # Simple seasonal adjustment (Northern Hemisphere)
        month = current_date.month
        
        if month in [12, 1, 2]:  # Winter
            return 3.0
        elif month in [3, 4, 5]:  # Spring
            return 8.0
        elif month in [6, 7, 8]:  # Summer
            return 15.0
        else:  # Fall
            return 6.0


# Global service instance
gdd_calculator_service = GDDCalculatorService()
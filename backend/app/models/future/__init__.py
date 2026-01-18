"""
Future Models Package

Models for planned BijMantra modules (Tier 1-3 from futureWorkspaces.ts).
These models support the expansion roadmap defined in the reference apps analysis.

Modules:
- Crop Intelligence: calendars, yield prediction, suitability, GDD
- Soil & Nutrients: tests, recommendations, health, carbon
- Crop Protection: pests, disease forecasts, spray, IPM
- Water & Irrigation: schedules, balance, moisture, footprint
- Market & Economics: prices, budgets, inventory, contracts
"""

# Crop Intelligence
from app.models.future.gdd_log import GrowingDegreeDayLog
from app.models.future.crop_calendar import CropCalendar
from app.models.future.crop_suitability import CropSuitability
from app.models.future.yield_prediction import YieldPrediction

# Soil & Nutrients
from app.models.future.fertilizer_recommendation import FertilizerRecommendation
from app.models.future.soil_test import SoilTest
from app.models.future.soil_health_score import SoilHealthScore
from app.models.future.carbon_sequestration import CarbonSequestration

# Water & Irrigation
from app.models.future.field import Field
from app.models.future.water_balance import WaterBalance
from app.models.future.irrigation_schedule import IrrigationSchedule, IrrigationStatus
from app.models.future.soil_moisture_reading import SoilMoistureReading

# Crop Protection
from app.models.future.disease_risk_forecast import DiseaseRiskForecast
from app.models.future.spray_application import SprayApplication
from app.models.future.pest_observation import PestObservation
from app.models.future.ipm_strategy import IPMStrategy

__all__ = [
    # Crop Intelligence
    "GrowingDegreeDayLog",
    "CropCalendar",
    "CropSuitability",
    "YieldPrediction",
    # Soil & Nutrients
    "FertilizerRecommendation",
    "SoilTest",
    "SoilHealthScore",
    "CarbonSequestration",
    # Water & Irrigation
    "Field",
    "WaterBalance",
    "IrrigationSchedule",
    "IrrigationStatus",
    "SoilMoistureReading",
    # Crop Protection
    "DiseaseRiskForecast",
    "SprayApplication",
    "PestObservation",
    "IPMStrategy",
]

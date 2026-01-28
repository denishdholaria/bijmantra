"""
Future Module API Routers

FastAPI routers for planned BijMantra modules (Tier 1-3).
All routers follow BijMantra patterns:
- Async endpoints with AsyncSession
- Multi-tenant isolation via organization_id
- BrAPI-compliant response format
- Proper authentication dependencies

Modules:
- Crop Intelligence: calendars, yield prediction, suitability, GDD
- Soil & Nutrients: tests, recommendations, health, carbon
- Crop Protection: pests, disease forecasts, spray, IPM
- Water & Irrigation: schedules, balance, moisture, footprint
"""

from app.api.v2.future.crop_calendar import router as crop_calendar_router
from app.api.v2.future.gdd import router as gdd_router
from app.api.v2.future.crop_suitability import router as crop_suitability_router
from app.api.v2.future.yield_prediction import router as yield_prediction_router
from app.api.v2.future.soil_test import router as soil_test_router
from app.api.v2.future.fertilizer_recommendation import router as fertilizer_recommendation_router
from app.api.v2.future.soil_health import router as soil_health_router
from app.api.v2.future.carbon_sequestration import router as carbon_sequestration_router
from app.api.v2.future.pest_observation import router as pest_observation_router
from app.api.v2.future.disease_risk_forecast import router as disease_risk_forecast_router
from app.api.v2.future.spray_application import router as spray_application_router
from app.api.v2.future.ipm_strategy import router as ipm_strategy_router
from app.api.v2.future.irrigation_schedule import router as irrigation_schedule_router
from app.api.v2.future.water_balance import router as water_balance_router
from app.api.v2.future.soil_moisture import router as soil_moisture_router

__all__ = [
    # Crop Intelligence
    "crop_calendar_router",
    "gdd_router",
    "crop_suitability_router",
    "yield_prediction_router",
    # Soil & Nutrients
    "soil_test_router",
    "fertilizer_recommendation_router",
    "soil_health_router",
    "carbon_sequestration_router",
    # Crop Protection
    "pest_observation_router",
    "disease_risk_forecast_router",
    "spray_application_router",
    "ipm_strategy_router",
    # Water & Irrigation
    "irrigation_schedule_router",
    "water_balance_router",
    "soil_moisture_router",
]

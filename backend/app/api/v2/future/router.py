"""
Future / Earth Systems Router Aggregator
Combines all "Crop Intelligence" & "Earth Systems" future endpoints.
"""
from fastapi import APIRouter

from app.api.v2.future import (
    yield_prediction,
    crop_suitability,
    gdd,
    soil_test,
    fertilizer_recommendation,
    soil_health,
    carbon_sequestration,
    pest_observation,
    disease_risk_forecast,
    spray_application,
    ipm_strategy,
    irrigation_schedule,
    water_balance,
    soil_moisture,
)

future_router = APIRouter(tags=["Future - Earth Systems"])

# Crop Intelligence
future_router.include_router(yield_prediction.router, tags=["Yield Prediction"])
future_router.include_router(crop_suitability.router, tags=["Crop Suitability"])

# Growing Degree Days
future_router.include_router(gdd.router, tags=["Growing Degree Days"])

# Soil & Fertilizer
future_router.include_router(soil_test.router, prefix="/future", tags=["Soil Tests"])
future_router.include_router(fertilizer_recommendation.router, prefix="/future", tags=["Fertilizer Recommendations"])
future_router.include_router(soil_health.router, prefix="/future", tags=["Soil Health"])
future_router.include_router(carbon_sequestration.router, prefix="/future", tags=["Carbon Sequestration"])

# Pest & Disease
future_router.include_router(pest_observation.router, tags=["Pest Observations"])
future_router.include_router(disease_risk_forecast.router, tags=["Disease Risk Forecasts"])
future_router.include_router(spray_application.router, tags=["Spray Applications"])
future_router.include_router(ipm_strategy.router, tags=["IPM Strategies"])

# Water & Irrigation
future_router.include_router(irrigation_schedule.router, prefix="/future", tags=["Irrigation Schedules"])
future_router.include_router(water_balance.router, prefix="/future", tags=["Water Balance"])
future_router.include_router(soil_moisture.router, prefix="/future", tags=["Soil Moisture"])

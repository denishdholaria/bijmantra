"""
Future Module CRUD Operations

CRUD operations for planned BijMantra modules (Tier 1-3).
All CRUD classes inherit from CRUDBase and support:
- Async database operations
- Multi-tenant filtering via organization_id
- Pagination with total count
"""

from . import (
    carbon_sequestration,
    crop_calendar,
    crop_suitability,
    disease_risk_forecast,
    fertilizer_recommendation,
    gdd,
    ipm_strategy,
    irrigation_schedule,
    pest_observation,
    soil_health,
    soil_moisture,
    soil_test,
    spray_application,
    water_balance,
    yield_prediction,
)

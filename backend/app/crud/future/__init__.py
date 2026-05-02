"""Future CRUD package.

Avoid eager sibling imports here so targeted imports like
``from app.crud.future import pest_observation`` do not pull every future CRUD
module into memory and create unnecessary import chains during tests.
"""

__all__ = [
    "carbon_sequestration",
    "crop_calendar",
    "crop_suitability",
    "disease_risk_forecast",
    "fertilizer_recommendation",
    "gdd",
    "ipm_strategy",
    "irrigation_schedule",
    "pest_observation",
    "soil_health",
    "soil_moisture",
    "soil_test",
    "spray_application",
    "water_balance",
    "yield_prediction",
]

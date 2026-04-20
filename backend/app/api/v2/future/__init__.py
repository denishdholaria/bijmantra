"""Future module package.

Keep this package initializer lightweight so individual future-module routers can
be imported without eagerly importing every sibling module. This avoids circular
imports during unit tests and targeted route imports while preserving normal
package-based access such as ``from app.api.v2.future import pest_observation``.
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

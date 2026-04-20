"""
Environment Domain Module

Handles weather, climate data, and environmental conditions.
"""

from .services import (
    EnvironmentalPhysicsService,
    environmental_service,
    FieldEnvironmentService,
    FieldHistory,
    InputLog,
    InputType,
    IrrigationEvent,
    IrrigationType,
    SoilProfile,
    SoilTexture,
    GDDCalculatorService,
    gdd_calculator_service,
    GEEIntegrationService,
    get_gee_service,
    weather_client,
    WeatherService,
    weather_service,
)

__all__ = [
    "EnvironmentalPhysicsService",
    "environmental_service",
    "FieldEnvironmentService",
    "FieldHistory",
    "InputLog",
    "InputType",
    "IrrigationEvent",
    "IrrigationType",
    "SoilProfile",
    "SoilTexture",
    "GDDCalculatorService",
    "gdd_calculator_service",
    "GEEIntegrationService",
    "get_gee_service",
    "weather_client",
    "WeatherService",
    "weather_service",
]

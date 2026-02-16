"""
Future Module Schemas

Pydantic schemas for planned BijMantra modules (Tier 1-3).
Matches models in app/models/future/.
"""

from app.schemas.future.crop_intelligence import (
    GrowingDegreeDayLogBase,
    GrowingDegreeDayLogCreate,
    GrowingDegreeDayLogUpdate,
    GrowingDegreeDayLog,
    CropCalendarBase,
    CropCalendarCreate,
    CropCalendarUpdate,
    CropCalendar,
    CropSuitabilityBase,
    CropSuitabilityCreate,
    CropSuitability,
    YieldPredictionBase,
    YieldPredictionCreate,
    YieldPrediction,
)

from app.schemas.future.gdd_prediction import (
    GDDPredictionBase,
    GDDPredictionCreate,
    GDDPredictionUpdate,
    GDDPredictionResponse,
)

from app.schemas.future.soil_nutrients import (
    SoilTestBase,
    SoilTestCreate,
    SoilTestUpdate,
    SoilTest,
    SoilHealthScoreBase,
    SoilHealthScoreCreate,
    SoilHealthScore,
    FertilizerRecommendationBase,
    FertilizerRecommendationCreate,
    FertilizerRecommendation,
    CarbonSequestrationBase,
    CarbonSequestrationCreate,
    CarbonSequestration,
    NutrientSufficiencyParams,
    NutrientSufficiency,
)

from app.schemas.future.water_irrigation import (
    FieldBase,
    FieldCreate,
    FieldUpdate,
    Field as FieldSchema,
    WaterBalanceBase,
    WaterBalanceCreate,
    WaterBalance,
    IrrigationScheduleBase,
    IrrigationScheduleCreate,
    IrrigationScheduleUpdate,
    IrrigationSchedule,
    IrrigationStatus,
    SoilMoistureReadingBase,
    SoilMoistureReadingCreate,
    SoilMoistureReading,
)

from app.schemas.future.crop_protection import (
    DiseaseRiskForecastBase,
    DiseaseRiskForecastCreate,
    DiseaseRiskForecast,
    SprayApplicationBase,
    SprayApplicationCreate,
    SprayApplicationUpdate,
    SprayApplication,
    PestObservationBase,
    PestObservationCreate,
    PestObservation,
    IPMStrategyBase,
    IPMStrategyCreate,
    IPMStrategyUpdate,
    IPMStrategy,
)

__all__ = [
    # Crop Intelligence
    "GrowingDegreeDayLogBase", "GrowingDegreeDayLogCreate", "GrowingDegreeDayLogUpdate", "GrowingDegreeDayLog",
    "GDDPredictionBase", "GDDPredictionCreate", "GDDPredictionUpdate", "GDDPredictionResponse",
    "CropCalendarBase", "CropCalendarCreate", "CropCalendarUpdate", "CropCalendar",
    "CropSuitabilityBase", "CropSuitabilityCreate", "CropSuitability",
    "YieldPredictionBase", "YieldPredictionCreate", "YieldPrediction",
    # Soil & Nutrients
    "SoilTestBase", "SoilTestCreate", "SoilTestUpdate", "SoilTest",
    "SoilHealthScoreBase", "SoilHealthScoreCreate", "SoilHealthScore",
    "FertilizerRecommendationBase", "FertilizerRecommendationCreate", "FertilizerRecommendation",
    "CarbonSequestrationBase", "CarbonSequestrationCreate", "CarbonSequestration",
    "NutrientSufficiencyParams", "NutrientSufficiency",
    # Water & Irrigation
    "FieldBase", "FieldCreate", "FieldUpdate", "FieldSchema",
    "WaterBalanceBase", "WaterBalanceCreate", "WaterBalance",
    "IrrigationScheduleBase", "IrrigationScheduleCreate", "IrrigationScheduleUpdate", "IrrigationSchedule", "IrrigationStatus",
    "SoilMoistureReadingBase", "SoilMoistureReadingCreate", "SoilMoistureReading",
    # Crop Protection
    "DiseaseRiskForecastBase", "DiseaseRiskForecastCreate", "DiseaseRiskForecast",
    "SprayApplicationBase", "SprayApplicationCreate", "SprayApplicationUpdate", "SprayApplication",
    "PestObservationBase", "PestObservationCreate", "PestObservation",
    "IPMStrategyBase", "IPMStrategyCreate", "IPMStrategyUpdate", "IPMStrategy",
]

from datetime import date
from typing import Dict, Any
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.future import soil_test as soil_test_crud
from app.schemas.future.soil_nutrients import NutrientSufficiency, SoilTest

# In a real application, this would be in a database or a more complex configuration file.
CROP_NUTRIENT_RANGES = {
    "default": {
        "ph": {"low": 6.0, "high": 7.0},
        "p_ppm": {"low": 15, "high": 30},
        "k_ppm": {"low": 100, "high": 150},
        "s_ppm": {"low": 10, "high": 20},
        "zn_ppm": {"low": 0.8, "high": 1.5},
    },
    "corn": {
        "ph": {"low": 6.0, "high": 6.8},
        "p_ppm": {"low": 20, "high": 30},
        "k_ppm": {"low": 100, "high": 150},
        "s_ppm": {"low": 10, "high": 15},
        "zn_ppm": {"low": 0.8, "high": 1.2},
    },
}

async def calculate_nutrient_sufficiency(
    db: AsyncSession, *, soil_test_id: int, target_crop: str
) -> NutrientSufficiency:
    """
    Analyzes the nutrient sufficiency of a soil test for a specific crop.

    Args:
        db: The database session.
        soil_test_id: The ID of the soil test to analyze.
        target_crop: The name of the target crop.

    Returns:
        A NutrientSufficiency object with the analysis results.

    Raises:
        HTTPException: If the soil test is not found.
    """
    soil_test = await soil_test_crud.soil_test.get(db, id=soil_test_id)
    if not soil_test:
        raise HTTPException(status_code=404, detail="Soil test not found")

    ranges = CROP_NUTRIENT_RANGES.get(target_crop.lower(), CROP_NUTRIENT_RANGES["default"])

    sufficiency_levels: Dict[str, Dict[str, Any]] = {}
    low_nutrients = []
    high_nutrients = []

    for nutrient, range_values in ranges.items():
        value = getattr(soil_test, nutrient, None)
        if value is not None:
            status = "Sufficient"
            if value < range_values["low"]:
                status = "Low"
                low_nutrients.append(nutrient)
            elif value > range_values["high"]:
                status = "High"
                high_nutrients.append(nutrient)

            sufficiency_levels[nutrient] = {
                "value": value,
                "status": status,
                "range": f"{range_values['low']}-{range_values['high']}"
            }

    summary = "Overall nutrient levels are sufficient."
    if low_nutrients:
        summary = f"Low levels of: {', '.join(low_nutrients)}. "
    if high_nutrients:
        summary += f"High levels of: {', '.join(high_nutrients)}."

    return NutrientSufficiency(
        soil_test_id=soil_test.id,
        target_crop=target_crop,
        analysis_date=date.today(),
        sufficiency_levels=sufficiency_levels,
        summary=summary.strip(),
    )

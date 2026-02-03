
import logging
import math
from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from app.models.future.gdd_log import GrowingDegreeDayLog
from app.services.gdd_calculator_service import gdd_calculator_service, GrowthStagePrediction

logger = logging.getLogger(__name__)

class ProcessBasedPredictor:
    """
    Process-Based Crop Growth Simulator (Simplified DSSAT).

    Implements Task 2:
    - 2.1 Create crop growth simulation service
    - 2.2 Add biomass accumulation calculations
    - 2.3 Implement stress factor calculations
    - 2.4 Add grain partitioning and harvest index logic
    """

    # Crop parameters (Simplified)
    CROP_PARAMS = {
        "corn": {"RUE": 1.6, "HI": 0.5, "BaseTemp": 10.0, "OptTemp": 25.0}, # RUE: Radiation Use Efficiency (g/MJ)
        "maize": {"RUE": 1.6, "HI": 0.5, "BaseTemp": 10.0, "OptTemp": 25.0},
        "wheat": {"RUE": 1.4, "HI": 0.45, "BaseTemp": 0.0, "OptTemp": 20.0},
        "rice": {"RUE": 1.2, "HI": 0.45, "BaseTemp": 10.0, "OptTemp": 28.0},
        "soybean": {"RUE": 1.0, "HI": 0.4, "BaseTemp": 10.0, "OptTemp": 25.0},
    }

    async def predict(
        self,
        db: AsyncSession,
        field_id: int,
        crop_name: str,
        planting_date: date,
        org_id: int,
        solar_radiation: float = 20.0 # MJ/m2/day average if not provided
    ) -> Dict:
        """
        Predict yield using process-based simulation.
        """
        # 1. Get Cumulative GDD
        gdd_logs = await self._get_gdd_logs(db, field_id, crop_name, planting_date, org_id)

        if not gdd_logs:
            logger.warning(f"No GDD logs found for field {field_id}, crop {crop_name}")
            return {
                "predicted_yield": None,
                "confidence_interval": None,
                "method": "process_based",
                "status": "insufficient_data",
                "message": "No GDD logs found for this field and crop."
            }

        current_gdd = gdd_logs[-1].cumulative_gdd
        last_log_date = gdd_logs[-1].log_date

        # 2. Predict Growth Stage
        stage_prediction: GrowthStagePrediction = gdd_calculator_service.predict_growth_stages(
            crop_name, current_gdd, planting_date, last_log_date
        )

        # 3. Biomass Accumulation (2.2)
        # Simplified: Biomass = RUE * IPAR * Days
        # IPAR (Intercepted Photosynthetically Active Radiation) depends on LAI (Leaf Area Index)
        # LAI depends on GDD

        params = self.CROP_PARAMS.get(crop_name.lower(), self.CROP_PARAMS["corn"])
        rue = params["RUE"]

        # Simulate day by day
        total_biomass = 0.0
        stress_factor = 1.0 # 2.3 Stress Factors (simplified)

        for log in gdd_logs:
            # Estimate LAI based on GDD (Logistic function)
            # Max LAI ~ 5-6
            if log.cumulative_gdd > 0:
                 lai = 5.0 / (1 + math.exp(-0.005 * (log.cumulative_gdd - 700))) # Sigmoid curve
            else:
                 lai = 0.0

            # Fraction of intercepted radiation
            f_intercepted = 1 - math.exp(-0.65 * lai)

            # Daily biomass gain
            # Assumes constant solar radiation for now if not in log
            daily_biomass = rue * f_intercepted * solar_radiation * 0.5 # 0.5 is PAR fraction

            # Apply Temperature Stress (Heat)
            if log.max_temperature is not None and log.min_temperature is not None:
                t_avg = (log.max_temperature + log.min_temperature) / 2
                if t_avg > params["OptTemp"] + 10:
                    current_stress = max(0, 1 - 0.05 * (t_avg - (params["OptTemp"] + 10)))
                    stress_factor = min(stress_factor, current_stress)

            # Apply Water Stress (Stub)
            # water_stress = self._calculate_water_stress(...)
            # stress_factor *= water_stress

            total_biomass += daily_biomass * stress_factor

        # 4. Grain Partitioning (2.4)
        # Harvest Index increases during reproductive stages
        if stage_prediction.maturity_confidence > 0.5 and stage_prediction.predicted_maturity_date:
            # Project remaining biomass until maturity
            days_remaining = (stage_prediction.predicted_maturity_date - last_log_date).days
            if days_remaining > 0:
                projected_biomass = total_biomass + (days_remaining * rue * 0.9 * solar_radiation * 0.5) # 0.9 assuming full canopy
            else:
                projected_biomass = total_biomass
        else:
            projected_biomass = total_biomass # If maturity unknown, use current

        predicted_yield = projected_biomass * params["HI"] * 0.01 # Convert g/m2 to t/ha (approx factor)

        return {
            "predicted_yield": round(predicted_yield, 2),
            "biomass_g_m2": round(projected_biomass, 2),
            "current_stage": stage_prediction.current_stage,
            "days_to_maturity": stage_prediction.days_to_next_stage,
            "predicted_maturity_date": stage_prediction.predicted_maturity_date,
            "stress_factors": {
                "temperature": round(stress_factor, 2),
                "water": 1.0 # Placeholder
            },
            "method": "process_based",
            "status": "success"
        }

    async def _get_gdd_logs(self, db: AsyncSession, field_id: int, crop_name: str, planting_date: date, org_id: int) -> List[GrowingDegreeDayLog]:
        query = select(GrowingDegreeDayLog).where(
            GrowingDegreeDayLog.organization_id == org_id,
            GrowingDegreeDayLog.field_id == field_id,
            GrowingDegreeDayLog.crop_name == crop_name,
            GrowingDegreeDayLog.planting_date == planting_date
        ).order_by(GrowingDegreeDayLog.log_date)
        result = await db.execute(query)
        return list(result.scalars().all())

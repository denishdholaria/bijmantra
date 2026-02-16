"""
Biosimulation Service
Phenology Prediction and Biomass Simulation
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.biosimulation import CropModel, SimulationRun
from app.services.environmental_physics import environmental_service

class BiosimulationService:
    """
    Simulation engine for crop growth and development.
    """

    def simulate_phenology(
        self,
        daily_gdd: List[float],
        crop_model: CropModel
    ) -> Dict[str, int]:
        """
        Predict days to key phenological stages based on GDD accumulation.
        Returns: { "emergence_day": int, "flowering_day": int, "maturity_day": int }
        """
        accumulated_gdd = 0.0
        stages = {}

        gdd_reqs = {
            "emergence": crop_model.gdd_emergence or 100,
            "flowering": crop_model.gdd_flowering or 800,
            "maturity": crop_model.gdd_maturity or 1600
        }

        for day_idx, gdd in enumerate(daily_gdd):
            accumulated_gdd += gdd

            if "emergence" not in stages and accumulated_gdd >= gdd_reqs["emergence"]:
                stages["emergence"] = day_idx + 1

            if "flowering" not in stages and accumulated_gdd >= gdd_reqs["flowering"]:
                stages["flowering"] = day_idx + 1

            if "maturity" not in stages and accumulated_gdd >= gdd_reqs["maturity"]:
                stages["maturity"] = day_idx + 1
                break # Stop after maturity

        return stages

    def simulate_biomass(
        self,
        daily_par: List[float], # Photosynthetically Active Radiation (MJ/m2)
        crop_model: CropModel,
        stress_factors: Optional[List[float]] = None # 0-1 scale (1=no stress)
    ) -> float:
        """
        Calculate potential biomass using Radiation Use Efficiency (RUE).
        Biomass = Sum( PAR * RUE * StressFactor )
        """
        total_biomass = 0.0
        rue = crop_model.rue or 1.5 # g/MJ

        for i, par in enumerate(daily_par):
            stress = stress_factors[i] if stress_factors and i < len(stress_factors) else 1.0

            daily_gain = par * rue * stress
            total_biomass += daily_gain

        return total_biomass

    async def run_simulation(
        self,
        db: AsyncSession,
        organization_id: int,
        crop_model_id: int,
        location_id: int,
        start_date: datetime,
        daily_weather_data: List[Dict] # [{t_max, t_min, par...}]
    ) -> SimulationRun:
        """
        Execute a full simulation run.
        """
        # Fetch model
        stmt = select(CropModel).where(CropModel.id == crop_model_id)
        result = await db.execute(stmt)
        crop_model = result.scalar_one_or_none()

        if not crop_model:
            raise ValueError(f"CropModel {crop_model_id} not found")

        # 1. Calculate Daily GDD
        daily_gdd = []
        for day in daily_weather_data:
            gdd = await environmental_service.calculate_gdd(
                day["t_max"],
                day["t_min"],
                t_base=crop_model.base_temp
            )
            daily_gdd.append(gdd)

        # 2. Simulate Phenology
        phenology_stages = self.simulate_phenology(daily_gdd, crop_model)

        # Calculate dates
        flowering_date = start_date + timedelta(days=phenology_stages.get("flowering", 0))
        maturity_date = start_date + timedelta(days=phenology_stages.get("maturity", 0))

        # 3. Simulate Biomass (Simple RUE model)
        # Mock PAR if missing: assume 0.5 * SolarRad or typically 8-10 MJ/m2 in summer
        daily_par = [day.get("par", 9.0) for day in daily_weather_data]
        total_biomass = self.simulate_biomass(daily_par, crop_model)

        predicted_yield = total_biomass * (crop_model.harvest_index or 0.5)

        # Save run
        run = SimulationRun(
            organization_id=organization_id,
            model_id=crop_model_id,
            location_id=location_id,
            start_date=start_date,
            predicted_flowering_date=flowering_date,
            predicted_maturity_date=maturity_date,
            predicted_yield=predicted_yield,
            predicted_biomass=total_biomass,
            status="COMPLETED"
        )

        db.add(run)
        await db.commit()
        await db.refresh(run)
        return run

# Global instance
biosimulation_service = BiosimulationService()

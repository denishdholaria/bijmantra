from typing import Dict, Any
from app.models.mars import MarsFailureMode
from app.modules.space.mars.schemas import MarsEnvironmentProfileBase

class MarsOptimizer:
    @staticmethod
    def simulate_trial(profile: MarsEnvironmentProfileBase, generation: int) -> Dict[str, Any]:
        """
        Deterministic simulation of plant performance in Mars environment.
        Logic is heuristic-based for Phase 1.
        """
        failure_mode = MarsFailureMode.UNKNOWN
        survival_score = 1.0
        biomass_yield = 100.0 # Base yield units

        # 1. Atmospheric Pressure Check
        # Mars surface is ~0.6 kPa. Earth is 101.3 kPa.
        # Plants need at least ~10 kPa (Armstrong limit for water boiling at body temp is higher, but plants need vapor pressure control)
        if profile.pressure_kpa < 5.0:
            failure_mode = MarsFailureMode.ATMOSPHERIC_COLLAPSE
            survival_score = 0.0
            biomass_yield = 0.0
            return MarsOptimizer._package_result(survival_score, biomass_yield, failure_mode)

        # 2. Radiation Check
        # Earth is ~2-3 mSv/year. Mars trip is ~1000 mSv.
        if profile.radiation_msv > 2000.0:
            failure_mode = MarsFailureMode.RADIATION_DAMAGE
            survival_score = 0.0
            biomass_yield = 0.0
            return MarsOptimizer._package_result(survival_score, biomass_yield, failure_mode)
        elif profile.radiation_msv > 500.0:
            survival_score *= 0.5
            biomass_yield *= 0.4
            failure_mode = MarsFailureMode.RADIATION_DAMAGE # Partial damage

        # 3. O2 Check (Plants need O2 for respiration at night)
        if profile.o2_ppm < 500.0:
            failure_mode = MarsFailureMode.PHYSIOLOGICAL_LIMIT
            survival_score *= 0.1
            biomass_yield *= 0.1

        # 4. CO2 Check (Photosynthesis)
        if profile.co2_ppm < 50.0:
             failure_mode = MarsFailureMode.PHYSIOLOGICAL_LIMIT
             survival_score *= 0.2
             biomass_yield *= 0.1

        # 5. Gravity Check
        if profile.gravity_factor < 0.1:
            # Very low gravity issues
            survival_score *= 0.6
            biomass_yield *= 0.5

        # Final determination
        if survival_score < 0.1:
             if failure_mode == MarsFailureMode.UNKNOWN:
                 failure_mode = MarsFailureMode.PHYSIOLOGICAL_LIMIT
             survival_score = 0.0
             biomass_yield = 0.0
        else:
             # If survived well and no specific failure set, it remains UNKNOWN (which implies survival/no failure in this context, or we need a NONE mode?)
             # Spec says "Failure modes MUST be classified as one of... UNKNOWN".
             # We will leave it as UNKNOWN if no specific failure occurred.
             pass

        # Closed Loop Metrics
        # Heuristics
        # Water recycling decreases if temperature is too high (evaporation loss/leakage)
        avg_temp = 20.0
        if isinstance(profile.temperature_profile, dict):
            avg_temp = float(profile.temperature_profile.get("average", 20.0))

        water_recycling_pct = 98.0 - (abs(avg_temp - 20.0) * 0.2)
        water_recycling_pct = max(0.0, min(100.0, water_recycling_pct))

        nutrient_loss_pct = 2.0 + (generation * 0.5)

        # Energy input increases with lower pressure (pressurization cost) and gravity control
        energy_input_kwh = 100.0 + (100.0 / (profile.pressure_kpa + 0.1))

        oxygen_output = biomass_yield * 1.2 # Photosynthesis ratio

        return {
            "survival_score": round(survival_score, 2),
            "biomass_yield": round(biomass_yield, 2),
            "failure_mode": failure_mode,
            "closed_loop_metrics": {
                "water_recycling_pct": round(water_recycling_pct, 2),
                "nutrient_loss_pct": round(nutrient_loss_pct, 2),
                "energy_input_kwh": round(energy_input_kwh, 2),
                "oxygen_output": round(oxygen_output, 2)
            }
        }

    @staticmethod
    def _package_result(survival, yield_val, failure):
        return {
            "survival_score": survival,
            "biomass_yield": yield_val,
            "failure_mode": failure,
            "closed_loop_metrics": {
                "water_recycling_pct": 0.0,
                "nutrient_loss_pct": 0.0,
                "energy_input_kwh": 0.0,
                "oxygen_output": 0.0
            }
        }

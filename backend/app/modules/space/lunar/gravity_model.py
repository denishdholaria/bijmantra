import math
import random
from app.modules.space.lunar.schemas import FailureMode, LunarEnvironmentProfileBase

class FractionalGravityEnvironmentEngine:
    def simulate(self, profile: LunarEnvironmentProfileBase, generation: int, germplasm_id: int) -> dict:
        """
        Deterministic simulation of fractional gravity effects (FGEE).
        Models gravity as a first-class biological stressor.
        """

        # Deterministic variation based on germplasm_id
        # This ensures that the same germplasm in the same environment always produces the same result
        rng = random.Random(germplasm_id)
        # Germplasm resilience factors (pseudo-randomly assigned based on ID)
        root_resilience = rng.uniform(0.8, 1.2)
        photoperiod_tolerance = rng.uniform(0.8, 1.2)
        general_vigor = rng.uniform(0.8, 1.2)

        # 1. Anchorage Score
        # Gravity helps roots go down (gravitropism). Less gravity = less orientation.
        # Root support helps.
        # Formula: (gravity_factor / 0.3) * weight + (root_support_factor * weight)
        # Normalized to 0-1.
        # 0.3g is the max considered in this model (Martian/Lunar range). Lunar is 0.16g.
        gravity_contribution = (profile.gravity_factor / 0.3) * 0.6
        support_contribution = profile.root_support_factor * 0.4
        anchorage_score = (gravity_contribution + support_contribution) * root_resilience
        anchorage_score = min(max(anchorage_score, 0.0), 1.0)

        # 2. Morphology Stability
        # Photoperiod stress. Long days/nights cause circadian disruption.
        # Stability drops as cycle length deviates from 24h.
        cycle_length_days = profile.light_cycle_days + profile.dark_cycle_days
        # Ideal is 1 day.
        # Stress increases as we move away from 1.
        # Lunar day is ~29.5 days.
        photoperiod_stress = max(0.0, (cycle_length_days - 1.0) / 28.0) # 0 at 1 day, ~1 at 29 days

        # Gravity also affects morphology (turgor pressure, fluid dynamics)
        gravity_stability = math.sqrt(profile.gravity_factor / 0.3)

        morphology_stability = gravity_stability * (1.0 - (photoperiod_stress / photoperiod_tolerance))
        morphology_stability = min(max(morphology_stability, 0.0), 1.0)

        # 3. Yield Index
        # Combination of stability, anchorage, and atmospheric conditions.
        # Low pressure reduces yield.
        pressure_factor = min(profile.habitat_pressure_kpa / 101.3, 1.0)

        yield_index = morphology_stability * anchorage_score * pressure_factor * general_vigor

        # Generation decay (multigenerational instability)
        if generation > 1:
            yield_index *= (0.9 ** (generation - 1))

        yield_index = min(max(yield_index, 0.0), 1.0)

        # 4. Determine Failure Mode
        # Identify the primary bottleneck
        failure_mode = FailureMode.UNKNOWN

        # Thresholds for failure
        CRITICAL_THRESHOLD = 0.3

        if anchorage_score < CRITICAL_THRESHOLD:
            if profile.gravity_factor < 0.05:
                failure_mode = FailureMode.ROOT_DISORIENTATION
            else:
                failure_mode = FailureMode.ANCHORAGE_FAILURE
        elif morphology_stability < CRITICAL_THRESHOLD:
            if photoperiod_stress > 0.5:
                failure_mode = FailureMode.PHOTOPERIOD_COLLAPSE
            else:
                failure_mode = FailureMode.MORPHOGENETIC_INSTABILITY
        elif yield_index < CRITICAL_THRESHOLD:
            failure_mode = FailureMode.TRANSLOCATION_IMPAIRMENT
        else:
            # If all metrics are above threshold, we return UNKNOWN (as in "No specific failure detected")
            failure_mode = FailureMode.UNKNOWN

        return {
            "anchorage_score": anchorage_score,
            "morphology_stability": morphology_stability,
            "yield_index": yield_index,
            "failure_mode": failure_mode
        }

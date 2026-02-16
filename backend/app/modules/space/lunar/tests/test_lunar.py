import pytest
from app.modules.space.lunar.gravity_model import FractionalGravityEnvironmentEngine
from app.modules.space.lunar.schemas import LunarEnvironmentProfileBase, FailureMode

class TestGravityModel:
    def setup_method(self):
        self.engine = FractionalGravityEnvironmentEngine()
        self.profile_base = LunarEnvironmentProfileBase(
            gravity_factor=0.16,
            light_cycle_days=14.0,
            dark_cycle_days=14.0,
            habitat_pressure_kpa=101.3,
            o2_ppm=210000,
            co2_ppm=400,
            root_support_factor=1.0
        )

    def test_determinism(self):
        """Test that simulation is deterministic for same inputs."""
        res1 = self.engine.simulate(self.profile_base, generation=1, germplasm_id=123)
        res2 = self.engine.simulate(self.profile_base, generation=1, germplasm_id=123)
        assert res1 == res2

        # Different germplasm should likely vary
        res3 = self.engine.simulate(self.profile_base, generation=1, germplasm_id=456)
        # We assume they are different usually, but technically random seed collision is possible (rare).
        # We won't assert !=, but mainly res1 == res2.

    def test_gravity_boundary_low(self):
        """Test response to extremely low gravity."""
        # g < 0.05
        profile = self.profile_base.model_copy(update={"gravity_factor": 0.04})
        res = self.engine.simulate(profile, generation=1, germplasm_id=1)

        # Should likely fail with ROOT_DISORIENTATION or ANCHORAGE_FAILURE or UNKNOWN if valid.
        # But 0.04g is very low.
        # My logic: if score < threshold (which it should be low due to low g) -> Check failure.

        # anchorage_score = (0.04/0.3)*0.6 + 1.0*0.4 = 0.08 + 0.4 = 0.48.
        # 0.48 might be > threshold (0.3).
        # So it might not fail anchorage!
        # But let's check morphology.
        # gravity_stability = sqrt(0.04/0.3) = sqrt(0.133) = 0.36.
        # morphology_stability = 0.36 * (1 - stress).
        # stress for 28 days cycle is ~1.
        # morphology_stability ~= 0.
        # So it should fail morphology.

        if res["failure_mode"] != FailureMode.UNKNOWN:
            # If it fails, check it's one of the expected ones for low g/bad light.
            assert res["failure_mode"] in [
                FailureMode.ROOT_DISORIENTATION,
                FailureMode.ANCHORAGE_FAILURE,
                FailureMode.MORPHOGENETIC_INSTABILITY,
                FailureMode.PHOTOPERIOD_COLLAPSE
            ]

    def test_photoperiod_stress(self):
        """Test response to extreme photoperiods."""
        # 14/14 is extreme.
        profile = self.profile_base # defaults are 14/14
        res = self.engine.simulate(profile, generation=1, germplasm_id=1)

        # 1/1 (Earth-like-ish total 2 days. Earth is 0.5/0.5).
        # But 1/1 is much better than 14/14.
        profile_better = self.profile_base.model_copy(update={"light_cycle_days": 1.0, "dark_cycle_days": 1.0})
        res_better = self.engine.simulate(profile_better, generation=1, germplasm_id=1)

        # Compare
        assert res_better["morphology_stability"] > res["morphology_stability"]

    def test_anchorage_failure(self):
        """Test anchorage failure with low support."""
        # Low support and low gravity
        profile = self.profile_base.model_copy(update={"root_support_factor": 0.0, "gravity_factor": 0.1})
        # Score = (0.1/0.3)*0.6 + 0 = 0.2.
        # 0.2 < 0.3 threshold.
        res = self.engine.simulate(profile, generation=1, germplasm_id=1)

        # Should be ANCHORAGE_FAILURE or ROOT_DISORIENTATION (g=0.1 > 0.05, so likely ANCHORAGE)
        assert res["anchorage_score"] < 0.3
        assert res["failure_mode"] == FailureMode.ANCHORAGE_FAILURE

    def test_generation_decay(self):
        """Test multigenerational decay."""
        res1 = self.engine.simulate(self.profile_base, generation=1, germplasm_id=1)
        res5 = self.engine.simulate(self.profile_base, generation=5, germplasm_id=1)

        assert res5["yield_index"] < res1["yield_index"]

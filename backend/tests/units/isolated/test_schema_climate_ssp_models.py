import unittest
from pydantic import ValidationError

from app.schemas.schema_climate_ssp_models import (
    ClimateRiskAssessment,
    ClimateVariable,
    SSPDataPoint,
    SSPModelMetadata,
    SSPProjection,
    SSPScenario,
    TemporalResolution,
)


class TestClimateSSPModels(unittest.TestCase):

    def test_ssp_data_point_validation(self):
        """Test validation of SSPDataPoint."""
        # Valid data point
        dp = SSPDataPoint(year=2030, value=1.5, unit="K")
        self.assertEqual(dp.year, 2030)
        self.assertEqual(dp.value, 1.5)

        # Valid range
        dp = SSPDataPoint(year=2030, value=1.5, unit="K", uncertainty_range=(1.0, 2.0))
        self.assertEqual(dp.uncertainty_range, (1.0, 2.0))

        # Invalid year
        with self.assertRaises(ValidationError):
            SSPDataPoint(year=1800, value=1.5, unit="K")

        # Invalid range (min > max)
        with self.assertRaises(ValidationError):
            SSPDataPoint(year=2030, value=1.5, unit="K", uncertainty_range=(2.0, 1.0))

    def test_ssp_projection_model(self):
        """Test SSPProjection model structure."""
        metadata = SSPModelMetadata(model_name="TestModel", institution="TestInst")

        data_points = [
            SSPDataPoint(year=2020, value=290.0, unit="K"),
            SSPDataPoint(year=2030, value=291.0, unit="K"),
        ]

        proj = SSPProjection(
            scenario=SSPScenario.SSP1_19,
            variable=ClimateVariable.TAS,
            model_metadata=metadata,
            temporal_resolution=TemporalResolution.ANNUAL,
            data=data_points
        )

        self.assertEqual(proj.scenario, "SSP1-1.9")
        self.assertEqual(proj.variable, "tas")
        self.assertEqual(proj.min_year, 2020)
        self.assertEqual(proj.max_year, 2030)
        self.assertEqual(len(proj.data), 2)

    def test_climate_risk_assessment(self):
        """Test ClimateRiskAssessment."""
        assessment = ClimateRiskAssessment(
            scenario=SSPScenario.SSP5_85,
            risk_level=5,
            description="High risk of extreme heat",
            impact_sectors=["Agriculture", "Health"]
        )

        self.assertEqual(assessment.risk_level, 5)
        self.assertIn("Agriculture", assessment.impact_sectors)

        # Invalid risk level
        with self.assertRaises(ValidationError):
            ClimateRiskAssessment(
                scenario=SSPScenario.SSP5_85,
                risk_level=6,  # Must be <= 5
                description="Extreme"
            )

if __name__ == "__main__":
    unittest.main()

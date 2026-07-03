import sys
from unittest.mock import MagicMock

# Try to import dependencies. If they fail (e.g. no sqlalchemy), mock them.
try:
    import app.services.phenology
except ImportError:
    mock_phenology = MagicMock()
    mock_phenology.GROWTH_STAGES = [
        {"code": 0, "name": "Germination"},
        {"code": 10, "name": "Seedling"},
        {"code": 20, "name": "Tillering"},
        {"code": 30, "name": "Stem Elongation"},
        {"code": 40, "name": "Booting"},
        {"code": 50, "name": "Heading"},
        {"code": 60, "name": "Flowering"},
        {"code": 70, "name": "Grain Fill"},
        {"code": 80, "name": "Ripening"},
        {"code": 90, "name": "Maturity"},
    ]
    sys.modules["app.services.phenology"] = mock_phenology

import pytest
from datetime import datetime, UTC
from app.modules.ai.services.reevu.expansions.growth_stage_transition_model import (
    GrowthStageTransitionModel,
    TransitionContext,
    TimeEvidence,
    VisionEvidence
)

class TestGrowthStageTransitionModel:

    @pytest.fixture
    def model(self):
        return GrowthStageTransitionModel()

    def test_initialization(self, model):
        assert model.crop_params is not None
        assert "default" in model.crop_params

    def test_gaussian_probability(self, model):
        # Mean 10, Std 2. At x=10, should be peak.
        peak = model._gaussian_probability(10, 10, 2)
        # At x=12 (1 std away), should be lower
        one_std = model._gaussian_probability(12, 10, 2)
        assert peak > one_std
        assert peak > 0

    def test_predict_stage_time_only(self, model):
        # 45 days after sowing -> expect stage 30 (Stem Elongation) based on default params
        context = TransitionContext(
            crop_type="default",
            current_stage_code=20,
            time_evidence=TimeEvidence(
                days_after_sowing=45,
                accumulated_gdd=450,
                sowing_date=datetime.now(UTC)
            )
        )

        prediction = model.predict_stage(context)

        assert prediction.predicted_stage_code == 30
        assert prediction.predicted_stage_name == "Stem Elongation"
        assert prediction.confidence > 0.0

    def test_predict_stage_with_vision_support(self, model):
        # 45 days (Stage 30) AND Vision says Stage 30 with 0.9 confidence
        vision = VisionEvidence(
            predicted_stage_code=30,
            confidence=0.9,
            probabilities={30: 0.9, 20: 0.05, 40: 0.05},
            timestamp=datetime.now(UTC)
        )

        context = TransitionContext(
            crop_type="default",
            current_stage_code=20,
            vision_evidence=vision,
            time_evidence=TimeEvidence(
                days_after_sowing=45,
                accumulated_gdd=450,
                sowing_date=datetime.now(UTC)
            )
        )

        prediction = model.predict_stage(context)

        assert prediction.predicted_stage_code == 30
        assert prediction.evidence_breakdown["vision_support"] >= 0.9
        # Combined confidence should be high
        assert prediction.confidence > 0.8

    def test_predict_stage_conflict(self, model):
        # Time says Stage 30 (45 days), Vision says Stage 50 (Heading) with high confidence
        # The model should weigh them. Since standard dev is small (5 days), time prior will be very low for stage 50 (expected 70 days).
        # Vision likelihood is high for 50.
        # Posterior should reflect the conflict.

        vision = VisionEvidence(
            predicted_stage_code=50,
            confidence=0.95,
            probabilities={50: 0.95, 30: 0.01},
            timestamp=datetime.now(UTC)
        )

        context = TransitionContext(
            crop_type="default",
            current_stage_code=30,
            vision_evidence=vision,
            time_evidence=TimeEvidence(
                days_after_sowing=45, # Expected for stage 30
                accumulated_gdd=450,
                sowing_date=datetime.now(UTC)
            )
        )

        prediction = model.predict_stage(context)

        # If time prior for stage 50 is ~0 (45 days vs 70 days with std 3), posterior for 50 will be crushed.
        # So likely it will predict 30 (because time prior is high) or maybe 0 if both are low (but normalized).

        # Let's check logic:
        # P(Time|30) is high. P(Vision|30) is 0.01. Product is moderate.
        # P(Time|50) is ~0. P(Vision|50) is 0.95. Product is ~0.
        # So 30 should win despite vision.

        assert prediction.predicted_stage_code == 30

    def test_transition_probability(self, model):
        # Current stage 20. Prediction is 30. Transition prob should be high.
        context = TransitionContext(
            crop_type="default",
            current_stage_code=20,
            time_evidence=TimeEvidence(
                days_after_sowing=45, # Strongly supports 30
                accumulated_gdd=450,
                sowing_date=datetime.now(UTC)
            )
        )

        prediction = model.predict_stage(context)

        assert prediction.predicted_stage_code == 30
        assert prediction.transition_probability > 0.8

import math
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.modules.phenotyping.services.phenology_service import GROWTH_STAGES

class VisionEvidence(BaseModel):
    """Evidence from computer vision analysis."""
    predicted_stage_code: int
    confidence: float
    probabilities: dict[int, float] = Field(default_factory=dict)
    timestamp: datetime

class TimeEvidence(BaseModel):
    """Evidence from time and environmental factors."""
    days_after_sowing: int
    accumulated_gdd: float
    sowing_date: datetime

class TransitionContext(BaseModel):
    """Context for analyzing growth stage transition."""
    crop_type: str = "default"
    vision_evidence: VisionEvidence | None = None
    time_evidence: TimeEvidence
    current_stage_code: int

class GrowthStagePrediction(BaseModel):
    """Result of growth stage prediction."""
    predicted_stage_code: int
    predicted_stage_name: str
    confidence: float
    transition_probability: float  # Probability of transitioning FROM current stage
    next_stage_prediction: dict[str, Any] | None = None
    evidence_breakdown: dict[str, float]

class CropGrowthParameters(BaseModel):
    """Growth parameters for a specific crop."""
    base_temp: float
    stages: dict[int, dict[str, float]] # stage_code -> {expected_das, expected_gdd, std_dev_days}

# Default parameters for scaffolding (e.g. Rice/Wheat generic)
DEFAULT_CROP_PARAMS = CropGrowthParameters(
    base_temp=10.0,
    stages={
        0:  {"expected_das": 0,   "expected_gdd": 0,    "std_dev_days": 2},   # Germination
        10: {"expected_das": 10,  "expected_gdd": 100,  "std_dev_days": 3},   # Seedling
        20: {"expected_das": 25,  "expected_gdd": 250,  "std_dev_days": 4},   # Tillering
        30: {"expected_das": 45,  "expected_gdd": 450,  "std_dev_days": 5},   # Stem Elongation
        40: {"expected_das": 60,  "expected_gdd": 600,  "std_dev_days": 4},   # Booting
        50: {"expected_das": 70,  "expected_gdd": 700,  "std_dev_days": 3},   # Heading
        60: {"expected_das": 75,  "expected_gdd": 750,  "std_dev_days": 3},   # Flowering
        70: {"expected_das": 90,  "expected_gdd": 900,  "std_dev_days": 5},   # Grain Fill
        80: {"expected_das": 110, "expected_gdd": 1100, "std_dev_days": 5},   # Ripening
        90: {"expected_das": 120, "expected_gdd": 1200, "std_dev_days": 5},   # Maturity
    }
)

class GrowthStageTransitionModel:
    """
    Hybrid model for growth stage prediction combining:
    1. Computer Vision Evidence (CNN/ViT probabilities)
    2. Temporal Evidence (Days After Sowing, GDD)
    Using a Bayesian update approach.
    """

    def __init__(self):
        self.crop_params = {"default": DEFAULT_CROP_PARAMS}

    def _get_stage_name(self, code: int) -> str:
        for stage in GROWTH_STAGES:
            if stage["code"] == code:
                return stage["name"]
        return "Unknown"

    def _gaussian_probability(self, x: float, mean: float, std: float) -> float:
        """Calculate probability density of x given Gaussian(mean, std)."""
        if std <= 0: return 0.0
        exponent = -((x - mean) ** 2) / (2 * (std ** 2))
        return (1 / (math.sqrt(2 * math.pi) * std)) * math.exp(exponent)

    def _calculate_time_prior(self, stage_code: int, das: int, params: CropGrowthParameters) -> float:
        """Calculate prior probability of being in a stage given DAS."""
        stage_params = params.stages.get(stage_code)
        if not stage_params:
            return 0.0

        # We model the stage duration as a Gaussian around expected DAS
        # But this is "probability of observing this stage at this time"
        return self._gaussian_probability(das, stage_params["expected_das"], stage_params["std_dev_days"])

    def predict_stage(self, context: TransitionContext) -> GrowthStagePrediction:
        """
        Predict the most likely growth stage.
        Posterior ~ Vision_Likelihood * Time_Prior
        """
        params = self.crop_params.get(context.crop_type, self.crop_params["default"])

        # 1. Calculate Time Priors for all known stages
        time_priors = {}
        possible_stages = [s["code"] for s in GROWTH_STAGES]

        total_time_prob = 0.0
        for stage in possible_stages:
            prob = self._calculate_time_prior(stage, context.time_evidence.days_after_sowing, params)
            time_priors[stage] = prob
            total_time_prob += prob

        # Normalize time priors
        if total_time_prob > 0:
            for s in time_priors:
                time_priors[s] /= total_time_prob
        else:
            # Fallback if far outside range (uniform or closest)
            # For now, uniform
            for s in possible_stages:
                time_priors[s] = 1.0 / len(possible_stages)

        # 2. Incorporate Vision Evidence (Likelihood)
        vision_likelihoods = {s: 1.0 for s in possible_stages} # Default neutral if no vision

        if context.vision_evidence:
            # If we have specific probabilities, use them
            if context.vision_evidence.probabilities:
                # Map vision classes to stage codes (assuming vision model output aligns)
                # If vision model gives 0.0, we use a small epsilon
                epsilon = 0.01
                for s in possible_stages:
                    # Vision model might not return all keys
                    likelihood = context.vision_evidence.probabilities.get(s, 0.0)
                    vision_likelihoods[s] = max(likelihood, epsilon)
            else:
                # Simple case: trust the predicted class with confidence
                # Distribute (1-confidence) among others
                pred = context.vision_evidence.predicted_stage_code
                conf = context.vision_evidence.confidence
                other_prob = (1.0 - conf) / (len(possible_stages) - 1) if len(possible_stages) > 1 else 0
                for s in possible_stages:
                    vision_likelihoods[s] = conf if s == pred else other_prob

        # 3. Calculate Posterior
        posteriors = {}
        total_posterior = 0.0

        # Weight factors can be tuned. Currently 1:1
        for s in possible_stages:
            # Posterior = Prior (Time) * Likelihood (Vision)
            p = time_priors[s] * vision_likelihoods[s]
            posteriors[s] = p
            total_posterior += p

        # Normalize
        if total_posterior > 0:
            for s in posteriors:
                posteriors[s] /= total_posterior
        else:
             # Should not happen ideally
             pass

        # 4. Determine Winner
        best_stage = max(posteriors, key=posteriors.get)
        confidence = posteriors[best_stage]

        # 5. Analyze Transition
        # If best_stage > current_stage, we are transitioning or have transitioned
        # Transition probability is roughly the probability that we are NOT in current_stage AND we are in a later stage
        prob_advanced = sum(p for s, p in posteriors.items() if s > context.current_stage_code)

        return GrowthStagePrediction(
            predicted_stage_code=best_stage,
            predicted_stage_name=self._get_stage_name(best_stage),
            confidence=confidence,
            transition_probability=prob_advanced,
            evidence_breakdown={
                "time_support": time_priors.get(best_stage, 0.0),
                "vision_support": vision_likelihoods.get(best_stage, 0.0)
            }
        )

growth_stage_model = GrowthStageTransitionModel()

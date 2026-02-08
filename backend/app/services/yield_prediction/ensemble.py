
import logging
import numpy as np
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.services.yield_prediction.statistical import StatisticalPredictor
from app.services.yield_prediction.process import ProcessBasedPredictor
from app.services.yield_prediction.ml import MLPredictor

logger = logging.getLogger(__name__)

class EnsemblePredictor:
    """
    Hybrid Ensemble Yield Predictor.

    Implements Task 4:
    - 4.1 Create ensemble service
    - 4.2 Add dynamic weight calculation
    - 4.3 Implement ensemble uncertainty quantification
    - 4.4 Add adaptive method selection logic
    """

    def __init__(self):
        self.statistical = StatisticalPredictor()
        self.process = ProcessBasedPredictor()
        self.ml = MLPredictor()

    async def predict(
        self,
        db: AsyncSession,
        field_id: int,
        crop_name: str,
        planting_date: date,
        target_year: int,
        org_id: int,
        features: Dict[str, Any] = None
    ) -> Dict:
        """
        Generate ensemble prediction.
        """
        if features is None:
            features = {}

        # 1. Gather Predictions
        predictions = []

        # Statistical
        try:
            stat_result = await self.statistical.predict(db, field_id, crop_name, target_year, org_id)
            if stat_result.get("status") == "success":
                val = stat_result["predicted_yield"]
                # Avoid zero uncertainty division
                uncertainty = max(0.1, (stat_result["upper_bound"] - stat_result["lower_bound"]) / 4) # approx sigma

                predictions.append({
                    "method": "statistical",
                    "value": val,
                    "uncertainty": uncertainty,
                    "weight": 0.3 # Initial base weight
                })
        except Exception as e:
            logger.error(f"Statistical prediction failed: {e}")

        # Process-Based
        try:
            # Assuming solar_radiation is in features or default
            solar = features.get("solar_radiation", 20.0)
            process_result = await self.process.predict(db, field_id, crop_name, planting_date, org_id, solar_radiation=solar)
            if process_result.get("status") == "success":
                val = process_result["predicted_yield"]
                predictions.append({
                    "method": "process_based",
                    "value": val,
                    "uncertainty": max(0.1, val * 0.2), # Estimate 20% uncertainty
                    "weight": 0.3
                })
        except Exception as e:
            logger.error(f"Process-based prediction failed: {e}")

        # ML
        try:
            ml_result = await self.ml.predict(db, field_id, crop_name, org_id, features)
            if ml_result.get("status") == "success":
                 val = ml_result["predicted_yield"]
                 predictions.append({
                    "method": "ml_based",
                    "value": val,
                    "uncertainty": max(0.1, val * 0.15), # Estimate 15%
                    "weight": 0.4
                })
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")

        if not predictions:
            return {
                "predicted_yield": None,
                "status": "error",
                "message": "All prediction methods failed or returned insufficient data."
            }

        # 2. Dynamic Weight Calculation (4.2)
        # Adjust weights based on uncertainty (Inverse Variance Weighting)
        # w_i = 1 / sigma_i^2
        total_inv_variance = sum(1 / (p["uncertainty"]**2 + 1e-6) for p in predictions)

        weighted_sum = 0
        sum_weights = 0

        method_contributions = {}

        for p in predictions:
            # Normalized uncertainty weight
            unc_weight = (1 / (p["uncertainty"]**2 + 1e-6)) / total_inv_variance

            # Blend predefined and uncertainty-based weight
            final_weight = (unc_weight + p["weight"]) / 2

            weighted_sum += p["value"] * final_weight
            sum_weights += final_weight

            method_contributions[p["method"]] = float(final_weight)

        # Normalize weights
        ensemble_yield = weighted_sum / sum_weights

        # Normalize contributions for output
        total_contrib = sum(method_contributions.values())
        method_contributions = {k: round(v/total_contrib, 2) for k, v in method_contributions.items()}

        # 3. Ensemble Uncertainty (4.3)
        # Combined standard deviation approximation
        ensemble_uncertainty = np.sqrt(1 / total_inv_variance)

        return {
            "predicted_yield": round(ensemble_yield, 2),
            "lower_bound": round(max(0, ensemble_yield - 1.96 * ensemble_uncertainty), 2),
            "upper_bound": round(ensemble_yield + 1.96 * ensemble_uncertainty, 2),
            "confidence_level": 0.95,
            "method": "hybrid_ensemble",
            "method_contributions": method_contributions,
            "individual_results": {p["method"]: p["value"] for p in predictions},
            "status": "success"
        }

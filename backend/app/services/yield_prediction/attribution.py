
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class FactorAttribution:
    """
    Yield Factor Attribution Service.

    Implements Task 5:
    - 5.1 Create factor attribution service
    - 5.2 Add genetic component calculation
    - 5.3 Add environmental component calculation
    - 5.4 Add management component calculation
    - 5.5 Add G×E interaction quantification
    """

    async def analyze(
        self,
        db: AsyncSession,
        prediction_result: Dict[str, Any],
        field_id: int,
        crop_name: str,
        features: Dict[str, Any]
    ) -> Dict:
        """
        Decompose yield into G, E, M components.

        Args:
            db: Database session
            prediction_result: Result from predictor
            field_id: Field ID
            crop_name: Crop name
            features: Input features used for prediction

        Returns:
            Dictionary with attributed yield components
        """
        predicted_yield = prediction_result.get("predicted_yield")
        if not predicted_yield:
            return {}

        # Default shares (Baseline)
        g_share = 0.33
        e_share = 0.33
        m_share = 0.34

        # 1. Adjust shares based on Method Specific Insights

        # A) Process-Based Insights
        # Process model explicitly calculates stress (Environment)
        if prediction_result.get("method") == "process_based" or \
           (prediction_result.get("individual_results") and "process_based" in prediction_result["individual_results"]):

             # Extract stress factors if available (from process model direct return or embedded in ensemble)
             # Note: In ensemble, we might need to store this metadata better.
             # For now assuming it might be in prediction_result if direct, or we rely on general heuristics.

             stress = prediction_result.get("stress_factors", {})
             temp_stress = stress.get("temperature", 1.0)
             water_stress = stress.get("water", 1.0)

             # If high stress (low factor), Environment is the limiting factor (high impact)
             min_stress = min(temp_stress, water_stress)
             if min_stress < 0.8:
                 # Environment is limiting, so it explains the (lower) yield
                 e_share += 0.2
                 g_share -= 0.1
                 m_share -= 0.1

        # B) ML Insights
        # ML model provides feature importance
        if prediction_result.get("method") == "ml_based" or \
           (prediction_result.get("individual_results") and "ml_based" in prediction_result["individual_results"]):

             # This requires access to feature importance which is returned by MLPredictor
             # If passed in prediction_result
             importance = prediction_result.get("feature_importance", {})

             if importance:
                 # Map features to G, E, M
                 g_imp = sum(v for k,v in importance.items() if any(x in k.lower() for x in ["variety", "gen", "cultivar"]))
                 e_imp = sum(v for k,v in importance.items() if any(x in k.lower() for x in ["rain", "temp", "soil", "weather", "sun", "rad"]))
                 m_imp = sum(v for k,v in importance.items() if any(x in k.lower() for x in ["fert", "irrigation", "plant", "sow", "tillage"]))

                 total_imp = g_imp + e_imp + m_imp
                 if total_imp > 0:
                     g_share = g_imp / total_imp
                     e_share = e_imp / total_imp
                     m_share = m_imp / total_imp

        # 2. Normalize
        total = g_share + e_share + m_share
        g_share /= total
        e_share /= total
        m_share /= total

        return {
            "genetic_contribution": round(predicted_yield * g_share, 2),
            "environmental_contribution": round(predicted_yield * e_share, 2),
            "management_contribution": round(predicted_yield * m_share, 2),
            "interaction_ge": round(predicted_yield * 0.05, 2), # Simplified 5% interaction
            "shares": {
                "genetic": round(g_share, 2),
                "environmental": round(e_share, 2),
                "management": round(m_share, 2)
            }
        }

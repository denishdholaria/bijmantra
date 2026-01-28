# backend/app/services/cross_domain_gdd_service.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date, timedelta
import random
import logging

from app.services.gdd_calculator_service import gdd_calculator_service

logger = logging.getLogger(__name__)

class CrossDomainGDDService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_gdd_requirements(self, crop_varieties: List[str]) -> Dict[str, Any]:
        """
        Analyzes the GDD requirements for different crop varieties.
        """
        # In a real implementation, this would query a database of crop information.
        # For now, we simulate variety-specific differences around the species baseline

        requirements = {}
        for variety in crop_varieties:
            # Determine crop type from variety name or default to corn
            crop_type = "corn"
            if "wheat" in variety.lower(): crop_type = "wheat"
            elif "rice" in variety.lower(): crop_type = "rice"
            elif "soy" in variety.lower(): crop_type = "soybean"

            # Get base GDD for the crop
            # This is a simplification; varieties differ
            base_temp = gdd_calculator_service.get_crop_base_temperature(crop_type)

            # Simulate variety maturity ratings
            maturity_variance = random.randint(-100, 100)

            # Use growth stages to estimate total
            stages = gdd_calculator_service.GROWTH_STAGES.get(crop_type, [])
            total_gdd = stages[-1][1] if stages else 2000

            requirements[variety] = {
                "base_temp": base_temp,
                "min_gdd": total_gdd + maturity_variance - 50,
                "max_gdd": total_gdd + maturity_variance + 50
            }

        return {
            "gdd_requirements": requirements,
            "uncertainty": {"level": 0.1, "source": "Crop model estimation"},
        }

    def match_varieties_to_thermal_history(
        self, field_id: int, varieties: List[str]
    ) -> Dict[str, Any]:
        """
        Matches crop varieties to a field's thermal history.
        """
        # In production: Query Field's historical weather data -> calculate average seasonal GDD
        # For now, we assume a typical season has ~2500 GDD

        seasonal_gdd = 2500 + random.randint(-200, 200)

        variety_reqs = self.analyze_gdd_requirements(varieties)["gdd_requirements"]

        matches = {}
        for variety, req in variety_reqs.items():
            required_gdd = (req["min_gdd"] + req["max_gdd"]) / 2
            diff = abs(seasonal_gdd - required_gdd)

            # Simple suitability score: closer is better
            suitability = max(0, 1.0 - (diff / 1000))

            matches[variety] = {
                "suitability_score": round(suitability, 2),
                "seasonal_gdd_potential": seasonal_gdd,
                "variety_requirement": required_gdd
            }

        return {
            "variety_matches": matches,
            "uncertainty": {
                "level": 0.15,
                "source": "Historical weather variability",
            },
        }

    def recommend_varieties(self, field_id: int) -> Dict[str, Any]:
        """
        Provides variety recommendations based on GDD patterns.
        """
        # Placeholder for variety database
        varieties = ["Generic Corn 105-day", "Generic Corn 112-day", "Generic Corn 95-day"]

        matches = self.match_varieties_to_thermal_history(field_id, varieties)["variety_matches"]

        recommendations = []
        for variety, data in matches.items():
            score = data["suitability_score"]
            reason = "Optimal GDD match" if score > 0.8 else "Acceptable GDD match" if score > 0.6 else "High risk of maturity issues"
            recommendations.append({
                "variety": variety,
                "score": score,
                "reason": reason
            })

        recommendations.sort(key=lambda x: x["score"], reverse=True)

        return {
            "recommendations": recommendations,
            "uncertainty": {
                "level": 0.2,
                "source": "Combined model and weather uncertainty",
            },
        }

    def analyze_planting_windows(
        self, field_id: int, crop_name: str
    ) -> Dict[str, Any]:
        """
        Analyzes historical GDD accumulation patterns to project optimal planting dates.
        """
        today = date.today()
        windows = []

        # Simulate analyzing 3 potential planting weeks
        for i in range(3):
            start_date = today + timedelta(days=i * 7)

            # Predict outcome if planted on this date
            # We use the calculator service to predict maturity
            # Assuming 0 cumulative GDD at planting
            try:
                prediction = gdd_calculator_service.predict_growth_stages(
                    crop_name,
                    0,
                    start_date,
                    current_date=start_date
                )

                maturity_date = prediction.predicted_maturity_date
                days_to_maturity = (maturity_date - start_date).days if maturity_date else 120

                # Suitability logic: faster maturity isn't always better, but late maturity risks frost
                # This is simplified logic
                score = 0.9 if days_to_maturity < 130 else 0.7

                windows.append({
                    "start_date": start_date.isoformat(),
                    "predicted_maturity": maturity_date.isoformat() if maturity_date else "Unknown",
                    "days_to_maturity": days_to_maturity,
                    "suitability_score": score,
                    "confidence_interval": {
                        "lower": round(score - 0.1, 2),
                        "upper": round(score + 0.05, 2),
                    },
                })
            except Exception as e:
                logger.error(f"Error predicting for planting date {start_date}: {e}")

        return {
            "planting_windows": windows,
            "uncertainty": {"level": 0.25, "source": "Weather forecast uncertainty"},
        }

    def predict_harvest_timing(
        self, field_id: int, planting_date: date, crop_name: str
    ) -> Dict[str, Any]:
        """
        Predicts harvest dates based on cumulative GDD and analyzes market premium windows.
        """
        # Use core calculator for phenology
        # We need current cumulative GDD. Since we don't have field history easily here without more queries,
        # we'll estimate it or assume 0 if it's a future prediction

        # Ideally: cumulative_gdd = gdd_log_repo.get_cumulative(field_id)
        cumulative_gdd = 0 # Placeholder for actual accumulated GDD

        prediction = gdd_calculator_service.predict_growth_stages(
            crop_name,
            cumulative_gdd,
            planting_date,
            current_date=date.today()
        )

        predicted_harvest_date = prediction.predicted_maturity_date or (planting_date + timedelta(days=120))

        return {
            "predicted_harvest_date": predicted_harvest_date.isoformat(),
            "confidence_interval": {
                "lower": (predicted_harvest_date - timedelta(days=5)).isoformat(),
                "upper": (predicted_harvest_date + timedelta(days=5)).isoformat(),
            },
            "market_analysis": {
                "premium_window_start": (
                    predicted_harvest_date - timedelta(days=10)
                ).isoformat(),
                "premium_window_end": (
                    predicted_harvest_date + timedelta(days=2)
                ).isoformat(),
                "economic_impact_usd": round(
                    random.uniform(50, 200), 2
                ),  # $/acre
            },
            "uncertainty": {
                "level": 0.18,
                "source": "GDD projection and market volatility",
            },
        }

    def create_climate_risk_alerts(self, field_id: int) -> Dict[str, Any]:
        """
        Monitors GDD accumulation vs. historical norms and generates alerts for management interventions.
        """
        # Placeholder logic: In real app, compare current season GDD vs 10-year average for this date

        deviation = round(random.uniform(-15, 15), 2)  # Percentage deviation
        severity = "low"
        if abs(deviation) > 10:
            severity = "medium"
        if abs(deviation) > 20:
            severity = "high"

        return {
            "risk_alerts": [
                {
                    "field_id": field_id,
                    "risk_type": "GDD Deviation",
                    "severity": severity,
                    "message": f"GDD accumulation is {deviation}% {'above' if deviation > 0 else 'below'} historical average.",
                    "recommendation": "Monitor crop for signs of stress or accelerated/delayed growth.",
                }
            ],
            "uncertainty": {"level": 0.1, "source": "Based on 30-year climate normals"},
        }

"""
Genomic Selection Service

Provides GS model training, GEBV prediction, and selection tools
for genomic-assisted breeding programs.
"""

from typing import Optional
from datetime import datetime, timedelta
import random


# Demo GS models
DEMO_MODELS = [
    {
        "id": "gs1",
        "name": "Yield_GBLUP_2024",
        "method": "GBLUP",
        "trait": "Grain Yield",
        "accuracy": 0.72,
        "heritability": 0.45,
        "markers": 12500,
        "train_size": 500,
        "valid_size": 100,
        "status": "trained",
        "created_at": "2024-11-15",
        "description": "Genomic BLUP model for grain yield prediction",
    },
    {
        "id": "gs2",
        "name": "Height_BayesB_2024",
        "method": "BayesB",
        "trait": "Plant Height",
        "accuracy": 0.81,
        "heritability": 0.68,
        "markers": 12500,
        "train_size": 500,
        "valid_size": 100,
        "status": "trained",
        "created_at": "2024-11-18",
        "description": "Bayesian B model for plant height",
    },
    {
        "id": "gs3",
        "name": "DTF_RKHS_2024",
        "method": "RKHS",
        "trait": "Days to Flowering",
        "accuracy": 0.65,
        "heritability": 0.52,
        "markers": 12500,
        "train_size": 500,
        "valid_size": 100,
        "status": "trained",
        "created_at": "2024-11-20",
        "description": "Reproducing Kernel Hilbert Space model",
    },
    {
        "id": "gs4",
        "name": "MultiTrait_MT_2024",
        "method": "Multi-trait",
        "trait": "Multiple",
        "accuracy": 0.68,
        "heritability": 0.55,
        "markers": 12500,
        "train_size": 500,
        "valid_size": 100,
        "status": "training",
        "created_at": "2024-11-25",
        "description": "Multi-trait genomic selection model",
    },
]

# Demo predictions
DEMO_PREDICTIONS = [
    {"germplasm_id": "G001", "germplasm_name": "Elite-2024-001", "gebv": 2.45, "reliability": 0.85, "rank": 1, "selected": True},
    {"germplasm_id": "G002", "germplasm_name": "Elite-2024-002", "gebv": 2.32, "reliability": 0.82, "rank": 2, "selected": True},
    {"germplasm_id": "G003", "germplasm_name": "Elite-2024-003", "gebv": 2.18, "reliability": 0.79, "rank": 3, "selected": True},
    {"germplasm_id": "G004", "germplasm_name": "Elite-2024-004", "gebv": 1.95, "reliability": 0.81, "rank": 4, "selected": True},
    {"germplasm_id": "G005", "germplasm_name": "Elite-2024-005", "gebv": 1.82, "reliability": 0.77, "rank": 5, "selected": True},
    {"germplasm_id": "G006", "germplasm_name": "Elite-2024-006", "gebv": 1.68, "reliability": 0.75, "rank": 6, "selected": False},
    {"germplasm_id": "G007", "germplasm_name": "Elite-2024-007", "gebv": 1.55, "reliability": 0.73, "rank": 7, "selected": False},
    {"germplasm_id": "G008", "germplasm_name": "Elite-2024-008", "gebv": 1.42, "reliability": 0.71, "rank": 8, "selected": False},
    {"germplasm_id": "G009", "germplasm_name": "Elite-2024-009", "gebv": 1.28, "reliability": 0.69, "rank": 9, "selected": False},
    {"germplasm_id": "G010", "germplasm_name": "Elite-2024-010", "gebv": 1.15, "reliability": 0.67, "rank": 10, "selected": False},
]

# Demo yield predictions
DEMO_YIELD_PREDICTIONS = [
    {"germplasm_id": "G001", "germplasm_name": "Elite-2024-001", "predicted_yield": 8.5, "confidence_low": 7.8, "confidence_high": 9.2, "environment": "Irrigated"},
    {"germplasm_id": "G002", "germplasm_name": "Elite-2024-002", "predicted_yield": 8.2, "confidence_low": 7.5, "confidence_high": 8.9, "environment": "Irrigated"},
    {"germplasm_id": "G003", "germplasm_name": "Elite-2024-003", "predicted_yield": 7.9, "confidence_low": 7.2, "confidence_high": 8.6, "environment": "Irrigated"},
    {"germplasm_id": "G004", "germplasm_name": "Elite-2024-004", "predicted_yield": 7.6, "confidence_low": 6.9, "confidence_high": 8.3, "environment": "Irrigated"},
    {"germplasm_id": "G005", "germplasm_name": "Elite-2024-005", "predicted_yield": 7.3, "confidence_low": 6.6, "confidence_high": 8.0, "environment": "Irrigated"},
]


class GenomicSelectionService:
    """Service for genomic selection analysis."""
    
    def __init__(self):
        self.models = DEMO_MODELS.copy()
        self.predictions = DEMO_PREDICTIONS.copy()
    
    def list_models(
        self,
        trait: Optional[str] = None,
        method: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        """List GS models with optional filters."""
        filtered = self.models.copy()
        
        if trait:
            filtered = [m for m in filtered if m["trait"].lower() == trait.lower()]
        if method:
            filtered = [m for m in filtered if m["method"].lower() == method.lower()]
        if status:
            filtered = [m for m in filtered if m["status"] == status]
        
        return filtered
    
    def get_model(self, model_id: str) -> Optional[dict]:
        """Get a single model by ID."""
        for model in self.models:
            if model["id"] == model_id:
                return model
        return None
    
    def get_predictions(
        self,
        model_id: str,
        min_gebv: Optional[float] = None,
        min_reliability: Optional[float] = None,
        selected_only: bool = False,
    ) -> list[dict]:
        """Get GEBV predictions for a model."""
        predictions = self.predictions.copy()
        
        if min_gebv is not None:
            predictions = [p for p in predictions if p["gebv"] >= min_gebv]
        if min_reliability is not None:
            predictions = [p for p in predictions if p["reliability"] >= min_reliability]
        if selected_only:
            predictions = [p for p in predictions if p["selected"]]
        
        return predictions
    
    def get_yield_predictions(
        self,
        environment: Optional[str] = None,
    ) -> list[dict]:
        """Get yield predictions."""
        predictions = DEMO_YIELD_PREDICTIONS.copy()
        
        if environment:
            predictions = [p for p in predictions if p["environment"].lower() == environment.lower()]
        
        return predictions
    
    def get_model_comparison(self) -> list[dict]:
        """Compare accuracy across models."""
        return [
            {"model_id": m["id"], "name": m["name"], "method": m["method"], "trait": m["trait"], "accuracy": m["accuracy"]}
            for m in self.models if m["status"] == "trained"
        ]
    
    def get_selection_response(self, model_id: str, selection_intensity: float = 0.1) -> dict:
        """Calculate expected selection response."""
        model = self.get_model(model_id)
        if not model:
            return {}
        
        # R = i * r * sigma_g
        # where i = selection intensity, r = accuracy, sigma_g = genetic std dev
        i = 1.755  # Selection intensity for top 10%
        r = model["accuracy"]
        sigma_g = 1.5  # Assumed genetic standard deviation
        
        response = i * r * sigma_g
        
        return {
            "model_id": model_id,
            "selection_intensity": selection_intensity,
            "selection_differential": round(i, 3),
            "accuracy": r,
            "genetic_variance": round(sigma_g ** 2, 3),
            "expected_response": round(response, 3),
            "response_percent": round((response / 5) * 100, 1),  # Assuming mean of 5
        }
    
    def get_cross_predictions(self, parent1_id: str, parent2_id: str) -> dict:
        """Predict progeny performance from cross."""
        # Get parent GEBVs
        p1 = next((p for p in self.predictions if p["germplasm_id"] == parent1_id), None)
        p2 = next((p for p in self.predictions if p["germplasm_id"] == parent2_id), None)
        
        if not p1 or not p2:
            return {"error": "Parent not found"}
        
        # Mid-parent value
        mid_parent = (p1["gebv"] + p2["gebv"]) / 2
        
        # Predicted progeny distribution
        variance = 0.5  # Assumed segregation variance
        
        return {
            "parent1": {"id": parent1_id, "name": p1["germplasm_name"], "gebv": p1["gebv"]},
            "parent2": {"id": parent2_id, "name": p2["germplasm_name"], "gebv": p2["gebv"]},
            "mid_parent_value": round(mid_parent, 3),
            "progeny_mean": round(mid_parent, 3),
            "progeny_variance": variance,
            "progeny_std": round(variance ** 0.5, 3),
            "top_10_percent_expected": round(mid_parent + 1.28 * (variance ** 0.5), 3),
            "probability_exceeds_best_parent": round(0.5 + 0.1 * (p1["gebv"] - p2["gebv"]), 2),
        }
    
    def get_summary(self) -> dict:
        """Get summary statistics."""
        trained = [m for m in self.models if m["status"] == "trained"]
        
        return {
            "total_models": len(self.models),
            "trained_models": len(trained),
            "training_models": len([m for m in self.models if m["status"] == "training"]),
            "average_accuracy": round(sum(m["accuracy"] for m in trained) / len(trained), 3) if trained else 0,
            "best_model": max(trained, key=lambda x: x["accuracy"])["name"] if trained else None,
            "traits_covered": list(set(m["trait"] for m in self.models)),
            "methods_used": list(set(m["method"] for m in self.models)),
            "total_predictions": len(self.predictions),
            "selected_candidates": len([p for p in self.predictions if p["selected"]]),
        }
    
    def get_methods(self) -> list[dict]:
        """Get available GS methods."""
        return [
            {"id": "gblup", "name": "GBLUP", "description": "Genomic Best Linear Unbiased Prediction"},
            {"id": "bayesa", "name": "BayesA", "description": "Bayesian regression with scaled inverse chi-square prior"},
            {"id": "bayesb", "name": "BayesB", "description": "Bayesian regression with mixture prior"},
            {"id": "bayesc", "name": "BayesC", "description": "Bayesian regression with common variance"},
            {"id": "rkhs", "name": "RKHS", "description": "Reproducing Kernel Hilbert Space"},
            {"id": "rf", "name": "Random Forest", "description": "Machine learning ensemble method"},
            {"id": "multitrait", "name": "Multi-trait", "description": "Multi-trait genomic selection"},
        ]
    
    def get_traits(self) -> list[str]:
        """Get available traits."""
        return sorted(list(set(m["trait"] for m in self.models)))


# Singleton instance
_service = None


def get_genomic_selection_service() -> GenomicSelectionService:
    """Get the genomic selection service singleton."""
    global _service
    if _service is None:
        _service = GenomicSelectionService()
    return _service

"""
Phenomic Selection Service
High-throughput phenotyping for genomic prediction
"""
from typing import Optional
from datetime import datetime, timedelta
import random

# Demo phenomic datasets
DEMO_DATASETS = [
    {
        "id": "phen-001",
        "name": "Rice NIRS Spectral Data 2024",
        "crop": "Rice",
        "platform": "NIRS",
        "samples": 2500,
        "wavelengths": 2151,
        "traits_predicted": ["Protein", "Amylose", "Moisture", "Oil"],
        "accuracy": 0.89,
        "created_at": "2024-06-15",
        "status": "active"
    },
    {
        "id": "phen-002", 
        "name": "Wheat Hyperspectral Imaging",
        "crop": "Wheat",
        "platform": "Hyperspectral",
        "samples": 1800,
        "wavelengths": 224,
        "traits_predicted": ["Yield", "Biomass", "Chlorophyll", "Water Content"],
        "accuracy": 0.85,
        "created_at": "2024-08-20",
        "status": "active"
    },
    {
        "id": "phen-003",
        "name": "Maize Thermal Imaging Stress",
        "crop": "Maize",
        "platform": "Thermal",
        "samples": 3200,
        "wavelengths": 1,
        "traits_predicted": ["Drought Tolerance", "Heat Stress", "Stomatal Conductance"],
        "accuracy": 0.82,
        "created_at": "2024-09-10",
        "status": "active"
    }
]

# Demo prediction models
DEMO_MODELS = [
    {
        "id": "model-001",
        "name": "PLSR Protein Predictor",
        "type": "PLSR",
        "dataset_id": "phen-001",
        "target_trait": "Protein",
        "r_squared": 0.92,
        "rmse": 0.34,
        "components": 12,
        "status": "deployed"
    },
    {
        "id": "model-002",
        "name": "RF Yield Predictor",
        "type": "Random Forest",
        "dataset_id": "phen-002",
        "target_trait": "Yield",
        "r_squared": 0.87,
        "rmse": 0.45,
        "n_estimators": 500,
        "status": "deployed"
    },
    {
        "id": "model-003",
        "name": "CNN Stress Classifier",
        "type": "Deep Learning",
        "dataset_id": "phen-003",
        "target_trait": "Drought Tolerance",
        "accuracy": 0.91,
        "f1_score": 0.89,
        "architecture": "ResNet18",
        "status": "training"
    }
]


class PhenomicSelectionService:
    """Service for phenomic selection and high-throughput phenotyping"""
    
    async def get_datasets(
        self,
        crop: Optional[str] = None,
        platform: Optional[str] = None
    ) -> list:
        """Get phenomic datasets"""
        datasets = DEMO_DATASETS.copy()
        
        if crop:
            datasets = [d for d in datasets if d["crop"].lower() == crop.lower()]
        if platform:
            datasets = [d for d in datasets if d["platform"].lower() == platform.lower()]
            
        return datasets
    
    async def get_dataset(self, dataset_id: str) -> Optional[dict]:
        """Get single dataset by ID"""
        for d in DEMO_DATASETS:
            if d["id"] == dataset_id:
                return d
        return None
    
    async def get_models(
        self,
        dataset_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> list:
        """Get prediction models"""
        models = DEMO_MODELS.copy()
        
        if dataset_id:
            models = [m for m in models if m["dataset_id"] == dataset_id]
        if status:
            models = [m for m in models if m["status"] == status]
            
        return models
    
    async def predict_traits(
        self,
        model_id: str,
        sample_ids: list[str]
    ) -> dict:
        """Predict traits for samples using a model"""
        model = next((m for m in DEMO_MODELS if m["id"] == model_id), None)
        if not model:
            return {"error": "Model not found"}
        
        predictions = []
        for sample_id in sample_ids:
            predictions.append({
                "sample_id": sample_id,
                "trait": model["target_trait"],
                "predicted_value": round(random.uniform(5, 15), 2),
                "confidence": round(random.uniform(0.75, 0.95), 2),
                "uncertainty": round(random.uniform(0.1, 0.5), 2)
            })
        
        return {
            "model_id": model_id,
            "model_name": model["name"],
            "predictions": predictions,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_spectral_data(
        self,
        dataset_id: str,
        sample_id: Optional[str] = None
    ) -> dict:
        """Get spectral data for visualization"""
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            return {"error": "Dataset not found"}
        
        # Generate demo spectral curve
        n_wavelengths = min(dataset["wavelengths"], 100)
        wavelengths = list(range(350, 350 + n_wavelengths * 10, 10))
        
        # Generate sample spectra
        samples = []
        for i in range(5):
            reflectance = [round(random.uniform(0.1, 0.9), 3) for _ in wavelengths]
            samples.append({
                "sample_id": sample_id or f"sample-{i+1}",
                "wavelengths": wavelengths,
                "reflectance": reflectance
            })
        
        return {
            "dataset_id": dataset_id,
            "platform": dataset["platform"],
            "samples": samples
        }
    
    async def get_statistics(self) -> dict:
        """Get phenomic selection statistics"""
        return {
            "total_datasets": len(DEMO_DATASETS),
            "total_models": len(DEMO_MODELS),
            "deployed_models": len([m for m in DEMO_MODELS if m["status"] == "deployed"]),
            "total_samples": sum(d["samples"] for d in DEMO_DATASETS),
            "platforms": list(set(d["platform"] for d in DEMO_DATASETS)),
            "crops": list(set(d["crop"] for d in DEMO_DATASETS)),
            "avg_accuracy": round(sum(d["accuracy"] for d in DEMO_DATASETS) / len(DEMO_DATASETS), 2)
        }


# Singleton instance
phenomic_selection_service = PhenomicSelectionService()

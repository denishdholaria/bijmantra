"""
Vision Datasets Service - AI Plant Vision Training Ground
Phase 1: Foundation - Dataset management, image upload, metadata
"""

import uuid
import random
from datetime import datetime, UTC
from typing import Optional
from enum import Enum


class DatasetType(str, Enum):
    CLASSIFICATION = "classification"
    OBJECT_DETECTION = "object_detection"
    SEGMENTATION = "segmentation"


class DatasetStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    TRAINING = "training"
    ARCHIVED = "archived"


# In-memory storage (replace with database in production)
DATASETS: dict = {}
IMAGES: dict = {}
MODELS: dict = {}


def _init_demo_data():
    """Initialize demo datasets and models"""
    if DATASETS:
        return
    
    # Demo datasets
    demo_datasets = [
        {
            "id": "ds-rice-blast-001",
            "name": "Rice Blast Detection v2",
            "description": "Rice blast disease detection dataset with 4 severity classes",
            "dataset_type": DatasetType.CLASSIFICATION,
            "crop": "rice",
            "classes": ["healthy", "mild", "moderate", "severe"],
            "status": DatasetStatus.READY,
            "image_count": 2847,
            "annotated_count": 2847,
            "train_split": 0.7,
            "val_split": 0.15,
            "test_split": 0.15,
            "quality_score": 94.2,
            "created_at": "2025-11-15T10:30:00Z",
            "updated_at": "2025-12-10T14:20:00Z",
            "created_by": "demo_user",
        },
        {
            "id": "ds-wheat-rust-001",
            "name": "Wheat Rust Classification",
            "description": "Stem rust, leaf rust, and stripe rust detection",
            "dataset_type": DatasetType.CLASSIFICATION,
            "crop": "wheat",
            "classes": ["healthy", "stem_rust", "leaf_rust", "stripe_rust"],
            "status": DatasetStatus.READY,
            "image_count": 1523,
            "annotated_count": 1523,
            "train_split": 0.7,
            "val_split": 0.15,
            "test_split": 0.15,
            "quality_score": 91.8,
            "created_at": "2025-10-20T08:15:00Z",
            "updated_at": "2025-12-08T11:45:00Z",
            "created_by": "demo_user",
        },
        {
            "id": "ds-maize-growth-001",
            "name": "Maize Growth Stages",
            "description": "Growth stage classification using BBCH scale",
            "dataset_type": DatasetType.CLASSIFICATION,
            "crop": "maize",
            "classes": ["VE", "V1-V6", "V7-V12", "VT", "R1", "R2-R4", "R5-R6"],
            "status": DatasetStatus.DRAFT,
            "image_count": 892,
            "annotated_count": 654,
            "train_split": 0.7,
            "val_split": 0.15,
            "test_split": 0.15,
            "quality_score": 78.5,
            "created_at": "2025-12-01T16:00:00Z",
            "updated_at": "2025-12-11T09:30:00Z",
            "created_by": "demo_user",
        },
    ]
    
    for ds in demo_datasets:
        DATASETS[ds["id"]] = ds
    
    # Demo models
    demo_models = [
        {
            "id": "model-rice-blast-v3",
            "name": "RiceBlast-v3",
            "description": "Rice blast disease detection model",
            "dataset_id": "ds-rice-blast-001",
            "crop": "rice",
            "task": "classification",
            "base_model": "MobileNetV2",
            "accuracy": 0.94,
            "precision": 0.93,
            "recall": 0.92,
            "f1_score": 0.925,
            "size_mb": 12.4,
            "inference_time_ms": 45,
            "status": "deployed",
            "version": "3.0.0",
            "created_at": "2025-11-20T14:00:00Z",
            "downloads": 156,
        },
        {
            "id": "model-wheat-rust-v2",
            "name": "WheatRust-v2",
            "description": "Wheat rust disease classification",
            "dataset_id": "ds-wheat-rust-001",
            "crop": "wheat",
            "task": "classification",
            "base_model": "EfficientNetB0",
            "accuracy": 0.91,
            "precision": 0.90,
            "recall": 0.89,
            "f1_score": 0.895,
            "size_mb": 15.2,
            "inference_time_ms": 52,
            "status": "deployed",
            "version": "2.0.0",
            "created_at": "2025-10-25T10:30:00Z",
            "downloads": 89,
        },
        {
            "id": "model-maize-growth-v1",
            "name": "MaizeGrowth-v1",
            "description": "Maize growth stage classifier",
            "dataset_id": "ds-maize-growth-001",
            "crop": "maize",
            "task": "classification",
            "base_model": "MobileNetV2",
            "accuracy": 0.88,
            "precision": 0.87,
            "recall": 0.86,
            "f1_score": 0.865,
            "size_mb": 8.7,
            "inference_time_ms": 38,
            "status": "ready",
            "version": "1.0.0",
            "created_at": "2025-12-05T09:15:00Z",
            "downloads": 34,
        },
    ]
    
    for model in demo_models:
        MODELS[model["id"]] = model


# Initialize demo data on module load
_init_demo_data()


class VisionDatasetService:
    """Service for managing vision datasets"""
    
    def create_dataset(
        self,
        name: str,
        description: str,
        dataset_type: DatasetType,
        crop: str,
        classes: list[str],
        train_split: float = 0.7,
        val_split: float = 0.15,
        test_split: float = 0.15,
        created_by: str = "system",
    ) -> dict:
        """Create a new dataset"""
        dataset_id = f"ds-{uuid.uuid4().hex[:8]}"
        
        dataset = {
            "id": dataset_id,
            "name": name,
            "description": description,
            "dataset_type": dataset_type,
            "crop": crop,
            "classes": classes,
            "status": DatasetStatus.DRAFT,
            "image_count": 0,
            "annotated_count": 0,
            "train_split": train_split,
            "val_split": val_split,
            "test_split": test_split,
            "quality_score": 0.0,
            "created_at": datetime.now(UTC).isoformat() + "Z",
            "updated_at": datetime.now(UTC).isoformat() + "Z",
            "created_by": created_by,
        }
        
        DATASETS[dataset_id] = dataset
        IMAGES[dataset_id] = []
        
        return dataset
    
    def get_dataset(self, dataset_id: str) -> Optional[dict]:
        """Get dataset by ID"""
        return DATASETS.get(dataset_id)
    
    def list_datasets(
        self,
        crop: Optional[str] = None,
        status: Optional[DatasetStatus] = None,
        dataset_type: Optional[DatasetType] = None,
    ) -> list[dict]:
        """List all datasets with optional filters"""
        datasets = list(DATASETS.values())
        
        if crop:
            datasets = [d for d in datasets if d["crop"] == crop]
        if status:
            datasets = [d for d in datasets if d["status"] == status]
        if dataset_type:
            datasets = [d for d in datasets if d["dataset_type"] == dataset_type]
        
        return sorted(datasets, key=lambda x: x["updated_at"], reverse=True)
    
    def update_dataset(self, dataset_id: str, updates: dict) -> Optional[dict]:
        """Update dataset metadata"""
        if dataset_id not in DATASETS:
            return None
        
        allowed_fields = ["name", "description", "classes", "train_split", "val_split", "test_split", "status"]
        for field in allowed_fields:
            if field in updates:
                DATASETS[dataset_id][field] = updates[field]
        
        DATASETS[dataset_id]["updated_at"] = datetime.now(UTC).isoformat() + "Z"
        return DATASETS[dataset_id]
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset"""
        if dataset_id not in DATASETS:
            return False
        
        del DATASETS[dataset_id]
        if dataset_id in IMAGES:
            del IMAGES[dataset_id]
        return True
    
    def add_images(
        self,
        dataset_id: str,
        images: list[dict],
    ) -> dict:
        """Add images to a dataset"""
        if dataset_id not in DATASETS:
            return {"error": "Dataset not found"}
        
        if dataset_id not in IMAGES:
            IMAGES[dataset_id] = []
        
        added = []
        for img in images:
            image_id = f"img-{uuid.uuid4().hex[:8]}"
            image_record = {
                "id": image_id,
                "filename": img.get("filename", f"image_{image_id}.jpg"),
                "url": img.get("url", f"/storage/datasets/{dataset_id}/{image_id}.jpg"),
                "width": img.get("width", 640),
                "height": img.get("height", 480),
                "size_bytes": img.get("size_bytes", random.randint(50000, 500000)),
                "metadata": img.get("metadata", {}),
                "annotation": img.get("annotation"),
                "split": img.get("split", "train"),
                "uploaded_at": datetime.now(UTC).isoformat() + "Z",
            }
            IMAGES[dataset_id].append(image_record)
            added.append(image_record)
        
        # Update dataset counts
        DATASETS[dataset_id]["image_count"] = len(IMAGES[dataset_id])
        DATASETS[dataset_id]["annotated_count"] = len([i for i in IMAGES[dataset_id] if i.get("annotation")])
        DATASETS[dataset_id]["updated_at"] = datetime.now(UTC).isoformat() + "Z"
        
        # Recalculate quality score
        if DATASETS[dataset_id]["image_count"] > 0:
            DATASETS[dataset_id]["quality_score"] = round(
                (DATASETS[dataset_id]["annotated_count"] / DATASETS[dataset_id]["image_count"]) * 100, 1
            )
        
        return {
            "added": len(added),
            "total_images": DATASETS[dataset_id]["image_count"],
            "images": added,
        }
    
    def get_dataset_images(
        self,
        dataset_id: str,
        split: Optional[str] = None,
        annotated_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Get images from a dataset"""
        if dataset_id not in IMAGES:
            return []
        
        images = IMAGES[dataset_id]
        
        if split:
            images = [i for i in images if i.get("split") == split]
        if annotated_only:
            images = [i for i in images if i.get("annotation")]
        
        return images[offset:offset + limit]
    
    def get_dataset_stats(self, dataset_id: str) -> Optional[dict]:
        """Get detailed statistics for a dataset"""
        dataset = DATASETS.get(dataset_id)
        if not dataset:
            return None
        
        images = IMAGES.get(dataset_id, [])
        
        # Calculate class distribution
        class_counts = {cls: 0 for cls in dataset["classes"]}
        for img in images:
            if img.get("annotation"):
                label = img["annotation"].get("label")
                if label in class_counts:
                    class_counts[label] += 1
        
        # Calculate split distribution
        split_counts = {"train": 0, "val": 0, "test": 0}
        for img in images:
            split = img.get("split", "train")
            if split in split_counts:
                split_counts[split] += 1
        
        return {
            "dataset_id": dataset_id,
            "total_images": dataset["image_count"],
            "annotated_images": dataset["annotated_count"],
            "unannotated_images": dataset["image_count"] - dataset["annotated_count"],
            "annotation_progress": round(dataset["annotated_count"] / max(dataset["image_count"], 1) * 100, 1),
            "quality_score": dataset["quality_score"],
            "class_distribution": class_counts,
            "split_distribution": split_counts,
            "classes": dataset["classes"],
            "recommended_actions": _get_recommendations(dataset, class_counts),
        }
    
    def export_annotations(
        self,
        dataset_id: str,
        format: str = "coco",
    ) -> Optional[dict]:
        """Export dataset annotations in specified format"""
        dataset = DATASETS.get(dataset_id)
        if not dataset:
            return None
        
        images = IMAGES.get(dataset_id, [])
        
        if format == "coco":
            return _export_coco(dataset, images)
        elif format == "yolo":
            return _export_yolo(dataset, images)
        elif format == "csv":
            return _export_csv(dataset, images)
        else:
            return {"error": f"Unsupported format: {format}"}


class VisionModelService:
    """Service for managing vision models"""
    
    def list_models(
        self,
        crop: Optional[str] = None,
        task: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        """List available models"""
        models = list(MODELS.values())
        
        if crop:
            models = [m for m in models if m["crop"] == crop]
        if task:
            models = [m for m in models if m["task"] == task]
        if status:
            models = [m for m in models if m["status"] == status]
        
        return sorted(models, key=lambda x: x["downloads"], reverse=True)
    
    def get_model(self, model_id: str) -> Optional[dict]:
        """Get model by ID"""
        return MODELS.get(model_id)
    
    def predict(
        self,
        model_id: str,
        image_data: str,
    ) -> dict:
        """Run inference on an image (simulated for Phase 1)"""
        model = MODELS.get(model_id)
        if not model:
            return {"error": "Model not found"}
        
        # Simulated predictions based on model type
        if model["crop"] == "rice":
            predictions = [
                {"label": "healthy", "confidence": 0.12},
                {"label": "mild", "confidence": 0.08},
                {"label": "moderate", "confidence": 0.15},
                {"label": "severe", "confidence": 0.65},
            ]
        elif model["crop"] == "wheat":
            predictions = [
                {"label": "healthy", "confidence": 0.05},
                {"label": "stem_rust", "confidence": 0.78},
                {"label": "leaf_rust", "confidence": 0.12},
                {"label": "stripe_rust", "confidence": 0.05},
            ]
        else:
            predictions = [
                {"label": "VE", "confidence": 0.02},
                {"label": "V1-V6", "confidence": 0.05},
                {"label": "V7-V12", "confidence": 0.08},
                {"label": "VT", "confidence": 0.75},
                {"label": "R1", "confidence": 0.07},
                {"label": "R2-R4", "confidence": 0.02},
                {"label": "R5-R6", "confidence": 0.01},
            ]
        
        # Sort by confidence
        predictions.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "model_id": model_id,
            "model_name": model["name"],
            "predictions": predictions,
            "top_prediction": predictions[0],
            "inference_time_ms": model["inference_time_ms"],
        }


def _get_recommendations(dataset: dict, class_counts: dict) -> list[str]:
    """Generate recommendations for dataset improvement"""
    recommendations = []
    
    # Check annotation progress
    if dataset["annotated_count"] < dataset["image_count"]:
        unannotated = dataset["image_count"] - dataset["annotated_count"]
        recommendations.append(f"Annotate {unannotated} remaining images")
    
    # Check class balance
    if class_counts:
        counts = list(class_counts.values())
        if counts and max(counts) > 0:
            imbalance = max(counts) / max(min(counts), 1)
            if imbalance > 3:
                min_class = min(class_counts, key=class_counts.get)
                recommendations.append(f"Add more images for class '{min_class}' to improve balance")
    
    # Check total images
    if dataset["image_count"] < 500:
        recommendations.append("Consider adding more images (500+ recommended for training)")
    
    # Check quality score
    if dataset["quality_score"] < 80:
        recommendations.append("Review annotations for quality (target 80%+ quality score)")
    
    return recommendations


def _export_coco(dataset: dict, images: list) -> dict:
    """Export in COCO format"""
    coco = {
        "info": {
            "description": dataset["description"],
            "version": "1.0",
            "year": 2025,
            "contributor": "Bijmantra",
            "date_created": dataset["created_at"],
        },
        "categories": [
            {"id": i, "name": cls} for i, cls in enumerate(dataset["classes"])
        ],
        "images": [],
        "annotations": [],
    }
    
    for i, img in enumerate(images):
        coco["images"].append({
            "id": i,
            "file_name": img["filename"],
            "width": img["width"],
            "height": img["height"],
        })
        
        if img.get("annotation"):
            label = img["annotation"].get("label")
            category_id = dataset["classes"].index(label) if label in dataset["classes"] else 0
            coco["annotations"].append({
                "id": i,
                "image_id": i,
                "category_id": category_id,
            })
    
    return coco


def _export_yolo(dataset: dict, images: list) -> dict:
    """Export in YOLO format"""
    return {
        "format": "yolo",
        "classes": dataset["classes"],
        "images": [
            {
                "filename": img["filename"],
                "label": img.get("annotation", {}).get("label", ""),
                "class_id": dataset["classes"].index(img.get("annotation", {}).get("label", dataset["classes"][0])) if img.get("annotation") else -1,
            }
            for img in images
        ],
    }


def _export_csv(dataset: dict, images: list) -> dict:
    """Export as CSV-compatible dict"""
    return {
        "format": "csv",
        "headers": ["filename", "label", "split", "width", "height"],
        "rows": [
            [
                img["filename"],
                img.get("annotation", {}).get("label", ""),
                img.get("split", "train"),
                img["width"],
                img["height"],
            ]
            for img in images
        ],
    }


# Service instances
vision_dataset_service = VisionDatasetService()
vision_model_service = VisionModelService()

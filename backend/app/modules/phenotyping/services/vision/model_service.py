"""
Vision Model Management Service

Model registry and inference scaffold for CNN-based plant phenotyping.
Supports model version tracking, metadata management, and a pluggable
inference interface for ONNX/TorchScript/TFLite models.

This service now fails closed when runtime weights are unavailable.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

import numpy as np


logger = logging.getLogger(__name__)


class VisionModel:
    """Metadata container for a registered vision model."""

    def __init__(
        self,
        name: str,
        task: str,
        architecture: str,
        input_shape: tuple,
        classes: list[str],
        version: str = "1.0",
        framework: str = "onnx",
        runtime_available: bool = False,
    ):
        self.id = str(uuid4())[:8]
        self.name = name
        self.task = task
        self.architecture = architecture
        self.input_shape = input_shape
        self.classes = classes
        self.version = version
        self.framework = framework
        self.runtime_available = runtime_available
        self.created_at = datetime.utcnow().isoformat()
        self.metrics: dict[str, float] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "task": self.task,
            "architecture": self.architecture,
            "input_shape": list(self.input_shape),
            "classes": self.classes,
            "n_classes": len(self.classes),
            "version": self.version,
            "framework": self.framework,
            "runtime_available": self.runtime_available,
            "created_at": self.created_at,
            "metrics": self.metrics,
        }


class VisionModelService:
    """Model registry and runtime readiness gate for plant vision models."""

    def __init__(self):
        self.models: dict[str, VisionModel] = {}
        self._init_default_models()

    def _init_default_models(self):
        """Register built-in model definitions."""
        defaults = [
            VisionModel(
                name="PlantDiseaseNet",
                task="classification",
                architecture="ResNet50",
                input_shape=(224, 224, 3),
                classes=["healthy", "leaf_blight", "rust", "powdery_mildew", "bacterial_spot"],
                version="1.0",
            ),
            VisionModel(
                name="CanopySegNet",
                task="segmentation",
                architecture="UNet",
                input_shape=(512, 512, 3),
                classes=["background", "canopy", "soil", "shadow"],
                version="1.0",
            ),
            VisionModel(
                name="SeedCounterNet",
                task="detection",
                architecture="YOLOv8-nano",
                input_shape=(640, 640, 3),
                classes=["seed"],
                version="1.0",
            ),
        ]
        for model in defaults:
            self.models[model.id] = model

    def register_model(
        self,
        name: str,
        task: str,
        architecture: str,
        input_shape: tuple,
        classes: list[str],
        version: str = "1.0",
        framework: str = "onnx",
        runtime_available: bool = False,
    ) -> dict[str, Any]:
        """Register a new vision model."""
        model = VisionModel(
            name=name,
            task=task,
            architecture=architecture,
            input_shape=input_shape,
            classes=classes,
            version=version,
            framework=framework,
            runtime_available=runtime_available,
        )
        self.models[model.id] = model
        logger.info("Registered model: %s (%s)", name, model.id)
        return model.to_dict()

    def list_models(self, task: str | None = None) -> list[dict[str, Any]]:
        """List all registered models, optionally filtered by task."""
        models = list(self.models.values())
        if task:
            models = [model for model in models if model.task == task]
        return [model.to_dict() for model in models]

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        """Get model by ID."""
        model = self.models.get(model_id)
        return model.to_dict() if model else None

    def preprocess_image(
        self,
        image: np.ndarray,
        target_shape: tuple,
        normalize: bool = True,
    ) -> np.ndarray:
        """Preprocess image for model input."""
        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV not installed") from exc

        target_h, target_w = target_shape[0], target_shape[1]
        resized = cv2.resize(image, (target_w, target_h))

        if normalize:
            resized = resized.astype(np.float32) / 255.0

        return resized

    def predict(
        self,
        model_id: str,
        image: np.ndarray,
    ) -> dict[str, Any]:
        """Run inference only when a real runtime is available."""
        model = self.models.get(model_id)
        if not model:
            return {"error": f"Model {model_id} not found"}

        self.preprocess_image(image, model.input_shape)

        if not model.runtime_available:
            return {
                "error": f"Model {model.name} is registered for metadata only. Runtime weights are not available.",
                "model": model.name,
                "task": model.task,
                "status": "runtime_unavailable",
            }

        return {"error": f"No runtime adapter is implemented for task {model.task}"}

    def batch_predict(
        self,
        model_id: str,
        images: list[np.ndarray],
    ) -> list[dict[str, Any]]:
        """Run inference on multiple images."""
        return [self.predict(model_id, image) for image in images]


vision_model_service = VisionModelService()

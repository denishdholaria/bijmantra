"""
Tests for Vision Model Management Service (B4.4)
"""

import pytest
import numpy as np
from app.modules.phenotyping.services.vision.model_service import vision_model_service


class TestVisionModelService:

    def test_default_models_registered(self):
        """Default models should be pre-registered."""
        models = vision_model_service.list_models()
        assert len(models) >= 3

        names = [m["name"] for m in models]
        assert "PlantDiseaseNet" in names
        assert "CanopySegNet" in names
        assert "SeedCounterNet" in names

    def test_register_custom_model(self):
        """Should register a new model and return its metadata."""
        result = vision_model_service.register_model(
            name="TestNet",
            task="classification",
            architecture="MobileNetV2",
            input_shape=(224, 224, 3),
            classes=["class_a", "class_b"],
            version="0.1",
        )
        assert result["name"] == "TestNet"
        assert result["n_classes"] == 2
        assert result["id"] is not None
        assert result["runtime_available"] is False

    def test_filter_by_task(self):
        """Should filter models by task type."""
        seg_models = vision_model_service.list_models(task="segmentation")
        for m in seg_models:
            assert m["task"] == "segmentation"

    def test_classification_inference_requires_runtime(self):
        """Metadata-only models should fail closed until runtime weights exist."""
        models = vision_model_service.list_models(task="classification")
        model_id = models[0]["id"]

        dummy_image = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
        result = vision_model_service.predict(model_id, dummy_image)

        assert result["status"] == "runtime_unavailable"
        assert "Runtime weights are not available" in result["error"]

    def test_detection_inference_requires_runtime(self):
        """Detection models should fail closed until runtime weights exist."""
        models = vision_model_service.list_models(task="detection")
        model_id = models[0]["id"]

        dummy_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        result = vision_model_service.predict(model_id, dummy_image)

        assert result["status"] == "runtime_unavailable"
        assert result["task"] == "detection"

    def test_batch_predict(self):
        """Batch prediction should return one fail-closed result per image."""
        models = vision_model_service.list_models(task="classification")
        model_id = models[0]["id"]

        images = [
            np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            for _ in range(3)
        ]
        results = vision_model_service.batch_predict(model_id, images)

        assert len(results) == 3
        assert all(result["status"] == "runtime_unavailable" for result in results)

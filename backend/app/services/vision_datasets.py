"""
Vision Datasets Service — stub replacement.

Refactored: Session 94 — removed all in-memory demo data.
Provides the same interface but returns empty results.
Dataset CRUD will be backed by a VisionDataset table in a future migration.
"""

from enum import Enum


class DatasetType(str, Enum):
    CLASSIFICATION = "classification"
    DETECTION = "detection"
    SEGMENTATION = "segmentation"


class DatasetStatus(str, Enum):
    DRAFT = "draft"
    COLLECTING = "collecting"
    ANNOTATING = "annotating"
    READY = "ready"
    TRAINING = "training"


class VisionDatasetService:
    """Stub — returns empty results until VisionDataset table is created."""

    def create_dataset(self, **kwargs) -> dict:
        return {"error": "VisionDataset table not yet created. Migration pending."}

    def list_datasets(self, **kwargs) -> list:
        return []

    def get_dataset(self, dataset_id: str) -> dict | None:
        return None

    def update_dataset(self, dataset_id: str, updates: dict) -> dict | None:
        return None

    def delete_dataset(self, dataset_id: str) -> bool:
        return False

    def add_images(self, dataset_id: str, images: list) -> dict:
        return {"error": "VisionDataset table not yet created"}

    def get_dataset_images(self, dataset_id: str, **kwargs) -> list:
        return []

    def get_dataset_stats(self, dataset_id: str) -> dict | None:
        return None

    def export_annotations(self, dataset_id: str, fmt: str) -> dict | None:
        return None


class VisionModelService:
    """Stub — returns empty results until VisionModel queries are wired."""

    def list_models(self, **kwargs) -> list:
        return []

    def get_model(self, model_id: str) -> dict | None:
        return None

    def predict(self, model_id: str, image_data: str) -> dict:
        return {"error": "No models available"}


vision_dataset_service = VisionDatasetService()
vision_model_service = VisionModelService()

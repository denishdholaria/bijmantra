"""
Vision Datasets Service — stub replacement.

Refactored: Session 94 — removed all in-memory demo data.
Provides the same interface but returns empty results.
Dataset CRUD will be backed by a VisionDataset table in a future migration.
"""

from enum import StrEnum


class DatasetType(StrEnum):
    CLASSIFICATION = "classification"
    DETECTION = "detection"
    SEGMENTATION = "segmentation"


class DatasetStatus(StrEnum):
    DRAFT = "draft"
    COLLECTING = "collecting"
    ANNOTATING = "annotating"
    READY = "ready"
    TRAINING = "training"


class VisionDatasetService:
    """Stub — returns empty results until VisionDataset table is created."""

    def create_dataset(self, **_kwargs) -> dict:
        return {"error": "VisionDataset table not yet created. Migration pending."}

    def list_datasets(self, **_kwargs) -> list:
        return []

    def get_dataset(self, _dataset_id: str) -> dict | None:
        return None

    def update_dataset(self, _dataset_id: str, _updates: dict) -> dict | None:
        return None

    def delete_dataset(self, _dataset_id: str) -> bool:
        return False

    def add_images(self, _dataset_id: str, _images: list) -> dict:
        return {"error": "VisionDataset table not yet created"}

    def get_dataset_images(self, _dataset_id: str, **_kwargs) -> list:
        return []

    def get_dataset_stats(self, _dataset_id: str) -> dict | None:
        return None

    def export_annotations(self, _dataset_id: str, _fmt: str) -> dict | None:
        return None


class VisionModelService:
    """Stub — returns empty results until VisionModel queries are wired."""

    def list_models(self, **_kwargs) -> list:
        return []

    def get_model(self, _model_id: str) -> dict | None:
        return None

    def predict(self, _model_id: str, _image_data: str) -> dict:
        return {"error": "No models available"}


vision_dataset_service = VisionDatasetService()
vision_model_service = VisionModelService()

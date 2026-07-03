"""Vision dataset and model catalog services.

The dataset service is backed by the persisted vision tables and enforces
organization scoping on every query. It intentionally stores image references
and metadata, not raw image bytes; object storage remains a separate concern.
"""

import os
from collections import Counter
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.vision import (
    VisionDataset,
    VisionDatasetImage,
    VisionDatasetStatus,
    VisionDatasetType,
    VisionModel,
    VisionModelLifecycleState,
)
from app.modules.phenotyping.services.vision.artifact_utils import validate_artifact_checksum


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


VALID_SPLITS = {"train", "val", "test"}


def _dataset_code() -> str:
    return f"vision-dataset-{uuid4().hex[:12]}"


def _image_code() -> str:
    return f"vision-image-{uuid4().hex[:12]}"


def _clean_filename(filename: str) -> str:
    cleaned = os.path.basename(filename or "").strip()
    return cleaned or "image"


def _normalize_dataset_type(value: str | DatasetType | VisionDatasetType) -> VisionDatasetType:
    raw = value.value if isinstance(value, StrEnum) else str(value)
    return VisionDatasetType(raw.upper())


def _normalize_dataset_status(
    value: str | DatasetStatus | VisionDatasetStatus,
) -> VisionDatasetStatus:
    raw = value.value if isinstance(value, StrEnum) else str(value)
    return VisionDatasetStatus(raw.upper())


def _api_dataset_type(value: VisionDatasetType) -> str:
    return value.value.lower()


def _api_dataset_status(value: VisionDatasetStatus) -> str:
    return value.value.lower()


class VisionDatasetService:
    """Persisted dataset lifecycle service."""

    def _serialize_dataset(
        self,
        dataset: VisionDataset,
        image_count: int | None = None,
        annotated_count: int | None = None,
    ) -> dict:
        if image_count is None:
            image_count = len(dataset.images) if "images" in dataset.__dict__ else 0
        if annotated_count is None:
            if "images" in dataset.__dict__:
                annotated_count = sum(1 for image in dataset.images if image.annotation_data)
            else:
                annotated_count = 0

        quality_score = round((annotated_count / image_count) * 100, 2) if image_count else 0.0

        return {
            "id": str(dataset.id),
            "dataset_code": dataset.dataset_code,
            "organization_id": dataset.organization_id,
            "name": dataset.name,
            "description": dataset.description or "",
            "dataset_type": _api_dataset_type(dataset.dataset_type),
            "crop": dataset.crop,
            "classes": dataset.classes or [],
            "train_split": dataset.train_split,
            "val_split": dataset.val_split,
            "test_split": dataset.test_split,
            "status": _api_dataset_status(dataset.status),
            "created_by": dataset.created_by,
            "image_count": image_count,
            "total_images": image_count,
            "annotated_count": annotated_count,
            "quality_score": quality_score,
            "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
            "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None,
        }

    def _serialize_image(self, image: VisionDatasetImage) -> dict:
        return {
            "id": str(image.id),
            "image_code": image.image_code,
            "dataset_id": str(image.dataset_id),
            "organization_id": image.organization_id,
            "filename": image.filename,
            "url": image.url,
            "width": image.width,
            "height": image.height,
            "size_bytes": image.size_bytes,
            "split": image.split,
            "metadata": image.metadata_json or {},
            "annotation": image.annotation_data,
            "created_at": image.created_at.isoformat() if image.created_at else None,
            "updated_at": image.updated_at.isoformat() if image.updated_at else None,
        }

    def _splits_are_valid(self, train_split: float, val_split: float, test_split: float) -> bool:
        return abs(train_split + val_split + test_split - 1.0) <= 0.01

    async def _get_dataset_row(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str,
        *,
        include_images: bool = False,
    ) -> VisionDataset | None:
        query = select(VisionDataset).where(VisionDataset.organization_id == organization_id)
        if include_images:
            query = query.options(selectinload(VisionDataset.images))

        if str(dataset_id).isdigit():
            query = query.where(
                or_(
                    VisionDataset.id == int(dataset_id),
                    VisionDataset.dataset_code == str(dataset_id),
                )
            )
        else:
            query = query.where(VisionDataset.dataset_code == str(dataset_id))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_dataset(
        self,
        db: AsyncSession,
        organization_id: int,
        *,
        name: str,
        description: str,
        dataset_type: DatasetType,
        crop: str,
        classes: list[str],
        train_split: float,
        val_split: float,
        test_split: float,
        created_by: str | None = None,
    ) -> dict:
        if not self._splits_are_valid(train_split, val_split, test_split):
            return {"error": "Train, val, and test splits must sum to 1.0"}

        dataset = VisionDataset(
            dataset_code=_dataset_code(),
            organization_id=organization_id,
            name=name.strip(),
            description=description,
            dataset_type=_normalize_dataset_type(dataset_type),
            crop=crop.strip().lower(),
            classes=[label.strip() for label in classes if label.strip()],
            train_split=train_split,
            val_split=val_split,
            test_split=test_split,
            status=VisionDatasetStatus.DRAFT,
            created_by=created_by,
        )
        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)
        return self._serialize_dataset(dataset)

    async def list_datasets(
        self,
        db: AsyncSession,
        organization_id: int,
        *,
        crop: str | None = None,
        status: DatasetStatus | None = None,
        dataset_type: DatasetType | None = None,
    ) -> list[dict]:
        counts_query = (
            select(
                VisionDatasetImage.dataset_id,
                func.count(VisionDatasetImage.id).label("image_count"),
                func.sum(case((VisionDatasetImage.annotation_data.is_not(None), 1), else_=0)).label(
                    "annotated_count"
                ),
            )
            .where(VisionDatasetImage.organization_id == organization_id)
            .group_by(VisionDatasetImage.dataset_id)
        )
        counts_result = await db.execute(counts_query)
        counts = {
            row.dataset_id: {
                "image_count": row.image_count or 0,
                "annotated_count": row.annotated_count or 0,
            }
            for row in counts_result
        }

        query = select(VisionDataset).where(VisionDataset.organization_id == organization_id)
        if crop:
            query = query.where(VisionDataset.crop == crop.lower())
        if status:
            query = query.where(VisionDataset.status == _normalize_dataset_status(status))
        if dataset_type:
            query = query.where(VisionDataset.dataset_type == _normalize_dataset_type(dataset_type))
        query = query.order_by(VisionDataset.created_at.desc(), VisionDataset.id.desc())

        result = await db.execute(query)
        datasets = result.scalars().all()
        return [
            self._serialize_dataset(
                dataset,
                counts.get(dataset.id, {}).get("image_count", 0),
                counts.get(dataset.id, {}).get("annotated_count", 0),
            )
            for dataset in datasets
        ]

    async def get_dataset(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str,
    ) -> dict | None:
        dataset = await self._get_dataset_row(db, organization_id, dataset_id, include_images=True)
        return self._serialize_dataset(dataset) if dataset else None

    async def update_dataset(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str,
        updates: dict,
    ) -> dict | None:
        dataset = await self._get_dataset_row(db, organization_id, dataset_id, include_images=True)
        if not dataset:
            return None

        train = updates.get("train_split", dataset.train_split)
        val = updates.get("val_split", dataset.val_split)
        test = updates.get("test_split", dataset.test_split)
        if not self._splits_are_valid(train, val, test):
            return {"error": "Train, val, and test splits must sum to 1.0"}

        if "name" in updates:
            dataset.name = updates["name"].strip()
        if "description" in updates:
            dataset.description = updates["description"]
        if "classes" in updates:
            dataset.classes = [label.strip() for label in updates["classes"] if label.strip()]
        if "train_split" in updates:
            dataset.train_split = updates["train_split"]
        if "val_split" in updates:
            dataset.val_split = updates["val_split"]
        if "test_split" in updates:
            dataset.test_split = updates["test_split"]
        if "status" in updates:
            dataset.status = _normalize_dataset_status(updates["status"])
        dataset.updated_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(dataset)
        return self._serialize_dataset(dataset)

    async def delete_dataset(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str,
    ) -> bool:
        dataset = await self._get_dataset_row(db, organization_id, dataset_id)
        if not dataset:
            return False

        await db.execute(
            delete(VisionDatasetImage).where(
                VisionDatasetImage.dataset_id == dataset.id,
                VisionDatasetImage.organization_id == organization_id,
            )
        )
        await db.execute(
            delete(VisionDataset).where(
                VisionDataset.id == dataset.id,
                VisionDataset.organization_id == organization_id,
            )
        )
        await db.commit()
        return True

    async def add_images(
        self,
        db: AsyncSession,
        organization_id: int,
        *,
        dataset_id: str,
        images: list[dict],
    ) -> dict:
        dataset = await self._get_dataset_row(db, organization_id, dataset_id)
        if not dataset:
            return {"error": "Dataset not found"}

        rows: list[VisionDatasetImage] = []
        for image in images:
            split = image.get("split", "train")
            if split not in VALID_SPLITS:
                return {"error": f"Invalid split '{split}'"}

            rows.append(
                VisionDatasetImage(
                    image_code=_image_code(),
                    dataset_id=dataset.id,
                    organization_id=organization_id,
                    filename=_clean_filename(image.get("filename", "")),
                    url=image.get("url"),
                    width=int(image.get("width") or 0),
                    height=int(image.get("height") or 0),
                    size_bytes=image.get("size_bytes"),
                    split=split,
                    metadata_json=image.get("metadata") or {},
                    annotation_data=image.get("annotation"),
                )
            )

        db.add_all(rows)
        await db.commit()
        for row in rows:
            await db.refresh(row)

        total_result = await db.execute(
            select(func.count(VisionDatasetImage.id)).where(
                VisionDatasetImage.dataset_id == dataset.id,
                VisionDatasetImage.organization_id == organization_id,
            )
        )
        total_images = total_result.scalar_one()
        return {
            "dataset_id": str(dataset.id),
            "dataset_code": dataset.dataset_code,
            "added_count": len(rows),
            "total_images": total_images,
            "images": [self._serialize_image(row) for row in rows],
        }

    async def get_dataset_images(
        self,
        db: AsyncSession,
        organization_id: int,
        *,
        dataset_id: str,
        split: str | None = None,
        annotated_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        dataset = await self._get_dataset_row(db, organization_id, dataset_id)
        if not dataset:
            return []

        query = select(VisionDatasetImage).where(
            VisionDatasetImage.organization_id == organization_id,
            VisionDatasetImage.dataset_id == dataset.id,
        )
        if split:
            query = query.where(VisionDatasetImage.split == split)
        if annotated_only:
            query = query.where(VisionDatasetImage.annotation_data.is_not(None))
        query = query.order_by(VisionDatasetImage.created_at.desc(), VisionDatasetImage.id.desc())
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        images = [self._serialize_image(image) for image in result.scalars().all()]
        if annotated_only:
            images = [image for image in images if image["annotation"]]
        return images

    async def get_dataset_stats(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str,
    ) -> dict | None:
        dataset = await self._get_dataset_row(db, organization_id, dataset_id, include_images=True)
        if not dataset:
            return None

        split_counts = {split: 0 for split in VALID_SPLITS}
        class_distribution: Counter[str] = Counter()
        annotated_count = 0

        for image in dataset.images:
            split_counts[image.split] = split_counts.get(image.split, 0) + 1
            if image.annotation_data:
                annotated_count += 1
                label = image.annotation_data.get("label")
                if label:
                    class_distribution[label] += 1

        image_count = len(dataset.images)
        quality_score = round((annotated_count / image_count) * 100, 2) if image_count else 0.0

        return {
            "dataset": self._serialize_dataset(dataset, image_count, annotated_count),
            "image_count": image_count,
            "annotated_count": annotated_count,
            "unannotated_count": image_count - annotated_count,
            "split_counts": {
                "train": split_counts.get("train", 0),
                "val": split_counts.get("val", 0),
                "test": split_counts.get("test", 0),
            },
            "class_distribution": dict(class_distribution),
            "quality_score": quality_score,
        }

    async def export_annotations(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str,
        fmt: str,
    ) -> dict | None:
        dataset = await self._get_dataset_row(db, organization_id, dataset_id)
        if not dataset:
            return None

        images = await self.get_dataset_images(
            db,
            organization_id,
            dataset_id=str(dataset.id),
            annotated_only=True,
            limit=10000,
        )
        export_format = fmt.lower()

        if export_format == "csv":
            rows = [
                {
                    "image_id": image["id"],
                    "filename": image["filename"],
                    "label": image["annotation"].get("label"),
                    "split": image["split"],
                }
                for image in images
            ]
            return {"format": "csv", "rows": rows}

        if export_format == "coco":
            return {
                "format": "coco",
                "images": [
                    {
                        "id": image["id"],
                        "file_name": image["filename"],
                        "width": image["width"],
                        "height": image["height"],
                    }
                    for image in images
                ],
                "annotations": [
                    {
                        "image_id": image["id"],
                        "label": image["annotation"].get("label"),
                        "data": image["annotation"],
                    }
                    for image in images
                ],
                "categories": dataset.classes or [],
            }

        if export_format == "yolo":
            return {
                "format": "yolo",
                "labels": [
                    {
                        "image_id": image["id"],
                        "filename": image["filename"],
                        "annotation": image["annotation"],
                    }
                    for image in images
                ],
            }

        return {"error": f"Unsupported export format '{fmt}'"}


class VisionModelService:
    """Persisted model metadata facade used by the Vision API."""

    def _serialize_model(self, model: VisionModel) -> dict:
        artifact_exists = bool(model.file_path and os.path.exists(model.file_path))
        artifact_valid = (
            artifact_exists
            and os.path.isdir(model.file_path)
            and validate_artifact_checksum(Path(model.file_path), model.artifact_checksum)
        )
        lifecycle_state = model.lifecycle_state or VisionModelLifecycleState.CANDIDATE.value
        provenance = model.training_provenance or {}
        return {
            "id": str(model.id),
            "name": model.name,
            "description": model.description,
            "version": model.version,
            "format": model.format,
            "file_path": model.file_path,
            "metrics": model.metrics or {},
            "size_bytes": model.size_bytes,
            "size_mb": round((model.size_bytes or 0) / (1024 * 1024), 2),
            "status": "ready" if artifact_exists else "artifact_missing",
            "lifecycle_state": lifecycle_state,
            "artifact_checksum": model.artifact_checksum,
            "label_mapping": model.label_mapping or {},
            "preprocessing_config": model.preprocessing_config or {},
            "training_provenance": provenance,
            "allowed_uses": provenance.get("allowed_uses") or [],
            "project_use": provenance.get("project_use"),
            "commercial_use_allowed": provenance.get("commercial_use_allowed", False),
            "requires_attribution": provenance.get("requires_attribution", True),
            "requires_sharealike": provenance.get("requires_sharealike", False),
            "readiness_score": model.readiness_score or 0.0,
            "runtime_available": (
                lifecycle_state == VisionModelLifecycleState.PRODUCTION.value
                and model.format == "sklearn_image_classifier"
                and artifact_valid
            ),
            "is_public": model.is_public,
            "created_by": model.created_by,
            "created_at": model.created_at.isoformat() if model.created_at else None,
        }

    async def list_models(
        self,
        db: AsyncSession,
        organization_id: int,
        *,
        crop: str | None = None,
        task: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        query = select(VisionModel).where(
            or_(VisionModel.organization_id == organization_id, VisionModel.is_public.is_(True))
        )
        query = query.order_by(VisionModel.created_at.desc(), VisionModel.id.desc())
        result = await db.execute(query)
        models = [self._serialize_model(model) for model in result.scalars().all()]

        # The current schema does not yet persist crop/task. Filters are retained
        # at the API boundary for forward compatibility and ignored until Phase 2.
        if status:
            models = [model for model in models if model["status"] == status]
        return models

    async def get_model(
        self,
        db: AsyncSession,
        organization_id: int,
        model_id: str,
    ) -> dict | None:
        if not str(model_id).isdigit():
            return None
        result = await db.execute(
            select(VisionModel).where(
                VisionModel.id == int(model_id),
                or_(
                    VisionModel.organization_id == organization_id, VisionModel.is_public.is_(True)
                ),
            )
        )
        model = result.scalar_one_or_none()
        return self._serialize_model(model) if model else None

    async def predict(
        self,
        db: AsyncSession,
        organization_id: int,
        *,
        model_id: str,
        image_data: str,
    ) -> dict:
        model = await self.get_model(db, organization_id, model_id)
        if not model:
            return {"error": "Model not found"}
        if model["status"] == "artifact_missing":
            return {
                "error": f"Model artifact is missing at {model['file_path']}",
                "status": "artifact_missing",
                "model": model,
            }
        return {
            "error": "No production inference runtime adapter is configured",
            "status": "runtime_unavailable",
            "model": model,
        }


vision_dataset_service = VisionDatasetService()
vision_model_service = VisionModelService()

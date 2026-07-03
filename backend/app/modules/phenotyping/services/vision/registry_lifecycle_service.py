"""Approved-model lifecycle and active-version resolution for Plant Vision."""

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vision import VisionModel, VisionModelLifecycleState
from app.modules.phenotyping.services.vision.artifact_utils import validate_artifact_checksum
from app.modules.phenotyping.services.vision.public_dataset_catalog import (
    PROJECT_USE_COMMERCIAL,
    PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
)


SERVABLE_FORMATS = {"sklearn_image_classifier"}


class VisionModelLifecycleService:
    """Controls model validation, promotion, rollback, and serving resolution."""

    async def _get_model_row(
        self,
        db: AsyncSession,
        organization_id: int,
        model_id: str,
    ) -> VisionModel | None:
        if not str(model_id).isdigit():
            return None
        result = await db.execute(
            select(VisionModel).where(
                VisionModel.id == int(model_id),
                VisionModel.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    def _artifact_is_valid(self, model: VisionModel) -> bool:
        if not model.file_path:
            return False
        artifact_dir = Path(model.file_path)
        if not artifact_dir.exists() or not artifact_dir.is_dir():
            return False
        return validate_artifact_checksum(artifact_dir, model.artifact_checksum)

    def _readiness_score(self, model: VisionModel) -> float:
        metrics = model.metrics or {}
        score = 0.0
        score += min(float(metrics.get("test_accuracy", 0.0)), 1.0) * 55
        score += min(float(metrics.get("val_accuracy", 0.0)), 1.0) * 25
        if model.label_mapping:
            score += 5
        if model.preprocessing_config:
            score += 5
        if model.training_provenance:
            score += 5
        if self._artifact_is_valid(model):
            score += 5
        return round(min(score, 100.0), 2)

    def _crop_task(self, model: VisionModel) -> tuple[str | None, str]:
        provenance = model.training_provenance or {}
        preprocessing = model.preprocessing_config or {}
        crop = provenance.get("crop") or preprocessing.get("crop")
        task = provenance.get("task") or preprocessing.get("task") or "classification"
        return crop, task

    def _runtime_available(self, model: VisionModel) -> bool:
        return (
            model.lifecycle_state == VisionModelLifecycleState.PRODUCTION.value
            and model.format in SERVABLE_FORMATS
            and self._artifact_is_valid(model)
        )

    def _model_allows_deployment(self, model: VisionModel, deployment_mode: str) -> bool:
        provenance = model.training_provenance or {}
        allowed_uses = provenance.get("allowed_uses") or []
        if deployment_mode not in allowed_uses:
            return False
        if deployment_mode == PROJECT_USE_COMMERCIAL and not provenance.get(
            "commercial_use_allowed", False
        ):
            return False
        return True

    def _serialize_model(self, model: VisionModel) -> dict:
        crop, task = self._crop_task(model)
        provenance = model.training_provenance or {}
        return {
            "id": str(model.id),
            "organization_id": model.organization_id,
            "name": model.name,
            "description": model.description,
            "version": model.version,
            "format": model.format,
            "file_path": model.file_path,
            "metrics": model.metrics or {},
            "size_bytes": model.size_bytes or 0,
            "lifecycle_state": model.lifecycle_state,
            "artifact_checksum": model.artifact_checksum,
            "label_mapping": model.label_mapping or {},
            "preprocessing_config": model.preprocessing_config or {},
            "training_provenance": model.training_provenance or {},
            "readiness_score": model.readiness_score or 0.0,
            "approved_by": model.approved_by,
            "approved_at": model.approved_at.isoformat() if model.approved_at else None,
            "archived_at": model.archived_at.isoformat() if model.archived_at else None,
            "crop": crop,
            "task": task,
            "allowed_uses": provenance.get("allowed_uses") or [],
            "project_use": provenance.get("project_use"),
            "commercial_use_allowed": provenance.get("commercial_use_allowed", False),
            "requires_attribution": provenance.get("requires_attribution", True),
            "requires_sharealike": provenance.get("requires_sharealike", False),
            "runtime_available": self._runtime_available(model),
            "created_by": model.created_by,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }

    async def get_model(
        self,
        db: AsyncSession,
        organization_id: int,
        model_id: str,
    ) -> dict | None:
        model = await self._get_model_row(db, organization_id, model_id)
        return self._serialize_model(model) if model else None

    async def validate_model(
        self,
        db: AsyncSession,
        organization_id: int,
        model_id: str,
        *,
        approved_by: str,
    ) -> dict:
        model = await self._get_model_row(db, organization_id, model_id)
        if not model:
            return {"error": "Model not found"}
        if model.lifecycle_state != VisionModelLifecycleState.CANDIDATE.value:
            return {"error": "Only candidate models can be validated"}
        if not self._artifact_is_valid(model):
            return {"error": "Model artifact integrity validation failed"}

        model.lifecycle_state = VisionModelLifecycleState.VALIDATED.value
        model.readiness_score = self._readiness_score(model)
        model.approved_by = approved_by
        model.approved_at = datetime.now(UTC)
        model.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(model)
        return self._serialize_model(model)

    async def _archive_active_models(
        self,
        db: AsyncSession,
        organization_id: int,
        *,
        crop: str | None,
        task: str,
        keep_model_id: int,
    ) -> None:
        result = await db.execute(
            select(VisionModel).where(
                VisionModel.organization_id == organization_id,
                VisionModel.lifecycle_state == VisionModelLifecycleState.PRODUCTION.value,
                VisionModel.id != keep_model_id,
            )
        )
        now = datetime.now(UTC)
        for model in result.scalars().all():
            model_crop, model_task = self._crop_task(model)
            if model_task == task and (crop is None or model_crop == crop):
                model.lifecycle_state = VisionModelLifecycleState.ARCHIVED.value
                model.archived_at = now
                model.updated_at = now

    async def promote_model(
        self,
        db: AsyncSession,
        organization_id: int,
        model_id: str,
        *,
        approved_by: str,
        deployment_mode: str = PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
    ) -> dict:
        model = await self._get_model_row(db, organization_id, model_id)
        if not model:
            return {"error": "Model not found"}
        if model.lifecycle_state != VisionModelLifecycleState.VALIDATED.value:
            return {"error": "Only validated models can be promoted to production"}
        if not self._artifact_is_valid(model):
            return {"error": "Model artifact integrity validation failed"}
        if not self._model_allows_deployment(model, deployment_mode):
            return {
                "error": "Model license policy does not allow this deployment mode",
                "deployment_mode": deployment_mode,
                "allowed_uses": (model.training_provenance or {}).get("allowed_uses") or [],
            }

        crop, task = self._crop_task(model)
        await self._archive_active_models(
            db,
            organization_id,
            crop=crop,
            task=task,
            keep_model_id=model.id,
        )
        now = datetime.now(UTC)
        model.lifecycle_state = VisionModelLifecycleState.PRODUCTION.value
        model.readiness_score = self._readiness_score(model)
        model.approved_by = approved_by
        model.approved_at = now
        model.archived_at = None
        model.updated_at = now
        await db.commit()
        await db.refresh(model)
        return self._serialize_model(model)

    async def rollback_to_model(
        self,
        db: AsyncSession,
        organization_id: int,
        model_id: str,
        *,
        approved_by: str,
        deployment_mode: str = PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
    ) -> dict:
        model = await self._get_model_row(db, organization_id, model_id)
        if not model:
            return {"error": "Model not found"}
        if model.lifecycle_state not in {
            VisionModelLifecycleState.VALIDATED.value,
            VisionModelLifecycleState.ARCHIVED.value,
        }:
            return {"error": "Rollback target must be validated or archived"}
        if not self._artifact_is_valid(model):
            return {"error": "Model artifact integrity validation failed"}
        if not self._model_allows_deployment(model, deployment_mode):
            return {
                "error": "Model license policy does not allow this deployment mode",
                "deployment_mode": deployment_mode,
                "allowed_uses": (model.training_provenance or {}).get("allowed_uses") or [],
            }

        crop, task = self._crop_task(model)
        await self._archive_active_models(
            db,
            organization_id,
            crop=crop,
            task=task,
            keep_model_id=model.id,
        )
        now = datetime.now(UTC)
        model.lifecycle_state = VisionModelLifecycleState.PRODUCTION.value
        model.readiness_score = self._readiness_score(model)
        model.approved_by = approved_by
        model.approved_at = now
        model.archived_at = None
        model.updated_at = now
        await db.commit()
        await db.refresh(model)
        return self._serialize_model(model)

    async def archive_model(
        self,
        db: AsyncSession,
        organization_id: int,
        model_id: str,
    ) -> dict:
        model = await self._get_model_row(db, organization_id, model_id)
        if not model:
            return {"error": "Model not found"}
        now = datetime.now(UTC)
        model.lifecycle_state = VisionModelLifecycleState.ARCHIVED.value
        model.archived_at = now
        model.updated_at = now
        await db.commit()
        await db.refresh(model)
        return self._serialize_model(model)

    async def get_active_production_model(
        self,
        db: AsyncSession,
        organization_id: int,
        *,
        crop: str | None = None,
        task: str = "classification",
    ) -> dict | None:
        result = await db.execute(
            select(VisionModel)
            .where(
                VisionModel.organization_id == organization_id,
                VisionModel.lifecycle_state == VisionModelLifecycleState.PRODUCTION.value,
            )
            .order_by(VisionModel.updated_at.desc(), VisionModel.id.desc())
        )
        for model in result.scalars().all():
            model_crop, model_task = self._crop_task(model)
            if model_task != task:
                continue
            if crop and model_crop and model_crop != crop:
                continue
            if self._runtime_available(model):
                return self._serialize_model(model)
        return None


vision_model_lifecycle_service = VisionModelLifecycleService()

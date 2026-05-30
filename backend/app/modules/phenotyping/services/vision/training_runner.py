"""Plant Vision training runner orchestration."""

import os
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vision import (
    VisionDataset,
    VisionDatasetImage,
    VisionModel,
    VisionModelLifecycleState,
    VisionTrainingJob,
    VisionTrainingLog,
    VisionTrainingStatus,
)
from app.modules.phenotyping.services.vision.artifact_utils import write_artifact_manifest
from app.modules.phenotyping.services.vision.baseline_training import (
    TrainingRecord,
    baseline_image_classifier_trainer,
)
from app.modules.phenotyping.services.vision.public_dataset_catalog import (
    PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
)
from app.modules.phenotyping.services.vision.training_service import vision_training_service


def _default_artifact_root() -> Path:
    return Path(os.getenv("BIJMANTRA_VISION_ARTIFACT_DIR", "var/vision-artifacts"))


class VisionTrainingRunner:
    """Runs persisted Plant Vision jobs through a concrete training backend."""

    async def _get_job(
        self,
        db: AsyncSession,
        organization_id: int,
        job_id: str,
    ) -> VisionTrainingJob | None:
        query = select(VisionTrainingJob).where(
            VisionTrainingJob.organization_id == organization_id
        )
        if str(job_id).isdigit():
            query = query.where(VisionTrainingJob.id == int(job_id))
        else:
            query = query.where(VisionTrainingJob.job_code == str(job_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _log(
        self,
        db: AsyncSession,
        organization_id: int,
        job: VisionTrainingJob,
        *,
        event_type: str,
        message: str,
        level: str = "info",
        status: VisionTrainingStatus | None = None,
        metrics: dict | None = None,
    ) -> None:
        db.add(
            VisionTrainingLog(
                organization_id=organization_id,
                job_id=job.id,
                event_type=event_type,
                level=level,
                message=message,
                status=status,
                metrics=metrics,
            )
        )

    async def _load_training_records(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: int,
    ) -> tuple[VisionDataset | None, list[TrainingRecord]]:
        dataset_result = await db.execute(
            select(VisionDataset).where(
                VisionDataset.id == dataset_id,
                VisionDataset.organization_id == organization_id,
            )
        )
        dataset = dataset_result.scalar_one_or_none()
        if not dataset:
            return None, []

        image_result = await db.execute(
            select(VisionDatasetImage).where(
                VisionDatasetImage.dataset_id == dataset_id,
                VisionDatasetImage.organization_id == organization_id,
            )
        )
        records: list[TrainingRecord] = []
        for image in image_result.scalars().all():
            annotation = image.annotation_data or {}
            label = annotation.get("label")
            metadata = image.metadata_json or {}
            raw_path = metadata.get("raw_path") or image.url
            if not label or not raw_path:
                continue
            path = Path(raw_path)
            if not path.exists():
                continue
            records.append(
                TrainingRecord(
                    image_path=path,
                    label=label,
                    split=image.split,
                    sha256=metadata.get("sha256", ""),
                    metadata=metadata,
                )
            )
        return dataset, records

    async def run_job(
        self,
        db: AsyncSession,
        organization_id: int,
        job_id: str,
        *,
        artifact_root: Path | None = None,
    ) -> dict:
        job = await self._get_job(db, organization_id, job_id)
        if not job:
            return {"error": "Job not found"}
        if job.status not in {VisionTrainingStatus.QUEUED, VisionTrainingStatus.PREPARING}:
            return {"error": f"Job cannot be run from status {job.status.value.lower()}"}

        dataset, records = await self._load_training_records(db, organization_id, job.dataset_id)
        if not dataset:
            return {"error": "Dataset not found"}
        if len(records) < 4:
            return {"error": "At least four governed image records are required for training"}

        started_at = datetime.now(UTC)
        job.status = VisionTrainingStatus.TRAINING
        job.started_at = started_at
        job.progress = 5
        await self._log(
            db,
            organization_id,
            job,
            event_type="runner_started",
            message="Baseline training runner started",
            status=VisionTrainingStatus.TRAINING,
        )
        await db.commit()

        config = {
            **(job.hyperparameters or {}),
            "base_model": job.base_model,
            "job_code": job.job_code,
            "dataset_id": str(dataset.id),
            "dataset_code": dataset.dataset_code,
            "crop": dataset.crop,
            "classes": dataset.classes or [],
        }
        allowed_uses = sorted(
            {
                allowed_use
                for record in records
                for allowed_use in record.metadata.get("allowed_uses", [])
            }
        )
        project_use_values = sorted(
            {
                record.metadata.get("project_use")
                for record in records
                if record.metadata.get("project_use")
            }
        )
        commercial_use_allowed = all(
            bool(record.metadata.get("commercial_use_allowed", False)) for record in records
        )
        requires_attribution = any(
            bool(record.metadata.get("requires_attribution", True)) for record in records
        )
        requires_sharealike = any(
            bool(record.metadata.get("requires_sharealike", False)) for record in records
        )
        terms_acceptance_records = sorted(
            {
                (
                    record.metadata.get("source_slug"),
                    record.metadata.get("terms_accepted_by"),
                    record.metadata.get("terms_acceptance_recorded_at"),
                )
                for record in records
                if record.metadata.get("terms_accepted_by")
            }
        )
        project_use = (
            str(config.get("project_use"))
            if config.get("project_use")
            else (
                project_use_values[0]
                if project_use_values
                else PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL
            )
        )
        config["project_use"] = project_use
        root = artifact_root or _default_artifact_root()
        artifact_dir = root / f"{job.job_code}-{started_at.strftime('%Y%m%d%H%M%S')}"

        result = baseline_image_classifier_trainer.train(
            records=records,
            artifact_dir=artifact_dir,
            config=config,
        )
        if "error" in result:
            failed = await vision_training_service.fail_job(
                db,
                organization_id,
                str(job.id),
                result["error"],
            )
            return failed or result

        manifest = write_artifact_manifest(artifact_dir)
        preprocessing_config = {
            **result["preprocessing_config"],
            "crop": dataset.crop,
            "task": "classification",
            "project_use": project_use,
        }
        training_provenance = {
            **result["training_provenance"],
            "dataset_id": str(dataset.id),
            "dataset_code": dataset.dataset_code,
            "dataset_classes": dataset.classes or [],
            "allowed_uses": allowed_uses,
            "project_use": project_use,
            "commercial_use_allowed": commercial_use_allowed,
            "requires_attribution": requires_attribution,
            "requires_sharealike": requires_sharealike,
            "terms_acceptance_records": [
                {
                    "source_slug": source_slug,
                    "accepted_by": accepted_by,
                    "recorded_at": recorded_at,
                }
                for source_slug, accepted_by, recorded_at in terms_acceptance_records
            ],
        }
        model = VisionModel(
            organization_id=organization_id,
            name=job.name,
            description=f"Baseline classifier trained from dataset {dataset.dataset_code}",
            version="0.1.0",
            format="sklearn_image_classifier",
            file_path=str(artifact_dir),
            metrics=result["metrics"],
            size_bytes=result["size_bytes"],
            lifecycle_state=VisionModelLifecycleState.CANDIDATE.value,
            artifact_checksum=manifest["artifact_checksum"],
            label_mapping=result["label_mapping"],
            preprocessing_config=preprocessing_config,
            training_provenance=training_provenance,
            readiness_score=0.0,
            is_public=False,
            created_by=job.created_by,
        )
        db.add(model)
        await db.flush()
        await self._log(
            db,
            organization_id,
            job,
            event_type="artifact_created",
            message="Baseline model artifacts created",
            status=VisionTrainingStatus.TRAINING,
            metrics={
                "artifact_checksum": manifest["artifact_checksum"],
                "artifact_dir": str(artifact_dir),
            },
        )
        await db.commit()
        await db.refresh(model)

        completed = await vision_training_service.complete_job(
            db,
            organization_id,
            str(job.id),
            str(model.id),
            {
                **result["metrics"],
                "artifact_checksum": manifest["artifact_checksum"],
                "artifact_dir": str(artifact_dir),
            },
        )
        if not completed:
            return {"error": "Training completed but job record could not be updated"}
        return completed


vision_training_runner = VisionTrainingRunner()

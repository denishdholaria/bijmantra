"""Vision training job service.

Phase 1 persists job intent and lifecycle state. Actual model training is a
separate runner concern; until a runner is configured, start requests fail
closed with a durable log entry instead of pretending to train.
"""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vision import (
    VisionDataset,
    VisionTrainingBackend,
    VisionTrainingJob,
    VisionTrainingLog,
    VisionTrainingStatus,
)


class TrainingStatus(StrEnum):
    QUEUED = "queued"
    PREPARING = "preparing"
    TRAINING = "training"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingBackend(StrEnum):
    BROWSER = "browser"
    SERVER = "server"
    CLOUD = "cloud"


def _job_code() -> str:
    return f"vision-training-{uuid4().hex[:12]}"


def _normalize_backend(
    value: str | TrainingBackend | VisionTrainingBackend,
) -> VisionTrainingBackend:
    raw = value.value if isinstance(value, StrEnum) else str(value)
    return VisionTrainingBackend(raw.upper())


def _normalize_status(value: str | TrainingStatus | VisionTrainingStatus) -> VisionTrainingStatus:
    raw = value.value if isinstance(value, StrEnum) else str(value)
    return VisionTrainingStatus(raw.upper())


def _api_status(value: VisionTrainingStatus) -> TrainingStatus:
    return TrainingStatus(value.value.lower())


def _api_backend(value: VisionTrainingBackend) -> TrainingBackend:
    return TrainingBackend(value.value.lower())


class VisionTrainingService:
    """Service for managing persisted training jobs."""

    default_hyperparameters = {
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 50,
        "optimizer": "adam",
        "augmentation": True,
        "early_stopping": True,
        "early_stopping_patience": 5,
    }

    async def _get_dataset(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str,
    ) -> VisionDataset | None:
        query = select(VisionDataset).where(VisionDataset.organization_id == organization_id)
        if str(dataset_id).isdigit():
            query = query.where(VisionDataset.id == int(dataset_id))
        else:
            query = query.where(VisionDataset.dataset_code == str(dataset_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

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

    def _serialize_job(self, job: VisionTrainingJob) -> dict:
        return {
            "id": str(job.id),
            "job_code": job.job_code,
            "organization_id": job.organization_id,
            "dataset_id": str(job.dataset_id),
            "name": job.name,
            "base_model": job.base_model,
            "backend": _api_backend(job.backend),
            "status": _api_status(job.status),
            "hyperparameters": job.hyperparameters or {},
            "metrics": job.metrics or {},
            "progress": job.progress,
            "current_epoch": job.current_epoch,
            "total_epochs": job.total_epochs,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "model_id": job.model_id,
            "created_by": job.created_by,
            "error_message": job.error_message,
        }

    def _serialize_log(self, log: VisionTrainingLog) -> dict:
        return {
            "id": str(log.id),
            "job_id": str(log.job_id),
            "event_type": log.event_type,
            "level": log.level,
            "message": log.message,
            "status": _api_status(log.status) if log.status else None,
            "epoch": log.epoch,
            "metrics": log.metrics or {},
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }

    async def _add_log(
        self,
        db: AsyncSession,
        organization_id: int,
        job: VisionTrainingJob,
        *,
        event_type: str,
        message: str,
        level: str = "info",
        status: VisionTrainingStatus | None = None,
        epoch: int | None = None,
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
                epoch=epoch,
                metrics=metrics,
            )
        )

    async def create_job(
        self,
        db: AsyncSession,
        organization_id: int,
        name: str,
        dataset_id: str,
        base_model: str,
        backend: TrainingBackend,
        hyperparameters: dict,
        created_by: str = "system",
    ) -> dict:
        dataset = await self._get_dataset(db, organization_id, dataset_id)
        if not dataset:
            return {"error": "Dataset not found"}

        merged_hyperparameters = dict(self.default_hyperparameters)
        merged_hyperparameters.update(hyperparameters or {})

        job = VisionTrainingJob(
            job_code=_job_code(),
            organization_id=organization_id,
            dataset_id=dataset.id,
            name=name.strip(),
            base_model=base_model,
            backend=_normalize_backend(backend),
            status=VisionTrainingStatus.QUEUED,
            hyperparameters=merged_hyperparameters,
            metrics={},
            progress=0,
            current_epoch=0,
            total_epochs=int(merged_hyperparameters["epochs"]),
            created_by=created_by,
        )
        db.add(job)
        await db.flush()
        await self._add_log(
            db,
            organization_id,
            job,
            event_type="created",
            message="Training job queued",
            status=VisionTrainingStatus.QUEUED,
        )
        await db.commit()
        await db.refresh(job)
        return self._serialize_job(job)

    async def get_job(
        self,
        db: AsyncSession,
        organization_id: int,
        job_id: str,
    ) -> dict | None:
        job = await self._get_job(db, organization_id, job_id)
        return self._serialize_job(job) if job else None

    async def list_jobs(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str | None = None,
        status: TrainingStatus | None = None,
        created_by: str | None = None,
    ) -> list[dict]:
        query = select(VisionTrainingJob).where(
            VisionTrainingJob.organization_id == organization_id
        )
        if dataset_id:
            dataset = await self._get_dataset(db, organization_id, dataset_id)
            if not dataset:
                return []
            query = query.where(VisionTrainingJob.dataset_id == dataset.id)
        if status:
            query = query.where(VisionTrainingJob.status == _normalize_status(status))
        if created_by:
            query = query.where(VisionTrainingJob.created_by == created_by)
        query = query.order_by(VisionTrainingJob.created_at.desc(), VisionTrainingJob.id.desc())
        result = await db.execute(query)
        return [self._serialize_job(job) for job in result.scalars().all()]

    async def start_job(
        self,
        db: AsyncSession,
        organization_id: int,
        job_id: str,
    ) -> dict | None:
        job = await self._get_job(db, organization_id, job_id)
        if not job:
            return None
        if job.status not in {VisionTrainingStatus.QUEUED, VisionTrainingStatus.PREPARING}:
            return {"error": f"Job cannot be started from status {_api_status(job.status)}"}

        job.status = VisionTrainingStatus.FAILED
        job.started_at = datetime.now(UTC)
        job.completed_at = datetime.now(UTC)
        job.error_message = "No training runner is configured for Plant Vision"
        job.updated_at = datetime.now(UTC)
        await self._add_log(
            db,
            organization_id,
            job,
            event_type="runner_unavailable",
            level="error",
            message=job.error_message,
            status=VisionTrainingStatus.FAILED,
        )
        await db.commit()
        await db.refresh(job)
        return self._serialize_job(job)

    async def update_progress(
        self,
        db: AsyncSession,
        organization_id: int,
        job_id: str,
        epoch: int,
        metrics: dict,
    ) -> dict | None:
        job = await self._get_job(db, organization_id, job_id)
        if not job:
            return None
        job.current_epoch = epoch
        job.metrics = metrics
        job.progress = round(min(100, max(0, (epoch / max(job.total_epochs, 1)) * 100)), 2)
        job.status = VisionTrainingStatus.TRAINING
        job.updated_at = datetime.now(UTC)
        await self._add_log(
            db,
            organization_id,
            job,
            event_type="progress",
            message=f"Epoch {epoch} completed",
            status=VisionTrainingStatus.TRAINING,
            epoch=epoch,
            metrics=metrics,
        )
        await db.commit()
        await db.refresh(job)
        return self._serialize_job(job)

    async def complete_job(
        self,
        db: AsyncSession,
        organization_id: int,
        job_id: str,
        model_id: str,
        final_metrics: dict,
    ) -> dict | None:
        job = await self._get_job(db, organization_id, job_id)
        if not job:
            return None
        job.status = VisionTrainingStatus.COMPLETED
        job.model_id = model_id
        job.metrics = final_metrics
        job.progress = 100
        job.completed_at = datetime.now(UTC)
        job.updated_at = datetime.now(UTC)
        await self._add_log(
            db,
            organization_id,
            job,
            event_type="completed",
            message="Training job completed",
            status=VisionTrainingStatus.COMPLETED,
            metrics=final_metrics,
        )
        await db.commit()
        await db.refresh(job)
        return self._serialize_job(job)

    async def fail_job(
        self,
        db: AsyncSession,
        organization_id: int,
        job_id: str,
        error_message: str,
    ) -> dict | None:
        job = await self._get_job(db, organization_id, job_id)
        if not job:
            return None
        job.status = VisionTrainingStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.now(UTC)
        job.updated_at = datetime.now(UTC)
        await self._add_log(
            db,
            organization_id,
            job,
            event_type="failed",
            level="error",
            message=error_message,
            status=VisionTrainingStatus.FAILED,
        )
        await db.commit()
        await db.refresh(job)
        return self._serialize_job(job)

    async def cancel_job(
        self,
        db: AsyncSession,
        organization_id: int,
        job_id: str,
    ) -> dict | None:
        job = await self._get_job(db, organization_id, job_id)
        if not job:
            return None
        if job.status in {VisionTrainingStatus.COMPLETED, VisionTrainingStatus.FAILED}:
            return {"error": f"Job cannot be cancelled from status {_api_status(job.status)}"}
        job.status = VisionTrainingStatus.CANCELLED
        job.completed_at = datetime.now(UTC)
        job.updated_at = datetime.now(UTC)
        await self._add_log(
            db,
            organization_id,
            job,
            event_type="cancelled",
            message="Training job cancelled",
            status=VisionTrainingStatus.CANCELLED,
        )
        await db.commit()
        await db.refresh(job)
        return self._serialize_job(job)

    async def get_logs(
        self,
        db: AsyncSession,
        organization_id: int,
        job_id: str,
        last_n: int | None = None,
    ) -> list[dict]:
        job = await self._get_job(db, organization_id, job_id)
        if not job:
            return []
        query = select(VisionTrainingLog).where(
            VisionTrainingLog.organization_id == organization_id,
            VisionTrainingLog.job_id == job.id,
        )
        query = query.order_by(VisionTrainingLog.created_at.desc(), VisionTrainingLog.id.desc())
        if last_n:
            query = query.limit(last_n)
        result = await db.execute(query)
        logs = [self._serialize_log(log) for log in result.scalars().all()]
        return list(reversed(logs))

    async def compare_jobs(
        self,
        db: AsyncSession,
        organization_id: int,
        job_ids: list[str],
    ) -> dict:
        if len(job_ids) < 2:
            return {"error": "Need at least 2 jobs to compare"}

        jobs = []
        for job_id in job_ids:
            job = await self.get_job(db, organization_id, job_id)
            if job:
                jobs.append(job)

        best = None
        for job in jobs:
            accuracy = job["metrics"].get("val_accuracy")
            if accuracy is not None and (
                best is None or accuracy > best["metrics"]["val_accuracy"]
            ):
                best = job

        return {
            "jobs": jobs,
            "best_accuracy": best["metrics"]["val_accuracy"] if best else None,
            "best_job_id": best["id"] if best else None,
            "message": None if jobs else "No training jobs available for comparison",
        }


class HyperparameterService:
    """Recommendation helper for model training configuration."""

    async def get_recommended_config(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_size: int,
        task_type: str,
    ) -> dict:
        if dataset_size < 500:
            return {
                "learning_rate": 0.001,
                "batch_size": 8,
                "epochs": 20,
                "optimizer": "adam",
                "augmentation": True,
                "early_stopping": True,
                "early_stopping_patience": 5,
                "recommendation": "Small dataset - using aggressive augmentation and early stopping",
            }
        if dataset_size < 2000:
            return {
                "learning_rate": 0.001,
                "batch_size": 16,
                "epochs": 30,
                "optimizer": "adam",
                "augmentation": True,
                "early_stopping": True,
                "early_stopping_patience": 7,
                "recommendation": "Medium dataset - balanced configuration",
            }
        return {
            "learning_rate": 0.0005,
            "batch_size": 32,
            "epochs": 50,
            "optimizer": "adamw",
            "augmentation": True,
            "early_stopping": True,
            "early_stopping_patience": 10,
            "recommendation": "Large dataset - can train longer with lower learning rate",
        }

    async def create_grid_search(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str,
        param_grid: dict,
    ) -> dict:
        total = 1
        for values in param_grid.values():
            total *= len(values)
        return {
            "id": None,
            "dataset_id": dataset_id,
            "param_grid": param_grid,
            "total_combinations": total,
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat() + "Z",
            "message": "Grid-search runner is not configured",
        }

    def get_augmentation_options(self) -> list[dict]:
        return [
            {"name": "horizontal_flip", "description": "Flip image horizontally", "default": True},
            {"name": "vertical_flip", "description": "Flip image vertically", "default": False},
            {
                "name": "rotation",
                "description": "Random rotation (-15 to +15 degrees)",
                "default": True,
            },
            {"name": "zoom", "description": "Random zoom (0.9x to 1.1x)", "default": True},
            {"name": "brightness", "description": "Random brightness adjustment", "default": True},
            {"name": "contrast", "description": "Random contrast adjustment", "default": True},
            {"name": "saturation", "description": "Random saturation adjustment", "default": False},
            {"name": "noise", "description": "Add random noise", "default": False},
            {"name": "blur", "description": "Random Gaussian blur", "default": False},
            {"name": "cutout", "description": "Random cutout/erasing", "default": False},
        ]


vision_training_service = VisionTrainingService()
hyperparameter_service = HyperparameterService()

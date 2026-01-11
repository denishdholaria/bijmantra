"""
Vision Training Service - Phase 3: Training Infrastructure
Server-side training, hyperparameter tuning, model comparison
"""

import uuid
import random
from datetime import datetime, UTC, timedelta
from typing import Optional
from enum import Enum


class TrainingStatus(str, Enum):
    QUEUED = "queued"
    PREPARING = "preparing"
    TRAINING = "training"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingBackend(str, Enum):
    BROWSER = "browser"  # TensorFlow.js
    SERVER = "server"    # PyTorch/TensorFlow
    CLOUD = "cloud"      # AWS/GCP


# In-memory storage
TRAINING_JOBS: dict = {}
TRAINING_LOGS: dict = {}
HYPERPARAMETER_CONFIGS: dict = {}


def _init_demo_data():
    """Initialize demo training data"""
    if TRAINING_JOBS:
        return
    
    # Demo training jobs
    demo_jobs = [
        {
            "id": "job-rice-blast-001",
            "name": "Rice Blast Classifier v3",
            "dataset_id": "ds-rice-blast-001",
            "base_model": "mobilenetv2",
            "backend": TrainingBackend.SERVER,
            "status": TrainingStatus.COMPLETED,
            "hyperparameters": {
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 50,
                "optimizer": "adam",
                "augmentation": True,
            },
            "metrics": {
                "train_loss": 0.12,
                "val_loss": 0.18,
                "train_accuracy": 0.96,
                "val_accuracy": 0.94,
                "best_epoch": 42,
            },
            "progress": 100,
            "current_epoch": 50,
            "total_epochs": 50,
            "created_at": "2025-11-18T10:00:00Z",
            "started_at": "2025-11-18T10:05:00Z",
            "completed_at": "2025-11-18T14:30:00Z",
            "model_id": "model-rice-blast-v3",
            "created_by": "demo_user",
        },
        {
            "id": "job-wheat-rust-001",
            "name": "Wheat Rust Detector v2",
            "dataset_id": "ds-wheat-rust-001",
            "base_model": "efficientnetb0",
            "backend": TrainingBackend.SERVER,
            "status": TrainingStatus.COMPLETED,
            "hyperparameters": {
                "learning_rate": 0.0005,
                "batch_size": 16,
                "epochs": 30,
                "optimizer": "adamw",
                "augmentation": True,
            },
            "metrics": {
                "train_loss": 0.15,
                "val_loss": 0.22,
                "train_accuracy": 0.93,
                "val_accuracy": 0.91,
                "best_epoch": 28,
            },
            "progress": 100,
            "current_epoch": 30,
            "total_epochs": 30,
            "created_at": "2025-10-22T09:00:00Z",
            "started_at": "2025-10-22T09:10:00Z",
            "completed_at": "2025-10-22T15:45:00Z",
            "model_id": "model-wheat-rust-v2",
            "created_by": "demo_user",
        },
        {
            "id": "job-maize-growth-001",
            "name": "Maize Growth Stage v1",
            "dataset_id": "ds-maize-growth-001",
            "base_model": "mobilenetv2",
            "backend": TrainingBackend.BROWSER,
            "status": TrainingStatus.TRAINING,
            "hyperparameters": {
                "learning_rate": 0.001,
                "batch_size": 8,
                "epochs": 20,
                "optimizer": "adam",
                "augmentation": False,
            },
            "metrics": {
                "train_loss": 0.35,
                "val_loss": 0.42,
                "train_accuracy": 0.82,
                "val_accuracy": 0.78,
                "best_epoch": 12,
            },
            "progress": 65,
            "current_epoch": 13,
            "total_epochs": 20,
            "created_at": "2025-12-11T08:00:00Z",
            "started_at": "2025-12-11T08:02:00Z",
            "completed_at": None,
            "model_id": None,
            "created_by": "demo_user",
        },
    ]
    
    for job in demo_jobs:
        TRAINING_JOBS[job["id"]] = job
        # Generate demo logs
        TRAINING_LOGS[job["id"]] = _generate_demo_logs(job)


def _generate_demo_logs(job: dict) -> list[dict]:
    """Generate demo training logs"""
    logs = []
    epochs = job.get("current_epoch", 10)
    
    for epoch in range(1, epochs + 1):
        train_loss = max(0.1, 1.0 - (epoch * 0.05) + random.uniform(-0.05, 0.05))
        val_loss = train_loss + random.uniform(0.02, 0.1)
        train_acc = min(0.99, 0.5 + (epoch * 0.03) + random.uniform(-0.02, 0.02))
        val_acc = train_acc - random.uniform(0.01, 0.05)
        
        logs.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "val_loss": round(val_loss, 4),
            "train_accuracy": round(train_acc, 4),
            "val_accuracy": round(val_acc, 4),
            "learning_rate": job["hyperparameters"]["learning_rate"],
            "timestamp": (datetime.fromisoformat(job["started_at"].replace("Z", "")) + timedelta(minutes=epoch * 5)).isoformat() + "Z",
        })
    
    return logs


_init_demo_data()


class VisionTrainingService:
    """Service for managing training jobs"""
    
    def create_job(
        self,
        name: str,
        dataset_id: str,
        base_model: str,
        backend: TrainingBackend,
        hyperparameters: dict,
        created_by: str = "system",
    ) -> dict:
        """Create a new training job"""
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        
        # Default hyperparameters
        default_hp = {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 50,
            "optimizer": "adam",
            "augmentation": True,
            "early_stopping": True,
            "early_stopping_patience": 5,
        }
        default_hp.update(hyperparameters)
        
        job = {
            "id": job_id,
            "name": name,
            "dataset_id": dataset_id,
            "base_model": base_model,
            "backend": backend,
            "status": TrainingStatus.QUEUED,
            "hyperparameters": default_hp,
            "metrics": {},
            "progress": 0,
            "current_epoch": 0,
            "total_epochs": default_hp["epochs"],
            "created_at": datetime.now(UTC).isoformat() + "Z",
            "started_at": None,
            "completed_at": None,
            "model_id": None,
            "created_by": created_by,
            "error_message": None,
        }
        
        TRAINING_JOBS[job_id] = job
        TRAINING_LOGS[job_id] = []
        
        return job
    
    def get_job(self, job_id: str) -> Optional[dict]:
        """Get training job by ID"""
        return TRAINING_JOBS.get(job_id)
    
    def list_jobs(
        self,
        dataset_id: Optional[str] = None,
        status: Optional[TrainingStatus] = None,
        created_by: Optional[str] = None,
    ) -> list[dict]:
        """List training jobs"""
        jobs = list(TRAINING_JOBS.values())
        
        if dataset_id:
            jobs = [j for j in jobs if j["dataset_id"] == dataset_id]
        if status:
            jobs = [j for j in jobs if j["status"] == status]
        if created_by:
            jobs = [j for j in jobs if j.get("created_by") == created_by]
        
        return sorted(jobs, key=lambda x: x["created_at"], reverse=True)
    
    def start_job(self, job_id: str) -> Optional[dict]:
        """Start a training job"""
        if job_id not in TRAINING_JOBS:
            return None
        
        job = TRAINING_JOBS[job_id]
        if job["status"] != TrainingStatus.QUEUED:
            return {"error": f"Job is {job['status']}, cannot start"}
        
        job["status"] = TrainingStatus.PREPARING
        job["started_at"] = datetime.now(UTC).isoformat() + "Z"
        
        # Simulate immediate transition to training
        job["status"] = TrainingStatus.TRAINING
        
        return job
    
    def update_progress(
        self,
        job_id: str,
        epoch: int,
        metrics: dict,
    ) -> Optional[dict]:
        """Update training progress"""
        if job_id not in TRAINING_JOBS:
            return None
        
        job = TRAINING_JOBS[job_id]
        job["current_epoch"] = epoch
        job["progress"] = round((epoch / job["total_epochs"]) * 100, 1)
        job["metrics"] = metrics
        
        # Add to logs
        log_entry = {
            "epoch": epoch,
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            **metrics,
        }
        TRAINING_LOGS[job_id].append(log_entry)
        
        # Check if completed
        if epoch >= job["total_epochs"]:
            job["status"] = TrainingStatus.VALIDATING
        
        return job
    
    def complete_job(self, job_id: str, model_id: str, final_metrics: dict) -> Optional[dict]:
        """Mark job as completed"""
        if job_id not in TRAINING_JOBS:
            return None
        
        job = TRAINING_JOBS[job_id]
        job["status"] = TrainingStatus.COMPLETED
        job["completed_at"] = datetime.now(UTC).isoformat() + "Z"
        job["model_id"] = model_id
        job["metrics"] = final_metrics
        job["progress"] = 100
        
        return job
    
    def fail_job(self, job_id: str, error_message: str) -> Optional[dict]:
        """Mark job as failed"""
        if job_id not in TRAINING_JOBS:
            return None
        
        job = TRAINING_JOBS[job_id]
        job["status"] = TrainingStatus.FAILED
        job["error_message"] = error_message
        job["completed_at"] = datetime.now(UTC).isoformat() + "Z"
        
        return job
    
    def cancel_job(self, job_id: str) -> Optional[dict]:
        """Cancel a training job"""
        if job_id not in TRAINING_JOBS:
            return None
        
        job = TRAINING_JOBS[job_id]
        if job["status"] in [TrainingStatus.COMPLETED, TrainingStatus.FAILED]:
            return {"error": "Cannot cancel completed or failed job"}
        
        job["status"] = TrainingStatus.CANCELLED
        job["completed_at"] = datetime.now(UTC).isoformat() + "Z"
        
        return job
    
    def get_logs(self, job_id: str, last_n: Optional[int] = None) -> list[dict]:
        """Get training logs for a job"""
        logs = TRAINING_LOGS.get(job_id, [])
        if last_n:
            return logs[-last_n:]
        return logs
    
    def compare_jobs(self, job_ids: list[str]) -> dict:
        """Compare multiple training jobs"""
        jobs = [TRAINING_JOBS.get(jid) for jid in job_ids if jid in TRAINING_JOBS]
        
        if len(jobs) < 2:
            return {"error": "Need at least 2 jobs to compare"}
        
        comparison = {
            "jobs": [],
            "best_accuracy": None,
            "best_job_id": None,
        }
        
        best_acc = 0
        for job in jobs:
            val_acc = job.get("metrics", {}).get("val_accuracy", 0)
            job_summary = {
                "id": job["id"],
                "name": job["name"],
                "base_model": job["base_model"],
                "status": job["status"],
                "val_accuracy": val_acc,
                "val_loss": job.get("metrics", {}).get("val_loss"),
                "epochs": job["current_epoch"],
                "hyperparameters": job["hyperparameters"],
            }
            comparison["jobs"].append(job_summary)
            
            if val_acc > best_acc:
                best_acc = val_acc
                comparison["best_accuracy"] = val_acc
                comparison["best_job_id"] = job["id"]
        
        return comparison


class HyperparameterService:
    """Service for hyperparameter tuning"""
    
    def get_recommended_config(self, dataset_size: int, task_type: str) -> dict:
        """Get recommended hyperparameters based on dataset size"""
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
        elif dataset_size < 2000:
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
        else:
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
    
    def create_grid_search(
        self,
        dataset_id: str,
        param_grid: dict,
    ) -> dict:
        """Create a grid search configuration"""
        config_id = f"grid-{uuid.uuid4().hex[:8]}"
        
        # Calculate total combinations
        total = 1
        for values in param_grid.values():
            total *= len(values)
        
        config = {
            "id": config_id,
            "dataset_id": dataset_id,
            "param_grid": param_grid,
            "total_combinations": total,
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat() + "Z",
        }
        
        HYPERPARAMETER_CONFIGS[config_id] = config
        return config
    
    def get_augmentation_options(self) -> list[dict]:
        """Get available augmentation options"""
        return [
            {"name": "horizontal_flip", "description": "Flip image horizontally", "default": True},
            {"name": "vertical_flip", "description": "Flip image vertically", "default": False},
            {"name": "rotation", "description": "Random rotation (-15° to +15°)", "default": True},
            {"name": "zoom", "description": "Random zoom (0.9x to 1.1x)", "default": True},
            {"name": "brightness", "description": "Random brightness adjustment", "default": True},
            {"name": "contrast", "description": "Random contrast adjustment", "default": True},
            {"name": "saturation", "description": "Random saturation adjustment", "default": False},
            {"name": "noise", "description": "Add random noise", "default": False},
            {"name": "blur", "description": "Random Gaussian blur", "default": False},
            {"name": "cutout", "description": "Random cutout/erasing", "default": False},
        ]


# Service instances
vision_training_service = VisionTrainingService()
hyperparameter_service = HyperparameterService()

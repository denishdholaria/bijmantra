"""
Vision Deployment Service - Phase 4: Deployment & Registry
Multi-target export, model versioning, community registry
"""

import uuid
from datetime import datetime, UTC
from typing import Optional
from enum import Enum


class ExportFormat(str, Enum):
    TFJS = "tfjs"           # TensorFlow.js (browser)
    TFLITE = "tflite"       # TensorFlow Lite (mobile)
    ONNX = "onnx"           # ONNX (cross-platform)
    TORCHSCRIPT = "torchscript"  # PyTorch
    SAVEDMODEL = "savedmodel"    # TensorFlow SavedModel


class DeploymentTarget(str, Enum):
    BROWSER = "browser"
    MOBILE = "mobile"
    EDGE = "edge"
    SERVER = "server"
    API = "api"


class ModelVisibility(str, Enum):
    PRIVATE = "private"
    ORGANIZATION = "organization"
    PUBLIC = "public"


# In-memory storage
DEPLOYMENTS: dict = {}
REGISTRY_MODELS: dict = {}
MODEL_VERSIONS: dict = {}


def _init_demo_data():
    """Initialize demo deployment data"""
    if REGISTRY_MODELS:
        return
    
    # Demo registry models (community shared)
    demo_registry = [
        {
            "id": "reg-rice-blast-v3",
            "model_id": "model-rice-blast-v3",
            "name": "RiceBlast-v3",
            "description": "High-accuracy rice blast disease detection model trained on 2800+ images",
            "author": "Bijmantra Research",
            "crop": "rice",
            "task": "classification",
            "classes": ["healthy", "mild", "moderate", "severe"],
            "accuracy": 0.94,
            "size_mb": 12.4,
            "visibility": ModelVisibility.PUBLIC,
            "downloads": 156,
            "likes": 42,
            "tags": ["disease", "rice", "blast", "classification"],
            "published_at": "2025-11-22T10:00:00Z",
            "updated_at": "2025-12-01T14:30:00Z",
            "version": "3.0.0",
            "license": "CC-BY-4.0",
            "paper_url": None,
            "dataset_size": 2847,
        },
        {
            "id": "reg-wheat-rust-v2",
            "model_id": "model-wheat-rust-v2",
            "name": "WheatRust-v2",
            "description": "Multi-class wheat rust detection (stem, leaf, stripe rust)",
            "author": "Bijmantra Research",
            "crop": "wheat",
            "task": "classification",
            "classes": ["healthy", "stem_rust", "leaf_rust", "stripe_rust"],
            "accuracy": 0.91,
            "size_mb": 15.2,
            "visibility": ModelVisibility.PUBLIC,
            "downloads": 89,
            "likes": 28,
            "tags": ["disease", "wheat", "rust", "classification"],
            "published_at": "2025-10-28T09:00:00Z",
            "updated_at": "2025-11-15T11:20:00Z",
            "version": "2.0.0",
            "license": "CC-BY-4.0",
            "paper_url": None,
            "dataset_size": 1523,
        },
        {
            "id": "reg-plantvillage-base",
            "model_id": "model-plantvillage-base",
            "name": "PlantVillage-Base",
            "description": "General plant disease detection pre-trained on PlantVillage dataset",
            "author": "Community",
            "crop": "multi",
            "task": "classification",
            "classes": ["healthy", "diseased"],
            "accuracy": 0.87,
            "size_mb": 22.5,
            "visibility": ModelVisibility.PUBLIC,
            "downloads": 1245,
            "likes": 312,
            "tags": ["pretrained", "transfer-learning", "multi-crop"],
            "published_at": "2025-06-15T12:00:00Z",
            "updated_at": "2025-09-20T08:45:00Z",
            "version": "1.2.0",
            "license": "MIT",
            "paper_url": "https://arxiv.org/abs/example",
            "dataset_size": 54000,
        },
    ]
    
    for model in demo_registry:
        REGISTRY_MODELS[model["id"]] = model
    
    # Demo deployments
    demo_deployments = [
        {
            "id": "deploy-001",
            "model_id": "model-rice-blast-v3",
            "target": DeploymentTarget.BROWSER,
            "format": ExportFormat.TFJS,
            "status": "active",
            "endpoint_url": "/models/rice-blast-v3/model.json",
            "created_at": "2025-11-25T10:00:00Z",
            "requests_count": 1523,
            "avg_latency_ms": 45,
        },
        {
            "id": "deploy-002",
            "model_id": "model-rice-blast-v3",
            "target": DeploymentTarget.MOBILE,
            "format": ExportFormat.TFLITE,
            "status": "active",
            "endpoint_url": "/models/rice-blast-v3/model.tflite",
            "created_at": "2025-11-26T14:30:00Z",
            "requests_count": 892,
            "avg_latency_ms": 28,
        },
        {
            "id": "deploy-003",
            "model_id": "model-wheat-rust-v2",
            "target": DeploymentTarget.API,
            "format": ExportFormat.SAVEDMODEL,
            "status": "active",
            "endpoint_url": "/api/v2/vision/models/wheat-rust-v2/predict",
            "created_at": "2025-11-01T09:00:00Z",
            "requests_count": 3421,
            "avg_latency_ms": 12,
        },
    ]
    
    for deploy in demo_deployments:
        DEPLOYMENTS[deploy["id"]] = deploy


_init_demo_data()


class VisionDeploymentService:
    """Service for model deployment"""
    
    def export_model(
        self,
        model_id: str,
        format: ExportFormat,
        optimize: bool = True,
        quantize: bool = False,
    ) -> dict:
        """Export model to specified format"""
        export_id = f"export-{uuid.uuid4().hex[:8]}"
        
        # Simulated export sizes
        size_multipliers = {
            ExportFormat.TFJS: 1.0,
            ExportFormat.TFLITE: 0.3,
            ExportFormat.ONNX: 0.9,
            ExportFormat.TORCHSCRIPT: 1.1,
            ExportFormat.SAVEDMODEL: 1.5,
        }
        
        base_size = 12.0  # MB
        size = base_size * size_multipliers.get(format, 1.0)
        if quantize:
            size *= 0.25  # INT8 quantization
        
        return {
            "export_id": export_id,
            "model_id": model_id,
            "format": format,
            "optimized": optimize,
            "quantized": quantize,
            "size_mb": round(size, 2),
            "download_url": f"/exports/{export_id}/model.{format.value}",
            "created_at": datetime.now(UTC).isoformat() + "Z",
            "expires_at": (datetime.now(UTC).replace(hour=23, minute=59)).isoformat() + "Z",
        }
    
    def deploy_model(
        self,
        model_id: str,
        target: DeploymentTarget,
        format: ExportFormat,
    ) -> dict:
        """Deploy model to a target"""
        deploy_id = f"deploy-{uuid.uuid4().hex[:8]}"
        
        # Generate endpoint URL based on target
        if target == DeploymentTarget.API:
            endpoint = f"/api/v2/vision/models/{model_id}/predict"
        elif target == DeploymentTarget.BROWSER:
            endpoint = f"/models/{model_id}/model.json"
        else:
            endpoint = f"/models/{model_id}/model.{format.value}"
        
        deployment = {
            "id": deploy_id,
            "model_id": model_id,
            "target": target,
            "format": format,
            "status": "active",
            "endpoint_url": endpoint,
            "created_at": datetime.now(UTC).isoformat() + "Z",
            "requests_count": 0,
            "avg_latency_ms": 0,
        }
        
        DEPLOYMENTS[deploy_id] = deployment
        return deployment
    
    def get_deployment(self, deploy_id: str) -> Optional[dict]:
        """Get deployment by ID"""
        return DEPLOYMENTS.get(deploy_id)
    
    def list_deployments(self, model_id: Optional[str] = None) -> list[dict]:
        """List deployments"""
        deployments = list(DEPLOYMENTS.values())
        if model_id:
            deployments = [d for d in deployments if d["model_id"] == model_id]
        return sorted(deployments, key=lambda x: x["created_at"], reverse=True)
    
    def undeploy(self, deploy_id: str) -> bool:
        """Remove a deployment"""
        if deploy_id not in DEPLOYMENTS:
            return False
        
        DEPLOYMENTS[deploy_id]["status"] = "inactive"
        return True
    
    def get_deployment_stats(self, deploy_id: str) -> Optional[dict]:
        """Get deployment statistics"""
        deployment = DEPLOYMENTS.get(deploy_id)
        if not deployment:
            return None
        
        return {
            "deployment_id": deploy_id,
            "model_id": deployment["model_id"],
            "target": deployment["target"],
            "status": deployment["status"],
            "total_requests": deployment["requests_count"],
            "avg_latency_ms": deployment["avg_latency_ms"],
            "uptime_percent": 99.9,
            "error_rate": 0.1,
        }


class ModelRegistryService:
    """Service for community model registry"""
    
    def publish_model(
        self,
        model_id: str,
        name: str,
        description: str,
        author: str,
        crop: str,
        task: str,
        classes: list[str],
        accuracy: float,
        size_mb: float,
        tags: list[str],
        visibility: ModelVisibility = ModelVisibility.PUBLIC,
        license: str = "CC-BY-4.0",
    ) -> dict:
        """Publish a model to the registry"""
        registry_id = f"reg-{uuid.uuid4().hex[:8]}"
        
        entry = {
            "id": registry_id,
            "model_id": model_id,
            "name": name,
            "description": description,
            "author": author,
            "crop": crop,
            "task": task,
            "classes": classes,
            "accuracy": accuracy,
            "size_mb": size_mb,
            "visibility": visibility,
            "downloads": 0,
            "likes": 0,
            "tags": tags,
            "published_at": datetime.now(UTC).isoformat() + "Z",
            "updated_at": datetime.now(UTC).isoformat() + "Z",
            "version": "1.0.0",
            "license": license,
            "paper_url": None,
            "dataset_size": None,
        }
        
        REGISTRY_MODELS[registry_id] = entry
        return entry
    
    def get_registry_model(self, registry_id: str) -> Optional[dict]:
        """Get model from registry"""
        return REGISTRY_MODELS.get(registry_id)
    
    def search_registry(
        self,
        query: Optional[str] = None,
        crop: Optional[str] = None,
        task: Optional[str] = None,
        min_accuracy: Optional[float] = None,
        sort_by: str = "downloads",
    ) -> list[dict]:
        """Search the model registry"""
        models = [m for m in REGISTRY_MODELS.values() if m["visibility"] == ModelVisibility.PUBLIC]
        
        if query:
            query_lower = query.lower()
            models = [m for m in models if 
                query_lower in m["name"].lower() or 
                query_lower in m["description"].lower() or
                any(query_lower in tag for tag in m["tags"])]
        
        if crop:
            models = [m for m in models if m["crop"] == crop or m["crop"] == "multi"]
        
        if task:
            models = [m for m in models if m["task"] == task]
        
        if min_accuracy:
            models = [m for m in models if m["accuracy"] >= min_accuracy]
        
        # Sort
        if sort_by == "downloads":
            models.sort(key=lambda x: x["downloads"], reverse=True)
        elif sort_by == "accuracy":
            models.sort(key=lambda x: x["accuracy"], reverse=True)
        elif sort_by == "recent":
            models.sort(key=lambda x: x["published_at"], reverse=True)
        elif sort_by == "likes":
            models.sort(key=lambda x: x["likes"], reverse=True)
        
        return models
    
    def download_model(self, registry_id: str) -> Optional[dict]:
        """Record a model download"""
        if registry_id not in REGISTRY_MODELS:
            return None
        
        REGISTRY_MODELS[registry_id]["downloads"] += 1
        
        return {
            "registry_id": registry_id,
            "model_id": REGISTRY_MODELS[registry_id]["model_id"],
            "download_url": f"/registry/{registry_id}/download",
            "size_mb": REGISTRY_MODELS[registry_id]["size_mb"],
        }
    
    def like_model(self, registry_id: str) -> Optional[dict]:
        """Like a model"""
        if registry_id not in REGISTRY_MODELS:
            return None
        
        REGISTRY_MODELS[registry_id]["likes"] += 1
        return {"likes": REGISTRY_MODELS[registry_id]["likes"]}
    
    def get_featured_models(self, limit: int = 5) -> list[dict]:
        """Get featured/popular models"""
        models = [m for m in REGISTRY_MODELS.values() if m["visibility"] == ModelVisibility.PUBLIC]
        models.sort(key=lambda x: x["downloads"] + x["likes"] * 2, reverse=True)
        return models[:limit]


class ModelVersionService:
    """Service for model versioning"""
    
    def create_version(
        self,
        model_id: str,
        version: str,
        changes: str,
        metrics: dict,
    ) -> dict:
        """Create a new model version"""
        version_id = f"ver-{uuid.uuid4().hex[:8]}"
        
        if model_id not in MODEL_VERSIONS:
            MODEL_VERSIONS[model_id] = []
        
        version_entry = {
            "id": version_id,
            "model_id": model_id,
            "version": version,
            "changes": changes,
            "metrics": metrics,
            "created_at": datetime.now(UTC).isoformat() + "Z",
            "is_latest": True,
        }
        
        # Mark previous versions as not latest
        for v in MODEL_VERSIONS[model_id]:
            v["is_latest"] = False
        
        MODEL_VERSIONS[model_id].append(version_entry)
        return version_entry
    
    def list_versions(self, model_id: str) -> list[dict]:
        """List all versions of a model"""
        return MODEL_VERSIONS.get(model_id, [])
    
    def get_latest_version(self, model_id: str) -> Optional[dict]:
        """Get the latest version of a model"""
        versions = MODEL_VERSIONS.get(model_id, [])
        for v in reversed(versions):
            if v["is_latest"]:
                return v
        return versions[-1] if versions else None


# Service instances
vision_deployment_service = VisionDeploymentService()
model_registry_service = ModelRegistryService()
model_version_service = ModelVersionService()

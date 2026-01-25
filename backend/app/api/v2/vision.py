"""
Vision API - AI Plant Vision Training Ground
Phase 1: Dataset management, image upload, model inference
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.services.vision_datasets import (
    vision_dataset_service,
    vision_model_service,
    DatasetType,
    DatasetStatus,
)

router = APIRouter(prefix="/vision", tags=["Vision Training Ground"])


# ============ Schemas ============

class DatasetCreate(BaseModel):
    name: str = Field(..., description="Dataset name")
    description: str = Field("", description="Dataset description")
    dataset_type: DatasetType = Field(DatasetType.CLASSIFICATION, description="Type of dataset")
    crop: str = Field(..., description="Target crop (rice, wheat, maize, etc.)")
    classes: list[str] = Field(..., description="Class labels for classification")
    train_split: float = Field(0.7, ge=0, le=1, description="Training split ratio")
    val_split: float = Field(0.15, ge=0, le=1, description="Validation split ratio")
    test_split: float = Field(0.15, ge=0, le=1, description="Test split ratio")


class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    classes: Optional[list[str]] = None
    train_split: Optional[float] = None
    val_split: Optional[float] = None
    test_split: Optional[float] = None
    status: Optional[DatasetStatus] = None


class ImageUpload(BaseModel):
    filename: str = Field(..., description="Image filename")
    url: Optional[str] = Field(None, description="Image URL or base64 data")
    width: int = Field(640, description="Image width")
    height: int = Field(480, description="Image height")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")
    metadata: Optional[dict] = Field(None, description="Additional metadata (GPS, date, etc.)")
    annotation: Optional[dict] = Field(None, description="Annotation data")
    split: str = Field("train", description="Dataset split (train, val, test)")


class ImageBatchUpload(BaseModel):
    images: list[ImageUpload] = Field(..., description="List of images to upload")


class PredictRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image or URL")


# ============ Dataset Endpoints ============

@router.post("/datasets", summary="Create dataset")
async def create_dataset(data: DatasetCreate):
    """Create a new vision dataset for training"""
    # Validate splits sum to 1
    if abs(data.train_split + data.val_split + data.test_split - 1.0) > 0.01:
        raise HTTPException(400, "Train, val, and test splits must sum to 1.0")
    
    dataset = vision_dataset_service.create_dataset(
        name=data.name,
        description=data.description,
        dataset_type=data.dataset_type,
        crop=data.crop,
        classes=data.classes,
        train_split=data.train_split,
        val_split=data.val_split,
        test_split=data.test_split,
    )
    return {"success": True, "dataset": dataset}


@router.get("/datasets", summary="List datasets")
async def list_datasets(
    crop: Optional[str] = Query(None, description="Filter by crop"),
    status: Optional[DatasetStatus] = Query(None, description="Filter by status"),
    dataset_type: Optional[DatasetType] = Query(None, description="Filter by type"),
):
    """List all vision datasets"""
    datasets = vision_dataset_service.list_datasets(
        crop=crop,
        status=status,
        dataset_type=dataset_type,
    )
    return {
        "success": True,
        "count": len(datasets),
        "datasets": datasets,
    }


@router.get("/datasets/{dataset_id}", summary="Get dataset")
async def get_dataset(dataset_id: str):
    """Get dataset details by ID"""
    dataset = vision_dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    return {"success": True, "dataset": dataset}


@router.put("/datasets/{dataset_id}", summary="Update dataset")
async def update_dataset(dataset_id: str, data: DatasetUpdate):
    """Update dataset metadata"""
    updates = data.model_dump(exclude_none=True)
    
    # Validate splits if provided
    if any(k in updates for k in ["train_split", "val_split", "test_split"]):
        dataset = vision_dataset_service.get_dataset(dataset_id)
        if dataset:
            train = updates.get("train_split", dataset["train_split"])
            val = updates.get("val_split", dataset["val_split"])
            test = updates.get("test_split", dataset["test_split"])
            if abs(train + val + test - 1.0) > 0.01:
                raise HTTPException(400, "Train, val, and test splits must sum to 1.0")
    
    dataset = vision_dataset_service.update_dataset(dataset_id, updates)
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    return {"success": True, "dataset": dataset}


@router.delete("/datasets/{dataset_id}", summary="Delete dataset")
async def delete_dataset(dataset_id: str):
    """Delete a dataset and all its images"""
    success = vision_dataset_service.delete_dataset(dataset_id)
    if not success:
        raise HTTPException(404, "Dataset not found")
    return {"success": True, "message": "Dataset deleted"}


# ============ Image Endpoints ============

@router.post("/datasets/{dataset_id}/images", summary="Upload images")
async def upload_images(dataset_id: str, data: ImageBatchUpload):
    """Upload images to a dataset"""
    result = vision_dataset_service.add_images(
        dataset_id=dataset_id,
        images=[img.model_dump() for img in data.images],
    )
    if "error" in result:
        raise HTTPException(404, result["error"])
    return {"success": True, **result}


@router.get("/datasets/{dataset_id}/images", summary="Get dataset images")
async def get_dataset_images(
    dataset_id: str,
    split: Optional[str] = Query(None, description="Filter by split (train, val, test)"),
    annotated_only: bool = Query(False, description="Only return annotated images"),
    limit: int = Query(100, ge=1, le=1000, description="Max images to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """Get images from a dataset"""
    images = vision_dataset_service.get_dataset_images(
        dataset_id=dataset_id,
        split=split,
        annotated_only=annotated_only,
        limit=limit,
        offset=offset,
    )
    return {
        "success": True,
        "count": len(images),
        "images": images,
    }


# ============ Statistics Endpoints ============

@router.get("/datasets/{dataset_id}/stats", summary="Get dataset statistics")
async def get_dataset_stats(dataset_id: str):
    """Get detailed statistics for a dataset"""
    stats = vision_dataset_service.get_dataset_stats(dataset_id)
    if not stats:
        raise HTTPException(404, "Dataset not found")
    return {"success": True, "stats": stats}


# ============ Export Endpoints ============

@router.post("/datasets/{dataset_id}/export", summary="Export annotations")
async def export_annotations(
    dataset_id: str,
    format: str = Query("coco", description="Export format (coco, yolo, csv)"),
):
    """Export dataset annotations in specified format"""
    result = vision_dataset_service.export_annotations(dataset_id, format)
    if not result:
        raise HTTPException(404, "Dataset not found")
    if "error" in result:
        raise HTTPException(400, result["error"])
    return {"success": True, "format": format, "data": result}


# ============ Model Endpoints ============

@router.get("/models", summary="List available models")
async def list_models(
    crop: Optional[str] = Query(None, description="Filter by crop"),
    task: Optional[str] = Query(None, description="Filter by task (classification, detection)"),
    status: Optional[str] = Query(None, description="Filter by status (ready, deployed)"),
):
    """List available pre-trained and custom models"""
    models = vision_model_service.list_models(
        crop=crop,
        task=task,
        status=status,
    )
    return {
        "success": True,
        "count": len(models),
        "models": models,
    }


@router.get("/models/{model_id}", summary="Get model details")
async def get_model(model_id: str):
    """Get model details by ID"""
    model = vision_model_service.get_model(model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    return {"success": True, "model": model}


@router.post("/predict", summary="Run inference")
async def predict(
    model_id: str = Query(..., description="Model ID to use for prediction"),
    data: PredictRequest = None,
):
    """Run inference on an image using a trained model"""
    if not data:
        data = PredictRequest(image_data="")
    
    result = vision_model_service.predict(
        model_id=model_id,
        image_data=data.image_data,
    )
    if "error" in result:
        raise HTTPException(404, result["error"])
    return {"success": True, **result}


# ============ Reference Data ============

@router.get("/crops", summary="List supported crops")
async def list_crops():
    """List crops supported for vision training"""
    crops = [
        {"code": "rice", "name": "Rice", "icon": "🌾", "diseases": 8, "stages": 8},
        {"code": "wheat", "name": "Wheat", "icon": "🌾", "diseases": 6, "stages": 8},
        {"code": "maize", "name": "Maize", "icon": "🌽", "diseases": 5, "stages": 7},
        {"code": "soybean", "name": "Soybean", "icon": "🫘", "diseases": 4, "stages": 6},
        {"code": "cotton", "name": "Cotton", "icon": "☁️", "diseases": 5, "stages": 5},
        {"code": "tomato", "name": "Tomato", "icon": "🍅", "diseases": 7, "stages": 6},
        {"code": "potato", "name": "Potato", "icon": "🥔", "diseases": 6, "stages": 5},
    ]
    return {"success": True, "crops": crops}


@router.get("/base-models", summary="List base models for transfer learning")
async def list_base_models():
    """List available base models for transfer learning"""
    base_models = [
        {
            "id": "mobilenetv2",
            "name": "MobileNetV2",
            "description": "Lightweight model optimized for mobile/edge deployment",
            "size_mb": 14,
            "accuracy_imagenet": 0.718,
            "recommended_for": ["mobile", "edge", "real-time"],
        },
        {
            "id": "efficientnetb0",
            "name": "EfficientNetB0",
            "description": "Efficient scaling with good accuracy/size tradeoff",
            "size_mb": 29,
            "accuracy_imagenet": 0.772,
            "recommended_for": ["balanced", "general"],
        },
        {
            "id": "resnet50",
            "name": "ResNet50",
            "description": "Classic architecture with strong feature extraction",
            "size_mb": 98,
            "accuracy_imagenet": 0.749,
            "recommended_for": ["accuracy", "research"],
        },
    ]
    return {"success": True, "base_models": base_models}


# ============ Phase 2: Annotation Endpoints ============

from app.services.vision_annotation import (
    vision_annotation_service,
    annotation_task_service,
    quality_control_service,
    AnnotationType,
    AnnotationStatus,
)


class BoundingBoxCreate(BaseModel):
    image_id: str = Field(..., description="Image ID")
    boxes: list[dict] = Field(..., description="Bounding boxes [{x, y, width, height, label}]")


class SegmentationCreate(BaseModel):
    image_id: str = Field(..., description="Image ID")
    polygons: list[dict] = Field(..., description="Polygons [{points: [[x,y],...], label}]")


class AnnotationTaskCreate(BaseModel):
    name: str = Field(..., description="Task name")
    annotation_type: AnnotationType = Field(..., description="Type of annotation")
    image_ids: list[str] = Field(..., description="Image IDs to annotate")
    assigned_to: list[str] = Field(default=[], description="Annotator IDs")


class ReviewRequest(BaseModel):
    approved: bool = Field(..., description="Whether to approve")
    notes: Optional[str] = Field(None, description="Review notes")


@router.post("/annotations/bounding-box", summary="Create bounding box annotation")
async def create_bounding_box(dataset_id: str, data: BoundingBoxCreate):
    """Create bounding box annotations for an image"""
    annotation = vision_annotation_service.create_bounding_box(
        image_id=data.image_id,
        dataset_id=dataset_id,
        boxes=data.boxes,
    )
    return {"success": True, "annotation": annotation}


@router.post("/annotations/segmentation", summary="Create segmentation annotation")
async def create_segmentation(dataset_id: str, data: SegmentationCreate):
    """Create segmentation annotations for an image"""
    annotation = vision_annotation_service.create_segmentation(
        image_id=data.image_id,
        dataset_id=dataset_id,
        polygons=data.polygons,
    )
    return {"success": True, "annotation": annotation}


@router.get("/images/{image_id}/annotations", summary="Get image annotations")
async def get_image_annotations(image_id: str):
    """Get all annotations for an image"""
    annotations = vision_annotation_service.get_image_annotations(image_id)
    return {"success": True, "count": len(annotations), "annotations": annotations}


@router.put("/annotations/{annotation_id}", summary="Update annotation")
async def update_annotation(annotation_id: str, data: dict):
    """Update annotation data"""
    annotation = vision_annotation_service.update_annotation(annotation_id, data)
    if not annotation:
        raise HTTPException(404, "Annotation not found")
    return {"success": True, "annotation": annotation}


@router.post("/annotations/{annotation_id}/submit", summary="Submit for review")
async def submit_annotation_for_review(annotation_id: str):
    """Submit annotation for review"""
    annotation = vision_annotation_service.submit_for_review(annotation_id)
    if not annotation:
        raise HTTPException(404, "Annotation not found")
    return {"success": True, "annotation": annotation}


@router.post("/annotations/{annotation_id}/review", summary="Review annotation")
async def review_annotation(annotation_id: str, data: ReviewRequest, reviewer_id: str = "reviewer"):
    """Approve or reject an annotation"""
    annotation = vision_annotation_service.review_annotation(
        annotation_id=annotation_id,
        approved=data.approved,
        reviewer_id=reviewer_id,
        notes=data.notes,
    )
    if not annotation:
        raise HTTPException(404, "Annotation not found")
    return {"success": True, "annotation": annotation}


@router.delete("/annotations/{annotation_id}", summary="Delete annotation")
async def delete_annotation(annotation_id: str):
    """Delete an annotation"""
    success = vision_annotation_service.delete_annotation(annotation_id)
    if not success:
        raise HTTPException(404, "Annotation not found")
    return {"success": True, "message": "Annotation deleted"}


# Annotation Tasks (Collaborative Workflow)
@router.post("/datasets/{dataset_id}/tasks", summary="Create annotation task")
async def create_annotation_task(dataset_id: str, data: AnnotationTaskCreate):
    """Create a collaborative annotation task"""
    task = annotation_task_service.create_task(
        dataset_id=dataset_id,
        name=data.name,
        annotation_type=data.annotation_type,
        image_ids=data.image_ids,
        assigned_to=data.assigned_to,
    )
    return {"success": True, "task": task}


@router.get("/tasks", summary="List annotation tasks")
async def list_annotation_tasks(
    dataset_id: Optional[str] = None,
    status: Optional[AnnotationStatus] = None,
    annotator_id: Optional[str] = None,
):
    """List annotation tasks"""
    tasks = annotation_task_service.list_tasks(
        dataset_id=dataset_id,
        status=status,
        annotator_id=annotator_id,
    )
    return {"success": True, "count": len(tasks), "tasks": tasks}


@router.get("/tasks/{task_id}", summary="Get annotation task")
async def get_annotation_task(task_id: str):
    """Get annotation task details"""
    task = annotation_task_service.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return {"success": True, "task": task}


# Quality Control
@router.get("/annotators", summary="List annotators")
async def list_annotators():
    """List all annotators"""
    annotators = quality_control_service.list_annotators()
    return {"success": True, "annotators": annotators}


@router.get("/annotators/{annotator_id}/stats", summary="Get annotator stats")
async def get_annotator_stats(annotator_id: str):
    """Get statistics for an annotator"""
    stats = quality_control_service.get_annotator_stats(annotator_id)
    if "error" in stats:
        raise HTTPException(404, stats["error"])
    return {"success": True, "stats": stats}


@router.get("/datasets/{dataset_id}/quality", summary="Get quality metrics")
async def get_quality_metrics(dataset_id: str):
    """Get annotation quality metrics for a dataset"""
    metrics = quality_control_service.get_quality_metrics(dataset_id)
    return {"success": True, "metrics": metrics}


# ============ Phase 3: Training Endpoints ============

from app.services.vision_training import (
    vision_training_service,
    hyperparameter_service,
    TrainingStatus,
    TrainingBackend,
)


class TrainingJobCreate(BaseModel):
    name: str = Field(..., description="Job name")
    dataset_id: str = Field(..., description="Dataset to train on")
    base_model: str = Field("mobilenetv2", description="Base model for transfer learning")
    backend: TrainingBackend = Field(TrainingBackend.SERVER, description="Training backend")
    hyperparameters: dict = Field(default={}, description="Training hyperparameters")


class TrainingProgressUpdate(BaseModel):
    epoch: int = Field(..., description="Current epoch")
    metrics: dict = Field(..., description="Training metrics")


@router.post("/training/jobs", summary="Create training job")
async def create_training_job(data: TrainingJobCreate):
    """Create a new training job"""
    job = vision_training_service.create_job(
        name=data.name,
        dataset_id=data.dataset_id,
        base_model=data.base_model,
        backend=data.backend,
        hyperparameters=data.hyperparameters,
    )
    return {"success": True, "job": job}


@router.get("/training/jobs", summary="List training jobs")
async def list_training_jobs(
    dataset_id: Optional[str] = None,
    status: Optional[TrainingStatus] = None,
):
    """List training jobs"""
    jobs = vision_training_service.list_jobs(dataset_id=dataset_id, status=status)
    return {"success": True, "count": len(jobs), "jobs": jobs}


@router.get("/training/jobs/{job_id}", summary="Get training job")
async def get_training_job(job_id: str):
    """Get training job details"""
    job = vision_training_service.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"success": True, "job": job}


@router.post("/training/jobs/{job_id}/start", summary="Start training job")
async def start_training_job(job_id: str):
    """Start a queued training job"""
    result = vision_training_service.start_job(job_id)
    if not result:
        raise HTTPException(404, "Job not found")
    if "error" in result:
        raise HTTPException(400, result["error"])
    return {"success": True, "job": result}


@router.post("/training/jobs/{job_id}/cancel", summary="Cancel training job")
async def cancel_training_job(job_id: str):
    """Cancel a training job"""
    result = vision_training_service.cancel_job(job_id)
    if not result:
        raise HTTPException(404, "Job not found")
    if "error" in result:
        raise HTTPException(400, result["error"])
    return {"success": True, "job": result}


@router.get("/training/jobs/{job_id}/logs", summary="Get training logs")
async def get_training_logs(job_id: str, last_n: Optional[int] = None):
    """Get training logs for a job"""
    logs = vision_training_service.get_logs(job_id, last_n)
    return {"success": True, "count": len(logs), "logs": logs}


@router.post("/training/jobs/compare", summary="Compare training jobs")
async def compare_training_jobs(job_ids: list[str]):
    """Compare multiple training jobs"""
    comparison = vision_training_service.compare_jobs(job_ids)
    if "error" in comparison:
        raise HTTPException(400, comparison["error"])
    return {"success": True, "comparison": comparison}


@router.get("/training/hyperparameters/recommend", summary="Get recommended hyperparameters")
async def get_recommended_hyperparameters(
    dataset_size: int = Query(..., description="Number of images in dataset"),
    task_type: str = Query("classification", description="Task type"),
):
    """Get recommended hyperparameters based on dataset size"""
    config = hyperparameter_service.get_recommended_config(dataset_size, task_type)
    return {"success": True, "config": config}


@router.get("/training/augmentation-options", summary="Get augmentation options")
async def get_augmentation_options():
    """Get available data augmentation options"""
    options = hyperparameter_service.get_augmentation_options()
    return {"success": True, "options": options}


# ============ Phase 4: Deployment & Registry Endpoints ============

from app.services.vision_deployment import (
    vision_deployment_service,
    model_registry_service,
    model_version_service,
    ExportFormat,
    DeploymentTarget,
    ModelVisibility,
)


class ExportRequest(BaseModel):
    format: ExportFormat = Field(..., description="Export format")
    optimize: bool = Field(True, description="Apply optimizations")
    quantize: bool = Field(False, description="Apply INT8 quantization")


class DeployRequest(BaseModel):
    target: DeploymentTarget = Field(..., description="Deployment target")
    format: ExportFormat = Field(..., description="Model format")


class PublishRequest(BaseModel):
    name: str = Field(..., description="Model name")
    description: str = Field(..., description="Model description")
    crop: str = Field(..., description="Target crop")
    task: str = Field("classification", description="Task type")
    classes: list[str] = Field(..., description="Class labels")
    accuracy: float = Field(..., description="Model accuracy")
    size_mb: float = Field(..., description="Model size in MB")
    tags: list[str] = Field(default=[], description="Tags")
    visibility: ModelVisibility = Field(ModelVisibility.PUBLIC, description="Visibility")
    license: str = Field("CC-BY-4.0", description="License")


@router.post("/models/{model_id}/export", summary="Export model")
async def export_model(model_id: str, data: ExportRequest):
    """Export model to specified format"""
    result = vision_deployment_service.export_model(
        model_id=model_id,
        format=data.format,
        optimize=data.optimize,
        quantize=data.quantize,
    )
    return {"success": True, "export": result}


@router.post("/models/{model_id}/deploy", summary="Deploy model")
async def deploy_model(model_id: str, data: DeployRequest):
    """Deploy model to a target"""
    deployment = vision_deployment_service.deploy_model(
        model_id=model_id,
        target=data.target,
        format=data.format,
    )
    return {"success": True, "deployment": deployment}


@router.get("/deployments", summary="List deployments")
async def list_deployments(model_id: Optional[str] = None):
    """List model deployments"""
    deployments = vision_deployment_service.list_deployments(model_id)
    return {"success": True, "count": len(deployments), "deployments": deployments}


@router.get("/deployments/{deploy_id}", summary="Get deployment")
async def get_deployment(deploy_id: str):
    """Get deployment details"""
    deployment = vision_deployment_service.get_deployment(deploy_id)
    if not deployment:
        raise HTTPException(404, "Deployment not found")
    return {"success": True, "deployment": deployment}


@router.get("/deployments/{deploy_id}/stats", summary="Get deployment stats")
async def get_deployment_stats(deploy_id: str):
    """Get deployment statistics"""
    stats = vision_deployment_service.get_deployment_stats(deploy_id)
    if not stats:
        raise HTTPException(404, "Deployment not found")
    return {"success": True, "stats": stats}


@router.delete("/deployments/{deploy_id}", summary="Undeploy model")
async def undeploy_model(deploy_id: str):
    """Remove a deployment"""
    success = vision_deployment_service.undeploy(deploy_id)
    if not success:
        raise HTTPException(404, "Deployment not found")
    return {"success": True, "message": "Model undeployed"}


# Model Registry
@router.post("/models/{model_id}/publish", summary="Publish to registry")
async def publish_to_registry(model_id: str, data: PublishRequest, author: str = "Anonymous"):
    """Publish a model to the community registry"""
    entry = model_registry_service.publish_model(
        model_id=model_id,
        name=data.name,
        description=data.description,
        author=author,
        crop=data.crop,
        task=data.task,
        classes=data.classes,
        accuracy=data.accuracy,
        size_mb=data.size_mb,
        tags=data.tags,
        visibility=data.visibility,
        license=data.license,
    )
    return {"success": True, "registry_entry": entry}


@router.get("/registry", summary="Search model registry")
async def search_registry(
    query: Optional[str] = None,
    crop: Optional[str] = None,
    task: Optional[str] = None,
    min_accuracy: Optional[float] = None,
    sort_by: str = Query("downloads", description="Sort by: downloads, accuracy, recent, likes"),
):
    """Search the community model registry"""
    models = model_registry_service.search_registry(
        query=query,
        crop=crop,
        task=task,
        min_accuracy=min_accuracy,
        sort_by=sort_by,
    )
    return {"success": True, "count": len(models), "models": models}


@router.get("/registry/featured", summary="Get featured models")
async def get_featured_models(limit: int = 5):
    """Get featured/popular models from registry"""
    models = model_registry_service.get_featured_models(limit)
    return {"success": True, "models": models}


@router.get("/registry/{registry_id}", summary="Get registry model")
async def get_registry_model(registry_id: str):
    """Get model details from registry"""
    model = model_registry_service.get_registry_model(registry_id)
    if not model:
        raise HTTPException(404, "Model not found in registry")
    return {"success": True, "model": model}


@router.post("/registry/{registry_id}/download", summary="Download model")
async def download_registry_model(registry_id: str):
    """Download a model from registry"""
    result = model_registry_service.download_model(registry_id)
    if not result:
        raise HTTPException(404, "Model not found in registry")
    return {"success": True, **result}


@router.post("/registry/{registry_id}/like", summary="Like model")
async def like_registry_model(registry_id: str):
    """Like a model in the registry"""
    result = model_registry_service.like_model(registry_id)
    if not result:
        raise HTTPException(404, "Model not found in registry")
    return {"success": True, **result}


# Model Versions
@router.get("/models/{model_id}/versions", summary="List model versions")
async def list_model_versions(model_id: str):
    """List all versions of a model"""
    versions = model_version_service.list_versions(model_id)
    return {"success": True, "versions": versions}


@router.get("/models/{model_id}/versions/latest", summary="Get latest version")
async def get_latest_model_version(model_id: str):
    """Get the latest version of a model"""
    version = model_version_service.get_latest_version(model_id)
    if not version:
        return {"success": True, "version": None, "message": "No versions found"}
    return {"success": True, "version": version}

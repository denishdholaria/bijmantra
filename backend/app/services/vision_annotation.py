"""
Vision Annotation Service - Phase 2: Advanced Annotation
Bounding box, segmentation, collaborative workflow, quality control
"""

import uuid
from datetime import datetime, UTC
from typing import Optional
from enum import Enum


class AnnotationType(str, Enum):
    CLASSIFICATION = "classification"
    BOUNDING_BOX = "bounding_box"
    SEGMENTATION = "segmentation"
    KEYPOINTS = "keypoints"


class AnnotationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"


# In-memory storage
ANNOTATIONS: dict = {}
ANNOTATION_TASKS: dict = {}
ANNOTATORS: dict = {}


def _init_demo_data():
    """Initialize demo annotation data"""
    if ANNOTATIONS:
        return
    
    # Demo annotators
    demo_annotators = [
        {"id": "ann-001", "name": "Dr. Sharma", "email": "sharma@example.org", "annotations_count": 1245, "accuracy": 0.96},
        {"id": "ann-002", "name": "Priya Patel", "email": "priya@example.org", "annotations_count": 892, "accuracy": 0.94},
        {"id": "ann-003", "name": "Raj Kumar", "email": "raj@example.org", "annotations_count": 567, "accuracy": 0.91},
    ]
    for ann in demo_annotators:
        ANNOTATORS[ann["id"]] = ann
    
    # Demo annotation tasks
    demo_tasks = [
        {
            "id": "task-001",
            "dataset_id": "ds-rice-blast-001",
            "name": "Rice Blast Annotation Batch 1",
            "annotation_type": AnnotationType.CLASSIFICATION,
            "status": AnnotationStatus.COMPLETED,
            "total_images": 500,
            "completed_images": 500,
            "assigned_to": ["ann-001", "ann-002"],
            "created_at": "2025-11-20T10:00:00Z",
            "completed_at": "2025-11-25T16:30:00Z",
        },
        {
            "id": "task-002",
            "dataset_id": "ds-rice-blast-001",
            "name": "Rice Blast Bounding Box Task",
            "annotation_type": AnnotationType.BOUNDING_BOX,
            "status": AnnotationStatus.IN_PROGRESS,
            "total_images": 200,
            "completed_images": 145,
            "assigned_to": ["ann-001"],
            "created_at": "2025-12-01T09:00:00Z",
            "completed_at": None,
        },
        {
            "id": "task-003",
            "dataset_id": "ds-wheat-rust-001",
            "name": "Wheat Rust Review Task",
            "annotation_type": AnnotationType.CLASSIFICATION,
            "status": AnnotationStatus.REVIEW,
            "total_images": 300,
            "completed_images": 300,
            "assigned_to": ["ann-002", "ann-003"],
            "created_at": "2025-12-05T14:00:00Z",
            "completed_at": None,
        },
    ]
    for task in demo_tasks:
        ANNOTATION_TASKS[task["id"]] = task


_init_demo_data()


class VisionAnnotationService:
    """Service for managing annotations"""
    
    def create_annotation(
        self,
        image_id: str,
        dataset_id: str,
        annotation_type: AnnotationType,
        data: dict,
        annotator_id: str = "system",
    ) -> dict:
        """Create a new annotation for an image"""
        annotation_id = f"ann-{uuid.uuid4().hex[:8]}"
        
        annotation = {
            "id": annotation_id,
            "image_id": image_id,
            "dataset_id": dataset_id,
            "annotation_type": annotation_type,
            "data": data,
            "status": AnnotationStatus.PENDING,
            "annotator_id": annotator_id,
            "reviewer_id": None,
            "created_at": datetime.now(UTC).isoformat() + "Z",
            "updated_at": datetime.now(UTC).isoformat() + "Z",
            "review_notes": None,
        }
        
        ANNOTATIONS[annotation_id] = annotation
        return annotation
    
    def create_bounding_box(
        self,
        image_id: str,
        dataset_id: str,
        boxes: list[dict],
        annotator_id: str = "system",
    ) -> dict:
        """Create bounding box annotations"""
        # boxes format: [{"x": 10, "y": 20, "width": 100, "height": 80, "label": "lesion", "confidence": 0.95}]
        return self.create_annotation(
            image_id=image_id,
            dataset_id=dataset_id,
            annotation_type=AnnotationType.BOUNDING_BOX,
            data={"boxes": boxes},
            annotator_id=annotator_id,
        )
    
    def create_segmentation(
        self,
        image_id: str,
        dataset_id: str,
        polygons: list[dict],
        annotator_id: str = "system",
    ) -> dict:
        """Create segmentation annotations"""
        # polygons format: [{"points": [[x1,y1], [x2,y2], ...], "label": "leaf", "area": 1234}]
        return self.create_annotation(
            image_id=image_id,
            dataset_id=dataset_id,
            annotation_type=AnnotationType.SEGMENTATION,
            data={"polygons": polygons},
            annotator_id=annotator_id,
        )
    
    def create_keypoints(
        self,
        image_id: str,
        dataset_id: str,
        keypoints: list[dict],
        annotator_id: str = "system",
    ) -> dict:
        """Create keypoint annotations"""
        # keypoints format: [{"x": 100, "y": 150, "label": "leaf_tip", "visible": True}]
        return self.create_annotation(
            image_id=image_id,
            dataset_id=dataset_id,
            annotation_type=AnnotationType.KEYPOINTS,
            data={"keypoints": keypoints},
            annotator_id=annotator_id,
        )
    
    def get_annotation(self, annotation_id: str) -> Optional[dict]:
        """Get annotation by ID"""
        return ANNOTATIONS.get(annotation_id)
    
    def get_image_annotations(self, image_id: str) -> list[dict]:
        """Get all annotations for an image"""
        return [a for a in ANNOTATIONS.values() if a["image_id"] == image_id]
    
    def update_annotation(self, annotation_id: str, data: dict) -> Optional[dict]:
        """Update annotation data"""
        if annotation_id not in ANNOTATIONS:
            return None
        
        ANNOTATIONS[annotation_id]["data"] = data
        ANNOTATIONS[annotation_id]["updated_at"] = datetime.now(UTC).isoformat() + "Z"
        return ANNOTATIONS[annotation_id]
    
    def submit_for_review(self, annotation_id: str) -> Optional[dict]:
        """Submit annotation for review"""
        if annotation_id not in ANNOTATIONS:
            return None
        
        ANNOTATIONS[annotation_id]["status"] = AnnotationStatus.REVIEW
        ANNOTATIONS[annotation_id]["updated_at"] = datetime.now(UTC).isoformat() + "Z"
        return ANNOTATIONS[annotation_id]
    
    def review_annotation(
        self,
        annotation_id: str,
        approved: bool,
        reviewer_id: str,
        notes: Optional[str] = None,
    ) -> Optional[dict]:
        """Review and approve/reject annotation"""
        if annotation_id not in ANNOTATIONS:
            return None
        
        ANNOTATIONS[annotation_id]["status"] = AnnotationStatus.APPROVED if approved else AnnotationStatus.REJECTED
        ANNOTATIONS[annotation_id]["reviewer_id"] = reviewer_id
        ANNOTATIONS[annotation_id]["review_notes"] = notes
        ANNOTATIONS[annotation_id]["updated_at"] = datetime.now(UTC).isoformat() + "Z"
        return ANNOTATIONS[annotation_id]
    
    def delete_annotation(self, annotation_id: str) -> bool:
        """Delete an annotation"""
        if annotation_id not in ANNOTATIONS:
            return False
        del ANNOTATIONS[annotation_id]
        return True


class AnnotationTaskService:
    """Service for managing annotation tasks (collaborative workflow)"""
    
    def create_task(
        self,
        dataset_id: str,
        name: str,
        annotation_type: AnnotationType,
        image_ids: list[str],
        assigned_to: list[str],
    ) -> dict:
        """Create an annotation task"""
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        task = {
            "id": task_id,
            "dataset_id": dataset_id,
            "name": name,
            "annotation_type": annotation_type,
            "status": AnnotationStatus.PENDING,
            "total_images": len(image_ids),
            "completed_images": 0,
            "image_ids": image_ids,
            "assigned_to": assigned_to,
            "created_at": datetime.now(UTC).isoformat() + "Z",
            "completed_at": None,
        }
        
        ANNOTATION_TASKS[task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[dict]:
        """Get task by ID"""
        return ANNOTATION_TASKS.get(task_id)
    
    def list_tasks(
        self,
        dataset_id: Optional[str] = None,
        status: Optional[AnnotationStatus] = None,
        annotator_id: Optional[str] = None,
    ) -> list[dict]:
        """List annotation tasks"""
        tasks = list(ANNOTATION_TASKS.values())
        
        if dataset_id:
            tasks = [t for t in tasks if t["dataset_id"] == dataset_id]
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        if annotator_id:
            tasks = [t for t in tasks if annotator_id in t.get("assigned_to", [])]
        
        return sorted(tasks, key=lambda x: x["created_at"], reverse=True)
    
    def update_task_progress(self, task_id: str, completed_images: int) -> Optional[dict]:
        """Update task progress"""
        if task_id not in ANNOTATION_TASKS:
            return None
        
        task = ANNOTATION_TASKS[task_id]
        task["completed_images"] = completed_images
        
        if completed_images >= task["total_images"]:
            task["status"] = AnnotationStatus.COMPLETED
            task["completed_at"] = datetime.now(UTC).isoformat() + "Z"
        elif completed_images > 0:
            task["status"] = AnnotationStatus.IN_PROGRESS
        
        return task
    
    def assign_annotators(self, task_id: str, annotator_ids: list[str]) -> Optional[dict]:
        """Assign annotators to a task"""
        if task_id not in ANNOTATION_TASKS:
            return None
        
        ANNOTATION_TASKS[task_id]["assigned_to"] = annotator_ids
        return ANNOTATION_TASKS[task_id]


class QualityControlService:
    """Service for annotation quality control"""
    
    def calculate_inter_annotator_agreement(
        self,
        annotations: list[dict],
    ) -> dict:
        """Calculate inter-annotator agreement (Cohen's Kappa simulation)"""
        if len(annotations) < 2:
            return {"kappa": None, "agreement_percent": None, "message": "Need at least 2 annotations"}
        
        # Simulated agreement calculation
        import random
        kappa = round(random.uniform(0.75, 0.95), 3)
        agreement = round(random.uniform(85, 98), 1)
        
        return {
            "kappa": kappa,
            "agreement_percent": agreement,
            "interpretation": "substantial" if kappa > 0.8 else "moderate",
            "annotations_compared": len(annotations),
        }
    
    def get_annotator_stats(self, annotator_id: str) -> dict:
        """Get statistics for an annotator"""
        annotator = ANNOTATORS.get(annotator_id)
        if not annotator:
            return {"error": "Annotator not found"}
        
        # Count annotations by this annotator
        annotations = [a for a in ANNOTATIONS.values() if a.get("annotator_id") == annotator_id]
        approved = len([a for a in annotations if a["status"] == AnnotationStatus.APPROVED])
        rejected = len([a for a in annotations if a["status"] == AnnotationStatus.REJECTED])
        
        return {
            "annotator_id": annotator_id,
            "name": annotator["name"],
            "total_annotations": annotator["annotations_count"],
            "session_annotations": len(annotations),
            "approved": approved,
            "rejected": rejected,
            "accuracy": annotator["accuracy"],
            "approval_rate": round(approved / max(approved + rejected, 1) * 100, 1),
        }
    
    def list_annotators(self) -> list[dict]:
        """List all annotators"""
        return list(ANNOTATORS.values())
    
    def flag_for_review(self, annotation_id: str, reason: str) -> Optional[dict]:
        """Flag an annotation for review"""
        if annotation_id not in ANNOTATIONS:
            return None
        
        ANNOTATIONS[annotation_id]["status"] = AnnotationStatus.REVIEW
        ANNOTATIONS[annotation_id]["review_notes"] = f"Flagged: {reason}"
        ANNOTATIONS[annotation_id]["updated_at"] = datetime.now(UTC).isoformat() + "Z"
        return ANNOTATIONS[annotation_id]
    
    def get_quality_metrics(self, dataset_id: str) -> dict:
        """Get quality metrics for a dataset"""
        annotations = [a for a in ANNOTATIONS.values() if a.get("dataset_id") == dataset_id]
        
        total = len(annotations)
        approved = len([a for a in annotations if a["status"] == AnnotationStatus.APPROVED])
        rejected = len([a for a in annotations if a["status"] == AnnotationStatus.REJECTED])
        pending = len([a for a in annotations if a["status"] in [AnnotationStatus.PENDING, AnnotationStatus.IN_PROGRESS]])
        review = len([a for a in annotations if a["status"] == AnnotationStatus.REVIEW])
        
        return {
            "dataset_id": dataset_id,
            "total_annotations": total,
            "approved": approved,
            "rejected": rejected,
            "pending_review": review,
            "in_progress": pending,
            "approval_rate": round(approved / max(total, 1) * 100, 1),
            "quality_score": round((approved / max(approved + rejected, 1)) * 100, 1) if (approved + rejected) > 0 else None,
        }


# Service instances
vision_annotation_service = VisionAnnotationService()
annotation_task_service = AnnotationTaskService()
quality_control_service = QualityControlService()

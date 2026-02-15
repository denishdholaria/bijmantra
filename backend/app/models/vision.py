from enum import Enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum as SAEnum, ARRAY, Float, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

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

class AnnotationTask(BaseModel):
    __tablename__ = "annotation_tasks"

    dataset_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    annotation_type = Column(SAEnum(AnnotationType), nullable=False)
    status = Column(SAEnum(AnnotationStatus), default=AnnotationStatus.PENDING, nullable=False)
    priority = Column(String, default="medium")
    description = Column(Text, nullable=True)

    # Tracking
    total_images = Column(Integer, default=0)
    completed_images = Column(Integer, default=0)

    # Assignments
    assigned_to = Column(JSON, default=list)  # List of user IDs

    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    items = relationship("AnnotationTaskItem", back_populates="task", cascade="all, delete-orphan")

class AnnotationTaskItem(BaseModel):
    __tablename__ = "annotation_task_items"

    task_id = Column(Integer, ForeignKey("annotation_tasks.id"), nullable=False)
    image_id = Column(String, nullable=False)
    status = Column(SAEnum(AnnotationStatus), default=AnnotationStatus.PENDING, nullable=False)

    # Link to the actual annotation result
    annotation_id = Column(Integer, ForeignKey("vision_annotations.id"), nullable=True)

    assigned_to = Column(String, nullable=True) # specific assignment if needed

    task = relationship("AnnotationTask", back_populates="items")
    annotation = relationship("VisionAnnotation", back_populates="task_item")

class VisionAnnotation(BaseModel):
    __tablename__ = "vision_annotations"

    image_id = Column(String, index=True, nullable=False)
    dataset_id = Column(String, index=True, nullable=False)
    annotation_type = Column(SAEnum(AnnotationType), nullable=False)

    # The actual annotation data (boxes, polygons, class, etc.)
    data = Column(JSON, nullable=False)

    status = Column(SAEnum(AnnotationStatus), default=AnnotationStatus.PENDING, nullable=False)

    annotator_id = Column(String, index=True, nullable=False)
    reviewer_id = Column(String, index=True, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Relationships
    task_item = relationship("AnnotationTaskItem", back_populates="annotation", uselist=False)

class VisionModel(BaseModel):
    __tablename__ = "vision_models"

    organization_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String, default="1.0.0", nullable=False)

    # Artifact details
    format = Column(String, nullable=False) # e.g. "savedmodel", "pytorch"
    file_path = Column(String, nullable=False) # Path to the source model directory/file

    # Metrics (e.g. {"accuracy": 0.95})
    metrics = Column(JSON, default=dict)
    size_bytes = Column(Integer, default=0)

    is_public = Column(Boolean, default=False)
    created_by = Column(String, nullable=True) # User ID

    # Relationships
    deployments = relationship("VisionDeployment", back_populates="model", cascade="all, delete-orphan")

class VisionDeployment(BaseModel):
    __tablename__ = "vision_deployments"

    organization_id = Column(Integer, index=True, nullable=False)
    model_id = Column(Integer, ForeignKey("vision_models.id"), nullable=False)
    target = Column(String, nullable=False) # "browser", "mobile", etc.
    format = Column(String, nullable=False) # "tfjs", "tflite", etc.
    endpoint_url = Column(String, nullable=False)
    status = Column(String, default="pending")

    # Stats
    requests_count = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)

    model = relationship("VisionModel", back_populates="deployments")

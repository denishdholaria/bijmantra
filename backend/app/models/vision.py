from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class AnnotationType(StrEnum):
    CLASSIFICATION = "classification"
    BOUNDING_BOX = "bounding_box"
    SEGMENTATION = "segmentation"
    KEYPOINTS = "keypoints"


class AnnotationStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"


class VisionDatasetType(StrEnum):
    CLASSIFICATION = "CLASSIFICATION"
    DETECTION = "DETECTION"
    SEGMENTATION = "SEGMENTATION"


class VisionDatasetStatus(StrEnum):
    DRAFT = "DRAFT"
    COLLECTING = "COLLECTING"
    ANNOTATING = "ANNOTATING"
    READY = "READY"
    TRAINING = "TRAINING"


class VisionTrainingBackend(StrEnum):
    BROWSER = "BROWSER"
    SERVER = "SERVER"
    CLOUD = "CLOUD"


class VisionTrainingStatus(StrEnum):
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    TRAINING = "TRAINING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

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


class VisionDataset(BaseModel):
    __tablename__ = "vision_datasets"

    dataset_code = Column(String(64), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dataset_type = Column(
        SAEnum(VisionDatasetType, name="visiondatasettype"),
        nullable=False,
        default=VisionDatasetType.CLASSIFICATION,
    )
    crop = Column(String(100), nullable=False, index=True)
    classes = Column(JSON, nullable=False, default=list)
    train_split = Column(Float, nullable=False, default=0.7)
    val_split = Column(Float, nullable=False, default=0.15)
    test_split = Column(Float, nullable=False, default=0.15)
    status = Column(
        SAEnum(VisionDatasetStatus, name="visiondatasetstatus"),
        nullable=False,
        default=VisionDatasetStatus.DRAFT,
        index=True,
    )
    created_by = Column(String, nullable=True)

    organization = relationship("Organization")
    images = relationship("VisionDatasetImage", back_populates="dataset", cascade="all, delete-orphan")
    training_jobs = relationship("VisionTrainingJob", back_populates="dataset", cascade="all, delete-orphan")


class VisionDatasetImage(BaseModel):
    __tablename__ = "vision_dataset_images"

    image_code = Column(String(64), unique=True, index=True, nullable=False)
    dataset_id = Column(Integer, ForeignKey("vision_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    url = Column(Text, nullable=True)
    width = Column(Integer, nullable=False, default=0)
    height = Column(Integer, nullable=False, default=0)
    size_bytes = Column(Integer, nullable=True)
    split = Column(String(16), nullable=False, default="train", index=True)
    metadata_json = Column("metadata", JSON, nullable=False, default=dict)
    annotation_data = Column(JSON, nullable=True)

    dataset = relationship("VisionDataset", back_populates="images")
    organization = relationship("Organization")


class VisionTrainingJob(BaseModel):
    __tablename__ = "vision_training_jobs"

    job_code = Column(String(64), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    dataset_id = Column(Integer, ForeignKey("vision_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    base_model = Column(String(128), nullable=False)
    backend = Column(SAEnum(VisionTrainingBackend, name="visiontrainingbackend"), nullable=False)
    status = Column(
        SAEnum(VisionTrainingStatus, name="visiontrainingstatus"),
        nullable=False,
        default=VisionTrainingStatus.QUEUED,
        index=True,
    )
    hyperparameters = Column(JSON, nullable=False, default=dict)
    metrics = Column(JSON, nullable=False, default=dict)
    progress = Column(Float, nullable=False, default=0)
    current_epoch = Column(Integer, nullable=False, default=0)
    total_epochs = Column(Integer, nullable=False, default=0)
    model_id = Column(String(128), nullable=True)
    created_by = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization")
    dataset = relationship("VisionDataset", back_populates="training_jobs")
    logs = relationship("VisionTrainingLog", back_populates="job", cascade="all, delete-orphan")


class VisionTrainingLog(BaseModel):
    __tablename__ = "vision_training_logs"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("vision_training_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    level = Column(String(16), nullable=False, default="info")
    message = Column(Text, nullable=False)
    status = Column(SAEnum(VisionTrainingStatus, name="visiontrainingstatus"), nullable=True)
    epoch = Column(Integer, nullable=True)
    metrics = Column(JSON, nullable=True)

    organization = relationship("Organization")
    job = relationship("VisionTrainingJob", back_populates="logs")

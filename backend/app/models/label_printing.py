import enum

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PrintJobStatus(enum.StrEnum):
    """Status of a print job"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PrintJob(BaseModel):
    """Print job history"""
    __tablename__ = "print_jobs"
    __table_args__ = {'extend_existing': True}

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    job_id = Column(String(50), unique=True, index=True, nullable=False)

    template_id = Column(String(50), nullable=False)
    status = Column(SQLEnum(PrintJobStatus, values_callable=lambda x: [e.value for e in x]), default=PrintJobStatus.PENDING, index=True)

    completed_at = Column(DateTime(timezone=True), nullable=True)
    label_count = Column(Integer, default=0)
    copies = Column(Integer, default=1)
    items = Column(JSON, default=list)
    created_by = Column(String(255), nullable=True)

    # Relationships
    organization = relationship("Organization")

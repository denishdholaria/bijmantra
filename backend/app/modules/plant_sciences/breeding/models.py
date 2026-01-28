from sqlalchemy import Column, String, Enum, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum
from app.core.database import Base

class CrossStatus(str, enum.Enum):
    PLANNED = "planned"
    MADE = "made"
    SUCCESSFUL = "successful"
    FAILED = "failed"

class Cross(Base):
    """
    Represents a breeding cross between two parent germplasms.
    """
    __tablename__ = "breeding_crosses_demo"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent1_id = Column(String(50), nullable=False)
    parent2_id = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(Enum(CrossStatus), default=CrossStatus.PLANNED)
    notes = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "parent1_id": self.parent1_id,
            "parent2_id": self.parent2_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

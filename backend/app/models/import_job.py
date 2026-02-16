from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ImportJob(BaseModel):
    __tablename__ = "import_jobs"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    import_type = Column(String(50), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    status = Column(String(30), nullable=False, default="pending", index=True)
    dry_run = Column(Boolean, nullable=False, default=False)

    total_rows = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)

    mapping_config = Column(JSON)
    report = Column(JSON)
    error_details = Column(Text)

    organization = relationship("Organization")
    user = relationship("User")

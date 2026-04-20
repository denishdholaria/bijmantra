# backend/app/models/gdd_audit.py
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class GDDAuditLog(BaseModel):
    __tablename__ = "gdd_audit_logs"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    calculation_type = Column(String)
    input_parameters = Column(JSON)
    output_results = Column(JSON)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")
    user = relationship("User")

import enum

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class CertificateStatus(enum.StrEnum):
    VALID = "valid"
    REVOKED = "revoked"

class ComplianceCertificate(Base):
    __tablename__ = "compliance_certificates"

    id = Column(Integer, primary_key=True, index=True)
    certificate_hash = Column(String, unique=True, index=True, nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Enum(CertificateStatus), default=CertificateStatus.VALID)
    pdf_storage_path = Column(String, nullable=True)

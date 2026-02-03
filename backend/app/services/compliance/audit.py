from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.compliance import ComplianceCertificate, CertificateStatus
from app.schemas.compliance import SeedBatchInfo, ComplianceType
from app.services.compliance.pdf_generator import calculate_hash
import json

async def create_audit_record(
    session: AsyncSession,
    batch: SeedBatchInfo,
    compliance_type: ComplianceType,
    pdf_path: str = None
) -> ComplianceCertificate:

    cert_hash = calculate_hash(batch, compliance_type)

    # Check if exists
    result = await session.execute(
        select(ComplianceCertificate).where(ComplianceCertificate.certificate_hash == cert_hash)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return existing

    data_to_store = batch.model_dump()
    data_to_store["compliance_type"] = compliance_type.value

    certificate = ComplianceCertificate(
        certificate_hash=cert_hash,
        data=data_to_store,
        status=CertificateStatus.VALID,
        pdf_storage_path=pdf_path
    )

    session.add(certificate)
    await session.commit()
    await session.refresh(certificate)

    return certificate

async def verify_certificate(
    session: AsyncSession,
    cert_hash: str
) -> ComplianceCertificate | None:
    result = await session.execute(
        select(ComplianceCertificate).where(ComplianceCertificate.certificate_hash == cert_hash)
    )
    return result.scalar_one_or_none()

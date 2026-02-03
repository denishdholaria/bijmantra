import asyncio
import functools
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.v2.dependencies import get_current_user
from app.models.core import User
from app.schemas.compliance import (
    CertificateRequest,
    CertificateResponse,
    BatchGenerationRequest,
    BatchGenerationResponse,
    SeedBatchInfo,
    ComplianceType
)
from app.services.compliance.rules import validate_batch
from app.services.compliance.pdf_generator import calculate_hash, generate_certificate_pdf
from app.services.compliance.audit import create_audit_record, verify_certificate
from app.services.compliance.batch import submit_batch_job

router = APIRouter(prefix="/compliance", tags=["Compliance"])

@router.post("/generate", response_model=CertificateResponse)
async def generate_certificate(
    request: CertificateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Validate rules
    validation = validate_batch(request.seed_batch, request.compliance_type)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=f"Validation failed: {validation['errors']}")

    # 2. Audit Trail & DB Storage
    cert_hash = calculate_hash(request.seed_batch, request.compliance_type)
    verification_url = f"https://bijmantra.org/verify/{cert_hash}"

    # Generate PDF path (mock)
    pdf_path = f"generated_certificates/{request.seed_batch.batch_id}_{cert_hash[:8]}.pdf"

    record = await create_audit_record(
        session=db,
        batch=request.seed_batch,
        compliance_type=request.compliance_type,
        pdf_path=pdf_path
    )

    return CertificateResponse(
        id=record.id,
        certificate_hash=record.certificate_hash,
        created_at=record.created_at,
        status=record.status.value,
        verification_url=verification_url,
        download_url=f"/api/v2/compliance/download/{record.certificate_hash}"
    )

@router.get("/download/{cert_hash}")
async def download_certificate(
    cert_hash: str,
    db: AsyncSession = Depends(get_db)
):
    record = await verify_certificate(db, cert_hash)
    if not record:
        raise HTTPException(status_code=404, detail="Certificate not found")

    data = record.data
    compliance_type_str = data.get("compliance_type", "ISTA")
    compliance_type = ComplianceType(compliance_type_str)

    # Remove compliance_type from data to reconstruct SeedBatchInfo
    batch_data = {k: v for k, v in data.items() if k != "compliance_type"}

    try:
        batch = SeedBatchInfo(**batch_data)
    except Exception:
        raise HTTPException(status_code=500, detail="Corrupted certificate data")

    verification_url = f"https://bijmantra.org/verify/{cert_hash}"

    # Run PDF generation in thread pool
    loop = asyncio.get_running_loop()
    pdf_bytes = await loop.run_in_executor(
        None,
        functools.partial(
            generate_certificate_pdf,
            batch=batch,
            compliance_type=compliance_type,
            issuer_name="Bijmantra System",
            certificate_hash=cert_hash,
            verification_url=verification_url,
            issue_date=record.created_at
        )
    )

    return Response(content=pdf_bytes, media_type="application/pdf")

@router.post("/batch", response_model=BatchGenerationResponse)
async def batch_generate(
    request: BatchGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    # Submit job
    task_id = await submit_batch_job(
        compliance_type=request.compliance_type,
        batches=request.batches,
        issuer_name=request.issuer_name,
        email_to=request.email_to
    )

    return BatchGenerationResponse(
        task_id=task_id,
        message=f"Batch processing started for {len(request.batches)} batches. You will receive an email at {request.email_to}."
    )

@router.get("/verify/{cert_hash}")
async def verify(
    cert_hash: str,
    db: AsyncSession = Depends(get_db)
):
    record = await verify_certificate(db, cert_hash)
    if not record:
        return {"valid": False, "message": "Certificate not found or invalid."}

    return {
        "valid": True,
        "certificate_hash": record.certificate_hash,
        "status": record.status,
        "created_at": record.created_at,
        "data": record.data
    }

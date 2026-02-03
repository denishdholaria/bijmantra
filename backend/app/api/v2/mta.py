"""
Material Transfer Agreement (MTA) API

Endpoints for managing MTAs for germplasm exchange.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.modules.seed_bank.mta import mta_service, MTAType, MTAStatus, BenefitSharingType

router = APIRouter(prefix="/mta", tags=["Material Transfer Agreements"])


# Pydantic Models
class InstitutionInfo(BaseModel):
    institution: str
    country: str
    contact: str
    email: str


class BenefitSharingInfo(BaseModel):
    type: BenefitSharingType
    details: str
    royalty_rate: Optional[float] = None
    milestones: Optional[list] = None


class CreateMTARequest(BaseModel):
    mta_type: MTAType
    provider: InstitutionInfo
    recipient: InstitutionInfo
    accessions: list[str]
    crops: list[str]
    purpose: str
    benefit_sharing: Optional[BenefitSharingInfo] = None
    exchange_id: Optional[str] = None


class ApproveRequest(BaseModel):
    approver: str


class RejectRequest(BaseModel):
    reason: str
    rejector: str


class SignRequest(BaseModel):
    signatory: str


class TerminateRequest(BaseModel):
    reason: str
    terminator: str


# Endpoints
@router.get("/templates")
async def get_mta_templates():
    """Get all available MTA templates"""
    return {
        "templates": mta_service.get_templates(),
        "types": [t.value for t in MTAType],
    }


@router.get("/templates/{template_id}")
async def get_mta_template(template_id: str):
    """Get specific MTA template with full clauses"""
    template = mta_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("")
async def create_mta(request: CreateMTARequest):
    """Create a new Material Transfer Agreement"""
    try:
        mta = mta_service.create_mta(
            mta_type=request.mta_type,
            provider=request.provider.model_dump(),
            recipient=request.recipient.model_dump(),
            accessions=request.accessions,
            crops=request.crops,
            purpose=request.purpose,
            benefit_sharing=request.benefit_sharing.model_dump() if request.benefit_sharing else None,
            exchange_id=request.exchange_id,
        )
        return {"message": "MTA created successfully", "mta": mta}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_mtas(
    mta_type: Optional[MTAType] = Query(None, description="Filter by MTA type"),
    status: Optional[MTAStatus] = Query(None, description="Filter by status"),
    institution: Optional[str] = Query(None, description="Filter by institution name"),
):
    """List all MTAs with optional filters"""
    mtas = mta_service.list_mtas(
        mta_type=mta_type,
        status=status,
        institution=institution,
    )
    return {"mtas": mtas, "count": len(mtas)}


@router.get("/statistics")
async def get_mta_statistics():
    """Get MTA statistics"""
    return mta_service.get_statistics()


@router.get("/by-number/{mta_number}")
async def get_mta_by_number(mta_number: str):
    """Get MTA by its number"""
    mta = mta_service.get_mta_by_number(mta_number)
    if not mta:
        raise HTTPException(status_code=404, detail="MTA not found")
    return mta


@router.get("/by-exchange/{exchange_id}")
async def get_mta_for_exchange(exchange_id: str):
    """Get MTA associated with a germplasm exchange"""
    mta = mta_service.get_mta_for_exchange(exchange_id)
    if not mta:
        raise HTTPException(status_code=404, detail="No MTA found for this exchange")
    return mta


@router.get("/{mta_id}")
async def get_mta(mta_id: str):
    """Get MTA by ID"""
    mta = mta_service.get_mta(mta_id)
    if not mta:
        raise HTTPException(status_code=404, detail="MTA not found")
    return mta


@router.post("/{mta_id}/submit")
async def submit_mta_for_review(mta_id: str):
    """Submit MTA for review"""
    try:
        mta = mta_service.submit_for_review(mta_id)
        if not mta:
            raise HTTPException(status_code=404, detail="MTA not found")
        return {"message": "MTA submitted for review", "mta": mta}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{mta_id}/approve")
async def approve_mta(mta_id: str, request: ApproveRequest):
    """Approve MTA after review"""
    try:
        mta = mta_service.approve_mta(mta_id, request.approver)
        if not mta:
            raise HTTPException(status_code=404, detail="MTA not found")
        return {"message": "MTA approved", "mta": mta}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{mta_id}/reject")
async def reject_mta(mta_id: str, request: RejectRequest):
    """Reject MTA"""
    try:
        mta = mta_service.reject_mta(mta_id, request.reason, request.rejector)
        if not mta:
            raise HTTPException(status_code=404, detail="MTA not found")
        return {"message": "MTA rejected", "mta": mta}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{mta_id}/sign")
async def sign_mta(mta_id: str, request: SignRequest):
    """Sign and activate MTA"""
    try:
        mta = mta_service.sign_mta(mta_id, request.signatory)
        if not mta:
            raise HTTPException(status_code=404, detail="MTA not found")
        return {"message": "MTA signed and activated", "mta": mta}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{mta_id}/terminate")
async def terminate_mta(mta_id: str, request: TerminateRequest):
    """Terminate an active MTA"""
    try:
        mta = mta_service.terminate_mta(mta_id, request.reason, request.terminator)
        if not mta:
            raise HTTPException(status_code=404, detail="MTA not found")
        return {"message": "MTA terminated", "mta": mta}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{mta_id}/compliance")
async def check_mta_compliance(mta_id: str):
    """Check MTA compliance status"""
    result = mta_service.check_compliance(mta_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/types/reference")
async def get_mta_types():
    """Get MTA type reference data"""
    return {
        "types": [
            {
                "value": MTAType.SMTA.value,
                "name": "Standard MTA (SMTA)",
                "description": "For ITPGRFA Annex I crops, auto-approved",
            },
            {
                "value": MTAType.INSTITUTIONAL.value,
                "name": "Institutional MTA",
                "description": "Bilateral agreement between institutions",
            },
            {
                "value": MTAType.RESEARCH.value,
                "name": "Research MTA",
                "description": "Research-only use, no commercial development",
            },
            {
                "value": MTAType.COMMERCIAL.value,
                "name": "Commercial MTA",
                "description": "Commercial development with benefit sharing",
            },
        ],
        "statuses": [
            {"value": s.value, "name": s.value.replace("_", " ").title()}
            for s in MTAStatus
        ],
        "benefit_sharing_types": [
            {"value": b.value, "name": b.value.replace("_", " ").title()}
            for b in BenefitSharingType
        ],
    }

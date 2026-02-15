"""
Variety Licensing API
Manage Plant Variety Protection (PVP), Plant Breeders Rights (PBR),
and variety licensing agreements
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.variety_licensing import variety_licensing_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/licensing", tags=["Variety Licensing"], dependencies=[Depends(get_current_user)])


class VarietyRegistration(BaseModel):
    variety_name: str
    crop: str
    breeder_id: str
    breeder_name: str
    organization_id: str
    organization_name: str
    description: str
    key_traits: List[str]
    release_date: Optional[str] = None


class ProtectionFiling(BaseModel):
    variety_id: str
    protection_type: str  # pvp, pbr, patent, trademark, trade_secret
    application_number: str
    filing_date: str
    territory: List[str]
    authority: str


class ProtectionGrant(BaseModel):
    certificate_number: str
    grant_date: str
    expiry_date: str


class LicenseCreation(BaseModel):
    variety_id: str
    licensee_id: str
    licensee_name: str
    license_type: str  # exclusive, non_exclusive, research, evaluation, production, marketing
    territory: List[str]
    start_date: str
    end_date: str
    royalty_rate_percent: float
    minimum_royalty: Optional[float] = None
    upfront_fee: Optional[float] = None
    terms: Optional[str] = None


class RoyaltyRecord(BaseModel):
    period_start: str
    period_end: str
    sales_quantity_kg: float
    sales_value: float
    royalty_amount: float
    payment_status: str = "pending"


# Variety endpoints
@router.post("/varieties")
async def register_variety(data: VarietyRegistration):
    """Register a new variety for protection"""
    variety = variety_licensing_service.register_variety(**data.model_dump())
    return {"status": "success", "data": variety}


@router.get("/varieties")
async def list_varieties(
    crop: Optional[str] = None,
    organization_id: Optional[str] = None,
    status: Optional[str] = None,
):
    """List varieties with optional filters"""
    varieties = variety_licensing_service.list_varieties(
        crop=crop,
        organization_id=organization_id,
        status=status,
    )
    return {"status": "success", "data": varieties, "count": len(varieties)}


@router.get("/varieties/{variety_id}")
async def get_variety(variety_id: str):
    """Get variety details"""
    variety = variety_licensing_service.get_variety(variety_id)
    if not variety:
        raise HTTPException(status_code=404, detail=f"Variety {variety_id} not found")
    return {"status": "success", "data": variety}


# Protection endpoints
@router.post("/protections")
async def file_protection(data: ProtectionFiling):
    """File for variety protection (PVP/PBR/Patent)"""
    try:
        protection = variety_licensing_service.file_protection(**data.model_dump())
        return {"status": "success", "data": protection}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/protections/{protection_id}/grant")
async def grant_protection(protection_id: str, data: ProtectionGrant):
    """Record protection grant"""
    try:
        protection = variety_licensing_service.grant_protection(
            protection_id=protection_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": protection}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/protections")
async def list_protections(
    variety_id: Optional[str] = None,
    protection_type: Optional[str] = None,
    status: Optional[str] = None,
):
    """List protections with optional filters"""
    protections = variety_licensing_service.list_protections(
        variety_id=variety_id,
        protection_type=protection_type,
        status=status,
    )
    return {"status": "success", "data": protections, "count": len(protections)}


@router.get("/protections/{protection_id}")
async def get_protection(protection_id: str):
    """Get protection details"""
    protection = variety_licensing_service.get_protection(protection_id)
    if not protection:
        raise HTTPException(status_code=404, detail=f"Protection {protection_id} not found")
    return {"status": "success", "data": protection}


# License endpoints
@router.post("/licenses")
async def create_license(data: LicenseCreation):
    """Create a new license agreement"""
    try:
        license_agreement = variety_licensing_service.create_license(**data.model_dump())
        return {"status": "success", "data": license_agreement}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/licenses/{license_id}/activate")
async def activate_license(license_id: str):
    """Activate a license agreement"""
    try:
        license_agreement = variety_licensing_service.activate_license(license_id)
        return {"status": "success", "data": license_agreement}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/licenses/{license_id}/terminate")
async def terminate_license(license_id: str, reason: str = Query(...)):
    """Terminate a license agreement"""
    try:
        license_agreement = variety_licensing_service.terminate_license(license_id, reason)
        return {"status": "success", "data": license_agreement}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/licenses")
async def list_licenses(
    variety_id: Optional[str] = None,
    licensee_id: Optional[str] = None,
    license_type: Optional[str] = None,
    status: Optional[str] = None,
):
    """List licenses with optional filters"""
    licenses = variety_licensing_service.list_licenses(
        variety_id=variety_id,
        licensee_id=licensee_id,
        license_type=license_type,
        status=status,
    )
    return {"status": "success", "data": licenses, "count": len(licenses)}


@router.get("/licenses/{license_id}")
async def get_license(license_id: str):
    """Get license details"""
    license_agreement = variety_licensing_service.get_license(license_id)
    if not license_agreement:
        raise HTTPException(status_code=404, detail=f"License {license_id} not found")
    return {"status": "success", "data": license_agreement}


# Royalty endpoints
@router.post("/licenses/{license_id}/royalties")
async def record_royalty(license_id: str, data: RoyaltyRecord):
    """Record royalty payment for a license"""
    try:
        royalty = variety_licensing_service.record_royalty(
            license_id=license_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": royalty}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/varieties/{variety_id}/royalties")
async def get_royalty_summary(variety_id: str):
    """Get royalty summary for a variety"""
    summary = variety_licensing_service.get_royalty_summary(variety_id)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    return {"status": "success", "data": summary}


# Reference data endpoints
@router.get("/protection-types")
async def get_protection_types():
    """Get available protection types"""
    types = variety_licensing_service.get_protection_types()
    return {"status": "success", "data": types}


@router.get("/license-types")
async def get_license_types():
    """Get available license types"""
    types = variety_licensing_service.get_license_types()
    return {"status": "success", "data": types}


@router.get("/statistics")
async def get_statistics():
    """Get licensing statistics"""
    stats = variety_licensing_service.get_statistics()
    return {"status": "success", "data": stats}

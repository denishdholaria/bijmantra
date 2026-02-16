"""
BrAPI v2.1 Variants Endpoints
Genetic variants (SNPs, indels, etc.)

Database-backed implementation (no in-memory stores)
"""

from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.middleware.tenant_context import get_tenant_db
from app.services.genotyping import genotyping_service
from app.schemas.genotyping import VariantCreate, VariantUpdate
from app.models.genotyping import Variant

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Standard BrAPI response wrapper."""
    if isinstance(result, list):
        total = total if total is not None else len(result)
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {
                    "currentPage": page,
                    "pageSize": page_size,
                    "totalCount": total,
                    "totalPages": (total + page_size - 1) // page_size if total > 0 else 0
                },
                "status": [{"message": "Success", "messageType": "INFO"}]
            },
            "result": {"data": result}
        }
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": result
    }


def variant_to_brapi(variant: Variant) -> dict:
    """Convert Variant model to BrAPI format."""
    return {
        "variantDbId": variant.variant_db_id,
        "variantName": variant.variant_name,
        "variantSetDbId": [variant.variant_set.variant_set_db_id] if variant.variant_set else [],
        "variantType": variant.variant_type,
        "referenceName": variant.reference.reference_name if variant.reference else None,
        "referenceDbId": variant.reference.reference_db_id if variant.reference else None,
        "start": variant.start,
        "end": variant.end,
        "referenceBases": variant.reference_bases,
        "alternateBases": variant.alternate_bases or [],
        "cipos": variant.cipos,
        "ciend": variant.ciend,
        "svlen": variant.svlen,
        "filtersApplied": variant.filters_applied,
        "filtersPassed": variant.filters_passed,
        "filtersFailed": [],
        "created": variant.created_at.isoformat() if variant.created_at else None,
        "updated": variant.updated_at.isoformat() if variant.updated_at else None,
        "additionalInfo": variant.additional_info or {}
    }


@router.get("/variants")
async def get_variants(
    variantDbId: Optional[str] = None,
    variantSetDbId: Optional[str] = None,
    referenceDbId: Optional[str] = None,
    referenceName: Optional[str] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
    variantType: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_tenant_db)
):
    """Get a filtered list of variants."""
    variants, total = await genotyping_service.list_variants(
        db,
        variant_db_id=variantDbId,
        variant_set_db_id=variantSetDbId,
        reference_db_id=referenceDbId,
        reference_name=referenceName,
        start=start,
        end=end,
        variant_type=variantType,
        page=page,
        page_size=pageSize
    )

    data = [variant_to_brapi(v) for v in variants]
    return brapi_response(data, page, pageSize, total)


@router.get("/variants/{variantDbId}")
async def get_variant(
    variantDbId: str,
    db: AsyncSession = Depends(get_tenant_db)
):
    """Get a single variant by its ID."""
    variant = await genotyping_service.get_variant(db, variantDbId)

    if not variant:
        return {
            "metadata": {
                "status": [{"message": f"Variant {variantDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }

    return brapi_response(variant_to_brapi(variant))


@router.post("/variants")
async def create_variant(
    data: VariantCreate,
    db: AsyncSession = Depends(get_tenant_db)
):
    """Create a new variant."""
    variant = await genotyping_service.create_variant(db, data)
    return brapi_response(variant_to_brapi(variant))


@router.put("/variants/{variantDbId}")
async def update_variant(
    variantDbId: str,
    data: VariantUpdate,
    db: AsyncSession = Depends(get_tenant_db)
):
    """Update an existing variant."""
    variant = await genotyping_service.update_variant(db, variantDbId, data)

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant {variantDbId} not found"
        )

    return brapi_response(variant_to_brapi(variant))


@router.delete("/variants/{variantDbId}")
async def delete_variant(
    variantDbId: str,
    db: AsyncSession = Depends(get_tenant_db)
):
    """Delete a variant."""
    success = await genotyping_service.delete_variant(db, variantDbId)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant {variantDbId} not found"
        )

    return brapi_response({"message": f"Variant {variantDbId} deleted successfully"})


@router.get("/variants/{variantDbId}/calls")
async def get_variant_calls(
    variantDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_tenant_db)
):
    """Get the calls for a specific variant."""
    # Check if variant exists
    variant = await genotyping_service.get_variant(db, variantDbId)
    if not variant:
        return {
            "metadata": {
                "status": [{"message": f"Variant {variantDbId} not found", "messageType": "ERROR"}]
            },
            "result": {"data": []}
        }

    # Get calls
    calls, total = await genotyping_service.list_calls(
        db,
        variant_db_id=variantDbId,
        page=page,
        page_size=pageSize
    )

    # Convert to BrAPI format
    data = []
    for call in calls:
        data.append({
            "callSetDbId": call.call_set.call_set_db_id if call.call_set else None,
            "callSetName": call.call_set.call_set_name if call.call_set else None,
            "variantDbId": variantDbId,
            "variantName": variant.variant_name,
            "genotype": call.genotype,
            "genotype_value": call.genotype_value,
            "genotype_likelihood": call.genotype_likelihood,
            "phaseSet": call.phaseSet,
            "additionalInfo": call.additional_info or {}
        })

    return brapi_response(data, page, pageSize, total)

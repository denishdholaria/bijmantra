"""
BrAPI v2.1 VariantSets Endpoints
Variant sets (VCF file equivalents)

Database-backed implementation (no in-memory stores)
"""

from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.middleware.tenant_context import get_tenant_db
from app.services.genotyping import genotyping_service
from app.schemas.genotyping import VariantSetCreate, VariantSetUpdate
from app.models.genotyping import VariantSet, Variant, Call

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Wraps a result in the standard BrAPI response format."""
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


def variantset_to_brapi(vs: VariantSet) -> dict:
    """Converts a VariantSet model to its BrAPI representation."""
    return {
        "variantSetDbId": vs.variant_set_db_id,
        "variantSetName": vs.variant_set_name,
        "referenceSetDbId": vs.reference_set.reference_set_db_id if vs.reference_set else None,
        "studyDbId": vs.study.study_db_id if vs.study else None,
        "analysis": vs.analysis or [],
        "availableFormats": vs.available_formats or [],
        "callSetCount": vs.call_set_count,
        "variantCount": vs.variant_count,
        "additionalInfo": vs.additional_info or {}
    }


@router.get("/variantsets")
async def get_variantsets(
    variantSetDbId: Optional[str] = None,
    variantDbId: Optional[str] = None,
    callSetDbId: Optional[str] = None,
    referenceSetDbId: Optional[str] = None,
    studyDbId: Optional[str] = None,
    studyName: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_tenant_db)
):
    """Retrieves a list of variant sets filtered by the given parameters."""
    variantsets, total = await genotyping_service.list_variant_sets(
        db,
        variant_set_db_id=variantSetDbId,
        study_db_id=studyDbId,
        reference_set_db_id=referenceSetDbId,
        page=page,
        page_size=pageSize
    )
    
    data = [variantset_to_brapi(vs) for vs in variantsets]
    return brapi_response(data, page, pageSize, total)


@router.get("/variantsets/{variantSetDbId}")
async def get_variantset(
    variantSetDbId: str,
    db: AsyncSession = Depends(get_tenant_db)
):
    """Retrieves a single variant set by its ID."""
    variantset = await genotyping_service.get_variant_set(db, variantSetDbId)
    
    if not variantset:
        return {
            "metadata": {
                "status": [{"message": f"VariantSet {variantSetDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    return brapi_response(variantset_to_brapi(variantset))


@router.post("/variantsets")
async def create_variantset(
    data: VariantSetCreate,
    db: AsyncSession = Depends(get_tenant_db)
):
    """Create a new variant set."""
    variantset = await genotyping_service.create_variant_set(db, data)
    return brapi_response(variantset_to_brapi(variantset))


@router.put("/variantsets/{variantSetDbId}")
async def update_variantset(
    variantSetDbId: str,
    data: VariantSetUpdate,
    db: AsyncSession = Depends(get_tenant_db)
):
    """Update an existing variant set."""
    variantset = await genotyping_service.update_variant_set(db, variantSetDbId, data)

    if not variantset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VariantSet {variantSetDbId} not found"
        )

    return brapi_response(variantset_to_brapi(variantset))


@router.delete("/variantsets/{variantSetDbId}")
async def delete_variantset(
    variantSetDbId: str,
    db: AsyncSession = Depends(get_tenant_db)
):
    """Delete a variant set."""
    success = await genotyping_service.delete_variant_set(db, variantSetDbId)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VariantSet {variantSetDbId} not found"
        )

    return brapi_response({"message": f"VariantSet {variantSetDbId} deleted successfully"})


@router.get("/variantsets/{variantSetDbId}/calls")
async def get_variantset_calls(
    variantSetDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_tenant_db)
):
    """Retrieves the calls for a given variant set."""
    # Check if variant set exists
    variantset = await genotyping_service.get_variant_set(db, variantSetDbId)
    if not variantset:
        return {
            "metadata": {
                "status": [{"message": f"VariantSet {variantSetDbId} not found", "messageType": "ERROR"}]
            },
            "result": {"data": []}
        }

    # Get calls via service
    calls, total = await genotyping_service.list_calls(
        db,
        variant_set_db_id=variantSetDbId,
        page=page,
        page_size=pageSize
    )
    
    # Convert to BrAPI format
    data = []
    for call in calls:
        data.append({
            "callSetDbId": call.call_set.call_set_db_id if call.call_set else None,
            "callSetName": call.call_set.call_set_name if call.call_set else None,
            "variantDbId": call.variant.variant_db_id if call.variant else None,
            "variantName": call.variant.variant_name if call.variant else None,
            "genotype": call.genotype,
            "genotype_value": call.genotype_value,
            "genotype_likelihood": call.genotype_likelihood,
            "phaseSet": call.phaseSet,
            "additionalInfo": call.additional_info or {}
        })
    
    return brapi_response(data, page, pageSize, total)


@router.get("/variantsets/{variantSetDbId}/callsets")
async def get_variantset_callsets(
    variantSetDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_tenant_db)
):
    """Retrieves the call sets for a given variant set."""
    # Check exists
    variantset = await genotyping_service.get_variant_set(db, variantSetDbId)
    
    if not variantset:
        return {
            "metadata": {
                "status": [{"message": f"VariantSet {variantSetDbId} not found", "messageType": "ERROR"}]
            },
            "result": {"data": []}
        }
    
    # Reload with call_sets
    query = select(VariantSet).options(
        selectinload(VariantSet.call_sets)
    ).where(VariantSet.id == variantset.id)
    result = await db.execute(query)
    variantset = result.scalar_one()

    # Get call sets
    callsets = variantset.call_sets or []
    total = len(callsets)
    
    # Apply pagination
    start = page * pageSize
    end = start + pageSize
    paginated = callsets[start:end]
    
    # Convert to BrAPI format
    data = []
    for cs in paginated:
        data.append({
            "callSetDbId": cs.call_set_db_id,
            "callSetName": cs.call_set_name,
            "sampleDbId": cs.sample_db_id,
            "created": cs.created,
            "updated": cs.updated,
            "additionalInfo": cs.additional_info or {}
        })
    
    return brapi_response(data, page, pageSize, total)


@router.get("/variantsets/{variantSetDbId}/variants")
async def get_variantset_variants(
    variantSetDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_tenant_db)
):
    """Retrieves the variants for a given variant set."""
    # Use service method list_variants with filter
    variants, total = await genotyping_service.list_variants(
        db,
        variant_set_db_id=variantSetDbId,
        page=page,
        page_size=pageSize
    )
    
    # Local helper for conversion
    def variant_to_brapi_local(v):
        return {
            "variantDbId": v.variant_db_id,
            "variantName": v.variant_name,
            "variantSetDbId": [variantSetDbId],
            "variantType": v.variant_type,
            "referenceName": v.reference.reference_name if v.reference else None,
            "referenceDbId": v.reference.reference_db_id if v.reference else None,
            "start": v.start,
            "end": v.end,
            "referenceBases": v.reference_bases,
            "alternateBases": v.alternate_bases or [],
            "filtersApplied": v.filters_applied,
            "filtersPassed": v.filters_passed,
            "additionalInfo": v.additional_info or {}
        }

    data = [variant_to_brapi_local(v) for v in variants]
    
    return brapi_response(data, page, pageSize, total)


@router.post("/variantsets/extract")
async def extract_variantset(
    request: dict,
    db: AsyncSession = Depends(get_tenant_db)
):
    """Extracts a subset of variants and creates a new variant set."""
    return {
        "metadata": {
            "status": [{"message": "Extract functionality not yet implemented", "messageType": "INFO"}]
        },
        "result": {
            "extractDbId": None,
            "message": "Extract functionality is planned for future implementation"
        }
    }

"""
BrAPI v2.1 VariantSets Endpoints
Variant sets (VCF file equivalents)

Database-backed implementation (no in-memory stores)
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.core.database import get_db
from app.models.genotyping import VariantSet, Variant, CallSet, Call, ReferenceSet

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Wraps a result in the standard BrAPI response format.

    Args:
        result: The result data to be wrapped. Can be a list or a single object.
        page: The current page number.
        page_size: The number of items per page.
        total: The total number of items. If not provided for a list result,
               it will be calculated as the length of the list.

    Returns:
        A dictionary representing the standard BrAPI response.
    """
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
    """Converts a VariantSet model to its BrAPI representation.

    Args:
        vs: The VariantSet SQLAlchemy model instance.

    Returns:
        A dictionary representing the VariantSet in BrAPI format.
    """
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
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a list of variant sets filtered by the given parameters.

    Args:
        variantSetDbId: The ID of the variant set to retrieve.
        variantDbId: The ID of a variant to filter by.
        callSetDbId: The ID of a call set to filter by.
        referenceSetDbId: The ID of a reference set to filter by.
        studyDbId: The ID of a study to filter by.
        studyName: The name of a study to filter by.
        page: The page number to retrieve.
        pageSize: The number of items per page.
        db: The database session.

    Returns:
        A BrAPI response containing a list of variant sets.
    """
    # Build query
    query = select(VariantSet).options(
        selectinload(VariantSet.reference_set),
        selectinload(VariantSet.study)
    )
    
    # Apply filters
    if variantSetDbId:
        query = query.where(VariantSet.variant_set_db_id == variantSetDbId)
    if referenceSetDbId:
        query = query.join(ReferenceSet).where(ReferenceSet.reference_set_db_id == referenceSetDbId)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)
    
    # Execute query
    result = await db.execute(query)
    variantsets = result.scalars().all()
    
    # Convert to BrAPI format
    data = [variantset_to_brapi(vs) for vs in variantsets]
    
    return brapi_response(data, page, pageSize, total)


@router.get("/variantsets/{variantSetDbId}")
async def get_variantset(
    variantSetDbId: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a single variant set by its ID.

    Args:
        variantSetDbId: The ID of the variant set to retrieve.
        db: The database session.

    Returns:
        A BrAPI response containing the requested variant set, or a not found
        error if the variant set does not exist.
    """
    query = select(VariantSet).options(
        selectinload(VariantSet.reference_set),
        selectinload(VariantSet.study)
    ).where(VariantSet.variant_set_db_id == variantSetDbId)
    
    result = await db.execute(query)
    variantset = result.scalar_one_or_none()
    
    if not variantset:
        return {
            "metadata": {
                "status": [{"message": f"VariantSet {variantSetDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    return brapi_response(variantset_to_brapi(variantset))


@router.get("/variantsets/{variantSetDbId}/calls")
async def get_variantset_calls(
    variantSetDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves the calls for a given variant set.

    Args:
        variantSetDbId: The ID of the variant set.
        page: The page number to retrieve.
        pageSize: The number of items per page.
        db: The database session.

    Returns:
        A BrAPI response containing a list of calls for the variant set, or a
        not found error if the variant set does not exist.
    """
    # Get variant set
    vs_query = select(VariantSet).where(VariantSet.variant_set_db_id == variantSetDbId)
    vs_result = await db.execute(vs_query)
    variantset = vs_result.scalar_one_or_none()
    
    if not variantset:
        return {
            "metadata": {
                "status": [{"message": f"VariantSet {variantSetDbId} not found", "messageType": "ERROR"}]
            },
            "result": {"data": []}
        }
    
    # Get calls for variants in this variant set
    query = select(Call).options(
        selectinload(Call.call_set),
        selectinload(Call.variant)
    ).join(Variant).where(Variant.variant_set_id == variantset.id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)
    
    result = await db.execute(query)
    calls = result.scalars().all()
    
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
    db: AsyncSession = Depends(get_db)
):
    """Retrieves the call sets for a given variant set.

    Args:
        variantSetDbId: The ID of the variant set.
        page: The page number to retrieve.
        pageSize: The number of items per page.
        db: The database session.

    Returns:
        A BrAPI response containing a list of call sets for the variant set, or
        a not found error if the variant set does not exist.
    """
    # Get variant set
    vs_query = select(VariantSet).options(
        selectinload(VariantSet.call_sets)
    ).where(VariantSet.variant_set_db_id == variantSetDbId)
    vs_result = await db.execute(vs_query)
    variantset = vs_result.scalar_one_or_none()
    
    if not variantset:
        return {
            "metadata": {
                "status": [{"message": f"VariantSet {variantSetDbId} not found", "messageType": "ERROR"}]
            },
            "result": {"data": []}
        }
    
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
    db: AsyncSession = Depends(get_db)
):
    """Retrieves the variants for a given variant set.

    Args:
        variantSetDbId: The ID of the variant set.
        page: The page number to retrieve.
        pageSize: The number of items per page.
        db: The database session.

    Returns:
        A BrAPI response containing a list of variants for the variant set, or
        a not found error if the variant set does not exist.
    """
    # Get variant set
    vs_query = select(VariantSet).where(VariantSet.variant_set_db_id == variantSetDbId)
    vs_result = await db.execute(vs_query)
    variantset = vs_result.scalar_one_or_none()
    
    if not variantset:
        return {
            "metadata": {
                "status": [{"message": f"VariantSet {variantSetDbId} not found", "messageType": "ERROR"}]
            },
            "result": {"data": []}
        }
    
    # Get variants
    query = select(Variant).options(
        selectinload(Variant.reference)
    ).where(Variant.variant_set_id == variantset.id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)
    
    result = await db.execute(query)
    variants = result.scalars().all()
    
    # Convert to BrAPI format
    data = []
    for v in variants:
        data.append({
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
        })
    
    return brapi_response(data, page, pageSize, total)


@router.post("/variantsets/extract")
async def extract_variantset(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """Extracts a subset of variants and creates a new variant set.

    Note:
        This endpoint is a placeholder and is not yet implemented.

    Args:
        request: A dictionary containing the extraction parameters.
        db: The database session.

    Returns:
        A BrAPI response indicating that the functionality is not yet
        implemented.
    """
    return {
        "metadata": {
            "status": [{"message": "Extract functionality not yet implemented", "messageType": "INFO"}]
        },
        "result": {
            "extractDbId": None,
            "message": "Extract functionality is planned for future implementation"
        }
    }

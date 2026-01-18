"""
BrAPI v2.1 Variants Endpoints
Genetic variants (SNPs, indels, etc.)

Database-backed implementation (no in-memory stores)
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.models.genotyping import Variant, VariantSet, Reference, Call, CallSet

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Standard BrAPI response wrapper.

    Args:
        result (dict or list): The result data.
        page (int): The current page number.
        page_size (int): The number of items per page.
        total (int): The total number of items.

    Returns:
        A dictionary representing the BrAPI response.

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


def variant_to_brapi(variant: Variant) -> dict:
    """Convert Variant model to BrAPI format.

    Args:
        variant (Variant): The Variant object to convert.

    Returns:
        A dictionary representing the Variant in BrAPI format.

    """
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
    db: AsyncSession = Depends(get_db)
):
    """Get a filtered list of variants.

    Args:
        variantDbId (str): The ID of the variant to retrieve.
        variantSetDbId (str): The ID of the variant set to filter by.
        referenceDbId (str): The ID of the reference to filter by.
        referenceName (str): The name of the reference to filter by.
        start (int): The start position to filter by.
        end (int): The end position to filter by.
        variantType (str): The type of variant to filter by.
        page (int): The page number to return.
        pageSize (int): The number of items to return per page.
        db (AsyncSession): The database session.

    Returns:
        A BrAPI response containing a list of variants.

    """
    # Build query
    query = select(Variant).options(
        selectinload(Variant.variant_set),
        selectinload(Variant.reference)
    )
    
    # Apply filters
    if variantDbId:
        query = query.where(Variant.variant_db_id == variantDbId)
    if variantSetDbId:
        query = query.join(VariantSet).where(VariantSet.variant_set_db_id == variantSetDbId)
    if referenceDbId:
        query = query.join(Reference).where(Reference.reference_db_id == referenceDbId)
    if referenceName:
        query = query.join(Reference).where(Reference.reference_name == referenceName)
    if variantType:
        query = query.where(Variant.variant_type == variantType)
    if start is not None:
        query = query.where(Variant.start >= start)
    if end is not None:
        query = query.where(Variant.end <= end)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)
    
    # Execute query
    result = await db.execute(query)
    variants = result.scalars().all()
    
    # Convert to BrAPI format
    data = [variant_to_brapi(v) for v in variants]
    
    return brapi_response(data, page, pageSize, total)


@router.get("/variants/{variantDbId}")
async def get_variant(
    variantDbId: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a single variant by its ID.

    Args:
        variantDbId (str): The ID of the variant to retrieve.
        db (AsyncSession): The database session.

    Returns:
        A BrAPI response containing the variant.

    Raises:
        HTTPException: If the variant with the given ID is not found.

    """
    query = select(Variant).options(
        selectinload(Variant.variant_set),
        selectinload(Variant.reference)
    ).where(Variant.variant_db_id == variantDbId)
    
    result = await db.execute(query)
    variant = result.scalar_one_or_none()
    
    if not variant:
        return {
            "metadata": {
                "status": [{"message": f"Variant {variantDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    return brapi_response(variant_to_brapi(variant))


@router.get("/variants/{variantDbId}/calls")
async def get_variant_calls(
    variantDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Get the calls for a specific variant.

    Args:
        variantDbId (str): The ID of the variant to retrieve calls for.
        page (int): The page number to return.
        pageSize (int): The number of items to return per page.
        db (AsyncSession): The database session.

    Returns:
        A BrAPI response containing a list of calls for the variant.

    Raises:
        HTTPException: If the variant with the given ID is not found.

    """
    # Get variant
    variant_query = select(Variant).where(Variant.variant_db_id == variantDbId)
    variant_result = await db.execute(variant_query)
    variant = variant_result.scalar_one_or_none()
    
    if not variant:
        return {
            "metadata": {
                "status": [{"message": f"Variant {variantDbId} not found", "messageType": "ERROR"}]
            },
            "result": {"data": []}
        }
    
    # Get calls for this variant
    query = select(Call).options(
        selectinload(Call.call_set)
    ).where(Call.variant_id == variant.id)
    
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
            "variantDbId": variantDbId,
            "variantName": variant.variant_name,
            "genotype": call.genotype,
            "genotype_value": call.genotype_value,
            "genotype_likelihood": call.genotype_likelihood,
            "phaseSet": call.phaseSet,
            "additionalInfo": call.additional_info or {}
        })
    
    return brapi_response(data, page, pageSize, total)

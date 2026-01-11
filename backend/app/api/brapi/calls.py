"""
BrAPI v2.1 Calls Endpoints
Genotype calls for variants

Database-backed implementation (no in-memory stores)
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.models.genotyping import Call, CallSet, Variant

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Wraps results in a standard BrAPI v2.1 response object.

    Args:
        result: The result data to be returned. Can be a list or a single object.
        page: The current page number.
        page_size: The number of items per page.
        total: The total number of items. If not provided for a list result,
               it will be calculated as the length of the list.

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


def call_to_brapi(call: Call) -> dict:
    """Converts a Call SQLAlchemy model to a BrAPI-compliant dictionary.

    Args:
        call: The Call SQLAlchemy model instance.

    Returns:
        A dictionary representing the call in BrAPI format.
    """
    return {
        "callSetDbId": call.call_set.call_set_db_id if call.call_set else None,
        "callSetName": call.call_set.call_set_name if call.call_set else None,
        "variantDbId": call.variant.variant_db_id if call.variant else None,
        "variantName": call.variant.variant_name if call.variant else None,
        "genotype": call.genotype,
        "genotype_value": call.genotype_value,
        "genotype_likelihood": call.genotype_likelihood,
        "phaseSet": call.phaseSet,
        "additionalInfo": call.additional_info or {}
    }


@router.get("/calls")
async def get_calls(
    callSetDbId: Optional[str] = None,
    variantDbId: Optional[str] = None,
    variantSetDbId: Optional[str] = None,
    expandHomozygotes: Optional[bool] = None,
    unknownString: Optional[str] = None,
    sepPhased: Optional[str] = None,
    sepUnphased: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a filtered list of genotype calls.

    Args:
        callSetDbId: The ID of the call set to filter by.
        variantDbId: The ID of the variant to filter by.
        variantSetDbId: The ID of the variant set to filter by.
        expandHomozygotes: Whether to expand homozygotes. (Not implemented)
        unknownString: The string to use for unknown genotypes. (Not implemented)
        sepPhased: The separator for phased genotypes. (Not implemented)
        sepUnphased: The separator for unphased genotypes. (Not implemented)
        page: The page number to retrieve.
        pageSize: The number of items per page.
        db: The database session dependency.

    Returns:
        A BrAPI-compliant response containing a list of calls.
    """
    # Build query
    query = select(Call).options(
        selectinload(Call.call_set),
        selectinload(Call.variant)
    )
    
    # Apply filters
    if callSetDbId:
        query = query.join(CallSet).where(CallSet.call_set_db_id == callSetDbId)
    if variantDbId:
        query = query.join(Variant).where(Variant.variant_db_id == variantDbId)
    if variantSetDbId:
        query = query.join(Variant).where(Variant.variant_set_id == 
            select(Variant.variant_set_id).join(Variant.variant_set).where(
                Variant.variant_set.has(variant_set_db_id=variantSetDbId)
            ).scalar_subquery()
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)
    
    # Execute query
    result = await db.execute(query)
    calls = result.scalars().all()
    
    # Convert to BrAPI format
    data = [call_to_brapi(c) for c in calls]
    
    return brapi_response(data, page, pageSize, total)


@router.put("/calls")
async def update_calls(
    calls: List[dict],
    db: AsyncSession = Depends(get_db)
):
    """Updates existing genotype calls in bulk.

    Args:
        calls: A list of call objects to update. Each object must contain
               `callSetDbId` and `variantDbId` to identify the call.
        db: The database session dependency.

    Returns:
        A BrAPI-compliant response containing the updated calls.
    """
    updated = []
    
    for call_data in calls:
        call_set_db_id = call_data.get("callSetDbId")
        variant_db_id = call_data.get("variantDbId")
        
        if not call_set_db_id or not variant_db_id:
            continue
        
        # Find the call
        query = select(Call).join(CallSet).join(Variant, Call.variant_id == Variant.id).where(
            CallSet.call_set_db_id == call_set_db_id,
            Variant.variant_db_id == variant_db_id
        ).options(
            selectinload(Call.call_set),
            selectinload(Call.variant)
        )
        
        result = await db.execute(query)
        call = result.scalar_one_or_none()
        
        if call:
            # Update call
            if "genotype" in call_data:
                call.genotype = call_data["genotype"]
            if "genotype_value" in call_data:
                call.genotype_value = call_data["genotype_value"]
            if "genotype_likelihood" in call_data:
                call.genotype_likelihood = call_data["genotype_likelihood"]
            if "phaseSet" in call_data:
                call.phaseSet = call_data["phaseSet"]
            if "additionalInfo" in call_data:
                call.additional_info = call_data["additionalInfo"]
            
            updated.append(call_to_brapi(call))
    
    await db.commit()
    
    return brapi_response(updated)

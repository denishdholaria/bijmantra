"""
BrAPI v2.1 CallSets Endpoints
Call sets represent a collection of variant calls for a sample

Database-backed implementation (no in-memory stores)
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.models.genotyping import CallSet, Call, Variant, VariantSet

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Standard BrAPI response wrapper"""
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


def callset_to_brapi(callset: CallSet) -> dict:
    """Convert CallSet model to BrAPI format"""
    return {
        "callSetDbId": callset.call_set_db_id,
        "callSetName": callset.call_set_name,
        "sampleDbId": callset.sample_db_id,
        "variantSetDbIds": [vs.variant_set_db_id for vs in callset.variant_sets] if callset.variant_sets else [],
        "created": callset.created or (callset.created_at.isoformat() if callset.created_at else None),
        "updated": callset.updated or (callset.updated_at.isoformat() if callset.updated_at else None),
        "additionalInfo": callset.additional_info or {}
    }


@router.get("/callsets")
async def get_callsets(
    callSetDbId: Optional[str] = None,
    callSetName: Optional[str] = None,
    sampleDbId: Optional[str] = None,
    variantSetDbId: Optional[str] = None,
    germplasmDbId: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Get list of call sets"""
    # Build query
    query = select(CallSet).options(selectinload(CallSet.variant_sets))
    
    # Apply filters
    if callSetDbId:
        query = query.where(CallSet.call_set_db_id == callSetDbId)
    if callSetName:
        query = query.where(CallSet.call_set_name.ilike(f"%{callSetName}%"))
    if sampleDbId:
        query = query.where(CallSet.sample_db_id == sampleDbId)
    if variantSetDbId:
        query = query.join(CallSet.variant_sets).where(VariantSet.variant_set_db_id == variantSetDbId)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)
    
    # Execute query
    result = await db.execute(query)
    callsets = result.scalars().unique().all()
    
    # Convert to BrAPI format
    data = [callset_to_brapi(cs) for cs in callsets]
    
    return brapi_response(data, page, pageSize, total)


@router.get("/callsets/{callSetDbId}")
async def get_callset(
    callSetDbId: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a single call set by ID"""
    query = select(CallSet).options(
        selectinload(CallSet.variant_sets)
    ).where(CallSet.call_set_db_id == callSetDbId)
    
    result = await db.execute(query)
    callset = result.scalar_one_or_none()
    
    if not callset:
        return {
            "metadata": {
                "status": [{"message": f"CallSet {callSetDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    return brapi_response(callset_to_brapi(callset))


@router.get("/callsets/{callSetDbId}/calls")
async def get_callset_calls(
    callSetDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Get calls for a specific call set"""
    # Get call set
    callset_query = select(CallSet).where(CallSet.call_set_db_id == callSetDbId)
    callset_result = await db.execute(callset_query)
    callset = callset_result.scalar_one_or_none()
    
    if not callset:
        return {
            "metadata": {
                "status": [{"message": f"CallSet {callSetDbId} not found", "messageType": "ERROR"}]
            },
            "result": {"data": []}
        }
    
    # Get calls for this call set
    query = select(Call).options(
        selectinload(Call.variant)
    ).where(Call.call_set_id == callset.id)
    
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
            "callSetDbId": callSetDbId,
            "callSetName": callset.call_set_name,
            "variantDbId": call.variant.variant_db_id if call.variant else None,
            "variantName": call.variant.variant_name if call.variant else None,
            "genotype": call.genotype,
            "genotype_value": call.genotype_value,
            "genotype_likelihood": call.genotype_likelihood,
            "phaseSet": call.phaseSet,
            "additionalInfo": call.additional_info or {}
        })
    
    return brapi_response(data, page, pageSize, total)

"""
BrAPI Genotyping API
Endpoints for variant sets, calls, call sets, references, and marker positions
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.genotyping import genotyping_service
from app.schemas.genotyping import (
    VariantSetCreate,
    VendorOrderCreate,
    VendorOrderStatusUpdate
)
from app.api.v2.dependencies import get_current_user
from app.models.core import User

router = APIRouter(prefix="/genotyping", tags=["BrAPI Genotyping"])


# Helper for response formatting
def brapi_response(service_result: Dict):
    """Wraps service results in a standard BrAPI v2.1 response object."""
    return {
        "metadata": {
            "datafiles": [],
            "pagination": service_result.get("pagination", {}),
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": {"data": service_result.get("data", [])}
    }


# Variant Sets
@router.get("/variantsets")
async def list_variant_sets(
    variantSetDbId: Optional[str] = None,
    studyDbId: Optional[str] = None,
    referenceSetDbId: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List variant sets (BrAPI compliant)"""
    result = await genotyping_service.list_variant_sets(
        db=db,
        variant_set_db_id=variantSetDbId,
        study_db_id=studyDbId,
        reference_set_db_id=referenceSetDbId,
        page=page,
        page_size=pageSize,
    )
    return brapi_response(result)


@router.get("/variantsets/{variantSetDbId}")
async def get_variant_set(variantSetDbId: str, db: AsyncSession = Depends(get_db)):
    """Get a single variant set by ID"""
    result = await genotyping_service.get_variant_set(db, variantSetDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Variant set not found")
    return {"metadata": {}, "result": result}


@router.post("/variantsets")
async def create_variant_set(data: VariantSetCreate, db: AsyncSession = Depends(get_db)):
    """Create a new variant set"""
    result = await genotyping_service.create_variant_set(db, data.model_dump())
    return {"metadata": {}, "result": result}


# Call Sets
@router.get("/callsets")
async def list_call_sets(
    callSetDbId: Optional[str] = None,
    callSetName: Optional[str] = None,
    variantSetDbId: Optional[str] = None,
    sampleDbId: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List call sets (samples with genotype data)"""
    result = await genotyping_service.list_call_sets(
        db=db,
        call_set_db_id=callSetDbId,
        call_set_name=callSetName,
        variant_set_db_id=variantSetDbId,
        sample_db_id=sampleDbId,
        page=page,
        page_size=pageSize,
    )
    return brapi_response(result)


@router.get("/callsets/{callSetDbId}")
async def get_call_set(callSetDbId: str, db: AsyncSession = Depends(get_db)):
    """Get a single call set by ID"""
    result = await genotyping_service.get_call_set(db, callSetDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Call set not found")
    return {"metadata": {}, "result": result}


# Calls
@router.get("/calls")
async def list_calls(
    callSetDbId: Optional[str] = None,
    variantDbId: Optional[str] = None,
    variantSetDbId: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(100, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """List genotype calls"""
    result = await genotyping_service.list_calls(
        db=db,
        call_set_db_id=callSetDbId,
        variant_db_id=variantDbId,
        variant_set_db_id=variantSetDbId,
        page=page,
        page_size=pageSize,
    )
    return brapi_response(result)


@router.get("/calls/statistics")
async def get_calls_statistics(variantSetDbId: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Get statistics for genotype calls"""
    result = await genotyping_service.get_calls_statistics(db, variant_set_db_id=variantSetDbId)
    return {"metadata": {}, "result": result}


# References
@router.get("/references")
async def list_references(
    referenceDbId: Optional[str] = None,
    referenceSetDbId: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List references (chromosomes/contigs)"""
    result = await genotyping_service.list_references(
        db=db,
        reference_db_id=referenceDbId,
        reference_set_db_id=referenceSetDbId,
        page=page,
        page_size=pageSize,
    )
    return brapi_response(result)


@router.get("/references/{referenceDbId}")
async def get_reference(referenceDbId: str, db: AsyncSession = Depends(get_db)):
    """Get a single reference by ID"""
    result = await genotyping_service.get_reference(db, referenceDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Reference not found")
    return {"metadata": {}, "result": result}


# Reference Sets
@router.get("/referencesets")
async def list_reference_sets(
    referenceSetDbId: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List reference sets (genomes)"""
    result = await genotyping_service.list_reference_sets(
        db=db,
        reference_set_db_id=referenceSetDbId,
        page=page,
        page_size=pageSize,
    )
    return brapi_response(result)


# Marker Positions
@router.get("/markerpositions")
async def list_marker_positions(
    mapDbId: Optional[str] = None,
    linkageGroupName: Optional[str] = None,
    minPosition: Optional[float] = None,
    maxPosition: Optional[float] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(100, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """List marker positions on linkage maps"""
    result = await genotyping_service.list_marker_positions(
        db=db,
        map_db_id=mapDbId,
        linkage_group_name=linkageGroupName,
        min_position=minPosition,
        max_position=maxPosition,
        page=page,
        page_size=pageSize,
    )
    return brapi_response(result)


# Vendor Orders
@router.get("/vendor/orders")
async def list_vendor_orders(
    vendorOrderDbId: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List vendor orders for genotyping services"""
    result = await genotyping_service.list_vendor_orders(
        db=db,
        vendor_order_db_id=vendorOrderDbId,
        status=status,
        page=page,
        page_size=pageSize,
    )
    return brapi_response(result)


@router.get("/vendor/orders/{vendorOrderDbId}")
async def get_vendor_order(vendorOrderDbId: str, db: AsyncSession = Depends(get_db)):
    """Get a single vendor order by ID"""
    result = await genotyping_service.get_vendor_order(db, vendorOrderDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Vendor order not found")
    return {"metadata": {}, "result": result}


@router.post("/vendor/orders")
async def create_vendor_order(
    data: VendorOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new vendor order"""
    # Use by_alias=True to pass camelCase keys to the service (e.g., clientId instead of client_id)
    result = await genotyping_service.create_vendor_order(
        db,
        data.model_dump(by_alias=True),
        organization_id=current_user.organization_id
    )
    return {"metadata": {}, "result": result}


@router.put("/vendor/orders/{vendorOrderDbId}/status")
async def update_vendor_order_status(vendorOrderDbId: str, data: VendorOrderStatusUpdate, db: AsyncSession = Depends(get_db)):
    """Update vendor order status"""
    result = await genotyping_service.update_vendor_order_status(db, vendorOrderDbId, data.status)
    if not result:
        raise HTTPException(status_code=404, detail="Vendor order not found")
    return {"metadata": {}, "result": result}


# Summary endpoint
@router.get("/summary")
async def get_genotyping_summary(db: AsyncSession = Depends(get_db)):
    """Get summary of all genotyping data"""
    variant_sets = await genotyping_service.list_variant_sets(db, page_size=1000)
    call_sets = await genotyping_service.list_call_sets(db, page_size=1000)
    references = await genotyping_service.list_references(db, page_size=1000)
    reference_sets = await genotyping_service.list_reference_sets(db, page_size=1000)
    calls_stats = await genotyping_service.get_calls_statistics(db)
    vendor_orders = await genotyping_service.list_vendor_orders(db, page_size=1000)
    
    return {
        "metadata": {},
        "result": {
            "variantSets": variant_sets["pagination"]["totalCount"],
            "callSets": call_sets["pagination"]["totalCount"],
            "references": references["pagination"]["totalCount"],
            "referenceSets": reference_sets["pagination"]["totalCount"],
            "totalCalls": calls_stats["total"],
            "vendorOrders": vendor_orders["pagination"]["totalCount"],
            "callsStatistics": calls_stats,
        },
    }

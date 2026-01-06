"""
BrAPI Genotyping API
Endpoints for variant sets, calls, call sets, references, and marker positions
"""
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.services.genotyping import genotyping_service

router = APIRouter(prefix="/genotyping", tags=["BrAPI Genotyping"])


# Pydantic models
class VariantSetCreate(BaseModel):
    variantSetName: str
    studyDbId: Optional[str] = None
    studyName: Optional[str] = None
    referenceSetDbId: Optional[str] = None
    variantCount: int = 0
    callSetCount: int = 0


class VendorOrderCreate(BaseModel):
    clientId: str
    numberOfSamples: int
    serviceIds: List[str]
    requiredServiceInfo: Optional[dict] = None


class VendorOrderStatusUpdate(BaseModel):
    status: str


# Variant Sets
@router.get("/variantsets")
async def list_variant_sets(
    variantSetDbId: Optional[str] = None,
    studyDbId: Optional[str] = None,
    referenceSetDbId: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
):
    """List variant sets (BrAPI compliant)"""
    result = genotyping_service.list_variant_sets(
        variant_set_db_id=variantSetDbId,
        study_db_id=studyDbId,
        reference_set_db_id=referenceSetDbId,
        page=page,
        page_size=pageSize,
    )
    return {
        "metadata": {"pagination": result["pagination"]},
        "result": {"data": result["data"]},
    }


@router.get("/variantsets/{variantSetDbId}")
async def get_variant_set(variantSetDbId: str):
    """Get a single variant set by ID"""
    result = genotyping_service.get_variant_set(variantSetDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Variant set not found")
    return {"metadata": {}, "result": result}


@router.post("/variantsets")
async def create_variant_set(data: VariantSetCreate):
    """Create a new variant set"""
    result = genotyping_service.create_variant_set(data.model_dump())
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
):
    """List call sets (samples with genotype data)"""
    result = genotyping_service.list_call_sets(
        call_set_db_id=callSetDbId,
        call_set_name=callSetName,
        variant_set_db_id=variantSetDbId,
        sample_db_id=sampleDbId,
        page=page,
        page_size=pageSize,
    )
    return {
        "metadata": {"pagination": result["pagination"]},
        "result": {"data": result["data"]},
    }


@router.get("/callsets/{callSetDbId}")
async def get_call_set(callSetDbId: str):
    """Get a single call set by ID"""
    result = genotyping_service.get_call_set(callSetDbId)
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
):
    """List genotype calls"""
    result = genotyping_service.list_calls(
        call_set_db_id=callSetDbId,
        variant_db_id=variantDbId,
        variant_set_db_id=variantSetDbId,
        page=page,
        page_size=pageSize,
    )
    return {
        "metadata": {"pagination": result["pagination"]},
        "result": {"data": result["data"]},
    }


@router.get("/calls/statistics")
async def get_calls_statistics(variantSetDbId: Optional[str] = None):
    """Get statistics for genotype calls"""
    result = genotyping_service.get_calls_statistics(variant_set_db_id=variantSetDbId)
    return {"metadata": {}, "result": result}


# References
@router.get("/references")
async def list_references(
    referenceDbId: Optional[str] = None,
    referenceSetDbId: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
):
    """List references (chromosomes/contigs)"""
    result = genotyping_service.list_references(
        reference_db_id=referenceDbId,
        reference_set_db_id=referenceSetDbId,
        page=page,
        page_size=pageSize,
    )
    return {
        "metadata": {"pagination": result["pagination"]},
        "result": {"data": result["data"]},
    }


@router.get("/references/{referenceDbId}")
async def get_reference(referenceDbId: str):
    """Get a single reference by ID"""
    result = genotyping_service.get_reference(referenceDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Reference not found")
    return {"metadata": {}, "result": result}


# Reference Sets
@router.get("/referencesets")
async def list_reference_sets(
    referenceSetDbId: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
):
    """List reference sets (genomes)"""
    result = genotyping_service.list_reference_sets(
        reference_set_db_id=referenceSetDbId,
        page=page,
        page_size=pageSize,
    )
    return {
        "metadata": {"pagination": result["pagination"]},
        "result": {"data": result["data"]},
    }


# Marker Positions
@router.get("/markerpositions")
async def list_marker_positions(
    mapDbId: Optional[str] = None,
    linkageGroupName: Optional[str] = None,
    minPosition: Optional[float] = None,
    maxPosition: Optional[float] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(100, ge=1, le=10000),
):
    """List marker positions on linkage maps"""
    result = genotyping_service.list_marker_positions(
        map_db_id=mapDbId,
        linkage_group_name=linkageGroupName,
        min_position=minPosition,
        max_position=maxPosition,
        page=page,
        page_size=pageSize,
    )
    return {
        "metadata": {"pagination": result["pagination"]},
        "result": {"data": result["data"]},
    }


# Vendor Orders
@router.get("/vendor/orders")
async def list_vendor_orders(
    vendorOrderDbId: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
):
    """List vendor orders for genotyping services"""
    result = genotyping_service.list_vendor_orders(
        vendor_order_db_id=vendorOrderDbId,
        status=status,
        page=page,
        page_size=pageSize,
    )
    return {
        "metadata": {"pagination": result["pagination"]},
        "result": {"data": result["data"]},
    }


@router.get("/vendor/orders/{vendorOrderDbId}")
async def get_vendor_order(vendorOrderDbId: str):
    """Get a single vendor order by ID"""
    result = genotyping_service.get_vendor_order(vendorOrderDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Vendor order not found")
    return {"metadata": {}, "result": result}


@router.post("/vendor/orders")
async def create_vendor_order(data: VendorOrderCreate):
    """Create a new vendor order"""
    result = genotyping_service.create_vendor_order(data.model_dump())
    return {"metadata": {}, "result": result}


@router.put("/vendor/orders/{vendorOrderDbId}/status")
async def update_vendor_order_status(vendorOrderDbId: str, data: VendorOrderStatusUpdate):
    """Update vendor order status"""
    result = genotyping_service.update_vendor_order_status(vendorOrderDbId, data.status)
    if not result:
        raise HTTPException(status_code=404, detail="Vendor order not found")
    return {"metadata": {}, "result": result}


# Summary endpoint
@router.get("/summary")
async def get_genotyping_summary():
    """Get summary of all genotyping data"""
    variant_sets = genotyping_service.list_variant_sets(page_size=1000)
    call_sets = genotyping_service.list_call_sets(page_size=1000)
    references = genotyping_service.list_references(page_size=1000)
    reference_sets = genotyping_service.list_reference_sets(page_size=1000)
    calls_stats = genotyping_service.get_calls_statistics()
    vendor_orders = genotyping_service.list_vendor_orders(page_size=1000)
    
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

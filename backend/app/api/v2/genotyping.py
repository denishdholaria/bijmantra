"""
BrAPI Genotyping API
Endpoints for variant sets, calls, call sets, references, and marker positions
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.dependencies import get_current_user
from app.core.database import get_db
from app.models.core import User
from app.modules.genotyping.schemas import VCFImportResponse
from app.modules.genotyping.services.vcf_import import vcf_service
from app.schemas.genotyping import VariantSetCreate, VendorOrderCreate, VendorOrderStatusUpdate
from app.services.genotyping import genotyping_service


router = APIRouter(prefix="/genotyping", tags=["BrAPI Genotyping"], dependencies=[Depends(get_current_user)])


# Helper for response formatting
def brapi_response(data: list, page: int, page_size: int, total_count: int):
    """Wraps service results in a standard BrAPI v2.1 response object."""
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total_count,
                "totalPages": total_pages
            },
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": {"data": data}
    }


# Converters
def variant_set_to_dict(item):
    if not item:
        return None
    return {
        "variantSetDbId": item.variant_set_db_id,
        "variantSetName": item.variant_set_name,
        "studyDbId": item.study.study_db_id if item.study else None,
        "studyName": item.study.study_name if item.study else None,
        "referenceSetDbId": item.reference_set.reference_set_db_id if item.reference_set else None,
        "variantCount": item.variant_count,
        "callSetCount": item.call_set_count,
        "additionalInfo": item.additional_info
    }

def call_set_to_dict(item):
    if not item:
        return None
    return {
        "callSetDbId": item.call_set_db_id,
        "callSetName": item.call_set_name,
        "sampleDbId": item.sample_db_id,
        "variantSetDbIds": [vs.variant_set_db_id for vs in item.variant_sets],
        "created": item.created,
        "updated": item.updated,
        "additionalInfo": item.additional_info
    }

def call_to_dict(item):
    if not item:
        return None
    return {
        "callSetDbId": item.call_set.call_set_db_id if item.call_set else None,
        "callSetName": item.call_set.call_set_name if item.call_set else None,
        "variantDbId": item.variant.variant_db_id if item.variant else None,
        "variantName": item.variant.variant_name if item.variant else None,
        "genotype": item.genotype,
        "genotypeValue": item.genotype_value,
        "genotypeLikelihood": item.genotype_likelihood,
        "phaseSet": item.phaseSet,
        "additionalInfo": item.additional_info
    }

def reference_to_dict(item):
    if not item:
        return None
    return {
        "referenceDbId": item.reference_db_id,
        "referenceName": item.reference_name,
        "referenceSetDbId": str(item.reference_set_id) if item.reference_set_id else None,
        "length": item.length,
        "md5checksum": item.md5checksum,
        "sourceURI": item.source_uri,
        "isDerived": item.is_derived,
    }

def reference_set_to_dict(item):
    if not item:
        return None
    return {
        "referenceSetDbId": item.reference_set_db_id,
        "referenceSetName": item.reference_set_name,
        "description": item.description,
    }

def marker_position_to_dict(item):
    if not item:
        return None
    return {
        "markerPositionDbId": item.marker_position_db_id,
        "variantDbId": item.variant_db_id,
        "variantName": item.variant_name,
        "linkageGroupName": item.linkage_group_name,
        "position": item.position,
    }

def vendor_order_to_dict(item):
    if not item:
        return None
    return {
        "vendorOrderDbId": item.order_db_id,
        "clientId": item.client_id,
        "numberOfSamples": item.number_of_samples,
        "orderId": item.order_id,
        "serviceIds": item.service_ids,
        "status": item.status,
        "statusTimeStamp": item.status_time_stamp
    }


# Variant Sets
@router.get("/variantsets")
async def list_variant_sets(
    variantSetDbId: str | None = None,
    studyDbId: str | None = None,
    referenceSetDbId: str | None = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List variant sets (BrAPI compliant)"""
    items, total = await genotyping_service.list_variant_sets(
        db=db,
        variant_set_db_id=variantSetDbId,
        study_db_id=studyDbId,
        reference_set_db_id=referenceSetDbId,
        page=page,
        page_size=pageSize,
    )
    data = [variant_set_to_dict(item) for item in items]
    return brapi_response(data, page, pageSize, total)


@router.get("/variantsets/{variantSetDbId}")
async def get_variant_set(variantSetDbId: str, db: AsyncSession = Depends(get_db)):
    """Get a single variant set by ID"""
    result = await genotyping_service.get_variant_set(db, variantSetDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Variant set not found")
    return {"metadata": {}, "result": variant_set_to_dict(result)}


@router.post("/variantsets")
async def create_variant_set(
    data: VariantSetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new variant set"""
    result = await genotyping_service.create_variant_set(
        db,
        data,
        organization_id=current_user.organization_id
    )
    return {"metadata": {}, "result": variant_set_to_dict(result)}


# Data Import
@router.post("/import", response_model=VCFImportResponse)
async def import_vcf(
    variant_set_name: str = Form(...),
    study_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Import a VCF file (Variant Call Format).
    Converts data to Zarr format for high-performance analysis.
    """
    if not file.filename.endswith(('.vcf', '.vcf.gz')):
        raise HTTPException(status_code=400, detail="Invalid file format. Must be .vcf or .vcf.gz")

    result = await vcf_service.import_vcf(
        db=db,
        user=user,
        variant_set_name=variant_set_name,
        vcf_file=file,
        study_id=study_id
    )

    return {
        "success": True,
        "job_id": str(result.get("variant_set_id")),
        "message": "VCF imported successfully",
        "variant_set_id": result.get("variant_set_id"),
        "sample_count": result.get("sample_count"),
        "variant_count": result.get("variant_count")
    }


# Call Sets
@router.get("/callsets")
async def list_call_sets(
    callSetDbId: str | None = None,
    callSetName: str | None = None,
    variantSetDbId: str | None = None,
    sampleDbId: str | None = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List call sets (samples with genotype data)"""
    items, total = await genotyping_service.list_call_sets(
        db=db,
        call_set_db_id=callSetDbId,
        call_set_name=callSetName,
        variant_set_db_id=variantSetDbId,
        sample_db_id=sampleDbId,
        page=page,
        page_size=pageSize,
    )
    data = [call_set_to_dict(item) for item in items]
    return brapi_response(data, page, pageSize, total)


@router.get("/callsets/{callSetDbId}")
async def get_call_set(callSetDbId: str, db: AsyncSession = Depends(get_db)):
    """Get a single call set by ID"""
    result = await genotyping_service.get_call_set(db, callSetDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Call set not found")
    return {"metadata": {}, "result": call_set_to_dict(result)}


# Calls
@router.get("/calls")
async def list_calls(
    callSetDbId: str | None = None,
    variantDbId: str | None = None,
    variantSetDbId: str | None = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(100, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """List genotype calls"""
    items, total = await genotyping_service.list_calls(
        db=db,
        call_set_db_id=callSetDbId,
        variant_db_id=variantDbId,
        variant_set_db_id=variantSetDbId,
        page=page,
        page_size=pageSize,
    )
    data = [call_to_dict(item) for item in items]
    return brapi_response(data, page, pageSize, total)


@router.get("/calls/statistics")
async def get_calls_statistics(variantSetDbId: str | None = None, db: AsyncSession = Depends(get_db)):
    """Get statistics for genotype calls"""
    result = await genotyping_service.get_calls_statistics(db, variant_set_db_id=variantSetDbId)
    return {"metadata": {}, "result": result}


# References
@router.get("/references")
async def list_references(
    referenceDbId: str | None = None,
    referenceSetDbId: str | None = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List references (chromosomes/contigs)"""
    items, total = await genotyping_service.list_references(
        db=db,
        reference_db_id=referenceDbId,
        reference_set_db_id=referenceSetDbId,
        page=page,
        page_size=pageSize,
    )
    data = [reference_to_dict(item) for item in items]
    return brapi_response(data, page, pageSize, total)


@router.get("/references/{referenceDbId}")
async def get_reference(referenceDbId: str, db: AsyncSession = Depends(get_db)):
    """Get a single reference by ID"""
    result = await genotyping_service.get_reference(db, referenceDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Reference not found")
    return {"metadata": {}, "result": reference_to_dict(result)}


# Reference Sets
@router.get("/referencesets")
async def list_reference_sets(
    referenceSetDbId: str | None = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List reference sets (genomes)"""
    items, total = await genotyping_service.list_reference_sets(
        db=db,
        reference_set_db_id=referenceSetDbId,
        page=page,
        page_size=pageSize,
    )
    data = [reference_set_to_dict(item) for item in items]
    return brapi_response(data, page, pageSize, total)


# Marker Positions
@router.get("/markerpositions")
async def list_marker_positions(
    mapDbId: str | None = None,
    linkageGroupName: str | None = None,
    minPosition: float | None = None,
    maxPosition: float | None = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(100, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """List marker positions on linkage maps"""
    items, total = await genotyping_service.list_marker_positions(
        db=db,
        map_db_id=mapDbId,
        linkage_group_name=linkageGroupName,
        min_position=minPosition,
        max_position=maxPosition,
        page=page,
        page_size=pageSize,
    )
    data = [marker_position_to_dict(item) for item in items]
    return brapi_response(data, page, pageSize, total)


# Vendor Orders
@router.get("/vendor/orders")
async def list_vendor_orders(
    vendorOrderDbId: str | None = None,
    status: str | None = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List vendor orders for genotyping services"""
    items, total = await genotyping_service.list_vendor_orders(
        db=db,
        vendor_order_db_id=vendorOrderDbId,
        status=status,
        page=page,
        page_size=pageSize,
    )
    data = [vendor_order_to_dict(item) for item in items]
    return brapi_response(data, page, pageSize, total)


@router.get("/vendor/orders/{vendorOrderDbId}")
async def get_vendor_order(vendorOrderDbId: str, db: AsyncSession = Depends(get_db)):
    """Get a single vendor order by ID"""
    result = await genotyping_service.get_vendor_order(db, vendorOrderDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Vendor order not found")
    return {"metadata": {}, "result": vendor_order_to_dict(result)}


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
    return {"metadata": {}, "result": vendor_order_to_dict(result)}


@router.put("/vendor/orders/{vendorOrderDbId}/status")
async def update_vendor_order_status(vendorOrderDbId: str, data: VendorOrderStatusUpdate, db: AsyncSession = Depends(get_db)):
    """Update vendor order status"""
    result = await genotyping_service.update_vendor_order_status(db, vendorOrderDbId, data.status)
    if not result:
        raise HTTPException(status_code=404, detail="Vendor order not found")
    return {"metadata": {}, "result": vendor_order_to_dict(result)}


# Summary endpoint
@router.get("/summary")
async def get_genotyping_summary(db: AsyncSession = Depends(get_db)):
    """Get summary of all genotyping data"""
    variant_sets_items, variant_sets_total = await genotyping_service.list_variant_sets(db, page_size=1)
    call_sets_items, call_sets_total = await genotyping_service.list_call_sets(db, page_size=1)
    references_items, references_total = await genotyping_service.list_references(db, page_size=1)
    reference_sets_items, reference_sets_total = await genotyping_service.list_reference_sets(db, page_size=1)
    calls_stats = await genotyping_service.get_calls_statistics(db)
    vendor_orders_items, vendor_orders_total = await genotyping_service.list_vendor_orders(db, page_size=1)

    return {
        "metadata": {},
        "result": {
            "variantSets": variant_sets_total,
            "callSets": call_sets_total,
            "references": references_total,
            "referenceSets": reference_sets_total,
            "totalCalls": calls_stats["total"],
            "vendorOrders": vendor_orders_total,
            "callsStatistics": calls_stats,
        },
    }

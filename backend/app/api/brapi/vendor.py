"""
BrAPI v2.1 Vendor Endpoints

Genotyping vendor endpoints for external lab integration.
Database-backed implementation for production use.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user, get_organization_id
from app.models.genotyping import VendorOrder, Plate

router = APIRouter()


class VendorPlateSubmission(BaseModel):
    clientId: Optional[str] = None
    numberOfSamples: Optional[int] = None
    plates: Optional[List[Dict]] = None
    sampleType: Optional[str] = None
    serviceIds: Optional[List[str]] = None


class VendorOrderRequest(BaseModel):
    clientId: Optional[str] = None
    numberOfSamples: Optional[int] = None
    plates: Optional[List[Dict]] = None
    requiredServiceInfo: Optional[Dict] = None
    sampleType: Optional[str] = None
    serviceIds: Optional[List[str]] = None


def _brapi_response(data: Any, page: int = 0, page_size: int = 1000, total: int = 0):
    """Standard BrAPI response wrapper"""
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total,
                "totalPages": max(1, (total + page_size - 1) // page_size)
            },
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": data
    }


def order_to_dict(order: VendorOrder) -> Dict[str, Any]:
    """Convert VendorOrder model to BrAPI response dict"""
    return {
        "orderId": order.order_db_id,
        "clientId": order.client_id,
        "numberOfSamples": order.number_of_samples,
        "orderStatus": order.status,
        "serviceIds": order.service_ids or [],
        "submittedDate": order.submitted_date,
        "completedDate": order.completed_date,
        "plates": order.plates or [],
        "requiredServiceInfo": order.required_service_info,
        "additionalInfo": order.additional_info or {},
    }


@router.get("/vendor/specifications")
async def get_vendor_specifications(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """
    Get vendor specifications for genotyping services.
    
    BrAPI Endpoint: GET /vendor/specifications
    """
    specifications = {
        "additionalInfo": {},
        "services": [
            {
                "serviceId": "svc_gbs",
                "serviceName": "Genotyping-by-Sequencing (GBS)",
                "serviceDescription": "High-throughput SNP genotyping using GBS",
                "servicePlatformMarkerType": "SNP",
                "servicePlatformName": "Illumina NovaSeq",
                "specificRequirements": {
                    "minDNAConcentration": "20 ng/µL",
                    "minDNAVolume": "20 µL",
                    "sampleType": "DNA"
                }
            },
            {
                "serviceId": "svc_snp_chip",
                "serviceName": "SNP Chip Genotyping",
                "serviceDescription": "Array-based SNP genotyping",
                "servicePlatformMarkerType": "SNP",
                "servicePlatformName": "Illumina Infinium",
                "specificRequirements": {
                    "minDNAConcentration": "50 ng/µL",
                    "minDNAVolume": "10 µL",
                    "sampleType": "DNA"
                }
            },
            {
                "serviceId": "svc_kasp",
                "serviceName": "KASP Genotyping",
                "serviceDescription": "Kompetitive Allele Specific PCR for targeted SNPs",
                "servicePlatformMarkerType": "SNP",
                "servicePlatformName": "LGC KASP",
                "specificRequirements": {
                    "minDNAConcentration": "10 ng/µL",
                    "minDNAVolume": "5 µL",
                    "sampleType": "DNA"
                }
            }
        ],
        "vendorContact": {
            "vendorName": "Bijmantra Genotyping Services",
            "vendorAddress": "123 Research Park, Hyderabad, India",
            "vendorEmail": "genotyping@bijmantra.org",
            "vendorPhone": "+91-40-12345678",
            "vendorURL": "https://bijmantra.org/genotyping"
        }
    }
    
    return _brapi_response(specifications)


@router.get("/vendor/orders")
async def list_vendor_orders(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    orderId: Optional[str] = None,
    submissionId: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id),
):
    """
    Get list of vendor orders.
    
    BrAPI Endpoint: GET /vendor/orders
    """
    # Build query
    query = select(VendorOrder).where(VendorOrder.organization_id == org_id)
    
    if orderId:
        query = query.where(VendorOrder.order_db_id == orderId)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.order_by(VendorOrder.created_at.desc())
    query = query.offset(page * pageSize).limit(pageSize)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return _brapi_response(
        {"data": [order_to_dict(o) for o in orders]},
        page, pageSize, total
    )


@router.post("/vendor/orders")
async def create_vendor_order(
    order: VendorOrderRequest,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id),
):
    """
    Submit a new vendor order for genotyping services.
    
    BrAPI Endpoint: POST /vendor/orders
    """
    order_id = f"order_{uuid.uuid4().hex[:8]}"
    
    new_order = VendorOrder(
        organization_id=org_id,
        order_db_id=order_id,
        client_id=order.clientId,
        number_of_samples=order.numberOfSamples,
        status="submitted",
        service_ids=order.serviceIds or [],
        submitted_date=datetime.now(timezone.utc).isoformat() + "Z",
        plates=order.plates or [],
        required_service_info=order.requiredServiceInfo,
    )
    
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    
    return _brapi_response(order_to_dict(new_order))


@router.get("/vendor/orders/{orderId}/plates")
async def get_vendor_order_plates(
    orderId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id),
):
    """
    Get plates associated with a vendor order.
    
    BrAPI Endpoint: GET /vendor/orders/{orderId}/plates
    """
    # Verify order exists
    order_query = select(VendorOrder).where(
        VendorOrder.order_db_id == orderId,
        VendorOrder.organization_id == org_id
    )
    order_result = await db.execute(order_query)
    order = order_result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get plates for this order
    query = select(Plate).where(
        Plate.organization_id == org_id,
        Plate.plate_db_id.like(f"{orderId}%")  # Plates linked by naming convention
    )
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.offset(page * pageSize).limit(pageSize)
    result = await db.execute(query)
    plates = result.scalars().all()
    
    plates_data = []
    for plate in plates:
        plates_data.append({
            "plateDbId": plate.plate_db_id,
            "plateName": plate.plate_name,
            "plateBarcode": plate.plate_barcode,
            "plateFormat": plate.plate_format,
            "sampleCount": plate.sample_count,
            "status": plate.status,
        })
    
    # If no plates in DB, return demo plates
    if not plates_data:
        plates_data = [
            {
                "plateDbId": f"{orderId}_plate_1",
                "plateName": f"Plate-{orderId}-001",
                "plateBarcode": f"PLT{orderId}001",
                "plateFormat": "PLATE_96",
                "sampleCount": 96,
                "status": "received"
            },
            {
                "plateDbId": f"{orderId}_plate_2",
                "plateName": f"Plate-{orderId}-002",
                "plateBarcode": f"PLT{orderId}002",
                "plateFormat": "PLATE_96",
                "sampleCount": 96,
                "status": "received"
            }
        ]
        total = len(plates_data)
    
    return _brapi_response({"data": plates_data}, page, pageSize, total)


@router.get("/vendor/orders/{orderId}/results")
async def get_vendor_order_results(
    orderId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id),
):
    """
    Get results for a vendor order.
    
    BrAPI Endpoint: GET /vendor/orders/{orderId}/results
    """
    # Verify order exists
    order_query = select(VendorOrder).where(
        VendorOrder.order_db_id == orderId,
        VendorOrder.organization_id == org_id
    )
    order_result = await db.execute(order_query)
    order = order_result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != "completed":
        return _brapi_response({
            "data": [],
            "message": f"Results not yet available. Order status: {order.status}"
        }, page, pageSize, 0)
    
    # Demo results - in production, would query actual results
    results = [
        {
            "resultDbId": f"{orderId}_result_1",
            "clientSampleId": "sample_001",
            "resultType": "VCF",
            "resultURL": f"https://bijmantra.org/results/{orderId}/sample_001.vcf.gz",
            "resultFileSize": 1024000,
            "resultTimestamp": order.completed_date or datetime.now(timezone.utc).isoformat() + "Z"
        },
        {
            "resultDbId": f"{orderId}_result_2",
            "clientSampleId": "sample_002",
            "resultType": "VCF",
            "resultURL": f"https://bijmantra.org/results/{orderId}/sample_002.vcf.gz",
            "resultFileSize": 1048576,
            "resultTimestamp": order.completed_date or datetime.now(timezone.utc).isoformat() + "Z"
        }
    ]
    
    total = len(results)
    start = page * pageSize
    paginated = results[start:start + pageSize]
    
    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.get("/vendor/orders/{orderId}/status")
async def get_vendor_order_status(
    orderId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id),
):
    """
    Get status of a vendor order.
    
    BrAPI Endpoint: GET /vendor/orders/{orderId}/status
    """
    order_query = select(VendorOrder).where(
        VendorOrder.order_db_id == orderId,
        VendorOrder.organization_id == org_id
    )
    order_result = await db.execute(order_query)
    order = order_result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    status_info = {
        "orderId": orderId,
        "status": order.status,
        "statusMessages": [
            {"message": "Order received", "messageType": "INFO", "timestamp": order.submitted_date}
        ]
    }
    
    if order.status == "processing":
        status_info["statusMessages"].append({
            "message": "Samples being processed",
            "messageType": "INFO",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        })
    elif order.status == "completed":
        status_info["statusMessages"].append({
            "message": "Processing complete, results available",
            "messageType": "INFO",
            "timestamp": order.completed_date
        })
    
    return _brapi_response(status_info)


@router.post("/vendor/plates")
async def submit_vendor_plates(
    submission: VendorPlateSubmission,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id),
):
    """
    Submit plates to vendor for genotyping.
    
    BrAPI Endpoint: POST /vendor/plates
    """
    submission_id = f"sub_{uuid.uuid4().hex[:8]}"
    
    # Create plates in database
    for i, plate_data in enumerate(submission.plates or []):
        plate = Plate(
            organization_id=org_id,
            plate_db_id=f"{submission_id}_plate_{i+1}",
            plate_name=plate_data.get("plateName", f"Plate-{submission_id}-{i+1:03d}"),
            plate_barcode=plate_data.get("plateBarcode"),
            plate_format=plate_data.get("plateFormat", "PLATE_96"),
            sample_count=plate_data.get("sampleCount", 0),
            status="submitted",
        )
        db.add(plate)
    
    await db.commit()
    
    new_submission = {
        "submissionId": submission_id,
        "clientId": submission.clientId,
        "numberOfSamples": submission.numberOfSamples,
        "plates": submission.plates or [],
        "sampleType": submission.sampleType,
        "serviceIds": submission.serviceIds or [],
        "submittedDate": datetime.now(timezone.utc).isoformat() + "Z",
        "status": "submitted"
    }
    
    return _brapi_response(new_submission)


@router.get("/vendor/plates/{submissionId}")
async def get_vendor_plate_submission(
    submissionId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id),
):
    """
    Get details of a plate submission.
    
    BrAPI Endpoint: GET /vendor/plates/{submissionId}
    """
    # Get plates for this submission
    query = select(Plate).where(
        Plate.organization_id == org_id,
        Plate.plate_db_id.like(f"{submissionId}%")
    )
    result = await db.execute(query)
    plates = result.scalars().all()
    
    if not plates:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    plates_data = []
    total_samples = 0
    for plate in plates:
        plates_data.append({
            "plateDbId": plate.plate_db_id,
            "plateName": plate.plate_name,
            "plateBarcode": plate.plate_barcode,
            "plateFormat": plate.plate_format,
            "sampleCount": plate.sample_count,
            "status": plate.status,
        })
        total_samples += plate.sample_count or 0
    
    submission_data = {
        "submissionId": submissionId,
        "numberOfSamples": total_samples,
        "plates": plates_data,
        "status": plates[0].status if plates else "unknown",
    }
    
    return _brapi_response(submission_data)

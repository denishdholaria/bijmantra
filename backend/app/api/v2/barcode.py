"""
Barcode/QR Code API

Endpoints for barcode generation, scanning, and lookup.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List

from app.services.barcode_service import barcode_service, BarcodeFormat, EntityType
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter(prefix="/barcode", tags=["Barcode/QR"], dependencies=[Depends(get_current_user)])


# Pydantic Models
class GenerateBarcodeRequest(BaseModel):
    entity_type: str
    entity_id: str
    entity_name: str
    format: str = BarcodeFormat.QR_CODE
    data: Optional[dict] = None


class ScanBarcodeRequest(BaseModel):
    barcode_value: str
    scanned_by: str = "system"
    location: Optional[str] = None


class PrintRequest(BaseModel):
    barcode_ids: List[str]
    label_size: str = "small"


# Endpoints
@router.post("/generate")
async def generate_barcode(
    request: GenerateBarcodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate a new barcode for an entity"""
    barcode =  await barcode_service.generate_barcode(db, current_user.organization_id, 
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        entity_name=request.entity_name,
        format=request.format,
        data=request.data,
    )
    return {"message": "Barcode generated", "barcode": barcode}


@router.post("/scan")
async def scan_barcode(
    request: ScanBarcodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Scan a barcode and record the scan"""
    result =  await barcode_service.scan_barcode(db, current_user.organization_id, 
        barcode_value=request.barcode_value,
        scanned_by=request.scanned_by,
        location=request.location,
    )
    return result


@router.get("/lookup/{barcode_value}")
async def lookup_barcode(
    barcode_value: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Look up entity by barcode value"""
    barcode =  await barcode_service.lookup_barcode(db, current_user.organization_id, barcode_value)
    if not barcode:
        raise HTTPException(status_code=404, detail="Barcode not found")
    return barcode



@router.get("")
async def list_barcodes(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    active_only: bool = Query(True, description="Only show active barcodes"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all barcodes with optional filters"""
    barcodes =  await barcode_service.list_barcodes(db, current_user.organization_id, 
        entity_type=entity_type,
    )
    return {"barcodes": barcodes, "count": len(barcodes)}


@router.get("/statistics")
async def get_barcode_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get barcode statistics"""
    return await barcode_service.get_statistics(db, current_user.organization_id)


@router.get("/scans")
async def get_scan_history(
    limit: int = Query(50, description="Number of scans to return"),
    barcode_value: Optional[str] = Query(None, description="Filter by barcode"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get scan history"""
    scans =  await barcode_service.get_scan_history(db, current_user.organization_id, limit=limit, barcode_value=barcode_value)
    return {"scans": scans, "count": len(scans)}


@router.get("/{barcode_id}")
async def get_barcode(
    barcode_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get barcode by ID"""
    barcode =  await barcode_service.get_barcode(db, current_user.organization_id, barcode_id)
    if not barcode:
        raise HTTPException(status_code=404, detail="Barcode not found")
    return barcode


@router.delete("/{barcode_id}")
async def deactivate_barcode(
    barcode_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Deactivate a barcode"""
    barcode =  await barcode_service.deactivate_barcode(db, current_user.organization_id, barcode_id)
    if not barcode:
        raise HTTPException(status_code=404, detail="Barcode not found")
    return {"message": "Barcode deactivated", "barcode": barcode}


@router.post("/print")
async def generate_print_data(
    request: PrintRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate print-ready data for barcode labels"""
    data =  await barcode_service.generate_print_data(db, current_user.organization_id, 
        barcode_ids=request.barcode_ids,
        label_size=request.label_size,
    )
    return data


@router.get("/entity-types/reference")
async def get_entity_types():
    """Get supported entity types"""
    return {
        "entity_types": [
            {"value": EntityType.SEED_LOT, "name": "Seed Lot", "prefix": "SL"},
            {"value": EntityType.ACCESSION, "name": "Accession", "prefix": "AC"},
            {"value": EntityType.SAMPLE, "name": "Sample", "prefix": "SM"},
            {"value": EntityType.VAULT, "name": "Vault", "prefix": "VT"},
            {"value": EntityType.BATCH, "name": "Processing Batch", "prefix": "BT"},
            {"value": EntityType.DISPATCH, "name": "Dispatch", "prefix": "DP"},
            {"value": EntityType.MTA, "name": "MTA", "prefix": "MT"},
        ],
        "formats": [
            {"value": BarcodeFormat.QR_CODE, "name": "QR Code"},
            {"value": BarcodeFormat.CODE_128, "name": "Code 128"},
            {"value": BarcodeFormat.DATA_MATRIX, "name": "Data Matrix"},
            {"value": BarcodeFormat.EAN_13, "name": "EAN-13"},
        ],
    }

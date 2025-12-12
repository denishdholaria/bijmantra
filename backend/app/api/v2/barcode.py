"""
Barcode/QR Code API

Endpoints for barcode generation, scanning, and lookup.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from app.services.barcode_service import barcode_service, BarcodeFormat, EntityType

router = APIRouter(prefix="/barcode", tags=["Barcode/QR"])


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
async def generate_barcode(request: GenerateBarcodeRequest):
    """Generate a new barcode for an entity"""
    barcode = barcode_service.generate_barcode(
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        entity_name=request.entity_name,
        format=request.format,
        data=request.data,
    )
    return {"message": "Barcode generated", "barcode": barcode}


@router.post("/scan")
async def scan_barcode(request: ScanBarcodeRequest):
    """Scan a barcode and record the scan"""
    result = barcode_service.scan_barcode(
        barcode_value=request.barcode_value,
        scanned_by=request.scanned_by,
        location=request.location,
    )
    return result


@router.get("/lookup/{barcode_value}")
async def lookup_barcode(barcode_value: str):
    """Look up entity by barcode value"""
    barcode = barcode_service.lookup_barcode(barcode_value)
    if not barcode:
        raise HTTPException(status_code=404, detail="Barcode not found")
    return barcode



@router.get("")
async def list_barcodes(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    active_only: bool = Query(True, description="Only show active barcodes"),
):
    """List all barcodes with optional filters"""
    barcodes = barcode_service.list_barcodes(
        entity_type=entity_type,
        active_only=active_only,
    )
    return {"barcodes": barcodes, "count": len(barcodes)}


@router.get("/statistics")
async def get_barcode_statistics():
    """Get barcode statistics"""
    return barcode_service.get_statistics()


@router.get("/scans")
async def get_scan_history(
    limit: int = Query(50, description="Number of scans to return"),
    barcode_value: Optional[str] = Query(None, description="Filter by barcode"),
):
    """Get scan history"""
    scans = barcode_service.get_scan_history(limit=limit, barcode_value=barcode_value)
    return {"scans": scans, "count": len(scans)}


@router.get("/{barcode_id}")
async def get_barcode(barcode_id: str):
    """Get barcode by ID"""
    barcode = barcode_service.get_barcode(barcode_id)
    if not barcode:
        raise HTTPException(status_code=404, detail="Barcode not found")
    return barcode


@router.delete("/{barcode_id}")
async def deactivate_barcode(barcode_id: str):
    """Deactivate a barcode"""
    barcode = barcode_service.deactivate_barcode(barcode_id)
    if not barcode:
        raise HTTPException(status_code=404, detail="Barcode not found")
    return {"message": "Barcode deactivated", "barcode": barcode}


@router.post("/print")
async def generate_print_data(request: PrintRequest):
    """Generate print-ready data for barcode labels"""
    data = barcode_service.generate_print_data(
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

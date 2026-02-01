"""
Seed Traceability API
Track seed lots from origin through production to final sale
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.seed_traceability import seed_traceability_service, TraceabilityEventType

router = APIRouter(prefix="/traceability", tags=["Seed Traceability"])


class LotRegistration(BaseModel):
    variety_id: str
    variety_name: str
    crop: str
    seed_class: str
    production_year: int
    production_season: str
    production_location: str
    producer_id: str
    producer_name: str
    quantity_kg: float
    parent_lot_id: Optional[str] = None
    germination_percent: Optional[float] = None
    purity_percent: Optional[float] = None
    moisture_percent: Optional[float] = None


class EventRecord(BaseModel):
    event_type: str
    details: Dict[str, Any]
    operator_id: Optional[str] = None
    operator_name: Optional[str] = None
    location: Optional[str] = None


class CertificationRecord(BaseModel):
    cert_type: str
    cert_number: str
    issuing_authority: str
    issue_date: str
    expiry_date: str
    test_results: Optional[Dict[str, Any]] = None


class TransferRecord(BaseModel):
    from_entity_id: str
    from_entity_name: str
    to_entity_id: str
    to_entity_name: str
    quantity_kg: float
    transfer_type: str  # sale, donation, internal
    price_per_kg: Optional[float] = None
    invoice_number: Optional[str] = None


@router.post("/lots")
async def register_lot(data: LotRegistration):
    """Register a new seed lot for traceability"""
    try:
        lot = seed_traceability_service.register_lot(**data.model_dump())
        return {"status": "success", "data": lot}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/lots")
async def list_lots(
    crop: Optional[str] = None,
    variety_id: Optional[str] = None,
    seed_class: Optional[str] = None,
    status: Optional[str] = None,
):
    """List seed lots with optional filters"""
    lots = seed_traceability_service.list_lots(
        crop=crop,
        variety_id=variety_id,
        seed_class=seed_class,
        status=status,
    )
    return {"status": "success", "data": lots, "count": len(lots)}


@router.get("/lots/{lot_id}")
async def get_lot(lot_id: str):
    """Get seed lot details"""
    lot = seed_traceability_service.get_lot(lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail=f"Lot {lot_id} not found")
    return {"status": "success", "data": lot}


@router.post("/lots/{lot_id}/events")
async def record_event(lot_id: str, data: EventRecord):
    """Record a traceability event for a seed lot"""
    try:
        event = seed_traceability_service.record_event(
            lot_id=lot_id,
            event_type=data.event_type,
            details=data.details,
            operator_id=data.operator_id,
            operator_name=data.operator_name,
            location=data.location,
        )
        return {"status": "success", "data": event}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/lots/{lot_id}/history")
async def get_lot_history(lot_id: str):
    """Get complete event history for a seed lot"""
    history = seed_traceability_service.get_lot_history(lot_id)
    return {"status": "success", "data": history, "count": len(history)}


@router.post("/lots/{lot_id}/certifications")
async def add_certification(lot_id: str, data: CertificationRecord):
    """Add certification to a seed lot"""
    try:
        cert = seed_traceability_service.add_certification(
            lot_id=lot_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": cert}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/lots/{lot_id}/certifications")
async def get_certifications(lot_id: str):
    """Get all certifications for a seed lot"""
    certs = seed_traceability_service.get_certifications(lot_id)
    return {"status": "success", "data": certs, "count": len(certs)}


@router.post("/lots/{lot_id}/transfers")
async def record_transfer(lot_id: str, data: TransferRecord):
    """Record transfer of seed lot ownership"""
    try:
        transfer = seed_traceability_service.record_transfer(
            lot_id=lot_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": transfer}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/lots/{lot_id}/transfers")
async def get_transfers(lot_id: str):
    """Get all transfers for a seed lot"""
    transfers = seed_traceability_service.get_transfers(lot_id)
    return {"status": "success", "data": transfers, "count": len(transfers)}


@router.get("/lots/{lot_id}/lineage")
async def trace_lineage(lot_id: str):
    """Trace complete lineage of a seed lot (parent chain)"""
    lineage = seed_traceability_service.trace_lineage(lot_id)
    if "error" in lineage:
        raise HTTPException(status_code=404, detail=lineage["error"])
    return {"status": "success", "data": lineage}


@router.get("/lots/{lot_id}/descendants")
async def get_descendants(lot_id: str):
    """Find all seed lots derived from this lot"""
    descendants = seed_traceability_service.get_descendants(lot_id)
    return {"status": "success", "data": descendants, "count": len(descendants)}


@router.get("/lots/{lot_id}/qr")
async def generate_qr_data(lot_id: str):
    """Generate data for QR code label"""
    qr_data = seed_traceability_service.generate_qr_data(lot_id)
    if "error" in qr_data:
        raise HTTPException(status_code=404, detail=qr_data["error"])
    return {"status": "success", "data": qr_data}


@router.get("/event-types")
async def get_event_types():
    """Get available traceability event types"""
    event_types = [
        {"code": e.value, "name": e.name.replace("_", " ").title()}
        for e in TraceabilityEventType
    ]
    return {"status": "success", "data": event_types}


@router.get("/transfers")
async def get_all_transfers():
    """Get all transfers across all lots"""
    all_transfers = []
    for lot_id, transfers in seed_traceability_service.transfers.items():
        lot = seed_traceability_service.get_lot(lot_id)
        for transfer in transfers:
            transfer_with_lot = {**transfer}
            if lot:
                transfer_with_lot["variety_name"] = lot.get("variety_name", "")
            all_transfers.append(transfer_with_lot)
    return {"status": "success", "data": all_transfers, "count": len(all_transfers)}


@router.get("/statistics")
async def get_statistics():
    """Get traceability statistics"""
    stats = seed_traceability_service.get_statistics()
    return {"status": "success", "data": stats}

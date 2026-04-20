"""
Seed Traceability API
Track seed lots from origin through production to final sale
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_organization_id
from app.models.dispatch import Dispatch, DispatchItem
from app.modules.core.services.dispatch_management_service import DispatchStatus, get_dispatch_service
from app.modules.germplasm.services.seed_inventory_service import get_seed_inventory_service
from app.modules.germplasm.services.seed_traceability_service import TraceabilityEventType, seed_traceability_service


router = APIRouter(prefix="/traceability", tags=["Seed Traceability"], dependencies=[Depends(get_current_user)])


FULFILLED_DISPATCH_STATUSES = {
    DispatchStatus.SHIPPED.value,
    DispatchStatus.IN_TRANSIT.value,
    DispatchStatus.DELIVERED.value,
}


def _normalize_seed_class(seed_class: str | None) -> str:
    if not seed_class:
        return "certified"
    return seed_class.strip().lower().replace(" ", "_")


def _infer_production_season(harvest_date: str | None) -> str:
    if not harvest_date:
        return "Unknown"

    try:
        month = datetime.fromisoformat(harvest_date).month
    except ValueError:
        return "Unknown"

    if month in {6, 7, 8, 9, 10}:
        return "Kharif"
    if month in {11, 12, 1, 2, 3, 4}:
        return "Rabi"
    return "Zaid"


def _adapt_inventory_lot(inventory_lot: dict[str, Any]) -> dict[str, Any]:
    created_at = inventory_lot.get("harvest_date") or datetime.now().isoformat()
    return {
        "lot_id": inventory_lot["lot_id"],
        "variety_id": inventory_lot.get("accession_id") or inventory_lot["lot_id"],
        "variety_name": inventory_lot.get("variety") or inventory_lot.get("species") or "Unknown",
        "crop": inventory_lot.get("species") or "Unknown",
        "seed_class": _normalize_seed_class(inventory_lot.get("seed_class")),
        "parent_lot_id": None,
        "production_year": inventory_lot.get("production_year") or datetime.now().year,
        "production_season": _infer_production_season(inventory_lot.get("harvest_date")),
        "production_location": inventory_lot.get("production_location") or inventory_lot.get("storage_location") or "Unknown",
        "producer_id": inventory_lot.get("accession_uuid") or inventory_lot["lot_id"],
        "producer_name": inventory_lot.get("producer_name") or "Unknown",
        "initial_quantity_kg": inventory_lot.get("quantity_kg") or 0,
        "current_quantity_kg": inventory_lot.get("quantity_kg") or 0,
        "quantity_kg": inventory_lot.get("quantity_kg") or 0,
        "germination_percent": inventory_lot.get("germination_percent"),
        "purity_percent": inventory_lot.get("purity_percent"),
        "moisture_percent": inventory_lot.get("moisture_percent"),
        "status": inventory_lot.get("status") or "active",
        "created_at": created_at,
    }


def _normalize_traceability_lot(lot: dict[str, Any]) -> dict[str, Any]:
    normalized_lot = dict(lot)
    current_quantity = normalized_lot.get("current_quantity_kg")
    if current_quantity is None:
        current_quantity = normalized_lot.get("quantity_kg")

    normalized_lot["quantity_kg"] = current_quantity or 0
    return normalized_lot


async def _get_persisted_dispatch_transfers(
    db: AsyncSession,
    organization_id: int,
    lot_id: str | None = None,
) -> list[dict[str, Any]]:
    stmt = (
        select(Dispatch, DispatchItem)
        .join(DispatchItem, Dispatch.id == DispatchItem.dispatch_id)
        .where(Dispatch.organization_id == organization_id)
        .where(Dispatch.status.in_(FULFILLED_DISPATCH_STATUSES))
        .order_by(Dispatch.created_at)
    )

    if lot_id:
        stmt = stmt.where(DispatchItem.lot_id == lot_id)

    result = await db.execute(stmt)
    transfers: list[dict[str, Any]] = []
    for dispatch, item in result.all():
        timestamp = dispatch.delivered_at or dispatch.shipped_at or dispatch.created_at
        transfers.append({
            "transfer_id": f"dispatch-item-{item.id}",
            "dispatch_id": str(dispatch.id),
            "dispatch_number": dispatch.dispatch_number,
            "lot_id": item.lot_id,
            "from_entity_id": "SELF",
            "from_entity_name": "Seed Company",
            "to_entity_id": str(dispatch.recipient_id) if dispatch.recipient_id else None,
            "to_entity_name": dispatch.recipient_name,
            "quantity_kg": item.quantity_kg,
            "transfer_type": dispatch.transfer_type,
            "price_per_kg": item.unit_price,
            "total_value": item.total_price,
            "invoice_number": dispatch.invoice_number,
            "tracking_number": dispatch.tracking_number,
            "carrier": dispatch.carrier,
            "timestamp": timestamp.isoformat() if timestamp else datetime.now().isoformat(),
            "status": dispatch.status,
            "delivery_address": dispatch.recipient_address,
            "variety_name": item.variety_name,
            "crop": item.crop,
            "seed_class": item.seed_class,
        })
    return transfers


async def _get_persisted_dispatched_quantity(
    db: AsyncSession,
    organization_id: int,
    lot_id: str,
) -> float:
    transfers = await _get_persisted_dispatch_transfers(db, organization_id, lot_id)
    return sum(transfer.get("quantity_kg", 0) for transfer in transfers)


def _transfer_to_history_event(transfer: dict[str, Any]) -> dict[str, Any]:
    transfer_type = transfer.get("transfer_type") or "transfer"
    event_type = TraceabilityEventType.SALE.value if transfer_type == "sale" else TraceabilityEventType.TRANSFER.value
    details = {
        "from": transfer.get("from_entity_name"),
        "to": transfer.get("to_entity_name"),
        "quantity_kg": transfer.get("quantity_kg"),
        "transfer_type": transfer_type,
        "dispatch_number": transfer.get("dispatch_number"),
        "invoice_number": transfer.get("invoice_number"),
        "tracking_number": transfer.get("tracking_number"),
        "carrier": transfer.get("carrier"),
        "status": transfer.get("status"),
    }
    return {
        "event_id": transfer.get("transfer_id") or transfer.get("dispatch_id"),
        "lot_id": transfer.get("lot_id"),
        "event_type": event_type,
        "timestamp": transfer.get("timestamp"),
        "operator_id": None,
        "operator_name": None,
        "location": transfer.get("delivery_address"),
        "details": {key: value for key, value in details.items() if value not in {None, ""}},
    }


async def _persist_transfer_as_dispatch(
    db: AsyncSession,
    organization_id: int,
    lot: dict[str, Any],
    data: "TransferRecord",
) -> None:
    dispatch_service = get_dispatch_service()
    dispatch = await dispatch_service.create_dispatch(
        db=db,
        organization_id=organization_id,
        recipient_id=None,
        recipient_name=data.to_entity_name,
        recipient_address="",
        recipient_contact="",
        recipient_phone="",
        transfer_type=data.transfer_type,
        items=[{
            "lot_id": lot["lot_id"],
            "variety_name": lot.get("variety_name", ""),
            "crop": lot.get("crop", ""),
            "seed_class": lot.get("seed_class", "certified"),
            "quantity_kg": data.quantity_kg,
            "unit_price": data.price_per_kg,
        }],
        notes=f"Auto-generated from traceability transfer to {data.to_entity_name}",
    )

    dispatch_id = int(dispatch["dispatch_id"])
    stmt = select(Dispatch).where(Dispatch.id == dispatch_id)
    result = await db.execute(stmt)
    dispatch_model = result.scalar_one()
    dispatch_model.status = DispatchStatus.DELIVERED.value
    dispatch_model.shipped_at = datetime.now()
    dispatch_model.delivered_at = datetime.now()
    dispatch_model.invoice_number = data.invoice_number
    await db.commit()


def _sync_traceability_lot(lot: dict[str, Any]) -> dict[str, Any]:
    lot_id = lot["lot_id"]
    if lot_id not in seed_traceability_service.seed_lots:
        seed_traceability_service.seed_lots[lot_id] = lot
        seed_traceability_service.events.setdefault(lot_id, [])
        seed_traceability_service.certifications.setdefault(lot_id, [])
        seed_traceability_service.transfers.setdefault(lot_id, [])
    return _normalize_traceability_lot(seed_traceability_service.seed_lots[lot_id])


async def _get_traceability_lot_with_inventory_fallback(
    db: AsyncSession,
    lot_id: str,
    organization_id: int | None = None,
) -> dict[str, Any] | None:
    existing_lot = seed_traceability_service.get_lot(lot_id)
    if existing_lot:
        return _normalize_traceability_lot(existing_lot)

    inventory_lot = await get_seed_inventory_service().get_lot(db, lot_id)
    if not inventory_lot:
        return None

    adapted_lot = _adapt_inventory_lot(inventory_lot)
    if organization_id is not None:
        dispatched_quantity = await _get_persisted_dispatched_quantity(db, organization_id, lot_id)
        adapted_lot["current_quantity_kg"] = max((adapted_lot.get("initial_quantity_kg") or 0) - dispatched_quantity, 0)
        adapted_lot["quantity_kg"] = adapted_lot["current_quantity_kg"]

    return _sync_traceability_lot(adapted_lot)


async def _list_traceability_lots_with_inventory_fallback(
    db: AsyncSession,
    organization_id: int | None = None,
    crop: str | None = None,
    variety_id: str | None = None,
    seed_class: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    merged_lots = {
        lot["lot_id"]: lot
        for lot in seed_traceability_service.list_lots(
            crop=crop,
            variety_id=variety_id,
            seed_class=seed_class,
            status=status,
        )
    }

    inventory_lots = await get_seed_inventory_service().list_lots(db=db, status=status)
    normalized_seed_class = _normalize_seed_class(seed_class) if seed_class else None

    for inventory_lot in inventory_lots:
        adapted_lot = _adapt_inventory_lot(inventory_lot)
        if organization_id is not None:
            dispatched_quantity = await _get_persisted_dispatched_quantity(db, organization_id, adapted_lot["lot_id"])
            adapted_lot["current_quantity_kg"] = max((adapted_lot.get("initial_quantity_kg") or 0) - dispatched_quantity, 0)
            adapted_lot["quantity_kg"] = adapted_lot["current_quantity_kg"]
        if crop and adapted_lot["crop"].lower() != crop.lower():
            continue
        if variety_id and adapted_lot["variety_id"] != variety_id:
            continue
        if normalized_seed_class and adapted_lot["seed_class"] != normalized_seed_class:
            continue
        if status and adapted_lot["status"] != status:
            continue
        merged_lots.setdefault(adapted_lot["lot_id"], _sync_traceability_lot(adapted_lot))

    return [_normalize_traceability_lot(lot) for lot in merged_lots.values()]


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
    parent_lot_id: str | None = None
    germination_percent: float | None = None
    purity_percent: float | None = None
    moisture_percent: float | None = None


class EventRecord(BaseModel):
    event_type: str
    details: dict[str, Any]
    operator_id: str | None = None
    operator_name: str | None = None
    location: str | None = None


class CertificationRecord(BaseModel):
    cert_type: str
    cert_number: str
    issuing_authority: str
    issue_date: str
    expiry_date: str
    test_results: dict[str, Any] | None = None


class TransferRecord(BaseModel):
    from_entity_id: str
    from_entity_name: str
    to_entity_id: str
    to_entity_name: str
    quantity_kg: float
    transfer_type: str  # sale, donation, internal
    price_per_kg: float | None = None
    invoice_number: str | None = None


@router.post("/lots")
async def register_lot(data: LotRegistration):
    """Register a new seed lot for traceability"""
    try:
        lot = seed_traceability_service.register_lot(**data.model_dump())
        return {"status": "success", "data": _normalize_traceability_lot(lot)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/lots")
async def list_lots(
    crop: str | None = None,
    variety_id: str | None = None,
    seed_class: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """List seed lots with optional filters"""
    lots = await _list_traceability_lots_with_inventory_fallback(
        db=db,
        organization_id=organization_id,
        crop=crop,
        variety_id=variety_id,
        seed_class=seed_class,
        status=status,
    )
    return {"status": "success", "data": lots, "count": len(lots)}


@router.get("/lots/{lot_id}")
async def get_lot(
    lot_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get seed lot details"""
    lot = await _get_traceability_lot_with_inventory_fallback(db, lot_id, organization_id)
    if not lot:
        raise HTTPException(status_code=404, detail=f"Lot {lot_id} not found")
    return {"status": "success", "data": lot}


@router.post("/lots/{lot_id}/events")
async def record_event(
    lot_id: str,
    data: EventRecord,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Record a traceability event for a seed lot"""
    try:
        if not await _get_traceability_lot_with_inventory_fallback(db, lot_id, organization_id):
            raise ValueError(f"Lot {lot_id} not found")
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
async def get_lot_history(
    lot_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get complete event history for a seed lot"""
    if not await _get_traceability_lot_with_inventory_fallback(db, lot_id, organization_id):
        raise HTTPException(status_code=404, detail=f"Lot {lot_id} not found")
    history = [
        event
        for event in seed_traceability_service.get_lot_history(lot_id)
        if event.get("event_type") not in {TraceabilityEventType.SALE.value, TraceabilityEventType.TRANSFER.value}
    ]
    persisted_transfers = await _get_persisted_dispatch_transfers(db, organization_id, lot_id)
    history.extend(_transfer_to_history_event(transfer) for transfer in persisted_transfers)
    history.sort(key=lambda event: event.get("timestamp") or "")
    return {"status": "success", "data": history, "count": len(history)}


@router.post("/lots/{lot_id}/certifications")
async def add_certification(
    lot_id: str,
    data: CertificationRecord,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Add certification to a seed lot"""
    try:
        if not await _get_traceability_lot_with_inventory_fallback(db, lot_id, organization_id):
            raise ValueError(f"Lot {lot_id} not found")
        cert = seed_traceability_service.add_certification(
            lot_id=lot_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": cert}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/lots/{lot_id}/certifications")
async def get_certifications(
    lot_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get all certifications for a seed lot"""
    if not await _get_traceability_lot_with_inventory_fallback(db, lot_id, organization_id):
        raise HTTPException(status_code=404, detail=f"Lot {lot_id} not found")
    certs = seed_traceability_service.get_certifications(lot_id)
    return {"status": "success", "data": certs, "count": len(certs)}


@router.post("/lots/{lot_id}/transfers")
async def record_transfer(
    lot_id: str,
    data: TransferRecord,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Record transfer of seed lot ownership"""
    try:
        lot = await _get_traceability_lot_with_inventory_fallback(db, lot_id, organization_id)
        if not lot:
            raise ValueError(f"Lot {lot_id} not found")
        transfer = seed_traceability_service.record_transfer(
            lot_id=lot_id,
            **data.model_dump(),
        )
        await _persist_transfer_as_dispatch(db, organization_id, lot, data)
        return {"status": "success", "data": transfer}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/lots/{lot_id}/transfers")
async def get_transfers(
    lot_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get all transfers for a seed lot"""
    if not await _get_traceability_lot_with_inventory_fallback(db, lot_id, organization_id):
        raise HTTPException(status_code=404, detail=f"Lot {lot_id} not found")
    transfers = seed_traceability_service.get_transfers(lot_id)
    if not transfers:
        transfers = await _get_persisted_dispatch_transfers(db, organization_id, lot_id)
    return {"status": "success", "data": transfers, "count": len(transfers)}


@router.get("/lots/{lot_id}/lineage")
async def trace_lineage(
    lot_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Trace complete lineage of a seed lot (parent chain)"""
    if not await _get_traceability_lot_with_inventory_fallback(db, lot_id, organization_id):
        raise HTTPException(status_code=404, detail=f"Lot {lot_id} not found")
    lineage = seed_traceability_service.trace_lineage(lot_id)
    if "error" in lineage:
        raise HTTPException(status_code=404, detail=lineage["error"])
    return {"status": "success", "data": lineage}


@router.get("/lots/{lot_id}/descendants")
async def get_descendants(
    lot_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Find all seed lots derived from this lot"""
    if not await _get_traceability_lot_with_inventory_fallback(db, lot_id, organization_id):
        raise HTTPException(status_code=404, detail=f"Lot {lot_id} not found")
    descendants = seed_traceability_service.get_descendants(lot_id)
    return {"status": "success", "data": descendants, "count": len(descendants)}


@router.get("/lots/{lot_id}/qr")
async def generate_qr_data(
    lot_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Generate data for QR code label"""
    if not await _get_traceability_lot_with_inventory_fallback(db, lot_id, organization_id):
        raise HTTPException(status_code=404, detail=f"Lot {lot_id} not found")
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
async def get_all_transfers(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get all transfers across all lots"""
    all_transfers = []
    in_memory_lot_ids = set(seed_traceability_service.transfers.keys())
    for lot_id, transfers in seed_traceability_service.transfers.items():
        lot = seed_traceability_service.get_lot(lot_id)
        for transfer in transfers:
            transfer_with_lot = {**transfer}
            if lot:
                transfer_with_lot["variety_name"] = lot.get("variety_name", "")
            all_transfers.append(transfer_with_lot)
    persisted_transfers = await _get_persisted_dispatch_transfers(db, organization_id)
    all_transfers.extend(
        transfer for transfer in persisted_transfers if transfer.get("lot_id") not in in_memory_lot_ids
    )
    return {"status": "success", "data": all_transfers, "count": len(all_transfers)}


@router.get("/statistics")
async def get_statistics():
    """Get traceability statistics"""
    stats = seed_traceability_service.get_statistics()
    return {"status": "success", "data": stats}

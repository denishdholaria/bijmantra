"""
Dispatch Management API
Full dispatch workflow for seed company operations

Endpoints:
- POST /api/v2/dispatch/orders - Create dispatch order
- GET /api/v2/dispatch/orders - List dispatches
- GET /api/v2/dispatch/orders/{id} - Get dispatch details
- POST /api/v2/dispatch/orders/{id}/submit - Submit for approval
- POST /api/v2/dispatch/orders/{id}/approve - Approve dispatch
- POST /api/v2/dispatch/orders/{id}/pick - Start picking
- POST /api/v2/dispatch/orders/{id}/items/{item_id}/picked - Mark item picked
- POST /api/v2/dispatch/orders/{id}/ship - Ship dispatch
- POST /api/v2/dispatch/orders/{id}/deliver - Mark delivered
- POST /api/v2/dispatch/orders/{id}/cancel - Cancel dispatch
- POST /api/v2/dispatch/firms - Create firm
- GET /api/v2/dispatch/firms - List firms
- GET /api/v2/dispatch/firms/{id} - Get firm details
- PUT /api/v2/dispatch/firms/{id} - Update firm
- DELETE /api/v2/dispatch/firms/{id} - Deactivate firm
- GET /api/v2/dispatch/statistics - Get statistics
- GET /api/v2/dispatch/firm-types - Get firm types
- GET /api/v2/dispatch/statuses - Get dispatch statuses
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.dispatch_management import get_dispatch_service

router = APIRouter(prefix="/dispatch", tags=["Dispatch Management"])


# ============================================
# SCHEMAS
# ============================================

class DispatchItemCreate(BaseModel):
    lot_id: str = Field(..., description="Seed lot ID")
    variety_name: str = Field("", description="Variety name")
    crop: str = Field("", description="Crop name")
    seed_class: str = Field("certified", description="Seed class")
    quantity_kg: float = Field(..., gt=0, description="Quantity in kg")
    unit_price: Optional[float] = Field(None, description="Price per kg")


class DispatchCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "recipient_id": "FIRM-001",
            "recipient_name": "ABC Agro Dealers",
            "recipient_address": "123 Market Road, Mumbai",
            "recipient_contact": "Rajesh Kumar",
            "recipient_phone": "+91-9876543210",
            "transfer_type": "sale",
            "items": [
                {"lot_id": "LOT-2024-001", "variety_name": "IR64", "crop": "Rice", "quantity_kg": 100, "unit_price": 50}
            ],
            "notes": "Urgent delivery"
        }
    })

    recipient_id: str = Field(..., description="Recipient firm ID")
    recipient_name: str = Field(..., description="Recipient name")
    recipient_address: str = Field(..., description="Delivery address")
    recipient_contact: str = Field("", description="Contact person")
    recipient_phone: str = Field("", description="Contact phone")
    transfer_type: str = Field("sale", description="Transfer type: sale, internal, donation, sample, return")
    items: List[DispatchItemCreate] = Field(..., description="Items to dispatch")
    notes: str = Field("", description="Additional notes")


class ShipDispatch(BaseModel):
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    invoice_number: Optional[str] = None


class FirmCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "New Agro Dealers",
            "firm_type": "dealer",
            "address": "456 Farm Road",
            "city": "Pune",
            "state": "Maharashtra",
            "country": "India",
            "postal_code": "411001",
            "contact_person": "Amit Patel",
            "phone": "+91-9876543213",
            "email": "amit@newagro.com",
            "credit_limit": 200000
        }
    })

    name: str = Field(..., description="Firm name")
    firm_type: str = Field(..., description="Type: dealer, distributor, retailer, farmer, institution, government")
    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province")
    country: str = Field("India", description="Country")
    postal_code: str = Field(..., description="Postal/ZIP code")
    contact_person: str = Field(..., description="Primary contact name")
    phone: str = Field(..., description="Phone number")
    email: str = Field(..., description="Email address")
    gst_number: Optional[str] = Field(None, description="GST/Tax number")
    credit_limit: float = Field(0, description="Credit limit")
    notes: str = Field("", description="Additional notes")


class FirmUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gst_number: Optional[str] = None
    credit_limit: Optional[float] = None
    notes: Optional[str] = None


# ============================================
# DISPATCH ENDPOINTS
# ============================================

@router.post("/orders")
async def create_dispatch(
    request: DispatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create a new dispatch order
    
    Creates a dispatch in DRAFT status. Must be submitted for approval before shipping.
    """
    service = get_dispatch_service()

    try:
        items = [item.model_dump() for item in request.items]
        dispatch = await service.create_dispatch(db, current_user.organization_id, recipient_id=request.recipient_id,
            recipient_name=request.recipient_name,
            recipient_address=request.recipient_address,
            recipient_contact=request.recipient_contact,
            recipient_phone=request.recipient_phone,
            transfer_type=request.transfer_type,
            items=items,
            notes=request.notes,)
        return {
            "success": True,
            "message": f"Dispatch {dispatch.dispatch_number} created",
            "data": dispatch.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to create dispatch: {str(e)}")


@router.get("/orders")
async def list_dispatches(
    status: Optional[str] = Query(None, description="Filter by status"),
    recipient_id: Optional[str] = Query(None, description="Filter by recipient"),
    transfer_type: Optional[str] = Query(None, description="Filter by transfer type"),
    from_date: Optional[str] = Query(None, description="From date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="To date (YYYY-MM-DD)"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """List dispatch orders with optional filters"""
    service = get_dispatch_service()

    dispatches = await service.list_dispatches(db, current_user.organization_id, status=status,
        recipient_id=recipient_id,
        transfer_type=transfer_type,
        from_date=from_date,
        to_date=to_date,)

    return {
        "success": True,
        "count": len(dispatches),
        "data": dispatches,
    }


@router.get("/orders/{dispatch_id}")
async def get_dispatch(
    dispatch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get dispatch order details"""
    service = get_dispatch_service()

    dispatch = await service.get_dispatch(db, current_user.organization_id, dispatch_id)
    if not dispatch:
        raise HTTPException(404, f"Dispatch {dispatch_id} not found")

    return {"success": True, "data": dispatch}


@router.post("/orders/{dispatch_id}/submit")
async def submit_dispatch(
    dispatch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Submit dispatch for approval"""
    service = get_dispatch_service()

    try:
        dispatch = await service.submit_for_approval(db, current_user.organization_id, dispatch_id)
        return {
            "success": True,
            "message": "Dispatch submitted for approval",
            "data": dispatch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/orders/{dispatch_id}/approve")
async def approve_dispatch(
    dispatch_id: str, approved_by: str = Query("Manager"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve a dispatch order"""
    service = get_dispatch_service()

    try:
        dispatch = await service.approve_dispatch(db, current_user.organization_id, dispatch_id, approved_by)
        return {
            "success": True,
            "message": "Dispatch approved",
            "data": dispatch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/orders/{dispatch_id}/pick")
async def start_picking(
    dispatch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Start picking process for dispatch"""
    service = get_dispatch_service()

    try:
        dispatch = await service.start_picking(db, current_user.organization_id, dispatch_id)
        return {
            "success": True,
            "message": "Picking started",
            "data": dispatch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/orders/{dispatch_id}/items/{item_id}/picked")
async def mark_item_picked(
    dispatch_id: str, item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark a dispatch item as picked"""
    service = get_dispatch_service()

    try:
        dispatch = await service.mark_item_picked(db, current_user.organization_id, dispatch_id, item_id)
        return {
            "success": True,
            "message": "Item marked as picked",
            "data": dispatch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/orders/{dispatch_id}/ship")
async def ship_dispatch(
    dispatch_id: str, request: ShipDispatch,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark dispatch as shipped"""
    service = get_dispatch_service()

    try:
        dispatch = await service.ship_dispatch(db, current_user.organization_id, dispatch_id,
            tracking_number=request.tracking_number,
            carrier=request.carrier,
            invoice_number=request.invoice_number,)
        return {
            "success": True,
            "message": "Dispatch shipped",
            "data": dispatch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/orders/{dispatch_id}/deliver")
async def mark_delivered(
    dispatch_id: str, notes: str = Query(""),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark dispatch as delivered"""
    service = get_dispatch_service()

    try:
        dispatch = await service.mark_delivered(db, current_user.organization_id, dispatch_id, notes)
        return {
            "success": True,
            "message": "Dispatch delivered",
            "data": dispatch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/orders/{dispatch_id}/cancel")
async def cancel_dispatch(
    dispatch_id: str, reason: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cancel a dispatch order"""
    service = get_dispatch_service()

    try:
        dispatch = await service.cancel_dispatch(db, current_user.organization_id, dispatch_id, reason)
        return {
            "success": True,
            "message": "Dispatch cancelled",
            "data": dispatch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


# ============================================
# FIRM ENDPOINTS
# ============================================

@router.post("/firms")
async def create_firm(
    request: FirmCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new firm/dealer"""
    service = get_dispatch_service()

    try:
        firm = await service.create_firm(db, current_user.organization_id, **request.model_dump())
        return {
            "success": True,
            "message": f"Firm {firm.firm_code} created",
            "data": firm.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to create firm: {str(e)}")


@router.get("/firms")
async def list_firms(
    firm_type: Optional[str] = Query(None, description="Filter by type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
):
    """List firms with optional filters"""
    service = get_dispatch_service()

    firms = await service.list_firms(db, current_user.organization_id, firm_type=firm_type,
        status=status,
        city=city,
        state=state,)

    return {
        "success": True,
        "count": len(firms),
        "data": firms,
    }


@router.get("/firms/{firm_id}")
async def get_firm(
    firm_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get firm details"""
    service = get_dispatch_service()

    firm = await service.get_firm(db, current_user.organization_id, firm_id)
    if not firm:
        raise HTTPException(404, f"Firm {firm_id} not found")

    return {"success": True, "data": firm}


@router.put("/firms/{firm_id}")
async def update_firm(
    firm_id: str, request: FirmUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update firm details"""
    service = get_dispatch_service()

    try:
        updates = {k: v for k, v in request.model_dump().items() if v is not None}
        firm = await service.update_firm(db, current_user.organization_id, firm_id, **updates)
        return {
            "success": True,
            "message": "Firm updated",
            "data": firm,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/firms/{firm_id}")
async def deactivate_firm(
    firm_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Deactivate a firm"""
    service = get_dispatch_service()

    try:
        firm = await service.deactivate_firm(db, current_user.organization_id, firm_id)
        return {
            "success": True,
            "message": "Firm deactivated",
            "data": firm,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


# ============================================
# REFERENCE DATA ENDPOINTS
# ============================================

@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get dispatch and firm statistics"""
    service = get_dispatch_service()
    stats = await service.get_dispatch_statistics(db, current_user.organization_id)
    return {"success": True, "data": stats}


@router.get("/firm-types")
async def get_firm_types(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get available firm types"""
    service = get_dispatch_service()
    types = service.get_firm_types()
    return {"success": True, "data": types}


@router.get("/statuses")
async def get_dispatch_statuses(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get available dispatch statuses"""
    service = get_dispatch_service()
    statuses = service.get_dispatch_statuses()
    return {"success": True, "data": statuses}

"""
Dispatch Management Service

Full dispatch workflow for seed company operations.
Converted to use real database queries per Zero Mock Data Policy.
"""

from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dispatch import Firm, Dispatch, DispatchItem


class DispatchStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PICKING = "picking"
    PACKED = "packed"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class TransferType(str, Enum):
    SALE = "sale"
    INTERNAL = "internal"
    DONATION = "donation"
    SAMPLE = "sample"
    RETURN = "return"


class DispatchManagementService:
    """
    Service for managing seed dispatches and firms.
    
    All methods are async and require AsyncSession and organization_id
    for multi-tenant isolation per GOVERNANCE.md §4.3.1.
    """

    async def _generate_dispatch_number(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> str:
        """Generate unique dispatch number."""
        year = datetime.now().year
        
        # Count existing dispatches for this year
        stmt = select(func.count(Dispatch.id)).where(
            and_(
                Dispatch.organization_id == organization_id,
                Dispatch.dispatch_number.like(f"DSP-{year}-%")
            )
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        return f"DSP-{year}-{count + 1:04d}"

    async def _generate_firm_code(
        self,
        db: AsyncSession,
        organization_id: int,
        name: str,
    ) -> str:
        """Generate unique firm code."""
        prefix = ''.join(word[0].upper() for word in name.split()[:3])
        
        # Count existing firms with this prefix
        stmt = select(func.count(Firm.id)).where(
            and_(
                Firm.organization_id == organization_id,
                Firm.firm_code.like(f"{prefix}-%")
            )
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        return f"{prefix}-{count + 1:03d}"

    # ==================== DISPATCH OPERATIONS ====================

    async def create_dispatch(
        self,
        db: AsyncSession,
        organization_id: int,
        recipient_id: Optional[int],
        recipient_name: str,
        recipient_address: str,
        recipient_contact: str,
        recipient_phone: str,
        transfer_type: str,
        items: List[Dict],
        notes: str = "",
        created_by: str = "system",
    ) -> Dict:
        """Create a new dispatch order."""
        dispatch_number = await self._generate_dispatch_number(db, organization_id)
        
        total_qty = 0.0
        total_value = 0.0
        
        # Calculate totals
        for item in items:
            qty = item.get("quantity_kg", 0)
            price = item.get("unit_price", 0) or 0
            total_qty += qty
            total_value += qty * price
        
        # Create dispatch
        dispatch = Dispatch(
            dispatch_number=dispatch_number,
            recipient_id=recipient_id,
            recipient_name=recipient_name,
            recipient_address=recipient_address,
            recipient_contact=recipient_contact,
            recipient_phone=recipient_phone,
            transfer_type=transfer_type,
            total_quantity_kg=total_qty,
            total_value=total_value,
            status=DispatchStatus.DRAFT.value,
            notes=notes,
            created_by=created_by,
            organization_id=organization_id,
        )
        db.add(dispatch)
        await db.flush()
        
        # Create dispatch items
        for item in items:
            qty = item.get("quantity_kg", 0)
            price = item.get("unit_price", 0) or 0
            total = qty * price
            
            dispatch_item = DispatchItem(
                dispatch_id=dispatch.id,
                seedlot_id=item.get("seedlot_id"),
                lot_id=item["lot_id"],
                variety_name=item.get("variety_name", ""),
                crop=item.get("crop", ""),
                seed_class=item.get("seed_class", "certified"),
                quantity_kg=qty,
                unit_price=price if price > 0 else None,
                total_price=total if total > 0 else None,
            )
            db.add(dispatch_item)
        
        await db.commit()
        await db.refresh(dispatch)
        
        return await self.get_dispatch(db, organization_id, dispatch.id)

    async def get_dispatch(
        self,
        db: AsyncSession,
        organization_id: int,
        dispatch_id: int,
    ) -> Optional[Dict]:
        """Get dispatch by ID."""
        stmt = select(Dispatch).options(
            selectinload(Dispatch.items),
            selectinload(Dispatch.recipient_firm)
        ).where(
            and_(
                Dispatch.organization_id == organization_id,
                Dispatch.id == dispatch_id
            )
        )
        result = await db.execute(stmt)
        dispatch = result.scalar_one_or_none()
        
        return self._dispatch_to_dict(dispatch) if dispatch else None

    async def list_dispatches(
        self,
        db: AsyncSession,
        organization_id: int,
        status: Optional[str] = None,
        recipient_id: Optional[int] = None,
        transfer_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """List dispatches with filters."""
        stmt = select(Dispatch).options(
            selectinload(Dispatch.items)
        ).where(
            Dispatch.organization_id == organization_id
        )
        
        if status:
            stmt = stmt.where(Dispatch.status == status)
        if recipient_id:
            stmt = stmt.where(Dispatch.recipient_id == recipient_id)
        if transfer_type:
            stmt = stmt.where(Dispatch.transfer_type == transfer_type)
        if from_date:
            stmt = stmt.where(Dispatch.created_at >= from_date)
        if to_date:
            stmt = stmt.where(Dispatch.created_at <= to_date)
        
        stmt = stmt.order_by(Dispatch.created_at.desc()).limit(limit)
        
        result = await db.execute(stmt)
        dispatches = result.scalars().all()
        
        return [self._dispatch_to_dict(d) for d in dispatches]

    async def submit_for_approval(
        self,
        db: AsyncSession,
        organization_id: int,
        dispatch_id: int,
    ) -> Dict:
        """Submit dispatch for approval."""
        dispatch = await self._get_dispatch_or_raise(db, organization_id, dispatch_id)
        
        if dispatch.status != DispatchStatus.DRAFT.value:
            raise ValueError(f"Cannot submit dispatch in {dispatch.status} status")
        
        dispatch.status = DispatchStatus.PENDING_APPROVAL.value
        await db.commit()
        
        return await self.get_dispatch(db, organization_id, dispatch_id)

    async def approve_dispatch(
        self,
        db: AsyncSession,
        organization_id: int,
        dispatch_id: int,
        approved_by: str,
    ) -> Dict:
        """Approve a dispatch."""
        dispatch = await self._get_dispatch_or_raise(db, organization_id, dispatch_id)
        
        if dispatch.status != DispatchStatus.PENDING_APPROVAL.value:
            raise ValueError(f"Cannot approve dispatch in {dispatch.status} status")
        
        dispatch.status = DispatchStatus.APPROVED.value
        dispatch.approved_at = datetime.now(UTC)
        dispatch.approved_by = approved_by
        await db.commit()
        
        return await self.get_dispatch(db, organization_id, dispatch_id)

    async def start_picking(
        self,
        db: AsyncSession,
        organization_id: int,
        dispatch_id: int,
    ) -> Dict:
        """Start picking process."""
        dispatch = await self._get_dispatch_or_raise(db, organization_id, dispatch_id)
        
        if dispatch.status != DispatchStatus.APPROVED.value:
            raise ValueError(f"Cannot start picking for dispatch in {dispatch.status} status")
        
        dispatch.status = DispatchStatus.PICKING.value
        await db.commit()
        
        return await self.get_dispatch(db, organization_id, dispatch_id)

    async def mark_item_picked(
        self,
        db: AsyncSession,
        organization_id: int,
        dispatch_id: int,
        item_id: int,
    ) -> Dict:
        """Mark an item as picked."""
        dispatch = await self._get_dispatch_or_raise(db, organization_id, dispatch_id)
        
        # Find and update item
        stmt = select(DispatchItem).where(
            and_(
                DispatchItem.dispatch_id == dispatch_id,
                DispatchItem.id == item_id
            )
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        
        if item:
            item.picked = True
            await db.flush()
        
        # Check if all items picked
        all_picked_stmt = select(func.count(DispatchItem.id)).where(
            and_(
                DispatchItem.dispatch_id == dispatch_id,
                DispatchItem.picked == False
            )
        )
        result = await db.execute(all_picked_stmt)
        unpicked_count = result.scalar() or 0
        
        if unpicked_count == 0:
            dispatch.status = DispatchStatus.PACKED.value
        
        await db.commit()
        
        return await self.get_dispatch(db, organization_id, dispatch_id)

    async def ship_dispatch(
        self,
        db: AsyncSession,
        organization_id: int,
        dispatch_id: int,
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None,
        invoice_number: Optional[str] = None,
    ) -> Dict:
        """Mark dispatch as shipped."""
        dispatch = await self._get_dispatch_or_raise(db, organization_id, dispatch_id)
        
        if dispatch.status not in [DispatchStatus.APPROVED.value, DispatchStatus.PACKED.value]:
            raise ValueError(f"Cannot ship dispatch in {dispatch.status} status")
        
        dispatch.status = DispatchStatus.SHIPPED.value
        dispatch.shipped_at = datetime.now(UTC)
        dispatch.tracking_number = tracking_number
        dispatch.carrier = carrier
        dispatch.invoice_number = invoice_number
        await db.commit()
        
        return await self.get_dispatch(db, organization_id, dispatch_id)

    async def mark_delivered(
        self,
        db: AsyncSession,
        organization_id: int,
        dispatch_id: int,
        delivery_notes: str = "",
    ) -> Dict:
        """Mark dispatch as delivered."""
        dispatch = await self._get_dispatch_or_raise(db, organization_id, dispatch_id)
        
        if dispatch.status not in [DispatchStatus.SHIPPED.value, DispatchStatus.IN_TRANSIT.value]:
            raise ValueError(f"Cannot mark delivered for dispatch in {dispatch.status} status")
        
        dispatch.status = DispatchStatus.DELIVERED.value
        dispatch.delivered_at = datetime.now(UTC)
        if delivery_notes:
            dispatch.notes = f"{dispatch.notes or ''}\nDelivery: {delivery_notes}"
        await db.commit()
        
        return await self.get_dispatch(db, organization_id, dispatch_id)

    async def cancel_dispatch(
        self,
        db: AsyncSession,
        organization_id: int,
        dispatch_id: int,
        reason: str,
    ) -> Dict:
        """Cancel a dispatch."""
        dispatch = await self._get_dispatch_or_raise(db, organization_id, dispatch_id)
        
        if dispatch.status == DispatchStatus.DELIVERED.value:
            raise ValueError("Cannot cancel delivered dispatch")
        
        dispatch.status = DispatchStatus.CANCELLED.value
        dispatch.notes = f"{dispatch.notes or ''}\nCancelled: {reason}"
        await db.commit()
        
        return await self.get_dispatch(db, organization_id, dispatch_id)

    # ==================== FIRM OPERATIONS ====================

    async def create_firm(
        self,
        db: AsyncSession,
        organization_id: int,
        name: str,
        firm_type: str,
        address: str,
        city: str,
        state: str,
        country: str,
        postal_code: str,
        contact_person: str,
        phone: str,
        email: str,
        gst_number: Optional[str] = None,
        credit_limit: float = 0.0,
        notes: str = "",
    ) -> Dict:
        """Create a new firm/dealer."""
        firm_code = await self._generate_firm_code(db, organization_id, name)
        
        firm = Firm(
            firm_code=firm_code,
            name=name,
            firm_type=firm_type,
            address=address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            contact_person=contact_person,
            phone=phone,
            email=email,
            gst_number=gst_number,
            credit_limit=credit_limit,
            status="active",
            notes=notes,
            organization_id=organization_id,
        )
        db.add(firm)
        await db.commit()
        await db.refresh(firm)
        
        return self._firm_to_dict(firm)

    async def get_firm(
        self,
        db: AsyncSession,
        organization_id: int,
        firm_id: int,
    ) -> Optional[Dict]:
        """Get firm by ID."""
        stmt = select(Firm).where(
            and_(
                Firm.organization_id == organization_id,
                Firm.id == firm_id
            )
        )
        result = await db.execute(stmt)
        firm = result.scalar_one_or_none()
        
        return self._firm_to_dict(firm) if firm else None

    async def list_firms(
        self,
        db: AsyncSession,
        organization_id: int,
        firm_type: Optional[str] = None,
        status: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """List firms with filters."""
        stmt = select(Firm).where(
            Firm.organization_id == organization_id
        )
        
        if firm_type:
            stmt = stmt.where(Firm.firm_type == firm_type)
        if status:
            stmt = stmt.where(Firm.status == status)
        if city:
            stmt = stmt.where(func.lower(Firm.city) == city.lower())
        if state:
            stmt = stmt.where(func.lower(Firm.state) == state.lower())
        
        stmt = stmt.order_by(Firm.name).limit(limit)
        
        result = await db.execute(stmt)
        firms = result.scalars().all()
        
        return [self._firm_to_dict(f) for f in firms]

    async def update_firm(
        self,
        db: AsyncSession,
        organization_id: int,
        firm_id: int,
        **updates,
    ) -> Dict:
        """Update firm details."""
        stmt = select(Firm).where(
            and_(
                Firm.organization_id == organization_id,
                Firm.id == firm_id
            )
        )
        result = await db.execute(stmt)
        firm = result.scalar_one_or_none()
        
        if not firm:
            raise ValueError(f"Firm {firm_id} not found")
        
        # Update allowed fields
        allowed_fields = {
            'name', 'firm_type', 'address', 'city', 'state', 'country',
            'postal_code', 'contact_person', 'phone', 'email', 'gst_number',
            'credit_limit', 'notes', 'status'
        }
        
        for key, value in updates.items():
            if key in allowed_fields and value is not None:
                setattr(firm, key, value)
        
        await db.commit()
        await db.refresh(firm)
        
        return self._firm_to_dict(firm)

    async def deactivate_firm(
        self,
        db: AsyncSession,
        organization_id: int,
        firm_id: int,
    ) -> Dict:
        """Deactivate a firm."""
        return await self.update_firm(db, organization_id, firm_id, status="inactive")

    # ==================== STATISTICS ====================

    async def get_dispatch_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict:
        """Get dispatch statistics."""
        # Total dispatches
        total_stmt = select(func.count(Dispatch.id)).where(
            Dispatch.organization_id == organization_id
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        # By status
        status_stmt = select(
            Dispatch.status,
            func.count(Dispatch.id)
        ).where(
            Dispatch.organization_id == organization_id
        ).group_by(Dispatch.status)
        status_result = await db.execute(status_stmt)
        by_status = {row[0]: row[1] for row in status_result.all()}
        
        # By transfer type
        type_stmt = select(
            Dispatch.transfer_type,
            func.count(Dispatch.id)
        ).where(
            Dispatch.organization_id == organization_id
        ).group_by(Dispatch.transfer_type)
        type_result = await db.execute(type_stmt)
        by_type = {row[0]: row[1] for row in type_result.all()}
        
        # Totals
        totals_stmt = select(
            func.sum(Dispatch.total_quantity_kg),
            func.sum(Dispatch.total_value)
        ).where(
            Dispatch.organization_id == organization_id
        )
        totals_result = await db.execute(totals_stmt)
        totals = totals_result.one()
        
        # Firm counts
        firms_stmt = select(func.count(Firm.id)).where(
            Firm.organization_id == organization_id
        )
        firms_result = await db.execute(firms_stmt)
        total_firms = firms_result.scalar() or 0
        
        active_firms_stmt = select(func.count(Firm.id)).where(
            and_(
                Firm.organization_id == organization_id,
                Firm.status == "active"
            )
        )
        active_result = await db.execute(active_firms_stmt)
        active_firms = active_result.scalar() or 0
        
        return {
            "total_dispatches": total,
            "by_status": by_status,
            "by_transfer_type": by_type,
            "total_quantity_kg": totals[0] or 0,
            "total_value": totals[1] or 0,
            "total_firms": total_firms,
            "active_firms": active_firms,
        }

    def get_firm_types(self) -> List[Dict]:
        """Get available firm types."""
        return [
            {"id": "dealer", "name": "Dealer", "description": "Authorized seed dealer"},
            {"id": "distributor", "name": "Distributor", "description": "Regional distributor"},
            {"id": "retailer", "name": "Retailer", "description": "Retail outlet"},
            {"id": "farmer", "name": "Farmer", "description": "Direct farmer customer"},
            {"id": "institution", "name": "Institution", "description": "Research/educational institution"},
            {"id": "government", "name": "Government", "description": "Government agency"},
        ]

    def get_dispatch_statuses(self) -> List[Dict]:
        """Get available dispatch statuses."""
        return [
            {"id": s.value, "name": s.name.replace("_", " ").title()}
            for s in DispatchStatus
        ]

    # ==================== HELPER METHODS ====================

    async def _get_dispatch_or_raise(
        self,
        db: AsyncSession,
        organization_id: int,
        dispatch_id: int,
    ) -> Dispatch:
        """Get dispatch or raise ValueError."""
        stmt = select(Dispatch).where(
            and_(
                Dispatch.organization_id == organization_id,
                Dispatch.id == dispatch_id
            )
        )
        result = await db.execute(stmt)
        dispatch = result.scalar_one_or_none()
        
        if not dispatch:
            raise ValueError(f"Dispatch {dispatch_id} not found")
        
        return dispatch

    def _dispatch_to_dict(self, dispatch: Dispatch) -> Dict:
        """Convert Dispatch model to dictionary."""
        return {
            "dispatch_id": str(dispatch.id),
            "dispatch_number": dispatch.dispatch_number,
            "recipient_id": str(dispatch.recipient_id) if dispatch.recipient_id else None,
            "recipient_name": dispatch.recipient_name,
            "recipient_address": dispatch.recipient_address,
            "recipient_contact": dispatch.recipient_contact,
            "recipient_phone": dispatch.recipient_phone,
            "transfer_type": dispatch.transfer_type,
            "items": [self._item_to_dict(item) for item in dispatch.items] if dispatch.items else [],
            "total_quantity_kg": dispatch.total_quantity_kg,
            "total_value": dispatch.total_value,
            "status": dispatch.status,
            "notes": dispatch.notes,
            "created_at": dispatch.created_at.isoformat() if dispatch.created_at else None,
            "created_by": dispatch.created_by,
            "approved_at": dispatch.approved_at.isoformat() if dispatch.approved_at else None,
            "approved_by": dispatch.approved_by,
            "shipped_at": dispatch.shipped_at.isoformat() if dispatch.shipped_at else None,
            "delivered_at": dispatch.delivered_at.isoformat() if dispatch.delivered_at else None,
            "tracking_number": dispatch.tracking_number,
            "carrier": dispatch.carrier,
            "invoice_number": dispatch.invoice_number,
        }

    def _item_to_dict(self, item: DispatchItem) -> Dict:
        """Convert DispatchItem model to dictionary."""
        return {
            "item_id": str(item.id),
            "lot_id": item.lot_id,
            "variety_name": item.variety_name,
            "crop": item.crop,
            "seed_class": item.seed_class,
            "quantity_kg": item.quantity_kg,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "picked": item.picked,
            "packed": item.packed,
        }

    def _firm_to_dict(self, firm: Firm) -> Dict:
        """Convert Firm model to dictionary."""
        return {
            "firm_id": str(firm.id),
            "firm_code": firm.firm_code,
            "name": firm.name,
            "firm_type": firm.firm_type,
            "address": firm.address,
            "city": firm.city,
            "state": firm.state,
            "country": firm.country,
            "postal_code": firm.postal_code,
            "contact_person": firm.contact_person,
            "phone": firm.phone,
            "email": firm.email,
            "gst_number": firm.gst_number,
            "credit_limit": firm.credit_limit,
            "credit_used": firm.credit_used,
            "status": firm.status,
            "created_at": firm.created_at.isoformat() if firm.created_at else None,
            "notes": firm.notes,
        }


# Service instance (for backward compatibility)
dispatch_service = DispatchManagementService()


def get_dispatch_service() -> DispatchManagementService:
    return dispatch_service

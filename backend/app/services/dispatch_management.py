"""
Dispatch Management Service

Full dispatch workflow for seed company operations.
Converted to use real database queries per Zero Mock Data Policy.
"""

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import and_, func, literal, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dispatch import Dispatch, DispatchItem, Firm


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
        recipient_id: int | None,
        recipient_name: str,
        recipient_address: str,
        recipient_contact: str,
        recipient_phone: str,
        transfer_type: str,
        items: list[dict],
        notes: str = "",
        created_by: str = "system",
    ) -> dict:
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
    ) -> dict | None:
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
        status: str | None = None,
        recipient_id: int | None = None,
        transfer_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict]:
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
    ) -> dict:
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
    ) -> dict:
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
    ) -> dict:
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
    ) -> dict:
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
        tracking_number: str | None = None,
        carrier: str | None = None,
        invoice_number: str | None = None,
    ) -> dict:
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
    ) -> dict:
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
    ) -> dict:
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
        gst_number: str | None = None,
        credit_limit: float = 0.0,
        notes: str = "",
    ) -> dict:
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
    ) -> dict | None:
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
        firm_type: str | None = None,
        status: str | None = None,
        city: str | None = None,
        state: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
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
    ) -> dict:
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
    ) -> dict:
        """Deactivate a firm."""
        return await self.update_firm(db, organization_id, firm_id, status="inactive")

    # ==================== STATISTICS ====================

    async def get_dispatch_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> dict:
        """
        Get dispatch statistics.

        Optimized to reduce round-trips using combined queries.
        """
        # 1. Combined Scalars Query (Counts and Totals)
        # Subqueries for firms
        firm_count_sq = select(func.count(Firm.id)).where(
            Firm.organization_id == organization_id
        ).scalar_subquery()

        active_firm_count_sq = select(func.count(Firm.id)).where(
            and_(
                Firm.organization_id == organization_id,
                Firm.status == "active"
            )
        ).scalar_subquery()

        # Main scalar query
        scalars_stmt = select(
            func.count(Dispatch.id),
            func.sum(Dispatch.total_quantity_kg),
            func.sum(Dispatch.total_value),
            firm_count_sq,
            active_firm_count_sq
        ).where(Dispatch.organization_id == organization_id)

        scalars_result = await db.execute(scalars_stmt)
        scalars_row = scalars_result.one()

        total_dispatches = scalars_row[0] or 0
        total_quantity = scalars_row[1] or 0
        total_value = scalars_row[2] or 0
        total_firms = scalars_row[3] or 0
        active_firms = scalars_row[4] or 0

        # 2. Combined Group By Query (Status and Transfer Type)
        # Using UNION ALL to fetch both groupings in one query
        status_query = select(
            literal("status").label("category"),
            Dispatch.status.label("key"),
            func.count(Dispatch.id).label("count")
        ).where(
            Dispatch.organization_id == organization_id
        ).group_by(Dispatch.status)

        type_query = select(
            literal("type").label("category"),
            Dispatch.transfer_type.label("key"),
            func.count(Dispatch.id).label("count")
        ).where(
            Dispatch.organization_id == organization_id
        ).group_by(Dispatch.transfer_type)

        union_stmt = union_all(status_query, type_query)
        union_result = await db.execute(union_stmt)
        union_rows = union_result.all()

        by_status = {}
        by_transfer_type = {}

        for row in union_rows:
            # row is (category, key, count)
            category = row[0]
            key = row[1]
            count = row[2]

            if category == "status":
                by_status[key] = count
            elif category == "type":
                by_transfer_type[key] = count

        return {
            "total_dispatches": total_dispatches,
            "by_status": by_status,
            "by_transfer_type": by_transfer_type,
            "total_quantity_kg": total_quantity,
            "total_value": total_value,
            "total_firms": total_firms,
            "active_firms": active_firms,
        }

    def get_firm_types(self) -> list[dict]:
        """Get available firm types."""
        return [
            {"id": "dealer", "name": "Dealer", "description": "Authorized seed dealer"},
            {"id": "distributor", "name": "Distributor", "description": "Regional distributor"},
            {"id": "retailer", "name": "Retailer", "description": "Retail outlet"},
            {"id": "farmer", "name": "Farmer", "description": "Direct farmer customer"},
            {"id": "institution", "name": "Institution", "description": "Research/educational institution"},
            {"id": "government", "name": "Government", "description": "Government agency"},
        ]

    def get_dispatch_statuses(self) -> list[dict]:
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

    def _dispatch_to_dict(self, dispatch: Dispatch) -> dict:
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

    def _item_to_dict(self, item: DispatchItem) -> dict:
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

    def _firm_to_dict(self, firm: Firm) -> dict:
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

"""
Dispatch Management Service
Full dispatch workflow for seed company operations
"""

from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid


class DispatchStatus(Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PICKING = "picking"
    PACKED = "packed"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class TransferType(Enum):
    SALE = "sale"
    INTERNAL = "internal"
    DONATION = "donation"
    SAMPLE = "sample"
    RETURN = "return"


@dataclass
class DispatchItem:
    item_id: str
    lot_id: str
    variety_name: str
    crop: str
    seed_class: str
    quantity_kg: float
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    picked: bool = False
    packed: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Dispatch:
    dispatch_id: str
    dispatch_number: str
    recipient_id: str
    recipient_name: str
    recipient_address: str
    recipient_contact: str
    recipient_phone: str
    transfer_type: str
    items: List[DispatchItem]
    total_quantity_kg: float
    total_value: float
    status: str
    notes: str
    created_at: str
    created_by: str
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    shipped_at: Optional[str] = None
    delivered_at: Optional[str] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    invoice_number: Optional[str] = None

    def to_dict(self) -> Dict:
        d = asdict(self)
        d['items'] = [item.to_dict() if isinstance(item, DispatchItem) else item for item in self.items]
        return d


@dataclass
class Firm:
    firm_id: str
    firm_code: str
    name: str
    firm_type: str  # dealer, distributor, retailer, farmer, institution
    address: str
    city: str
    state: str
    country: str
    postal_code: str
    contact_person: str
    phone: str
    email: str
    gst_number: Optional[str] = None
    credit_limit: float = 0.0
    credit_used: float = 0.0
    status: str = "active"
    created_at: str = ""
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


class DispatchManagementService:
    """Service for managing seed dispatches and firms"""

    def __init__(self):
        self._dispatches: Dict[str, Dispatch] = {}
        self._firms: Dict[str, Firm] = {}
        self._dispatch_counter = 0
        self._firm_counter = 0
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize with demo firms"""
        demo_firms = [
            {
                "name": "ABC Agro Dealers",
                "firm_type": "dealer",
                "address": "123 Market Road",
                "city": "Mumbai",
                "state": "Maharashtra",
                "country": "India",
                "postal_code": "400001",
                "contact_person": "Rajesh Kumar",
                "phone": "+91-9876543210",
                "email": "rajesh@abcagro.com",
                "credit_limit": 500000,
            },
            {
                "name": "State Seed Corporation",
                "firm_type": "distributor",
                "address": "Seed Bhavan, MG Road",
                "city": "Hyderabad",
                "state": "Telangana",
                "country": "India",
                "postal_code": "500001",
                "contact_person": "Dr. Sharma",
                "phone": "+91-9876543211",
                "email": "procurement@ssc.gov.in",
                "credit_limit": 2000000,
            },
            {
                "name": "Green Fields Cooperative",
                "firm_type": "retailer",
                "address": "Village Center",
                "city": "Ludhiana",
                "state": "Punjab",
                "country": "India",
                "postal_code": "141001",
                "contact_person": "Gurpreet Singh",
                "phone": "+91-9876543212",
                "email": "greenfields@coop.in",
                "credit_limit": 100000,
            },
        ]
        for firm_data in demo_firms:
            self.create_firm(**firm_data)

    def _generate_dispatch_number(self) -> str:
        self._dispatch_counter += 1
        return f"DSP-{datetime.now().year}-{self._dispatch_counter:04d}"

    def _generate_firm_code(self, name: str) -> str:
        self._firm_counter += 1
        prefix = ''.join(word[0].upper() for word in name.split()[:3])
        return f"{prefix}-{self._firm_counter:03d}"

    # ==================== DISPATCH OPERATIONS ====================

    def create_dispatch(
        self,
        recipient_id: str,
        recipient_name: str,
        recipient_address: str,
        recipient_contact: str,
        recipient_phone: str,
        transfer_type: str,
        items: List[Dict],
        notes: str = "",
        created_by: str = "system",
    ) -> Dispatch:
        """Create a new dispatch order"""
        dispatch_id = str(uuid.uuid4())
        dispatch_number = self._generate_dispatch_number()

        dispatch_items = []
        total_qty = 0.0
        total_value = 0.0

        for item in items:
            item_id = str(uuid.uuid4())
            qty = item.get("quantity_kg", 0)
            price = item.get("unit_price", 0) or 0
            total = qty * price

            dispatch_items.append(DispatchItem(
                item_id=item_id,
                lot_id=item["lot_id"],
                variety_name=item.get("variety_name", ""),
                crop=item.get("crop", ""),
                seed_class=item.get("seed_class", "certified"),
                quantity_kg=qty,
                unit_price=price if price > 0 else None,
                total_price=total if total > 0 else None,
            ))
            total_qty += qty
            total_value += total

        dispatch = Dispatch(
            dispatch_id=dispatch_id,
            dispatch_number=dispatch_number,
            recipient_id=recipient_id,
            recipient_name=recipient_name,
            recipient_address=recipient_address,
            recipient_contact=recipient_contact,
            recipient_phone=recipient_phone,
            transfer_type=transfer_type,
            items=dispatch_items,
            total_quantity_kg=total_qty,
            total_value=total_value,
            status=DispatchStatus.DRAFT.value,
            notes=notes,
            created_at=datetime.now(UTC).isoformat(),
            created_by=created_by,
        )

        self._dispatches[dispatch_id] = dispatch
        return dispatch

    def get_dispatch(self, dispatch_id: str) -> Optional[Dict]:
        """Get dispatch by ID"""
        dispatch = self._dispatches.get(dispatch_id)
        return dispatch.to_dict() if dispatch else None

    def list_dispatches(
        self,
        status: Optional[str] = None,
        recipient_id: Optional[str] = None,
        transfer_type: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict]:
        """List dispatches with filters"""
        results = []
        for dispatch in self._dispatches.values():
            if status and dispatch.status != status:
                continue
            if recipient_id and dispatch.recipient_id != recipient_id:
                continue
            if transfer_type and dispatch.transfer_type != transfer_type:
                continue
            if from_date and dispatch.created_at < from_date:
                continue
            if to_date and dispatch.created_at > to_date:
                continue
            results.append(dispatch.to_dict())
        return sorted(results, key=lambda x: x["created_at"], reverse=True)

    def submit_for_approval(self, dispatch_id: str) -> Dict:
        """Submit dispatch for approval"""
        dispatch = self._dispatches.get(dispatch_id)
        if not dispatch:
            raise ValueError(f"Dispatch {dispatch_id} not found")
        if dispatch.status != DispatchStatus.DRAFT.value:
            raise ValueError(f"Cannot submit dispatch in {dispatch.status} status")

        dispatch.status = DispatchStatus.PENDING_APPROVAL.value
        return dispatch.to_dict()

    def approve_dispatch(self, dispatch_id: str, approved_by: str) -> Dict:
        """Approve a dispatch"""
        dispatch = self._dispatches.get(dispatch_id)
        if not dispatch:
            raise ValueError(f"Dispatch {dispatch_id} not found")
        if dispatch.status != DispatchStatus.PENDING_APPROVAL.value:
            raise ValueError(f"Cannot approve dispatch in {dispatch.status} status")

        dispatch.status = DispatchStatus.APPROVED.value
        dispatch.approved_at = datetime.now(UTC).isoformat()
        dispatch.approved_by = approved_by
        return dispatch.to_dict()

    def start_picking(self, dispatch_id: str) -> Dict:
        """Start picking process"""
        dispatch = self._dispatches.get(dispatch_id)
        if not dispatch:
            raise ValueError(f"Dispatch {dispatch_id} not found")
        if dispatch.status != DispatchStatus.APPROVED.value:
            raise ValueError(f"Cannot start picking for dispatch in {dispatch.status} status")

        dispatch.status = DispatchStatus.PICKING.value
        return dispatch.to_dict()

    def mark_item_picked(self, dispatch_id: str, item_id: str) -> Dict:
        """Mark an item as picked"""
        dispatch = self._dispatches.get(dispatch_id)
        if not dispatch:
            raise ValueError(f"Dispatch {dispatch_id} not found")

        for item in dispatch.items:
            if item.item_id == item_id:
                item.picked = True
                break

        # Check if all items picked
        if all(item.picked for item in dispatch.items):
            dispatch.status = DispatchStatus.PACKED.value

        return dispatch.to_dict()

    def ship_dispatch(
        self,
        dispatch_id: str,
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None,
        invoice_number: Optional[str] = None,
    ) -> Dict:
        """Mark dispatch as shipped"""
        dispatch = self._dispatches.get(dispatch_id)
        if not dispatch:
            raise ValueError(f"Dispatch {dispatch_id} not found")
        if dispatch.status not in [DispatchStatus.APPROVED.value, DispatchStatus.PACKED.value]:
            raise ValueError(f"Cannot ship dispatch in {dispatch.status} status")

        dispatch.status = DispatchStatus.SHIPPED.value
        dispatch.shipped_at = datetime.now(UTC).isoformat()
        dispatch.tracking_number = tracking_number
        dispatch.carrier = carrier
        dispatch.invoice_number = invoice_number
        return dispatch.to_dict()

    def mark_delivered(self, dispatch_id: str, delivery_notes: str = "") -> Dict:
        """Mark dispatch as delivered"""
        dispatch = self._dispatches.get(dispatch_id)
        if not dispatch:
            raise ValueError(f"Dispatch {dispatch_id} not found")
        if dispatch.status not in [DispatchStatus.SHIPPED.value, DispatchStatus.IN_TRANSIT.value]:
            raise ValueError(f"Cannot mark delivered for dispatch in {dispatch.status} status")

        dispatch.status = DispatchStatus.DELIVERED.value
        dispatch.delivered_at = datetime.now(UTC).isoformat()
        if delivery_notes:
            dispatch.notes = f"{dispatch.notes}\nDelivery: {delivery_notes}"
        return dispatch.to_dict()

    def cancel_dispatch(self, dispatch_id: str, reason: str) -> Dict:
        """Cancel a dispatch"""
        dispatch = self._dispatches.get(dispatch_id)
        if not dispatch:
            raise ValueError(f"Dispatch {dispatch_id} not found")
        if dispatch.status in [DispatchStatus.DELIVERED.value]:
            raise ValueError("Cannot cancel delivered dispatch")

        dispatch.status = DispatchStatus.CANCELLED.value
        dispatch.notes = f"{dispatch.notes}\nCancelled: {reason}"
        return dispatch.to_dict()

    # ==================== FIRM OPERATIONS ====================

    def create_firm(
        self,
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
    ) -> Firm:
        """Create a new firm/dealer"""
        firm_id = str(uuid.uuid4())
        firm_code = self._generate_firm_code(name)

        firm = Firm(
            firm_id=firm_id,
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
            created_at=datetime.now(UTC).isoformat(),
            notes=notes,
        )

        self._firms[firm_id] = firm
        return firm

    def get_firm(self, firm_id: str) -> Optional[Dict]:
        """Get firm by ID"""
        firm = self._firms.get(firm_id)
        return firm.to_dict() if firm else None

    def list_firms(
        self,
        firm_type: Optional[str] = None,
        status: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
    ) -> List[Dict]:
        """List firms with filters"""
        results = []
        for firm in self._firms.values():
            if firm_type and firm.firm_type != firm_type:
                continue
            if status and firm.status != status:
                continue
            if city and firm.city.lower() != city.lower():
                continue
            if state and firm.state.lower() != state.lower():
                continue
            results.append(firm.to_dict())
        return sorted(results, key=lambda x: x["name"])

    def update_firm(self, firm_id: str, **updates) -> Dict:
        """Update firm details"""
        firm = self._firms.get(firm_id)
        if not firm:
            raise ValueError(f"Firm {firm_id} not found")

        for key, value in updates.items():
            if hasattr(firm, key) and value is not None:
                setattr(firm, key, value)

        return firm.to_dict()

    def deactivate_firm(self, firm_id: str) -> Dict:
        """Deactivate a firm"""
        firm = self._firms.get(firm_id)
        if not firm:
            raise ValueError(f"Firm {firm_id} not found")

        firm.status = "inactive"
        return firm.to_dict()

    # ==================== STATISTICS ====================

    def get_dispatch_statistics(self) -> Dict:
        """Get dispatch statistics"""
        total = len(self._dispatches)
        by_status = {}
        by_type = {}
        total_qty = 0.0
        total_value = 0.0

        for dispatch in self._dispatches.values():
            by_status[dispatch.status] = by_status.get(dispatch.status, 0) + 1
            by_type[dispatch.transfer_type] = by_type.get(dispatch.transfer_type, 0) + 1
            total_qty += dispatch.total_quantity_kg
            total_value += dispatch.total_value

        return {
            "total_dispatches": total,
            "by_status": by_status,
            "by_transfer_type": by_type,
            "total_quantity_kg": total_qty,
            "total_value": total_value,
            "total_firms": len(self._firms),
            "active_firms": sum(1 for f in self._firms.values() if f.status == "active"),
        }

    def get_firm_types(self) -> List[Dict]:
        """Get available firm types"""
        return [
            {"id": "dealer", "name": "Dealer", "description": "Authorized seed dealer"},
            {"id": "distributor", "name": "Distributor", "description": "Regional distributor"},
            {"id": "retailer", "name": "Retailer", "description": "Retail outlet"},
            {"id": "farmer", "name": "Farmer", "description": "Direct farmer customer"},
            {"id": "institution", "name": "Institution", "description": "Research/educational institution"},
            {"id": "government", "name": "Government", "description": "Government agency"},
        ]

    def get_dispatch_statuses(self) -> List[Dict]:
        """Get available dispatch statuses"""
        return [
            {"id": s.value, "name": s.name.replace("_", " ").title()}
            for s in DispatchStatus
        ]


# Singleton instance
dispatch_service = DispatchManagementService()


def get_dispatch_service() -> DispatchManagementService:
    return dispatch_service

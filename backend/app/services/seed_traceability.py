"""
Seed Traceability Service
Track seed lots from origin through production to final sale
Supports chain of custody, certifications, and regulatory compliance
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any
from uuid import uuid4
from enum import Enum


class TraceabilityEventType(str, Enum):
    HARVEST = "harvest"
    PROCESSING = "processing"
    TESTING = "testing"
    CERTIFICATION = "certification"
    STORAGE = "storage"
    TRANSFER = "transfer"
    TREATMENT = "treatment"
    PACKAGING = "packaging"
    SHIPPING = "shipping"
    SALE = "sale"
    RECALL = "recall"


class SeedClass(str, Enum):
    BREEDER = "breeder"
    PRE_BASIC = "pre_basic"
    BASIC = "basic"
    CERTIFIED_1 = "certified_1"
    CERTIFIED_2 = "certified_2"
    TRUTHFUL = "truthful"


class SeedTraceabilityService:
    """Service for seed lot traceability and chain of custody"""

    def __init__(self):
        # In-memory storage (replace with database in production)
        self.seed_lots: Dict[str, Dict] = {}
        self.events: Dict[str, List[Dict]] = {}
        self.certifications: Dict[str, List[Dict]] = {}
        self.transfers: Dict[str, List[Dict]] = {}

        # Initialize with sample data
        self._init_sample_data()

    def _init_sample_data(self):
        """Initialize with sample seed lots"""
        sample_lots = [
            {
                "lot_id": "LOT-2024-001",
                "variety_id": "VAR-001",
                "variety_name": "IR64",
                "crop": "Rice",
                "seed_class": SeedClass.CERTIFIED_1,
                "parent_lot_id": "LOT-2023-050",
                "production_year": 2024,
                "production_season": "Kharif",
                "production_location": "Punjab, India",
                "producer_id": "PROD-001",
                "producer_name": "State Seed Farm",
                "initial_quantity_kg": 5000,
                "current_quantity_kg": 4200,
                "germination_percent": 92,
                "purity_percent": 99.5,
                "moisture_percent": 12,
                "status": "available",
                "created_at": datetime.now().isoformat(),
            },
            {
                "lot_id": "LOT-2024-002",
                "variety_id": "VAR-002",
                "variety_name": "HD-2967",
                "crop": "Wheat",
                "seed_class": SeedClass.BASIC,
                "parent_lot_id": "LOT-2023-025",
                "production_year": 2024,
                "production_season": "Rabi",
                "production_location": "Haryana, India",
                "producer_id": "PROD-002",
                "producer_name": "ICAR Research Station",
                "initial_quantity_kg": 2000,
                "current_quantity_kg": 1800,
                "germination_percent": 95,
                "purity_percent": 99.8,
                "moisture_percent": 11,
                "status": "available",
                "created_at": datetime.now().isoformat(),
            },
        ]

        for lot in sample_lots:
            self.seed_lots[lot["lot_id"]] = lot
            self.events[lot["lot_id"]] = []
            self.certifications[lot["lot_id"]] = []
            self.transfers[lot["lot_id"]] = []

    def register_lot(
        self,
        variety_id: str,
        variety_name: str,
        crop: str,
        seed_class: str,
        production_year: int,
        production_season: str,
        production_location: str,
        producer_id: str,
        producer_name: str,
        quantity_kg: float,
        parent_lot_id: Optional[str] = None,
        germination_percent: Optional[float] = None,
        purity_percent: Optional[float] = None,
        moisture_percent: Optional[float] = None,
    ) -> Dict:
        """Register a new seed lot"""
        lot_id = f"LOT-{datetime.now().year}-{str(uuid4())[:8].upper()}"

        lot = {
            "lot_id": lot_id,
            "variety_id": variety_id,
            "variety_name": variety_name,
            "crop": crop,
            "seed_class": seed_class,
            "parent_lot_id": parent_lot_id,
            "production_year": production_year,
            "production_season": production_season,
            "production_location": production_location,
            "producer_id": producer_id,
            "producer_name": producer_name,
            "initial_quantity_kg": quantity_kg,
            "current_quantity_kg": quantity_kg,
            "germination_percent": germination_percent,
            "purity_percent": purity_percent,
            "moisture_percent": moisture_percent,
            "status": "registered",
            "created_at": datetime.now().isoformat(),
        }

        self.seed_lots[lot_id] = lot
        self.events[lot_id] = []
        self.certifications[lot_id] = []
        self.transfers[lot_id] = []

        # Record registration event
        self.record_event(lot_id, TraceabilityEventType.HARVEST, {
            "description": "Seed lot registered",
            "quantity_kg": quantity_kg,
            "location": production_location,
        })

        return lot

    def get_lot(self, lot_id: str) -> Optional[Dict]:
        """Get seed lot details"""
        return self.seed_lots.get(lot_id)

    def list_lots(
        self,
        crop: Optional[str] = None,
        variety_id: Optional[str] = None,
        seed_class: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """List seed lots with optional filters"""
        lots = list(self.seed_lots.values())

        if crop:
            lots = [l for l in lots if l["crop"].lower() == crop.lower()]
        if variety_id:
            lots = [l for l in lots if l["variety_id"] == variety_id]
        if seed_class:
            lots = [l for l in lots if l["seed_class"] == seed_class]
        if status:
            lots = [l for l in lots if l["status"] == status]

        return lots

    def record_event(
        self,
        lot_id: str,
        event_type: TraceabilityEventType,
        details: Dict[str, Any],
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict:
        """Record a traceability event for a seed lot"""
        if lot_id not in self.seed_lots:
            raise ValueError(f"Lot {lot_id} not found")

        event = {
            "event_id": str(uuid4()),
            "lot_id": lot_id,
            "event_type": event_type.value if isinstance(event_type, TraceabilityEventType) else event_type,
            "timestamp": datetime.now().isoformat(),
            "operator_id": operator_id,
            "operator_name": operator_name,
            "location": location,
            "details": details,
        }

        self.events[lot_id].append(event)

        # Update lot status based on event type
        if event_type == TraceabilityEventType.CERTIFICATION:
            self.seed_lots[lot_id]["status"] = "certified"
        elif event_type == TraceabilityEventType.RECALL:
            self.seed_lots[lot_id]["status"] = "recalled"
        elif event_type == TraceabilityEventType.SALE:
            self.seed_lots[lot_id]["status"] = "sold"

        return event

    def get_lot_history(self, lot_id: str) -> List[Dict]:
        """Get complete event history for a seed lot"""
        if lot_id not in self.events:
            return []
        return sorted(self.events[lot_id], key=lambda x: x["timestamp"])

    def add_certification(
        self,
        lot_id: str,
        cert_type: str,
        cert_number: str,
        issuing_authority: str,
        issue_date: str,
        expiry_date: str,
        test_results: Optional[Dict] = None,
    ) -> Dict:
        """Add certification to a seed lot"""
        if lot_id not in self.seed_lots:
            raise ValueError(f"Lot {lot_id} not found")

        cert = {
            "cert_id": str(uuid4()),
            "lot_id": lot_id,
            "cert_type": cert_type,
            "cert_number": cert_number,
            "issuing_authority": issuing_authority,
            "issue_date": issue_date,
            "expiry_date": expiry_date,
            "test_results": test_results or {},
            "status": "valid",
            "created_at": datetime.now().isoformat(),
        }

        self.certifications[lot_id].append(cert)

        # Record certification event
        self.record_event(lot_id, TraceabilityEventType.CERTIFICATION, {
            "cert_type": cert_type,
            "cert_number": cert_number,
            "issuing_authority": issuing_authority,
        })

        return cert

    def get_certifications(self, lot_id: str) -> List[Dict]:
        """Get all certifications for a seed lot"""
        return self.certifications.get(lot_id, [])

    def record_transfer(
        self,
        lot_id: str,
        from_entity_id: str,
        from_entity_name: str,
        to_entity_id: str,
        to_entity_name: str,
        quantity_kg: float,
        transfer_type: str,  # sale, donation, internal
        price_per_kg: Optional[float] = None,
        invoice_number: Optional[str] = None,
    ) -> Dict:
        """Record transfer of seed lot ownership"""
        if lot_id not in self.seed_lots:
            raise ValueError(f"Lot {lot_id} not found")

        lot = self.seed_lots[lot_id]
        if quantity_kg > lot["current_quantity_kg"]:
            raise ValueError(f"Insufficient quantity. Available: {lot['current_quantity_kg']} kg")

        transfer = {
            "transfer_id": str(uuid4()),
            "lot_id": lot_id,
            "from_entity_id": from_entity_id,
            "from_entity_name": from_entity_name,
            "to_entity_id": to_entity_id,
            "to_entity_name": to_entity_name,
            "quantity_kg": quantity_kg,
            "transfer_type": transfer_type,
            "price_per_kg": price_per_kg,
            "total_value": price_per_kg * quantity_kg if price_per_kg else None,
            "invoice_number": invoice_number,
            "timestamp": datetime.now().isoformat(),
        }

        self.transfers[lot_id].append(transfer)

        # Update quantity
        lot["current_quantity_kg"] -= quantity_kg

        # Record event
        event_type = TraceabilityEventType.SALE if transfer_type == "sale" else TraceabilityEventType.TRANSFER
        self.record_event(lot_id, event_type, {
            "from": from_entity_name,
            "to": to_entity_name,
            "quantity_kg": quantity_kg,
            "transfer_type": transfer_type,
        })

        return transfer

    def get_transfers(self, lot_id: str) -> List[Dict]:
        """Get all transfers for a seed lot"""
        return self.transfers.get(lot_id, [])

    def trace_lineage(self, lot_id: str) -> Dict:
        """Trace complete lineage of a seed lot (parent chain)"""
        if lot_id not in self.seed_lots:
            return {"error": f"Lot {lot_id} not found"}

        lineage = []
        current_lot = self.seed_lots[lot_id]

        while current_lot:
            lineage.append({
                "lot_id": current_lot["lot_id"],
                "variety_name": current_lot["variety_name"],
                "seed_class": current_lot["seed_class"],
                "production_year": current_lot["production_year"],
                "producer_name": current_lot["producer_name"],
            })

            parent_id = current_lot.get("parent_lot_id")
            current_lot = self.seed_lots.get(parent_id) if parent_id else None

        return {
            "lot_id": lot_id,
            "lineage": lineage,
            "generations": len(lineage),
        }

    def get_descendants(self, lot_id: str) -> List[Dict]:
        """Find all seed lots derived from this lot"""
        descendants = []
        for lot in self.seed_lots.values():
            if lot.get("parent_lot_id") == lot_id:
                descendants.append({
                    "lot_id": lot["lot_id"],
                    "variety_name": lot["variety_name"],
                    "seed_class": lot["seed_class"],
                    "production_year": lot["production_year"],
                    "quantity_kg": lot["current_quantity_kg"],
                })
        return descendants

    def generate_qr_data(self, lot_id: str) -> Dict:
        """Generate data for QR code label"""
        lot = self.seed_lots.get(lot_id)
        if not lot:
            return {"error": f"Lot {lot_id} not found"}

        certs = self.certifications.get(lot_id, [])
        valid_certs = [c for c in certs if c["status"] == "valid"]

        return {
            "lot_id": lot_id,
            "variety": lot["variety_name"],
            "crop": lot["crop"],
            "class": lot["seed_class"],
            "producer": lot["producer_name"],
            "year": lot["production_year"],
            "germination": lot.get("germination_percent"),
            "purity": lot.get("purity_percent"),
            "certified": len(valid_certs) > 0,
            "cert_numbers": [c["cert_number"] for c in valid_certs],
            "trace_url": f"/trace/{lot_id}",
        }

    def get_statistics(self) -> Dict:
        """Get traceability statistics"""
        lots = list(self.seed_lots.values())

        by_class = {}
        by_crop = {}
        by_status = {}
        total_quantity = 0

        for lot in lots:
            # By class
            cls = lot["seed_class"]
            by_class[cls] = by_class.get(cls, 0) + 1

            # By crop
            crop = lot["crop"]
            by_crop[crop] = by_crop.get(crop, 0) + 1

            # By status
            status = lot["status"]
            by_status[status] = by_status.get(status, 0) + 1

            # Total quantity
            total_quantity += lot["current_quantity_kg"]

        total_events = sum(len(e) for e in self.events.values())
        total_transfers = sum(len(t) for t in self.transfers.values())

        return {
            "total_lots": len(lots),
            "total_quantity_kg": total_quantity,
            "total_events": total_events,
            "total_transfers": total_transfers,
            "by_seed_class": by_class,
            "by_crop": by_crop,
            "by_status": by_status,
        }


# Singleton instance
seed_traceability_service = SeedTraceabilityService()

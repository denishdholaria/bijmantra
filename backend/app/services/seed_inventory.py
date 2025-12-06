"""
Seed Inventory Service for Seed Bank Management
Seed lot tracking, viability testing, and inventory management

Features:
- Seed lot registration and tracking
- Viability testing and germination records
- Storage location management
- Seed requests and distribution
- Inventory alerts and reporting
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SeedStatus(str, Enum):
    ACTIVE = "active"
    LOW_STOCK = "low_stock"
    DEPLETED = "depleted"
    EXPIRED = "expired"
    QUARANTINE = "quarantine"


class StorageType(str, Enum):
    SHORT_TERM = "short_term"  # 5-10 years, 5°C
    MEDIUM_TERM = "medium_term"  # 10-20 years, -5°C
    LONG_TERM = "long_term"  # 50+ years, -18°C
    CRYO = "cryo"  # Cryopreservation, -196°C


@dataclass
class SeedLot:
    """Seed lot record"""
    lot_id: str
    accession_id: str
    species: str
    variety: str
    harvest_date: date
    initial_quantity: float  # grams
    current_quantity: float
    storage_type: StorageType
    storage_location: str
    initial_viability: float  # percentage
    current_viability: Optional[float] = None
    last_viability_test: Optional[date] = None
    status: SeedStatus = SeedStatus.ACTIVE
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "lot_id": self.lot_id,
            "accession_id": self.accession_id,
            "species": self.species,
            "variety": self.variety,
            "harvest_date": self.harvest_date.isoformat(),
            "initial_quantity_g": self.initial_quantity,
            "current_quantity_g": self.current_quantity,
            "storage_type": self.storage_type.value,
            "storage_location": self.storage_location,
            "initial_viability_percent": self.initial_viability,
            "current_viability_percent": self.current_viability,
            "last_viability_test": self.last_viability_test.isoformat() if self.last_viability_test else None,
            "status": self.status.value,
            "notes": self.notes,
        }


@dataclass
class ViabilityTest:
    """Viability test record"""
    test_id: str
    lot_id: str
    test_date: date
    seeds_tested: int
    seeds_germinated: int
    germination_percent: float
    test_method: str
    tester: str
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "lot_id": self.lot_id,
            "test_date": self.test_date.isoformat(),
            "seeds_tested": self.seeds_tested,
            "seeds_germinated": self.seeds_germinated,
            "germination_percent": round(self.germination_percent, 1),
            "test_method": self.test_method,
            "tester": self.tester,
            "notes": self.notes,
        }


@dataclass
class SeedRequest:
    """Seed distribution request"""
    request_id: str
    lot_id: str
    requester: str
    institution: str
    quantity_requested: float
    quantity_approved: Optional[float] = None
    purpose: str = ""
    request_date: date = field(default_factory=date.today)
    status: str = "pending"  # pending, approved, shipped, completed, rejected
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "lot_id": self.lot_id,
            "requester": self.requester,
            "institution": self.institution,
            "quantity_requested_g": self.quantity_requested,
            "quantity_approved_g": self.quantity_approved,
            "purpose": self.purpose,
            "request_date": self.request_date.isoformat(),
            "status": self.status,
        }


class SeedInventoryService:
    """
    Seed inventory management for seed banks
    """
    
    def __init__(self):
        self.seed_lots: Dict[str, SeedLot] = {}
        self.viability_tests: Dict[str, List[ViabilityTest]] = {}  # lot_id -> tests
        self.requests: Dict[str, SeedRequest] = {}
        self._lot_counter = 0
        self._test_counter = 0
        self._request_counter = 0
    
    def register_seed_lot(
        self,
        accession_id: str,
        species: str,
        variety: str,
        harvest_date: str,
        quantity: float,
        storage_type: str,
        storage_location: str,
        initial_viability: float,
        notes: str = ""
    ) -> SeedLot:
        """
        Register a new seed lot
        
        Args:
            accession_id: Accession identifier
            species: Species name
            variety: Variety/cultivar name
            harvest_date: Date of harvest (YYYY-MM-DD)
            quantity: Initial quantity in grams
            storage_type: Storage type (short_term, medium_term, long_term, cryo)
            storage_location: Storage location code
            initial_viability: Initial germination percentage
            notes: Additional notes
            
        Returns:
            Registered SeedLot
        """
        self._lot_counter += 1
        lot_id = f"LOT-{self._lot_counter:06d}"
        
        lot = SeedLot(
            lot_id=lot_id,
            accession_id=accession_id,
            species=species,
            variety=variety,
            harvest_date=date.fromisoformat(harvest_date),
            initial_quantity=quantity,
            current_quantity=quantity,
            storage_type=StorageType(storage_type),
            storage_location=storage_location,
            initial_viability=initial_viability,
            current_viability=initial_viability,
            last_viability_test=date.fromisoformat(harvest_date),
            notes=notes,
        )
        
        self.seed_lots[lot_id] = lot
        self.viability_tests[lot_id] = []
        
        return lot
    
    def record_viability_test(
        self,
        lot_id: str,
        test_date: str,
        seeds_tested: int,
        seeds_germinated: int,
        test_method: str,
        tester: str,
        notes: str = ""
    ) -> ViabilityTest:
        """
        Record a viability test result
        
        Args:
            lot_id: Seed lot identifier
            test_date: Date of test (YYYY-MM-DD)
            seeds_tested: Number of seeds tested
            seeds_germinated: Number that germinated
            test_method: Testing method used
            tester: Person who conducted test
            notes: Additional notes
            
        Returns:
            ViabilityTest record
        """
        if lot_id not in self.seed_lots:
            raise ValueError(f"Seed lot {lot_id} not found")
        
        self._test_counter += 1
        test_id = f"VT-{self._test_counter:06d}"
        
        germination_percent = (seeds_germinated / seeds_tested * 100) if seeds_tested > 0 else 0
        
        test = ViabilityTest(
            test_id=test_id,
            lot_id=lot_id,
            test_date=date.fromisoformat(test_date),
            seeds_tested=seeds_tested,
            seeds_germinated=seeds_germinated,
            germination_percent=germination_percent,
            test_method=test_method,
            tester=tester,
            notes=notes,
        )
        
        self.viability_tests[lot_id].append(test)
        
        # Update lot viability
        lot = self.seed_lots[lot_id]
        lot.current_viability = germination_percent
        lot.last_viability_test = date.fromisoformat(test_date)
        
        # Update status if viability is low
        if germination_percent < 50:
            lot.status = SeedStatus.EXPIRED
        
        return test
    
    def create_request(
        self,
        lot_id: str,
        requester: str,
        institution: str,
        quantity: float,
        purpose: str = ""
    ) -> SeedRequest:
        """
        Create a seed distribution request
        
        Args:
            lot_id: Seed lot identifier
            requester: Name of requester
            institution: Requesting institution
            quantity: Quantity requested in grams
            purpose: Purpose of request
            
        Returns:
            SeedRequest record
        """
        if lot_id not in self.seed_lots:
            raise ValueError(f"Seed lot {lot_id} not found")
        
        self._request_counter += 1
        request_id = f"REQ-{self._request_counter:06d}"
        
        request = SeedRequest(
            request_id=request_id,
            lot_id=lot_id,
            requester=requester,
            institution=institution,
            quantity_requested=quantity,
            purpose=purpose,
        )
        
        self.requests[request_id] = request
        return request
    
    def approve_request(
        self,
        request_id: str,
        quantity_approved: float
    ) -> SeedRequest:
        """Approve a seed request"""
        if request_id not in self.requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self.requests[request_id]
        lot = self.seed_lots[request.lot_id]
        
        if quantity_approved > lot.current_quantity:
            raise ValueError(f"Insufficient stock. Available: {lot.current_quantity}g")
        
        request.quantity_approved = quantity_approved
        request.status = "approved"
        
        return request
    
    def ship_request(self, request_id: str) -> SeedRequest:
        """Mark request as shipped and deduct from inventory"""
        if request_id not in self.requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self.requests[request_id]
        
        if request.status != "approved":
            raise ValueError(f"Request must be approved before shipping")
        
        lot = self.seed_lots[request.lot_id]
        
        # Deduct from inventory
        lot.current_quantity -= request.quantity_approved
        
        # Update lot status
        if lot.current_quantity <= 0:
            lot.status = SeedStatus.DEPLETED
        elif lot.current_quantity < lot.initial_quantity * 0.1:
            lot.status = SeedStatus.LOW_STOCK
        
        request.status = "shipped"
        return request
    
    def get_lot(self, lot_id: str) -> Optional[Dict[str, Any]]:
        """Get seed lot details"""
        if lot_id not in self.seed_lots:
            return None
        return self.seed_lots[lot_id].to_dict()
    
    def list_lots(
        self,
        species: Optional[str] = None,
        status: Optional[str] = None,
        storage_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List seed lots with optional filters"""
        result = []
        for lot in self.seed_lots.values():
            if species and lot.species != species:
                continue
            if status and lot.status.value != status:
                continue
            if storage_type and lot.storage_type.value != storage_type:
                continue
            result.append(lot.to_dict())
        return result
    
    def get_viability_history(self, lot_id: str) -> List[Dict[str, Any]]:
        """Get viability test history for a lot"""
        if lot_id not in self.viability_tests:
            return []
        return [t.to_dict() for t in self.viability_tests[lot_id]]
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get inventory summary statistics"""
        total_lots = len(self.seed_lots)
        total_quantity = sum(lot.current_quantity for lot in self.seed_lots.values())
        
        by_status = {}
        by_storage = {}
        by_species = {}
        
        for lot in self.seed_lots.values():
            # By status
            status = lot.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            # By storage type
            storage = lot.storage_type.value
            by_storage[storage] = by_storage.get(storage, 0) + 1
            
            # By species
            species = lot.species
            if species not in by_species:
                by_species[species] = {"lots": 0, "quantity_g": 0}
            by_species[species]["lots"] += 1
            by_species[species]["quantity_g"] += lot.current_quantity
        
        # Lots needing viability test (> 1 year since last test)
        today = date.today()
        needs_testing = []
        for lot in self.seed_lots.values():
            if lot.last_viability_test:
                days_since = (today - lot.last_viability_test).days
                if days_since > 365:
                    needs_testing.append({
                        "lot_id": lot.lot_id,
                        "days_since_test": days_since,
                        "last_viability": lot.current_viability,
                    })
        
        return {
            "total_lots": total_lots,
            "total_quantity_g": round(total_quantity, 2),
            "by_status": by_status,
            "by_storage_type": by_storage,
            "by_species": by_species,
            "lots_needing_viability_test": needs_testing[:10],
            "pending_requests": len([r for r in self.requests.values() if r.status == "pending"]),
        }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get inventory alerts"""
        alerts = []
        today = date.today()
        
        for lot in self.seed_lots.values():
            # Low stock alert
            if lot.status == SeedStatus.LOW_STOCK:
                alerts.append({
                    "type": "low_stock",
                    "severity": "warning",
                    "lot_id": lot.lot_id,
                    "message": f"Low stock: {lot.current_quantity}g remaining",
                })
            
            # Expired/low viability alert
            if lot.current_viability and lot.current_viability < 70:
                alerts.append({
                    "type": "low_viability",
                    "severity": "warning" if lot.current_viability >= 50 else "critical",
                    "lot_id": lot.lot_id,
                    "message": f"Low viability: {lot.current_viability}%",
                })
            
            # Viability test overdue
            if lot.last_viability_test:
                days_since = (today - lot.last_viability_test).days
                if days_since > 365:
                    alerts.append({
                        "type": "test_overdue",
                        "severity": "info",
                        "lot_id": lot.lot_id,
                        "message": f"Viability test overdue by {days_since - 365} days",
                    })
        
        return sorted(alerts, key=lambda x: {"critical": 0, "warning": 1, "info": 2}[x["severity"]])


# Singleton
_seed_inventory_service: Optional[SeedInventoryService] = None


def get_seed_inventory_service() -> SeedInventoryService:
    """Get or create seed inventory service singleton"""
    global _seed_inventory_service
    if _seed_inventory_service is None:
        _seed_inventory_service = SeedInventoryService()
    return _seed_inventory_service

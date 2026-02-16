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
import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.germplasm import Seedlot, SeedlotTransaction
from app.services.analytics.etl_service import ETLService

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
class SeedLotDTO:
    """Seed lot data transfer object"""
    lot_id: str
    accession_id: str  # Legacy text ref
    accession_uuid: Optional[str] # UUID link
    species: str
    variety: str
    harvest_date: date
    initial_quantity: float  # grams
    current_quantity: float
    storage_type: str
    storage_location: str
    initial_viability: float  # percentage
    current_viability: Optional[float] = None
    last_viability_test: Optional[date] = None
    status: str = "active"
    notes: str = ""

    # Extended fields
    seed_class: Optional[str] = None
    purity_percent: Optional[float] = None
    moisture_percent: Optional[float] = None
    production_year: Optional[int] = None
    producer_name: Optional[str] = None
    production_location: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lot_id": self.lot_id,
            "accession_id": self.accession_id,
            "accession_uuid": self.accession_uuid,
            "species": self.species,
            "variety": self.variety,
            "harvest_date": self.harvest_date.isoformat() if self.harvest_date else None,
            "initial_quantity_g": self.initial_quantity,
            "current_quantity_g": self.current_quantity,
            "quantity_kg": round(self.current_quantity / 1000, 3) if self.current_quantity else 0,
            "storage_type": self.storage_type,
            "storage_location": self.storage_location,
            "initial_viability_percent": self.initial_viability,
            "current_viability_percent": self.current_viability,
            "germination_percent": self.current_viability, # Alias for frontend
            "last_viability_test": self.last_viability_test.isoformat() if self.last_viability_test else None,
            "status": self.status,
            "notes": self.notes,

            # Extended fields
            "seed_class": self.seed_class,
            "purity_percent": self.purity_percent,
            "moisture_percent": self.moisture_percent,
            "production_year": self.production_year,
            "producer_name": self.producer_name,
            "production_location": self.production_location,
        }

    @classmethod
    def from_model(cls, model: Seedlot) -> "SeedLotDTO":
        """Create DTO from SQLAlchemy model"""
        info = model.additional_info or {}

        # Handle dates safely
        harvest_date = None
        if info.get("harvest_date"):
            try:
                harvest_date = date.fromisoformat(info["harvest_date"])
            except (ValueError, TypeError):
                pass

        last_test = None
        if info.get("last_viability_test"):
            try:
                last_test = date.fromisoformat(info["last_viability_test"])
            except (ValueError, TypeError):
                pass

        return cls(
            lot_id=model.seedlot_db_id,
            accession_id=info.get("accession_id", ""),
            accession_uuid=str(model.accession_uuid) if hasattr(model, "accession_uuid") and model.accession_uuid else None,
            species=info.get("species", ""),
            variety=model.seedlot_name.split(" - ")[1] if " - " in model.seedlot_name else model.seedlot_name,
            harvest_date=harvest_date or date.today(),
            initial_quantity=info.get("initial_quantity", model.count or 0),
            current_quantity=model.count or 0,
            storage_type=info.get("storage_type", "medium_term"),
            storage_location=model.storage_location or "",
            initial_viability=info.get("initial_viability", 0.0),
            current_viability=info.get("current_viability"),
            last_viability_test=last_test,
            status=info.get("status", "active"),
            notes=model.seedlot_description or "",

            # Extended
            seed_class=info.get("seed_class"),
            purity_percent=info.get("purity_percent"),
            moisture_percent=info.get("moisture_percent"),
            production_year=info.get("production_year"),
            producer_name=info.get("producer_name"),
            production_location=info.get("production_location"),
        )


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

    @classmethod
    def from_transaction(cls, tx: SeedlotTransaction, lot_id: str = None) -> "SeedRequest":
        info = tx.additional_info or {}
        return cls(
            request_id=tx.transaction_db_id,
            lot_id=lot_id or tx.from_seedlot_db_id or "", # Assuming we store lot_id here or link
            requester=info.get("requester", "Unknown"),
            institution=info.get("institution", "Unknown"),
            quantity_requested=tx.amount,
            quantity_approved=info.get("quantity_approved"),
            purpose=info.get("purpose", ""),
            request_date=date.fromisoformat(info.get("request_date", date.today().isoformat())),
            status=info.get("status", "pending")
        )


class SeedInventoryService:
    """
    Seed inventory management for seed banks
    """

    # Stateless service, persistence handled by DB

    async def register_seed_lot(
        self,
        db: AsyncSession,
        organization_id: int,
        accession_id: str,
        species: str,
        variety: str,
        harvest_date: str,
        quantity: float,
        storage_type: str,
        storage_location: str,
        initial_viability: float,
        notes: str = "",
        accession_uuid: Optional[str] = None,
        # Extended fields
        seed_class: Optional[str] = None,
        purity_percent: Optional[float] = None,
        moisture_percent: Optional[float] = None,
        production_year: Optional[int] = None,
        producer_name: Optional[str] = None,
        production_location: Optional[str] = None,
    ) -> SeedLotDTO:
        """
        Register a new seed lot
        """
        lot_id = f"LOT-{uuid.uuid4().hex[:8].upper()}"

        # Prepare additional info
        additional_info = {
            "accession_id": accession_id,
            "species": species,
            "variety": variety,
            "harvest_date": harvest_date,
            "initial_quantity": quantity,
            "storage_type": storage_type,
            "initial_viability": initial_viability,
            "current_viability": initial_viability,
            "last_viability_test": harvest_date,
            "status": "active",
            "seed_class": seed_class,
            "purity_percent": purity_percent,
            "moisture_percent": moisture_percent,
            "production_year": production_year,
            "producer_name": producer_name,
            "production_location": production_location,
            "viability_tests": []
        }

        seedlot = Seedlot(
            organization_id=organization_id,
            seedlot_db_id=lot_id,
            accession_uuid=uuid.UUID(accession_uuid) if accession_uuid else None,
            seedlot_name=f"{species} - {variety}",
            seedlot_description=notes,
            storage_location=storage_location,
            count=quantity,
            units="g",
            creation_date=date.today(),
            last_updated=date.today(),
            additional_info=additional_info
        )

        db.add(seedlot)
        await db.commit()
        await db.refresh(seedlot)

        return SeedLotDTO.from_model(seedlot)

    async def record_viability_test(
        self,
        db: AsyncSession,
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
        """
        # Fetch lot
        stmt = select(Seedlot).where(Seedlot.seedlot_db_id == lot_id)
        result = await db.execute(stmt)
        lot = result.scalar_one_or_none()

        if not lot:
            raise ValueError(f"Seed lot {lot_id} not found")

        test_id = f"VT-{uuid.uuid4().hex[:8].upper()}"

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

        # Update lot info
        info = dict(lot.additional_info or {})
        tests = info.get("viability_tests", [])
        tests.append(test.to_dict())
        info["viability_tests"] = tests
        info["current_viability"] = germination_percent
        info["last_viability_test"] = test_date

        # Update status if low
        if germination_percent < 50:
            info["status"] = "expired"

        lot.additional_info = info
        lot.last_updated = date.today()

        db.add(lot)
        await db.commit()

        return test

    async def get_lot(self, db: AsyncSession, lot_id: str) -> Optional[Dict[str, Any]]:
        """Get seed lot details"""
        stmt = select(Seedlot).where(Seedlot.seedlot_db_id == lot_id)
        result = await db.execute(stmt)
        lot = result.scalar_one_or_none()

        if lot is None:
            return None

        return SeedLotDTO.from_model(lot).to_dict()

    async def list_lots(
        self,
        db: AsyncSession,
        species: Optional[str] = None,
        status: Optional[str] = None,
        storage_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List seed lots with optional filters"""
        stmt = select(Seedlot)

        result = await db.execute(stmt)
        lots = result.scalars().all()

        dtos = []
        for lot in lots:
            dto = SeedLotDTO.from_model(lot)

            if species and dto.species != species:
                continue
            if status and dto.status != status:
                continue
            if storage_type and dto.storage_type != storage_type:
                continue

            dtos.append(dto.to_dict())

        return dtos

    async def get_viability_history(self, db: AsyncSession, lot_id: str) -> List[Dict[str, Any]]:
        """Get viability test history for a lot"""
        stmt = select(Seedlot).where(Seedlot.seedlot_db_id == lot_id)
        result = await db.execute(stmt)
        lot = result.scalar_one_or_none()

        if not lot or not lot.additional_info:
            return []

        return lot.additional_info.get("viability_tests", [])

    async def get_inventory_summary(self, db: AsyncSession) -> Dict[str, Any]:
        """Get inventory summary statistics"""
        stmt = select(Seedlot)
        result = await db.execute(stmt)
        lots = result.scalars().all()

        total_lots = len(lots)
        total_quantity = sum((lot.count or 0) for lot in lots)

        by_status = {}
        by_storage = {}
        by_species = {}

        today = date.today()
        needs_testing = []

        for lot in lots:
            dto = SeedLotDTO.from_model(lot)

            # By status
            status = dto.status
            by_status[status] = by_status.get(status, 0) + 1

            # By storage type
            storage = dto.storage_type
            by_storage[storage] = by_storage.get(storage, 0) + 1

            # By species
            species = dto.species
            if species not in by_species:
                by_species[species] = {"lots": 0, "quantity_g": 0}
            by_species[species]["lots"] += 1
            by_species[species]["quantity_g"] += dto.current_quantity

            # Needs testing
            if dto.last_viability_test:
                days_since = (today - dto.last_viability_test).days
                if days_since > 365:
                    needs_testing.append({
                        "lot_id": dto.lot_id,
                        "days_since_test": days_since,
                        "last_viability": dto.current_viability,
                    })

        # Pending requests count from transactions
        stmt_req = select(SeedlotTransaction).where(
            # Using JSON filtering usually requires casting or dialect specific syntax.
            # For simplicity, filtering in python for now since table scan is expensive but safer without dialect.
            # Or assume we can add a column later.
            # Or rely on transaction_description starting with "Request" and no quantity deducted yet?
            # Let's filter in python for now.
            SeedlotTransaction.transaction_db_id.like("REQ-%")
        )
        result_req = await db.execute(stmt_req)
        txs = result_req.scalars().all()
        pending_requests = sum(1 for tx in txs if (tx.additional_info or {}).get("status") == "pending")

        return {
            "total_lots": total_lots,
            "total_quantity_g": round(total_quantity, 2),
            "by_status": by_status,
            "by_storage_type": by_storage,
            "by_species": by_species,
            "lots_needing_viability_test": needs_testing[:10],
            "pending_requests": pending_requests,
        }

    async def get_alerts(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get inventory alerts"""
        stmt = select(Seedlot)
        result = await db.execute(stmt)
        lots = result.scalars().all()

        alerts = []
        today = date.today()

        for lot in lots:
            dto = SeedLotDTO.from_model(lot)

            if dto.current_quantity < 100:
                 alerts.append({
                    "type": "low_stock",
                    "severity": "warning",
                    "lot_id": dto.lot_id,
                    "message": f"Low stock: {dto.current_quantity}g remaining",
                })

            if dto.current_viability and dto.current_viability < 70:
                alerts.append({
                    "type": "low_viability",
                    "severity": "warning" if dto.current_viability >= 50 else "critical",
                    "lot_id": dto.lot_id,
                    "message": f"Low viability: {dto.current_viability}%",
                })

        return sorted(alerts, key=lambda x: {"critical": 0, "warning": 1, "info": 2}[x["severity"]])

    async def create_request(
        self,
        db: AsyncSession,
        organization_id: int,
        lot_id: str,
        requester: str,
        institution: str,
        quantity: float,
        purpose: str = ""
    ) -> SeedRequest:
        """
        Create a seed distribution request (persistent)
        """
        # Verify lot exists and get ID
        stmt = select(Seedlot).where(Seedlot.seedlot_db_id == lot_id)
        result = await db.execute(stmt)
        lot = result.scalar_one_or_none()

        if not lot:
            raise ValueError(f"Seed lot {lot_id} not found")

        request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"

        info = {
            "requester": requester,
            "institution": institution,
            "purpose": purpose,
            "status": "pending",
            "request_date": date.today().isoformat()
        }

        # We store request as a transaction but without deducting amount yet (or deduct 0?)
        # Or just use the table to store the record.
        transaction = SeedlotTransaction(
            organization_id=organization_id,
            seedlot_id=lot.id,
            transaction_db_id=request_id,
            transaction_description=f"Request from {requester}",
            transaction_timestamp=datetime.now().isoformat(),
            amount=quantity, # Requested amount
            units="g",
            from_seedlot_db_id=lot_id, # Source
            additional_info=info
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        return SeedRequest.from_transaction(transaction, lot_id)

    async def approve_request(
        self,
        db: AsyncSession,
        request_id: str,
        quantity_approved: float
    ) -> SeedRequest:
        """Approve a seed request"""
        # Fetch transaction
        stmt = select(SeedlotTransaction).where(SeedlotTransaction.transaction_db_id == request_id)
        result = await db.execute(stmt)
        tx = result.scalar_one_or_none()

        if not tx:
            raise ValueError(f"Request {request_id} not found")

        info = dict(tx.additional_info or {})
        if info.get("status") != "pending":
             # Already approved or shipped?
             pass # Or raise error if strict

        # Check stock again
        stmt_lot = select(Seedlot).where(Seedlot.id == tx.seedlot_id)
        result_lot = await db.execute(stmt_lot)
        lot = result_lot.scalar_one_or_none()

        if not lot:
             raise ValueError(f"Lot for request not found")

        if quantity_approved > (lot.count or 0):
            raise ValueError(f"Insufficient stock. Available: {lot.count}g")

        info["status"] = "approved"
        info["quantity_approved"] = quantity_approved
        tx.additional_info = info

        db.add(tx)
        await db.commit()

        return SeedRequest.from_transaction(tx, lot.seedlot_db_id)

    async def ship_request(self, db: AsyncSession, request_id: str) -> SeedRequest:
        """Mark request as shipped and deduct from inventory"""
        # Fetch transaction
        stmt = select(SeedlotTransaction).where(SeedlotTransaction.transaction_db_id == request_id)
        result = await db.execute(stmt)
        tx = result.scalar_one_or_none()

        if not tx:
            raise ValueError(f"Request {request_id} not found")

        info = dict(tx.additional_info or {})
        if info.get("status") != "approved":
            raise ValueError(f"Request must be approved before shipping (Current: {info.get('status')})")

        quantity_approved = info.get("quantity_approved", tx.amount)

        # Update Lot
        stmt_lot = select(Seedlot).where(Seedlot.id == tx.seedlot_id)
        result_lot = await db.execute(stmt_lot)
        lot = result_lot.scalar_one_or_none()

        if lot:
            lot.count = (lot.count or 0) - quantity_approved
            lot.last_updated = date.today()

            # Update status in additional_info
            lot_info = dict(lot.additional_info or {})
            initial = lot_info.get("initial_quantity", lot.count + quantity_approved)

            if lot.count <= 0:
                lot_info["status"] = "depleted"
            elif lot.count < initial * 0.1:
                lot_info["status"] = "low_stock"

            lot.additional_info = lot_info
            db.add(lot)

        info["status"] = "shipped"
        info["shipped_date"] = date.today().isoformat()
        tx.additional_info = info

        db.add(tx)
        await db.commit()

        return SeedRequest.from_transaction(tx, lot.seedlot_db_id if lot else None)


# Singleton
_seed_inventory_service: Optional[SeedInventoryService] = None


def get_seed_inventory_service() -> SeedInventoryService:
    """Get or create seed inventory service singleton"""
    global _seed_inventory_service
    if _seed_inventory_service is None:
        _seed_inventory_service = SeedInventoryService()
    return _seed_inventory_service

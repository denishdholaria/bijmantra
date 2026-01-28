"""
Barcode/QR Code Service

Generates and manages barcodes for seed lots, accessions, samples, and other entities.
Supports multiple formats: QR Code, Code128, DataMatrix, EAN-13.
Queries real data from database - no demo/mock data.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import uuid4
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


class BarcodeFormat:
    QR_CODE = "qr_code"
    CODE_128 = "code_128"
    DATA_MATRIX = "data_matrix"
    EAN_13 = "ean_13"


class EntityType:
    SEED_LOT = "seed_lot"
    ACCESSION = "accession"
    SAMPLE = "sample"
    VAULT = "vault"
    BATCH = "batch"
    DISPATCH = "dispatch"
    MTA = "mta"


# Barcode prefixes by entity type (reference data)
ENTITY_PREFIXES = {
    EntityType.SEED_LOT: "SL",
    EntityType.ACCESSION: "AC",
    EntityType.SAMPLE: "SM",
    EntityType.VAULT: "VT",
    EntityType.BATCH: "BT",
    EntityType.DISPATCH: "DP",
    EntityType.MTA: "MT",
}


class BarcodeService:
    """Service for barcode generation and lookup.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """
    
    def generate_barcode_value(
        self,
        entity_type: str,
        entity_id: str,
    ) -> str:
        """Generate a unique barcode value for an entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            
        Returns:
            Generated barcode value string
        """
        prefix = ENTITY_PREFIXES.get(entity_type, "XX")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        hash_input = f"{entity_type}:{entity_id}:{timestamp}"
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()
        return f"{prefix}-{short_hash}"
    
    def generate_qr_content(
        self,
        entity_type: str,
        entity_id: str,
        entity_name: str,
        barcode_value: str,
    ) -> str:
        """Generate QR code content JSON.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            entity_name: Entity name
            barcode_value: Barcode value
            
        Returns:
            JSON string for QR code content
        """
        qr_data = {
            "type": entity_type,
            "id": entity_id,
            "name": entity_name,
            "barcode": barcode_value,
            "app": "bijmantra",
        }
        return json.dumps(qr_data)
    
    async def list_barcodes(
        self,
        db: AsyncSession,
        organization_id: int,
        entity_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List barcodes from database entities.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            entity_type: Filter by entity type
            
        Returns:
            List of barcode dictionaries
        """
        barcodes = []
        
        # Get barcodes from seed lots
        if entity_type is None or entity_type == EntityType.SEED_LOT:
            seedlot_barcodes = await self._get_seedlot_barcodes(db, organization_id)
            barcodes.extend(seedlot_barcodes)
        
        # Get barcodes from accessions/germplasm
        if entity_type is None or entity_type == EntityType.ACCESSION:
            accession_barcodes = await self._get_accession_barcodes(db, organization_id)
            barcodes.extend(accession_barcodes)
        
        # Get barcodes from samples
        if entity_type is None or entity_type == EntityType.SAMPLE:
            sample_barcodes = await self._get_sample_barcodes(db, organization_id)
            barcodes.extend(sample_barcodes)
        
        return sorted(barcodes, key=lambda x: x.get("created_at", ""), reverse=True)
    
    async def _get_seedlot_barcodes(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> List[Dict[str, Any]]:
        """Get barcodes for seed lots."""
        from app.models.germplasm import SeedLot
        from sqlalchemy.orm import selectinload
        
        stmt = (
            select(SeedLot)
            .where(SeedLot.organization_id == organization_id)
            .options(selectinload(SeedLot.germplasm))
        )
        
        result = await db.execute(stmt)
        lots = result.scalars().all()
        
        barcodes = []
        for lot in lots:
            info = lot.additional_info or {}
            barcode_value = info.get("barcode") or self.generate_barcode_value(EntityType.SEED_LOT, str(lot.id))
            
            barcodes.append({
                "id": str(lot.id),
                "barcode_value": barcode_value,
                "format": BarcodeFormat.QR_CODE,
                "entity_type": EntityType.SEED_LOT,
                "entity_id": str(lot.id),
                "entity_name": lot.seed_lot_db_id or f"SL-{lot.id}",
                "data": {
                    "germplasm": lot.germplasm.germplasm_name if lot.germplasm else None,
                    "amount": lot.amount,
                    "units": lot.units,
                },
                "created_at": lot.created_at.isoformat() if lot.created_at else None,
                "active": True,
            })
        
        return barcodes
    
    async def _get_accession_barcodes(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> List[Dict[str, Any]]:
        """Get barcodes for accessions."""
        from app.models.germplasm import Germplasm
        
        stmt = (
            select(Germplasm)
            .where(Germplasm.organization_id == organization_id)
        )
        
        result = await db.execute(stmt)
        accessions = result.scalars().all()
        
        barcodes = []
        for acc in accessions:
            info = acc.additional_info or {}
            barcode_value = info.get("barcode") or self.generate_barcode_value(EntityType.ACCESSION, str(acc.id))
            
            barcodes.append({
                "id": str(acc.id),
                "barcode_value": barcode_value,
                "format": BarcodeFormat.QR_CODE,
                "entity_type": EntityType.ACCESSION,
                "entity_id": str(acc.id),
                "entity_name": acc.accession_number or acc.germplasm_db_id or f"ACC-{acc.id}",
                "data": {
                    "species": acc.species,
                    "origin": acc.country_of_origin_code,
                },
                "created_at": acc.created_at.isoformat() if acc.created_at else None,
                "active": True,
            })
        
        return barcodes
    
    async def _get_sample_barcodes(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> List[Dict[str, Any]]:
        """Get barcodes for samples."""
        from app.models.genotyping import Sample
        
        stmt = (
            select(Sample)
            .where(Sample.organization_id == organization_id)
        )
        
        result = await db.execute(stmt)
        samples = result.scalars().all()
        
        barcodes = []
        for sample in samples:
            info = sample.additional_info or {}
            barcode_value = info.get("barcode") or self.generate_barcode_value(EntityType.SAMPLE, str(sample.id))
            
            barcodes.append({
                "id": str(sample.id),
                "barcode_value": barcode_value,
                "format": BarcodeFormat.DATA_MATRIX,
                "entity_type": EntityType.SAMPLE,
                "entity_id": str(sample.id),
                "entity_name": sample.sample_db_id or f"SAM-{sample.id}",
                "data": {
                    "type": sample.sample_type,
                },
                "created_at": sample.created_at.isoformat() if sample.created_at else None,
                "active": True,
            })
        
        return barcodes
    
    async def lookup_barcode(
        self,
        db: AsyncSession,
        organization_id: int,
        barcode_value: str,
    ) -> Optional[Dict[str, Any]]:
        """Look up entity by barcode value.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            barcode_value: Barcode value to look up
            
        Returns:
            Barcode dictionary or None if not found
        """
        barcodes = await self.list_barcodes(db, organization_id)
        
        for barcode in barcodes:
            if barcode["barcode_value"] == barcode_value:
                return barcode
        
        return None
    
    async def scan_barcode(
        self,
        db: AsyncSession,
        organization_id: int,
        barcode_value: str,
        scanned_by: str = "system",
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a barcode scan.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            barcode_value: Barcode value scanned
            scanned_by: User who scanned
            location: Scan location
            
        Returns:
            Scan result dictionary
        """
        barcode = await self.lookup_barcode(db, organization_id, barcode_value)
        
        scan_record = {
            "id": str(uuid4()),
            "barcode_value": barcode_value,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "scanned_by": scanned_by,
            "location": location,
            "found": barcode is not None,
            "entity_type": barcode["entity_type"] if barcode else None,
            "entity_id": barcode["entity_id"] if barcode else None,
            "entity_name": barcode["entity_name"] if barcode else None,
        }
        
        # TODO: Store scan record in database
        
        return {
            "scan": scan_record,
            "entity": barcode,
        }
    
    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict[str, Any]:
        """Get barcode statistics.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Statistics dictionary
        """
        barcodes = await self.list_barcodes(db, organization_id)
        
        by_type = {}
        for b in barcodes:
            t = b["entity_type"]
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            "total_barcodes": len(barcodes),
            "active_barcodes": len([b for b in barcodes if b.get("active", True)]),
            "by_entity_type": by_type,
            "total_scans": 0,  # Would need scan history table
            "successful_scans": 0,
            "scan_success_rate": 0,
        }
    
    def generate_print_data(
        self,
        barcodes: List[Dict[str, Any]],
        label_size: str = "small",
    ) -> Dict[str, Any]:
        """Generate print-ready data for labels.
        
        Args:
            barcodes: List of barcode dictionaries
            label_size: Label size (small, medium, large)
            
        Returns:
            Print data dictionary
        """
        label_sizes = {
            "small": {"width": 50, "height": 25, "unit": "mm"},
            "medium": {"width": 75, "height": 35, "unit": "mm"},
            "large": {"width": 100, "height": 50, "unit": "mm"},
        }
        
        return {
            "barcodes": barcodes,
            "label_size": label_sizes.get(label_size, label_sizes["small"]),
            "count": len(barcodes),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


# Singleton instance
barcode_service = BarcodeService()

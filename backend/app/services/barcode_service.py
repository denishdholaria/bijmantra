"""
Barcode/QR Code Service

Generates and manages barcodes for seed lots, accessions, samples, and other entities.
Supports multiple formats: QR Code, Code128, DataMatrix, EAN-13.
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4
import base64
import json
import hashlib


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


# Barcode prefixes by entity type
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
    """Service for barcode generation and lookup"""
    
    def __init__(self):
        self.barcodes: dict = {}
        self.scans: list = []
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize demo barcodes"""
        demo_entities = [
            {"entity_type": EntityType.SEED_LOT, "entity_id": "lot-001", "entity_name": "SL-2024-001", "data": {"crop": "Rice", "variety": "IR64", "quantity": 5000}},
            {"entity_type": EntityType.SEED_LOT, "entity_id": "lot-002", "entity_name": "SL-2024-002", "data": {"crop": "Wheat", "variety": "HD2967", "quantity": 3000}},
            {"entity_type": EntityType.ACCESSION, "entity_id": "acc-001", "entity_name": "ACC-2024-001", "data": {"genus": "Oryza", "species": "sativa", "origin": "India"}},
            {"entity_type": EntityType.ACCESSION, "entity_id": "acc-002", "entity_name": "ACC-2024-002", "data": {"genus": "Triticum", "species": "aestivum", "origin": "Mexico"}},
            {"entity_type": EntityType.SAMPLE, "entity_id": "smp-001", "entity_name": "QC-2024-001", "data": {"test_type": "germination", "lot_id": "lot-001"}},
            {"entity_type": EntityType.VAULT, "entity_id": "vault-001", "entity_name": "VAULT-A1", "data": {"type": "base", "temperature": -18, "capacity": 10000}},
        ]
        
        for entity in demo_entities:
            self.generate_barcode(
                entity_type=entity["entity_type"],
                entity_id=entity["entity_id"],
                entity_name=entity["entity_name"],
                data=entity["data"],
            )

    
    def generate_barcode(
        self,
        entity_type: str,
        entity_id: str,
        entity_name: str,
        format: str = BarcodeFormat.QR_CODE,
        data: Optional[dict] = None,
    ) -> dict:
        """Generate a barcode for an entity"""
        prefix = ENTITY_PREFIXES.get(entity_type, "XX")
        
        # Generate unique barcode value
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_input = f"{entity_type}:{entity_id}:{timestamp}"
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()
        barcode_value = f"{prefix}-{short_hash}"
        
        # Create barcode record
        barcode = {
            "id": str(uuid4()),
            "barcode_value": barcode_value,
            "format": format,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_name": entity_name,
            "data": data or {},
            "created_at": datetime.now().isoformat(),
            "scan_count": 0,
            "last_scanned": None,
            "active": True,
        }
        
        # Generate QR code data URL (simplified - in production use qrcode library)
        qr_data = {
            "type": entity_type,
            "id": entity_id,
            "name": entity_name,
            "barcode": barcode_value,
            "app": "bijmantra",
        }
        barcode["qr_content"] = json.dumps(qr_data)
        
        self.barcodes[barcode["id"]] = barcode
        return barcode
    
    def lookup_barcode(self, barcode_value: str) -> Optional[dict]:
        """Look up entity by barcode value"""
        for barcode in self.barcodes.values():
            if barcode["barcode_value"] == barcode_value:
                return barcode
        return None
    
    def scan_barcode(self, barcode_value: str, scanned_by: str = "system", location: Optional[str] = None) -> dict:
        """Record a barcode scan"""
        barcode = self.lookup_barcode(barcode_value)
        
        scan_record = {
            "id": str(uuid4()),
            "barcode_value": barcode_value,
            "scanned_at": datetime.now().isoformat(),
            "scanned_by": scanned_by,
            "location": location,
            "found": barcode is not None,
            "entity_type": barcode["entity_type"] if barcode else None,
            "entity_id": barcode["entity_id"] if barcode else None,
            "entity_name": barcode["entity_name"] if barcode else None,
        }
        
        self.scans.append(scan_record)
        
        if barcode:
            barcode["scan_count"] += 1
            barcode["last_scanned"] = scan_record["scanned_at"]
        
        return {
            "scan": scan_record,
            "entity": barcode,
        }
    
    def get_barcode(self, barcode_id: str) -> Optional[dict]:
        """Get barcode by ID"""
        return self.barcodes.get(barcode_id)
    
    def list_barcodes(
        self,
        entity_type: Optional[str] = None,
        active_only: bool = True,
    ) -> List[dict]:
        """List barcodes with optional filters"""
        result = list(self.barcodes.values())
        
        if entity_type:
            result = [b for b in result if b["entity_type"] == entity_type]
        
        if active_only:
            result = [b for b in result if b["active"]]
        
        return sorted(result, key=lambda x: x["created_at"], reverse=True)
    
    def get_scan_history(self, limit: int = 50, barcode_value: Optional[str] = None) -> List[dict]:
        """Get scan history"""
        result = self.scans
        
        if barcode_value:
            result = [s for s in result if s["barcode_value"] == barcode_value]
        
        return sorted(result, key=lambda x: x["scanned_at"], reverse=True)[:limit]
    
    def deactivate_barcode(self, barcode_id: str) -> Optional[dict]:
        """Deactivate a barcode"""
        barcode = self.barcodes.get(barcode_id)
        if barcode:
            barcode["active"] = False
            barcode["deactivated_at"] = datetime.now().isoformat()
        return barcode
    
    def get_statistics(self) -> dict:
        """Get barcode statistics"""
        barcodes = list(self.barcodes.values())
        
        by_type = {}
        for b in barcodes:
            t = b["entity_type"]
            by_type[t] = by_type.get(t, 0) + 1
        
        total_scans = len(self.scans)
        successful_scans = len([s for s in self.scans if s["found"]])
        
        return {
            "total_barcodes": len(barcodes),
            "active_barcodes": len([b for b in barcodes if b["active"]]),
            "by_entity_type": by_type,
            "total_scans": total_scans,
            "successful_scans": successful_scans,
            "scan_success_rate": round(successful_scans / total_scans * 100, 1) if total_scans > 0 else 0,
        }
    
    def generate_print_data(self, barcode_ids: List[str], label_size: str = "small") -> dict:
        """Generate print-ready data for labels"""
        barcodes = [self.barcodes.get(bid) for bid in barcode_ids if bid in self.barcodes]
        
        label_sizes = {
            "small": {"width": 50, "height": 25, "unit": "mm"},
            "medium": {"width": 75, "height": 35, "unit": "mm"},
            "large": {"width": 100, "height": 50, "unit": "mm"},
        }
        
        return {
            "barcodes": barcodes,
            "label_size": label_sizes.get(label_size, label_sizes["small"]),
            "count": len(barcodes),
            "generated_at": datetime.now().isoformat(),
        }


# Singleton instance
barcode_service = BarcodeService()

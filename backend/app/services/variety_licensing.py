"""
Variety Licensing Service
Manage Plant Variety Protection (PVP), Plant Breeders Rights (PBR),
and variety licensing agreements
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4
from enum import Enum


class ProtectionType(str, Enum):
    PVP = "pvp"  # Plant Variety Protection
    PBR = "pbr"  # Plant Breeders Rights
    PATENT = "patent"
    TRADEMARK = "trademark"
    TRADE_SECRET = "trade_secret"


class LicenseType(str, Enum):
    EXCLUSIVE = "exclusive"
    NON_EXCLUSIVE = "non_exclusive"
    RESEARCH = "research"
    EVALUATION = "evaluation"
    PRODUCTION = "production"
    MARKETING = "marketing"


class LicenseStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


class VarietyLicensingService:
    """Service for variety protection and licensing management"""
    
    def __init__(self):
        # In-memory storage
        self.varieties: Dict[str, Dict] = {}
        self.protections: Dict[str, Dict] = {}
        self.licenses: Dict[str, Dict] = {}
        self.royalty_records: Dict[str, List[Dict]] = {}
        
        # Initialize sample data
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize with sample varieties and protections"""
        # Sample protected varieties
        varieties = [
            {
                "variety_id": "VAR-001",
                "variety_name": "BijGold-101",
                "crop": "Rice",
                "breeder_id": "BRD-001",
                "breeder_name": "Dr. Sharma",
                "organization_id": "ORG-001",
                "organization_name": "Bijmantra Research",
                "release_date": "2022-06-15",
                "description": "High-yielding, drought-tolerant rice variety",
                "key_traits": ["drought_tolerance", "high_yield", "short_duration"],
                "status": "protected",
                "created_at": datetime.now().isoformat(),
            },
            {
                "variety_id": "VAR-002",
                "variety_name": "BijWheat-55",
                "crop": "Wheat",
                "breeder_id": "BRD-002",
                "breeder_name": "Dr. Patel",
                "organization_id": "ORG-001",
                "organization_name": "Bijmantra Research",
                "release_date": "2023-01-20",
                "description": "Rust-resistant wheat with high protein content",
                "key_traits": ["rust_resistance", "high_protein", "good_chapati_quality"],
                "status": "protected",
                "created_at": datetime.now().isoformat(),
            },
        ]
        
        for v in varieties:
            self.varieties[v["variety_id"]] = v
            self.royalty_records[v["variety_id"]] = []
        
        # Sample protections
        protections = [
            {
                "protection_id": "PROT-001",
                "variety_id": "VAR-001",
                "protection_type": ProtectionType.PVP,
                "application_number": "PVP/2022/001234",
                "certificate_number": "PVP-2023-5678",
                "filing_date": "2022-07-01",
                "grant_date": "2023-03-15",
                "expiry_date": "2043-03-15",
                "territory": ["India"],
                "status": "granted",
                "authority": "PPV&FR Authority, India",
            },
            {
                "protection_id": "PROT-002",
                "variety_id": "VAR-002",
                "protection_type": ProtectionType.PBR,
                "application_number": "PBR/2023/000567",
                "certificate_number": None,
                "filing_date": "2023-02-15",
                "grant_date": None,
                "expiry_date": None,
                "territory": ["India", "Bangladesh", "Nepal"],
                "status": "pending",
                "authority": "PPV&FR Authority, India",
            },
        ]
        
        for p in protections:
            self.protections[p["protection_id"]] = p
    
    def register_variety(
        self,
        variety_name: str,
        crop: str,
        breeder_id: str,
        breeder_name: str,
        organization_id: str,
        organization_name: str,
        description: str,
        key_traits: List[str],
        release_date: Optional[str] = None,
    ) -> Dict:
        """Register a new variety for protection"""
        variety_id = f"VAR-{str(uuid4())[:8].upper()}"
        
        variety = {
            "variety_id": variety_id,
            "variety_name": variety_name,
            "crop": crop,
            "breeder_id": breeder_id,
            "breeder_name": breeder_name,
            "organization_id": organization_id,
            "organization_name": organization_name,
            "release_date": release_date,
            "description": description,
            "key_traits": key_traits,
            "status": "registered",
            "created_at": datetime.now().isoformat(),
        }
        
        self.varieties[variety_id] = variety
        self.royalty_records[variety_id] = []
        
        return variety
    
    def get_variety(self, variety_id: str) -> Optional[Dict]:
        """Get variety details"""
        return self.varieties.get(variety_id)
    
    def list_varieties(
        self,
        crop: Optional[str] = None,
        organization_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """List varieties with optional filters"""
        varieties = list(self.varieties.values())
        
        if crop:
            varieties = [v for v in varieties if v["crop"].lower() == crop.lower()]
        if organization_id:
            varieties = [v for v in varieties if v["organization_id"] == organization_id]
        if status:
            varieties = [v for v in varieties if v["status"] == status]
        
        return varieties
    
    def file_protection(
        self,
        variety_id: str,
        protection_type: str,
        application_number: str,
        filing_date: str,
        territory: List[str],
        authority: str,
    ) -> Dict:
        """File for variety protection (PVP/PBR/Patent)"""
        if variety_id not in self.varieties:
            raise ValueError(f"Variety {variety_id} not found")
        
        protection_id = f"PROT-{str(uuid4())[:8].upper()}"
        
        protection = {
            "protection_id": protection_id,
            "variety_id": variety_id,
            "protection_type": protection_type,
            "application_number": application_number,
            "certificate_number": None,
            "filing_date": filing_date,
            "grant_date": None,
            "expiry_date": None,
            "territory": territory,
            "status": "pending",
            "authority": authority,
            "created_at": datetime.now().isoformat(),
        }
        
        self.protections[protection_id] = protection
        self.varieties[variety_id]["status"] = "protection_pending"
        
        return protection
    
    def grant_protection(
        self,
        protection_id: str,
        certificate_number: str,
        grant_date: str,
        expiry_date: str,
    ) -> Dict:
        """Record protection grant"""
        if protection_id not in self.protections:
            raise ValueError(f"Protection {protection_id} not found")
        
        protection = self.protections[protection_id]
        protection["certificate_number"] = certificate_number
        protection["grant_date"] = grant_date
        protection["expiry_date"] = expiry_date
        protection["status"] = "granted"
        
        # Update variety status
        variety_id = protection["variety_id"]
        if variety_id in self.varieties:
            self.varieties[variety_id]["status"] = "protected"
        
        return protection
    
    def get_protection(self, protection_id: str) -> Optional[Dict]:
        """Get protection details"""
        return self.protections.get(protection_id)
    
    def list_protections(
        self,
        variety_id: Optional[str] = None,
        protection_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """List protections with optional filters"""
        protections = list(self.protections.values())
        
        if variety_id:
            protections = [p for p in protections if p["variety_id"] == variety_id]
        if protection_type:
            protections = [p for p in protections if p["protection_type"] == protection_type]
        if status:
            protections = [p for p in protections if p["status"] == status]
        
        return protections
    
    def create_license(
        self,
        variety_id: str,
        licensee_id: str,
        licensee_name: str,
        license_type: str,
        territory: List[str],
        start_date: str,
        end_date: str,
        royalty_rate_percent: float,
        minimum_royalty: Optional[float] = None,
        upfront_fee: Optional[float] = None,
        terms: Optional[str] = None,
    ) -> Dict:
        """Create a new license agreement"""
        if variety_id not in self.varieties:
            raise ValueError(f"Variety {variety_id} not found")
        
        license_id = f"LIC-{str(uuid4())[:8].upper()}"
        
        license_agreement = {
            "license_id": license_id,
            "variety_id": variety_id,
            "variety_name": self.varieties[variety_id]["variety_name"],
            "licensor_id": self.varieties[variety_id]["organization_id"],
            "licensor_name": self.varieties[variety_id]["organization_name"],
            "licensee_id": licensee_id,
            "licensee_name": licensee_name,
            "license_type": license_type,
            "territory": territory,
            "start_date": start_date,
            "end_date": end_date,
            "royalty_rate_percent": royalty_rate_percent,
            "minimum_royalty": minimum_royalty,
            "upfront_fee": upfront_fee,
            "terms": terms,
            "status": LicenseStatus.DRAFT,
            "created_at": datetime.now().isoformat(),
        }
        
        self.licenses[license_id] = license_agreement
        
        return license_agreement
    
    def activate_license(self, license_id: str) -> Dict:
        """Activate a license agreement"""
        if license_id not in self.licenses:
            raise ValueError(f"License {license_id} not found")
        
        self.licenses[license_id]["status"] = LicenseStatus.ACTIVE
        self.licenses[license_id]["activated_at"] = datetime.now().isoformat()
        
        return self.licenses[license_id]
    
    def terminate_license(self, license_id: str, reason: str) -> Dict:
        """Terminate a license agreement"""
        if license_id not in self.licenses:
            raise ValueError(f"License {license_id} not found")
        
        self.licenses[license_id]["status"] = LicenseStatus.TERMINATED
        self.licenses[license_id]["terminated_at"] = datetime.now().isoformat()
        self.licenses[license_id]["termination_reason"] = reason
        
        return self.licenses[license_id]
    
    def get_license(self, license_id: str) -> Optional[Dict]:
        """Get license details"""
        return self.licenses.get(license_id)
    
    def list_licenses(
        self,
        variety_id: Optional[str] = None,
        licensee_id: Optional[str] = None,
        license_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """List licenses with optional filters"""
        licenses = list(self.licenses.values())
        
        if variety_id:
            licenses = [l for l in licenses if l["variety_id"] == variety_id]
        if licensee_id:
            licenses = [l for l in licenses if l["licensee_id"] == licensee_id]
        if license_type:
            licenses = [l for l in licenses if l["license_type"] == license_type]
        if status:
            licenses = [l for l in licenses if l["status"] == status]
        
        return licenses
    
    def record_royalty(
        self,
        license_id: str,
        period_start: str,
        period_end: str,
        sales_quantity_kg: float,
        sales_value: float,
        royalty_amount: float,
        payment_status: str = "pending",
    ) -> Dict:
        """Record royalty payment for a license"""
        if license_id not in self.licenses:
            raise ValueError(f"License {license_id} not found")
        
        license_agreement = self.licenses[license_id]
        variety_id = license_agreement["variety_id"]
        
        royalty = {
            "royalty_id": str(uuid4()),
            "license_id": license_id,
            "variety_id": variety_id,
            "licensee_id": license_agreement["licensee_id"],
            "licensee_name": license_agreement["licensee_name"],
            "period_start": period_start,
            "period_end": period_end,
            "sales_quantity_kg": sales_quantity_kg,
            "sales_value": sales_value,
            "royalty_rate_percent": license_agreement["royalty_rate_percent"],
            "calculated_royalty": sales_value * license_agreement["royalty_rate_percent"] / 100,
            "royalty_amount": royalty_amount,
            "payment_status": payment_status,
            "recorded_at": datetime.now().isoformat(),
        }
        
        self.royalty_records[variety_id].append(royalty)
        
        return royalty
    
    def get_royalty_summary(self, variety_id: str) -> Dict:
        """Get royalty summary for a variety"""
        if variety_id not in self.varieties:
            return {"error": f"Variety {variety_id} not found"}
        
        records = self.royalty_records.get(variety_id, [])
        
        total_royalty = sum(r["royalty_amount"] for r in records)
        total_sales = sum(r["sales_value"] for r in records)
        total_quantity = sum(r["sales_quantity_kg"] for r in records)
        
        pending = sum(r["royalty_amount"] for r in records if r["payment_status"] == "pending")
        received = sum(r["royalty_amount"] for r in records if r["payment_status"] == "received")
        
        return {
            "variety_id": variety_id,
            "variety_name": self.varieties[variety_id]["variety_name"],
            "total_royalty": total_royalty,
            "total_sales_value": total_sales,
            "total_quantity_kg": total_quantity,
            "royalty_pending": pending,
            "royalty_received": received,
            "record_count": len(records),
        }
    
    def get_protection_types(self) -> List[Dict]:
        """Get available protection types"""
        return [
            {"code": "pvp", "name": "Plant Variety Protection", "description": "Protection under UPOV convention"},
            {"code": "pbr", "name": "Plant Breeders Rights", "description": "Rights for plant breeders"},
            {"code": "patent", "name": "Patent", "description": "Utility patent for plant varieties"},
            {"code": "trademark", "name": "Trademark", "description": "Brand protection for variety name"},
            {"code": "trade_secret", "name": "Trade Secret", "description": "Proprietary breeding methods"},
        ]
    
    def get_license_types(self) -> List[Dict]:
        """Get available license types"""
        return [
            {"code": "exclusive", "name": "Exclusive License", "description": "Sole rights in territory"},
            {"code": "non_exclusive", "name": "Non-Exclusive License", "description": "Shared rights"},
            {"code": "research", "name": "Research License", "description": "For research purposes only"},
            {"code": "evaluation", "name": "Evaluation License", "description": "Trial/evaluation period"},
            {"code": "production", "name": "Production License", "description": "Seed production rights"},
            {"code": "marketing", "name": "Marketing License", "description": "Sales and distribution rights"},
        ]
    
    def get_statistics(self) -> Dict:
        """Get licensing statistics"""
        varieties = list(self.varieties.values())
        protections = list(self.protections.values())
        licenses = list(self.licenses.values())
        
        # Protection stats
        protection_by_type = {}
        protection_by_status = {}
        for p in protections:
            ptype = p["protection_type"]
            protection_by_type[ptype] = protection_by_type.get(ptype, 0) + 1
            status = p["status"]
            protection_by_status[status] = protection_by_status.get(status, 0) + 1
        
        # License stats
        license_by_type = {}
        license_by_status = {}
        for l in licenses:
            ltype = l["license_type"]
            license_by_type[ltype] = license_by_type.get(ltype, 0) + 1
            status = l["status"]
            license_by_status[status] = license_by_status.get(status, 0) + 1
        
        # Royalty stats
        total_royalty = 0
        for records in self.royalty_records.values():
            total_royalty += sum(r["royalty_amount"] for r in records)
        
        return {
            "total_varieties": len(varieties),
            "total_protections": len(protections),
            "total_licenses": len(licenses),
            "total_royalty_recorded": total_royalty,
            "protection_by_type": protection_by_type,
            "protection_by_status": protection_by_status,
            "license_by_type": license_by_type,
            "license_by_status": license_by_status,
        }


# Singleton instance
variety_licensing_service = VarietyLicensingService()

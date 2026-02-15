"""
Harvest Management Service
Track harvest operations, post-harvest handling, and storage
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any
from uuid import uuid4
from enum import Enum


class HarvestStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StorageType(str, Enum):
    AMBIENT = "ambient"
    COLD = "cold"
    CONTROLLED_ATMOSPHERE = "controlled_atmosphere"
    HERMETIC = "hermetic"
    SILO = "silo"


class HarvestManagementService:
    """Service for harvest and post-harvest management"""
    
    def __init__(self):
        # In-memory storage
        self.harvests: Dict[str, Dict] = {}
        self.storage_units: Dict[str, Dict] = {}
        self.storage_records: Dict[str, List[Dict]] = {}
        self.quality_checks: Dict[str, List[Dict]] = {}
        
        # Initialize sample data
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize with sample data"""
        # Sample storage units
        storage_units = [
            {
                "unit_id": "STU-001",
                "name": "Cold Storage A",
                "type": StorageType.COLD,
                "capacity_kg": 50000,
                "current_stock_kg": 25000,
                "temperature_c": 4,
                "humidity_percent": 65,
                "location": "Warehouse 1",
                "status": "active",
            },
            {
                "unit_id": "STU-002",
                "name": "Silo B",
                "type": StorageType.SILO,
                "capacity_kg": 100000,
                "current_stock_kg": 75000,
                "temperature_c": None,
                "humidity_percent": None,
                "location": "Field Station",
                "status": "active",
            },
        ]
        
        for unit in storage_units:
            self.storage_units[unit["unit_id"]] = unit
            self.storage_records[unit["unit_id"]] = []
        
        # Sample harvest
        harvest = {
            "harvest_id": "HRV-2024-001",
            "trial_id": "TRL-001",
            "plot_id": "PLT-001",
            "crop": "Rice",
            "variety": "IR64",
            "harvest_date": "2024-11-15",
            "area_ha": 2.5,
            "yield_kg": 12500,
            "yield_per_ha": 5000,
            "moisture_percent": 18,
            "status": HarvestStatus.COMPLETED,
            "operator": "Field Team A",
            "notes": "Good harvest, no lodging",
            "created_at": datetime.now().isoformat(),
        }
        self.harvests[harvest["harvest_id"]] = harvest
        self.quality_checks[harvest["harvest_id"]] = []
    
    def plan_harvest(
        self,
        trial_id: str,
        plot_id: str,
        crop: str,
        variety: str,
        planned_date: str,
        area_ha: float,
        expected_yield_kg: Optional[float] = None,
        operator: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict:
        """Plan a harvest operation"""
        harvest_id = f"HRV-{datetime.now().year}-{str(uuid4())[:8].upper()}"
        
        harvest = {
            "harvest_id": harvest_id,
            "trial_id": trial_id,
            "plot_id": plot_id,
            "crop": crop,
            "variety": variety,
            "planned_date": planned_date,
            "harvest_date": None,
            "area_ha": area_ha,
            "expected_yield_kg": expected_yield_kg,
            "yield_kg": None,
            "yield_per_ha": None,
            "moisture_percent": None,
            "status": HarvestStatus.PLANNED,
            "operator": operator,
            "notes": notes,
            "created_at": datetime.now().isoformat(),
        }
        
        self.harvests[harvest_id] = harvest
        self.quality_checks[harvest_id] = []
        
        return harvest
    
    def record_harvest(
        self,
        harvest_id: str,
        harvest_date: str,
        yield_kg: float,
        moisture_percent: float,
        operator: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict:
        """Record actual harvest data"""
        if harvest_id not in self.harvests:
            raise ValueError(f"Harvest {harvest_id} not found")
        
        harvest = self.harvests[harvest_id]
        harvest["harvest_date"] = harvest_date
        harvest["yield_kg"] = yield_kg
        harvest["moisture_percent"] = moisture_percent
        harvest["yield_per_ha"] = yield_kg / harvest["area_ha"] if harvest["area_ha"] > 0 else 0
        harvest["status"] = HarvestStatus.COMPLETED
        
        if operator:
            harvest["operator"] = operator
        if notes:
            harvest["notes"] = notes
        
        harvest["completed_at"] = datetime.now().isoformat()
        
        return harvest
    
    def get_harvest(self, harvest_id: str) -> Optional[Dict]:
        """Get harvest details"""
        return self.harvests.get(harvest_id)
    
    def list_harvests(
        self,
        trial_id: Optional[str] = None,
        crop: Optional[str] = None,
        status: Optional[str] = None,
        year: Optional[int] = None,
    ) -> List[Dict]:
        """List harvests with optional filters"""
        harvests = list(self.harvests.values())
        
        if trial_id:
            harvests = [h for h in harvests if h["trial_id"] == trial_id]
        if crop:
            harvests = [h for h in harvests if h["crop"].lower() == crop.lower()]
        if status:
            harvests = [h for h in harvests if h["status"] == status]
        if year:
            harvests = [h for h in harvests if str(year) in h["harvest_id"]]
        
        return harvests
    
    def add_quality_check(
        self,
        harvest_id: str,
        check_type: str,
        value: float,
        unit: str,
        passed: bool,
        notes: Optional[str] = None,
    ) -> Dict:
        """Add quality check for harvested material"""
        if harvest_id not in self.harvests:
            raise ValueError(f"Harvest {harvest_id} not found")
        
        check = {
            "check_id": str(uuid4()),
            "harvest_id": harvest_id,
            "check_type": check_type,
            "value": value,
            "unit": unit,
            "passed": passed,
            "notes": notes,
            "checked_at": datetime.now().isoformat(),
        }
        
        self.quality_checks[harvest_id].append(check)
        
        return check
    
    def get_quality_checks(self, harvest_id: str) -> List[Dict]:
        """Get quality checks for a harvest"""
        return self.quality_checks.get(harvest_id, [])
    
    def create_storage_unit(
        self,
        name: str,
        storage_type: str,
        capacity_kg: float,
        location: str,
        temperature_c: Optional[float] = None,
        humidity_percent: Optional[float] = None,
    ) -> Dict:
        """Create a new storage unit"""
        unit_id = f"STU-{str(uuid4())[:8].upper()}"
        
        unit = {
            "unit_id": unit_id,
            "name": name,
            "type": storage_type,
            "capacity_kg": capacity_kg,
            "current_stock_kg": 0,
            "temperature_c": temperature_c,
            "humidity_percent": humidity_percent,
            "location": location,
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }
        
        self.storage_units[unit_id] = unit
        self.storage_records[unit_id] = []
        
        return unit
    
    def get_storage_unit(self, unit_id: str) -> Optional[Dict]:
        """Get storage unit details"""
        return self.storage_units.get(unit_id)
    
    def list_storage_units(
        self,
        storage_type: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[Dict]:
        """List storage units"""
        units = list(self.storage_units.values())
        
        if storage_type:
            units = [u for u in units if u["type"] == storage_type]
        if location:
            units = [u for u in units if location.lower() in u["location"].lower()]
        
        return units
    
    def store_harvest(
        self,
        harvest_id: str,
        unit_id: str,
        quantity_kg: float,
        notes: Optional[str] = None,
    ) -> Dict:
        """Store harvested material in a storage unit"""
        if harvest_id not in self.harvests:
            raise ValueError(f"Harvest {harvest_id} not found")
        if unit_id not in self.storage_units:
            raise ValueError(f"Storage unit {unit_id} not found")
        
        unit = self.storage_units[unit_id]
        available = unit["capacity_kg"] - unit["current_stock_kg"]
        
        if quantity_kg > available:
            raise ValueError(f"Insufficient capacity. Available: {available} kg")
        
        record = {
            "record_id": str(uuid4()),
            "harvest_id": harvest_id,
            "unit_id": unit_id,
            "action": "store",
            "quantity_kg": quantity_kg,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.storage_records[unit_id].append(record)
        unit["current_stock_kg"] += quantity_kg
        
        return record
    
    def withdraw_from_storage(
        self,
        unit_id: str,
        quantity_kg: float,
        purpose: str,
        destination: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict:
        """Withdraw material from storage"""
        if unit_id not in self.storage_units:
            raise ValueError(f"Storage unit {unit_id} not found")
        
        unit = self.storage_units[unit_id]
        
        if quantity_kg > unit["current_stock_kg"]:
            raise ValueError(f"Insufficient stock. Available: {unit['current_stock_kg']} kg")
        
        record = {
            "record_id": str(uuid4()),
            "unit_id": unit_id,
            "action": "withdraw",
            "quantity_kg": quantity_kg,
            "purpose": purpose,
            "destination": destination,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.storage_records[unit_id].append(record)
        unit["current_stock_kg"] -= quantity_kg
        
        return record
    
    def get_storage_history(self, unit_id: str) -> List[Dict]:
        """Get storage transaction history"""
        return self.storage_records.get(unit_id, [])
    
    def calculate_dry_weight(
        self,
        wet_weight_kg: float,
        moisture_percent: float,
        target_moisture: float = 14.0,
    ) -> Dict:
        """Calculate dry weight at target moisture"""
        # Formula: Dry weight = Wet weight × (100 - current moisture) / (100 - target moisture)
        dry_weight = wet_weight_kg * (100 - moisture_percent) / (100 - target_moisture)
        moisture_loss = wet_weight_kg - dry_weight
        
        return {
            "wet_weight_kg": wet_weight_kg,
            "current_moisture_percent": moisture_percent,
            "target_moisture_percent": target_moisture,
            "dry_weight_kg": round(dry_weight, 2),
            "moisture_loss_kg": round(moisture_loss, 2),
            "weight_reduction_percent": round((moisture_loss / wet_weight_kg) * 100, 2),
        }
    
    def get_storage_types(self) -> List[Dict]:
        """Get available storage types"""
        return [
            {"code": "ambient", "name": "Ambient Storage", "description": "Room temperature storage"},
            {"code": "cold", "name": "Cold Storage", "description": "Refrigerated storage (2-8°C)"},
            {"code": "controlled_atmosphere", "name": "Controlled Atmosphere", "description": "Modified O2/CO2 levels"},
            {"code": "hermetic", "name": "Hermetic Storage", "description": "Airtight sealed containers"},
            {"code": "silo", "name": "Silo", "description": "Large grain storage structure"},
        ]
    
    def get_statistics(self) -> Dict:
        """Get harvest and storage statistics"""
        harvests = list(self.harvests.values())
        units = list(self.storage_units.values())
        
        completed = [h for h in harvests if h["status"] == HarvestStatus.COMPLETED]
        total_yield = sum(h.get("yield_kg", 0) or 0 for h in completed)
        total_area = sum(h.get("area_ha", 0) or 0 for h in completed)
        
        total_capacity = sum(u["capacity_kg"] for u in units)
        total_stock = sum(u["current_stock_kg"] for u in units)
        
        return {
            "total_harvests": len(harvests),
            "completed_harvests": len(completed),
            "total_yield_kg": total_yield,
            "total_area_ha": total_area,
            "average_yield_per_ha": round(total_yield / total_area, 2) if total_area > 0 else 0,
            "storage_units": len(units),
            "total_storage_capacity_kg": total_capacity,
            "total_stock_kg": total_stock,
            "storage_utilization_percent": round((total_stock / total_capacity) * 100, 2) if total_capacity > 0 else 0,
        }


# Singleton instance
harvest_management_service = HarvestManagementService()

"""
Speed Breeding Service
Accelerated generation advancement protocols
"""
from typing import Optional
from datetime import datetime, timedelta
import random

# Demo speed breeding protocols
DEMO_PROTOCOLS = [
    {
        "id": "sb-001",
        "name": "Rice Rapid Generation Advance",
        "crop": "Rice",
        "photoperiod": "22h light / 2h dark",
        "temperature": {"day": 28, "night": 22},
        "humidity": 70,
        "generations_per_year": 5,
        "days_to_flower": 35,
        "days_to_harvest": 75,
        "success_rate": 0.92,
        "status": "active"
    },
    {
        "id": "sb-002",
        "name": "Wheat Speed Protocol",
        "crop": "Wheat",
        "photoperiod": "22h light / 2h dark",
        "temperature": {"day": 22, "night": 17},
        "humidity": 60,
        "generations_per_year": 6,
        "days_to_flower": 28,
        "days_to_harvest": 60,
        "success_rate": 0.95,
        "status": "active"
    },
    {
        "id": "sb-003",
        "name": "Chickpea Accelerated",
        "crop": "Chickpea",
        "photoperiod": "20h light / 4h dark",
        "temperature": {"day": 25, "night": 20},
        "humidity": 55,
        "generations_per_year": 4,
        "days_to_flower": 42,
        "days_to_harvest": 90,
        "success_rate": 0.88,
        "status": "active"
    }
]

# Demo active batches
DEMO_BATCHES = [
    {
        "id": "batch-001",
        "protocol_id": "sb-001",
        "name": "IR64 x Swarna F2 Population",
        "entries": 500,
        "generation": "F2",
        "start_date": "2024-10-01",
        "expected_harvest": "2024-12-15",
        "chamber": "Chamber A",
        "status": "growing",
        "progress": 65
    },
    {
        "id": "batch-002",
        "protocol_id": "sb-002",
        "name": "HD2967 Backcross Lines",
        "entries": 200,
        "generation": "BC2F3",
        "start_date": "2024-11-01",
        "expected_harvest": "2024-12-30",
        "chamber": "Chamber B",
        "status": "flowering",
        "progress": 45
    },
    {
        "id": "batch-003",
        "protocol_id": "sb-001",
        "name": "Drought Tolerance RILs",
        "entries": 300,
        "generation": "F5",
        "start_date": "2024-09-15",
        "expected_harvest": "2024-11-30",
        "chamber": "Chamber A",
        "status": "harvesting",
        "progress": 90
    }
]


class SpeedBreedingService:
    """Service for speed breeding protocol management"""
    
    async def get_protocols(
        self,
        crop: Optional[str] = None,
        status: Optional[str] = None
    ) -> list:
        """Get speed breeding protocols"""
        protocols = DEMO_PROTOCOLS.copy()
        
        if crop:
            protocols = [p for p in protocols if p["crop"].lower() == crop.lower()]
        if status:
            protocols = [p for p in protocols if p["status"] == status]
            
        return protocols
    
    async def get_protocol(self, protocol_id: str) -> Optional[dict]:
        """Get single protocol"""
        for p in DEMO_PROTOCOLS:
            if p["id"] == protocol_id:
                return p
        return None
    
    async def get_batches(
        self,
        protocol_id: Optional[str] = None,
        status: Optional[str] = None,
        chamber: Optional[str] = None
    ) -> list:
        """Get active batches"""
        batches = DEMO_BATCHES.copy()
        
        if protocol_id:
            batches = [b for b in batches if b["protocol_id"] == protocol_id]
        if status:
            batches = [b for b in batches if b["status"] == status]
        if chamber:
            batches = [b for b in batches if b["chamber"] == chamber]
            
        return batches
    
    async def get_batch(self, batch_id: str) -> Optional[dict]:
        """Get single batch"""
        for b in DEMO_BATCHES:
            if b["id"] == batch_id:
                return b
        return None
    
    async def calculate_timeline(
        self,
        protocol_id: str,
        target_generation: str,
        start_date: Optional[str] = None
    ) -> dict:
        """Calculate breeding timeline"""
        protocol = await self.get_protocol(protocol_id)
        if not protocol:
            return {"error": "Protocol not found"}
        
        # Parse generation (e.g., F6 -> 6)
        gen_num = int(target_generation.replace("F", "").replace("BC", ""))
        
        start = datetime.fromisoformat(start_date) if start_date else datetime.now()
        days_per_gen = protocol["days_to_harvest"]
        total_days = gen_num * days_per_gen
        
        timeline = []
        current_date = start
        for i in range(1, gen_num + 1):
            flower_date = current_date + timedelta(days=protocol["days_to_flower"])
            harvest_date = current_date + timedelta(days=days_per_gen)
            timeline.append({
                "generation": f"F{i}",
                "sowing": current_date.strftime("%Y-%m-%d"),
                "flowering": flower_date.strftime("%Y-%m-%d"),
                "harvest": harvest_date.strftime("%Y-%m-%d")
            })
            current_date = harvest_date + timedelta(days=7)  # 7 days for seed processing
        
        return {
            "protocol": protocol["name"],
            "crop": protocol["crop"],
            "target_generation": target_generation,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": (start + timedelta(days=total_days + gen_num * 7)).strftime("%Y-%m-%d"),
            "total_days": total_days + gen_num * 7,
            "generations_per_year": protocol["generations_per_year"],
            "timeline": timeline
        }
    
    async def get_chamber_status(self) -> list:
        """Get growth chamber status"""
        chambers = ["Chamber A", "Chamber B", "Chamber C", "Chamber D"]
        status = []
        
        for chamber in chambers:
            batches = [b for b in DEMO_BATCHES if b["chamber"] == chamber]
            status.append({
                "name": chamber,
                "capacity": 1000,
                "occupied": sum(b["entries"] for b in batches),
                "batches": len(batches),
                "temperature": round(random.uniform(22, 28), 1),
                "humidity": round(random.uniform(55, 75), 1),
                "light_hours": 22,
                "status": "active" if batches else "available"
            })
        
        return status
    
    async def get_statistics(self) -> dict:
        """Get speed breeding statistics"""
        return {
            "total_protocols": len(DEMO_PROTOCOLS),
            "active_batches": len(DEMO_BATCHES),
            "total_entries": sum(b["entries"] for b in DEMO_BATCHES),
            "chambers_in_use": len(set(b["chamber"] for b in DEMO_BATCHES)),
            "crops": list(set(p["crop"] for p in DEMO_PROTOCOLS)),
            "avg_generations_per_year": round(
                sum(p["generations_per_year"] for p in DEMO_PROTOCOLS) / len(DEMO_PROTOCOLS), 1
            ),
            "avg_success_rate": round(
                sum(p["success_rate"] for p in DEMO_PROTOCOLS) / len(DEMO_PROTOCOLS), 2
            )
        }


# Singleton instance
speed_breeding_service = SpeedBreedingService()

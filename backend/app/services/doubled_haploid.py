"""
Doubled Haploid Service
DH production and management
"""
from typing import Optional
from datetime import datetime
import random

# Demo DH protocols
DEMO_PROTOCOLS = [
    {
        "id": "dh-001",
        "name": "Maize Maternal Haploid Induction",
        "crop": "Maize",
        "method": "In vivo maternal",
        "inducer": "Stock 6 derivatives",
        "induction_rate": 0.10,
        "doubling_agent": "Colchicine",
        "doubling_rate": 0.25,
        "overall_efficiency": 0.025,
        "days_to_complete": 180,
        "status": "active"
    },
    {
        "id": "dh-002",
        "name": "Wheat Anther Culture",
        "crop": "Wheat",
        "method": "Anther culture",
        "inducer": "N/A",
        "induction_rate": 0.15,
        "doubling_agent": "Spontaneous",
        "doubling_rate": 0.60,
        "overall_efficiency": 0.09,
        "days_to_complete": 240,
        "status": "active"
    },
    {
        "id": "dh-003",
        "name": "Rice Anther Culture",
        "crop": "Rice",
        "method": "Anther culture",
        "inducer": "N/A",
        "induction_rate": 0.20,
        "doubling_agent": "Spontaneous",
        "doubling_rate": 0.70,
        "overall_efficiency": 0.14,
        "days_to_complete": 200,
        "status": "active"
    },
    {
        "id": "dh-004",
        "name": "Barley Microspore Culture",
        "crop": "Barley",
        "method": "Microspore culture",
        "inducer": "N/A",
        "induction_rate": 0.25,
        "doubling_agent": "Colchicine",
        "doubling_rate": 0.40,
        "overall_efficiency": 0.10,
        "days_to_complete": 220,
        "status": "active"
    }
]

# Demo DH batches
DEMO_BATCHES = [
    {
        "id": "dhb-001",
        "protocol_id": "dh-001",
        "name": "Elite Maize Hybrid DH",
        "donor_cross": "B73 x Mo17",
        "donor_plants": 100,
        "haploids_induced": 850,
        "haploids_identified": 85,
        "doubled_plants": 21,
        "fertile_dh_lines": 18,
        "stage": "Field evaluation",
        "start_date": "2024-03-01",
        "status": "active"
    },
    {
        "id": "dhb-002",
        "protocol_id": "dh-002",
        "name": "Wheat Rust Resistance DH",
        "donor_cross": "HD2967 x Lr24 donor",
        "donor_plants": 50,
        "anthers_cultured": 5000,
        "embryos_formed": 750,
        "plants_regenerated": 450,
        "fertile_dh_lines": 270,
        "stage": "Chromosome doubling",
        "start_date": "2024-05-15",
        "status": "active"
    },
    {
        "id": "dhb-003",
        "protocol_id": "dh-003",
        "name": "Rice Quality DH Population",
        "donor_cross": "Basmati 370 x IR64",
        "donor_plants": 30,
        "anthers_cultured": 3000,
        "embryos_formed": 600,
        "plants_regenerated": 420,
        "fertile_dh_lines": 294,
        "stage": "Seed multiplication",
        "start_date": "2024-04-01",
        "status": "completed"
    }
]


class DoubledHaploidService:
    """Service for doubled haploid production management"""
    
    async def get_protocols(
        self,
        crop: Optional[str] = None,
        method: Optional[str] = None
    ) -> list:
        """Get DH protocols"""
        protocols = DEMO_PROTOCOLS.copy()
        
        if crop:
            protocols = [p for p in protocols if p["crop"].lower() == crop.lower()]
        if method:
            protocols = [p for p in protocols if method.lower() in p["method"].lower()]
            
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
        stage: Optional[str] = None
    ) -> list:
        """Get DH batches"""
        batches = DEMO_BATCHES.copy()
        
        if protocol_id:
            batches = [b for b in batches if b["protocol_id"] == protocol_id]
        if status:
            batches = [b for b in batches if b["status"] == status]
        if stage:
            batches = [b for b in batches if stage.lower() in b["stage"].lower()]
            
        return batches
    
    async def get_batch(self, batch_id: str) -> Optional[dict]:
        """Get single batch"""
        for b in DEMO_BATCHES:
            if b["id"] == batch_id:
                return b
        return None
    
    async def calculate_efficiency(
        self,
        protocol_id: str,
        donor_plants: int
    ) -> dict:
        """Calculate expected DH production efficiency"""
        protocol = await self.get_protocol(protocol_id)
        if not protocol:
            return {"error": "Protocol not found"}
        
        # Calculate expected outputs
        if "anther" in protocol["method"].lower() or "microspore" in protocol["method"].lower():
            anthers_per_plant = 100
            total_anthers = donor_plants * anthers_per_plant
            embryos = int(total_anthers * protocol["induction_rate"])
            regenerated = int(embryos * 0.70)
            doubled = int(regenerated * protocol["doubling_rate"])
        else:
            # In vivo method
            seeds_per_plant = 200
            total_seeds = donor_plants * seeds_per_plant
            haploids = int(total_seeds * protocol["induction_rate"])
            doubled = int(haploids * protocol["doubling_rate"])
            regenerated = haploids
            embryos = haploids
        
        return {
            "protocol": protocol["name"],
            "crop": protocol["crop"],
            "method": protocol["method"],
            "donor_plants": donor_plants,
            "expected_embryos": embryos,
            "expected_regenerated": regenerated,
            "expected_dh_lines": doubled,
            "overall_efficiency": protocol["overall_efficiency"],
            "days_to_complete": protocol["days_to_complete"],
            "cost_estimate": f"${donor_plants * 50}-{donor_plants * 100}"
        }
    
    async def get_stage_workflow(self, protocol_id: str) -> list:
        """Get workflow stages for a protocol"""
        protocol = await self.get_protocol(protocol_id)
        if not protocol:
            return []
        
        if "anther" in protocol["method"].lower():
            return [
                {"stage": 1, "name": "Donor plant growth", "days": 60},
                {"stage": 2, "name": "Anther collection", "days": 7},
                {"stage": 3, "name": "Culture initiation", "days": 14},
                {"stage": 4, "name": "Embryo induction", "days": 30},
                {"stage": 5, "name": "Plant regeneration", "days": 45},
                {"stage": 6, "name": "Chromosome doubling", "days": 14},
                {"stage": 7, "name": "Hardening", "days": 21},
                {"stage": 8, "name": "Field transfer", "days": 7},
                {"stage": 9, "name": "Seed multiplication", "days": 90}
            ]
        else:
            return [
                {"stage": 1, "name": "Donor plant growth", "days": 60},
                {"stage": 2, "name": "Pollination with inducer", "days": 7},
                {"stage": 3, "name": "Seed harvest", "days": 45},
                {"stage": 4, "name": "Haploid identification", "days": 14},
                {"stage": 5, "name": "Chromosome doubling", "days": 14},
                {"stage": 6, "name": "D0 plant growth", "days": 60},
                {"stage": 7, "name": "Seed multiplication", "days": 90}
            ]
    
    async def get_statistics(self) -> dict:
        """Get DH production statistics"""
        total_dh_lines = sum(b.get("fertile_dh_lines", 0) for b in DEMO_BATCHES)
        
        return {
            "total_protocols": len(DEMO_PROTOCOLS),
            "active_batches": len([b for b in DEMO_BATCHES if b["status"] == "active"]),
            "completed_batches": len([b for b in DEMO_BATCHES if b["status"] == "completed"]),
            "total_dh_lines_produced": total_dh_lines,
            "crops": list(set(p["crop"] for p in DEMO_PROTOCOLS)),
            "methods": list(set(p["method"] for p in DEMO_PROTOCOLS)),
            "avg_efficiency": round(
                sum(p["overall_efficiency"] for p in DEMO_PROTOCOLS) / len(DEMO_PROTOCOLS), 3
            )
        }


# Singleton instance
doubled_haploid_service = DoubledHaploidService()

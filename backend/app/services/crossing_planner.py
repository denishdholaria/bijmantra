"""
Crossing Planner Service
Manages planned crosses between germplasm
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import random


class CrossingPlannerService:
    """Service for managing crossing plans"""
    
    def __init__(self):
        self._crosses: Dict[str, Dict] = {}
        self._germplasm: Dict[str, Dict] = {}
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize demo data"""
        # Demo germplasm
        self._germplasm = {
            "germ001": {"id": "germ001", "name": "Elite Line A", "type": "elite", "traits": ["high_yield", "disease_resistant"]},
            "germ002": {"id": "germ002", "name": "Disease Resistant B", "type": "donor", "traits": ["blast_resistant", "bph_resistant"]},
            "germ003": {"id": "germ003", "name": "High Yield X", "type": "elite", "traits": ["high_yield", "early_maturity"]},
            "germ004": {"id": "germ004", "name": "Drought Tolerant Y", "type": "donor", "traits": ["drought_tolerant", "deep_roots"]},
            "germ005": {"id": "germ005", "name": "Variety 2023", "type": "released", "traits": ["good_quality", "medium_yield"]},
            "germ006": {"id": "germ006", "name": "Wild Relative", "type": "wild", "traits": ["stress_tolerant", "diverse_alleles"]},
            "germ007": {"id": "germ007", "name": "Inbred A", "type": "inbred", "traits": ["uniform", "stable"]},
            "germ008": {"id": "germ008", "name": "Inbred B", "type": "inbred", "traits": ["uniform", "high_combining"]},
            "germ009": {"id": "germ009", "name": "Test Line 1", "type": "breeding", "traits": ["experimental"]},
            "germ010": {"id": "germ010", "name": "Test Line 2", "type": "breeding", "traits": ["experimental"]},
        }
        
        # Demo crosses
        self._crosses = {
            "CX001": {
                "crossId": "CX001",
                "crossName": "Elite A × Disease B",
                "femaleParentId": "germ001",
                "femaleParentName": "Elite Line A",
                "maleParentId": "germ002",
                "maleParentName": "Disease Resistant B",
                "objective": "Combine yield + resistance",
                "priority": "high",
                "targetDate": "2024-12-15",
                "status": "scheduled",
                "expectedProgeny": 50,
                "actualProgeny": 0,
                "crossType": "single",
                "season": "2024-Kharif",
                "location": "Field Station A",
                "breeder": "Dr. Smith",
                "notes": "Priority cross for disease resistance introgression",
                "created": "2024-11-01",
            },
            "CX002": {
                "crossId": "CX002",
                "crossName": "Yield X × Drought Y",
                "femaleParentId": "germ003",
                "femaleParentName": "High Yield X",
                "maleParentId": "germ004",
                "maleParentName": "Drought Tolerant Y",
                "objective": "Drought tolerance introgression",
                "priority": "high",
                "targetDate": "2024-12-20",
                "status": "planned",
                "expectedProgeny": 100,
                "actualProgeny": 0,
                "crossType": "single",
                "season": "2024-Kharif",
                "location": "Field Station A",
                "breeder": "Dr. Smith",
                "notes": "Climate adaptation breeding",
                "created": "2024-11-05",
            },
            "CX003": {
                "crossId": "CX003",
                "crossName": "Variety 2023 × Wild",
                "femaleParentId": "germ005",
                "femaleParentName": "Variety 2023",
                "maleParentId": "germ006",
                "maleParentName": "Wild Relative",
                "objective": "Widen genetic base",
                "priority": "medium",
                "targetDate": "2025-01-10",
                "status": "planned",
                "expectedProgeny": 30,
                "actualProgeny": 0,
                "crossType": "wide",
                "season": "2024-Rabi",
                "location": "Greenhouse",
                "breeder": "Dr. Jones",
                "notes": "Pre-breeding for genetic diversity",
                "created": "2024-11-10",
            },
            "CX004": {
                "crossId": "CX004",
                "crossName": "Inbred A × Inbred B",
                "femaleParentId": "germ007",
                "femaleParentName": "Inbred A",
                "maleParentId": "germ008",
                "maleParentName": "Inbred B",
                "objective": "Hybrid development",
                "priority": "high",
                "targetDate": "2024-12-10",
                "status": "completed",
                "expectedProgeny": 200,
                "actualProgeny": 185,
                "crossType": "single",
                "season": "2024-Kharif",
                "location": "Field Station B",
                "breeder": "Dr. Smith",
                "notes": "F1 hybrid seed production",
                "created": "2024-10-15",
                "completedDate": "2024-12-08",
            },
            "CX005": {
                "crossId": "CX005",
                "crossName": "Test 1 × Test 2",
                "femaleParentId": "germ009",
                "femaleParentName": "Test Line 1",
                "maleParentId": "germ010",
                "maleParentName": "Test Line 2",
                "objective": "Recombination",
                "priority": "low",
                "targetDate": "2025-02-01",
                "status": "planned",
                "expectedProgeny": 40,
                "actualProgeny": 0,
                "crossType": "single",
                "season": "2024-Rabi",
                "location": "Field Station A",
                "breeder": "Dr. Jones",
                "notes": "Exploratory cross",
                "created": "2024-11-15",
            },
        }
    
    def list_crosses(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        season: Optional[str] = None,
        breeder: Optional[str] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List planned crosses with filters"""
        results = list(self._crosses.values())
        
        if status:
            results = [c for c in results if c["status"] == status]
        if priority:
            results = [c for c in results if c["priority"] == priority]
        if season:
            results = [c for c in results if c.get("season") == season]
        if breeder:
            results = [c for c in results if breeder.lower() in c.get("breeder", "").lower()]
        
        total = len(results)
        start = page * page_size
        end = start + page_size
        
        return {
            "data": results[start:end],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total,
                "totalPages": (total + page_size - 1) // page_size,
            },
        }
    
    def get_cross(self, cross_id: str) -> Optional[Dict]:
        """Get a single cross by ID"""
        return self._crosses.get(cross_id)
    
    def create_cross(self, data: Dict) -> Dict:
        """Create a new planned cross"""
        cross_num = len(self._crosses) + 1
        cross_id = f"CX{cross_num:03d}"
        
        female = self._germplasm.get(data.get("femaleParentId", ""))
        male = self._germplasm.get(data.get("maleParentId", ""))
        
        cross = {
            "crossId": cross_id,
            "crossName": data.get("crossName", f"{female.get('name', 'Unknown')} × {male.get('name', 'Unknown')}" if female and male else f"Cross {cross_id}"),
            "femaleParentId": data.get("femaleParentId"),
            "femaleParentName": female.get("name") if female else data.get("femaleParentName", "Unknown"),
            "maleParentId": data.get("maleParentId"),
            "maleParentName": male.get("name") if male else data.get("maleParentName", "Unknown"),
            "objective": data.get("objective", ""),
            "priority": data.get("priority", "medium"),
            "targetDate": data.get("targetDate", ""),
            "status": "planned",
            "expectedProgeny": data.get("expectedProgeny", 50),
            "actualProgeny": 0,
            "crossType": data.get("crossType", "single"),
            "season": data.get("season", ""),
            "location": data.get("location", ""),
            "breeder": data.get("breeder", ""),
            "notes": data.get("notes", ""),
            "created": datetime.now().strftime("%Y-%m-%d"),
        }
        
        self._crosses[cross_id] = cross
        return cross
    
    def update_cross(self, cross_id: str, data: Dict) -> Optional[Dict]:
        """Update a cross"""
        if cross_id not in self._crosses:
            return None
        
        cross = self._crosses[cross_id]
        for key in ["objective", "priority", "targetDate", "expectedProgeny", "crossType", "season", "location", "breeder", "notes"]:
            if key in data:
                cross[key] = data[key]
        
        return cross
    
    def update_status(self, cross_id: str, status: str, actual_progeny: Optional[int] = None) -> Optional[Dict]:
        """Update cross status"""
        if cross_id not in self._crosses:
            return None
        
        cross = self._crosses[cross_id]
        cross["status"] = status
        
        if status == "completed":
            cross["completedDate"] = datetime.now().strftime("%Y-%m-%d")
            if actual_progeny is not None:
                cross["actualProgeny"] = actual_progeny
        
        return cross
    
    def delete_cross(self, cross_id: str) -> bool:
        """Delete a cross"""
        if cross_id in self._crosses:
            del self._crosses[cross_id]
            return True
        return False
    
    def get_statistics(self) -> Dict:
        """Get crossing statistics"""
        crosses = list(self._crosses.values())
        
        return {
            "total": len(crosses),
            "planned": sum(1 for c in crosses if c["status"] == "planned"),
            "scheduled": sum(1 for c in crosses if c["status"] == "scheduled"),
            "inProgress": sum(1 for c in crosses if c["status"] == "in_progress"),
            "completed": sum(1 for c in crosses if c["status"] == "completed"),
            "failed": sum(1 for c in crosses if c["status"] == "failed"),
            "totalExpectedProgeny": sum(c["expectedProgeny"] for c in crosses),
            "totalActualProgeny": sum(c["actualProgeny"] for c in crosses),
            "byPriority": {
                "high": sum(1 for c in crosses if c["priority"] == "high"),
                "medium": sum(1 for c in crosses if c["priority"] == "medium"),
                "low": sum(1 for c in crosses if c["priority"] == "low"),
            },
        }
    
    def list_germplasm(self, search: Optional[str] = None) -> List[Dict]:
        """List available germplasm for crossing"""
        results = list(self._germplasm.values())
        if search:
            results = [g for g in results if search.lower() in g["name"].lower()]
        return results


# Singleton instance
crossing_planner_service = CrossingPlannerService()

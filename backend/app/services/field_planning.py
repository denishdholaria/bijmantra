"""
Field Planning Service
Field and season planning for trials
"""
from typing import Optional
from datetime import datetime, timedelta
import random

# Demo field plans
DEMO_FIELD_PLANS = [
    {
        "id": "fp-001",
        "name": "Rice Breeding Block A - 2025",
        "field_id": "field-001",
        "field_name": "North Research Station",
        "season": "Kharif 2025",
        "crop": "Rice",
        "total_plots": 500,
        "allocated_plots": 450,
        "trials": [
            {"trial_id": "t-001", "name": "Yield Trial 2025", "plots": 200},
            {"trial_id": "t-002", "name": "Disease Screening", "plots": 150},
            {"trial_id": "t-003", "name": "Quality Evaluation", "plots": 100}
        ],
        "start_date": "2025-06-15",
        "end_date": "2025-11-30",
        "status": "active"
    },
    {
        "id": "fp-002",
        "name": "Wheat Multi-Location Trial",
        "field_id": "field-002",
        "field_name": "Central Station",
        "season": "Rabi 2024-25",
        "crop": "Wheat",
        "total_plots": 300,
        "allocated_plots": 280,
        "trials": [
            {"trial_id": "t-004", "name": "Advanced Yield Trial", "plots": 180},
            {"trial_id": "t-005", "name": "Heat Tolerance", "plots": 100}
        ],
        "start_date": "2024-11-01",
        "end_date": "2025-04-15",
        "status": "active"
    }
]

# Demo season plans
DEMO_SEASON_PLANS = [
    {
        "id": "sp-001",
        "name": "Kharif 2025",
        "year": 2025,
        "season_type": "Kharif",
        "start_date": "2025-06-01",
        "end_date": "2025-11-30",
        "crops": ["Rice", "Maize", "Sorghum"],
        "total_trials": 25,
        "total_plots": 2500,
        "budget": 500000,
        "status": "planning"
    },
    {
        "id": "sp-002",
        "name": "Rabi 2024-25",
        "year": 2025,
        "season_type": "Rabi",
        "start_date": "2024-11-01",
        "end_date": "2025-04-30",
        "crops": ["Wheat", "Chickpea", "Mustard"],
        "total_trials": 18,
        "total_plots": 1800,
        "budget": 400000,
        "status": "active"
    }
]


class FieldPlanningService:
    """Service for field and season planning"""
    
    async def get_field_plans(
        self,
        field_id: Optional[str] = None,
        season: Optional[str] = None,
        status: Optional[str] = None
    ) -> list:
        """Get field plans"""
        plans = DEMO_FIELD_PLANS.copy()
        
        if field_id:
            plans = [p for p in plans if p["field_id"] == field_id]
        if season:
            plans = [p for p in plans if season.lower() in p["season"].lower()]
        if status:
            plans = [p for p in plans if p["status"] == status]
            
        return plans
    
    async def get_field_plan(self, plan_id: str) -> Optional[dict]:
        """Get single field plan"""
        for p in DEMO_FIELD_PLANS:
            if p["id"] == plan_id:
                return p
        return None
    
    async def get_season_plans(
        self,
        year: Optional[int] = None,
        season_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> list:
        """Get season plans"""
        plans = DEMO_SEASON_PLANS.copy()
        
        if year:
            plans = [p for p in plans if p["year"] == year]
        if season_type:
            plans = [p for p in plans if p["season_type"].lower() == season_type.lower()]
        if status:
            plans = [p for p in plans if p["status"] == status]
            
        return plans
    
    async def get_season_plan(self, plan_id: str) -> Optional[dict]:
        """Get single season plan"""
        for p in DEMO_SEASON_PLANS:
            if p["id"] == plan_id:
                return p
        return None
    
    async def get_resource_allocation(self, plan_id: str) -> dict:
        """Get resource allocation for a plan"""
        return {
            "plan_id": plan_id,
            "resources": [
                {"type": "Labor", "required": 50, "allocated": 45, "unit": "person-days"},
                {"type": "Seeds", "required": 500, "allocated": 480, "unit": "kg"},
                {"type": "Fertilizer", "required": 200, "allocated": 200, "unit": "kg"},
                {"type": "Equipment", "required": 5, "allocated": 4, "unit": "units"},
            ],
            "budget": {
                "total": 100000,
                "allocated": 85000,
                "spent": 45000
            }
        }
    
    async def get_calendar(self, year: int, month: Optional[int] = None) -> list:
        """Get planning calendar"""
        events = []
        base_date = datetime(year, month or 1, 1)
        
        activities = [
            "Land preparation", "Sowing", "Fertilizer application",
            "Irrigation", "Pest scouting", "Data collection", "Harvest"
        ]
        
        for i in range(12 if not month else 1):
            current_month = (month or 1) + i if month else i + 1
            if current_month > 12:
                break
            for j in range(random.randint(3, 8)):
                events.append({
                    "id": f"evt-{current_month}-{j}",
                    "date": f"{year}-{current_month:02d}-{random.randint(1, 28):02d}",
                    "activity": random.choice(activities),
                    "field": f"Field {random.randint(1, 5)}",
                    "trial": f"Trial {random.randint(1, 10)}"
                })
        
        return sorted(events, key=lambda x: x["date"])
    
    async def get_statistics(self) -> dict:
        """Get planning statistics"""
        return {
            "total_field_plans": len(DEMO_FIELD_PLANS),
            "total_season_plans": len(DEMO_SEASON_PLANS),
            "active_plans": len([p for p in DEMO_FIELD_PLANS if p["status"] == "active"]),
            "total_plots_planned": sum(p["total_plots"] for p in DEMO_FIELD_PLANS),
            "total_plots_allocated": sum(p["allocated_plots"] for p in DEMO_FIELD_PLANS),
            "utilization_rate": round(
                sum(p["allocated_plots"] for p in DEMO_FIELD_PLANS) / 
                sum(p["total_plots"] for p in DEMO_FIELD_PLANS) * 100, 1
            )
        }


# Singleton instance
field_planning_service = FieldPlanningService()

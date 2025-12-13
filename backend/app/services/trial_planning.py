"""
Trial Planning Service
Manages trial planning, scheduling, and resource allocation
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import uuid


class TrialStatus(str, Enum):
    PLANNING = "planning"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TrialType(str, Enum):
    OYT = "OYT"  # Observation Yield Trial
    PYT = "PYT"  # Preliminary Yield Trial
    AYT = "AYT"  # Advanced Yield Trial
    MLT = "MLT"  # Multi-Location Trial
    DST = "DST"  # Disease Screening Trial
    QT = "QT"    # Quality Trial
    DUS = "DUS"  # DUS Trial


@dataclass
class PlannedTrial:
    """Planned trial definition"""
    id: str
    name: str
    trial_type: TrialType
    season: str
    year: int
    locations: List[str]
    entries: int
    reps: int
    design: str
    status: TrialStatus
    progress: int
    start_date: date
    end_date: Optional[date] = None
    program_id: Optional[str] = None
    program_name: Optional[str] = None
    crop: str = "Rice"
    objectives: Optional[str] = None
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_date: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_plots(self) -> int:
        return self.entries * self.reps * len(self.locations)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.trial_type.value,
            "season": self.season,
            "year": self.year,
            "locations": self.locations,
            "entries": self.entries,
            "reps": self.reps,
            "design": self.design,
            "status": self.status.value,
            "progress": self.progress,
            "startDate": self.start_date.isoformat(),
            "endDate": self.end_date.isoformat() if self.end_date else None,
            "programId": self.program_id,
            "programName": self.program_name,
            "crop": self.crop,
            "objectives": self.objectives,
            "totalPlots": self.total_plots,
            "createdBy": self.created_by,
            "approvedBy": self.approved_by,
            "approvedDate": self.approved_date.isoformat() if self.approved_date else None,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass
class TrialResource:
    """Resource allocation for a trial"""
    id: str
    trial_id: str
    resource_type: str  # seed, labor, equipment, chemicals
    resource_name: str
    quantity: float
    unit: str
    estimated_cost: float
    status: str  # planned, allocated, used
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trialId": self.trial_id,
            "resourceType": self.resource_type,
            "resourceName": self.resource_name,
            "quantity": self.quantity,
            "unit": self.unit,
            "estimatedCost": self.estimated_cost,
            "status": self.status,
        }


class TrialPlanningService:
    """Service for trial planning and scheduling"""
    
    def __init__(self):
        self._trials: Dict[str, PlannedTrial] = {}
        self._resources: Dict[str, List[TrialResource]] = {}  # trial_id -> resources
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize demo trials"""
        demo_trials = [
            PlannedTrial(
                id="TRL-001",
                name="Advanced Yield Trial 2025",
                trial_type=TrialType.AYT,
                season="Rabi 2025",
                year=2025,
                locations=["Location A", "Location B", "Location C"],
                entries=25,
                reps=3,
                design="RCBD",
                status=TrialStatus.PLANNING,
                progress=30,
                start_date=date(2025, 1, 15),
                end_date=date(2025, 5, 15),
                program_id="PRG-001",
                program_name="Rice Improvement Program",
                crop="Rice",
                objectives="Evaluate advanced breeding lines for yield potential",
                created_by="Dr. Sharma",
            ),
            PlannedTrial(
                id="TRL-002",
                name="Multi-Location Trial 2025",
                trial_type=TrialType.MLT,
                season="Rabi 2025",
                year=2025,
                locations=["Location A", "Location B", "Location C", "Location D", "Location E"],
                entries=15,
                reps=3,
                design="Alpha-Lattice",
                status=TrialStatus.APPROVED,
                progress=60,
                start_date=date(2025, 1, 20),
                end_date=date(2025, 5, 20),
                program_id="PRG-001",
                program_name="Rice Improvement Program",
                crop="Rice",
                objectives="Test stability across multiple environments",
                created_by="Dr. Sharma",
                approved_by="Dr. Patel",
                approved_date=date(2024, 12, 15),
            ),
            PlannedTrial(
                id="TRL-003",
                name="Preliminary Yield Trial",
                trial_type=TrialType.PYT,
                season="Kharif 2024",
                year=2024,
                locations=["Location A"],
                entries=100,
                reps=2,
                design="Augmented",
                status=TrialStatus.ACTIVE,
                progress=85,
                start_date=date(2024, 7, 1),
                end_date=date(2024, 11, 30),
                program_id="PRG-002",
                program_name="Wheat Breeding Program",
                crop="Wheat",
                objectives="Initial screening of new breeding lines",
                created_by="Dr. Kumar",
                approved_by="Dr. Patel",
                approved_date=date(2024, 6, 15),
            ),
            PlannedTrial(
                id="TRL-004",
                name="Disease Screening Trial",
                trial_type=TrialType.DST,
                season="Kharif 2024",
                year=2024,
                locations=["Location B"],
                entries=50,
                reps=2,
                design="RCBD",
                status=TrialStatus.COMPLETED,
                progress=100,
                start_date=date(2024, 6, 15),
                end_date=date(2024, 10, 15),
                program_id="PRG-001",
                program_name="Rice Improvement Program",
                crop="Rice",
                objectives="Screen for blast and bacterial blight resistance",
                created_by="Dr. Singh",
                approved_by="Dr. Sharma",
                approved_date=date(2024, 6, 1),
            ),
            PlannedTrial(
                id="TRL-005",
                name="Quality Evaluation Trial",
                trial_type=TrialType.QT,
                season="Rabi 2025",
                year=2025,
                locations=["Location A", "Location C"],
                entries=20,
                reps=3,
                design="RCBD",
                status=TrialStatus.PLANNING,
                progress=15,
                start_date=date(2025, 2, 1),
                end_date=date(2025, 6, 1),
                program_id="PRG-001",
                program_name="Rice Improvement Program",
                crop="Rice",
                objectives="Evaluate grain quality parameters",
                created_by="Dr. Sharma",
            ),
        ]
        
        for trial in demo_trials:
            self._trials[trial.id] = trial
            self._resources[trial.id] = self._generate_resources(trial)
    
    def _generate_resources(self, trial: PlannedTrial) -> List[TrialResource]:
        """Generate resource allocations for a trial"""
        resources = []
        
        # Seed requirement
        seed_qty = trial.entries * trial.reps * len(trial.locations) * 0.5  # 0.5 kg per plot
        resources.append(TrialResource(
            id=f"{trial.id}-R001",
            trial_id=trial.id,
            resource_type="seed",
            resource_name="Seed material",
            quantity=seed_qty,
            unit="kg",
            estimated_cost=seed_qty * 100,
            status="planned" if trial.status == TrialStatus.PLANNING else "allocated",
        ))
        
        # Labor
        labor_days = trial.total_plots * 0.1  # 0.1 person-days per plot
        resources.append(TrialResource(
            id=f"{trial.id}-R002",
            trial_id=trial.id,
            resource_type="labor",
            resource_name="Field labor",
            quantity=labor_days,
            unit="person-days",
            estimated_cost=labor_days * 500,
            status="planned" if trial.status == TrialStatus.PLANNING else "allocated",
        ))
        
        # Fertilizer
        fert_qty = trial.total_plots * 0.2  # 0.2 kg per plot
        resources.append(TrialResource(
            id=f"{trial.id}-R003",
            trial_id=trial.id,
            resource_type="chemicals",
            resource_name="NPK Fertilizer",
            quantity=fert_qty,
            unit="kg",
            estimated_cost=fert_qty * 50,
            status="planned" if trial.status == TrialStatus.PLANNING else "allocated",
        ))
        
        return resources
    
    # Trial CRUD
    def list_trials(
        self,
        status: Optional[str] = None,
        trial_type: Optional[str] = None,
        season: Optional[str] = None,
        year: Optional[int] = None,
        crop: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List trials with optional filters"""
        trials = list(self._trials.values())
        
        if status:
            trials = [t for t in trials if t.status.value == status]
        
        if trial_type:
            trials = [t for t in trials if t.trial_type.value == trial_type]
        
        if season:
            trials = [t for t in trials if t.season == season]
        
        if year:
            trials = [t for t in trials if t.year == year]
        
        if crop:
            trials = [t for t in trials if t.crop.lower() == crop.lower()]
        
        if search:
            search_lower = search.lower()
            trials = [t for t in trials if search_lower in t.name.lower() or search_lower in (t.objectives or "").lower()]
        
        # Sort by start date descending
        trials.sort(key=lambda t: t.start_date, reverse=True)
        
        return [t.to_dict() for t in trials]
    
    def get_trial(self, trial_id: str) -> Optional[Dict[str, Any]]:
        """Get trial by ID"""
        trial = self._trials.get(trial_id)
        if trial:
            result = trial.to_dict()
            result["resources"] = [r.to_dict() for r in self._resources.get(trial_id, [])]
            return result
        return None
    
    def create_trial(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new planned trial"""
        trial_id = f"TRL-{uuid.uuid4().hex[:6].upper()}"
        
        trial = PlannedTrial(
            id=trial_id,
            name=data["name"],
            trial_type=TrialType(data["type"]),
            season=data["season"],
            year=data.get("year", date.today().year),
            locations=data["locations"],
            entries=data["entries"],
            reps=data["reps"],
            design=data.get("design", "RCBD"),
            status=TrialStatus.PLANNING,
            progress=0,
            start_date=date.fromisoformat(data["startDate"]),
            end_date=date.fromisoformat(data["endDate"]) if data.get("endDate") else None,
            program_id=data.get("programId"),
            program_name=data.get("programName"),
            crop=data.get("crop", "Rice"),
            objectives=data.get("objectives"),
            created_by=data.get("createdBy"),
        )
        
        self._trials[trial_id] = trial
        self._resources[trial_id] = self._generate_resources(trial)
        
        return trial.to_dict()
    
    def update_trial(self, trial_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a trial"""
        trial = self._trials.get(trial_id)
        if not trial:
            return None
        
        if "name" in data:
            trial.name = data["name"]
        if "type" in data:
            trial.trial_type = TrialType(data["type"])
        if "season" in data:
            trial.season = data["season"]
        if "year" in data:
            trial.year = data["year"]
        if "locations" in data:
            trial.locations = data["locations"]
        if "entries" in data:
            trial.entries = data["entries"]
        if "reps" in data:
            trial.reps = data["reps"]
        if "design" in data:
            trial.design = data["design"]
        if "status" in data:
            trial.status = TrialStatus(data["status"])
        if "progress" in data:
            trial.progress = data["progress"]
        if "startDate" in data:
            trial.start_date = date.fromisoformat(data["startDate"])
        if "endDate" in data:
            trial.end_date = date.fromisoformat(data["endDate"]) if data["endDate"] else None
        if "objectives" in data:
            trial.objectives = data["objectives"]
        
        trial.updated_at = datetime.now()
        return trial.to_dict()
    
    def delete_trial(self, trial_id: str) -> bool:
        """Delete a trial"""
        if trial_id in self._trials:
            del self._trials[trial_id]
            if trial_id in self._resources:
                del self._resources[trial_id]
            return True
        return False
    
    # Status transitions
    def approve_trial(self, trial_id: str, approved_by: str) -> Optional[Dict[str, Any]]:
        """Approve a trial"""
        trial = self._trials.get(trial_id)
        if not trial or trial.status != TrialStatus.PLANNING:
            return None
        
        trial.status = TrialStatus.APPROVED
        trial.approved_by = approved_by
        trial.approved_date = date.today()
        trial.progress = max(trial.progress, 50)
        trial.updated_at = datetime.now()
        
        # Update resource status
        for resource in self._resources.get(trial_id, []):
            resource.status = "allocated"
        
        return trial.to_dict()
    
    def start_trial(self, trial_id: str) -> Optional[Dict[str, Any]]:
        """Start a trial (move to active)"""
        trial = self._trials.get(trial_id)
        if not trial or trial.status != TrialStatus.APPROVED:
            return None
        
        trial.status = TrialStatus.ACTIVE
        trial.progress = max(trial.progress, 60)
        trial.updated_at = datetime.now()
        
        return trial.to_dict()
    
    def complete_trial(self, trial_id: str) -> Optional[Dict[str, Any]]:
        """Complete a trial"""
        trial = self._trials.get(trial_id)
        if not trial or trial.status != TrialStatus.ACTIVE:
            return None
        
        trial.status = TrialStatus.COMPLETED
        trial.progress = 100
        trial.end_date = date.today()
        trial.updated_at = datetime.now()
        
        # Update resource status
        for resource in self._resources.get(trial_id, []):
            resource.status = "used"
        
        return trial.to_dict()
    
    def cancel_trial(self, trial_id: str, reason: str) -> Optional[Dict[str, Any]]:
        """Cancel a trial"""
        trial = self._trials.get(trial_id)
        if not trial or trial.status == TrialStatus.COMPLETED:
            return None
        
        trial.status = TrialStatus.CANCELLED
        trial.updated_at = datetime.now()
        
        return trial.to_dict()
    
    # Resources
    def get_resources(self, trial_id: str) -> List[Dict[str, Any]]:
        """Get resources for a trial"""
        return [r.to_dict() for r in self._resources.get(trial_id, [])]
    
    def add_resource(self, trial_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a resource to a trial"""
        if trial_id not in self._trials:
            return None
        
        resource_id = f"{trial_id}-R{len(self._resources.get(trial_id, [])) + 1:03d}"
        
        resource = TrialResource(
            id=resource_id,
            trial_id=trial_id,
            resource_type=data["resourceType"],
            resource_name=data["resourceName"],
            quantity=data["quantity"],
            unit=data["unit"],
            estimated_cost=data.get("estimatedCost", 0),
            status=data.get("status", "planned"),
        )
        
        if trial_id not in self._resources:
            self._resources[trial_id] = []
        self._resources[trial_id].append(resource)
        
        return resource.to_dict()
    
    # Statistics
    def get_statistics(self) -> Dict[str, Any]:
        """Get trial planning statistics"""
        trials = list(self._trials.values())
        
        status_counts = {}
        type_counts = {}
        total_plots = 0
        total_entries = 0
        
        for trial in trials:
            status_counts[trial.status.value] = status_counts.get(trial.status.value, 0) + 1
            type_counts[trial.trial_type.value] = type_counts.get(trial.trial_type.value, 0) + 1
            total_plots += trial.total_plots
            total_entries += trial.entries
        
        # Calculate total estimated cost
        total_cost = 0
        for resources in self._resources.values():
            for r in resources:
                total_cost += r.estimated_cost
        
        return {
            "totalTrials": len(trials),
            "byStatus": status_counts,
            "byType": type_counts,
            "totalPlots": total_plots,
            "totalEntries": total_entries,
            "totalEstimatedCost": total_cost,
            "planning": status_counts.get("planning", 0),
            "active": status_counts.get("active", 0),
            "completed": status_counts.get("completed", 0),
        }
    
    def get_timeline(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get trial timeline for visualization"""
        trials = list(self._trials.values())
        
        if year:
            trials = [t for t in trials if t.year == year]
        
        # Sort by start date
        trials.sort(key=lambda t: t.start_date)
        
        return [{
            "id": t.id,
            "name": t.name,
            "type": t.trial_type.value,
            "status": t.status.value,
            "startDate": t.start_date.isoformat(),
            "endDate": t.end_date.isoformat() if t.end_date else None,
            "locations": len(t.locations),
            "progress": t.progress,
        } for t in trials]
    
    def get_trial_types(self) -> List[Dict[str, str]]:
        """Get list of trial types"""
        return [
            {"value": "OYT", "label": "Observation Yield Trial"},
            {"value": "PYT", "label": "Preliminary Yield Trial"},
            {"value": "AYT", "label": "Advanced Yield Trial"},
            {"value": "MLT", "label": "Multi-Location Trial"},
            {"value": "DST", "label": "Disease Screening Trial"},
            {"value": "QT", "label": "Quality Trial"},
            {"value": "DUS", "label": "DUS Trial"},
        ]
    
    def get_seasons(self) -> List[str]:
        """Get list of seasons"""
        return list(set(t.season for t in self._trials.values()))
    
    def get_designs(self) -> List[Dict[str, str]]:
        """Get list of trial designs"""
        return [
            {"value": "RCBD", "label": "Randomized Complete Block Design"},
            {"value": "Alpha-Lattice", "label": "Alpha-Lattice Design"},
            {"value": "Augmented", "label": "Augmented Design"},
            {"value": "Split-Plot", "label": "Split-Plot Design"},
            {"value": "CRD", "label": "Completely Randomized Design"},
        ]


# Singleton instance
_trial_planning_service: Optional[TrialPlanningService] = None


def get_trial_planning_service() -> TrialPlanningService:
    """Get or create trial planning service singleton"""
    global _trial_planning_service
    if _trial_planning_service is None:
        _trial_planning_service = TrialPlanningService()
    return _trial_planning_service

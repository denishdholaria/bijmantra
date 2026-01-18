"""
Resource Management Service

Handles resource allocation, calendar scheduling, and harvest logging.
Provides backend for:
- /resource-allocation
- /resource-calendar  
- /harvest-log
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import uuid4


class ResourceType(str, Enum):
    FIELD = "field"
    LAB = "lab"
    EQUIPMENT = "equipment"
    MEETING = "meeting"
    PERSONNEL = "personnel"


class EventStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BudgetStatus(str, Enum):
    ON_TRACK = "on-track"
    OVER = "over"
    UNDER = "under"


class HarvestQuality(str, Enum):
    A = "A"
    B = "B"
    C = "C"


@dataclass
class BudgetCategory:
    id: str
    name: str
    allocated: float
    used: float
    unit: str
    status: str
    year: int
    organization_id: int = 1


@dataclass
class StaffAllocation:
    id: str
    role: str
    count: int
    projects: int
    department: str
    organization_id: int = 1


@dataclass
class FieldAllocation:
    id: str
    field: str
    area: float
    trials: int
    utilization: float
    location_id: Optional[int] = None
    organization_id: int = 1


@dataclass
class CalendarEvent:
    id: str
    title: str
    type: str
    date: str
    time: str
    duration: str
    location: str
    assignee: str
    status: str
    description: Optional[str] = None
    trial_id: Optional[int] = None
    organization_id: int = 1


@dataclass
class HarvestRecord:
    id: str
    entry: str
    plot: str
    harvest_date: str
    fresh_weight: float
    dry_weight: float
    moisture: float
    grain_yield: float
    quality: str
    trial_id: Optional[int] = None
    study_id: Optional[int] = None
    notes: Optional[str] = None
    recorded_by: Optional[str] = None
    organization_id: int = 1


class ResourceManagementService:
    """Service for managing resources, calendar, and harvest data."""
    
    def __init__(self):
        # In-memory storage (would be database in production)
        self._budget_categories: Dict[str, BudgetCategory] = {}
        self._staff_allocations: Dict[str, StaffAllocation] = {}
        self._field_allocations: Dict[str, FieldAllocation] = {}
        self._calendar_events: Dict[str, CalendarEvent] = {}
        self._harvest_records: Dict[str, HarvestRecord] = {}
        
        # Initialize with demo data
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize with realistic demo data."""
        # Budget categories
        budget_data = [
            ("Field Operations", 150000, 98000),
            ("Laboratory", 80000, 72000),
            ("Personnel", 250000, 208000),
            ("Equipment", 50000, 55000),
            ("Consumables", 30000, 18000),
            ("Travel", 25000, 12000),
            ("Training", 15000, 8000),
            ("Software & IT", 20000, 18500),
        ]
        for name, allocated, used in budget_data:
            status = "on-track" if used <= allocated * 0.9 else ("over" if used > allocated else "under")
            cat = BudgetCategory(
                id=f"budget-{uuid4().hex[:8]}",
                name=name,
                allocated=allocated,
                used=used,
                unit="USD",
                status=status,
                year=2025
            )
            self._budget_categories[cat.id] = cat
        
        # Staff allocations
        staff_data = [
            ("Breeders", 4, 8, "Breeding"),
            ("Technicians", 12, 15, "Field Operations"),
            ("Data Analysts", 2, 6, "Bioinformatics"),
            ("Field Workers", 20, 12, "Field Operations"),
            ("Lab Technicians", 6, 10, "Laboratory"),
            ("Research Associates", 3, 5, "Research"),
        ]
        for role, count, projects, dept in staff_data:
            staff = StaffAllocation(
                id=f"staff-{uuid4().hex[:8]}",
                role=role,
                count=count,
                projects=projects,
                department=dept
            )
            self._staff_allocations[staff.id] = staff
        
        # Field allocations
        field_data = [
            ("Field A - Main Station", 5.0, 4, 85),
            ("Field B - North Block", 3.5, 3, 72),
            ("Field C - South Block", 4.0, 2, 45),
            ("Field D - Irrigated", 2.5, 3, 90),
            ("Greenhouse 1", 0.5, 6, 95),
            ("Greenhouse 2", 0.3, 4, 80),
            ("Nursery Area", 1.0, 8, 75),
        ]
        for field, area, trials, util in field_data:
            fa = FieldAllocation(
                id=f"field-{uuid4().hex[:8]}",
                field=field,
                area=area,
                trials=trials,
                utilization=util
            )
            self._field_allocations[fa.id] = fa
        
        # Calendar events
        base_date = date.today()
        events_data = [
            ("Field Planting - Block A", "field", 0, "06:00", "4h", "Field Station 1", "Maria Garcia"),
            ("DNA Extraction - Batch 12", "lab", 0, "09:00", "3h", "Molecular Lab", "Dr. Sarah Chen"),
            ("Tractor Maintenance", "equipment", 1, "08:00", "2h", "Equipment Shed", "John Smith"),
            ("Breeding Team Meeting", "meeting", 1, "14:00", "1h", "Conference Room", "All Team"),
            ("Phenotyping - Plant Height", "field", 2, "07:00", "6h", "Trial Block B", "Raj Patel"),
            ("PCR Analysis", "lab", 3, "10:00", "4h", "Molecular Lab", "Aisha Okonkwo"),
            ("Irrigation System Check", "equipment", 3, "08:00", "2h", "Field A", "Carlos Rodriguez"),
            ("Data Review Meeting", "meeting", 4, "10:00", "2h", "Conference Room", "Data Team"),
            ("Seed Processing", "lab", 5, "09:00", "5h", "Seed Lab", "Emily Watson"),
            ("Harvest - Trial 2025-A", "field", 6, "06:00", "8h", "Field A", "Field Team"),
            ("Equipment Calibration", "equipment", 7, "09:00", "3h", "Lab", "Tech Team"),
            ("Weekly Progress Review", "meeting", 7, "15:00", "1h", "Conference Room", "All Staff"),
        ]
        for title, etype, day_offset, time, duration, location, assignee in events_data:
            event_date = base_date + timedelta(days=day_offset)
            event = CalendarEvent(
                id=f"event-{uuid4().hex[:8]}",
                title=title,
                type=etype,
                date=event_date.isoformat(),
                time=time,
                duration=duration,
                location=location,
                assignee=assignee,
                status="scheduled"
            )
            self._calendar_events[event.id] = event
        
        # Harvest records
        harvest_data = [
            ("BIJ-R-001", "A-001", -5, 12.5, 10.2, 14.2, 8.5, "A"),
            ("BIJ-R-002", "A-002", -5, 11.8, 9.6, 14.8, 7.9, "A"),
            ("BIJ-R-003", "A-003", -4, 10.2, 8.1, 15.5, 6.8, "B"),
            ("BIJ-R-004", "A-004", -4, 13.1, 10.8, 13.9, 9.1, "A"),
            ("BIJ-R-005", "A-005", -3, 9.8, 7.9, 15.2, 6.5, "B"),
            ("BIJ-R-006", "A-006", -3, 14.2, 11.5, 13.5, 9.6, "A"),
            ("BIJ-R-007", "B-001", -2, 11.0, 8.9, 14.6, 7.4, "A"),
            ("BIJ-R-008", "B-002", -2, 8.5, 6.8, 16.1, 5.6, "C"),
            ("BIJ-R-009", "B-003", -1, 12.8, 10.4, 14.0, 8.7, "A"),
            ("BIJ-R-010", "B-004", -1, 10.5, 8.5, 14.9, 7.1, "B"),
        ]
        for entry, plot, day_offset, fresh, dry, moisture, yield_val, quality in harvest_data:
            harvest_date = base_date + timedelta(days=day_offset)
            record = HarvestRecord(
                id=f"harvest-{uuid4().hex[:8]}",
                entry=entry,
                plot=plot,
                harvest_date=harvest_date.isoformat(),
                fresh_weight=fresh,
                dry_weight=dry,
                moisture=moisture,
                grain_yield=yield_val,
                quality=quality,
                recorded_by="System"
            )
            self._harvest_records[record.id] = record
    
    # ==========================================
    # Budget Management
    # ==========================================
    
    def get_budget_categories(self, year: int = 2025) -> List[Dict]:
        """Get all budget categories for a year."""
        return [asdict(c) for c in self._budget_categories.values() if c.year == year]
    
    def get_budget_summary(self, year: int = 2025) -> Dict:
        """Get budget summary statistics."""
        categories = [c for c in self._budget_categories.values() if c.year == year]
        total_allocated = sum(c.allocated for c in categories)
        total_used = sum(c.used for c in categories)
        
        return {
            "year": year,
            "total_allocated": total_allocated,
            "total_used": total_used,
            "utilization_percent": round((total_used / total_allocated) * 100, 1) if total_allocated > 0 else 0,
            "remaining": total_allocated - total_used,
            "categories_count": len(categories),
            "over_budget_count": len([c for c in categories if c.status == "over"]),
            "on_track_count": len([c for c in categories if c.status == "on-track"]),
        }
    
    def update_budget_category(self, category_id: str, used: float) -> Optional[Dict]:
        """Update budget usage for a category."""
        if category_id not in self._budget_categories:
            return None
        
        cat = self._budget_categories[category_id]
        cat.used = used
        cat.status = "on-track" if used <= cat.allocated * 0.9 else ("over" if used > cat.allocated else "under")
        return asdict(cat)
    
    # ==========================================
    # Staff Allocation
    # ==========================================
    
    def get_staff_allocations(self) -> List[Dict]:
        """Get all staff allocations."""
        return [asdict(s) for s in self._staff_allocations.values()]
    
    def get_staff_summary(self) -> Dict:
        """Get staff summary statistics."""
        staff = list(self._staff_allocations.values())
        total_staff = sum(s.count for s in staff)
        total_projects = sum(s.projects for s in staff)
        
        return {
            "total_staff": total_staff,
            "total_projects": total_projects,
            "roles_count": len(staff),
            "avg_projects_per_person": round(total_projects / total_staff, 1) if total_staff > 0 else 0,
            "by_department": self._group_staff_by_department(),
        }
    
    def _group_staff_by_department(self) -> Dict[str, int]:
        """Group staff count by department."""
        result = {}
        for s in self._staff_allocations.values():
            result[s.department] = result.get(s.department, 0) + s.count
        return result
    
    # ==========================================
    # Field Allocation
    # ==========================================
    
    def get_field_allocations(self) -> List[Dict]:
        """Get all field allocations."""
        return [asdict(f) for f in self._field_allocations.values()]
    
    def get_field_summary(self) -> Dict:
        """Get field summary statistics."""
        fields = list(self._field_allocations.values())
        total_area = sum(f.area for f in fields)
        total_trials = sum(f.trials for f in fields)
        avg_utilization = sum(f.utilization for f in fields) / len(fields) if fields else 0
        
        return {
            "total_area_ha": round(total_area, 1),
            "total_trials": total_trials,
            "fields_count": len(fields),
            "avg_utilization": round(avg_utilization, 1),
            "high_utilization_count": len([f for f in fields if f.utilization > 80]),
            "low_utilization_count": len([f for f in fields if f.utilization < 50]),
        }
    
    # ==========================================
    # Calendar Events
    # ==========================================
    
    def get_calendar_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """Get calendar events with optional filters."""
        events = list(self._calendar_events.values())
        
        if start_date:
            events = [e for e in events if e.date >= start_date]
        if end_date:
            events = [e for e in events if e.date <= end_date]
        if event_type:
            events = [e for e in events if e.type == event_type]
        if status:
            events = [e for e in events if e.status == status]
        
        # Sort by date and time
        events.sort(key=lambda e: (e.date, e.time))
        return [asdict(e) for e in events]
    
    def get_events_by_date(self, target_date: str) -> List[Dict]:
        """Get all events for a specific date."""
        events = [e for e in self._calendar_events.values() if e.date == target_date]
        events.sort(key=lambda e: e.time)
        return [asdict(e) for e in events]
    
    def get_calendar_summary(self) -> Dict:
        """Get calendar summary by event type."""
        events = list(self._calendar_events.values())
        today = date.today().isoformat()
        
        by_type = {}
        for e in events:
            by_type[e.type] = by_type.get(e.type, 0) + 1
        
        upcoming = [e for e in events if e.date >= today and e.status == "scheduled"]
        
        return {
            "total_events": len(events),
            "upcoming_count": len(upcoming),
            "by_type": by_type,
            "next_7_days": len([e for e in upcoming if e.date <= (date.today() + timedelta(days=7)).isoformat()]),
        }
    
    def create_calendar_event(self, event_data: Dict) -> Dict:
        """Create a new calendar event."""
        event = CalendarEvent(
            id=f"event-{uuid4().hex[:8]}",
            title=event_data["title"],
            type=event_data.get("type", "meeting"),
            date=event_data["date"],
            time=event_data.get("time", "09:00"),
            duration=event_data.get("duration", "1h"),
            location=event_data.get("location", "TBD"),
            assignee=event_data.get("assignee", "Unassigned"),
            status="scheduled",
            description=event_data.get("description"),
            trial_id=event_data.get("trial_id"),
        )
        self._calendar_events[event.id] = event
        return asdict(event)
    
    def update_event_status(self, event_id: str, status: str) -> Optional[Dict]:
        """Update event status."""
        if event_id not in self._calendar_events:
            return None
        
        event = self._calendar_events[event_id]
        event.status = status
        return asdict(event)
    
    def delete_calendar_event(self, event_id: str) -> bool:
        """Delete a calendar event."""
        if event_id in self._calendar_events:
            del self._calendar_events[event_id]
            return True
        return False
    
    # ==========================================
    # Harvest Records
    # ==========================================
    
    def get_harvest_records(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        quality: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict]:
        """Get harvest records with optional filters."""
        records = list(self._harvest_records.values())
        
        if start_date:
            records = [r for r in records if r.harvest_date >= start_date]
        if end_date:
            records = [r for r in records if r.harvest_date <= end_date]
        if quality:
            records = [r for r in records if r.quality == quality]
        if search:
            search_lower = search.lower()
            records = [r for r in records if search_lower in r.entry.lower() or search_lower in r.plot.lower()]
        
        # Sort by date descending
        records.sort(key=lambda r: r.harvest_date, reverse=True)
        return [asdict(r) for r in records]
    
    def get_harvest_summary(self) -> Dict:
        """Get harvest summary statistics."""
        records = list(self._harvest_records.values())
        
        if not records:
            return {
                "total_records": 0,
                "avg_yield": 0,
                "total_dry_weight": 0,
                "quality_distribution": {},
            }
        
        total_yield = sum(r.grain_yield for r in records)
        total_dry_weight = sum(r.dry_weight for r in records)
        avg_moisture = sum(r.moisture for r in records) / len(records)
        
        quality_dist = {}
        for r in records:
            quality_dist[r.quality] = quality_dist.get(r.quality, 0) + 1
        
        return {
            "total_records": len(records),
            "avg_yield": round(total_yield / len(records), 2),
            "max_yield": max(r.grain_yield for r in records),
            "min_yield": min(r.grain_yield for r in records),
            "total_dry_weight": round(total_dry_weight, 1),
            "avg_moisture": round(avg_moisture, 1),
            "quality_distribution": quality_dist,
            "grade_a_count": quality_dist.get("A", 0),
            "grade_a_percent": round((quality_dist.get("A", 0) / len(records)) * 100, 1),
        }
    
    def create_harvest_record(self, record_data: Dict) -> Dict:
        """Create a new harvest record."""
        record = HarvestRecord(
            id=f"harvest-{uuid4().hex[:8]}",
            entry=record_data["entry"],
            plot=record_data["plot"],
            harvest_date=record_data.get("harvest_date", date.today().isoformat()),
            fresh_weight=record_data["fresh_weight"],
            dry_weight=record_data["dry_weight"],
            moisture=record_data.get("moisture", 14.0),
            grain_yield=record_data["grain_yield"],
            quality=record_data.get("quality", "B"),
            trial_id=record_data.get("trial_id"),
            study_id=record_data.get("study_id"),
            notes=record_data.get("notes"),
            recorded_by=record_data.get("recorded_by", "System"),
        )
        self._harvest_records[record.id] = record
        return asdict(record)
    
    def update_harvest_record(self, record_id: str, updates: Dict) -> Optional[Dict]:
        """Update a harvest record."""
        if record_id not in self._harvest_records:
            return None
        
        record = self._harvest_records[record_id]
        for key, value in updates.items():
            if hasattr(record, key):
                setattr(record, key, value)
        
        return asdict(record)
    
    def delete_harvest_record(self, record_id: str) -> bool:
        """Delete a harvest record."""
        if record_id in self._harvest_records:
            del self._harvest_records[record_id]
            return True
        return False
    
    # ==========================================
    # Resource Overview
    # ==========================================
    
    def get_resource_overview(self) -> Dict:
        """Get complete resource overview."""
        return {
            "budget": self.get_budget_summary(),
            "staff": self.get_staff_summary(),
            "fields": self.get_field_summary(),
            "calendar": self.get_calendar_summary(),
            "harvest": self.get_harvest_summary(),
        }


# Singleton instance
resource_management_service = ResourceManagementService()

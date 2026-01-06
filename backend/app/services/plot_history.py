"""
Plot History Service
Manages plot event history and timeline tracking
"""
from datetime import datetime, date, timedelta
from typing import Optional
import uuid


# In-memory store (would be database in production)
_plots: dict[str, dict] = {}
_events: dict[str, dict] = {}


def _init_demo_data():
    """Initialize demo data if empty."""
    if _plots:
        return
    
    # Demo plots
    demo_plots = [
        {
            "id": "plot-001",
            "name": "A-001",
            "field_id": "field-a",
            "field_name": "Block A",
            "current_crop": "Rice - BIJ-R-001",
            "germplasm_id": "germ-001",
            "planting_date": "2025-06-15",
            "expected_harvest": "2025-10-15",
            "area_sqm": 100,
            "row": 1,
            "column": 1,
            "status": "active",
            "created_at": "2025-06-15T08:00:00Z",
        },
        {
            "id": "plot-002",
            "name": "A-002",
            "field_id": "field-a",
            "field_name": "Block A",
            "current_crop": "Rice - BIJ-R-002",
            "germplasm_id": "germ-002",
            "planting_date": "2025-06-15",
            "expected_harvest": "2025-10-20",
            "area_sqm": 100,
            "row": 1,
            "column": 2,
            "status": "active",
            "created_at": "2025-06-15T08:00:00Z",
        },
        {
            "id": "plot-003",
            "name": "A-003",
            "field_id": "field-a",
            "field_name": "Block A",
            "current_crop": "Rice - BIJ-R-003",
            "germplasm_id": "germ-003",
            "planting_date": "2025-06-16",
            "expected_harvest": "2025-10-18",
            "area_sqm": 100,
            "row": 1,
            "column": 3,
            "status": "active",
            "created_at": "2025-06-16T08:00:00Z",
        },
        {
            "id": "plot-004",
            "name": "B-001",
            "field_id": "field-b",
            "field_name": "Block B",
            "current_crop": "Wheat - BIJ-W-001",
            "germplasm_id": "germ-004",
            "planting_date": "2025-11-01",
            "expected_harvest": "2026-03-15",
            "area_sqm": 150,
            "row": 1,
            "column": 1,
            "status": "active",
            "created_at": "2025-11-01T08:00:00Z",
        },
        {
            "id": "plot-005",
            "name": "B-002",
            "field_id": "field-b",
            "field_name": "Block B",
            "current_crop": "Wheat - BIJ-W-002",
            "germplasm_id": "germ-005",
            "planting_date": "2025-11-01",
            "expected_harvest": "2026-03-20",
            "area_sqm": 150,
            "row": 1,
            "column": 2,
            "status": "active",
            "created_at": "2025-11-01T08:00:00Z",
        },
    ]
    
    for plot in demo_plots:
        _plots[plot["id"]] = plot
    
    # Demo events
    demo_events = [
        # Plot A-001 events
        {"id": "evt-001", "plot_id": "plot-001", "date": "2025-06-15", "type": "planting", "description": "Transplanted BIJ-R-001", "value": None, "notes": "Good soil moisture", "recorded_by": "Field Tech 1"},
        {"id": "evt-002", "plot_id": "plot-001", "date": "2025-07-01", "type": "observation", "description": "Plant height measurement", "value": "45 cm", "notes": "Healthy growth", "recorded_by": "Field Tech 1"},
        {"id": "evt-003", "plot_id": "plot-001", "date": "2025-07-15", "type": "treatment", "description": "Fertilizer application - NPK 15-15-15", "value": "50 kg/ha", "notes": "Basal dose", "recorded_by": "Field Tech 2"},
        {"id": "evt-004", "plot_id": "plot-001", "date": "2025-08-01", "type": "observation", "description": "Tiller count", "value": "12 tillers/plant", "notes": "Above average", "recorded_by": "Field Tech 1"},
        {"id": "evt-005", "plot_id": "plot-001", "date": "2025-08-15", "type": "treatment", "description": "Pest control - Stem borer", "value": "Chlorantraniliprole", "notes": "Preventive spray", "recorded_by": "Field Tech 2"},
        {"id": "evt-006", "plot_id": "plot-001", "date": "2025-09-01", "type": "observation", "description": "Flowering stage", "value": "50% flowering", "notes": "On schedule", "recorded_by": "Field Tech 1"},
        # Plot A-002 events
        {"id": "evt-007", "plot_id": "plot-002", "date": "2025-06-15", "type": "planting", "description": "Transplanted BIJ-R-002", "value": None, "notes": None, "recorded_by": "Field Tech 1"},
        {"id": "evt-008", "plot_id": "plot-002", "date": "2025-07-01", "type": "observation", "description": "Plant height measurement", "value": "42 cm", "notes": None, "recorded_by": "Field Tech 1"},
        {"id": "evt-009", "plot_id": "plot-002", "date": "2025-07-20", "type": "treatment", "description": "Weed control", "value": "Manual weeding", "notes": None, "recorded_by": "Field Tech 3"},
        # Plot A-003 events
        {"id": "evt-010", "plot_id": "plot-003", "date": "2025-06-16", "type": "planting", "description": "Transplanted BIJ-R-003", "value": None, "notes": None, "recorded_by": "Field Tech 1"},
        {"id": "evt-011", "plot_id": "plot-003", "date": "2025-07-02", "type": "observation", "description": "Plant height measurement", "value": "40 cm", "notes": "Slightly delayed", "recorded_by": "Field Tech 1"},
        # Plot B-001 events
        {"id": "evt-012", "plot_id": "plot-004", "date": "2025-11-01", "type": "planting", "description": "Sown BIJ-W-001", "value": "100 kg/ha seed rate", "notes": "Good germination expected", "recorded_by": "Field Tech 2"},
        {"id": "evt-013", "plot_id": "plot-004", "date": "2025-11-15", "type": "observation", "description": "Germination count", "value": "92%", "notes": "Excellent", "recorded_by": "Field Tech 2"},
        {"id": "evt-014", "plot_id": "plot-004", "date": "2025-12-01", "type": "treatment", "description": "First irrigation", "value": "50mm", "notes": None, "recorded_by": "Field Tech 3"},
    ]
    
    for event in demo_events:
        event["created_at"] = datetime.now().isoformat()
        _events[event["id"]] = event


class PlotHistoryService:
    """Service for managing plot history and events."""
    
    def __init__(self):
        _init_demo_data()
    
    def get_plots(
        self,
        field_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get plots with optional filters."""
        plots = list(_plots.values())
        
        if field_id:
            plots = [p for p in plots if p["field_id"] == field_id]
        
        if status:
            plots = [p for p in plots if p["status"] == status]
        
        if search:
            search_lower = search.lower()
            plots = [p for p in plots if 
                     search_lower in p["name"].lower() or 
                     search_lower in p.get("current_crop", "").lower() or
                     search_lower in p.get("field_name", "").lower()]
        
        # Add event count to each plot
        for plot in plots:
            plot["event_count"] = len([e for e in _events.values() if e["plot_id"] == plot["id"]])
        
        total = len(plots)
        plots = plots[offset:offset + limit]
        
        return {"plots": plots, "total": total}
    
    def get_plot(self, plot_id: str) -> Optional[dict]:
        """Get a single plot with its events."""
        plot = _plots.get(plot_id)
        if not plot:
            return None
        
        # Get events for this plot
        events = [e for e in _events.values() if e["plot_id"] == plot_id]
        events.sort(key=lambda x: x["date"], reverse=True)
        
        return {**plot, "events": events, "event_count": len(events)}
    
    def get_plot_events(
        self,
        plot_id: str,
        event_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Get events for a specific plot."""
        events = [e for e in _events.values() if e["plot_id"] == plot_id]
        
        if event_type:
            events = [e for e in events if e["type"] == event_type]
        
        if start_date:
            events = [e for e in events if e["date"] >= start_date]
        
        if end_date:
            events = [e for e in events if e["date"] <= end_date]
        
        events.sort(key=lambda x: x["date"], reverse=True)
        
        return {"events": events, "total": len(events)}
    
    def create_event(self, plot_id: str, data: dict) -> Optional[dict]:
        """Create a new event for a plot."""
        if plot_id not in _plots:
            return None
        
        event_id = f"evt-{uuid.uuid4().hex[:8]}"
        event = {
            "id": event_id,
            "plot_id": plot_id,
            "date": data.get("date", date.today().isoformat()),
            "type": data["type"],
            "description": data["description"],
            "value": data.get("value"),
            "notes": data.get("notes"),
            "recorded_by": data.get("recorded_by", "System"),
            "created_at": datetime.now().isoformat(),
        }
        
        _events[event_id] = event
        return event
    
    def update_event(self, event_id: str, data: dict) -> Optional[dict]:
        """Update an existing event."""
        if event_id not in _events:
            return None
        
        event = _events[event_id]
        for key in ["date", "type", "description", "value", "notes"]:
            if key in data and data[key] is not None:
                event[key] = data[key]
        
        event["updated_at"] = datetime.now().isoformat()
        return event
    
    def delete_event(self, event_id: str) -> bool:
        """Delete an event."""
        if event_id in _events:
            del _events[event_id]
            return True
        return False
    
    def get_stats(self, field_id: Optional[str] = None) -> dict:
        """Get plot history statistics."""
        plots = list(_plots.values())
        events = list(_events.values())
        
        if field_id:
            plot_ids = {p["id"] for p in plots if p["field_id"] == field_id}
            plots = [p for p in plots if p["field_id"] == field_id]
            events = [e for e in events if e["plot_id"] in plot_ids]
        
        # Count by event type
        by_type = {}
        for event in events:
            event_type = event["type"]
            by_type[event_type] = by_type.get(event_type, 0) + 1
        
        # Count by field
        by_field = {}
        for plot in _plots.values():
            field = plot["field_name"]
            by_field[field] = by_field.get(field, 0) + 1
        
        # Recent events (last 7 days)
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        recent_events = len([e for e in events if e["date"] >= week_ago])
        
        return {
            "total_plots": len(plots),
            "total_events": len(events),
            "recent_events": recent_events,
            "by_event_type": by_type,
            "by_field": by_field,
            "active_plots": len([p for p in plots if p["status"] == "active"]),
        }
    
    def get_event_types(self) -> list:
        """Get available event types."""
        return [
            {"id": "planting", "name": "Planting", "description": "Sowing or transplanting", "color": "green"},
            {"id": "observation", "name": "Observation", "description": "Data collection", "color": "blue"},
            {"id": "treatment", "name": "Treatment", "description": "Fertilizer, pesticide, irrigation", "color": "orange"},
            {"id": "harvest", "name": "Harvest", "description": "Crop harvest", "color": "purple"},
            {"id": "maintenance", "name": "Maintenance", "description": "Field maintenance", "color": "gray"},
            {"id": "sampling", "name": "Sampling", "description": "Sample collection", "color": "cyan"},
        ]
    
    def get_fields(self) -> list:
        """Get unique fields from plots."""
        fields = {}
        for plot in _plots.values():
            field_id = plot["field_id"]
            if field_id not in fields:
                fields[field_id] = {
                    "id": field_id,
                    "name": plot["field_name"],
                    "plot_count": 0,
                }
            fields[field_id]["plot_count"] += 1
        
        return list(fields.values())


# Singleton instance
plot_history_service = PlotHistoryService()

"""
Field Map Service
Manages field blocks, plots, and spatial data for breeding operations
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import uuid


class FieldStatus(str, Enum):
    ACTIVE = "active"
    FALLOW = "fallow"
    HARVESTED = "harvested"
    PREPARATION = "preparation"


class PlotStatus(str, Enum):
    AVAILABLE = "available"
    PLANTED = "planted"
    GROWING = "growing"
    HARVESTED = "harvested"
    FALLOW = "fallow"


@dataclass
class Field:
    """Field/Block definition"""
    id: str
    name: str
    location: str
    station: str
    area_hectares: float
    total_plots: int
    status: FieldStatus
    coordinates: Optional[Dict[str, float]] = None  # lat, lng
    boundary: Optional[List[Dict[str, float]]] = None  # polygon coordinates
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "station": self.station,
            "area": self.area_hectares,
            "plots": self.total_plots,
            "status": self.status.value,
            "coordinates": self.coordinates,
            "boundary": self.boundary,
            "soilType": self.soil_type,
            "irrigationType": self.irrigation_type,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass
class Plot:
    """Individual plot within a field"""
    id: str
    field_id: str
    plot_number: int
    row: int
    column: int
    status: PlotStatus
    trial_id: Optional[str] = None
    germplasm_id: Optional[str] = None
    germplasm_name: Optional[str] = None
    planted_date: Optional[date] = None
    harvested_date: Optional[date] = None
    coordinates: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "fieldId": self.field_id,
            "plotNumber": self.plot_number,
            "row": self.row,
            "column": self.column,
            "status": self.status.value,
            "trialId": self.trial_id,
            "germplasmId": self.germplasm_id,
            "germplasmName": self.germplasm_name,
            "plantedDate": self.planted_date.isoformat() if self.planted_date else None,
            "harvestedDate": self.harvested_date.isoformat() if self.harvested_date else None,
            "coordinates": self.coordinates,
        }


class FieldMapService:
    """Service for managing field maps and plots"""
    
    def __init__(self):
        self._fields: Dict[str, Field] = {}
        self._plots: Dict[str, List[Plot]] = {}  # field_id -> plots
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize demo fields and plots"""
        demo_fields = [
            Field(
                id="FLD-001",
                name="Block A",
                location="Research Station 1",
                station="Station 1",
                area_hectares=2.5,
                total_plots=150,
                status=FieldStatus.ACTIVE,
                coordinates={"lat": 17.3850, "lng": 78.4867},
                soil_type="Clay loam",
                irrigation_type="Drip",
            ),
            Field(
                id="FLD-002",
                name="Block B",
                location="Research Station 1",
                station="Station 1",
                area_hectares=3.0,
                total_plots=180,
                status=FieldStatus.ACTIVE,
                coordinates={"lat": 17.3860, "lng": 78.4877},
                soil_type="Sandy loam",
                irrigation_type="Sprinkler",
            ),
            Field(
                id="FLD-003",
                name="Block C",
                location="Research Station 2",
                station="Station 2",
                area_hectares=1.8,
                total_plots=100,
                status=FieldStatus.HARVESTED,
                coordinates={"lat": 17.4000, "lng": 78.5000},
                soil_type="Red soil",
                irrigation_type="Flood",
            ),
            Field(
                id="FLD-004",
                name="Nursery",
                location="Research Station 1",
                station="Station 1",
                area_hectares=0.5,
                total_plots=50,
                status=FieldStatus.ACTIVE,
                coordinates={"lat": 17.3840, "lng": 78.4857},
                soil_type="Potting mix",
                irrigation_type="Manual",
            ),
            Field(
                id="FLD-005",
                name="Block D",
                location="Research Station 2",
                station="Station 2",
                area_hectares=2.0,
                total_plots=120,
                status=FieldStatus.PREPARATION,
                coordinates={"lat": 17.4010, "lng": 78.5010},
                soil_type="Black soil",
                irrigation_type="Drip",
            ),
        ]
        
        for f in demo_fields:
            self._fields[f.id] = f
            self._plots[f.id] = self._generate_plots(f)
    
    def _generate_plots(self, field: Field) -> List[Plot]:
        """Generate plots for a field in a grid pattern"""
        plots = []
        rows = int((field.total_plots ** 0.5) * 1.2)  # Slightly more rows than columns
        cols = (field.total_plots + rows - 1) // rows
        
        plot_num = 1
        for r in range(1, rows + 1):
            for c in range(1, cols + 1):
                if plot_num > field.total_plots:
                    break
                
                # Assign some plots to trials with germplasm
                status = PlotStatus.AVAILABLE
                trial_id = None
                germplasm_id = None
                germplasm_name = None
                
                if field.status == FieldStatus.ACTIVE and plot_num <= field.total_plots * 0.7:
                    status = PlotStatus.GROWING
                    trial_id = f"TRL-{(plot_num % 3) + 1:03d}"
                    germplasm_id = f"GRM-{(plot_num % 10) + 1:03d}"
                    germplasm_name = f"Entry-{(plot_num % 10) + 1}"
                elif field.status == FieldStatus.HARVESTED:
                    status = PlotStatus.HARVESTED
                
                plots.append(Plot(
                    id=f"{field.id}-P{plot_num:03d}",
                    field_id=field.id,
                    plot_number=plot_num,
                    row=r,
                    column=c,
                    status=status,
                    trial_id=trial_id,
                    germplasm_id=germplasm_id,
                    germplasm_name=germplasm_name,
                ))
                plot_num += 1
        
        return plots
    
    # Field CRUD
    def list_fields(
        self,
        station: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all fields with optional filters"""
        fields = list(self._fields.values())
        
        if station:
            fields = [f for f in fields if f.station.lower() == station.lower()]
        
        if status:
            fields = [f for f in fields if f.status.value == status]
        
        if search:
            search_lower = search.lower()
            fields = [f for f in fields if search_lower in f.name.lower() or search_lower in f.location.lower()]
        
        return [f.to_dict() for f in fields]
    
    def get_field(self, field_id: str) -> Optional[Dict[str, Any]]:
        """Get field by ID"""
        field = self._fields.get(field_id)
        return field.to_dict() if field else None
    
    def create_field(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new field"""
        field_id = f"FLD-{uuid.uuid4().hex[:6].upper()}"
        
        field = Field(
            id=field_id,
            name=data["name"],
            location=data["location"],
            station=data.get("station", data["location"]),
            area_hectares=data["area"],
            total_plots=data["plots"],
            status=FieldStatus(data.get("status", "preparation")),
            coordinates=data.get("coordinates"),
            boundary=data.get("boundary"),
            soil_type=data.get("soilType"),
            irrigation_type=data.get("irrigationType"),
        )
        
        self._fields[field_id] = field
        self._plots[field_id] = self._generate_plots(field)
        
        return field.to_dict()
    
    def update_field(self, field_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a field"""
        field = self._fields.get(field_id)
        if not field:
            return None
        
        if "name" in data:
            field.name = data["name"]
        if "location" in data:
            field.location = data["location"]
        if "station" in data:
            field.station = data["station"]
        if "area" in data:
            field.area_hectares = data["area"]
        if "status" in data:
            field.status = FieldStatus(data["status"])
        if "coordinates" in data:
            field.coordinates = data["coordinates"]
        if "soilType" in data:
            field.soil_type = data["soilType"]
        if "irrigationType" in data:
            field.irrigation_type = data["irrigationType"]
        
        field.updated_at = datetime.now()
        return field.to_dict()
    
    def delete_field(self, field_id: str) -> bool:
        """Delete a field"""
        if field_id in self._fields:
            del self._fields[field_id]
            if field_id in self._plots:
                del self._plots[field_id]
            return True
        return False
    
    # Plot operations
    def get_plots(
        self,
        field_id: str,
        status: Optional[str] = None,
        trial_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get plots for a field"""
        plots = self._plots.get(field_id, [])
        
        if status:
            plots = [p for p in plots if p.status.value == status]
        
        if trial_id:
            plots = [p for p in plots if p.trial_id == trial_id]
        
        return [p.to_dict() for p in plots]
    
    def get_plot(self, field_id: str, plot_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific plot"""
        plots = self._plots.get(field_id, [])
        for plot in plots:
            if plot.id == plot_id:
                return plot.to_dict()
        return None
    
    def update_plot(self, field_id: str, plot_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a plot"""
        plots = self._plots.get(field_id, [])
        for plot in plots:
            if plot.id == plot_id:
                if "status" in data:
                    plot.status = PlotStatus(data["status"])
                if "trialId" in data:
                    plot.trial_id = data["trialId"]
                if "germplasmId" in data:
                    plot.germplasm_id = data["germplasmId"]
                if "germplasmName" in data:
                    plot.germplasm_name = data["germplasmName"]
                if "plantedDate" in data:
                    plot.planted_date = date.fromisoformat(data["plantedDate"]) if data["plantedDate"] else None
                if "harvestedDate" in data:
                    plot.harvested_date = date.fromisoformat(data["harvestedDate"]) if data["harvestedDate"] else None
                return plot.to_dict()
        return None
    
    # Summary and statistics
    def get_summary(self) -> Dict[str, Any]:
        """Get field map summary statistics"""
        fields = list(self._fields.values())
        
        total_area = sum(f.area_hectares for f in fields)
        total_plots = sum(f.total_plots for f in fields)
        
        status_counts = {}
        for f in fields:
            status_counts[f.status.value] = status_counts.get(f.status.value, 0) + 1
        
        stations = list(set(f.station for f in fields))
        
        # Count plot statuses across all fields
        plot_status_counts = {}
        for field_id, plots in self._plots.items():
            for plot in plots:
                plot_status_counts[plot.status.value] = plot_status_counts.get(plot.status.value, 0) + 1
        
        return {
            "totalFields": len(fields),
            "totalArea": round(total_area, 2),
            "totalPlots": total_plots,
            "fieldsByStatus": status_counts,
            "plotsByStatus": plot_status_counts,
            "stations": stations,
            "activeFields": status_counts.get("active", 0),
        }
    
    def get_stations(self) -> List[str]:
        """Get list of unique stations"""
        return list(set(f.station for f in self._fields.values()))
    
    def get_field_statuses(self) -> List[str]:
        """Get list of field statuses"""
        return [s.value for s in FieldStatus]
    
    def get_plot_statuses(self) -> List[str]:
        """Get list of plot statuses"""
        return [s.value for s in PlotStatus]


# Singleton instance
_field_map_service: Optional[FieldMapService] = None


def get_field_map_service() -> FieldMapService:
    """Get or create field map service singleton"""
    global _field_map_service
    if _field_map_service is None:
        _field_map_service = FieldMapService()
    return _field_map_service

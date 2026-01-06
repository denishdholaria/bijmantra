"""
Field Map API
Endpoints for field and plot management
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from ...services.field_map import get_field_map_service


router = APIRouter(prefix="/field-map", tags=["Field Map"])


# Request/Response Models
class FieldCreate(BaseModel):
    name: str
    location: str
    station: Optional[str] = None
    area: float
    plots: int
    status: Optional[str] = "preparation"
    coordinates: Optional[Dict[str, float]] = None
    boundary: Optional[List[Dict[str, float]]] = None
    soilType: Optional[str] = None
    irrigationType: Optional[str] = None


class FieldUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    station: Optional[str] = None
    area: Optional[float] = None
    status: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    soilType: Optional[str] = None
    irrigationType: Optional[str] = None


class PlotUpdate(BaseModel):
    status: Optional[str] = None
    trialId: Optional[str] = None
    germplasmId: Optional[str] = None
    germplasmName: Optional[str] = None
    plantedDate: Optional[str] = None
    harvestedDate: Optional[str] = None


# Field endpoints
@router.get("")
async def list_fields(
    station: Optional[str] = Query(None, description="Filter by station"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name or location"),
):
    """List all fields with optional filters"""
    service = get_field_map_service()
    return service.list_fields(station=station, status=status, search=search)


@router.get("/summary")
async def get_summary():
    """Get field map summary statistics"""
    service = get_field_map_service()
    return service.get_summary()


@router.get("/stations")
async def get_stations():
    """Get list of unique stations"""
    service = get_field_map_service()
    return service.get_stations()


@router.get("/statuses")
async def get_field_statuses():
    """Get list of field statuses"""
    service = get_field_map_service()
    return {"fieldStatuses": service.get_field_statuses(), "plotStatuses": service.get_plot_statuses()}


@router.post("")
async def create_field(data: FieldCreate):
    """Create a new field"""
    service = get_field_map_service()
    return service.create_field(data.model_dump())


@router.get("/{field_id}")
async def get_field(field_id: str):
    """Get field by ID"""
    service = get_field_map_service()
    field = service.get_field(field_id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.put("/{field_id}")
async def update_field(field_id: str, data: FieldUpdate):
    """Update a field"""
    service = get_field_map_service()
    field = service.update_field(field_id, data.model_dump(exclude_none=True))
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.delete("/{field_id}")
async def delete_field(field_id: str):
    """Delete a field"""
    service = get_field_map_service()
    if not service.delete_field(field_id):
        raise HTTPException(status_code=404, detail="Field not found")
    return {"message": "Field deleted successfully"}


# Plot endpoints
@router.get("/{field_id}/plots")
async def get_plots(
    field_id: str,
    status: Optional[str] = Query(None, description="Filter by plot status"),
    trial_id: Optional[str] = Query(None, description="Filter by trial ID"),
):
    """Get plots for a field"""
    service = get_field_map_service()
    return service.get_plots(field_id, status=status, trial_id=trial_id)


@router.get("/{field_id}/plots/{plot_id}")
async def get_plot(field_id: str, plot_id: str):
    """Get a specific plot"""
    service = get_field_map_service()
    plot = service.get_plot(field_id, plot_id)
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    return plot


@router.put("/{field_id}/plots/{plot_id}")
async def update_plot(field_id: str, plot_id: str, data: PlotUpdate):
    """Update a plot"""
    service = get_field_map_service()
    plot = service.update_plot(field_id, plot_id, data.model_dump(exclude_none=True))
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    return plot

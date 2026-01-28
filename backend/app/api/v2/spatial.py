"""
Spatial Analysis API
GIS and spatial analysis for field trials
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.spatial_analysis import spatial_analysis_service

router = APIRouter(prefix="/spatial", tags=["Spatial Analysis"])


class FieldCreate(BaseModel):
    name: str
    location: str
    latitude: float
    longitude: float
    area_ha: float
    rows: int
    columns: int
    plot_size_m2: float
    soil_type: Optional[str] = None
    irrigation: Optional[str] = None


class PlotCoordinatesRequest(BaseModel):
    plot_width_m: float
    plot_length_m: float
    alley_width_m: float = 0.5
    border_m: float = 2.0


class DistanceRequest(BaseModel):
    lat1: float
    lon1: float
    lat2: float
    lon2: float


class SpatialAutocorrelationRequest(BaseModel):
    values: List[Dict[str, Any]]
    x_key: str = "x"
    y_key: str = "y"
    value_key: str = "value"
    max_distance: Optional[float] = None


class MovingAverageRequest(BaseModel):
    values: List[Dict[str, Any]]
    row_key: str = "row"
    col_key: str = "column"
    value_key: str = "value"
    window_size: int = 3


class NearestNeighborRequest(BaseModel):
    points: List[Dict[str, float]]
    x_key: str = "x"
    y_key: str = "y"
    area: Optional[float] = None


class RowColumnTrendRequest(BaseModel):
    values: List[Dict[str, Any]]
    row_key: str = "row"
    col_key: str = "column"
    value_key: str = "value"


@router.post("/fields")
async def create_field(data: FieldCreate):
    """Create a new field for spatial analysis"""
    field = spatial_analysis_service.create_field(**data.model_dump())
    return {"status": "success", "data": field}


@router.get("/fields")
async def list_fields():
    """List all fields"""
    fields = spatial_analysis_service.list_fields()
    return {"status": "success", "data": fields, "count": len(fields)}


@router.get("/fields/{field_id}")
async def get_field(field_id: str):
    """Get field details"""
    field = spatial_analysis_service.get_field(field_id)
    if not field:
        raise HTTPException(status_code=404, detail=f"Field {field_id} not found")
    return {"status": "success", "data": field}


@router.post("/fields/{field_id}/plots")
async def generate_plot_coordinates(field_id: str, data: PlotCoordinatesRequest):
    """Generate plot coordinates for a field"""
    try:
        plots = spatial_analysis_service.generate_plot_coordinates(
            field_id=field_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": plots, "count": len(plots)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/fields/{field_id}/plots")
async def get_plots(field_id: str):
    """Get all plots for a field"""
    plots = spatial_analysis_service.get_plots(field_id)
    return {"status": "success", "data": plots, "count": len(plots)}


@router.post("/calculate/distance")
async def calculate_distance(data: DistanceRequest):
    """Calculate distance between two GPS coordinates"""
    distance = spatial_analysis_service.calculate_distance(
        lat1=data.lat1,
        lon1=data.lon1,
        lat2=data.lat2,
        lon2=data.lon2,
    )
    return {
        "status": "success",
        "data": {
            "distance_m": round(distance, 2),
            "distance_km": round(distance / 1000, 4),
        },
    }


@router.post("/analyze/autocorrelation")
async def spatial_autocorrelation(data: SpatialAutocorrelationRequest):
    """Calculate Moran's I spatial autocorrelation"""
    result = spatial_analysis_service.spatial_autocorrelation(
        values=data.values,
        x_key=data.x_key,
        y_key=data.y_key,
        value_key=data.value_key,
        max_distance=data.max_distance,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.post("/analyze/moving-average")
async def moving_average_adjustment(data: MovingAverageRequest):
    """Apply moving average spatial adjustment"""
    result = spatial_analysis_service.moving_average_adjustment(
        values=data.values,
        row_key=data.row_key,
        col_key=data.col_key,
        value_key=data.value_key,
        window_size=data.window_size,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.post("/analyze/nearest-neighbor")
async def nearest_neighbor_analysis(data: NearestNeighborRequest):
    """Nearest neighbor analysis for point pattern"""
    result = spatial_analysis_service.nearest_neighbor_analysis(
        points=data.points,
        x_key=data.x_key,
        y_key=data.y_key,
        area=data.area,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.post("/analyze/row-column-trend")
async def row_column_trend(data: RowColumnTrendRequest):
    """Analyze row and column trends in field data"""
    result = spatial_analysis_service.row_column_trend(
        values=data.values,
        row_key=data.row_key,
        col_key=data.col_key,
        value_key=data.value_key,
    )
    return {"status": "success", "data": result}


@router.get("/statistics")
async def get_statistics():
    """Get spatial analysis statistics"""
    stats = spatial_analysis_service.get_statistics()
    return {"status": "success", "data": stats}

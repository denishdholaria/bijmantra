from typing import List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.services.spatial import spatial_service
from app.models.spatial import GISLayer
from pydantic import BaseModel

router = APIRouter()

class PointQueryRequest(BaseModel):
    layer_id: int
    latitude: float
    longitude: float

class ZonalStatsRequest(BaseModel):
    layer_id: int
    polygon_geojson: Dict

@router.post("/query-point", response_model=Dict)
async def query_point(
    request: PointQueryRequest,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Extract value from a GIS layer at a specific point.
    """
    layer = await db.get(GISLayer, request.layer_id)
    if not layer:
        raise HTTPException(status_code=404, detail="GIS Layer not found")

    val = spatial_service.extract_point_value(
        layer.source_path,
        request.longitude,
        request.latitude
    )

    return {"value": val, "unit": "index"}

@router.post("/zonal-stats", response_model=Dict)
async def query_zonal_stats(
    request: ZonalStatsRequest,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Calculate statistics for a polygon over a raster layer.
    """
    layer = await db.get(GISLayer, request.layer_id)
    if not layer:
        raise HTTPException(status_code=404, detail="GIS Layer not found")

    stats = spatial_service.zonal_statistics(
        layer.source_path,
        request.polygon_geojson
    )

    return stats

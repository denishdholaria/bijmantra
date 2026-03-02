import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.spatial import GISLayer
from app.services.spatial import spatial_service


router = APIRouter()

class PointQueryRequest(BaseModel):
    layer_id: int
    latitude: float
    longitude: float

class ZonalStatsRequest(BaseModel):
    layer_id: int
    polygon_geojson: dict

@router.post("/query-point", response_model=dict)
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

    loop = asyncio.get_running_loop()
    val = await loop.run_in_executor(
        None,
        spatial_service.extract_point_value,
        layer.source_path,
        request.longitude,
        request.latitude
    )

    return {"value": val, "unit": "index"}

@router.post("/zonal-stats", response_model=dict)
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

    loop = asyncio.get_running_loop()
    stats = await loop.run_in_executor(
        None,
        spatial_service.zonal_statistics,
        layer.source_path,
        request.polygon_geojson
    )

    return stats

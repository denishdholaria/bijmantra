"""
Spatial Analysis Service
GIS Operations: Point Query, Zonal Statistics
"""

import os
from typing import List, Dict, Optional, Tuple, Union
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shapely.geometry import shape, Point, Polygon
import rasterio
from rasterio.mask import mask

from app.models.spatial import GISLayer, RemoteSensingData
from app.models.core import Location

class SpatialService:
    """
    Service for geospatial analysis.
    Requires GDAL/Rasterio.
    """

    def extract_point_value(
        self,
        raster_path: str,
        lon: float,
        lat: float
    ) -> Optional[float]:
        """
        Extract value from a raster at a specific longitude/latitude.
        """
        if not os.path.exists(raster_path):
            raise FileNotFoundError(f"Raster file not found: {raster_path}")

        try:
            with rasterio.open(raster_path) as src:
                # Convert lon/lat to raster CRS coordinates if needed (simplified assuming same CRS)
                # Ideally, reprojection logic should be here.

                # Sample the raster at the point
                # index() returns row, col for x, y
                row, col = src.index(lon, lat)

                # Check bounds
                if row < 0 or row >= src.height or col < 0 or col >= src.width:
                    return None

                # Read value
                value = src.read(1)[row, col]

                # Handle NoData
                if value == src.nodata:
                    return None

                return float(value)
        except Exception as e:
            print(f"Error extracting point value: {e}")
            return None

    def zonal_statistics(
        self,
        raster_path: str,
        polygon_geojson: Dict
    ) -> Dict[str, float]:
        """
        Calculate statistics (min, max, mean) for a raster within a polygon.
        """
        if not os.path.exists(raster_path):
            raise FileNotFoundError(f"Raster file not found: {raster_path}")

        try:
            with rasterio.open(raster_path) as src:
                shapes = [polygon_geojson]

                # Mask the raster with the polygon
                out_image, out_transform = mask(src, shapes, crop=True)

                # Flatten and remove NoData values
                data = out_image[0] # Band 1
                if src.nodata is not None:
                    data = data[data != src.nodata]
                else:
                    data = data.flatten()

                if data.size == 0:
                    return {"mean": None, "max": None, "min": None, "std": None}

                return {
                    "mean": float(np.mean(data)),
                    "max": float(np.max(data)),
                    "min": float(np.min(data)),
                    "std": float(np.std(data)),
                    "count": int(data.size)
                }
        except Exception as e:
            print(f"Error calculating zonal stats: {e}")
            return {"error": str(e)}

    async def get_remote_sensing_data(
        self,
        db: AsyncSession,
        location_id: int,
        metric_name: str
    ) -> List[RemoteSensingData]:
        """
        Retrieve historical remote sensing data for a location.
        """
        stmt = select(RemoteSensingData).where(
            RemoteSensingData.location_id == location_id,
            RemoteSensingData.metric_name == metric_name
        ).order_by(RemoteSensingData.acquisition_date.desc())

        result = await db.execute(stmt)
        return result.scalars().all()

# Global instance
spatial_service = SpatialService()

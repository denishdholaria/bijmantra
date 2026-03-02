"""
Google Earth Engine NDVI Raster Fetcher

Provides functionality to fetch NDVI raster data from Google Earth Engine.
Focuses on retrieving download URLs for processed NDVI images.
"""

import logging
import os
from typing import Any

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class NDVIRasterRequest(BaseModel):
    """Request model for fetching NDVI raster."""

    geometry: dict[str, Any] = Field(..., description="GeoJSON geometry dictionary (Polygon or MultiPolygon)")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    scale: int = Field(10, description="Scale in meters (resolution)")
    crs: str = Field("EPSG:4326", description="Coordinate Reference System")
    cloud_cover_threshold: float = Field(20.0, description="Maximum cloud cover percentage")


class NDVIRasterResponse(BaseModel):
    """Response model containing the download URL."""

    url: str = Field(..., description="Download URL for the GeoTIFF")
    start_date: str
    end_date: str
    scale: int
    crs: str


class GEENDVIRasterFetcher:
    """
    Fetcher for NDVI raster data from Google Earth Engine.
    """

    def __init__(self):
        """Initialize the fetcher."""
        self._authenticated = False
        self._ee = None

    def authenticate(self) -> bool:
        """
        Authenticate with Google Earth Engine using service account credentials.

        Returns:
            bool: True if authentication successful, False otherwise.
        """
        if self._authenticated:
            return True

        try:
            import ee
            self._ee = ee

            service_account = os.getenv('GEE_SERVICE_ACCOUNT_EMAIL')
            key_file = os.getenv('GEE_PRIVATE_KEY_PATH')

            if not service_account or not key_file:
                logger.warning(
                    "GEE credentials not found. Set GEE_SERVICE_ACCOUNT_EMAIL "
                    "and GEE_PRIVATE_KEY_PATH environment variables."
                )
                return False

            credentials = ee.ServiceAccountCredentials(
                email=service_account,
                key_file=key_file
            )
            ee.Initialize(credentials)

            self._authenticated = True
            logger.info("Successfully authenticated with Google Earth Engine")
            return True

        except ImportError:
            logger.error("earthengine-api not installed.")
            return False
        except Exception as e:
            logger.error(f"GEE authentication failed: {str(e)}")
            return False

    def fetch_raster_url(self, request: NDVIRasterRequest) -> NDVIRasterResponse | None:
        """
        Fetch the download URL for an NDVI raster based on the request.

        Args:
            request: NDVIRasterRequest object containing parameters.

        Returns:
            NDVIRasterResponse object with the URL, or None if failed.
        """
        if not self.authenticate():
            return None

        try:
            ee = self._ee

            # Parse geometry
            geom = ee.Geometry(request.geometry)

            # Define date range
            start = request.start_date
            end = request.end_date

            # Load Sentinel-2 collection
            collection = (
                ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(geom)
                .filterDate(start, end)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', request.cloud_cover_threshold))
            )

            # Check if collection is empty
            if collection.size().getInfo() == 0:
                logger.warning(f"No images found for date range {start} to {end}")
                return None

            # Function to calculate NDVI
            def add_ndvi(image):
                ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
                return image.addBands(ndvi)

            # Map NDVI and select it
            ndvi_collection = collection.map(add_ndvi).select('NDVI')

            # Create a composite (median)
            # using median reduces cloud artifacts and transient noise
            composite = ndvi_collection.median()

            # Clip to geometry
            clipped_composite = composite.clip(geom)

            # Get download URL
            url = clipped_composite.getDownloadURL({
                'scale': request.scale,
                'crs': request.crs,
                'region': geom,
                'format': 'GEO_TIFF'
            })

            return NDVIRasterResponse(
                url=url,
                start_date=start,
                end_date=end,
                scale=request.scale,
                crs=request.crs
            )

        except Exception as e:
            logger.error(f"Error fetching NDVI raster URL: {str(e)}")
            return None

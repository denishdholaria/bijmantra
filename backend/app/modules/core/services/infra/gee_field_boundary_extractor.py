"""
GEE Field Boundary Extractor

Extracts agricultural field boundaries from satellite imagery using
Google Earth Engine's segmentation algorithms (SNIC).
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from app.modules.environment.services.gee_integration_service import get_gee_service

logger = logging.getLogger(__name__)


class GEEFieldBoundaryExtractor:
    """
    Service for extracting field boundaries from satellite imagery.
    Uses Sentinel-2 data and SNIC segmentation.
    """

    def __init__(self):
        """Initialize the extractor."""
        self.gee_service = get_gee_service()

    async def extract_boundaries(
        self,
        latitude: float,
        longitude: float,
        date: datetime,
        buffer_meters: int = 1000
    ) -> dict[str, Any] | None:
        """
        Extract field boundaries around a coordinate.

        Algorithm:
        1. Fetch best cloud-free Sentinel-2 image near date.
        2. Apply SNIC (Simple Non-Iterative Clustering) segmentation.
        3. Vectorize segments to polygons.
        4. Return as GeoJSON FeatureCollection.

        Args:
            latitude: Latitude of center point.
            longitude: Longitude of center point.
            date: Target date for imagery.
            buffer_meters: Radius to search/extract (default 1000m).

        Returns:
            dict: GeoJSON FeatureCollection of field boundaries.
            None if extraction fails.
        """
        # Ensure authenticated
        if not await self.gee_service.authenticate():
            logger.error("GEE authentication failed")
            return None

        try:
            import ee

            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(buffer_meters)

            # Get Sentinel-2 image collection
            # Look for images within 1 month window
            start_date = (date - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = (date + timedelta(days=30)).strftime('%Y-%m-%d')

            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                         .filterBounds(region)
                         .filterDate(start_date, end_date)
                         .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                         .sort('CLOUDY_PIXEL_PERCENTAGE'))

            # Execute blocking GEE call in thread pool
            count = await asyncio.to_thread(collection.size().getInfo)
            if count == 0:
                logger.warning(
                    f"No suitable images found for {latitude}, {longitude} "
                    f"between {start_date} and {end_date}"
                )
                return None

            # Clip to region to save processing
            image = collection.first().clip(region)

            # Select bands for segmentation
            # Using Visible (RGB) + NIR (B8) for vegetation differentiation
            input_image = image.select(['B2', 'B3', 'B4', 'B8'])

            # SNIC Segmentation parameters
            # size: Superpixel seed spacing in pixels (10m pixels)
            # 15 pixels = 150m spacing approx, good for medium fields.
            seed_spacing = 15

            seeds = ee.Algorithms.Image.Segmentation.seedGrid(seed_spacing)

            # Run SNIC
            snic = ee.Algorithms.Image.Segmentation.SNIC(
                image=input_image,
                size=seed_spacing,
                compactness=0.8,  # Balance between color and spatial distance
                connectivity=8,
                neighborhoodSize=256,
                seeds=seeds
            )

            # Vectorize the 'clusters' band
            clusters = snic.select(['clusters'])

            vectors = clusters.reduceToVectors(
                geometry=region,
                scale=10,
                geometryType='polygon',
                eightConnected=False,
                labelProperty='cluster_id',
                reducer=ee.Reducer.count(), # Count pixels in each cluster
                maxPixels=1e8,
                bestEffort=True
            )

            # Convert to client-side GeoJSON (blocking call)
            geojson = await asyncio.to_thread(vectors.getInfo)

            if not geojson or 'features' not in geojson:
                logger.warning("Vectorization returned no features")
                return {'type': 'FeatureCollection', 'features': []}

            # Enrich metadata (blocking calls)
            image_id = await asyncio.to_thread(image.id().getInfo)
            acq_date = await asyncio.to_thread(image.date().format('YYYY-MM-dd').getInfo)

            for feature in geojson['features']:
                feature['properties']['image_id'] = image_id
                feature['properties']['acquisition_date'] = acq_date
                feature['properties']['area_ha'] = (
                    feature['properties'].get('count', 0) * 100 / 10000
                ) # 100 sq m per pixel / 10000 sq m per ha

            return geojson

        except Exception as e:
            logger.error(f"Field boundary extraction error: {str(e)}", exc_info=True)
            return None


# Singleton instance
_extractor = None

def get_boundary_extractor() -> GEEFieldBoundaryExtractor:
    """Get singleton extractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = GEEFieldBoundaryExtractor()
    return _extractor

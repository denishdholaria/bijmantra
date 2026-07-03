"""
Spatial Query Service

Provides location-based queries using PostGIS spatial functions.
Requires GIST indexes on geometry columns (migration 20260423_1000).
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SpatialQueryService:
    """Service for spatial queries using PostGIS.

    All methods use the SQL functions created in migration 20260423_1000:
    - find_nearest_devices() — uses ST_DWithin on iot_devices.coordinates
    - find_nearest_locations() — uses ST_DWithin on locations.coordinates

    Both functions use geography type for accurate distance calculations
    in meters (not degrees), leveraging the GIST indexes for performance.
    """

    async def find_nearest_devices(
        self,
        db: AsyncSession,
        lat: float,
        lon: float,
        radius_km: float,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Find IoT devices within radius_km of the given coordinates.

        Args:
            db: Database session
            lat: Latitude of the search center
            lon: Longitude of the search center
            radius_km: Search radius in kilometers
            max_results: Maximum number of results to return

        Returns:
            List of dicts with device_id, device_name, distance_km
            sorted by distance (nearest first)
        """
        result = await db.execute(
            text(
                "SELECT device_id, device_name, distance_km "
                "FROM find_nearest_devices(:lat, :lon, :radius_km, :max_results)"
            ),
            {
                "lat": lat,
                "lon": lon,
                "radius_km": radius_km,
                "max_results": max_results,
            },
        )
        return [
            {
                "device_id": row.device_id,
                "device_name": row.device_name,
                "distance_km": round(row.distance_km, 3),
            }
            for row in result.all()
        ]

    async def find_nearest_locations(
        self,
        db: AsyncSession,
        lat: float,
        lon: float,
        radius_km: float,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Find locations within radius_km of the given coordinates.

        Args:
            db: Database session
            lat: Latitude of the search center
            lon: Longitude of the search center
            radius_km: Search radius in kilometers
            max_results: Maximum number of results to return

        Returns:
            List of dicts with location_id, location_name, distance_km
            sorted by distance (nearest first)
        """
        result = await db.execute(
            text(
                "SELECT location_id, location_name, distance_km "
                "FROM find_nearest_locations(:lat, :lon, :radius_km, :max_results)"
            ),
            {
                "lat": lat,
                "lon": lon,
                "radius_km": radius_km,
                "max_results": max_results,
            },
        )
        return [
            {
                "location_id": row.location_id,
                "location_name": row.location_name,
                "distance_km": round(row.distance_km, 3),
            }
            for row in result.all()
        ]


# Singleton instance
spatial_query_service = SpatialQueryService()

"""
Location Search Service

Advanced location search and discovery.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_


class LocationSearchService:
    """Service for advanced location search.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def search(
        self, 
        db: AsyncSession,
        organization_id: int,
        query: Optional[str] = None,
        country: Optional[str] = None,
        location_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search locations with filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            query: Text search query (name, institute)
            country: Filter by country code or name
            location_type: Filter by location type
            limit: Maximum results to return
            
        Returns:
            List of location dictionaries, empty if no data
        """
        from app.models.core import Location
        
        stmt = (
            select(Location)
            .where(Location.organization_id == organization_id)
            .limit(limit)
        )
        
        if query:
            q = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Location.location_name).like(q),
                    func.lower(Location.location_db_id).like(q),
                    func.lower(Location.institute_name).like(q),
                    func.lower(Location.country_name).like(q),
                )
            )
        
        if country:
            stmt = stmt.where(
                or_(
                    func.lower(Location.country_code) == country.lower(),
                    func.lower(Location.country_name).like(f"%{country.lower()}%")
                )
            )
        
        if location_type:
            stmt = stmt.where(func.lower(Location.location_type) == location_type.lower())
        
        result = await db.execute(stmt)
        locations = result.scalars().all()
        
        results = []
        for loc in locations:
            # Extract coordinates if available
            lat, lon = None, None
            if loc.coordinates:
                try:
                    # PostGIS geometry - extract lat/lon
                    from geoalchemy2.shape import to_shape
                    point = to_shape(loc.coordinates)
                    lat, lon = point.y, point.x
                except Exception:
                    pass
            
            results.append({
                "id": str(loc.id),
                "location_db_id": loc.location_db_id,
                "name": loc.location_name,
                "type": loc.location_type or "Field",
                "abbreviation": loc.abbreviation,
                "country": loc.country_name,
                "country_code": loc.country_code,
                "institute": loc.institute_name,
                "address": loc.institute_address,
                "latitude": lat,
                "longitude": lon,
                "altitude": loc.altitude,
            })
        
        return results
    
    async def get_by_id(
        self, 
        db: AsyncSession,
        organization_id: int,
        location_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get location by ID with full details.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            location_id: Location ID
            
        Returns:
            Location dictionary or None if not found
        """
        from app.models.core import Location
        
        stmt = (
            select(Location)
            .where(Location.organization_id == organization_id)
            .where(Location.id == int(location_id))
        )
        
        result = await db.execute(stmt)
        loc = result.scalar_one_or_none()
        
        if not loc:
            return None
        
        # Extract coordinates
        lat, lon = None, None
        if loc.coordinates:
            try:
                from geoalchemy2.shape import to_shape
                point = to_shape(loc.coordinates)
                lat, lon = point.y, point.x
            except Exception:
                pass
        
        return {
            "id": str(loc.id),
            "location_db_id": loc.location_db_id,
            "name": loc.location_name,
            "type": loc.location_type,
            "abbreviation": loc.abbreviation,
            "country": loc.country_name,
            "country_code": loc.country_code,
            "institute": loc.institute_name,
            "address": loc.institute_address,
            "latitude": lat,
            "longitude": lon,
            "altitude": loc.altitude,
            "coordinate_uncertainty": loc.coordinate_uncertainty,
            "coordinate_description": loc.coordinate_description,
            "additional_info": loc.additional_info or {},
        }
    
    async def get_statistics(
        self, 
        db: AsyncSession,
        organization_id: int
    ) -> Dict[str, int]:
        """Get location statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Statistics dictionary with counts
        """
        from app.models.core import Location
        
        # Total count
        total_stmt = (
            select(func.count(Location.id))
            .where(Location.organization_id == organization_id)
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        # Country count
        country_stmt = (
            select(func.count(func.distinct(Location.country_code)))
            .where(Location.organization_id == organization_id)
        )
        country_result = await db.execute(country_stmt)
        country_count = country_result.scalar() or 0
        
        # Type count
        type_stmt = (
            select(func.count(func.distinct(Location.location_type)))
            .where(Location.organization_id == organization_id)
        )
        type_result = await db.execute(type_stmt)
        type_count = type_result.scalar() or 0
        
        return {
            "total_locations": total,
            "country_count": country_count,
            "type_count": type_count,
        }


# Singleton instance
location_search_service = LocationSearchService()

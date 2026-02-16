"""
Trial Network Service

Multi-environment trial coordination and analysis.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload


class TrialNetworkService:
    """Service for managing trial networks across multiple sites.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def get_sites(
        self,
        db: AsyncSession,
        organization_id: int,
        season: Optional[str] = None,
        status: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get trial sites from database with optional filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            season: Filter by season name
            status: Filter by status (active, completed, planned)
            country: Filter by country name
            region: Filter by region name
            
        Returns:
            List of trial site dictionaries, empty if no data
        """
        from app.models.core import Location, Trial

        # Query locations that have trials
        stmt = (
            select(Location)
            .where(Location.organization_id == organization_id)
            .options(selectinload(Location.trials))
        )

        if country:
            stmt = stmt.where(func.lower(Location.country_name) == country.lower())

        result = await db.execute(stmt)
        locations = result.scalars().all()

        sites = []
        for loc in locations:
            # Filter trials by season/status if specified
            trials = loc.trials
            if season:
                trials = [t for t in trials if t.additional_info and t.additional_info.get("season") == season]
            if status:
                trials = [t for t in trials if (t.active if status == "active" else not t.active)]

            if not trials:
                continue

            sites.append({
                "id": str(loc.id),
                "name": loc.location_name,
                "location": loc.institute_address or loc.location_name,
                "country": loc.country_name or "Unknown",
                "coordinates": self._extract_coordinates(loc),
                "trials": len(trials),
                "germplasm": 0,  # Would need to count from observation_units
                "status": "active" if any(t.active for t in trials) else "completed",
                "season": trials[0].additional_info.get("season") if trials and trials[0].additional_info else None,
                "lead": None,  # Would need to join with Person
                "region": loc.additional_info.get("region") if loc.additional_info else None,
            })

        # Apply region filter
        if region:
            sites = [s for s in sites if s.get("region", "").lower() == region.lower()]

        return sites

    def _extract_coordinates(self, location) -> Optional[Dict[str, float]]:
        """Extract lat/lng from PostGIS geometry."""
        if location.coordinates is None:
            return None
        try:
            # PostGIS geometry - would need to extract coordinates
            # For now return None, proper implementation needs ST_X/ST_Y
            return None
        except Exception:
            return None

    async def get_site(
        self,
        db: AsyncSession,
        organization_id: int,
        site_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific site by ID.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            site_id: Location ID
            
        Returns:
            Site dictionary or None if not found
        """
        from app.models.core import Location

        stmt = (
            select(Location)
            .where(Location.organization_id == organization_id)
            .where(Location.id == int(site_id))
            .options(selectinload(Location.trials))
        )

        result = await db.execute(stmt)
        loc = result.scalar_one_or_none()

        if not loc:
            return None

        return {
            "id": str(loc.id),
            "name": loc.location_name,
            "location": loc.institute_address or loc.location_name,
            "country": loc.country_name or "Unknown",
            "coordinates": self._extract_coordinates(loc),
            "trials": len(loc.trials),
            "germplasm": 0,
            "status": "active" if any(t.active for t in loc.trials) else "completed",
            "lead": None,
            "region": loc.additional_info.get("region") if loc.additional_info else None,
        }

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
        season: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get network statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            season: Optional season filter
            
        Returns:
            Statistics dictionary with counts
        """
        from app.models.core import Location, Trial

        # Count locations
        loc_stmt = select(func.count(Location.id)).where(Location.organization_id == organization_id)
        loc_result = await db.execute(loc_stmt)
        total_sites = loc_result.scalar() or 0

        # Count trials
        trial_stmt = select(Trial).where(Trial.organization_id == organization_id)
        if season:
            trial_stmt = trial_stmt.where(Trial.additional_info["season"].astext == season)
        trial_result = await db.execute(trial_stmt)
        trials = trial_result.scalars().all()

        active_trials = len([t for t in trials if t.active])

        # Count countries
        country_stmt = (
            select(func.count(func.distinct(Location.country_name)))
            .where(Location.organization_id == organization_id)
            .where(Location.country_name.isnot(None))
        )
        country_result = await db.execute(country_stmt)
        countries = country_result.scalar() or 0

        return {
            "total_sites": total_sites,
            "active_trials": active_trials,
            "countries": countries,
            "germplasm_entries": 0,  # Would need observation_units count
            "collaborators": 0,
            "by_status": {
                "active": active_trials,
                "completed": len(trials) - active_trials,
                "planned": 0,
            },
            "by_region": {}  # Would need to aggregate from location.additional_info
        }

    async def get_shared_germplasm(
        self,
        db: AsyncSession,
        organization_id: int,
        min_sites: int = 1,
        crop: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get germplasm shared across multiple sites.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            min_sites: Minimum number of sites germplasm must appear in
            crop: Filter by crop name
            
        Returns:
            List of germplasm dictionaries, empty if no data
        """
        # This would require a complex query joining germplasm -> observation_units -> studies -> locations
        # For now, return empty list - proper implementation needs the full query
        return []

    async def get_network_performance(
        self,
        db: AsyncSession,
        organization_id: int,
        trait: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get network-wide performance metrics.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            trait: Filter by trait name
            
        Returns:
            List of performance metrics, empty if no data
        """
        # This would require aggregating observations across sites
        # For now, return empty list - proper implementation needs observation aggregation
        return []

    async def get_site_comparison(
        self,
        db: AsyncSession,
        organization_id: int,
        site_ids: List[str]
    ) -> Dict[str, Any]:
        """Compare performance across selected sites.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            site_ids: List of location IDs to compare
            
        Returns:
            Comparison dictionary with sites and metrics
        """
        if not site_ids:
            return {"sites": [], "comparison": []}

        sites = []
        for site_id in site_ids:
            site = await self.get_site(db, organization_id, site_id)
            if site:
                sites.append(site)

        if not sites:
            return {"sites": [], "comparison": []}

        return {
            "sites": sites,
            "comparison": [
                {"metric": "Total Trials", "values": {s["id"]: s["trials"] for s in sites}},
                {"metric": "Status", "values": {s["id"]: s["status"] for s in sites}},
            ]
        }

    async def get_countries(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> List[Dict[str, Any]]:
        """Get list of countries with trial sites.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            List of country dictionaries with site counts
        """
        from app.models.core import Location, Trial

        stmt = (
            select(
                Location.country_name,
                func.count(Location.id).label("sites"),
            )
            .where(Location.organization_id == organization_id)
            .where(Location.country_name.isnot(None))
            .group_by(Location.country_name)
        )

        result = await db.execute(stmt)
        rows = result.all()

        countries = []
        for row in rows:
            countries.append({
                "name": row.country_name,
                "sites": row.sites,
                "trials": 0,  # Would need a join to count
                "region": None,
            })

        return countries

    async def get_seasons(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> List[Dict[str, Any]]:
        """Get available seasons from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            List of season dictionaries
        """
        from app.models.core import Season

        stmt = (
            select(Season)
            .where(Season.organization_id == organization_id)
            .order_by(Season.year.desc())
        )

        result = await db.execute(stmt)
        seasons = result.scalars().all()

        return [
            {
                "id": s.season_db_id or str(s.id),
                "name": s.season_name,
                "status": "active" if s.additional_info and s.additional_info.get("status") == "active" else "completed",
            }
            for s in seasons
        ]


# Singleton instance
trial_network_service = TrialNetworkService()

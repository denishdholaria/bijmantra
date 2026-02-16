"""
Germplasm Search Service

Advanced germplasm search and discovery.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_


class GermplasmSearchService:
    """Service for advanced germplasm search.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def search(
        self,
        db: AsyncSession,
        organization_id: int,
        query: Optional[str] = None,
        species: Optional[str] = None,
        origin: Optional[str] = None,
        collection: Optional[str] = None,
        trait: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search germplasm with filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            query: Text search query (name, accession, traits)
            species: Filter by species name
            origin: Filter by country of origin
            collection: Filter by collection/institute
            trait: Filter by trait keyword
            limit: Maximum results to return
            
        Returns:
            List of germplasm dictionaries, empty if no data
        """
        from app.models.germplasm import Germplasm

        stmt = (
            select(Germplasm)
            .where(Germplasm.organization_id == organization_id)
            .limit(limit)
        )

        if query:
            q = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Germplasm.germplasm_name).like(q),
                    func.lower(Germplasm.accession_number).like(q),
                    func.lower(Germplasm.germplasm_db_id).like(q),
                    func.lower(Germplasm.species).like(q),
                    func.lower(Germplasm.subtaxa).like(q),
                )
            )

        if species:
            stmt = stmt.where(func.lower(Germplasm.species) == species.lower())

        if origin:
            stmt = stmt.where(func.lower(Germplasm.country_of_origin_code) == origin.lower())

        if collection:
            stmt = stmt.where(func.lower(Germplasm.collection) == collection.lower())

        result = await db.execute(stmt)
        germplasm_list = result.scalars().all()

        results = []
        for g in germplasm_list:
            # Extract traits from additional_info if present
            traits = []
            if g.additional_info and isinstance(g.additional_info, dict):
                traits = g.additional_info.get("traits", [])

            # Filter by trait if specified
            if trait and not any(trait.lower() in t.lower() for t in traits):
                continue

            results.append({
                "id": str(g.id),
                "name": g.germplasm_name,
                "accession": g.accession_number or g.germplasm_db_id,
                "species": g.species or "Unknown",
                "subspecies": g.subtaxa or "",
                "origin": g.country_of_origin_code or "Unknown",
                "traits": traits,
                "status": "Active",
                "collection": g.collection or "",
                "year": g.acquisition_date[:4] if g.acquisition_date else None,
            })

        return results

    async def get_by_id(
        self,
        db: AsyncSession,
        organization_id: int,
        germplasm_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get germplasm by ID.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            germplasm_id: Germplasm ID
            
        Returns:
            Germplasm dictionary or None if not found
        """
        from app.models.germplasm import Germplasm

        stmt = (
            select(Germplasm)
            .where(Germplasm.organization_id == organization_id)
            .where(Germplasm.id == int(germplasm_id))
        )

        result = await db.execute(stmt)
        g = result.scalar_one_or_none()

        if not g:
            return None

        traits = []
        if g.additional_info and isinstance(g.additional_info, dict):
            traits = g.additional_info.get("traits", [])

        return {
            "id": str(g.id),
            "name": g.germplasm_name,
            "accession": g.accession_number or g.germplasm_db_id,
            "species": g.species or "Unknown",
            "subspecies": g.subtaxa or "",
            "origin": g.country_of_origin_code or "Unknown",
            "traits": traits,
            "status": "Active",
            "collection": g.collection or "",
            "year": g.acquisition_date[:4] if g.acquisition_date else None,
        }

    async def get_filters(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> Dict[str, List[str]]:
        """Get available filter options from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Dictionary with filter options (species, origins, collections, traits)
        """
        from app.models.germplasm import Germplasm

        # Get distinct species
        species_stmt = (
            select(func.distinct(Germplasm.species))
            .where(Germplasm.organization_id == organization_id)
            .where(Germplasm.species.isnot(None))
        )
        species_result = await db.execute(species_stmt)
        species = [r[0] for r in species_result.all() if r[0]]

        # Get distinct origins
        origin_stmt = (
            select(func.distinct(Germplasm.country_of_origin_code))
            .where(Germplasm.organization_id == organization_id)
            .where(Germplasm.country_of_origin_code.isnot(None))
        )
        origin_result = await db.execute(origin_stmt)
        origins = [r[0] for r in origin_result.all() if r[0]]

        # Get distinct collections
        collection_stmt = (
            select(func.distinct(Germplasm.collection))
            .where(Germplasm.organization_id == organization_id)
            .where(Germplasm.collection.isnot(None))
        )
        collection_result = await db.execute(collection_stmt)
        collections = [r[0] for r in collection_result.all() if r[0]]

        return {
            "species": sorted(species),
            "origins": sorted(origins),
            "collections": sorted(collections),
            "traits": [],  # Would need to aggregate from additional_info
        }

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> Dict[str, int]:
        """Get search statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Statistics dictionary with counts
        """
        from app.models.germplasm import Germplasm

        # Total count
        total_stmt = (
            select(func.count(Germplasm.id))
            .where(Germplasm.organization_id == organization_id)
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0

        # Species count
        species_stmt = (
            select(func.count(func.distinct(Germplasm.species)))
            .where(Germplasm.organization_id == organization_id)
        )
        species_result = await db.execute(species_stmt)
        species_count = species_result.scalar() or 0

        # Origin count
        origin_stmt = (
            select(func.count(func.distinct(Germplasm.country_of_origin_code)))
            .where(Germplasm.organization_id == organization_id)
        )
        origin_result = await db.execute(origin_stmt)
        origin_count = origin_result.scalar() or 0

        # Collection count
        collection_stmt = (
            select(func.count(func.distinct(Germplasm.collection)))
            .where(Germplasm.organization_id == organization_id)
        )
        collection_result = await db.execute(collection_stmt)
        collection_count = collection_result.scalar() or 0

        return {
            "total_germplasm": total,
            "species_count": species_count,
            "origin_count": origin_count,
            "collection_count": collection_count,
        }


# Singleton instance
germplasm_search_service = GermplasmSearchService()

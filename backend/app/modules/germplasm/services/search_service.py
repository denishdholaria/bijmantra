"""
Germplasm Search Service

Advanced germplasm search and discovery.
Queries real data from database - no demo/mock data.
"""

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


def _collection_expression(germplasm_model: Any):
    return func.coalesce(
        func.nullif(func.trim(germplasm_model.institute_name), ""),
        func.nullif(func.trim(germplasm_model.collection_site), ""),
    )


def _collection_label(germplasm: Any) -> str:
    institute_name = getattr(germplasm, "institute_name", None)
    if isinstance(institute_name, str) and institute_name.strip():
        return institute_name.strip()

    collection_site = getattr(germplasm, "collection_site", None)
    if isinstance(collection_site, str) and collection_site.strip():
        return collection_site.strip()

    return ""


class GermplasmSearchService:
    """Service for advanced germplasm search.

    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def search(
        self,
        db: AsyncSession,
        organization_id: int,
        query: str | None = None,
        species: str | None = None,
        origin: str | None = None,
        collection: str | None = None,
        trait: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
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

        collection_expr = _collection_expression(Germplasm)
        stmt = select(Germplasm).where(Germplasm.organization_id == organization_id).limit(limit)

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
            stmt = stmt.where(func.lower(collection_expr) == collection.strip().lower())

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

            results.append(
                {
                    "id": str(g.id),
                    "name": g.germplasm_name,
                    "accession": g.accession_number or g.germplasm_db_id,
                    "species": g.species or "Unknown",
                    "subspecies": g.subtaxa or "",
                    "origin": g.country_of_origin_code or "Unknown",
                    "traits": traits,
                    "status": "Active",
                    "collection": _collection_label(g),
                    "year": g.acquisition_date[:4] if g.acquisition_date else None,
                }
            )

        return results

    async def get_by_id(
        self, db: AsyncSession, organization_id: int, germplasm_id: str
    ) -> dict[str, Any] | None:
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
            "collection": _collection_label(g),
            "year": g.acquisition_date[:4] if g.acquisition_date else None,
        }

    async def get_filters(self, db: AsyncSession, organization_id: int) -> dict[str, list[str]]:
        """Get available filter options from database.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering

        Returns:
            Dictionary with filter options (species, origins, collections, traits)
        """
        from app.core.redis import redis_client
        from app.models.germplasm import Germplasm

        cache_key = f"germplasm:filters:{organization_id}"
        collection_expr = _collection_expression(Germplasm)

        # Try cache
        if redis_client.is_available:
            cached = await redis_client.get(cache_key)
            if cached:
                return cached

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
            select(func.distinct(collection_expr))
            .where(Germplasm.organization_id == organization_id)
            .where(collection_expr.isnot(None))
        )
        collection_result = await db.execute(collection_stmt)
        collections = [r[0] for r in collection_result.all() if r[0]]

        result = {
            "species": sorted(species),
            "origins": sorted(origins),
            "collections": sorted(collections),
            "traits": [],  # Would need to aggregate from additional_info
        }

        # Save to cache
        if redis_client.is_available:
            await redis_client.set(cache_key, result, ttl_seconds=3600)

        return result

    async def get_statistics(self, db: AsyncSession, organization_id: int) -> dict[str, int]:
        """Get search statistics from database.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering

        Returns:
            Statistics dictionary with counts
        """
        from app.models.germplasm import Germplasm

        collection_expr = _collection_expression(Germplasm)

        # Total count
        total_stmt = select(func.count(Germplasm.id)).where(
            Germplasm.organization_id == organization_id
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0

        # Species count
        species_stmt = select(func.count(func.distinct(Germplasm.species))).where(
            Germplasm.organization_id == organization_id
        )
        species_result = await db.execute(species_stmt)
        species_count = species_result.scalar() or 0

        # Origin count
        origin_stmt = select(func.count(func.distinct(Germplasm.country_of_origin_code))).where(
            Germplasm.organization_id == organization_id
        )
        origin_result = await db.execute(origin_stmt)
        origin_count = origin_result.scalar() or 0

        # Collection count
        collection_stmt = (
            select(func.count(func.distinct(collection_expr)))
            .where(Germplasm.organization_id == organization_id)
            .where(collection_expr.isnot(None))
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

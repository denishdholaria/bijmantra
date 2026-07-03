"""
Germplasm Comparison Service

Compare germplasm entries by traits and markers.
Extracted from germplasm_comparison API router.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.germplasm import Germplasm, GermplasmAttribute
from app.models.phenotyping import ObservationVariable


class GermplasmComparisonService:
    """Service for comparing germplasm entries."""

    async def list_germplasm(
        self,
        db: AsyncSession,
        organization_id: int,
        search: str | None = None,
        crop: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """List germplasm entries available for comparison.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            search: Search query for germplasm name
            crop: Filter by crop name
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with data, total, page, and page_size
        """
        q = select(Germplasm).where(Germplasm.organization_id == organization_id)
        if search:
            q = q.where(Germplasm.germplasm_name.ilike(f"%{search}%"))
        if crop:
            q = q.where(Germplasm.common_crop_name.ilike(f"%{crop}%"))

        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0

        q = q.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(q)
        items = result.scalars().all()

        return {
            "data": [self._germplasm_to_dict(g) for g in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_germplasm(
        self, db: AsyncSession, organization_id: int, germplasm_id: int
    ) -> dict[str, Any] | None:
        """Get a single germplasm entry.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            germplasm_id: Germplasm ID

        Returns:
            Germplasm dictionary or None if not found
        """
        g = (
            await db.execute(
                select(Germplasm).where(
                    Germplasm.id == germplasm_id,
                    Germplasm.organization_id == organization_id,
                )
            )
        ).scalar_one_or_none()
        if not g:
            return None
        return self._germplasm_to_dict(g)

    async def compare_germplasm(
        self, db: AsyncSession, organization_id: int, germplasm_ids: list[int]
    ) -> dict[str, Any]:
        """Compare two or more germplasm entries side-by-side.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            germplasm_ids: List of germplasm IDs to compare (min 2, max 20)

        Returns:
            Dictionary with entries and count

        Raises:
            ValueError: If less than 2 germplasm entries found
        """
        result = await db.execute(
            select(Germplasm).where(
                Germplasm.id.in_(germplasm_ids),
                Germplasm.organization_id == organization_id,
            )
        )
        entries = result.scalars().all()
        if len(entries) < 2:
            raise ValueError("Need at least 2 germplasm entries")

        comparison = []
        for g in entries:
            attrs = (
                (
                    await db.execute(
                        select(GermplasmAttribute).where(GermplasmAttribute.germplasm_id == g.id)
                    )
                )
                .scalars()
                .all()
            )

            comparison.append(
                {
                    **self._germplasm_to_dict(g),
                    "attributes": {a.attribute_name: a.value for a in attrs},
                }
            )

        return {"entries": comparison, "count": len(comparison)}

    async def get_traits(
        self, db: AsyncSession, organization_id: int, crop: str | None = None
    ) -> list[dict[str, Any]]:
        """Get observation variables (traits) available for comparison.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            crop: Filter by crop name

        Returns:
            List of trait dictionaries
        """
        q = select(ObservationVariable).where(
            ObservationVariable.organization_id == organization_id
        )
        if crop:
            q = q.where(ObservationVariable.common_crop_name.ilike(f"%{crop}%"))
        q = q.limit(200)
        result = await db.execute(q)
        variables = result.scalars().all()
        return [
            {
                "id": str(v.id),
                "name": v.observation_variable_name,
                "trait": getattr(v, "trait_name", None),
            }
            for v in variables
        ]

    async def get_markers(
        self, db: AsyncSession, organization_id: int, crop: str | None = None
    ) -> list[dict[str, Any]]:
        """Get genetic markers for comparison.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            crop: Filter by crop name

        Returns:
            List of marker dictionaries (empty for now - markers table not yet created)
        """
        # Markers table not yet created
        return []

    async def get_statistics(
        self, db: AsyncSession, organization_id: int
    ) -> dict[str, int]:
        """Get comparison statistics.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering

        Returns:
            Statistics dictionary with counts
        """
        germplasm_count = (
            await db.execute(
                select(func.count(Germplasm.id)).where(
                    Germplasm.organization_id == organization_id
                )
            )
        ).scalar() or 0

        crop_count = (
            await db.execute(
                select(func.count(func.distinct(Germplasm.common_crop_name))).where(
                    Germplasm.organization_id == organization_id,
                    Germplasm.common_crop_name.isnot(None),
                )
            )
        ).scalar() or 0

        return {
            "total_germplasm": germplasm_count,
            "total_crops": crop_count,
            "total_comparisons": 0,
        }

    @staticmethod
    def _germplasm_to_dict(g: Germplasm) -> dict[str, Any]:
        """Convert Germplasm model to dictionary.

        Args:
            g: Germplasm model instance

        Returns:
            Dictionary representation
        """
        return {
            "id": str(g.id),
            "germplasmDbId": g.germplasm_db_id or str(g.id),
            "germplasmName": g.germplasm_name,
            "commonCropName": g.common_crop_name,
            "genus": g.genus,
            "species": g.species,
            "pedigree": g.pedigree,
        }


# Singleton instance
germplasm_comparison_service = GermplasmComparisonService()

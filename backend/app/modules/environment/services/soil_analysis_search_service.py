"""
Soil Analysis Search Service

Queries soil test records for REEVU domain steps.
All queries are tenant-scoped. Returns empty results when no data exists.
No mock data — real DB only.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class SoilAnalysisSearchService:
    """Search and aggregate soil analysis records for REEVU.

    Wraps the SoilTest model (future/soil_test.py) with REEVU-compatible
    dict output and nutrient aggregation.
    """

    async def search(
        self,
        db: AsyncSession,
        organization_id: int,
        location_id: int | None = None,
        query: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search soil test records scoped to an organization.

        Args:
            db: Async DB session.
            organization_id: Tenant filter — mandatory.
            location_id: Optional field/location ID filter.
            query: Optional text filter (matched against sample_id, notes).
            limit: Max records to return.

        Returns:
            List of soil test dicts. Empty list when no data.
        """
        from app.models.future.soil_test import SoilTest

        stmt = (
            select(SoilTest)
            .where(SoilTest.organization_id == organization_id)
            .order_by(SoilTest.sample_date.desc())
            .limit(limit)
        )

        if location_id is not None:
            stmt = stmt.where(SoilTest.field_id == location_id)

        if query:
            from sqlalchemy import or_, func
            q = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(SoilTest.sample_id).like(q),
                    func.lower(SoilTest.notes).like(q),
                )
            )

        result = await db.execute(stmt)
        tests = result.scalars().all()

        return [self._to_dict(t) for t in tests]

    async def get_nutrient_summary(
        self,
        db: AsyncSession,
        organization_id: int,
        location_id: int,
    ) -> dict[str, Any]:
        """Aggregate nutrient levels across all soil tests for a location.

        Computes mean N, P, K, pH, and organic matter, skipping None values.
        Adds soil_health_indicators with pH and organic matter status flags.

        Args:
            db: Async DB session.
            organization_id: Tenant filter.
            location_id: Location/field ID to summarise.

        Returns:
            Summary dict. sample_count=0 and None means when no tests exist.
        """
        from app.models.future.soil_test import SoilTest

        stmt = (
            select(SoilTest)
            .where(
                SoilTest.organization_id == organization_id,
                SoilTest.field_id == location_id,
            )
            .order_by(SoilTest.sample_date.desc())
        )

        result = await db.execute(stmt)
        tests = list(result.scalars().all())

        if not tests:
            return {
                "location_id": location_id,
                "sample_count": 0,
                "mean_ph": None,
                "mean_n_ppm": None,
                "mean_p_ppm": None,
                "mean_k_ppm": None,
                "mean_organic_matter_percent": None,
                "soil_health_indicators": {},
            }

        def _mean(values: list[float | None]) -> float | None:
            valid = [v for v in values if v is not None]
            return sum(valid) / len(valid) if valid else None

        mean_ph = _mean([t.ph for t in tests])
        mean_n = _mean([t.n_ppm for t in tests])
        mean_p = _mean([t.p_ppm for t in tests])
        mean_k = _mean([t.k_ppm for t in tests])
        mean_om = _mean([t.organic_matter_percent for t in tests])

        indicators: dict[str, str] = {}
        if mean_ph is not None:
            if mean_ph < 5.5:
                indicators["ph_status"] = "acidic"
            elif mean_ph > 7.5:
                indicators["ph_status"] = "alkaline"
            else:
                indicators["ph_status"] = "optimal"
        if mean_om is not None:
            if mean_om < 2.0:
                indicators["organic_matter_status"] = "low"
            elif mean_om > 4.0:
                indicators["organic_matter_status"] = "high"
            else:
                indicators["organic_matter_status"] = "adequate"

        return {
            "location_id": location_id,
            "sample_count": len(tests),
            "mean_ph": mean_ph,
            "mean_n_ppm": mean_n,
            "mean_p_ppm": mean_p,
            "mean_k_ppm": mean_k,
            "mean_organic_matter_percent": mean_om,
            "soil_health_indicators": indicators,
        }

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _to_dict(t: Any) -> dict[str, Any]:
        """Convert a SoilTest ORM object to a plain dict."""
        return {
            "id": str(t.id),
            "field_id": t.field_id,
            "sample_id": t.sample_id,
            "sample_date": str(t.sample_date) if t.sample_date else None,
            "ph": t.ph,
            "organic_matter_percent": t.organic_matter_percent,
            "n_ppm": t.n_ppm,
            "p_ppm": t.p_ppm,
            "k_ppm": t.k_ppm,
            "ca_ppm": t.ca_ppm,
            "mg_ppm": t.mg_ppm,
            "s_ppm": t.s_ppm,
            "zn_ppm": t.zn_ppm,
            "texture_class": t.texture_class,
            "notes": t.notes,
        }


# Singleton instance
soil_analysis_search_service = SoilAnalysisSearchService()

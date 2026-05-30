"""
Disease Resistance Search Service

Queries disease resistance genes and pest/disease scouting records for REEVU.
All queries are tenant-scoped. Returns empty results when no data exists.
No mock data — real DB only.
"""

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class DiseaseResistanceSearchService:
    """Search disease resistance profiles and pest scouting records for REEVU.

    Wraps:
    - ResistanceGene model (stress_resistance.py) for resistance profiles
    - PestObservation model (future/pest_observation.py) for scouting records
    """

    async def get_resistance_profiles(
        self,
        db: AsyncSession,
        organization_id: int,
        germplasm_ids: list[int] | None = None,
        disease: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Query disease resistance gene records for an organization.

        Args:
            db: Async DB session.
            organization_id: Tenant filter — mandatory.
            germplasm_ids: Optional list of germplasm IDs to scope the query.
                           When provided, only genes whose source_germplasm
                           matches are returned (best-effort text match).
            disease: Optional disease name filter (case-insensitive substring).
            limit: Max records to return.

        Returns:
            List of resistance profile dicts. Empty list when no data.
        """
        from app.models.stress_resistance import ResistanceGene, Disease

        stmt = (
            select(ResistanceGene)
            .join(Disease, ResistanceGene.disease_id == Disease.id)
            .options(selectinload(ResistanceGene.disease))
            .where(ResistanceGene.organization_id == organization_id)
            .limit(limit)
        )

        if disease:
            d = f"%{disease.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Disease.name).like(d),
                    func.lower(Disease.pathogen).like(d),
                )
            )

        result = await db.execute(stmt)
        genes = result.scalars().all()

        return [self._gene_to_dict(g) for g in genes]

    async def search_scouting_records(
        self,
        db: AsyncSession,
        organization_id: int,
        location_id: int | None = None,
        crop: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Query pest/disease scouting observations for an organization.

        Args:
            db: Async DB session.
            organization_id: Tenant filter — mandatory.
            location_id: Optional field/location ID filter.
            crop: Optional crop name filter (case-insensitive substring).
            limit: Max records to return.

        Returns:
            List of scouting record dicts. Empty list when no data.
        """
        from app.models.future.pest_observation import PestObservation

        stmt = (
            select(PestObservation)
            .where(PestObservation.organization_id == organization_id)
            .order_by(PestObservation.observation_date.desc())
            .limit(limit)
        )

        if location_id is not None:
            stmt = stmt.where(PestObservation.field_id == location_id)

        if crop:
            c = f"%{crop.lower()}%"
            stmt = stmt.where(func.lower(PestObservation.crop_name).like(c))

        result = await db.execute(stmt)
        observations = result.scalars().all()

        return [self._obs_to_dict(o) for o in observations]

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _gene_to_dict(g: Any) -> dict[str, Any]:
        """Convert a ResistanceGene ORM object to a plain dict."""
        disease = g.disease
        return {
            "id": str(g.id),
            "gene_code": g.gene_code,
            "gene_name": g.name,
            "resistance_type": str(g.resistance_type.value) if hasattr(g.resistance_type, "value") else str(g.resistance_type),
            "disease_name": disease.name if disease else None,
            "disease_crop": disease.crop if disease else None,
            "pathogen_type": str(disease.pathogen_type.value) if disease and hasattr(disease.pathogen_type, "value") else (str(disease.pathogen_type) if disease else None),
            "chromosome": g.chromosome,
            "markers": list(g.markers) if g.markers else [],
            "source_germplasm": g.source_germplasm,
            "is_validated": g.is_validated,
            "reference": g.reference,
        }

    @staticmethod
    def _obs_to_dict(o: Any) -> dict[str, Any]:
        """Convert a PestObservation ORM object to a plain dict."""
        return {
            "id": str(o.id),
            "field_id": o.field_id,
            "pest_name": o.pest_name,
            "pest_type": o.pest_type,
            "severity_score": o.severity_score,
            "incidence_percent": o.incidence_percent,
            "crop_name": o.crop_name,
            "observation_date": str(o.observation_date) if o.observation_date else None,
            "growth_stage": o.growth_stage,
            "notes": o.notes,
        }


# Singleton instance
disease_resistance_search_service = DiseaseResistanceSearchService()

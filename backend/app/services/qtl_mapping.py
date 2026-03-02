"""
QTL Mapping Service

Provides QTL detection, GWAS analysis, and candidate gene identification
for marker-trait association studies.

Queries real data from database - no demo/mock data.
"""

from typing import Any

from scipy import stats
from sqlalchemy import func, select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.qtl import Gene, GOTerm
from app.modules.bio_analytics.models import GWASResult, GWASRun, BioQTL, CandidateGene


class QTLMappingService:
    """Service for QTL mapping and GWAS analysis.

    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def list_qtls(
        self,
        db: AsyncSession,
        organization_id: int,
        trait: str | None = None,
        chromosome: str | None = None,
        min_lod: float = 0,
        population: str | None = None,
    ) -> list[dict[str, Any]]:
        """List detected QTLs with optional filters.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            trait: Filter by trait name
            chromosome: Filter by chromosome
            min_lod: Minimum LOD score threshold
            population: Filter by mapping population

        Returns:
            List of QTL dictionaries, empty if no data
        """
        query = select(BioQTL).options(selectinload(BioQTL.candidate_genes)).where(BioQTL.organization_id == organization_id)

        if trait:
            query = query.where(BioQTL.trait == trait)
        if chromosome:
            query = query.where(BioQTL.chromosome == chromosome)
        if min_lod > 0:
            query = query.where(BioQTL.lod >= min_lod)
        if population:
            query = query.where(BioQTL.population == population)

        result = await db.execute(query)
        qtls = result.scalars().all()

        return [self._qtl_to_dict(q) for q in qtls]

    async def get_qtl(
        self,
        db: AsyncSession,
        organization_id: int,
        qtl_id: str
    ) -> dict[str, Any] | None:
        """Get a single QTL by ID.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            qtl_id: QTL ID

        Returns:
            QTL dictionary or None if not found
        """
        query = select(BioQTL).options(selectinload(BioQTL.candidate_genes)).where(
            BioQTL.organization_id == organization_id,
            BioQTL.qtl_db_id == qtl_id
        )
        result = await db.execute(query)
        qtl = result.scalar_one_or_none()

        return self._qtl_to_dict(qtl) if qtl else None

    async def get_gwas_results(
        self,
        db: AsyncSession,
        organization_id: int,
        trait: str | None = None,
        chromosome: str | None = None,
        min_log_p: float = 0,
        max_p_value: float | None = None,
    ) -> list[dict[str, Any]]:
        """Get GWAS marker-trait associations.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            trait: Filter by trait name
            chromosome: Filter by chromosome
            min_log_p: Minimum -log10(p) threshold
            max_p_value: Maximum p-value threshold

        Returns:
            List of GWAS result dictionaries, empty if no data
        """
        query = select(GWASResult, GWASRun.trait_name).join(GWASRun).options(selectinload(GWASResult.run)).where(GWASResult.organization_id == organization_id)

        if trait:
            query = query.where(GWASRun.trait_name == trait)
        if chromosome:
            query = query.where(GWASResult.chromosome == chromosome)
        if min_log_p > 0:
            query = query.where(GWASResult.neg_log10_p >= min_log_p)
        if max_p_value is not None:
            query = query.where(GWASResult.p_value <= max_p_value)

        result = await db.execute(query)
        rows = result.all()
        return [self._gwas_result_to_dict(row[0], row[1]) for row in rows]

    async def get_manhattan_data(
        self,
        db: AsyncSession,
        organization_id: int,
        trait: str | None = None
    ) -> dict[str, Any]:
        """Get data for Manhattan plot visualization.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            trait: Optional trait filter

        Returns:
            Dictionary with points and chromosome boundaries
        """
        gwas_results = await self.get_gwas_results(db, organization_id, trait=trait)

        if not gwas_results:
            return {
                "points": [],
                "chromosome_boundaries": [],
                "significance_threshold": 5.0,
                "suggestive_threshold": 4.0,
                "genomic_inflation_factor": 1.0,
            }

        # Convert GWAS results to Manhattan plot format
        points = []
        for r in gwas_results:
            points.append({
                "chromosome": r.get("chromosome"),
                "position": r.get("position"),
                "cumulative_position": r.get("position"),  # Would need proper calculation
                "log_p": r.get("log_p", 0),
            })

        return {
            "points": points,
            "chromosome_boundaries": [],
            "significance_threshold": 5.0,
            "suggestive_threshold": 4.0,
            "genomic_inflation_factor": 1.0,
        }

    async def get_lod_profile(
        self,
        db: AsyncSession,
        organization_id: int,
        chromosome: str,
        trait: str | None = None
    ) -> dict[str, Any]:
        """Get LOD score profile for a chromosome.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            chromosome: Chromosome identifier
            trait: Optional trait filter

        Returns:
            Dictionary with positions and LOD scores
        """
        qtls = await self.list_qtls(db, organization_id, chromosome=chromosome, trait=trait)

        return {
            "chromosome": chromosome,
            "positions": [],
            "lod_scores": [],
            "threshold": 3.0,
            "qtls_on_chromosome": qtls,
        }

    async def get_candidate_genes(
        self,
        db: AsyncSession,
        organization_id: int,
        qtl_id: str
    ) -> list[dict[str, Any]]:
        """Get candidate genes within a QTL confidence interval.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            qtl_id: QTL ID

        Returns:
            List of candidate gene dictionaries, empty if no data
        """
        query = select(CandidateGene).join(BioQTL).where(
            CandidateGene.organization_id == organization_id,
            BioQTL.qtl_db_id == str(qtl_id)
        )
        result = await db.execute(query)
        genes = result.scalars().all()

        return [
            {
                "id": str(g.id),
                "gene_id": g.gene_id,
                "gene_name": g.gene_name,
                "chromosome": g.chromosome,
                "start": g.start_position,
                "end": g.end_position,
                "source": g.source,
                "description": g.description,
                "go_terms": g.go_terms
            }
            for g in genes
        ]

    async def get_go_enrichment(
        self,
        db: AsyncSession,
        organization_id: int,
        qtl_ids: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Get GO enrichment analysis for candidate genes.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            qtl_ids: Optional list of QTL IDs to analyze

        Returns:
            List of GO enrichment result dictionaries
        """
        # 1. Identify candidate genes
        candidate_genes: set[str] = set()
        if qtl_ids:
            for q_id in qtl_ids:
                genes = await self.get_candidate_genes(db, organization_id, q_id)
                for g in genes:
                    candidate_genes.add(g["gene_id"])
        else:
            return []

        if not candidate_genes:
            return []

        # 2. Fetch GO annotations for candidate genes
        query_candidates = select(Gene).options(selectinload(Gene.go_terms)).where(
            Gene.organization_id == organization_id,
            Gene.gene_id.in_(candidate_genes)
        )
        result_candidates = await db.execute(query_candidates)
        candidate_gene_objs = result_candidates.scalars().all()

        candidate_go_counts: dict[str, int] = {}
        for gene in candidate_gene_objs:
            for go in gene.go_terms:
                if go.go_id not in candidate_go_counts:
                    candidate_go_counts[go.go_id] = 0
                candidate_go_counts[go.go_id] += 1

        go_map: dict[str, GOTerm] = {}
        for gene in candidate_gene_objs:
            for go in gene.go_terms:
                go_map[go.go_id] = go

        # 3. Background stats
        query_total = select(func.count()).select_from(Gene).where(Gene.organization_id == organization_id)
        result_total = await db.execute(query_total)
        M = result_total.scalar() or 0

        if M == 0:
            return []

        n = len(candidate_genes)

        results = []
        for go_id, k in candidate_go_counts.items():
            go_obj = go_map[go_id]

            # N: genes in background with this GO term
            query_N = select(func.count()).select_from(Gene).join(Gene.go_terms).where(
                Gene.organization_id == organization_id,
                GOTerm.go_id == go_id
            )
            result_N = await db.execute(query_N)
            N = result_N.scalar() or 0

            # Fisher's Exact Test
            table = [[k, n - k], [N - k, M - N - (n - k)]]
            _, p_value = stats.fisher_exact(table, alternative='greater')

            results.append({
                "go_id": go_id,
                "term": go_obj.term,
                "category": go_obj.category,
                "p_value": float(p_value),
                "count_in_candidates": k,
                "count_in_background": N,
                "total_candidates": n,
                "total_background": M,
                "fold_enrichment": (k / n) / (N / M) if N > 0 and M > 0 else 0
            })

        results.sort(key=lambda x: x["p_value"])
        return results

    async def get_qtl_summary(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> dict[str, Any]:
        """Get summary statistics for QTL analysis.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering

        Returns:
            Summary statistics dictionary
        """
        result = await db.execute(
            select(BioQTL)
            .where(BioQTL.organization_id == organization_id)
        )
        qtls = result.scalars().all()

        if not qtls:
            return {
                "total_qtls": 0,
                "traits_analyzed": 0,
                "traits": [],
                "chromosomes_with_qtls": 0,
                "total_pve": 0,
                "average_lod": 0,
                "major_qtls": 0,
                "minor_qtls": 0,
            }

        traits = list({q.trait for q in qtls if q.trait})
        chromosomes = list({q.chromosome for q in qtls if q.chromosome})
        total_pve = sum(q.pve for q in qtls if q.pve is not None)
        avg_lod = sum(q.lod for q in qtls if q.lod is not None) / len(qtls) if qtls else 0

        return {
            "total_qtls": len(qtls),
            "traits_analyzed": len(traits),
            "traits": traits,
            "chromosomes_with_qtls": len(chromosomes),
            "total_pve": round(total_pve, 1),
            "average_lod": round(avg_lod, 2),
            "major_qtls": len([q for q in qtls if q.pve is not None and q.pve >= 15]),
            "minor_qtls": len([q for q in qtls if q.pve is not None and q.pve < 15]),
        }

    async def get_gwas_summary(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> dict[str, Any]:
        """Get summary statistics for GWAS analysis.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering

        Returns:
            Summary statistics dictionary
        """
        gwas_results = await self.get_gwas_results(db, organization_id)

        if not gwas_results:
            return {
                "total_associations": 0,
                "significant_associations": 0,
                "suggestive_associations": 0,
                "traits_analyzed": 0,
                "traits": [],
                "top_association": None,
                "genomic_inflation_factor": 1.0,
            }

        traits = list({g.get("trait") for g in gwas_results if g.get("trait")})
        significant = [g for g in gwas_results if g.get("log_p", 0) >= 5]
        suggestive = [g for g in gwas_results if 4 <= g.get("log_p", 0) < 5]

        top = max(gwas_results, key=lambda x: x.get("log_p", 0)) if gwas_results else None

        return {
            "total_associations": len(gwas_results),
            "significant_associations": len(significant),
            "suggestive_associations": len(suggestive),
            "traits_analyzed": len(traits),
            "traits": traits,
            "top_association": top,
            "genomic_inflation_factor": 1.0,
        }

    async def get_traits(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> list[str]:
        """Get list of available traits.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering

        Returns:
            List of trait names
        """
        qtls = await self.list_qtls(db, organization_id)
        gwas = await self.get_gwas_results(db, organization_id)

        qtl_traits = {q.get("trait") for q in qtls if q.get("trait")}
        gwas_traits = {g.get("trait") for g in gwas if g.get("trait")}

        return sorted(qtl_traits | gwas_traits)

    async def get_populations(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> list[str]:
        """Get list of available mapping populations.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering

        Returns:
            List of population names
        """
        qtls = await self.list_qtls(db, organization_id)
        return sorted({q.get("population") for q in qtls if q.get("population")})

    def _qtl_to_dict(self, qtl: BioQTL) -> dict[str, Any]:
        """Convert QTL model to dictionary."""
        return {
            "qtl_id": getattr(qtl, "qtl_db_id", str(qtl.id)),
            "qtl_name": qtl.qtl_name,
            "trait": qtl.trait,
            "population": qtl.population,
            "method": qtl.method,
            "chromosome": qtl.chromosome,
            "start_position": qtl.start_position,
            "end_position": qtl.end_position,
            "peak_position": qtl.peak_position,
            "lod": qtl.lod,
            "pve": qtl.pve,
            "add_effect": qtl.add_effect,
            "dom_effect": qtl.dom_effect,
            "marker_name": qtl.marker_name,
            "confidence_interval": {
                "low": qtl.confidence_interval_low,
                "high": qtl.confidence_interval_high
            },
            "candidate_genes": qtl.candidate_genes,
            "additional_info": qtl.additional_info
        }

    def _gwas_result_to_dict(self, res: GWASResult, trait: str | None = None) -> dict[str, Any]:
        """Convert GWASResult model to dictionary."""
        d = {
            "marker_name": res.marker_name,
            "chromosome": res.chromosome,
            "position": res.position,
            "p_value": res.p_value,
            "log_p": res.neg_log10_p,
            "effect_size": res.effect_size,
            "standard_error": res.standard_error,
            "maf": res.maf,
            "is_significant": res.is_significant,
        }
        if trait:
            d["trait"] = trait
        return d


# Factory function
def get_qtl_mapping_service() -> QTLMappingService:
    """Get the QTL mapping service instance."""
    return QTLMappingService()

"""
Marker-Assisted Selection (MAS) Service for Plant Breeding
QTL analysis, marker scoring, and selection decisions

Features:
- QTL-marker association
- Marker scoring and genotyping
- Foreground selection (target alleles)
- Background selection (genome recovery)
- Marker-assisted backcrossing (MABC)
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MarkerType(str, Enum):
    SSR = "ssr"
    SNP = "snp"
    INDEL = "indel"
    KASP = "kasp"


class AlleleType(str, Enum):
    FAVORABLE = "favorable"
    UNFAVORABLE = "unfavorable"
    NEUTRAL = "neutral"


@dataclass
class Marker:
    """Molecular marker definition"""
    id: str
    name: str
    chromosome: str
    position: float  # cM or bp
    marker_type: MarkerType
    target_allele: str
    linked_trait: str
    distance_to_qtl: float  # cM

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "chromosome": self.chromosome,
            "position": self.position,
            "marker_type": self.marker_type.value,
            "target_allele": self.target_allele,
            "linked_trait": self.linked_trait,
            "distance_to_qtl_cM": self.distance_to_qtl,
        }


@dataclass
class GenotypeScore:
    """Genotype score for an individual"""
    individual_id: str
    marker_id: str
    allele1: str
    allele2: str
    is_target: bool
    is_heterozygous: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "individual_id": self.individual_id,
            "marker_id": self.marker_id,
            "genotype": f"{self.allele1}/{self.allele2}",
            "is_target_allele": self.is_target,
            "is_heterozygous": self.is_heterozygous,
            "zygosity": "heterozygous" if self.is_heterozygous else "homozygous",
        }


@dataclass
class SelectionResult:
    """Result of marker-assisted selection"""
    individual_id: str
    foreground_score: float  # % target alleles
    background_score: float  # % recurrent parent genome
    overall_score: float
    selected: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "individual_id": self.individual_id,
            "foreground_score_percent": round(self.foreground_score, 1),
            "background_score_percent": round(self.background_score, 1),
            "overall_score": round(self.overall_score, 2),
            "selected": self.selected,
        }


class MarkerAssistedService:
    """
    Marker-Assisted Selection for plant breeding
    """

    def __init__(self):
        self.markers: Dict[str, Marker] = {}
        self.genotypes: Dict[str, Dict[str, GenotypeScore]] = {}  # individual -> marker -> score

    def register_marker(
        self,
        marker_id: str,
        name: str,
        chromosome: str,
        position: float,
        marker_type: str,
        target_allele: str,
        linked_trait: str,
        distance_to_qtl: float = 0.0
    ) -> Marker:
        """
        Register a molecular marker
        
        Args:
            marker_id: Unique marker identifier
            name: Marker name
            chromosome: Chromosome location
            position: Position in cM or bp
            marker_type: Type (SSR, SNP, INDEL, KASP)
            target_allele: Favorable allele
            linked_trait: Associated trait
            distance_to_qtl: Distance to QTL in cM
            
        Returns:
            Registered Marker object
        """
        marker = Marker(
            id=marker_id,
            name=name,
            chromosome=chromosome,
            position=position,
            marker_type=MarkerType(marker_type.lower()),
            target_allele=target_allele,
            linked_trait=linked_trait,
            distance_to_qtl=distance_to_qtl,
        )
        self.markers[marker_id] = marker
        return marker

    def score_genotype(
        self,
        individual_id: str,
        marker_id: str,
        allele1: str,
        allele2: str
    ) -> GenotypeScore:
        """
        Score a genotype for a marker
        
        Args:
            individual_id: Individual identifier
            marker_id: Marker identifier
            allele1: First allele
            allele2: Second allele
            
        Returns:
            GenotypeScore object
        """
        if marker_id not in self.markers:
            raise ValueError(f"Marker {marker_id} not registered")

        marker = self.markers[marker_id]
        target = marker.target_allele

        is_target = (allele1 == target or allele2 == target)
        is_heterozygous = (allele1 != allele2)

        score = GenotypeScore(
            individual_id=individual_id,
            marker_id=marker_id,
            allele1=allele1,
            allele2=allele2,
            is_target=is_target,
            is_heterozygous=is_heterozygous,
        )

        if individual_id not in self.genotypes:
            self.genotypes[individual_id] = {}
        self.genotypes[individual_id][marker_id] = score

        return score

    def bulk_score(
        self,
        genotype_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Bulk score genotypes
        
        Args:
            genotype_data: List of {individual_id, marker_id, allele1, allele2}
            
        Returns:
            Summary of scoring
        """
        scored = 0
        errors = []

        for record in genotype_data:
            try:
                self.score_genotype(
                    individual_id=record["individual_id"],
                    marker_id=record["marker_id"],
                    allele1=record["allele1"],
                    allele2=record["allele2"],
                )
                scored += 1
            except Exception as e:
                errors.append({"record": record, "error": str(e)})

        return {
            "scored": scored,
            "errors": len(errors),
            "error_details": errors[:10],  # First 10 errors
        }

    def foreground_selection(
        self,
        individual_ids: List[str],
        target_markers: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Foreground selection - select for target alleles
        
        Args:
            individual_ids: Individuals to evaluate
            target_markers: Markers linked to target traits
            
        Returns:
            List of individuals with foreground scores
        """
        results = []

        for ind_id in individual_ids:
            if ind_id not in self.genotypes:
                continue

            ind_scores = self.genotypes[ind_id]
            target_count = 0
            total_markers = 0
            marker_details = []

            for marker_id in target_markers:
                if marker_id in ind_scores:
                    total_markers += 1
                    score = ind_scores[marker_id]

                    # Count target alleles (0, 1, or 2)
                    marker = self.markers[marker_id]
                    target = marker.target_allele
                    allele_count = (1 if score.allele1 == target else 0) + \
                                  (1 if score.allele2 == target else 0)
                    target_count += allele_count

                    marker_details.append({
                        "marker": marker_id,
                        "genotype": f"{score.allele1}/{score.allele2}",
                        "target_alleles": allele_count,
                        "trait": marker.linked_trait,
                    })

            # Score as percentage of maximum (2 alleles per marker)
            max_alleles = total_markers * 2
            fg_score = (target_count / max_alleles * 100) if max_alleles > 0 else 0

            results.append({
                "individual_id": ind_id,
                "foreground_score_percent": round(fg_score, 1),
                "target_alleles": target_count,
                "max_alleles": max_alleles,
                "markers_scored": total_markers,
                "marker_details": marker_details,
            })

        # Sort by score
        results.sort(key=lambda x: x["foreground_score_percent"], reverse=True)
        return results

    def background_selection(
        self,
        individual_ids: List[str],
        recurrent_parent_id: str,
        background_markers: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Background selection - select for recurrent parent genome recovery
        
        Args:
            individual_ids: Individuals to evaluate
            recurrent_parent_id: Recurrent parent identifier
            background_markers: Markers for genome-wide coverage
            
        Returns:
            List of individuals with background scores
        """
        if recurrent_parent_id not in self.genotypes:
            return [{"error": f"Recurrent parent {recurrent_parent_id} not genotyped"}]

        rp_genotypes = self.genotypes[recurrent_parent_id]
        results = []

        for ind_id in individual_ids:
            if ind_id not in self.genotypes or ind_id == recurrent_parent_id:
                continue

            ind_scores = self.genotypes[ind_id]
            matching_alleles = 0
            total_alleles = 0

            for marker_id in background_markers:
                if marker_id in ind_scores and marker_id in rp_genotypes:
                    ind_score = ind_scores[marker_id]
                    rp_score = rp_genotypes[marker_id]

                    # Count matching alleles
                    ind_alleles = {ind_score.allele1, ind_score.allele2}
                    rp_alleles = {rp_score.allele1, rp_score.allele2}

                    # For each RP allele, check if present in individual
                    for allele in [rp_score.allele1, rp_score.allele2]:
                        total_alleles += 1
                        if allele in ind_alleles:
                            matching_alleles += 1

            bg_score = (matching_alleles / total_alleles * 100) if total_alleles > 0 else 0

            results.append({
                "individual_id": ind_id,
                "background_score_percent": round(bg_score, 1),
                "matching_alleles": matching_alleles,
                "total_alleles": total_alleles,
                "markers_compared": len([m for m in background_markers
                                        if m in ind_scores and m in rp_genotypes]),
            })

        results.sort(key=lambda x: x["background_score_percent"], reverse=True)
        return results

    def mabc_selection(
        self,
        individual_ids: List[str],
        target_markers: List[str],
        background_markers: List[str],
        recurrent_parent_id: str,
        fg_weight: float = 0.6,
        bg_weight: float = 0.4,
        min_fg_score: float = 50.0,
        min_bg_score: float = 0.0,
        n_select: int = 10
    ) -> Dict[str, Any]:
        """
        Marker-Assisted Backcrossing (MABC) selection
        
        Combines foreground and background selection for optimal
        introgression of target traits while recovering recurrent
        parent genome.
        
        Args:
            individual_ids: Individuals to evaluate
            target_markers: Foreground markers (linked to target traits)
            background_markers: Background markers (genome-wide)
            recurrent_parent_id: Recurrent parent ID
            fg_weight: Weight for foreground score (default 0.6)
            bg_weight: Weight for background score (default 0.4)
            min_fg_score: Minimum foreground score to consider
            min_bg_score: Minimum background score to consider
            n_select: Number of individuals to select
            
        Returns:
            Selection results with rankings
        """
        # Get foreground scores
        fg_results = self.foreground_selection(individual_ids, target_markers)
        fg_scores = {r["individual_id"]: r["foreground_score_percent"] for r in fg_results}

        # Get background scores
        bg_results = self.background_selection(individual_ids, recurrent_parent_id, background_markers)
        bg_scores = {r["individual_id"]: r["background_score_percent"] for r in bg_results}

        # Combine scores
        combined = []
        for ind_id in individual_ids:
            fg = fg_scores.get(ind_id, 0)
            bg = bg_scores.get(ind_id, 0)

            # Apply minimum thresholds
            if fg < min_fg_score or bg < min_bg_score:
                continue

            overall = fg_weight * fg + bg_weight * bg

            combined.append(SelectionResult(
                individual_id=ind_id,
                foreground_score=fg,
                background_score=bg,
                overall_score=overall,
                selected=False,
            ))

        # Sort and select top n
        combined.sort(key=lambda x: x.overall_score, reverse=True)

        for i, result in enumerate(combined[:n_select]):
            result.selected = True

        return {
            "selection_parameters": {
                "fg_weight": fg_weight,
                "bg_weight": bg_weight,
                "min_fg_score": min_fg_score,
                "min_bg_score": min_bg_score,
                "n_select": n_select,
            },
            "n_evaluated": len(individual_ids),
            "n_passed_threshold": len(combined),
            "n_selected": min(n_select, len(combined)),
            "selected": [r.to_dict() for r in combined[:n_select]],
            "not_selected": [r.to_dict() for r in combined[n_select:]],
        }

    def get_marker(self, marker_id: str) -> Optional[Dict[str, Any]]:
        """Get marker details"""
        if marker_id not in self.markers:
            return None
        return self.markers[marker_id].to_dict()

    def list_markers(
        self,
        chromosome: Optional[str] = None,
        trait: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List registered markers"""
        result = []
        for marker in self.markers.values():
            if chromosome and marker.chromosome != chromosome:
                continue
            if trait and marker.linked_trait != trait:
                continue
            result.append(marker.to_dict())
        return sorted(result, key=lambda x: (x["chromosome"], x["position"]))

    def get_individual_genotypes(self, individual_id: str) -> List[Dict[str, Any]]:
        """Get all genotypes for an individual"""
        if individual_id not in self.genotypes:
            return []
        return [score.to_dict() for score in self.genotypes[individual_id].values()]


# Singleton
_mas_service: Optional[MarkerAssistedService] = None


def get_mas_service() -> MarkerAssistedService:
    """Get or create MAS service singleton"""
    global _mas_service
    if _mas_service is None:
        _mas_service = MarkerAssistedService()
    return _mas_service

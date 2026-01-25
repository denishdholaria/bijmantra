"""
Phenotype Analysis Service for Plant Breeding
Statistical analysis of phenotypic data

Features:
- Descriptive statistics
- Heritability estimation
- Genetic correlations
- Selection indices
- Best Linear Unbiased Prediction (BLUP)
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class DescriptiveStats:
    """Descriptive statistics for a trait"""
    trait: str
    n: int
    mean: float
    std: float
    min_val: float
    max_val: float
    cv: float  # Coefficient of variation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trait": self.trait,
            "n": self.n,
            "mean": round(self.mean, 3),
            "std": round(self.std, 3),
            "min": round(self.min_val, 3),
            "max": round(self.max_val, 3),
            "cv_percent": round(self.cv, 2),
            "range": round(self.max_val - self.min_val, 3),
        }


@dataclass
class HeritabilityResult:
    """Heritability estimation result"""
    trait: str
    h2_broad: float  # Broad-sense heritability
    h2_narrow: Optional[float]  # Narrow-sense (if available)
    vg: float  # Genetic variance
    ve: float  # Environmental variance
    vp: float  # Phenotypic variance
    se: float  # Standard error
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "trait": self.trait,
            "heritability_broad_sense": round(self.h2_broad, 3),
            "genetic_variance": round(self.vg, 4),
            "environmental_variance": round(self.ve, 4),
            "phenotypic_variance": round(self.vp, 4),
            "standard_error": round(self.se, 4),
        }
        if self.h2_narrow is not None:
            result["heritability_narrow_sense"] = round(self.h2_narrow, 3)
        return result


@dataclass
class SelectionResponse:
    """Expected response to selection"""
    trait: str
    selection_intensity: float
    heritability: float
    phenotypic_std: float
    expected_gain: float
    percent_gain: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trait": self.trait,
            "selection_intensity": round(self.selection_intensity, 2),
            "heritability": round(self.heritability, 3),
            "phenotypic_std": round(self.phenotypic_std, 3),
            "expected_gain": round(self.expected_gain, 3),
            "percent_gain": round(self.percent_gain, 2),
        }


class PhenotypeAnalysisService:
    """
    Phenotype analysis for plant breeding
    """
    
    def __init__(self):
        pass
    
    def descriptive_stats(
        self,
        values: List[float],
        trait_name: str = "trait"
    ) -> DescriptiveStats:
        """
        Calculate descriptive statistics
        
        Args:
            values: List of phenotypic values
            trait_name: Name of the trait
            
        Returns:
            DescriptiveStats object
        """
        n = len(values)
        if n == 0:
            return DescriptiveStats(trait_name, 0, 0, 0, 0, 0, 0)
        
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / (n - 1) if n > 1 else 0
        std = math.sqrt(variance)
        cv = (std / mean * 100) if mean != 0 else 0
        
        return DescriptiveStats(
            trait=trait_name,
            n=n,
            mean=mean,
            std=std,
            min_val=min(values),
            max_val=max(values),
            cv=cv,
        )
    
    def estimate_heritability(
        self,
        genotype_means: Dict[str, List[float]],
        trait_name: str = "trait"
    ) -> HeritabilityResult:
        """
        Estimate broad-sense heritability from replicated data
        
        H² = Vg / Vp = Vg / (Vg + Ve)
        
        Args:
            genotype_means: Dict of genotype_id -> list of replicate values
            trait_name: Name of the trait
            
        Returns:
            HeritabilityResult with variance components
        """
        # Calculate overall mean
        all_values = []
        for values in genotype_means.values():
            all_values.extend(values)
        
        grand_mean = sum(all_values) / len(all_values)
        
        # Calculate genotype means
        geno_means = {}
        for geno, values in genotype_means.items():
            geno_means[geno] = sum(values) / len(values)
        
        # Number of genotypes and reps
        n_geno = len(genotype_means)
        n_reps = len(list(genotype_means.values())[0])
        
        # Sum of squares
        ss_geno = sum(
            n_reps * (geno_means[g] - grand_mean) ** 2
            for g in genotype_means.keys()
        )
        
        ss_error = sum(
            (v - geno_means[g]) ** 2
            for g, values in genotype_means.items()
            for v in values
        )
        
        # Mean squares
        df_geno = n_geno - 1
        df_error = n_geno * (n_reps - 1)
        
        ms_geno = ss_geno / df_geno if df_geno > 0 else 0
        ms_error = ss_error / df_error if df_error > 0 else 0
        
        # Variance components
        ve = ms_error
        vg = (ms_geno - ms_error) / n_reps if n_reps > 0 else 0
        vg = max(0, vg)  # Can't be negative
        
        vp = vg + ve
        h2 = vg / vp if vp > 0 else 0
        
        # Standard error of heritability
        se = math.sqrt(2 * (1 - h2) ** 2 * (1 + (n_reps - 1) * h2) ** 2 / 
                      (n_reps * (n_reps - 1) * (n_geno - 1))) if n_geno > 1 and n_reps > 1 else 0
        
        return HeritabilityResult(
            trait=trait_name,
            h2_broad=h2,
            h2_narrow=None,
            vg=vg,
            ve=ve,
            vp=vp,
            se=se,
        )
    
    def genetic_correlation(
        self,
        trait1_geno_means: Dict[str, float],
        trait2_geno_means: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate genetic correlation between two traits
        
        rg = Cov(G1, G2) / sqrt(Vg1 * Vg2)
        
        Args:
            trait1_geno_means: Genotype means for trait 1
            trait2_geno_means: Genotype means for trait 2
            
        Returns:
            Genetic correlation and interpretation
        """
        # Get common genotypes
        common_genos = set(trait1_geno_means.keys()) & set(trait2_geno_means.keys())
        
        if len(common_genos) < 3:
            return {"error": "Need at least 3 common genotypes"}
        
        # Extract values for common genotypes
        x = [trait1_geno_means[g] for g in common_genos]
        y = [trait2_geno_means[g] for g in common_genos]
        
        # Calculate correlation
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        cov_xy = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / (n - 1)
        var_x = sum((xi - mean_x) ** 2 for xi in x) / (n - 1)
        var_y = sum((yi - mean_y) ** 2 for yi in y) / (n - 1)
        
        if var_x <= 0 or var_y <= 0:
            return {"error": "Insufficient variance"}
        
        r = cov_xy / math.sqrt(var_x * var_y)
        
        # Interpretation
        if abs(r) >= 0.7:
            strength = "strong"
        elif abs(r) >= 0.4:
            strength = "moderate"
        elif abs(r) >= 0.2:
            strength = "weak"
        else:
            strength = "negligible"
        
        direction = "positive" if r > 0 else "negative"
        
        return {
            "genetic_correlation": round(r, 4),
            "n_genotypes": n,
            "interpretation": f"{strength} {direction} correlation",
            "selection_implication": (
                "Selection for one trait will increase the other" if r > 0.3
                else "Selection for one trait will decrease the other" if r < -0.3
                else "Traits can be selected independently"
            ),
        }
    
    def selection_response(
        self,
        heritability: float,
        phenotypic_std: float,
        selection_proportion: float,
        trait_mean: float,
        trait_name: str = "trait"
    ) -> SelectionResponse:
        """
        Calculate expected response to selection
        
        R = i × h² × σp
        
        Args:
            heritability: Heritability (0-1)
            phenotypic_std: Phenotypic standard deviation
            selection_proportion: Proportion selected (e.g., 0.1 for top 10%)
            trait_mean: Current trait mean
            trait_name: Name of the trait
            
        Returns:
            SelectionResponse with expected gain
        """
        # Selection intensity from proportion
        # Approximation: i ≈ 2.06 - 0.8 * ln(p) for p < 0.5
        if selection_proportion <= 0 or selection_proportion >= 1:
            i = 0
        elif selection_proportion <= 0.5:
            i = 2.06 - 0.8 * math.log(selection_proportion)
        else:
            i = 0.8 * (1 - selection_proportion)
        
        # Response to selection
        r = i * heritability * phenotypic_std
        percent_gain = (r / trait_mean * 100) if trait_mean != 0 else 0
        
        return SelectionResponse(
            trait=trait_name,
            selection_intensity=i,
            heritability=heritability,
            phenotypic_std=phenotypic_std,
            expected_gain=r,
            percent_gain=percent_gain,
        )
    
    def selection_index(
        self,
        traits: List[str],
        phenotypic_values: Dict[str, List[float]],
        economic_weights: List[float],
        heritabilities: List[float]
    ) -> Dict[str, Any]:
        """
        Calculate Smith-Hazel selection index
        
        I = Σ(bi × Pi) where bi are index weights
        
        Args:
            traits: List of trait names
            phenotypic_values: Dict of genotype_id -> list of trait values
            economic_weights: Economic weight for each trait
            heritabilities: Heritability for each trait
            
        Returns:
            Index values and rankings
        """
        n_traits = len(traits)
        
        if len(economic_weights) != n_traits or len(heritabilities) != n_traits:
            return {"error": "Mismatched number of traits, weights, or heritabilities"}
        
        # Simplified index: I = Σ(wi × hi² × (Pi - mean_i) / std_i)
        # Standardize and weight by heritability and economic weight
        
        genotypes = list(phenotypic_values.keys())
        index_values = {}
        
        # Calculate means and stds for each trait
        trait_stats = []
        for i in range(n_traits):
            values = [phenotypic_values[g][i] for g in genotypes]
            mean = sum(values) / len(values)
            std = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
            trait_stats.append({"mean": mean, "std": std})
        
        # Calculate index for each genotype
        for geno in genotypes:
            index = 0
            for i in range(n_traits):
                if trait_stats[i]["std"] > 0:
                    standardized = (phenotypic_values[geno][i] - trait_stats[i]["mean"]) / trait_stats[i]["std"]
                    index += economic_weights[i] * heritabilities[i] * standardized
            index_values[geno] = index
        
        # Rank genotypes
        ranked = sorted(index_values.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "traits": traits,
            "economic_weights": economic_weights,
            "heritabilities": heritabilities,
            "index_values": {g: round(v, 4) for g, v in index_values.items()},
            "ranking": [{"rank": i + 1, "genotype": g, "index": round(v, 4)} 
                       for i, (g, v) in enumerate(ranked)],
        }
    
    def anova_rcbd(
        self,
        data: List[Dict[str, Any]],
        trait: str
    ) -> Dict[str, Any]:
        """
        ANOVA for Randomized Complete Block Design
        
        Args:
            data: List of {genotype, block, value} dicts
            trait: Trait name
            
        Returns:
            ANOVA table with F-test
        """
        # Organize data
        genotypes = list(set(d["genotype"] for d in data))
        blocks = list(set(d["block"] for d in data))
        
        n_geno = len(genotypes)
        n_block = len(blocks)
        n_total = len(data)
        
        # Calculate means
        grand_mean = sum(d["value"] for d in data) / n_total
        
        geno_means = {}
        for g in genotypes:
            values = [d["value"] for d in data if d["genotype"] == g]
            geno_means[g] = sum(values) / len(values)
        
        block_means = {}
        for b in blocks:
            values = [d["value"] for d in data if d["block"] == b]
            block_means[b] = sum(values) / len(values)
        
        # Sum of squares
        ss_total = sum((d["value"] - grand_mean) ** 2 for d in data)
        ss_geno = n_block * sum((geno_means[g] - grand_mean) ** 2 for g in genotypes)
        ss_block = n_geno * sum((block_means[b] - grand_mean) ** 2 for b in blocks)
        ss_error = ss_total - ss_geno - ss_block
        
        # Degrees of freedom
        df_geno = n_geno - 1
        df_block = n_block - 1
        df_error = (n_geno - 1) * (n_block - 1)
        df_total = n_total - 1
        
        # Mean squares
        ms_geno = ss_geno / df_geno if df_geno > 0 else 0
        ms_block = ss_block / df_block if df_block > 0 else 0
        ms_error = ss_error / df_error if df_error > 0 else 0
        
        # F-values
        f_geno = ms_geno / ms_error if ms_error > 0 else 0
        f_block = ms_block / ms_error if ms_error > 0 else 0
        
        # CV
        cv = (math.sqrt(ms_error) / grand_mean * 100) if grand_mean != 0 else 0
        
        return {
            "trait": trait,
            "n_genotypes": n_geno,
            "n_blocks": n_block,
            "grand_mean": round(grand_mean, 3),
            "cv_percent": round(cv, 2),
            "anova_table": {
                "genotype": {
                    "df": df_geno,
                    "ss": round(ss_geno, 4),
                    "ms": round(ms_geno, 4),
                    "f_value": round(f_geno, 2),
                },
                "block": {
                    "df": df_block,
                    "ss": round(ss_block, 4),
                    "ms": round(ms_block, 4),
                    "f_value": round(f_block, 2),
                },
                "error": {
                    "df": df_error,
                    "ss": round(ss_error, 4),
                    "ms": round(ms_error, 4),
                },
                "total": {
                    "df": df_total,
                    "ss": round(ss_total, 4),
                },
            },
            "genotype_means": {g: round(v, 3) for g, v in geno_means.items()},
        }


# Singleton
_phenotype_service: Optional[PhenotypeAnalysisService] = None


def get_phenotype_service() -> PhenotypeAnalysisService:
    """Get or create phenotype analysis service singleton"""
    global _phenotype_service
    if _phenotype_service is None:
        _phenotype_service = PhenotypeAnalysisService()
    return _phenotype_service

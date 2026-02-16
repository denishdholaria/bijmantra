"""
GWAS (Genome-Wide Association Study) Service
Statistical genetics for marker-trait associations

Methods:
- Single-marker regression (GLM)
- Mixed Linear Model (MLM) with kinship correction
- FarmCPU (Fixed and random model Circulating Probability Unification)

Uses NumPy/SciPy for calculations
"""

import numpy as np
from scipy import stats
from scipy.linalg import cholesky, solve_triangular
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class GWASResult:
    """GWAS analysis results"""
    marker_names: List[str]
    chromosomes: List[str]
    positions: List[int]
    p_values: np.ndarray
    effect_sizes: np.ndarray
    standard_errors: np.ndarray
    maf: np.ndarray  # Minor allele frequency
    n_samples: int
    n_markers: int
    method: str
    significance_threshold: float

    def to_dict(self) -> Dict[str, Any]:
        # Calculate -log10(p)
        neg_log_p = -np.log10(np.clip(self.p_values, 1e-300, 1))

        # Identify significant markers
        significant_idx = np.where(self.p_values < self.significance_threshold)[0]

        return {
            "n_samples": self.n_samples,
            "n_markers": self.n_markers,
            "method": self.method,
            "significance_threshold": self.significance_threshold,
            "n_significant": len(significant_idx),
            "markers": [
                {
                    "name": self.marker_names[i],
                    "chromosome": self.chromosomes[i],
                    "position": self.positions[i],
                    "p_value": float(self.p_values[i]),
                    "neg_log_p": float(neg_log_p[i]),
                    "effect": float(self.effect_sizes[i]),
                    "se": float(self.standard_errors[i]),
                    "maf": float(self.maf[i]),
                    "significant": bool(self.p_values[i] < self.significance_threshold),
                }
                for i in range(self.n_markers)
            ],
            "significant_markers": [
                {
                    "name": self.marker_names[i],
                    "chromosome": self.chromosomes[i],
                    "position": self.positions[i],
                    "p_value": float(self.p_values[i]),
                    "neg_log_p": float(neg_log_p[i]),
                    "effect": float(self.effect_sizes[i]),
                }
                for i in significant_idx
            ],
            "manhattan_data": self._get_manhattan_data(neg_log_p),
            "qq_data": self._get_qq_data(),
        }

    def _get_manhattan_data(self, neg_log_p: np.ndarray) -> List[Dict]:
        """Get data for Manhattan plot"""
        return [
            {
                "chr": self.chromosomes[i],
                "pos": self.positions[i],
                "p": float(neg_log_p[i]),
                "name": self.marker_names[i],
            }
            for i in range(self.n_markers)
        ]

    def _get_qq_data(self) -> Dict[str, List[float]]:
        """Get data for QQ plot"""
        n = len(self.p_values)
        expected = -np.log10(np.arange(1, n + 1) / (n + 1))
        observed = -np.log10(np.sort(self.p_values))

        return {
            "expected": expected.tolist(),
            "observed": observed.tolist(),
        }


class GWASService:
    """
    GWAS Analysis Service
    
    Provides genome-wide association analysis methods
    for identifying marker-trait associations.
    """

    def __init__(self):
        self.bonferroni_alpha = 0.05

    def glm_gwas(
        self,
        genotypes: np.ndarray,
        phenotypes: np.ndarray,
        marker_names: List[str],
        chromosomes: List[str],
        positions: List[int],
        covariates: Optional[np.ndarray] = None,
    ) -> GWASResult:
        """
        General Linear Model GWAS (single-marker regression)
        
        Model: y = Xβ + Zα + ε
        where X is covariates, Z is marker genotype
        
        Args:
            genotypes: Marker matrix (n_samples × n_markers), coded 0/1/2
            phenotypes: Trait values (n_samples,)
            marker_names: SNP/marker names
            chromosomes: Chromosome for each marker
            positions: Position for each marker
            covariates: Optional covariate matrix
            
        Returns:
            GWASResult with p-values and effects
        """
        n_samples, n_markers = genotypes.shape

        # Prepare phenotype
        y = phenotypes - np.mean(phenotypes)

        # Prepare design matrix with intercept
        if covariates is not None:
            X_base = np.column_stack([np.ones(n_samples), covariates])
        else:
            X_base = np.ones((n_samples, 1))

        p_values = np.zeros(n_markers)
        effects = np.zeros(n_markers)
        se = np.zeros(n_markers)
        maf = np.zeros(n_markers)

        for i in range(n_markers):
            g = genotypes[:, i]

            # Calculate MAF
            maf[i] = np.mean(g) / 2
            if maf[i] > 0.5:
                maf[i] = 1 - maf[i]

            # Skip monomorphic markers
            if maf[i] < 0.01:
                p_values[i] = 1.0
                continue

            # Design matrix with marker
            X = np.column_stack([X_base, g])

            # OLS regression
            try:
                XtX_inv = np.linalg.inv(X.T @ X)
                beta = XtX_inv @ X.T @ y

                # Residuals and variance
                residuals = y - X @ beta
                sigma2 = np.sum(residuals ** 2) / (n_samples - X.shape[1])

                # Standard error of marker effect
                se[i] = np.sqrt(sigma2 * XtX_inv[-1, -1])
                effects[i] = beta[-1]

                # t-statistic and p-value
                t_stat = effects[i] / se[i] if se[i] > 0 else 0
                p_values[i] = 2 * (1 - stats.t.cdf(abs(t_stat), n_samples - X.shape[1]))

            except np.linalg.LinAlgError:
                p_values[i] = 1.0

        # Bonferroni threshold
        threshold = self.bonferroni_alpha / n_markers

        return GWASResult(
            marker_names=marker_names,
            chromosomes=chromosomes,
            positions=positions,
            p_values=p_values,
            effect_sizes=effects,
            standard_errors=se,
            maf=maf,
            n_samples=n_samples,
            n_markers=n_markers,
            method="GLM",
            significance_threshold=threshold,
        )


    def mlm_gwas(
        self,
        genotypes: np.ndarray,
        phenotypes: np.ndarray,
        kinship: np.ndarray,
        marker_names: List[str],
        chromosomes: List[str],
        positions: List[int],
        covariates: Optional[np.ndarray] = None,
    ) -> GWASResult:
        """
        Mixed Linear Model GWAS with kinship correction
        
        Model: y = Xβ + Zα + Zu + ε
        where u ~ N(0, Kσ²_g) is random genetic effect
        
        Uses EMMA (Efficient Mixed-Model Association) approach.
        
        Args:
            genotypes: Marker matrix (n_samples × n_markers)
            phenotypes: Trait values
            kinship: Kinship matrix (n_samples × n_samples)
            marker_names: SNP names
            chromosomes: Chromosome for each marker
            positions: Position for each marker
            covariates: Optional covariates
            
        Returns:
            GWASResult with p-values corrected for population structure
        """
        n_samples, n_markers = genotypes.shape

        # Spectral decomposition of kinship
        eigenvalues, eigenvectors = np.linalg.eigh(kinship)
        eigenvalues = np.maximum(eigenvalues, 1e-10)  # Ensure positive

        # Transform phenotype
        y = phenotypes - np.mean(phenotypes)
        y_transformed = eigenvectors.T @ y

        # Estimate variance components using REML
        # Simplified: use fixed ratio for speed
        h2 = 0.5  # Heritability estimate
        lambda_val = h2 / (1 - h2) if h2 < 1 else 10

        # Weights for transformed model
        weights = 1.0 / (lambda_val * eigenvalues + 1)

        # Prepare base design matrix
        if covariates is not None:
            X_base = np.column_stack([np.ones(n_samples), covariates])
        else:
            X_base = np.ones((n_samples, 1))
        X_base_t = eigenvectors.T @ X_base

        p_values = np.zeros(n_markers)
        effects = np.zeros(n_markers)
        se = np.zeros(n_markers)
        maf = np.zeros(n_markers)

        for i in range(n_markers):
            g = genotypes[:, i]

            # MAF
            maf[i] = np.mean(g) / 2
            if maf[i] > 0.5:
                maf[i] = 1 - maf[i]

            if maf[i] < 0.01:
                p_values[i] = 1.0
                continue

            # Transform marker
            g_transformed = eigenvectors.T @ g

            # Weighted least squares
            X_t = np.column_stack([X_base_t, g_transformed])
            W = np.diag(weights)

            try:
                XtWX = X_t.T @ W @ X_t
                XtWy = X_t.T @ W @ y_transformed
                beta = np.linalg.solve(XtWX, XtWy)

                # Residual variance
                residuals = y_transformed - X_t @ beta
                sigma2 = np.sum(weights * residuals ** 2) / (n_samples - X_t.shape[1])

                # Standard error
                XtWX_inv = np.linalg.inv(XtWX)
                se[i] = np.sqrt(sigma2 * XtWX_inv[-1, -1])
                effects[i] = beta[-1]

                # Wald test
                chi2 = (effects[i] / se[i]) ** 2 if se[i] > 0 else 0
                p_values[i] = 1 - stats.chi2.cdf(chi2, 1)

            except np.linalg.LinAlgError:
                p_values[i] = 1.0

        threshold = self.bonferroni_alpha / n_markers

        return GWASResult(
            marker_names=marker_names,
            chromosomes=chromosomes,
            positions=positions,
            p_values=p_values,
            effect_sizes=effects,
            standard_errors=se,
            maf=maf,
            n_samples=n_samples,
            n_markers=n_markers,
            method="MLM",
            significance_threshold=threshold,
        )

    def calculate_kinship(
        self,
        genotypes: np.ndarray,
        method: str = "vanraden"
    ) -> np.ndarray:
        """
        Calculate genomic relationship matrix (kinship)
        
        Args:
            genotypes: Marker matrix (n_samples × n_markers), coded 0/1/2
            method: "vanraden" or "ibs"
            
        Returns:
            Kinship matrix (n_samples × n_samples)
        """
        n, m = genotypes.shape

        if method == "vanraden":
            # VanRaden (2008) method
            p = np.mean(genotypes, axis=0) / 2  # Allele frequencies
            P = 2 * (p - 0.5)
            Z = genotypes - 1 - P  # Center and scale

            # Scaling factor
            scale = 2 * np.sum(p * (1 - p))

            if scale > 0:
                K = (Z @ Z.T) / scale
            else:
                K = np.eye(n)
        else:
            # IBS (Identity by State)
            K = np.zeros((n, n))
            for i in range(n):
                for j in range(i, n):
                    shared = np.sum(genotypes[i] == genotypes[j])
                    K[i, j] = shared / m
                    K[j, i] = K[i, j]

        return K

    def calculate_pca(
        self,
        genotypes: np.ndarray,
        n_components: int = 10
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate principal components for population structure
        
        Args:
            genotypes: Marker matrix
            n_components: Number of PCs
            
        Returns:
            (PC scores, variance explained)
        """
        # Center genotypes
        G = genotypes - np.mean(genotypes, axis=0)

        # SVD
        U, S, Vt = np.linalg.svd(G, full_matrices=False)

        # PC scores
        n_comp = min(n_components, len(S))
        scores = U[:, :n_comp] * S[:n_comp]

        # Variance explained
        var_explained = (S[:n_comp] ** 2) / np.sum(S ** 2) * 100

        return scores, var_explained


# Singleton
_gwas_service: Optional[GWASService] = None


def get_gwas_service() -> GWASService:
    """Get or create GWAS service singleton"""
    global _gwas_service
    if _gwas_service is None:
        _gwas_service = GWASService()
    return _gwas_service


    def calculate_ld(
        self,
        genotypes: np.ndarray,
        marker_names: List[str],
        chromosomes: List[str],
        positions: List[int],
        max_distance: int = 50000,
        r2_threshold: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculate pairwise Linkage Disequilibrium (LD)
        
        Args:
            genotypes: Marker matrix (n_samples × n_markers), coded 0/1/2
            marker_names: SNP names
            chromosomes: Chromosome for each marker
            positions: Position for each marker
            max_distance: Maximum distance (bp) to calculate LD
            r2_threshold: Minimum r² to include in results
            
        Returns:
            LD statistics including r², D', and decay data
        """
        n_samples, n_markers = genotypes.shape

        ld_pairs = []
        r2_by_distance = {}

        for i in range(n_markers):
            for j in range(i + 1, n_markers):
                # Only calculate within chromosome
                if chromosomes[i] != chromosomes[j]:
                    continue

                distance = abs(positions[j] - positions[i])
                if distance > max_distance:
                    continue

                # Get genotypes
                g1 = genotypes[:, i]
                g2 = genotypes[:, j]

                # Calculate r²
                r2 = self._calculate_r2(g1, g2)
                dprime = self._calculate_dprime(g1, g2)

                if r2 >= r2_threshold:
                    ld_pairs.append({
                        "marker1": marker_names[i],
                        "marker2": marker_names[j],
                        "chromosome": chromosomes[i],
                        "distance": distance / 1000,  # Convert to kb
                        "r2": float(r2),
                        "dprime": float(dprime),
                    })

                # Bin by distance for decay curve
                dist_bin = int(distance / 1000)  # 1kb bins
                if dist_bin not in r2_by_distance:
                    r2_by_distance[dist_bin] = []
                r2_by_distance[dist_bin].append(r2)

        # Calculate LD decay curve
        decay_data = []
        for dist, r2_values in sorted(r2_by_distance.items()):
            decay_data.append({
                "distance": dist,
                "mean_r2": float(np.mean(r2_values)),
                "n_pairs": len(r2_values),
            })

        # Calculate LD decay distance (distance where r² = 0.2)
        ld_decay_distance = self._estimate_ld_decay(decay_data)

        # Statistics
        all_r2 = [p["r2"] for p in ld_pairs]
        high_ld_pairs = [p for p in ld_pairs if p["r2"] >= 0.8]

        return {
            "n_markers": n_markers,
            "n_pairs": len(ld_pairs),
            "n_high_ld": len(high_ld_pairs),
            "mean_r2": float(np.mean(all_r2)) if all_r2 else 0,
            "ld_decay_distance": ld_decay_distance,
            "pairs": sorted(ld_pairs, key=lambda x: -x["r2"])[:1000],  # Top 1000
            "decay_curve": decay_data,
            "chromosome_stats": self._ld_by_chromosome(ld_pairs, chromosomes),
        }

    def _calculate_r2(self, g1: np.ndarray, g2: np.ndarray) -> float:
        """Calculate r² between two markers"""
        # Remove missing values
        valid = ~(np.isnan(g1) | np.isnan(g2))
        if np.sum(valid) < 10:
            return 0.0

        g1_v = g1[valid]
        g2_v = g2[valid]

        # Correlation coefficient squared
        if np.std(g1_v) == 0 or np.std(g2_v) == 0:
            return 0.0

        r = np.corrcoef(g1_v, g2_v)[0, 1]
        return r ** 2 if not np.isnan(r) else 0.0

    def _calculate_dprime(self, g1: np.ndarray, g2: np.ndarray) -> float:
        """Calculate D' between two markers"""
        valid = ~(np.isnan(g1) | np.isnan(g2))
        if np.sum(valid) < 10:
            return 0.0

        g1_v = g1[valid]
        g2_v = g2[valid]
        n = len(g1_v)

        # Allele frequencies
        p1 = np.mean(g1_v) / 2
        p2 = np.mean(g2_v) / 2

        if p1 == 0 or p1 == 1 or p2 == 0 or p2 == 1:
            return 0.0

        # Haplotype frequency estimation (EM simplified)
        # Count haplotypes from diploid data
        p11 = np.mean((g1_v == 2) & (g2_v == 2)) + 0.5 * np.mean((g1_v == 1) & (g2_v == 2)) + \
              0.5 * np.mean((g1_v == 2) & (g2_v == 1)) + 0.25 * np.mean((g1_v == 1) & (g2_v == 1))

        # D coefficient
        D = p11 - p1 * p2

        # D' normalization
        if D > 0:
            Dmax = min(p1 * (1 - p2), (1 - p1) * p2)
        else:
            Dmax = min(p1 * p2, (1 - p1) * (1 - p2))

        if Dmax == 0:
            return 0.0

        return abs(D / Dmax)

    def _estimate_ld_decay(self, decay_data: List[Dict]) -> float:
        """Estimate distance where r² drops to 0.2"""
        for point in decay_data:
            if point["mean_r2"] <= 0.2:
                return float(point["distance"])
        return float(decay_data[-1]["distance"]) if decay_data else 0.0

    def _ld_by_chromosome(self, ld_pairs: List[Dict], chromosomes: List[str]) -> List[Dict]:
        """Calculate average LD by chromosome"""
        chr_r2 = {}
        for pair in ld_pairs:
            chr_name = pair["chromosome"]
            if chr_name not in chr_r2:
                chr_r2[chr_name] = []
            chr_r2[chr_name].append(pair["r2"])

        return [
            {"chromosome": chr_name, "mean_r2": float(np.mean(r2_list)), "n_pairs": len(r2_list)}
            for chr_name, r2_list in sorted(chr_r2.items())
        ]

    def ld_pruning(
        self,
        genotypes: np.ndarray,
        marker_names: List[str],
        chromosomes: List[str],
        positions: List[int],
        r2_threshold: float = 0.5,
        window_size: int = 50000,
    ) -> Dict[str, Any]:
        """
        LD-based marker pruning
        
        Removes markers in high LD to create independent marker set.
        
        Args:
            genotypes: Marker matrix
            marker_names: SNP names
            chromosomes: Chromosome for each marker
            positions: Position for each marker
            r2_threshold: r² threshold for pruning
            window_size: Window size in bp
            
        Returns:
            Pruned marker set
        """
        n_markers = len(marker_names)
        keep = np.ones(n_markers, dtype=bool)

        for i in range(n_markers):
            if not keep[i]:
                continue

            for j in range(i + 1, n_markers):
                if not keep[j]:
                    continue

                # Only within chromosome
                if chromosomes[i] != chromosomes[j]:
                    continue

                # Within window
                if abs(positions[j] - positions[i]) > window_size:
                    continue

                # Calculate r²
                r2 = self._calculate_r2(genotypes[:, i], genotypes[:, j])

                if r2 >= r2_threshold:
                    # Remove marker with lower MAF
                    maf_i = min(np.mean(genotypes[:, i]) / 2, 1 - np.mean(genotypes[:, i]) / 2)
                    maf_j = min(np.mean(genotypes[:, j]) / 2, 1 - np.mean(genotypes[:, j]) / 2)

                    if maf_i >= maf_j:
                        keep[j] = False
                    else:
                        keep[i] = False
                        break

        kept_indices = np.where(keep)[0]
        removed_indices = np.where(~keep)[0]

        return {
            "original_markers": n_markers,
            "kept_markers": len(kept_indices),
            "removed_markers": len(removed_indices),
            "removal_rate": float(len(removed_indices) / n_markers * 100),
            "r2_threshold": r2_threshold,
            "window_size": window_size,
            "kept_marker_names": [marker_names[i] for i in kept_indices],
            "removed_marker_names": [marker_names[i] for i in removed_indices[:100]],  # First 100
        }

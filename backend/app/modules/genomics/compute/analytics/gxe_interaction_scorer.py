"""
GxE Interaction Scorer (Matrix Calculator)

This service provides a suite of methods for calculating stability statistics and interaction matrices
for Genotype-by-Environment (GxE) analysis. It is designed to be used in conjunction with
the Analytics Engine and other statistical services.

Implements the following stability metrics:
- Wricke's Ecovalence (Wi)
- Shukla's Stability Variance (σ²i)
- Lin & Binns' Cultivar Superiority Measure (Pi)
- Kang's Yield-Stability Statistic (YSi)
- Interaction Matrix (GEij)

References:
- Wricke, G. (1962). Über eine Methode zur Erfassung der ökologischen Streubreite in Feldversuchen.
- Shukla, G. K. (1972). Some statistical aspects of partitioning genotype-environmental components of variability.
- Lin, C. S., & Binns, M. R. (1988). A superiority measure of cultivar performance for cultivar x location data.
- Kang, M. S. (1993). Simultaneous selection for yield and stability in crop performance trials.
"""

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class GxEScores:
    """Container for GxE stability scores."""
    wricke_ecovalence: dict[str, float]
    shukla_stability: dict[str, float]
    lin_binns_superiority: dict[str, float]
    kang_rank_sum: dict[str, float]
    interaction_matrix: np.ndarray
    genotype_names: list[str]
    environment_names: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "wricke_ecovalence": self.wricke_ecovalence,
            "shukla_stability": self.shukla_stability,
            "lin_binns_superiority": self.lin_binns_superiority,
            "kang_rank_sum": self.kang_rank_sum,
            "interaction_matrix": self.interaction_matrix.tolist(),
            "genotype_names": self.genotype_names,
            "environment_names": self.environment_names,
        }


class GxEInteractionScorer:
    """
    Calculator for Genotype-by-Environment (GxE) Interaction Matrices and Stability Statistics.
    """

    def calculate_interaction_matrix(self, yield_matrix: np.ndarray) -> np.ndarray:
        """
        Calculate the GxE Interaction Matrix (GE).

        Formula:
            GE_ij = Y_ij - Y_i. - Y_.j + Y_..
            where:
            Y_ij = Yield of genotype i in environment j
            Y_i. = Mean yield of genotype i across all environments
            Y_.j = Mean yield of environment j across all genotypes
            Y_.. = Grand mean yield

        Args:
            yield_matrix: A 2D numpy array of shape (n_genotypes, n_environments) containing yield values.

        Returns:
            A 2D numpy array representing the interaction effects.
        """
        if yield_matrix.size == 0:
            return np.empty_like(yield_matrix)

        grand_mean = np.mean(yield_matrix)
        genotype_means = np.mean(yield_matrix, axis=1, keepdims=True)
        environment_means = np.mean(yield_matrix, axis=0, keepdims=True)

        # Interaction = Cell - Genotype Mean - Environment Mean + Grand Mean
        interaction_matrix = yield_matrix - genotype_means - environment_means + grand_mean
        return interaction_matrix

    def calculate_wricke_ecovalence(
        self,
        yield_matrix: np.ndarray,
        genotype_names: list[str]
    ) -> dict[str, float]:
        """
        Calculate Wricke's Ecovalence (Wi).

        Formula:
            Wi = Σ_j (GE_ij)^2
            where GE_ij is the interaction effect of genotype i in environment j.

        Interpretation:
            Lower Wi indicates higher stability (less contribution to GxE interaction).

        Args:
            yield_matrix: (n_genotypes, n_environments) yield array.
            genotype_names: List of genotype names corresponding to rows.

        Returns:
            Dictionary mapping genotype names to Wi values.
        """
        interaction_matrix = self.calculate_interaction_matrix(yield_matrix)

        # Sum of squares of interaction effects for each genotype (row)
        wi_values = np.sum(interaction_matrix**2, axis=1)

        return dict(zip(genotype_names, wi_values.tolist(), strict=False))

    def calculate_shukla_stability(
        self,
        yield_matrix: np.ndarray,
        genotype_names: list[str]
    ) -> dict[str, float]:
        """
        Calculate Shukla's Stability Variance (σ²i).

        Formula:
            σ²_i = [p / ((p-2)(q-1))] * Wi - [SS(GE) / ((p-1)(p-2)(q-1))]
            where:
            p = number of genotypes
            q = number of environments
            Wi = Wricke's Ecovalence for genotype i
            SS(GE) = Σ_i Σ_j (GE_ij)^2 = Σ_i Wi

        Interpretation:
            Lower σ²i indicates higher stability.
            It is an unbiased estimate of the variance of genotype i across environments after removing main effects.

        Args:
            yield_matrix: (n_genotypes, n_environments) yield array.
            genotype_names: List of genotype names corresponding to rows.

        Returns:
            Dictionary mapping genotype names to σ²i values.
        """
        p, q = yield_matrix.shape

        if p < 3 or q < 2:
            # Cannot calculate if p < 3 (denominator p-2 becomes 0 or negative)
            # Cannot calculate if q < 2 (denominator q-1 becomes 0)
            logger.warning(f"Insufficient dimensions for Shukla's stability: p={p}, q={q}. Returning zeros.")
            return {name: 0.0 for name in genotype_names}

        # Calculate Wi first
        wi_dict = self.calculate_wricke_ecovalence(yield_matrix, genotype_names)
        wi_values = np.array([wi_dict[name] for name in genotype_names])

        ss_ge = np.sum(wi_values)

        # Calculate σ²i
        term1 = (p * wi_values) / ((p - 2) * (q - 1))
        term2 = ss_ge / ((p - 1) * (p - 2) * (q - 1))

        sigma2_i = term1 - term2

        # Stability variance shouldn't be negative theoretically, but can be due to estimation
        sigma2_i = np.maximum(sigma2_i, 0.0)

        return dict(zip(genotype_names, sigma2_i.tolist(), strict=False))

    def calculate_lin_binns_superiority(
        self,
        yield_matrix: np.ndarray,
        genotype_names: list[str]
    ) -> dict[str, float]:
        """
        Calculate Lin & Binns' Cultivar Superiority Measure (Pi).

        Formula:
            Pi = Σ_j (Y_ij - M_j)^2 / (2 * q)
            where:
            Y_ij = Yield of genotype i in environment j
            M_j = Maximum yield in environment j
            q = number of environments

        Interpretation:
            Lower Pi indicates superior performance (closer to the maximum yield in each environment).
            Combines yield and stability.

        Args:
            yield_matrix: (n_genotypes, n_environments) yield array.
            genotype_names: List of genotype names corresponding to rows.

        Returns:
            Dictionary mapping genotype names to Pi values.
        """
        q = yield_matrix.shape[1]
        if q == 0:
             return {name: 0.0 for name in genotype_names}

        # Max yield in each environment (column max)
        max_yields = np.max(yield_matrix, axis=0)

        # Calculate squared differences from max
        squared_diffs = (yield_matrix - max_yields)**2

        # Sum across environments and divide by 2q
        pi_values = np.sum(squared_diffs, axis=1) / (2 * q)

        return dict(zip(genotype_names, pi_values.tolist(), strict=False))

    def calculate_kang_rank_sum(
        self,
        yield_matrix: np.ndarray,
        genotype_names: list[str],
        weight_yield: int = 1,
        weight_stability: int = 1
    ) -> dict[str, float]:
        """
        Calculate Kang's Rank-Sum (Yield-Stability Statistic, YSi).

        Method:
        1. Rank genotypes by mean yield (highest yield = rank 1, or highest rank value depending on convention.
           Here, we assign Rank 1 to best performace).
           Wait, Kang sums the ranks. Usually Rank 1 is best.
           Let's use: Highest Yield -> Rank 1. Lowest Shukla Variance -> Rank 1.
           YSi = Rank(Yield) + Rank(Stability Variance).
        Interpretation:
            Lower YSi indicates better combined yield and stability.

        Args:
            yield_matrix: (n_genotypes, n_environments) yield array.
            genotype_names: List of genotype names corresponding to rows.
            weight_yield: Weight for yield rank (default 1).
            weight_stability: Weight for stability rank (default 1).

        Returns:
            Dictionary mapping genotype names to YSi values (Sum of Ranks).
        """
        p = yield_matrix.shape[0]
        if p == 0:
            return {}

        # 1. Mean Yield Rank
        mean_yields = np.mean(yield_matrix, axis=1)
        # argsort gives indices that sort the array.
        # To get ranks (1=highest), we sort descending.
        # Example: [10, 30, 20] -> argsort: [0, 2, 1] (asc) -> [1, 2, 0] (desc)?
        # scipy.stats.rankdata is useful but let's stick to numpy.
        # Rank 1 = Highest.
        # Sort indices by value descending
        sorted_indices_yield = np.argsort(mean_yields)[::-1]
        ranks_yield = np.empty(p)
        # Assign rank i+1 to the genotype at sorted_indices[i]
        ranks_yield[sorted_indices_yield] = np.arange(1, p + 1)

        # 2. Stability Variance Rank
        shukla_values = self.calculate_shukla_stability(yield_matrix, genotype_names)
        sigma2_array = np.array([shukla_values[name] for name in genotype_names])

        # Lower sigma2 is better (Rank 1 = Lowest)
        sorted_indices_stability = np.argsort(sigma2_array) # asc
        ranks_stability = np.empty(p)
        ranks_stability[sorted_indices_stability] = np.arange(1, p + 1)

        # 3. Sum Ranks
        ysi_values = (weight_yield * ranks_yield) + (weight_stability * ranks_stability)

        return dict(zip(genotype_names, ysi_values.tolist(), strict=False))

    def calculate_all_scores(
        self,
        yield_matrix: np.ndarray,
        genotype_names: list[str],
        environment_names: list[str]
    ) -> GxEScores:
        """
        Calculate all implemented GxE stability scores.

        Args:
            yield_matrix: (n_genotypes, n_environments) yield array.
            genotype_names: List of genotype names.
            environment_names: List of environment names.

        Returns:
            GxEScores object containing all results.
        """
        if yield_matrix.shape != (len(genotype_names), len(environment_names)):
            raise ValueError("Yield matrix shape does not match names lists dimensions.")

        interaction_matrix = self.calculate_interaction_matrix(yield_matrix)
        wricke = self.calculate_wricke_ecovalence(yield_matrix, genotype_names)
        shukla = self.calculate_shukla_stability(yield_matrix, genotype_names)
        lin_binns = self.calculate_lin_binns_superiority(yield_matrix, genotype_names)
        kang = self.calculate_kang_rank_sum(yield_matrix, genotype_names)

        return GxEScores(
            wricke_ecovalence=wricke,
            shukla_stability=shukla,
            lin_binns_superiority=lin_binns,
            kang_rank_sum=kang,
            interaction_matrix=interaction_matrix,
            genotype_names=genotype_names,
            environment_names=environment_names
        )

# Singleton instance
gxe_interaction_scorer = GxEInteractionScorer()

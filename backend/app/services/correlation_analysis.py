"""
Correlation Analysis Service

Computes pairwise trait correlations with p-values.
Supports Pearson (parametric) and Spearman (rank-based).
"""

import numpy as np
from typing import Dict, Any, List, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class CorrelationAnalysisService:
    """
    Pairwise correlation analysis with statistical significance.
    """

    def pearson_with_pvalue(
        self, x: np.ndarray, y: np.ndarray
    ) -> Dict[str, float]:
        """
        Pearson correlation with p-value.

        Args:
            x, y: 1D arrays of equal length

        Returns:
            Dict with r, p_value, n
        """
        mask = ~(np.isnan(x) | np.isnan(y))
        x_clean = x[mask]
        y_clean = y[mask]
        n = len(x_clean)

        if n < 3:
            return {"r": 0.0, "p_value": 1.0, "n": n}

        r, p = stats.pearsonr(x_clean, y_clean)
        return {"r": float(r), "p_value": float(p), "n": int(n)}

    def spearman_with_pvalue(
        self, x: np.ndarray, y: np.ndarray
    ) -> Dict[str, float]:
        """
        Spearman rank correlation with p-value.
        """
        mask = ~(np.isnan(x) | np.isnan(y))
        x_clean = x[mask]
        y_clean = y[mask]
        n = len(x_clean)

        if n < 3:
            return {"rho": 0.0, "p_value": 1.0, "n": n}

        rho, p = stats.spearmanr(x_clean, y_clean)
        return {"rho": float(rho), "p_value": float(p), "n": int(n)}

    def correlation_matrix(
        self,
        data: Dict[str, np.ndarray],
        method: str = "pearson",
    ) -> Dict[str, Any]:
        """
        Compute full pairwise correlation matrix with p-values.

        Args:
            data: Dict of {trait_name: values_array}
            method: 'pearson' or 'spearman'

        Returns:
            Dict with r_matrix, p_matrix, trait_names
        """
        traits = list(data.keys())
        n_traits = len(traits)

        r_matrix = np.ones((n_traits, n_traits))
        p_matrix = np.zeros((n_traits, n_traits))

        corr_fn = self.pearson_with_pvalue if method == "pearson" else self.spearman_with_pvalue
        r_key = "r" if method == "pearson" else "rho"

        for i in range(n_traits):
            for j in range(i + 1, n_traits):
                result = corr_fn(data[traits[i]], data[traits[j]])
                r_val = result[r_key]
                p_val = result["p_value"]

                r_matrix[i, j] = r_val
                r_matrix[j, i] = r_val
                p_matrix[i, j] = p_val
                p_matrix[j, i] = p_val

        # Significance stars
        sig_matrix = []
        for i in range(n_traits):
            row = []
            for j in range(n_traits):
                p = p_matrix[i, j]
                if i == j:
                    row.append("")
                elif p < 0.001:
                    row.append("***")
                elif p < 0.01:
                    row.append("**")
                elif p < 0.05:
                    row.append("*")
                else:
                    row.append("ns")
            sig_matrix.append(row)

        return {
            "trait_names": traits,
            "r_matrix": r_matrix.tolist(),
            "p_matrix": p_matrix.tolist(),
            "significance": sig_matrix,
            "method": method,
            "n_traits": n_traits,
        }


# Singleton
correlation_analysis_service = CorrelationAnalysisService()

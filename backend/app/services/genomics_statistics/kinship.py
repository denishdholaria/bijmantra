"""
Kinship Matrix Calculation Service
Ported from MrBeanApp (R/sommer) for Bijmantra.
Implements VanRaden (2008) Method 1.
"""

import numpy as np
import logging
from typing import Optional, Union, Dict, Any

logger = logging.getLogger(__name__)

def calculate_vanraden_kinship(
    genotype_matrix: np.ndarray,
    check_maf: bool = True
) -> Dict[str, Any]:
    """
    Calculate Genomic Relationship Matrix (Kinship/G-Matrix) using VanRaden Method 1.
    
    Port logic from: MrBeanApp/R/GBLUP.R -> adj_vanraden + sommer::A.mat
    
    Args:
        genotype_matrix (np.ndarray): (n_samples x n_markers) matrix.
                                      Values must be {-1, 0, 1} or {0, 1, 2}.
                                      (Heterozygotes must be the middle value).
    
    Returns:
        Dict containing:
            - K (np.ndarray): n x n Kinship matrix
            - denominator (float): Scaling factor
            - maf_report (dict): Minor Allele Frequency stats
    """
    try:
        M = np.array(genotype_matrix, dtype=float)
        n_ind, n_markers = M.shape

        # 1. Check coding and standardize to {0, 1, 2} if needed
        # Assuming input might be {-1, 0, 1} which is common in R/sommer
        # If min is -1, shift to 0, 1, 2?
        # VanRaden formula typically works on centered Z matrix.
        # Let's assess the data range.

        unique_vals = np.unique(M[~np.isnan(M)])
        logger.info(f"Genotype matrix unique values: {unique_vals}")

        # Heuristic: If values contain -1, assume {-1, 0, 1}.
        # Standardize for MAF calculation.
        # Let's just work with the matrix 'M' as the dosage matrix (0, 1, 2)
        # If input is -1, 0, 1 -> add 1 to make it 0, 1, 2
        if -1 in unique_vals:
            M = M + 1

        # 2. Impute missing values (Naive mean imputation)
        # R's A.mat does this automatically.
        col_means = np.nanmean(M, axis=0)
        inds = np.where(np.isnan(M))
        M[inds] = np.take(col_means, inds[1])

        # 3. Calculate Allele Frequencies (p)
        # p = sum(x) / (2n)
        p = np.mean(M, axis=0) / 2.0

        # 4. Construct Z matrix (Centered Genotypes)
        # Z = M - P
        # P = 2(p - 0.5) if range is -1..1? No.
        # VanRaden: Z = M - 2p
        # M is dosage (0..2), 2p is expected dosage.

        # Matrix of 2p values (n x m)
        P = 2 * p
        Z = M - P

        # 5. Calculate Denominator (Scaling Factor)
        # 2 * sum(p * (1-p))
        denominator = 2 * np.sum(p * (1 - p))

        if denominator == 0:
            logger.warning("Denominator is 0. Monomorphic markers? Using 1 to avoid NaN.")
            denominator = 1.0

        # 6. Calculate K
        # K = Z Z' / denominator
        K = np.dot(Z, Z.T) / denominator

        return {
            "success": True,
            "K": K.tolist(), # Convert to list for JSON serialization if needed
            "denominator": denominator,
            "marker_count": n_markers,
            "sample_count": n_ind
        }

    except Exception as e:
        logger.error(f"Kinship calculation failed: {str(e)}")
        return {"success": False, "error": str(e)}

def calculate_inbreeding(
    kinship_matrix: np.ndarray,
) -> Dict[str, Any]:
    """
    Extract inbreeding coefficients from genomic kinship matrix.

    Inbreeding Coefficient:
        F_i = K_{ii} - 1

    Where:
        K_{ii} = diagonal element of kinship matrix for individual i
        F > 0 indicates inbreeding (excess homozygosity)
        F < 0 indicates outcrossing (excess heterozygosity)
        F = 0 for Hardy-Weinberg equilibrium

    Average Kinship:
        f̄_i = mean(K_{i,j}) for j ≠ i
        (average relatedness of individual i to all others)

    Reference:
        VanRaden, P.M. (2008). Efficient methods to compute genomic
        predictions. J. Dairy Sci. 91:4414-4423.

    Args:
        kinship_matrix: n × n kinship/GRM matrix (as from calculate_vanraden_kinship)

    Returns:
        Dictionary with inbreeding coefficients, average kinship,
        and population-level summary statistics
    """
    try:
        K = np.array(kinship_matrix, dtype=float)
        n = K.shape[0]

        if K.shape[0] != K.shape[1]:
            return {"success": False, "error": "Kinship matrix must be square"}

        # Inbreeding coefficients: F = diag(K) - 1
        F = np.diag(K) - 1.0

        # Average kinship per individual (excluding self)
        mask = ~np.eye(n, dtype=bool)
        avg_kinship = np.array([
            K[i, mask[i]].mean() if n > 1 else 0.0
            for i in range(n)
        ])

        # Population-level metrics
        # Off-diagonal mean = average relatedness in population
        if n > 1:
            off_diag = K[mask]
            pop_avg_kinship = float(off_diag.mean())
            pop_kinship_sd = float(off_diag.std())
        else:
            pop_avg_kinship = 0.0
            pop_kinship_sd = 0.0

        # Effective population size approximation: Ne ≈ 1 / (2 × ΔF)
        mean_F = float(F.mean())
        ne_approx = (1.0 / (2.0 * abs(mean_F))) if abs(mean_F) > 1e-6 else None

        return {
            "success": True,
            "inbreeding_coefficients": F.tolist(),
            "average_kinship": avg_kinship.tolist(),
            "summary": {
                "mean_inbreeding": mean_F,
                "max_inbreeding": float(F.max()),
                "min_inbreeding": float(F.min()),
                "sd_inbreeding": float(F.std()),
                "n_inbred": int(np.sum(F > 0)),
                "n_outcrossed": int(np.sum(F < 0)),
                "population_avg_kinship": pop_avg_kinship,
                "population_kinship_sd": pop_kinship_sd,
                "effective_population_size": ne_approx,
            },
            "n_individuals": n,
        }

    except Exception as e:
        logger.error(f"Inbreeding calculation failed: {str(e)}")
        return {"success": False, "error": str(e)}


def _test_kinship():
    """Simple internal verification test"""
    # Create simple 3 ind x 5 marker matrix (0,1,2)
    G = np.array([
        [0, 1, 2, 0, 2],
        [0, 1, 2, 0, 2], # Identical to 1
        [2, 1, 0, 2, 0]  # Different
    ])
    result = calculate_vanraden_kinship(G)
    print("Test Result:", result["success"])
    if result["success"]:
        K = np.array(result["K"])
        print("Kinship Matrix:\n", K)
        # Diagonals should be close to 1 + F
        # Off-diagonal (1,2) should be close to diagonal

        # Test inbreeding extraction
        inbreeding = calculate_inbreeding(K)
        print("Inbreeding:", inbreeding["summary"])


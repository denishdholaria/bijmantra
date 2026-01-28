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

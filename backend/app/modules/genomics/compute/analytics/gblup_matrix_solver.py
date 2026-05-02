"""
GBLUP Matrix Solver

Core computational logic for Genomic Best Linear Unbiased Prediction (G-BLUP).
This module handles matrix operations for GEBV estimation.

Features:
- Standard G-BLUP solver (Henderson's Mixed Model Equations)
- Reliability calculation
- Variance component extraction

Dependencies:
- numpy: Array operations
- scipy.linalg: Matrix solving (more stable/faster than numpy for linear systems)
"""

import logging
from typing import TypedDict

import numpy as np
from scipy import linalg


logger = logging.getLogger(__name__)

class GBLUPResult(TypedDict):
    gebv: list[float]
    reliability: list[float]
    genetic_variance: float
    error_variance: float
    mean: float
    heritability: float
    error: str | None

class GBLUPMatrixSolver:
    """
    Solver for G-BLUP mixed model equations.
    """

    @staticmethod
    def solve(
        phenotypes: list[float],
        g_matrix: list[list[float]],
        heritability: float
    ) -> GBLUPResult:
        """
        Solve G-BLUP equations.

        Args:
            phenotypes: Vector of phenotypic values (y). NaN values are not supported in this solver
                        and should be imputed or removed before calling.
            g_matrix: Genomic relationship matrix (G), square matrix matching phenotype length.
            heritability: Narrow-sense heritability (h^2), must be in (0, 1].

        Returns:
            GBLUPResult dictionary containing GEBVs and statistics.
        """
        try:
            # 1. Input Validation and Type Conversion
            y = np.array(phenotypes, dtype=float)
            G = np.array(g_matrix, dtype=float)
            n = len(y)

            if G.shape != (n, n):
                return _error_result(
                    f"G-matrix dimension {G.shape} does not match phenotypes length {n}",
                    heritability
                )

            if not (0 < heritability <= 1.0):
                return _error_result(
                    f"Heritability must be in (0, 1]. Got {heritability}",
                    heritability
                )

            if np.isnan(y).any():
                 return _error_result(
                    "Phenotypes contain NaN values. Please impute missing data.",
                    heritability
                )

            if np.isnan(G).any():
                return _error_result(
                    "G-matrix contains NaN values.",
                    heritability
                )

            # 2. Setup Mixed Model Equations
            # Lambda = sigma_e^2 / sigma_g^2 = (1 - h^2) / h^2
            lambda_val = (1.0 - heritability) / heritability

            # Mean centering
            mu = float(np.mean(y))
            y_centered = y - mu

            # V = G + I * lambda
            # This is the coefficient matrix for the reduced MME: V * alpha = y - mu
            # Where alpha are the "rotated" effects, and u = G * alpha
            identity_matrix = np.eye(n)
            V = G + identity_matrix * lambda_val

            # 3. Solve Equations
            # Solve V * alpha = y_centered
            # Use linalg.solve (assumes V is non-singular)
            try:
                alpha = linalg.solve(V, y_centered, assume_a='sym')
            except linalg.LinAlgError as e:
                logger.error(f"Matrix inversion failed: {e}")
                return _error_result("Singular matrix encountered during GEBV estimation", heritability, mean=mu)

            # 4. Calculate GEBVs
            # u_hat = G * alpha
            gebv = np.dot(G, alpha)

            # 5. Calculate Reliability (PEV-based)
            # Reliability = 1 - PEV / sigma_g^2
            # PEV = lambda * diag(inv(V) * G) * sigma_g^2 ... wait.
            # Standard formula: PEV = diag(C_inv) * sigma_e^2 for full MME.
            # Simplified for GBLUP (VanRaden 2008):
            # rel = 1 - lambda * diag(inv(V)) ... almost.
            # Correct derivation:
            # MME: [Z'Z + G^-1 lambda] u = Z'y ...
            # With Z=I (single record per ind), [I + G^-1 lambda] u = y
            # inv(LHS) = inv(I + G^-1 lambda) = inv(G^-1(G + lambda I)) = (G + lambda I)^-1 G = V^-1 G.
            # PEV = diag(inv(LHS)) * sigma_e^2 = diag(V^-1 G) * sigma_e^2.
            # Reliability = 1 - PEV / sigma_g^2 = 1 - (diag(V^-1 G) * sigma_e^2) / sigma_g^2
            # Since sigma_e^2 / sigma_g^2 = lambda,
            # Reliability = 1 - lambda * diag(V^-1 G).

            # Calculate V^-1 G efficiently
            # We solve V * Z = G for Z
            try:
                V_inv_G = linalg.solve(V, G, assume_a='sym')
                reliabilities = 1.0 - lambda_val * np.diag(V_inv_G)
                # Clip to valid range [0, 1] due to numerical noise
                reliabilities = np.clip(reliabilities, 0.0, 1.0)
            except linalg.LinAlgError:
                # Fallback if V is singular (unlikely if alpha was solved, but possible)
                reliabilities = np.zeros(n)

            # 6. Variance Statistics
            var_gebv = float(np.var(gebv))
            residuals = y_centered - gebv
            var_e = float(np.var(residuals))

            return {
                "gebv": gebv.tolist(),
                "reliability": reliabilities.tolist(),
                "genetic_variance": var_gebv,
                "error_variance": var_e,
                "mean": mu,
                "heritability": heritability,
                "error": None
            }

        except Exception as e:
            logger.exception(f"Unexpected error in GBLUP solver: {e}")
            return _error_result(str(e), heritability)


def _error_result(message: str, heritability: float, mean: float = 0.0) -> GBLUPResult:
    """Helper to return consistent error structure."""
    return {
        "gebv": [],
        "reliability": [],
        "genetic_variance": 0.0,
        "error_variance": 0.0,
        "mean": mean,
        "heritability": heritability,
        "error": message
    }

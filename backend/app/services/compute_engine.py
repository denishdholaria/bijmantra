"""
Compute Engine Service
High-performance numerical computations via Fortran/Rust

This service provides a Python interface to the Fortran compute kernels
for breeding value estimation, variance component analysis, and genomic
relationship matrix computation.

Architecture:
- Python (FastAPI) -> Rust FFI -> Fortran HPC
- Fallback to NumPy/SciPy for development/testing
"""

import logging
import numpy as np
from enum import Enum
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
# Global flag for system compute availability (CALF)
SYSTEM_COMPUTE_AVAILABLE = False

logger = logging.getLogger(__name__)


class ComputeBackend(Enum):
    """Available compute backends"""
    FORTRAN = "fortran"  # Production: Fortran via Rust FFI
    NUMPY = "numpy"      # Development: Pure NumPy/SciPy
    AUTO = "auto"        # Auto-select based on availability


@dataclass
class BLUPResult:
    """Result from BLUP computation"""
    fixed_effects: np.ndarray
    breeding_values: np.ndarray
    reliability: Optional[np.ndarray] = None
    converged: bool = True
    iterations: int = 0


@dataclass
class REMLResult:
    """Result from REML variance estimation"""
    var_additive: float
    var_residual: float
    heritability: float
    converged: bool
    iterations: int
    log_likelihood: Optional[float] = None


@dataclass
class GRMResult:
    """Result from GRM computation"""
    matrix: np.ndarray
    method: str
    n_individuals: int
    n_markers: int


class ComputeEngine:
    """
    High-performance compute engine for breeding analytics
    
    Provides access to Fortran HPC kernels for:
    - BLUP/GBLUP breeding value estimation
    - REML variance component estimation
    - Genomic relationship matrix computation
    - PCA/SVD for population structure
    - LD analysis
    - G×E interaction analysis
    """

    def __init__(self, backend: ComputeBackend = ComputeBackend.AUTO):
        self.backend = backend
        self._fortran_available = self._check_fortran()

        if backend == ComputeBackend.AUTO:
            self.backend = ComputeBackend.FORTRAN if self._fortran_available else ComputeBackend.NUMPY

        logger.info(f"ComputeEngine initialized with backend: {self.backend.value}")

    def _check_fortran(self) -> bool:
        """Check if Fortran library is available"""
        global SYSTEM_COMPUTE_AVAILABLE
        try:
            # Try to import the Rust/Fortran bindings
            import bijmantra_compute
            SYSTEM_COMPUTE_AVAILABLE = True
            return True
        except ImportError:
            # CRITICAL: Fail loudly if native compute is missing in production contexts
            # We log as ERROR to ensure visibility in logs ("The Missing Link")
            logger.error("SYSTEM COMPUTE MISSING: Could not import bijmantra_compute. Falling back to NumPy (slower but correct).")
            SYSTEM_COMPUTE_AVAILABLE = False
            return False

    # =========================================================================
    # BLUP/GBLUP Methods
    # =========================================================================

    def compute_blup(
        self,
        phenotypes: np.ndarray,
        fixed_effects: np.ndarray,
        random_effects: np.ndarray,
        relationship_matrix_inv: np.ndarray,
        var_additive: float,
        var_residual: float
    ) -> BLUPResult:
        """
        Compute Best Linear Unbiased Prediction (BLUP)
        
        Parameters:
            phenotypes: Phenotypic observations (n,)
            fixed_effects: Fixed effects design matrix (n, p)
            random_effects: Random effects design matrix (n, q)
            relationship_matrix_inv: Inverse of relationship matrix (q, q)
            var_additive: Additive genetic variance
            var_residual: Residual variance
        
        Returns:
            BLUPResult with fixed effects and breeding values
        """
        if self.backend == ComputeBackend.FORTRAN:
            return self._blup_fortran(
                phenotypes, fixed_effects, random_effects,
                relationship_matrix_inv, var_additive, var_residual
            )
        else:
            return self._blup_numpy(
                phenotypes, fixed_effects, random_effects,
                relationship_matrix_inv, var_additive, var_residual
            )

    def compute_gblup(
        self,
        genotypes: np.ndarray,
        phenotypes: np.ndarray,
        heritability: float = 0.5
    ) -> BLUPResult:
        """
        Compute Genomic BLUP (GBLUP)
        
        Parameters:
            genotypes: Marker genotype matrix (n, m), coded as 0, 1, 2
            phenotypes: Phenotypic observations (n,)
            heritability: Heritability estimate (0-1)
        
        Returns:
            BLUPResult with genomic estimated breeding values
        """
        if self.backend == ComputeBackend.FORTRAN:
            return self._gblup_fortran(genotypes, phenotypes, heritability)
        else:
            return self._gblup_numpy(genotypes, phenotypes, heritability)

    # =========================================================================
    # REML Methods
    # =========================================================================

    def estimate_variance_components(
        self,
        phenotypes: np.ndarray,
        fixed_effects: np.ndarray,
        random_effects: np.ndarray,
        relationship_matrix: np.ndarray,
        var_additive_init: float = 0.5,
        var_residual_init: float = 1.0,
        method: str = "ai-reml",
        max_iter: int = 100,
        tolerance: float = 1e-8
    ) -> REMLResult:
        """
        Estimate variance components using REML
        
        Parameters:
            phenotypes: Phenotypic observations (n,)
            fixed_effects: Fixed effects design matrix (n, p)
            random_effects: Random effects design matrix (n, q)
            relationship_matrix: Relationship matrix (q, q)
            var_additive_init: Initial additive variance
            var_residual_init: Initial residual variance
            method: "ai-reml" or "em-reml"
            max_iter: Maximum iterations
            tolerance: Convergence tolerance
        
        Returns:
            REMLResult with estimated variance components
        """
        if self.backend == ComputeBackend.FORTRAN:
            return self._reml_fortran(
                phenotypes, fixed_effects, random_effects, relationship_matrix,
                var_additive_init, var_residual_init, method, max_iter, tolerance
            )
        else:
            return self._reml_numpy(
                phenotypes, fixed_effects, random_effects, relationship_matrix,
                var_additive_init, var_residual_init, method, max_iter, tolerance
            )

    # =========================================================================
    # GRM Methods
    # =========================================================================

    def compute_grm(
        self,
        genotypes: np.ndarray,
        method: str = "vanraden1"
    ) -> GRMResult:
        """
        Compute Genomic Relationship Matrix
        
        Parameters:
            genotypes: Marker genotype matrix (n, m), coded as 0, 1, 2
            method: "vanraden1", "vanraden2", or "yang"
        
        Returns:
            GRMResult with relationship matrix
        """
        n, m = genotypes.shape

        if self.backend == ComputeBackend.FORTRAN:
            G = self._grm_fortran(genotypes, method)
        else:
            G = self._grm_numpy(genotypes, method)

        return GRMResult(matrix=G, method=method, n_individuals=n, n_markers=m)

    # =========================================================================
    # NumPy Implementations (Fallback)
    # =========================================================================

    def _blup_numpy(
        self,
        y: np.ndarray,
        X: np.ndarray,
        Z: np.ndarray,
        A_inv: np.ndarray,
        var_a: float,
        var_e: float
    ) -> BLUPResult:
        """NumPy implementation of BLUP"""
        n, p = X.shape
        _, q = Z.shape

        # Lambda (variance ratio)
        lam = var_e / var_a

        # Build coefficient matrix
        XtX = X.T @ X
        XtZ = X.T @ Z
        ZtX = Z.T @ X
        ZtZ = Z.T @ Z + lam * A_inv

        C = np.block([
            [XtX, XtZ],
            [ZtX, ZtZ]
        ])

        # Build RHS
        rhs = np.concatenate([X.T @ y, Z.T @ y])

        # Solve
        try:
            solution = np.linalg.solve(C, rhs)
            beta = solution[:p]
            u = solution[p:]
            return BLUPResult(fixed_effects=beta, breeding_values=u)
        except np.linalg.LinAlgError:
            logger.error("BLUP solve failed")
            return BLUPResult(
                fixed_effects=np.zeros(p),
                breeding_values=np.zeros(q),
                converged=False
            )

    def _gblup_numpy(
        self,
        genotypes: np.ndarray,
        phenotypes: np.ndarray,
        h2: float
    ) -> BLUPResult:
        """NumPy implementation of GBLUP"""
        n, m = genotypes.shape

        # Compute GRM
        grm_result = self.compute_grm(genotypes, method="vanraden1")
        G = grm_result.matrix

        # Add small value to diagonal for stability
        G += np.eye(n) * 0.001

        # Invert G
        try:
            G_inv = np.linalg.inv(G)
        except np.linalg.LinAlgError:
            G_inv = np.linalg.pinv(G)

        # Lambda
        lam = (1 - h2) / h2

        # Build MME
        ones = np.ones((n, 1))
        C = np.block([
            [n, ones.T],
            [ones, np.eye(n) + lam * G_inv]
        ])

        rhs = np.concatenate([[phenotypes.sum()], phenotypes])

        try:
            solution = np.linalg.solve(C, rhs)
            gebv = solution[1:]
            return BLUPResult(
                fixed_effects=np.array([solution[0]]),
                breeding_values=gebv
            )
        except np.linalg.LinAlgError:
            return BLUPResult(
                fixed_effects=np.array([phenotypes.mean()]),
                breeding_values=np.zeros(n),
                converged=False
            )

    def _grm_numpy(self, genotypes: np.ndarray, method: str) -> np.ndarray:
        """NumPy implementation of GRM computation"""
        n, m = genotypes.shape

        # Allele frequencies
        p = genotypes.mean(axis=0) / 2

        if method == "vanraden1":
            # Center genotypes
            Z = genotypes - 2 * p
            # Scale factor
            scale = 2 * np.sum(p * (1 - p))
            if scale < 1e-10:
                scale = 1.0
            # G = ZZ' / scale
            G = (Z @ Z.T) / scale

        elif method == "vanraden2":
            # Weight by heterozygosity
            het = 2 * p * (1 - p)
            het[het < 1e-10] = 1e-10
            weights = 1 / het
            Z = (genotypes - 2 * p) * np.sqrt(weights)
            G = (Z @ Z.T) / m

        else:  # yang
            G = np.zeros((n, n))
            for k in range(m):
                het = 2 * p[k] * (1 - p[k])
                if het < 1e-10:
                    continue
                z = genotypes[:, k] - 2 * p[k]
                G += np.outer(z, z) / het
            G /= m

        return G

    def _reml_numpy(
        self,
        y: np.ndarray,
        X: np.ndarray,
        Z: np.ndarray,
        A: np.ndarray,
        var_a: float,
        var_e: float,
        method: str,
        max_iter: int,
        tol: float
    ) -> REMLResult:
        """NumPy implementation of REML (simplified EM)"""
        n = len(y)
        q = Z.shape[1]

        for iteration in range(max_iter):
            var_a_old, var_e_old = var_a, var_e

            # Compute V = ZAZ'*var_a + I*var_e
            V = var_a * (Z @ A @ Z.T) + var_e * np.eye(n)

            try:
                V_inv = np.linalg.inv(V)
            except np.linalg.LinAlgError:
                break

            # Projection matrix P
            VX = V_inv @ X
            XVX = X.T @ VX
            try:
                XVX_inv = np.linalg.inv(XVX)
            except np.linalg.LinAlgError:
                break

            P = V_inv - VX @ XVX_inv @ VX.T
            Py = P @ y

            # EM updates (simplified)
            ZPy = Z.T @ Py
            var_a = (np.dot(ZPy, ZPy) / var_a + var_a * q) / q
            var_e = np.dot(y - Z @ (var_a * Z.T @ Py), Py) / (n - X.shape[1])

            # Ensure positive
            var_a = max(var_a, 1e-6)
            var_e = max(var_e, 1e-6)

            # Check convergence
            if abs(var_a - var_a_old) < tol * abs(var_a_old) and \
               abs(var_e - var_e_old) < tol * abs(var_e_old):
                return REMLResult(
                    var_additive=var_a,
                    var_residual=var_e,
                    heritability=var_a / (var_a + var_e),
                    converged=True,
                    iterations=iteration + 1
                )

        return REMLResult(
            var_additive=var_a,
            var_residual=var_e,
            heritability=var_a / (var_a + var_e),
            converged=False,
            iterations=max_iter
        )

    # =========================================================================
    # Fortran Implementations (Production)
    # =========================================================================

    def _blup_fortran(
        self,
        phenotypes: np.ndarray,
        fixed_effects: np.ndarray,
        random_effects: np.ndarray,
        relationship_matrix_inv: np.ndarray,
        var_additive: float,
        var_residual: float
    ) -> BLUPResult:
        """Fortran implementation via Rust FFI"""
        import bijmantra_compute

        n = len(phenotypes)
        p = fixed_effects.shape[1]
        q = random_effects.shape[1]

        # Ensure correct data types (C-contiguous, float64)
        y = np.ascontiguousarray(phenotypes, dtype=np.float64)
        X = np.ascontiguousarray(fixed_effects.flatten(), dtype=np.float64)
        Z = np.ascontiguousarray(random_effects.flatten(), dtype=np.float64)
        A_inv = np.ascontiguousarray(relationship_matrix_inv.flatten(), dtype=np.float64)

        beta, u = bijmantra_compute.blup(y, X, Z, A_inv, var_additive, var_residual, n, p, q)

        return BLUPResult(fixed_effects=beta, breeding_values=u)

    def _gblup_fortran(
        self,
        genotypes: np.ndarray,
        phenotypes: np.ndarray,
        heritability: float
    ) -> BLUPResult:
        """Fortran implementation via Rust FFI"""
        import bijmantra_compute

        n, m = genotypes.shape

        G = np.ascontiguousarray(genotypes.flatten(), dtype=np.float64)
        y = np.ascontiguousarray(phenotypes, dtype=np.float64)

        gebv = bijmantra_compute.gblup(G, y, heritability, n, m)

        return BLUPResult(
            fixed_effects=np.array([0.0]),  # Placeholder
            breeding_values=gebv
        )

    def _grm_fortran(self, genotypes: np.ndarray, method: str) -> np.ndarray:
        """Fortran implementation via Rust FFI"""
        import bijmantra_compute

        n, m = genotypes.shape
        G_flat = np.ascontiguousarray(genotypes.flatten(), dtype=np.float64)

        grm_flat = bijmantra_compute.compute_grm(G_flat, method, n, m)
        return grm_flat.reshape(n, n)

    def _reml_fortran(
        self,
        y: np.ndarray,
        X: np.ndarray,
        Z: np.ndarray,
        A: np.ndarray,
        var_a: float,
        var_e: float,
        method: str,
        max_iter: int,
        tol: float
    ) -> REMLResult:
        """Fortran implementation via Rust FFI"""
        import bijmantra_compute

        n = len(y)
        p = X.shape[1]
        q = Z.shape[1]

        # Ensure correct data types (C-contiguous, float64)
        y_flat = np.ascontiguousarray(y, dtype=np.float64)
        X_flat = np.ascontiguousarray(X.flatten(), dtype=np.float64)
        Z_flat = np.ascontiguousarray(Z.flatten(), dtype=np.float64)
        A_flat = np.ascontiguousarray(A.flatten(), dtype=np.float64)

        var_a_est, var_e_est, h2, converged, iterations, log_lik = bijmantra_compute.reml_estimate(
            y_flat, X_flat, Z_flat, A_flat,
            var_a, var_e, method, max_iter, tol,
            n, p, q
        )

        return REMLResult(
            var_additive=var_a_est,
            var_residual=var_e_est,
            heritability=h2,
            converged=converged,
            iterations=iterations,
            log_likelihood=log_lik
        )


# Global compute engine instance
compute_engine = ComputeEngine()

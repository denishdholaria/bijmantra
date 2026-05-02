import pytest
import numpy as np
from app.modules.genomics.compute.analytics.gblup_matrix_solver import GBLUPMatrixSolver

class TestGBLUPMatrixSolver:

    def test_solve_basic_valid(self):
        """Test with a simple, valid 3x3 case."""
        phenotypes = [10.0, 12.0, 14.0]
        # Identity matrix for G -> no relationship
        g_matrix = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ]
        h2 = 0.5

        # lambda = (1-0.5)/0.5 = 1.0
        # V = G + I*1 = 2I
        # y_centered = [-2, 0, 2]
        # alpha = solve(2I, y_centered) = [-1, 0, 1]
        # gebv = G * alpha = [-1, 0, 1]

        result = GBLUPMatrixSolver.solve(phenotypes, g_matrix, h2)

        assert result["error"] is None
        np.testing.assert_allclose(result["gebv"], [-1.0, 0.0, 1.0], atol=1e-5)
        assert result["mean"] == 12.0

        # Reliability
        # r2 = 1 - lambda * diag(V^-1 G)
        # V^-1 G = (2I)^-1 I = 0.5 I
        # r2 = 1 - 1.0 * 0.5 = 0.5
        np.testing.assert_allclose(result["reliability"], [0.5, 0.5, 0.5], atol=1e-5)

    def test_solve_high_heritability(self):
        """Test with high heritability (h2=0.9)."""
        phenotypes = [10.0, 12.0]
        g_matrix = [[1.0, 0.0], [0.0, 1.0]]
        h2 = 0.9

        # lambda = (1-0.9)/0.9 = 0.111...

        result = GBLUPMatrixSolver.solve(phenotypes, g_matrix, h2)

        assert result["error"] is None
        # GEBV should be closer to y_centered
        y_centered = np.array([-1.0, 1.0])
        # With high h2, regularization is low, so GEBV -> y_centered
        np.testing.assert_allclose(result["gebv"], y_centered * (1 / (1 + (1-0.9)/0.9)), atol=1e-2)
        assert all(r > 0.8 for r in result["reliability"])

    def test_dimension_mismatch(self):
        """Test mismatched dimensions."""
        phenotypes = [10.0, 12.0]
        g_matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]] # 3x3

        result = GBLUPMatrixSolver.solve(phenotypes, g_matrix, 0.5)

        assert result["error"] is not None
        assert "dimension" in result["error"]

    def test_invalid_heritability(self):
        """Test invalid heritability values."""
        phenotypes = [10.0, 12.0]
        g_matrix = [[1.0, 0.0], [0.0, 1.0]]

        res1 = GBLUPMatrixSolver.solve(phenotypes, g_matrix, 1.5)
        assert res1["error"] is not None

        res2 = GBLUPMatrixSolver.solve(phenotypes, g_matrix, -0.1)
        assert res2["error"] is not None

        res3 = GBLUPMatrixSolver.solve(phenotypes, g_matrix, 0.0)
        assert res3["error"] is not None

    def test_nan_inputs(self):
        """Test NaN handling."""
        g_matrix = [[1.0, 0.0], [0.0, 1.0]]

        # NaN in phenotype
        res1 = GBLUPMatrixSolver.solve([10.0, float('nan')], g_matrix, 0.5)
        assert "NaN" in res1["error"]

        # NaN in G matrix
        g_nan = [[1.0, float('nan')], [0.0, 1.0]]
        res2 = GBLUPMatrixSolver.solve([10.0, 12.0], g_nan, 0.5)
        assert "NaN" in res2["error"]

    def test_singular_matrix_full_heritability(self):
        """Test singular matrix when h2=1 (lambda=0)."""
        phenotypes = [10.0, 10.0]
        # Rank deficient matrix [1 1; 1 1]
        g_matrix = [[1.0, 1.0], [1.0, 1.0]]
        h2 = 1.0

        # V = G + 0*I = G. G is singular. Solve should fail.
        result = GBLUPMatrixSolver.solve(phenotypes, g_matrix, h2)

        assert result["error"] is not None
        assert "Singular matrix" in result["error"]

    def test_correlated_individuals(self):
        """Test with correlated individuals."""
        phenotypes = [10.0, 12.0]
        # Correlation 0.5
        g_matrix = [[1.0, 0.5], [0.5, 1.0]]
        h2 = 0.5 # lambda = 1

        # V = [[2, 0.5], [0.5, 2]]
        # y_c = [-1, 1]
        # Solve V * alpha = y_c
        # det(V) = 4 - 0.25 = 3.75
        # inv(V) = 1/3.75 * [[2, -0.5], [-0.5, 2]]
        # alpha = 1/3.75 * [-2 - 0.5, 0.5 + 2] = [-2.5, 2.5] / 3.75 = [-2/3, 2/3]

        # gebv = G * alpha
        # [[1, 0.5], [0.5, 1]] * [-0.666, 0.666]
        # ind1: -0.666 + 0.333 = -0.333
        # ind2: -0.333 + 0.666 = 0.333

        result = GBLUPMatrixSolver.solve(phenotypes, g_matrix, h2)

        assert result["error"] is None
        np.testing.assert_allclose(result["gebv"], [-1.0/3.0, 1.0/3.0], atol=1e-5)

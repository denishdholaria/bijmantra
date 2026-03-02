import pytest
import numpy as np
from app.services.genomic_selection import GenomicSelectionService

@pytest.fixture
def gs_service():
    return GenomicSelectionService()

class TestGBLUPDetailed:
    """Detailed tests for GBLUP implementation."""

    def test_gblup_valid_small_case(self, gs_service):
        """Test with a small, valid 3x3 G-matrix."""
        phenotypes = [10.0, 12.0, 14.0]
        # Identity matrix for G -> no relationship, variance=1
        g_matrix = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ]
        h2 = 0.5

        # lambda = (1-0.5)/0.5 = 1.0
        # V_star = G + I*1 = I + I = 2I
        # y_centered = [-2, 0, 2]
        # x = solve(2I, [-2, 0, 2]) = [-1, 0, 1]
        # gebv = G*x = I*[-1, 0, 1] = [-1, 0, 1]

        result = gs_service.run_gblup(phenotypes, g_matrix, h2)

        assert "error" not in result
        np.testing.assert_allclose(result["gebv"], [-1.0, 0.0, 1.0], atol=1e-5)
        assert result["mean"] == 12.0

        # Reliability check
        # M_inv_G = solve(2I, I) = 0.5 I
        # rel = 1 - lambda * diag(0.5 I) = 1 - 1 * 0.5 = 0.5
        np.testing.assert_allclose(result["reliability"], [0.5, 0.5, 0.5], atol=1e-5)

    def test_gblup_dimension_mismatch(self, gs_service):
        """Test with mismatched phenotypes and G-matrix."""
        phenotypes = [10.0, 12.0]
        g_matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]] # 3x3

        # Should raise ValueError (currently from numpy)
        with pytest.raises((ValueError, Exception)):
             gs_service.run_gblup(phenotypes, g_matrix, 0.5)

    def test_gblup_zero_heritability(self, gs_service):
        """Test with h2=0 (should fail gracefully or raise ValueError)."""
        phenotypes = [10.0, 12.0]
        g_matrix = [[1.0, 0.0], [0.0, 1.0]]

        # Should raise ValueError, currently ZeroDivisionError
        with pytest.raises((ValueError, ZeroDivisionError)):
             gs_service.run_gblup(phenotypes, g_matrix, 0.0)

    def test_gblup_singular_matrix(self, gs_service):
        """Test with singular V_star."""
        phenotypes = [10.0, 10.0]
        g_matrix = [[1.0, 1.0], [1.0, 1.0]] # Singular, rank 1
        h2 = 1.0

        result = gs_service.run_gblup(phenotypes, g_matrix, h2)
        assert "error" in result
        assert result["error"] == "Singular matrix encountered"

    def test_gblup_reliability_bounds(self, gs_service):
        """Reliabilities should be in [0, 1]."""
        phenotypes = [10.0, 12.0, 14.0]
        g_matrix = [[1.0, 0.1, 0.1], [0.1, 1.0, 0.1], [0.1, 0.1, 1.0]]
        h2 = 0.5

        result = gs_service.run_gblup(phenotypes, g_matrix, h2)
        assert "error" not in result
        reliabilities = result["reliability"]
        assert all(0.0 <= r <= 1.0 for r in reliabilities)

    def test_gblup_invalid_heritability(self, gs_service):
         """Test with h2 > 1 or h2 < 0."""
         phenotypes = [10.0, 12.0]
         g_matrix = [[1.0, 0.0], [0.0, 1.0]]

         # Should raise ValueError
         with pytest.raises(ValueError):
             gs_service.run_gblup(phenotypes, g_matrix, 1.5)

         with pytest.raises(ValueError):
             gs_service.run_gblup(phenotypes, g_matrix, -0.1)

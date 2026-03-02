"""
Edge case tests for Genomic Selection Service (rrBLUP).

Tests rrBLUP with tetraploid data, constant phenotypes, constant markers,
high marker count (p > n), and perfect correlation.
"""

import pytest
import numpy as np
from app.services.genomic_selection import GenomicSelectionService


@pytest.fixture
def gs_service():
    """Create GenomicSelectionService instance."""
    return GenomicSelectionService()


class TestRrBLUPEdgeCases:
    """Tests for run_rrblup() edge cases."""

    def test_rrblup_tetraploid(self, gs_service):
        """rrBLUP should handle tetraploid (0-4) data correctly."""
        ploidy = 4
        n_ind = 20
        n_markers = 50

        # Random genotypes (0-4)
        markers = np.random.randint(0, ploidy + 1, size=(n_ind, n_markers)).tolist()

        # Simple additive model: y = sum(genotype) + noise
        true_effects = np.random.normal(0, 1, n_markers)
        gebv = np.dot(markers, true_effects)
        phenotypes = (gebv + np.random.normal(0, 0.1, n_ind)).tolist()

        result = gs_service.run_rrblup(markers, phenotypes, ploidy=ploidy)

        assert "error" not in result
        assert len(result["marker_effects"]) == n_markers
        assert result["variance_components"]["heritability"] > 0
        assert result["accuracy"] > 0.5  # Should be high for this simple case

    def test_rrblup_constant_phenotypes(self, gs_service):
        """Should return 0 accuracy and variance when all phenotypes are identical."""
        n_ind = 10
        n_markers = 20
        markers = np.random.randint(0, 3, size=(n_ind, n_markers)).tolist()
        phenotypes = [5.0] * n_ind  # All 5.0

        result = gs_service.run_rrblup(markers, phenotypes)

        assert "error" not in result
        assert result["accuracy"] == 0.0
        assert result["variance_components"]["var_genetic"] == 0.0
        assert result["variance_components"]["var_residual"] == 0.0
        # Marker effects should be near zero (numerical precision issues might give very small values)
        assert np.allclose(result["marker_effects"], 0, atol=1e-5)

    def test_rrblup_constant_markers(self, gs_service):
        """Constant markers (monomorphic) should have near-zero effects."""
        n_ind = 20
        n_markers = 10

        # 9 random markers, 1 constant marker (all 0)
        M = np.random.randint(0, 3, size=(n_ind, n_markers - 1))
        constant_col = np.zeros((n_ind, 1), dtype=int)
        M = np.hstack((M, constant_col))

        phenotypes = np.random.normal(0, 1, n_ind).tolist()
        markers = M.tolist()

        result = gs_service.run_rrblup(markers, phenotypes)

        assert "error" not in result
        effects = np.array(result["marker_effects"])
        # The last marker (constant) should have 0 effect
        assert np.isclose(effects[-1], 0.0, atol=1e-5)

    def test_rrblup_high_p_low_n(self, gs_service):
        """Should handle p > n case (more markers than individuals)."""
        n_ind = 10
        n_markers = 50  # p >> n

        markers = np.random.randint(0, 3, size=(n_ind, n_markers)).tolist()
        phenotypes = np.random.normal(0, 1, n_ind).tolist()

        result = gs_service.run_rrblup(markers, phenotypes)

        assert "error" not in result
        assert len(result["marker_effects"]) == n_markers
        assert len(result["gebv"]) == n_ind

    def test_rrblup_perfect_correlation(self, gs_service):
        """Should achieve near 1.0 accuracy when phenotype is perfectly determined by markers."""
        n_ind = 50
        n_markers = 20
        markers = np.random.randint(0, 3, size=(n_ind, n_markers))

        # Phenotype is exactly determined by first marker
        phenotypes = markers[:, 0].astype(float).tolist()
        markers_list = markers.tolist()

        result = gs_service.run_rrblup(markers_list, phenotypes)

        assert "error" not in result
        # Accuracy might not be exactly 1.0 due to shrinkage (lambda > 0), but should be very high
        assert result["accuracy"] > 0.95

        effects = np.array(result["marker_effects"])
        # First marker should have effect near 1.0
        # Note: With shrinkage, it might be slightly less than 1.0, and others non-zero
        # But relative effect of first marker should be dominant?
        # Let's just check accuracy for now.

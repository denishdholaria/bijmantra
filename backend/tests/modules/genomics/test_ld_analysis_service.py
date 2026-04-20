"""
Tests for LD Analysis Service

Tests the scientific accuracy and correctness of Linkage Disequilibrium calculations.
"""

import pytest
import math
from app.modules.genomics.services.ld_analysis_service import LDAnalysisService


class TestLDAnalysisService:
    """Test suite for LD Analysis Service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = LDAnalysisService()

    def test_calculate_r2_perfect_correlation(self):
        """Test r² calculation with perfect correlation."""
        # Identical genotypes should have r² = 1.0
        g1 = [0, 1, 2, 0, 1, 2]
        g2 = [0, 1, 2, 0, 1, 2]

        r2 = self.service.calculate_r2(g1, g2)
        assert r2 == pytest.approx(1.0, abs=0.01)

    def test_calculate_r2_no_correlation(self):
        """Test r² calculation with no correlation."""
        # Uncorrelated genotypes should have r² ≈ 0
        g1 = [0, 0, 0, 0, 0, 0]
        g2 = [1, 1, 1, 1, 1, 1]

        r2 = self.service.calculate_r2(g1, g2)
        # With constant values, variance is 0, so r² should be 0
        assert r2 == 0.0

    def test_calculate_r2_partial_correlation(self):
        """Test r² calculation with partial correlation."""
        # Some correlation but not perfect
        g1 = [0, 1, 2, 0, 1, 2, 0, 1]
        g2 = [0, 1, 2, 1, 2, 0, 0, 1]

        r2 = self.service.calculate_r2(g1, g2)
        assert 0.0 < r2 < 1.0

    def test_calculate_r2_with_missing_data(self):
        """Test r² calculation ignoring missing values (-1)."""
        # Missing values should be ignored
        g1 = [0, 1, 2, -1, 1, 2]
        g2 = [0, 1, 2, 0, -1, 2]

        r2 = self.service.calculate_r2(g1, g2)
        # Should calculate based on valid pairs only: (0,0), (1,1), (2,2)
        assert r2 == pytest.approx(1.0, abs=0.01)

    def test_calculate_r2_all_missing(self):
        """Test r² calculation with all missing values."""
        g1 = [-1, -1, -1]
        g2 = [-1, -1, -1]

        r2 = self.service.calculate_r2(g1, g2)
        assert r2 == 0.0

    def test_calculate_r2_insufficient_data(self):
        """Test r² calculation with insufficient valid data points."""
        # Only one valid pair
        g1 = [0, -1, -1]
        g2 = [0, -1, -1]

        r2 = self.service.calculate_r2(g1, g2)
        assert r2 == 0.0  # Need at least 2 valid points

    def test_calculate_r2_empty_arrays(self):
        """Test r² calculation with empty arrays."""
        g1 = []
        g2 = []

        r2 = self.service.calculate_r2(g1, g2)
        assert r2 == 0.0

    def test_calculate_r2_mismatched_lengths(self):
        """Test r² calculation with mismatched array lengths."""
        g1 = [0, 1, 2]
        g2 = [0, 1]

        r2 = self.service.calculate_r2(g1, g2)
        assert r2 == 0.0

    def test_calculate_r2_zero_variance(self):
        """Test r² calculation when one marker has zero variance."""
        # All same genotype for g1
        g1 = [1, 1, 1, 1, 1]
        g2 = [0, 1, 2, 0, 1]

        r2 = self.service.calculate_r2(g1, g2)
        assert r2 == 0.0  # Zero variance means no correlation can be calculated

    def test_calculate_pairwise_ld_basic(self):
        """Test pairwise LD calculation with basic data."""
        genotypes = [
            [0, 1, 2, 0, 1],
            [0, 1, 2, 0, 1],
            [1, 1, 1, 1, 1],
        ]
        positions = [100, 200, 300]
        marker_names = ['M1', 'M2', 'M3']

        pairs, matrix = self.service.calculate_pairwise_ld(
            genotypes, positions, marker_names, window_size=10
        )

        # Should have 3 pairs: M1-M2, M1-M3, M2-M3
        assert len(pairs) == 3

        # Matrix should be 3x3
        assert len(matrix) == 3
        assert len(matrix[0]) == 3

        # Diagonal should be 1.0
        assert matrix[0][0] == 1.0
        assert matrix[1][1] == 1.0
        assert matrix[2][2] == 1.0

        # Matrix should be symmetric
        assert matrix[0][1] == matrix[1][0]
        assert matrix[0][2] == matrix[2][0]
        assert matrix[1][2] == matrix[2][1]

    def test_calculate_pairwise_ld_sorted_by_r2(self):
        """Test that pairs are sorted by r² in descending order."""
        genotypes = [
            [0, 1, 2, 0, 1],  # M1
            [0, 1, 2, 0, 1],  # M2 - identical to M1 (r² = 1.0)
            [1, 1, 1, 1, 1],  # M3 - constant (r² = 0.0 with others)
        ]
        positions = [100, 200, 300]
        marker_names = ['M1', 'M2', 'M3']

        pairs, _ = self.service.calculate_pairwise_ld(
            genotypes, positions, marker_names, window_size=10
        )

        # Pairs should be sorted by r² descending
        for i in range(len(pairs) - 1):
            assert pairs[i].r2 >= pairs[i + 1].r2

    def test_calculate_pairwise_ld_window_size(self):
        """Test that window size limits pairwise comparisons."""
        genotypes = [[0, 1, 2] for _ in range(10)]
        positions = list(range(0, 1000, 100))
        marker_names = [f'M{i}' for i in range(10)]

        # Window size of 2 means each marker compares with next 2 markers
        pairs, _ = self.service.calculate_pairwise_ld(
            genotypes, positions, marker_names, window_size=2
        )

        # With 10 markers and window=2:
        # M0: M1, M2 (2 pairs)
        # M1: M2, M3 (2 pairs)
        # ...
        # M8: M9 (1 pair)
        # M9: none (0 pairs)
        # Total: 2*8 + 1 = 17 pairs
        assert len(pairs) == 17

    def test_calculate_pairwise_ld_distance_calculation(self):
        """Test that distances are calculated correctly."""
        genotypes = [
            [0, 1, 2],
            [0, 1, 2],
        ]
        positions = [1000, 5000]
        marker_names = ['M1', 'M2']

        pairs, _ = self.service.calculate_pairwise_ld(
            genotypes, positions, marker_names, window_size=10
        )

        assert len(pairs) == 1
        assert pairs[0].distance == 4000  # |5000 - 1000|

    def test_calculate_pairwise_ld_d_prime_approximation(self):
        """Test that D' is approximated as sqrt(r²)."""
        genotypes = [
            [0, 1, 2, 0, 1],
            [0, 1, 2, 0, 1],
        ]
        positions = [100, 200]
        marker_names = ['M1', 'M2']

        pairs, _ = self.service.calculate_pairwise_ld(
            genotypes, positions, marker_names, window_size=10
        )

        assert len(pairs) == 1
        # r² = 1.0, so D' should be sqrt(1.0) = 1.0
        assert pairs[0].d_prime == pytest.approx(math.sqrt(pairs[0].r2), abs=0.01)

    def test_calculate_decay_basic(self):
        """Test LD decay calculation with basic data."""
        # Create genotypes with decreasing LD by distance
        genotypes = [
            [0, 1, 2, 0, 1, 2, 0, 1],
            [0, 1, 2, 0, 1, 2, 0, 1],  # Perfect LD with M1
            [0, 1, 2, 1, 2, 0, 0, 1],  # Partial LD
            [1, 1, 1, 1, 1, 1, 1, 1],  # No LD
        ]
        positions = [0, 500, 1500, 3000]

        decay_points = self.service.calculate_decay(
            genotypes, positions, max_dist=5000, bin_size=1000
        )

        # Should have decay points
        assert len(decay_points) > 0

        # Each point should have required fields
        for point in decay_points:
            assert hasattr(point, 'distance')
            assert hasattr(point, 'mean_r2')
            assert hasattr(point, 'pair_count')
            assert point.mean_r2 >= 0.0
            assert point.mean_r2 <= 1.0
            assert point.pair_count > 0

    def test_calculate_decay_binning(self):
        """Test that decay points are correctly binned."""
        genotypes = [
            [0, 1, 2],
            [0, 1, 2],
            [0, 1, 2],
        ]
        positions = [0, 500, 1500]  # Distances: 500, 1500, 1000

        decay_points = self.service.calculate_decay(
            genotypes, positions, max_dist=5000, bin_size=1000
        )

        # Distances: 0-500 (500), 0-1500 (1500), 500-1500 (1000)
        # Bins: 0, 1000
        bins = {point.distance for point in decay_points}
        assert 0 in bins  # 500 falls in bin 0
        assert 1000 in bins  # 1000 and 1500 fall in bin 1000

    def test_calculate_decay_max_distance(self):
        """Test that max_distance limits comparisons."""
        genotypes = [
            [0, 1, 2],
            [0, 1, 2],
            [0, 1, 2],
        ]
        positions = [0, 500, 10000]  # Last marker is far away

        decay_points = self.service.calculate_decay(
            genotypes, positions, max_dist=1000, bin_size=500
        )

        # Only the 0-500 pair should be included
        assert len(decay_points) == 1
        assert decay_points[0].pair_count == 1

    def test_calculate_decay_empty_genotypes(self):
        """Test decay calculation with empty genotypes."""
        genotypes = []
        positions = []

        decay_points = self.service.calculate_decay(
            genotypes, positions, max_dist=5000, bin_size=1000
        )

        assert len(decay_points) == 0

    def test_calculate_decay_single_marker(self):
        """Test decay calculation with single marker."""
        genotypes = [[0, 1, 2]]
        positions = [100]

        decay_points = self.service.calculate_decay(
            genotypes, positions, max_dist=5000, bin_size=1000
        )

        assert len(decay_points) == 0  # No pairs to compare

    def test_calculate_decay_mean_r2_calculation(self):
        """Test that mean r² is calculated correctly per bin."""
        # Create controlled scenario
        genotypes = [
            [0, 1, 2, 0, 1],
            [0, 1, 2, 0, 1],  # r² = 1.0 with M1
            [0, 1, 2, 0, 1],  # r² = 1.0 with M1 and M2
        ]
        positions = [0, 500, 1000]

        decay_points = self.service.calculate_decay(
            genotypes, positions, max_dist=5000, bin_size=1000
        )

        # All pairs have r² = 1.0, so mean should be 1.0
        for point in decay_points:
            assert point.mean_r2 == pytest.approx(1.0, abs=0.01)

    def test_r2_calculation_properties(self):
        """Test mathematical properties of r² calculation."""
        # Property 1: r² should be between 0 and 1
        g1 = [0, 1, 2, 0, 1, 2]
        g2 = [2, 1, 0, 2, 1, 0]

        r2 = self.service.calculate_r2(g1, g2)
        assert 0.0 <= r2 <= 1.0

        # Property 2: r² should be symmetric
        r2_forward = self.service.calculate_r2(g1, g2)
        r2_reverse = self.service.calculate_r2(g2, g1)
        assert r2_forward == pytest.approx(r2_reverse, abs=0.001)

    def test_pairwise_ld_matrix_symmetry(self):
        """Test that LD matrix is symmetric."""
        genotypes = [
            [0, 1, 2, 0, 1],
            [0, 1, 2, 1, 2],
            [1, 1, 1, 1, 1],
        ]
        positions = [100, 200, 300]
        marker_names = ['M1', 'M2', 'M3']

        _, matrix = self.service.calculate_pairwise_ld(
            genotypes, positions, marker_names, window_size=10
        )

        # Check symmetry
        n = len(matrix)
        for i in range(n):
            for j in range(n):
                assert matrix[i][j] == pytest.approx(matrix[j][i], abs=0.001)

    def test_pairwise_ld_with_missing_data(self):
        """Test pairwise LD calculation with missing genotype data."""
        genotypes = [
            [0, 1, -1, 0, 1],
            [0, -1, 2, 0, 1],
            [1, 1, 1, -1, 1],
        ]
        positions = [100, 200, 300]
        marker_names = ['M1', 'M2', 'M3']

        pairs, matrix = self.service.calculate_pairwise_ld(
            genotypes, positions, marker_names, window_size=10
        )

        # Should still calculate LD, ignoring missing values
        assert len(pairs) == 3
        assert len(matrix) == 3

        # All r² values should be valid
        for pair in pairs:
            assert 0.0 <= pair.r2 <= 1.0

    def test_decay_calculation_with_missing_data(self):
        """Test decay calculation with missing genotype data."""
        genotypes = [
            [0, 1, -1, 0, 1],
            [0, -1, 2, 0, 1],
            [1, 1, 1, -1, 1],
        ]
        positions = [0, 1000, 2000]

        decay_points = self.service.calculate_decay(
            genotypes, positions, max_dist=5000, bin_size=1000
        )

        # Should still calculate decay
        assert len(decay_points) > 0

        # All mean r² values should be valid
        for point in decay_points:
            assert 0.0 <= point.mean_r2 <= 1.0


class TestLDAnalysisEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        self.service = LDAnalysisService()

    def test_large_genotype_matrix(self):
        """Test performance with larger genotype matrix."""
        # 100 markers x 50 samples
        genotypes = [[i % 3 for _ in range(50)] for i in range(100)]
        positions = list(range(0, 100000, 1000))
        marker_names = [f'M{i}' for i in range(100)]

        pairs, matrix = self.service.calculate_pairwise_ld(
            genotypes, positions, marker_names, window_size=10
        )

        # Should complete without error
        assert len(pairs) > 0
        assert len(matrix) == 100

    def test_extreme_r2_values(self):
        """Test handling of extreme r² values."""
        # Perfect positive correlation
        g1 = [0, 1, 2, 0, 1, 2]
        g2 = [0, 1, 2, 0, 1, 2]
        r2 = self.service.calculate_r2(g1, g2)
        assert r2 == pytest.approx(1.0, abs=0.01)

        # Perfect negative correlation (in terms of variance)
        g1 = [0, 0, 0, 2, 2, 2]
        g2 = [2, 2, 2, 0, 0, 0]
        r2 = self.service.calculate_r2(g1, g2)
        assert r2 == pytest.approx(1.0, abs=0.01)  # r² is always positive

    def test_floating_point_precision(self):
        """Test that calculations maintain reasonable precision."""
        g1 = [0, 1, 2, 0, 1, 2, 0]
        g2 = [0, 1, 2, 0, 1, 2, 1]

        r2 = self.service.calculate_r2(g1, g2)

        # Should be a reasonable value with good precision
        assert isinstance(r2, float)
        assert not math.isnan(r2)
        assert not math.isinf(r2)


if __name__ == "__main__":
    pytest.main([__file__])

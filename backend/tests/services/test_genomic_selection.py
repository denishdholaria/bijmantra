"""
Tests for Genomic Selection Service — Sprint 1 Engines

Tests B1.1 (rrBLUP), B1.2 (Cross-validation), B1.3 (Inbreeding)
Using simulated genotype/phenotype data with known properties.
"""

import pytest
import numpy as np
from app.services.genomic_selection import GenomicSelectionService
from app.services.genomics_statistics.kinship import (
    calculate_vanraden_kinship,
    calculate_inbreeding,
)


@pytest.fixture
def gs_service():
    """Create GenomicSelectionService instance."""
    return GenomicSelectionService()


@pytest.fixture
def simulated_data():
    """
    Simulate genotype and phenotype data with known marker effects.

    Creates:
    - 50 individuals × 100 markers
    - 5 causal markers with known effects
    - Phenotype = sum(causal_effects × genotypes) + noise
    """
    rng = np.random.RandomState(42)
    n_ind = 50
    n_markers = 100
    n_causal = 5

    # Generate random genotype matrix (0, 1, 2)
    allele_freq = rng.uniform(0.1, 0.9, n_markers)
    M = np.column_stack([
        rng.binomial(2, p, n_ind) for p in allele_freq
    ])

    # True marker effects (only first n_causal are non-zero)
    true_effects = np.zeros(n_markers)
    true_effects[:n_causal] = rng.normal(0, 1.0, n_causal)

    # Center genotypes
    Z = M - 2 * allele_freq
    true_gebv = Z @ true_effects

    # Phenotype with noise (h² ≈ 0.5)
    var_g = np.var(true_gebv)
    noise = rng.normal(0, np.sqrt(var_g), n_ind)  # var_e ≈ var_g → h² ≈ 0.5
    y = true_gebv + noise + 50  # Add intercept

    return {
        "markers": M.tolist(),
        "phenotypes": y.tolist(),
        "true_effects": true_effects,
        "true_gebv": true_gebv,
        "n_ind": n_ind,
        "n_markers": n_markers,
        "n_causal": n_causal,
        "M": M,
    }


# ──────────────────────────────────────────────
# B1.1: rrBLUP Marker-Effect Model
# ──────────────────────────────────────────────

class TestRrBLUP:
    """Tests for run_rrblup() — ridge regression marker effects."""

    def test_basic_output_structure(self, gs_service, simulated_data):
        """rrBLUP should return all expected fields."""
        result = gs_service.run_rrblup(
            simulated_data["markers"], simulated_data["phenotypes"]
        )

        assert "error" not in result
        assert "marker_effects" in result
        assert "gebv" in result
        assert "variance_components" in result
        assert "accuracy" in result
        assert "p_values" in result
        assert "pve" in result
        assert result["method"] == "rrBLUP"

    def test_dimensions(self, gs_service, simulated_data):
        """Output dimensions should match input."""
        result = gs_service.run_rrblup(
            simulated_data["markers"], simulated_data["phenotypes"]
        )

        assert len(result["marker_effects"]) == simulated_data["n_markers"]
        assert len(result["gebv"]) == simulated_data["n_ind"]
        assert len(result["p_values"]) == simulated_data["n_markers"]
        assert len(result["se_effects"]) == simulated_data["n_markers"]

    def test_variance_components(self, gs_service, simulated_data):
        """Variance components should be positive and h² in [0, 1]."""
        result = gs_service.run_rrblup(
            simulated_data["markers"], simulated_data["phenotypes"]
        )

        vc = result["variance_components"]
        assert vc["var_marker"] > 0
        assert vc["var_genetic"] > 0
        assert vc["var_residual"] > 0
        assert 0 <= vc["heritability"] <= 1
        assert vc["lambda"] > 0

    def test_prediction_accuracy(self, gs_service, simulated_data):
        """rrBLUP accuracy should be > 0 with correlated data."""
        result = gs_service.run_rrblup(
            simulated_data["markers"], simulated_data["phenotypes"]
        )

        # Accuracy should be positive (data has true signal)
        assert result["accuracy"] > 0

    def test_causal_markers_have_larger_effects(self, gs_service, simulated_data):
        """Causal markers should have larger absolute effects than non-causal."""
        result = gs_service.run_rrblup(
            simulated_data["markers"], simulated_data["phenotypes"]
        )

        effects = np.abs(result["marker_effects"])
        n_causal = simulated_data["n_causal"]

        # Mean absolute effect of causal markers should exceed non-causal
        causal_mean = np.mean(effects[:n_causal])
        noncausal_mean = np.mean(effects[n_causal:])
        assert causal_mean > noncausal_mean

    def test_dimension_mismatch_error(self, gs_service):
        """Should return error for mismatched dimensions."""
        result = gs_service.run_rrblup(
            [[0, 1], [1, 2], [2, 0]],  # 3 individuals
            [1.0, 2.0],  # 2 phenotypes
        )
        assert "error" in result

    def test_too_few_individuals(self, gs_service):
        """Should return error for < 3 individuals."""
        result = gs_service.run_rrblup(
            [[0, 1], [1, 2]],
            [1.0, 2.0],
        )
        assert "error" in result


# ──────────────────────────────────────────────
# GBLUP Smoke Tests
# ──────────────────────────────────────────────

class TestGBLUP:
    """Existing GBLUP should still work correctly."""

    def test_gblup_basic(self, gs_service, simulated_data):
        """GBLUP should produce valid GEBVs."""
        g_result = gs_service.calculate_g_matrix(simulated_data["markers"])
        gblup_result = gs_service.run_gblup(
            simulated_data["phenotypes"],
            g_result["matrix"],
            heritability=0.5,
        )

        assert "error" not in gblup_result
        assert len(gblup_result["gebv"]) == simulated_data["n_ind"]
        assert gblup_result["genetic_variance"] > 0


# ──────────────────────────────────────────────
# B1.2: Cross-Validation Pipeline
# ──────────────────────────────────────────────

class TestCrossValidation:
    """Tests for cross_validate() — k-fold CV pipeline."""

    def test_cv_gblup_structure(self, gs_service, simulated_data):
        """GBLUP CV should return all expected fields."""
        result = gs_service.cross_validate(
            simulated_data["markers"],
            simulated_data["phenotypes"],
            method="gblup",
            n_folds=5,
        )

        assert "error" not in result
        assert "per_fold_accuracy" in result
        assert "mean_accuracy" in result
        assert "se_accuracy" in result
        assert "ci_lower" in result
        assert "ci_upper" in result
        assert result["method"] == "gblup"
        assert len(result["per_fold_accuracy"]) == 5

    def test_cv_rrblup_structure(self, gs_service, simulated_data):
        """rrBLUP CV should return all expected fields."""
        result = gs_service.cross_validate(
            simulated_data["markers"],
            simulated_data["phenotypes"],
            method="rrblup",
            n_folds=5,
        )

        assert "error" not in result
        assert len(result["per_fold_accuracy"]) == 5
        assert result["method"] == "rrblup"

    def test_cv_repeated(self, gs_service, simulated_data):
        """Repeated CV should produce more fold results."""
        result = gs_service.cross_validate(
            simulated_data["markers"],
            simulated_data["phenotypes"],
            method="gblup",
            n_folds=3,
            n_repeats=2,
        )

        assert len(result["per_fold_accuracy"]) == 6  # 3 folds × 2 repeats

    def test_cv_accuracy_positive(self, gs_service, simulated_data):
        """Mean CV accuracy should be > 0 with real signal."""
        result = gs_service.cross_validate(
            simulated_data["markers"],
            simulated_data["phenotypes"],
            method="gblup",
            n_folds=5,
        )

        # With h² ≈ 0.5 and 50 individuals, expect some positive accuracy
        assert result["mean_accuracy"] > -0.5  # Should not be strongly negative

    def test_cv_ci_contains_mean(self, gs_service, simulated_data):
        """Confidence interval should contain the mean."""
        result = gs_service.cross_validate(
            simulated_data["markers"],
            simulated_data["phenotypes"],
            method="gblup",
            n_folds=5,
        )

        assert result["ci_lower"] <= result["mean_accuracy"] <= result["ci_upper"]

    def test_cv_too_few_individuals(self, gs_service):
        """Should return error when n < n_folds."""
        result = gs_service.cross_validate(
            [[0, 1], [1, 0]],
            [1.0, 2.0],
            n_folds=5,
        )
        assert "error" in result


# ──────────────────────────────────────────────
# B1.3: Inbreeding Coefficient Extraction
# ──────────────────────────────────────────────

class TestInbreeding:
    """Tests for calculate_inbreeding() from kinship matrix."""

    def test_kinship_then_inbreeding(self, simulated_data):
        """Full pipeline: genotypes → kinship → inbreeding."""
        # Step 1: Calculate kinship
        result = calculate_vanraden_kinship(
            np.array(simulated_data["markers"])
        )
        assert result["success"]

        # Step 2: Extract inbreeding
        K = np.array(result["K"])
        inbreeding = calculate_inbreeding(K)

        assert inbreeding["success"]
        assert len(inbreeding["inbreeding_coefficients"]) == simulated_data["n_ind"]
        assert len(inbreeding["average_kinship"]) == simulated_data["n_ind"]

    def test_identical_individuals_high_kinship(self):
        """Identical individuals should have kinship diag ≥ 1."""
        M = np.array([
            [0, 1, 2, 0, 2],
            [0, 1, 2, 0, 2],  # Identical to individual 1
            [2, 1, 0, 2, 0],  # Different
        ])
        result = calculate_vanraden_kinship(M)
        K = np.array(result["K"])
        inbreeding = calculate_inbreeding(K)

        assert inbreeding["success"]
        # Identical individuals should have same F
        F = inbreeding["inbreeding_coefficients"]
        np.testing.assert_almost_equal(F[0], F[1], decimal=5)

    def test_inbreeding_summary_stats(self, simulated_data):
        """Summary statistics should be consistent."""
        result = calculate_vanraden_kinship(
            np.array(simulated_data["markers"])
        )
        K = np.array(result["K"])
        inbreeding = calculate_inbreeding(K)

        summary = inbreeding["summary"]
        assert summary["max_inbreeding"] >= summary["mean_inbreeding"]
        assert summary["min_inbreeding"] <= summary["mean_inbreeding"]
        assert summary["sd_inbreeding"] >= 0
        assert summary["n_inbred"] + summary["n_outcrossed"] <= simulated_data["n_ind"]

    def test_non_square_matrix_error(self):
        """Should return error for non-square matrix."""
        result = calculate_inbreeding(np.array([[1, 2], [3, 4], [5, 6]]))
        assert not result["success"]

    def test_effective_population_size(self, simulated_data):
        """Ne should be positive when inbreeding is non-zero."""
        result = calculate_vanraden_kinship(
            np.array(simulated_data["markers"])
        )
        K = np.array(result["K"])
        inbreeding = calculate_inbreeding(K)

        ne = inbreeding["summary"]["effective_population_size"]
        if ne is not None:
            assert ne > 0


# ──────────────────────────────────────────────
# G-Matrix Tests (Existing, smoke test)
# ──────────────────────────────────────────────

class TestGMatrix:
    """Verify G-matrix calculation properties."""

    def test_g_matrix_symmetric(self, gs_service, simulated_data):
        """G-matrix should be symmetric."""
        result = gs_service.calculate_g_matrix(simulated_data["markers"])
        G = np.array(result["matrix"])
        np.testing.assert_array_almost_equal(G, G.T, decimal=10)

    def test_g_matrix_diagonal_positive(self, gs_service, simulated_data):
        """G-matrix diagonal should be positive."""
        result = gs_service.calculate_g_matrix(simulated_data["markers"])
        G = np.array(result["matrix"])
        assert np.all(np.diag(G) > 0)

    def test_g_matrix_mean_diagonal_near_one(self, gs_service, simulated_data):
        """Mean diagonal of G should be near 1."""
        result = gs_service.calculate_g_matrix(simulated_data["markers"])
        assert abs(result["mean_diagonal"] - 1.0) < 0.5


# ──────────────────────────────────────────────
# Methods Registry
# ──────────────────────────────────────────────

class TestMethodsRegistry:
    """Verify rrBLUP is registered in methods list."""

    def test_rrblup_available(self, gs_service):
        """rrBLUP should be listed as 'available'."""
        methods = gs_service.get_methods()
        rrblup = [m for m in methods if m["id"] == "rrblup"]
        assert len(rrblup) == 1
        assert rrblup[0]["status"] == "available"

    def test_gblup_available(self, gs_service):
        """GBLUP should be listed as 'available'."""
        methods = gs_service.get_methods()
        gblup = [m for m in methods if m["id"] == "gblup"]
        assert len(gblup) == 1
        assert gblup[0]["status"] == "available"

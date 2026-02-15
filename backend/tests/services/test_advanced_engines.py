"""
Tests for B6.2 NIRS Prediction, B6.3 Correlation Analysis, B6.4 SNP Clustering
"""

import pytest
import numpy as np
from app.services.nirs_prediction import nirs_prediction_service
from app.services.correlation_analysis import correlation_analysis_service
from app.services.snp_clustering import snp_clustering_service


# === B6.2: NIRS Prediction ===

class TestNIRSPrediction:

    def test_snv_preprocessing(self):
        """SNV should normalize each spectrum to mean=0, std=1."""
        spectra = np.random.rand(10, 100) * 1000 + 500
        processed = nirs_prediction_service.preprocess_spectra(spectra, method="snv")

        # Each row should have mean≈0, std≈1
        for i in range(10):
            assert abs(processed[i].mean()) < 1e-10
            assert abs(processed[i].std() - 1.0) < 1e-10

    def test_pls_fit_and_predict(self):
        """PLS should fit a linear trait-spectra relationship."""
        np.random.seed(42)
        n, p = 50, 100

        # Generate spectra and a trait that depends on first 5 wavelengths
        X = np.random.randn(n, p)
        true_coef = np.zeros(p)
        true_coef[:5] = np.array([3, -2, 1, 0.5, -1])
        y = X @ true_coef + np.random.normal(0, 0.5, n)

        model = nirs_prediction_service.fit_pls(X, y, n_components=5)

        assert model["r2_calibration"] > 0.8  # Good calibration expected
        assert model["n_samples"] == 50

        # Predict on training data (should be close)
        y_pred = nirs_prediction_service.predict(model, X)
        assert y_pred.shape == (n,)
        assert np.corrcoef(y, y_pred)[0, 1] > 0.9

    def test_derivative_preprocessing(self):
        """Derivative preprocessing should run without error."""
        spectra = np.random.rand(5, 50)
        processed = nirs_prediction_service.preprocess_spectra(
            spectra, method="derivative", deriv_order=1
        )
        assert processed.shape == spectra.shape


# === B6.3: Correlation Analysis ===

class TestCorrelationAnalysis:

    def test_pearson_with_known_correlation(self):
        """Pearson r should be ~1 for perfectly correlated data."""
        x = np.arange(100, dtype=float)
        y = 2 * x + 5

        result = correlation_analysis_service.pearson_with_pvalue(x, y)
        assert abs(result["r"] - 1.0) < 1e-10
        assert result["p_value"] < 0.001

    def test_spearman_with_monotonic(self):
        """Spearman rho should be 1 for any monotonic relationship."""
        x = np.arange(50, dtype=float)
        y = x ** 3  # Monotonic but nonlinear

        result = correlation_analysis_service.spearman_with_pvalue(x, y)
        assert abs(result["rho"] - 1.0) < 1e-10

    def test_correlation_matrix(self):
        """Matrix should have correct shape and diagonal = 1."""
        np.random.seed(10)
        n = 50
        data = {
            "yield": np.random.randn(n),
            "height": np.random.randn(n),
            "days_to_flower": np.random.randn(n),
        }

        result = correlation_analysis_service.correlation_matrix(data)
        assert len(result["trait_names"]) == 3
        assert len(result["r_matrix"]) == 3
        assert len(result["r_matrix"][0]) == 3
        assert len(result["significance"]) == 3

        # Diagonal should be 1
        for i in range(3):
            assert result["r_matrix"][i][i] == 1.0

    def test_nan_handling(self):
        """Should handle NaN values gracefully."""
        x = np.array([1, 2, np.nan, 4, 5], dtype=float)
        y = np.array([2, 4, 6, np.nan, 10], dtype=float)

        result = correlation_analysis_service.pearson_with_pvalue(x, y)
        assert result["n"] == 3  # Only 3 complete pairs


# === B6.4: SNP Clustering (Theta-R) ===

class TestSNPClustering:

    def test_theta_r_transform(self):
        """Theta should be 0 for (X>>0, Y=0) and ~1 for (X=0, Y>>0)."""
        x = np.array([100, 0, 50], dtype=float)
        y = np.array([0, 100, 50], dtype=float)

        theta, r = snp_clustering_service.theta_r_transform(x, y)

        assert theta[0] < 0.01       # AA: only allele A
        assert theta[1] > 0.99       # BB: only allele B
        assert abs(theta[2] - 0.5) < 0.01  # AB: equal mix
        assert r[0] == 100
        assert r[2] == 100

    def test_cluster_snp_three_groups(self):
        """Should separate clear AA, AB, BB clusters."""
        np.random.seed(7)
        n_per = 30

        # Simulate three clear clusters of theta
        theta_aa = np.random.normal(0.1, 0.02, n_per)
        theta_ab = np.random.normal(0.5, 0.02, n_per)
        theta_bb = np.random.normal(0.9, 0.02, n_per)

        theta = np.concatenate([theta_aa, theta_ab, theta_bb])
        r = np.ones(n_per * 3) * 2.0  # All high quality

        result = snp_clustering_service.cluster_snp(theta, r)

        assert result["call_rate"] == 1.0
        assert "AA" in result["cluster_stats"]
        assert "AB" in result["cluster_stats"]
        assert "BB" in result["cluster_stats"]

        # Check centroids are in expected order
        assert result["centroids"]["AA"] < result["centroids"]["AB"]
        assert result["centroids"]["AB"] < result["centroids"]["BB"]

    def test_batch_genotype_calling(self):
        """Batch calling should process multiple SNPs."""
        np.random.seed(99)
        n_snps, n_samples = 5, 60

        x = np.random.rand(n_snps, n_samples) * 100
        y = np.random.rand(n_snps, n_samples) * 100

        result = snp_clustering_service.call_genotypes(x, y)

        assert result["n_snps"] == 5
        assert result["n_samples"] == 60
        assert len(result["genotype_matrix"]) == 5
        assert result["mean_call_rate"] > 0

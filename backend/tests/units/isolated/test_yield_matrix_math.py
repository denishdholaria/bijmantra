
import unittest
import numpy as np
import sys
import os

# Ensure the app module can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../"))

from app.modules.breeding.compute.yield_prediction.yield_matrix_math import YieldMatrixMath

class TestYieldMatrixMath(unittest.TestCase):

    def test_fill_missing_values_zero(self):
        matrix = np.array([[1.0, np.nan], [2.0, 4.0]])
        result = YieldMatrixMath.fill_missing_values(matrix, method="zero")
        expected = np.array([[1.0, 0.0], [2.0, 4.0]])
        np.testing.assert_array_equal(result, expected)

    def test_fill_missing_values_mean(self):
        matrix = np.array([[1.0, np.nan], [3.0, 4.0], [2.0, 6.0]])
        # Col 1 mean: (4+6)/2 = 5.0
        result = YieldMatrixMath.fill_missing_values(matrix, method="mean")
        expected = np.array([[1.0, 5.0], [3.0, 4.0], [2.0, 6.0]])
        np.testing.assert_array_equal(result, expected)

    def test_fill_missing_values_median(self):
        matrix = np.array([[1.0, np.nan], [3.0, 4.0], [2.0, 10.0], [4.0, 6.0]])
        # Col 1: 4, 10, 6 -> median 6
        result = YieldMatrixMath.fill_missing_values(matrix, method="median")
        expected = np.array([[1.0, 6.0], [3.0, 4.0], [2.0, 10.0], [4.0, 6.0]])
        np.testing.assert_array_equal(result, expected)

    def test_normalize_matrix_axis0(self):
        # Column-wise normalization
        matrix = np.array([[1.0, 2.0], [3.0, 6.0], [2.0, 4.0]])
        # Col 0: 1, 3, 2 -> mean 2, std sqrt((1+1+0)/3) = sqrt(2/3) ~ 0.816
        # Col 1: 2, 6, 4 -> mean 4, std sqrt((4+4+0)/3) = sqrt(8/3) ~ 1.633

        result = YieldMatrixMath.normalize_matrix(matrix, axis=0)

        # Check means are 0 and stds are 1
        np.testing.assert_allclose(np.mean(result, axis=0), 0.0, atol=1e-7)
        np.testing.assert_allclose(np.std(result, axis=0), 1.0, atol=1e-7)

    def test_calculate_covariance_matrix(self):
        matrix = np.array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]])
        # Variables are columns. Perfectly correlated.
        # Covariance should be high.
        cov = YieldMatrixMath.calculate_covariance_matrix(matrix)
        self.assertEqual(cov.shape, (2, 2))
        self.assertAlmostEqual(cov[0, 1], cov[1, 0])
        self.assertTrue(cov[0, 1] > 0)

    def test_calculate_correlation_matrix(self):
        matrix = np.array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]])
        # Perfectly correlated
        corr = YieldMatrixMath.calculate_correlation_matrix(matrix)
        expected = np.array([[1.0, 1.0], [1.0, 1.0]])
        np.testing.assert_allclose(corr, expected, atol=1e-7)

    def test_apply_spatial_smoothing(self):
        # 3x3 matrix, 3x3 kernel
        matrix = np.array([
            [1.0, 1.0, 1.0],
            [1.0, 10.0, 1.0],
            [1.0, 1.0, 1.0]
        ])
        # Center pixel (1,1) should be smoothed.
        # Window sum = 18, count = 9, mean = 2.0

        result = YieldMatrixMath.apply_spatial_smoothing(matrix, kernel_size=3)

        self.assertAlmostEqual(result[1, 1], 2.0)

        # Corner (0,0) - due to padding (edge mode), it will be smoothed with padded values.
        # Original:
        # 1 1 1
        # 1 10 1
        # 1 1 1
        # Padded (edge):
        # 1 1 1 1 1
        # 1 1 1 1 1
        # 1 1 10 1 1
        # 1 1 1 1 1
        # 1 1 1 1 1
        # Window at (0,0) of original corresponds to top-left 3x3 of padded.
        # It includes (1,1) which is 10.
        # R0 (pad): 1 1 1
        # R1 (row0): 1 1 1
        # R2 (row1): 1 1 10
        # Sum = 18, Mean = 2.0
        self.assertAlmostEqual(result[0, 0], 2.0)

    def test_apply_spatial_smoothing_nan(self):
        matrix = np.array([
            [1.0, 1.0, 1.0],
            [1.0, np.nan, 1.0],
            [1.0, 1.0, 1.0]
        ])
        # Center should ignore nan. Sum = 8, count = 8 => mean = 1.0
        result = YieldMatrixMath.apply_spatial_smoothing(matrix, kernel_size=3)
        self.assertAlmostEqual(result[1, 1], 1.0)

if __name__ == '__main__':
    unittest.main()

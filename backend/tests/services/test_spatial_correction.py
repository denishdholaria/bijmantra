"""
Tests for Spatial Correction Service (SpATS)
"""

import pytest
import numpy as np
from app.services.spatial_correction import spatial_correction_service


class TestSpatialCorrection:

    def test_fit_spatial_trend_basic(self):
        """Test basic 2D spatial trend fitting on synthetic field data."""
        # Create a 5x5 field with a known gradient (values increase with row)
        rows = []
        cols = []
        values = []
        
        for r in range(1, 6):
            for c in range(1, 6):
                rows.append(r)
                cols.append(c)
                # True value = 10*row + noise
                values.append(10 * r + np.random.normal(0, 1))
        
        rows = np.array(rows, dtype=float)
        cols = np.array(cols, dtype=float)
        values = np.array(values, dtype=float)
        
        result = spatial_correction_service.fit_spatial_trend(rows, cols, values)
        
        assert "fitted_trend" in result
        assert "corrected_values" in result
        assert "diagnostics" in result
        assert len(result["fitted_trend"]) == 25
        assert len(result["corrected_values"]) == 25
        
        # The spatial trend should explain most of the variance
        r_sq = result["diagnostics"]["r_squared"]
        assert r_sq > 0.5  # Strong row gradient should be captured

    def test_correct_phenotypes_dict_api(self):
        """Test the high-level dict-based API."""
        data = []
        for r in range(1, 4):
            for c in range(1, 4):
                data.append({
                    "row": r,
                    "column": c,
                    "value": r * 5 + c * 2 + np.random.normal(0, 0.5),
                    "genotype": f"G{r}{c}"
                })
        
        result = spatial_correction_service.correct_phenotypes(data)
        
        assert "corrected_data" in result
        assert "diagnostics" in result
        assert len(result["corrected_data"]) == 9
        
        # Each corrected item should have the new fields
        item = result["corrected_data"][0]
        assert "spatial_trend" in item
        assert "corrected_value" in item
        assert "genotype" in item  # Original data preserved

    def test_residuals_have_reduced_variance(self):
        """After removing spatial trend, residual variance should be smaller."""
        rows = np.repeat(np.arange(1, 11), 10).astype(float)
        cols = np.tile(np.arange(1, 11), 10).astype(float)
        
        # Strong spatial gradient
        trend = 5 * rows + 3 * cols
        noise = np.random.normal(0, 2, len(rows))
        values = trend + noise
        
        result = spatial_correction_service.fit_spatial_trend(rows, cols, values)
        
        original_var = np.var(values)
        residual_var = result["diagnostics"]["residual_variance"]
        
        # Residual variance should be much less than original
        assert residual_var < original_var

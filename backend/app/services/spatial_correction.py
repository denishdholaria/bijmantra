"""
Spatial Correction Service (SpATS-inspired)

Implements spatial trend correction for field trials using 2D smoothing.
This is an ADDITIVE module — does NOT modify existing spatial_analysis.py.

Methods:
- fit_spatial_trend: 2D surface fit using row/column coordinates
- correct_phenotypes: Remove spatial trend from raw phenotypic values
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from scipy.interpolate import RectBivariateSpline
from scipy.ndimage import uniform_filter
import logging

logger = logging.getLogger(__name__)


class SpatialCorrectionService:
    """
    SpATS-inspired spatial trend correction.
    
    Uses 2D B-spline smoothing to estimate and remove spatial trends
    from field trial data, producing spatially-adjusted phenotypes.
    """
    
    def fit_spatial_trend(
        self,
        rows: np.ndarray,
        cols: np.ndarray,
        values: np.ndarray,
        n_knots_row: int = 10,
        n_knots_col: int = 10,
        smoothing: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Fit a 2D spatial surface to field data.
        
        Args:
            rows: Row coordinates (1D array, length N)
            cols: Column coordinates (1D array, length N) 
            values: Phenotypic values (1D array, length N)
            n_knots_row: Number of spline knots along rows
            n_knots_col: Number of spline knots along columns
            smoothing: Smoothing parameter (higher = smoother)
            
        Returns:
            Dict with fitted surface, residuals, and diagnostics
        """
        n = len(values)
        
        if n < 4:
            raise ValueError("Need at least 4 data points for spatial fitting")
        
        # Build grid from unique row/col values
        unique_rows = np.sort(np.unique(rows))
        unique_cols = np.sort(np.unique(cols))
        
        n_rows = len(unique_rows)
        n_cols = len(unique_cols)
        
        # Create matrix of values on the grid
        # Handle missing cells with NaN
        grid = np.full((n_rows, n_cols), np.nan)
        row_idx_map = {r: i for i, r in enumerate(unique_rows)}
        col_idx_map = {c: i for i, c in enumerate(unique_cols)}
        
        for i in range(n):
            ri = row_idx_map[rows[i]]
            ci = col_idx_map[cols[i]]
            grid[ri, ci] = values[i]
        
        # Fill NaN with column/row means for fitting
        col_means = np.nanmean(grid, axis=0)
        for j in range(n_cols):
            mask = np.isnan(grid[:, j])
            grid[mask, j] = col_means[j] if not np.isnan(col_means[j]) else np.nanmean(values)
        
        # Fit 2D B-spline
        # Adjust knot count to available data
        kx = min(3, n_rows - 1)
        ky = min(3, n_cols - 1)
        
        try:
            spline = RectBivariateSpline(
                unique_rows, unique_cols, grid,
                kx=kx, ky=ky,
                s=smoothing * n_rows * n_cols
            )
            
            # Evaluate fitted surface at original data points
            fitted = np.array([
                spline(rows[i], cols[i])[0, 0] for i in range(n)
            ])
            
        except Exception as e:
            logger.warning(f"B-spline fitting failed ({e}), falling back to moving average")
            # Fallback: 2D moving average
            smoothed_grid = uniform_filter(grid, size=3, mode='reflect')
            fitted = np.array([
                smoothed_grid[row_idx_map[rows[i]], col_idx_map[cols[i]]]
                for i in range(n)
            ])
        
        # Residuals = observed - fitted (spatially corrected values)
        residuals = values - fitted
        
        # Diagnostics
        ss_total = np.sum((values - np.mean(values)) ** 2)
        ss_residual = np.sum(residuals ** 2)
        r_squared = 1.0 - (ss_residual / ss_total) if ss_total > 0 else 0.0
        
        return {
            "fitted_trend": fitted.tolist(),
            "corrected_values": residuals.tolist(),
            "diagnostics": {
                "r_squared": float(r_squared),
                "trend_variance": float(np.var(fitted)),
                "residual_variance": float(np.var(residuals)),
                "n_observations": int(n),
                "spatial_heterogeneity_pct": float(r_squared * 100),
            }
        }
    
    def correct_phenotypes(
        self,
        data: List[Dict[str, Any]],
        row_key: str = "row",
        col_key: str = "column",
        value_key: str = "value",
        smoothing: float = 1.0,
    ) -> Dict[str, Any]:
        """
        High-level API: correct phenotypic values for spatial trends.
        
        Args:
            data: List of dicts with row, column, value keys
            row_key: Key for row coordinate
            col_key: Key for column coordinate
            value_key: Key for phenotypic value
            smoothing: Smoothing parameter
            
        Returns:
            Dict with corrected data and diagnostics
        """
        rows = np.array([d[row_key] for d in data], dtype=float)
        cols = np.array([d[col_key] for d in data], dtype=float)
        values = np.array([d[value_key] for d in data], dtype=float)
        
        result = self.fit_spatial_trend(rows, cols, values, smoothing=smoothing)
        
        # Build corrected data list
        corrected_data = []
        for i, d in enumerate(data):
            corrected = dict(d)
            corrected["spatial_trend"] = result["fitted_trend"][i]
            corrected["corrected_value"] = result["corrected_values"][i]
            corrected_data.append(corrected)
        
        return {
            "corrected_data": corrected_data,
            "diagnostics": result["diagnostics"],
        }


# Singleton
spatial_correction_service = SpatialCorrectionService()

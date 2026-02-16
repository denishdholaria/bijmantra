"""
NIRS Prediction Service

Near-Infrared Spectroscopy (NIRS) prediction engine for quality traits.
Implements PLS (Partial Least Squares) regression on spectral data.

Methods:
- preprocess_spectra: SNV, MSC, derivatives
- fit_pls: Train PLS model on calibration data
- predict: Apply trained model to new spectra
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy.signal import savgol_filter
import logging

logger = logging.getLogger(__name__)


class NIRSPredictionService:
    """
    NIRS calibration and prediction for quality traits.

    Supports spectral preprocessing (SNV, 1st/2nd derivative)
    and PLS regression for trait prediction.
    """

    def preprocess_spectra(
        self,
        spectra: np.ndarray,
        method: str = "snv",
        deriv_order: int = 1,
        window: int = 11,
        polyorder: int = 2,
    ) -> np.ndarray:
        """
        Preprocess spectral matrix.

        Args:
            spectra: (n_samples, n_wavelengths) matrix
            method: 'snv', 'derivative', 'msc', or 'raw'
            deriv_order: Derivative order (1 or 2)
            window: Savitzky-Golay window length
            polyorder: Savitzky-Golay polynomial order

        Returns:
            Preprocessed spectra, same shape
        """
        if method == "raw":
            return spectra.copy()

        if method == "snv":
            # Standard Normal Variate
            means = spectra.mean(axis=1, keepdims=True)
            stds = spectra.std(axis=1, keepdims=True)
            stds[stds == 0] = 1.0
            return (spectra - means) / stds

        if method == "derivative":
            # Savitzky-Golay derivative
            if window >= spectra.shape[1]:
                window = max(5, spectra.shape[1] // 2 * 2 - 1)
            return savgol_filter(spectra, window, polyorder, deriv=deriv_order, axis=1)

        if method == "msc":
            # Multiplicative Scatter Correction
            mean_spectrum = spectra.mean(axis=0)
            corrected = np.zeros_like(spectra)
            for i in range(spectra.shape[0]):
                fit = np.polyfit(mean_spectrum, spectra[i], 1)
                corrected[i] = (spectra[i] - fit[1]) / fit[0]
            return corrected

        raise ValueError(f"Unknown preprocessing method: {method}")

    def fit_pls(
        self,
        X: np.ndarray,
        y: np.ndarray,
        n_components: int = 10,
    ) -> Dict[str, Any]:
        """
        Fit PLS regression using NIPALS algorithm.

        Args:
            X: Preprocessed spectra (n_samples, n_wavelengths)
            y: Reference values (n_samples,)
            n_components: Number of PLS components

        Returns:
            Model dict with weights, loadings, and coefficients
        """
        n, p = X.shape
        n_components = min(n_components, min(n, p))

        # Center
        X_mean = X.mean(axis=0)
        y_mean = y.mean()
        Xc = X - X_mean
        yc = y - y_mean

        # NIPALS PLS1
        W = np.zeros((p, n_components))  # X weights
        P = np.zeros((p, n_components))  # X loadings
        T = np.zeros((n, n_components))  # X scores
        Q = np.zeros(n_components)        # y loadings

        E = Xc.copy()
        f = yc.copy()

        for a in range(n_components):
            # Weight vector
            w = E.T @ f
            w_norm = np.linalg.norm(w)
            if w_norm < 1e-10:
                n_components = a
                W = W[:, :a]
                P = P[:, :a]
                T = T[:, :a]
                Q = Q[:a]
                break
            w = w / w_norm

            # Score
            t = E @ w
            t_sq = t @ t
            if t_sq < 1e-10:
                n_components = a
                break

            # Loadings
            p_load = E.T @ t / t_sq
            q_load = f @ t / t_sq

            # Deflate
            E = E - np.outer(t, p_load)
            f = f - t * q_load

            W[:, a] = w
            P[:, a] = p_load
            T[:, a] = t
            Q[a] = q_load

        # Regression coefficients: B = W(P'W)^-1 * Q
        PW = P.T @ W
        try:
            B = W @ np.linalg.solve(PW, np.diag(Q))
            B = B.sum(axis=1)
        except np.linalg.LinAlgError:
            B = np.zeros(p)

        # Calculate R² on calibration
        y_pred = (X - X_mean) @ B + y_mean
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        r2_cal = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        rmse_cal = np.sqrt(ss_res / n)

        return {
            "coefficients": B,
            "x_mean": X_mean,
            "y_mean": float(y_mean),
            "n_components": n_components,
            "r2_calibration": float(r2_cal),
            "rmse_calibration": float(rmse_cal),
            "n_samples": int(n),
            "n_wavelengths": int(p),
        }

    def predict(
        self, model: Dict[str, Any], X_new: np.ndarray
    ) -> np.ndarray:
        """
        Predict trait values using a fitted PLS model.

        Args:
            model: Dict from fit_pls
            X_new: New spectra (n_samples, n_wavelengths)

        Returns:
            Predicted values (n_samples,)
        """
        B = model["coefficients"]
        X_mean = model["x_mean"]
        y_mean = model["y_mean"]

        return (X_new - X_mean) @ B + y_mean

    def cross_validate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        n_components: int = 10,
        n_folds: int = 5,
        preprocess: str = "snv",
    ) -> Dict[str, Any]:
        """
        Leave-group-out cross-validation for PLS.

        Args:
            X: Raw spectra
            y: Reference values
            n_components: Max PLS components
            n_folds: Number of CV folds
            preprocess: Preprocessing method

        Returns:
            CV statistics
        """
        n = len(y)
        indices = np.arange(n)
        np.random.shuffle(indices)
        fold_size = n // n_folds

        y_pred_cv = np.zeros(n)

        for fold in range(n_folds):
            start = fold * fold_size
            end = start + fold_size if fold < n_folds - 1 else n

            val_idx = indices[start:end]
            train_idx = np.concatenate([indices[:start], indices[end:]])

            X_train = self.preprocess_spectra(X[train_idx], method=preprocess)
            X_val = self.preprocess_spectra(X[val_idx], method=preprocess)

            model = self.fit_pls(X_train, y[train_idx], n_components)
            y_pred_cv[val_idx] = self.predict(model, X_val)

        ss_res = np.sum((y - y_pred_cv) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2_cv = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        rmse_cv = np.sqrt(ss_res / n)

        return {
            "r2_cv": float(r2_cv),
            "rmse_cv": float(rmse_cv),
            "n_folds": n_folds,
            "n_components": n_components,
            "preprocess": preprocess,
        }


# Singleton
nirs_prediction_service = NIRSPredictionService()

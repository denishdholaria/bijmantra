"""
Yield Environmental Covariate Matrix Service

Calculates environmental relationship matrices (Omega matrix)
for GxE analysis and yield prediction.

Features:
- Aggregates daily weather data into seasonal covariates.
- Computes relationship matrix using standardized covariates.
- Supports Linear and Gaussian (RBF) kernels.
"""

import logging
import numpy as np
from pydantic import BaseModel
from typing import Optional

# Import TemperatureData from weather integration service
# Assuming app structure allows this import
from app.modules.environment.services.weather_integration_service import TemperatureData

logger = logging.getLogger(__name__)

class EnvironmentalCovariates(BaseModel):
    """
    Aggregated environmental covariates for a specific environment (location/year).
    """
    environment_id: str
    mean_temperature: float
    total_precipitation: float
    gdd: float
    mean_humidity: Optional[float] = None
    mean_wind_speed: Optional[float] = None
    # Add more as needed (e.g., solar radiation if available)

class YieldEnvCovariateService:
    def calculate_covariates(self, environment_id: str, weather_data: list[TemperatureData], base_temp: float = 10.0) -> EnvironmentalCovariates:
        """
        Calculate aggregated environmental covariates from daily weather data.

        Args:
            environment_id: Unique identifier for the environment.
            weather_data: List of daily TemperatureData objects.
            base_temp: Base temperature for GDD calculation (default 10.0°C).

        Returns:
            EnvironmentalCovariates object.
        """
        if not weather_data:
            logger.warning(f"No weather data provided for environment {environment_id}")
            return EnvironmentalCovariates(
                environment_id=environment_id,
                mean_temperature=0.0,
                total_precipitation=0.0,
                gdd=0.0
            )

        total_temp = 0.0
        total_precip = 0.0
        total_gdd = 0.0
        total_humidity = 0.0
        total_wind = 0.0

        # Valid data counters
        temp_count = 0
        humidity_count = 0
        wind_count = 0

        for day in weather_data:
            # Temperature & GDD
            # Prefer avg, fallback to (max+min)/2, fallback to 0
            t_avg = day.temp_avg
            if t_avg is None:
                if day.temp_max is not None and day.temp_min is not None:
                    t_avg = (day.temp_max + day.temp_min) / 2.0

            if t_avg is not None:
                total_temp += t_avg
                gdd = max(0.0, t_avg - base_temp)
                total_gdd += gdd
                temp_count += 1

            # Precipitation
            if day.precipitation is not None:
                total_precip += day.precipitation

            # Humidity
            if day.humidity is not None:
                total_humidity += day.humidity
                humidity_count += 1

            # Wind Speed
            if day.wind_speed is not None:
                total_wind += day.wind_speed
                wind_count += 1

        mean_temp = total_temp / temp_count if temp_count > 0 else 0.0
        mean_humidity = total_humidity / humidity_count if humidity_count > 0 else None
        mean_wind_speed = total_wind / wind_count if wind_count > 0 else None

        return EnvironmentalCovariates(
            environment_id=environment_id,
            mean_temperature=mean_temp,
            total_precipitation=total_precip,
            gdd=total_gdd,
            mean_humidity=mean_humidity,
            mean_wind_speed=mean_wind_speed
        )

    def compute_relationship_matrix(self, covariates: list[EnvironmentalCovariates], kernel: str = "linear", length_scale: float = 1.0) -> np.ndarray:
        """
        Compute the environmental relationship matrix (Omega).

        Args:
            covariates: List of EnvironmentalCovariates objects.
            kernel: Kernel function ("linear" or "gaussian").
            length_scale: Length scale for Gaussian kernel.

        Returns:
            Symmetric matrix (n_env x n_env).
        """
        n = len(covariates)
        if n == 0:
            return np.array([])

        # Extract feature matrix X (n_env x n_features)
        features = []
        for cov in covariates:
            # Handle None values by replacing with 0.0 for matrix calculation
            # Ideally, we should impute, but 0.0 is safe for now if standardized later
            row = [
                cov.mean_temperature,
                cov.total_precipitation,
                cov.gdd,
                cov.mean_humidity if cov.mean_humidity is not None else 0.0,
                cov.mean_wind_speed if cov.mean_wind_speed is not None else 0.0
            ]
            features.append(row)

        X = np.array(features)

        # Standardize features (mean=0, std=1)
        mean = np.mean(X, axis=0)
        std = np.std(X, axis=0)

        # Prevent division by zero for constant features
        std[std == 0] = 1.0

        X_std = (X - mean) / std

        if kernel == "linear":
            # Linear kernel: K = X * X^T / m
            # Where m is number of features
            m = X.shape[1]
            return np.dot(X_std, X_std.T) / m

        elif kernel == "gaussian":
            # Gaussian (RBF) kernel: K(x, y) = exp(-||x - y||^2 / (2 * length_scale^2))
            # Efficient pairwise distance calculation
            # ||x - y||^2 = ||x||^2 + ||y||^2 - 2<x, y>

            X_sq = np.sum(X_std**2, axis=1)
            dist_sq = X_sq[:, np.newaxis] + X_sq[np.newaxis, :] - 2 * np.dot(X_std, X_std.T)

            # Ensure non-negative distances (numerical stability)
            dist_sq = np.maximum(dist_sq, 0.0)

            K = np.exp(-dist_sq / (2 * length_scale**2))
            return K

        else:
            raise ValueError(f"Unknown kernel type: {kernel}")

# Singleton instance
yield_env_covariate_service = YieldEnvCovariateService()

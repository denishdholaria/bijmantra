import pytest
import numpy as np
from datetime import date
from app.modules.genomics.compute.analytics.yield_env_covariate_matrix import (
    YieldEnvCovariateService,
    EnvironmentalCovariates,
    yield_env_covariate_service
)
from app.modules.environment.services.weather_integration_service import TemperatureData, WeatherProvider

@pytest.fixture
def mock_weather_data():
    return [
        TemperatureData(
            date=date(2023, 1, 1),
            temp_max=20.0,
            temp_min=10.0,
            temp_avg=15.0,
            source=WeatherProvider.CACHED,
            precipitation=5.0,
            humidity=50.0,
            wind_speed=10.0
        ),
        TemperatureData(
            date=date(2023, 1, 2),
            temp_max=25.0,
            temp_min=15.0,
            temp_avg=20.0,
            source=WeatherProvider.CACHED,
            precipitation=0.0,
            humidity=60.0,
            wind_speed=5.0
        )
    ]

def test_calculate_covariates(mock_weather_data):
    cov = yield_env_covariate_service.calculate_covariates("env1", mock_weather_data, base_temp=10.0)

    assert cov.environment_id == "env1"
    assert cov.mean_temperature == 17.5  # (15 + 20) / 2
    assert cov.total_precipitation == 5.0
    assert cov.gdd == 15.0  # (15-10) + (20-10) = 5 + 10 = 15
    assert cov.mean_humidity == 55.0
    assert cov.mean_wind_speed == 7.5

def test_calculate_covariates_empty():
    cov = yield_env_covariate_service.calculate_covariates("env_empty", [])
    assert cov.mean_temperature == 0.0
    assert cov.total_precipitation == 0.0
    assert cov.gdd == 0.0

def test_compute_relationship_matrix_linear():
    cov1 = EnvironmentalCovariates(
        environment_id="env1",
        mean_temperature=20.0,
        total_precipitation=100.0,
        gdd=200.0,
        mean_humidity=50.0,
        mean_wind_speed=10.0
    )
    # Use distinct covariates to check correlation
    cov3 = EnvironmentalCovariates(
        environment_id="env3",
        mean_temperature=30.0,
        total_precipitation=200.0,
        gdd=400.0,
        mean_humidity=60.0,
        mean_wind_speed=20.0
    )

    covariates = [cov1, cov3]
    # cov1: [20, 100, 200, 50, 10]
    # cov3: [30, 200, 400, 60, 20]
    # Means: [25, 150, 300, 55, 15]
    # Std: [5, 50, 100, 5, 5]

    # X_std1: [-1, -1, -1, -1, -1]
    # X_std3: [1, 1, 1, 1, 1]

    # K = X_std * X_std.T / m
    # K[0,0] = (-1*-1 + ... ) / 5 = 5/5 = 1.0
    # K[0,1] = (-1*1 + ... ) / 5 = -5/5 = -1.0

    K = yield_env_covariate_service.compute_relationship_matrix(covariates, kernel="linear")

    assert K.shape == (2, 2)
    assert np.isclose(K[0, 0], 1.0)
    assert np.isclose(K[0, 1], -1.0)
    assert np.isclose(K[1, 1], 1.0)

def test_compute_relationship_matrix_gaussian():
    cov1 = EnvironmentalCovariates(
        environment_id="env1",
        mean_temperature=20.0,
        total_precipitation=100.0,
        gdd=200.0,
        mean_humidity=50.0,
        mean_wind_speed=10.0
    )
    cov2 = EnvironmentalCovariates(
        environment_id="env2",
        mean_temperature=20.0,
        total_precipitation=100.0,
        gdd=200.0,
        mean_humidity=50.0,
        mean_wind_speed=10.0
    )

    covariates = [cov1, cov2]
    K = yield_env_covariate_service.compute_relationship_matrix(covariates, kernel="gaussian")

    # Distance is 0, exp(0) = 1
    assert np.allclose(K, np.ones((2, 2)))

def test_compute_relationship_matrix_empty():
    K = yield_env_covariate_service.compute_relationship_matrix([])
    assert K.size == 0

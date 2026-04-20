
"""
Tests for Cross Prediction Service
"""

import pytest
from app.modules.breeding.services.cross_prediction_service import CrossPredictionService

class TestCrossMeanPrediction:
    """Tests for predict_cross_mean()"""

    @pytest.fixture
    def service(self):
        return CrossPredictionService()

    def test_predict_cross_mean_positive(self, service):
        """Test with positive values"""
        result = service.predict_cross_mean(10.0, 20.0)
        assert result == 15.0

    def test_predict_cross_mean_negative(self, service):
        """Test with negative values"""
        result = service.predict_cross_mean(-10.0, -20.0)
        assert result == -15.0

    def test_predict_cross_mean_mixed(self, service):
        """Test with mixed positive and negative values"""
        result = service.predict_cross_mean(-10.0, 10.0)
        assert result == 0.0

    def test_predict_cross_mean_zero(self, service):
        """Test with zero values"""
        result = service.predict_cross_mean(0.0, 0.0)
        assert result == 0.0

    def test_predict_cross_mean_float(self, service):
        """Test with floating point values"""
        result = service.predict_cross_mean(10.5, 20.5)
        assert result == 15.5

    def test_predict_cross_mean_large_numbers(self, service):
        """Test with large numbers"""
        result = service.predict_cross_mean(1e6, 1e6)
        assert result == 1e6
# Instantiate the service for usefulness tests
service = CrossPredictionService()

def test_calculate_usefulness_basic():
    """Test basic usefulness calculation with positive values."""
    predicted_mean = 10.0
    predicted_variance = 4.0
    selection_intensity = 2.0

    # Expected: 10.0 + 2.0 * sqrt(4.0) = 10.0 + 2.0 * 2.0 = 14.0
    result = service.calculate_usefulness(
        predicted_mean,
        predicted_variance,
        selection_intensity
    )
    assert result == 14.0

def test_calculate_usefulness_zero_variance():
    """Test usefulness calculation with zero variance."""
    predicted_mean = 10.0
    predicted_variance = 0.0

    # Expected: 10.0 + 2.06 * sqrt(0) = 10.0
    result = service.calculate_usefulness(
        predicted_mean,
        predicted_variance
    )
    assert result == 10.0

def test_calculate_usefulness_negative_variance():
    """Test usefulness calculation with negative variance (should be treated as 0)."""
    predicted_mean = 10.0
    predicted_variance = -5.0

    # Expected: 10.0 + 2.06 * 0 = 10.0
    result = service.calculate_usefulness(
        predicted_mean,
        predicted_variance
    )
    assert result == 10.0

def test_calculate_usefulness_custom_intensity():
    """Test usefulness calculation with custom selection intensity."""
    predicted_mean = 10.0
    predicted_variance = 4.0
    selection_intensity = 1.5

    # Expected: 10.0 + 1.5 * sqrt(4.0) = 10.0 + 1.5 * 2.0 = 13.0
    result = service.calculate_usefulness(
        predicted_mean,
        predicted_variance,
        selection_intensity
    )
    assert result == 13.0

def test_calculate_usefulness_negative_mean():
    """Test usefulness calculation with negative mean."""
    predicted_mean = -5.0
    predicted_variance = 4.0
    selection_intensity = 2.0

    # Expected: -5.0 + 2.0 * sqrt(4.0) = -5.0 + 2.0 * 2.0 = -1.0
    result = service.calculate_usefulness(
        predicted_mean,
        predicted_variance,
        selection_intensity
    )
    assert result == -1.0

# backend/tests/services/test_data_quality_service.py
import pytest
from backend.app.services.data_quality_service import DataQualityService

def test_detect_outliers():
    service = DataQualityService()
    temps = [25, 26, 24, 25, 100, 25, 24]
    outliers, _ = service.detect_outliers(temps)
    assert outliers == [4]

def test_calculate_completeness():
    service = DataQualityService()
    data = [1, 2, None, 4, 5, None]
    completeness = service.calculate_completeness(data)
    assert completeness == 4 / 6

def test_validate_temperature_range():
    service = DataQualityService()
    assert service.validate_temperature_range(25)
    assert not service.validate_temperature_range(100)
    assert not service.validate_temperature_range(-60)

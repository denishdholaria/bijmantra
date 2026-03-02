"""
Tests for GDD API imports.
Verifies that the module can be imported correctly after refactoring imports.
"""

from app.api.v2.future import gdd

def test_gdd_module_imports():
    """Verify that the gdd module can be imported and has the expected attributes."""
    assert hasattr(gdd, "router")
    assert hasattr(gdd, "calculate_gdd")
    assert hasattr(gdd, "predict_growth_stages")
    assert hasattr(gdd, "calculate_cumulative_gdd")
    assert hasattr(gdd, "sync_weather_data")

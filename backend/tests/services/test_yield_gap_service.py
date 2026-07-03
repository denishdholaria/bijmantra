"""
Unit Tests for Yield Gap Service

Tests calculation logic for yield gap analysis.
"""

import pytest
from app.modules.breeding.services.yield_gap_service import yield_gap_service, YieldGapService

def test_identify_limiting_factors_no_factors():
    """Test that high indices result in no limiting factors."""
    env_data = {"water_index": 1.0, "temperature_index": 1.0}
    soil_data = {"nitrogen_index": 1.0, "phosphorus_index": 1.0}

    factors = yield_gap_service.identify_limiting_factors(env_data, soil_data)
    assert len(factors) == 0

def test_identify_limiting_factors_high_severity():
    """Test high severity factor identification."""
    # Water index 0.5 -> score 0.5 >= 0.35 -> High severity
    env_data = {"water_index": 0.5, "temperature_index": 1.0}
    soil_data = {"nitrogen_index": 1.0, "phosphorus_index": 1.0}

    factors = yield_gap_service.identify_limiting_factors(env_data, soil_data)

    assert len(factors) == 1
    assert factors[0].factor == "Water"
    assert factors[0].score == 0.5
    assert factors[0].severity == "high"
    assert factors[0].explanation == "Water is constraining yield by an estimated 50.0%."

def test_identify_limiting_factors_medium_severity():
    """Test medium severity factor identification."""
    # Nitrogen index 0.75 -> score 0.25 -> Medium severity (0.20 <= 0.25 < 0.35)
    env_data = {"water_index": 1.0, "temperature_index": 1.0}
    soil_data = {"nitrogen_index": 0.75, "phosphorus_index": 1.0}

    factors = yield_gap_service.identify_limiting_factors(env_data, soil_data)

    assert len(factors) == 1
    assert factors[0].factor == "Nitrogen"
    assert factors[0].score == 0.25
    assert factors[0].severity == "medium"
    assert factors[0].explanation == "Nitrogen is constraining yield by an estimated 25.0%."

def test_identify_limiting_factors_low_severity():
    """Test low severity factor identification."""
    # Phosphorus index 0.85 -> score 0.15 -> Low severity (0.05 < 0.15 < 0.20)
    env_data = {"water_index": 1.0, "temperature_index": 1.0}
    soil_data = {"nitrogen_index": 1.0, "phosphorus_index": 0.85}

    factors = yield_gap_service.identify_limiting_factors(env_data, soil_data)

    assert len(factors) == 1
    assert factors[0].factor == "Phosphorus"
    assert factors[0].score == 0.15
    assert factors[0].severity == "low"

def test_identify_limiting_factors_sorting():
    """Test that factors are sorted by score descending."""
    # Water: 0.4 (High), Nitrogen: 0.25 (Medium), Phosphorus: 0.15 (Low)
    env_data = {"water_index": 0.6, "temperature_index": 1.0}
    soil_data = {"nitrogen_index": 0.75, "phosphorus_index": 0.85}

    factors = yield_gap_service.identify_limiting_factors(env_data, soil_data)

    assert len(factors) == 3
    assert factors[0].factor == "Water"
    assert factors[0].score == 0.4

    assert factors[1].factor == "Nitrogen"
    assert factors[1].score == 0.25

    assert factors[2].factor == "Phosphorus"
    assert factors[2].score == 0.15

def test_identify_limiting_factors_edge_cases():
    """Test edge cases for clamping and missing keys."""
    # Missing keys should default to 1.0 -> score 0.0 -> ignored
    # Out of range values:
    # Temperature index -0.5 clamped to 0.0 -> score 1.0 -> High
    # Water index 1.5 clamped to 1.2 -> score -0.2 -> ignored

    env_data = {"temperature_index": -0.5, "water_index": 1.5}
    soil_data = {} # Missing nitrogen and phosphorus

    factors = yield_gap_service.identify_limiting_factors(env_data, soil_data)

    assert len(factors) == 1
    assert factors[0].factor == "Temperature"
    assert factors[0].score == 1.0
    assert factors[0].severity == "high"


class TestYieldGapCalculation:
    """Test yield gap calculation logic"""

    @pytest.fixture
    def service(self):
        """Fixture for YieldGapService"""
        return YieldGapService()

    def test_calculate_yield_gap_normal(self, service):
        """Test normal yield gap calculation (actual < potential)"""
        result = service.calculate_yield_gap(actual=5.0, potential=8.0)

        # Gap = 8.0 - 5.0 = 3.0
        # Pct = (3.0 / 8.0) * 100 = 37.5
        assert result["actual"] == 5.0
        assert result["potential"] == 8.0
        assert result["gap_absolute"] == 3.0
        assert result["gap_percent"] == 37.5

    def test_calculate_yield_gap_zero_gap(self, service):
        """Test zero yield gap (actual == potential)"""
        result = service.calculate_yield_gap(actual=8.0, potential=8.0)

        # Gap = 0.0
        # Pct = 0.0
        assert result["gap_absolute"] == 0.0
        assert result["gap_percent"] == 0.0

    def test_calculate_yield_gap_negative_gap(self, service):
        """Test negative yield gap (actual > potential)"""
        result = service.calculate_yield_gap(actual=9.0, potential=8.0)

        # Gap = max(8.0 - 9.0, 0.0) = 0.0
        # Pct = 0.0
        assert result["gap_absolute"] == 0.0
        assert result["gap_percent"] == 0.0

    def test_calculate_yield_gap_zero_potential(self, service):
        """Test zero potential yield (division by zero handling)"""
        result = service.calculate_yield_gap(actual=5.0, potential=0.0)

        # Gap = max(0.0 - 5.0, 0.0) = 0.0
        # Pct = safe_divide(0.0, 0.0) * 100 = 0.0
        assert result["gap_absolute"] == 0.0
        assert result["gap_percent"] == 0.0

    def test_calculate_yield_gap_zero_actual(self, service):
        """Test zero actual yield (100% gap)"""
        result = service.calculate_yield_gap(actual=0.0, potential=8.0)

        # Gap = 8.0 - 0.0 = 8.0
        # Pct = (8.0 / 8.0) * 100 = 100.0
        assert result["gap_absolute"] == 8.0
        assert result["gap_percent"] == 100.0

    def test_calculate_yield_gap_precision(self, service):
        """Test floating point precision handling"""
        # 1/3 actual, 1.0 potential
        actual = 1.0 / 3.0
        potential = 1.0

        result = service.calculate_yield_gap(actual=actual, potential=potential)

        # actual approx 0.333
        # potential 1.0
        # Gap = 1.0 - 0.3333... = 0.6666...
        # Pct = 66.66...

        # The service rounds results:
        # actual -> 3 decimals
        # potential -> 3 decimals
        # gap_absolute -> 3 decimals
        # gap_percent -> 2 decimals

        assert result["actual"] == pytest.approx(0.333, abs=0.001)
        assert result["gap_absolute"] == pytest.approx(0.667, abs=0.001)
        assert result["gap_percent"] == pytest.approx(66.67, abs=0.01)

    def test_calculate_yield_gap_very_small_potential(self, service):
        """Test very small potential yield to ensure stability"""
        result = service.calculate_yield_gap(actual=0.0, potential=1e-10)

        # gap_abs = 1e-10
        # gap_pct = (1e-10 / 1e-10) * 100 = 100.0

        # rounded to 3 decimal places -> 0.0
        assert result["gap_absolute"] == pytest.approx(0.0, abs=1e-9)
        assert result["gap_percent"] == 100.0

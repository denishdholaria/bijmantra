"""
Tests for Solar Service

Tests the scientific accuracy and correctness of photoperiod and solar calculations.
"""

import pytest
from datetime import date, timedelta
from app.modules.environment.services.solar_service import SolarService


class TestSolarService:
    """Test suite for Solar Service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = SolarService()

    def test_equator_equinox(self):
        """Test photoperiod at equator during equinox."""
        # March 21st (Spring Equinox)
        # Expected: ~12 hours day length
        result = self.service.calculate_photoperiod(0.0, date(2024, 3, 21))

        assert 11.9 <= result["day_length_hours"] <= 12.1
        assert result["sunrise"] is not None
        assert result["sunset"] is not None

    def test_london_summer_solstice(self):
        """Test photoperiod in London (51.5N) during summer solstice."""
        # June 21st
        # Expected: ~16.5 hours
        result = self.service.calculate_photoperiod(51.5, date(2024, 6, 21))

        assert result["day_length_hours"] > 16.0
        assert result["is_long_day"] is True
        assert "Long Day" in result["photoperiod_class"]

    def test_london_winter_solstice(self):
        """Test photoperiod in London (51.5N) during winter solstice."""
        # December 21st
        # Expected: ~7-8 hours
        result = self.service.calculate_photoperiod(51.5, date(2024, 12, 21))

        assert result["day_length_hours"] < 9.0
        assert result["is_long_day"] is False
        assert "Very Short" in result["photoperiod_class"]

    def test_polar_day(self):
        """Test polar day (24h daylight)."""
        # 80N in June
        result = self.service.calculate_photoperiod(80.0, date(2024, 6, 21))

        assert result["day_length_hours"] == 24.0
        assert result["sunrise"] == "00:00"
        assert result["sunset"] == "24:00"

    def test_polar_night(self):
        """Test polar night (0h daylight)."""
        # 80N in December
        result = self.service.calculate_photoperiod(80.0, date(2024, 12, 21))

        assert result["day_length_hours"] == 0.0
        assert result["sunrise"] == "--:--"
        assert result["sunset"] == "--:--"

    def test_southern_hemisphere(self):
        """Test southern hemisphere seasonality."""
        # Sydney (~34S)
        # December (Summer in South) -> Long Day
        summer_result = self.service.calculate_photoperiod(-34.0, date(2024, 12, 21))
        assert summer_result["day_length_hours"] > 14.0

        # June (Winter in South) -> Short Day
        winter_result = self.service.calculate_photoperiod(-34.0, date(2024, 6, 21))
        assert winter_result["day_length_hours"] < 10.5

    def test_default_date(self):
        """Test that method uses today's date if not provided."""
        result = self.service.calculate_photoperiod(45.0)
        today = date.today().isoformat()

        assert result["date"] == today

    def test_photoperiod_classification(self):
        """Test photoperiod classification categories."""
        # Use simple wrapper to access the logic indirectly via calculation
        # Or test private method if needed, but testing public interface is better.

        # > 14h -> Long Day
        r1 = self.service._classify_photoperiod(15.0)
        assert "Long Day" in r1

        # 12-14h -> Intermediate
        r2 = self.service._classify_photoperiod(13.0)
        assert "Intermediate" in r2

        # 10-12h -> Short Day
        r3 = self.service._classify_photoperiod(11.0)
        assert "Short Day" in r3

        # < 10h -> Very Short
        r4 = self.service._classify_photoperiod(9.0)
        assert "Very Short" in r4

    def test_get_photoperiod_series(self):
        """Test generating a series of photoperiod data."""
        days = 10
        start_date = date(2024, 1, 1)
        series = self.service.get_photoperiod_series(45.0, start_date, days=days)

        assert len(series) == days
        assert series[0]["date"] == start_date.isoformat()
        assert series[-1]["date"] == (start_date + timedelta(days=days-1)).isoformat()
        assert "day_length" in series[0]

if __name__ == "__main__":
    pytest.main([__file__])

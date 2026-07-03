"""
Tests for GDD Calculator Service

Tests the scientific accuracy and correctness of Growing Degree Day calculations.
"""

import pytest
import logging
from datetime import date, timedelta
from app.modules.environment.services.gdd_calculator_service import (
    GDDCalculatorService,
    TemperatureData,
    DataQuality,
    CropType,
)


class TestGDDCalculatorService:
    """Test suite for GDD Calculator Service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = GDDCalculatorService()

    def test_basic_gdd_calculation(self):
        """Test basic GDD calculation with known values."""
        # Test case: Tmax=25°C, Tmin=15°C, Tbase=10°C
        # Expected: GDD = max(0, (25+15)/2 - 10) = max(0, 20-10) = 10
        gdd, metadata = self.service.calculate_daily_gdd(25.0, 15.0, 10.0)

        assert gdd == 10.0
        assert metadata["average_temperature"] == 20.0
        assert metadata["base_exceeded"] is True
        assert "GDD = max(0, (Tmax + Tmin) / 2 - Tbase)" in metadata["formula"]

    def test_gdd_below_base_temperature(self):
        """Test GDD calculation when temperature is below base."""
        # Test case: Tmax=5°C, Tmin=2°C, Tbase=10°C
        # Expected: GDD = max(0, (5+2)/2 - 10) = max(0, 3.5-10) = 0
        gdd, metadata = self.service.calculate_daily_gdd(5.0, 2.0, 10.0)

        assert gdd == 0.0
        assert metadata["average_temperature"] == 3.5
        assert metadata["base_exceeded"] is False

    def test_wheat_base_temperature(self):
        """Test GDD calculation with wheat base temperature (0°C)."""
        # Test case: Tmax=8°C, Tmin=2°C, Tbase=0°C
        # Expected: GDD = max(0, (8+2)/2 - 0) = 5
        gdd, metadata = self.service.calculate_daily_gdd(8.0, 2.0, 0.0)

        assert gdd == 5.0
        assert metadata["average_temperature"] == 5.0
        assert metadata["base_exceeded"] is True

    def test_invalid_temperature_input(self):
        """Test error handling for invalid temperature inputs."""
        with pytest.raises(ValueError, match="Maximum temperature.*cannot be less than minimum"):
            self.service.calculate_daily_gdd(10.0, 15.0, 10.0)  # Tmax < Tmin

    def test_crop_base_temperatures(self):
        """Test that crop base temperatures are correctly defined."""
        assert self.service.get_crop_base_temperature("corn") == 10.0
        assert self.service.get_crop_base_temperature("wheat") == 0.0
        assert self.service.get_crop_base_temperature("rice") == 10.0
        assert self.service.get_crop_base_temperature("cotton") == 15.5
        assert self.service.get_crop_base_temperature("soybean") == 10.0

    def test_cumulative_gdd_calculation(self):
        """Test cumulative GDD calculation over multiple days."""
        # Create test temperature data
        temp_data = [
            TemperatureData(date(2024, 6, 1), 25.0, 15.0, source="test"),
            TemperatureData(date(2024, 6, 2), 27.0, 17.0, source="test"),
            TemperatureData(date(2024, 6, 3), 23.0, 13.0, source="test"),
        ]

        results = self.service.calculate_cumulative_gdd(temp_data, 10.0)

        assert len(results) == 3

        # Day 1: (25+15)/2 - 10 = 10 GDD
        assert results[0].daily_gdd == 10.0
        assert results[0].cumulative_gdd == 10.0

        # Day 2: (27+17)/2 - 10 = 12 GDD, cumulative = 22
        assert results[1].daily_gdd == 12.0
        assert results[1].cumulative_gdd == 22.0

        # Day 3: (23+13)/2 - 10 = 8 GDD, cumulative = 30
        assert results[2].daily_gdd == 8.0
        assert results[2].cumulative_gdd == 30.0

    def test_growth_stage_prediction_corn(self):
        """Test growth stage prediction for corn."""
        prediction = self.service.predict_growth_stages("corn", 350.0, date(2024, 5, 1))

        assert prediction.crop_name == "corn"
        assert prediction.current_stage == "V6"  # 350 GDD reaches V6 stage
        assert prediction.next_stage == "V12"
        assert prediction.gdd_to_next_stage == 250.0  # 600 - 350
        assert prediction.maturity_gdd == 1400.0

    def test_growth_stage_prediction_wheat(self):
        """Test growth stage prediction for wheat."""
        prediction = self.service.predict_growth_stages("wheat", 700.0, date(2024, 4, 1))

        assert prediction.crop_name == "wheat"
        assert prediction.current_stage == "Stem Extension"  # 700 GDD
        assert prediction.next_stage == "Heading"
        assert prediction.gdd_to_next_stage == 300.0  # 1000 - 700

    def test_temperature_data_validation(self):
        """Test temperature data validation."""
        # Valid data
        valid_data = TemperatureData(date.today(), 25.0, 15.0)
        is_valid, warnings, quality = self.service.validate_temperature_data(valid_data)

        assert is_valid is True
        assert len(warnings) == 0
        assert quality == DataQuality.GOOD

        # Invalid data (Tmax < Tmin)
        invalid_data = TemperatureData(date.today(), 10.0, 20.0)
        is_valid, warnings, quality = self.service.validate_temperature_data(invalid_data)

        assert is_valid is False
        assert len(warnings) > 0
        assert quality == DataQuality.UNRELIABLE

    def test_extreme_temperature_handling(self):
        """Test handling of extreme temperatures."""
        # Very hot day
        gdd, metadata = self.service.calculate_daily_gdd(45.0, 25.0, 10.0)
        assert gdd == 25.0  # (45+25)/2 - 10 = 35 - 10 = 25

        # Very cold day
        gdd, metadata = self.service.calculate_daily_gdd(-10.0, -20.0, 0.0)
        assert gdd == 0.0  # Below base temperature

    def test_modified_gdd_calculation_method(self):
        """Test modified GDD calculation method with temperature capping."""
        # Test with very high temperature that should be capped
        gdd_standard, _ = self.service.calculate_daily_gdd(40.0, 20.0, 10.0, method="standard")
        gdd_modified, _ = self.service.calculate_daily_gdd(40.0, 20.0, 10.0, method="modified")

        # Standard: (40+20)/2 - 10 = 20
        assert gdd_standard == 20.0

        # Modified: (30+20)/2 - 10 = 15 (max temp capped at 30°C)
        assert gdd_modified == 15.0


    def test_sine_wave_method(self):
        """Test sine wave calculation method."""
        # Currently same as standard method
        gdd, metadata = self.service.calculate_daily_gdd(25.0, 15.0, 10.0, method="sine_wave")
        assert gdd == 10.0
        assert metadata["method"] == "sine_wave"

    def test_unknown_method(self):
        """Test unknown calculation method raises error."""
        with pytest.raises(ValueError, match="Unknown calculation method"):
            self.service.calculate_daily_gdd(25.0, 15.0, 10.0, method="unknown_method")

    def test_extreme_temperature_logging(self, caplog):
        """Test that extreme temperatures log warnings."""
        with caplog.at_level(logging.WARNING):
            self.service.calculate_daily_gdd(65.0, 20.0, 10.0)
            assert "Extreme maximum temperature detected" in caplog.text

            caplog.clear()
            self.service.calculate_daily_gdd(20.0, -55.0, 10.0)
            assert "Extreme minimum temperature detected" in caplog.text

    def test_modified_method_edge_cases(self):
        """Test modified method edge cases around 30°C cap."""
        # Exactly 30°C: (30+20)/2 - 10 = 15
        gdd, _ = self.service.calculate_daily_gdd(30.0, 20.0, 10.0, method="modified")
        assert gdd == 15.0

        # Below 30°C: (29+20)/2 - 10 = 14.5
        gdd, _ = self.service.calculate_daily_gdd(29.0, 20.0, 10.0, method="modified")
        assert gdd == 14.5

        # Above 30°C: (31+20)/2 - 10 => (30+20)/2 - 10 = 15
        gdd, _ = self.service.calculate_daily_gdd(31.0, 20.0, 10.0, method="modified")
        assert gdd == 15.0

    def test_floating_point_precision(self):
        """Test rounding to 2 decimal places."""
        # Tmax=25.123, Tmin=15.123 => avg=20.123 => -10 = 10.123 => round(10.12)
        gdd, metadata = self.service.calculate_daily_gdd(25.123, 15.123, 10.0)
        assert gdd == 10.12
        assert metadata["average_temperature"] == 20.12
        assert metadata["temperature_range"] == 10.0

    def test_growth_stage_prediction_unknown_crop(self):
        """Test prediction for an unknown crop defaults to corn with lower confidence."""
        prediction = self.service.predict_growth_stages("unknown_crop", 100.0, date(2024, 5, 1))
        assert prediction.crop_name == "unknown_crop"
        # Defaults to corn stages. Corn emergence is 125. 100 < 125.
        assert prediction.next_stage == "Emergence"
        assert prediction.confidence == 0.5

    def test_growth_stage_prediction_exact_threshold(self):
        """Test prediction when GDD exactly matches a stage threshold."""
        # Corn Emergence is 125 GDD
        prediction = self.service.predict_growth_stages("corn", 125.0, date(2024, 5, 1))
        assert prediction.current_stage == "Emergence"
        assert prediction.next_stage == "V6"  # Next is V6 at 350

    def test_growth_stage_prediction_post_maturity(self):
        """Test prediction when GDD exceeds maturity."""
        # Corn Maturity is 1400 GDD
        prediction = self.service.predict_growth_stages("corn", 1500.0, date(2024, 5, 1))
        assert prediction.current_stage == "Maturity"
        assert prediction.next_stage is None
        assert prediction.days_to_next_stage is None
        assert prediction.predicted_maturity_date is None  # Already mature

    def test_growth_stage_prediction_pre_emergence(self):
        """Test prediction for very early growth (pre-emergence)."""
        # Corn Planting is 0, Emergence is 125
        prediction = self.service.predict_growth_stages("corn", 50.0, date(2024, 5, 1))
        # 50 >= 0 (Planting) but < 125 (Emergence)
        assert prediction.current_stage == "Planting"
        assert prediction.next_stage == "Emergence"
        assert prediction.gdd_to_next_stage == 75.0  # 125 - 50

    def test_growth_stage_prediction_confidence_reduction(self):
        """Test confidence reduction for long-term predictions."""
        # Use a winter date to get low daily GDD rate (3.0)
        # Corn maturity 1400. Current 100. Remaining 1300.
        # 1300 / 3.0 = 433 days > 60 days.
        current_date = date(2024, 1, 1)  # Winter
        prediction = self.service.predict_growth_stages(
            "corn", 100.0, date(2023, 12, 1), current_date=current_date
        )

        expected_confidence = 0.85 * 0.7
        assert prediction.maturity_confidence == pytest.approx(expected_confidence)

    def test_days_to_next_stage_calculation(self):
        """Test calculation of days to next stage."""
        # Summer date (rate 15.0)
        current_date = date(2024, 7, 1)
        # Corn: current 100. Next Emergence (125). Diff 25.
        # 25 / 15.0 = 1.66 -> int(1.66) = 1
        prediction = self.service.predict_growth_stages(
            "corn", 100.0, date(2024, 6, 1), current_date=current_date
        )

        assert prediction.days_to_next_stage == 1


# Property-based tests using hypothesis (if available)
try:
    from hypothesis import given, strategies as st

    class TestGDDProperties:
        """Property-based tests for GDD calculations."""

        def setup_method(self):
            self.service = GDDCalculatorService()

        @given(
            tmax=st.floats(min_value=-40, max_value=50),
            tmin=st.floats(min_value=-40, max_value=50),
            tbase=st.floats(min_value=-10, max_value=30),
        )
        def test_gdd_non_negative_property(self, tmax, tmin, tbase):
            """Property: GDD should always be non-negative."""
            # Skip invalid combinations
            if tmax < tmin:
                return

            gdd, _ = self.service.calculate_daily_gdd(tmax, tmin, tbase)
            assert gdd >= 0.0, f"GDD should be non-negative, got {gdd}"

        @given(
            tmax=st.floats(min_value=0, max_value=40),
            tmin=st.floats(min_value=-10, max_value=30),
            tbase=st.floats(min_value=0, max_value=20),
        )
        def test_gdd_formula_property(self, tmax, tmin, tbase):
            """Property: GDD should follow the standard formula."""
            # Skip invalid combinations
            if tmax < tmin:
                return

            gdd, metadata = self.service.calculate_daily_gdd(tmax, tmin, tbase)
            expected_gdd = max(0, (tmax + tmin) / 2 - tbase)

            assert abs(gdd - expected_gdd) < 0.01, (
                f"GDD calculation error: expected {expected_gdd}, got {gdd}"
            )

        @given(
            temp_data=st.lists(
                st.tuples(
                    st.floats(min_value=0, max_value=40),  # tmax
                    st.floats(min_value=-10, max_value=30),  # tmin
                ),
                min_size=1,
                max_size=10,
            ),
            tbase=st.floats(min_value=0, max_value=20),
        )
        def test_cumulative_gdd_monotonic_property(self, temp_data, tbase):
            """Property: Cumulative GDD should be monotonically increasing."""
            # Filter valid temperature pairs
            valid_data = [(tmax, tmin) for tmax, tmin in temp_data if tmax >= tmin]
            if not valid_data:
                return

            # Create TemperatureData objects
            temperature_objects = [
                TemperatureData(date(2024, 1, 1) + timedelta(days=i), tmax, tmin, source="test")
                for i, (tmax, tmin) in enumerate(valid_data)
            ]

            results = self.service.calculate_cumulative_gdd(temperature_objects, tbase)

            # Check monotonic increase
            for i in range(1, len(results)):
                assert results[i].cumulative_gdd >= results[i - 1].cumulative_gdd, (
                    "Cumulative GDD should be monotonically increasing"
                )

except ImportError:
    # Hypothesis not available, skip property-based tests
    pass


if __name__ == "__main__":
    pytest.main([__file__])

"""
Unit Tests for Carbon Monitoring Service

Tests carbon stock calculations and monitoring functions.

Scientific Basis:
    SOC Stock Formula:
        Stock (t/ha) = SOC (%) × BD (g/cm³) × Depth (cm) × 100
    
    Vegetation Carbon:
        Carbon (t/ha) = Dry Biomass (t/ha) × 0.45
    
    Sequestration Rate:
        Rate (t C/ha/year) = (C_final - C_initial) / Years
"""

import pytest
from app.services.carbon_monitoring_service import CarbonMonitoringService


class TestSOCStockCalculation:
    """Test soil organic carbon stock calculations"""
    
    def test_soc_stock_basic(self):
        """Test basic SOC stock calculation"""
        # Example from docstring:
        # SOC = 2.5%, BD = 1.3 g/cm³, Depth = 30 cm
        # Stock = 2.5 × 1.3 × 30 × 100 / 1000 = 9.75 t/ha
        result = CarbonMonitoringService.calculate_soc_stock(
            soc_percent=2.5,
            bulk_density=1.3,
            depth_cm=30
        )
        
        assert result == pytest.approx(9.75, rel=0.01)
    
    def test_soc_stock_high_carbon(self):
        """Test SOC calculation with high carbon content"""
        # High organic matter soil
        # SOC = 5.0%, BD = 1.2 g/cm³, Depth = 30 cm
        result = CarbonMonitoringService.calculate_soc_stock(
            soc_percent=5.0,
            bulk_density=1.2,
            depth_cm=30
        )
        
        # 5.0 × 1.2 × 30 × 100 / 1000 = 18.0 t/ha
        assert result == pytest.approx(18.0, rel=0.01)
    
    def test_soc_stock_deep_sampling(self):
        """Test SOC calculation with deep sampling"""
        # Deep sampling to 100 cm
        # SOC = 2.0%, BD = 1.4 g/cm³, Depth = 100 cm
        result = CarbonMonitoringService.calculate_soc_stock(
            soc_percent=2.0,
            bulk_density=1.4,
            depth_cm=100
        )
        
        # 2.0 × 1.4 × 100 × 100 / 1000 = 28.0 t/ha
        assert result == pytest.approx(28.0, rel=0.01)
    
    def test_soc_stock_low_carbon(self):
        """Test SOC calculation with low carbon content"""
        # Degraded soil
        # SOC = 0.5%, BD = 1.5 g/cm³, Depth = 30 cm
        result = CarbonMonitoringService.calculate_soc_stock(
            soc_percent=0.5,
            bulk_density=1.5,
            depth_cm=30
        )
        
        # 0.5 × 1.5 × 30 × 100 / 1000 = 2.25 t/ha
        assert result == pytest.approx(2.25, rel=0.01)
    
    def test_soc_stock_zero_carbon(self):
        """Test SOC calculation with zero carbon"""
        result = CarbonMonitoringService.calculate_soc_stock(
            soc_percent=0.0,
            bulk_density=1.3,
            depth_cm=30
        )
        
        assert result == 0.0
    
    def test_soc_stock_invalid_soc_negative(self):
        """Test that negative SOC raises ValueError"""
        with pytest.raises(ValueError, match="SOC percent must be between 0 and 100"):
            CarbonMonitoringService.calculate_soc_stock(
                soc_percent=-1.0,
                bulk_density=1.3,
                depth_cm=30
            )
    
    def test_soc_stock_invalid_soc_too_high(self):
        """Test that SOC > 100% raises ValueError"""
        with pytest.raises(ValueError, match="SOC percent must be between 0 and 100"):
            CarbonMonitoringService.calculate_soc_stock(
                soc_percent=101.0,
                bulk_density=1.3,
                depth_cm=30
            )
    
    def test_soc_stock_invalid_bulk_density_negative(self):
        """Test that negative bulk density raises ValueError"""
        with pytest.raises(ValueError, match="Bulk density must be between 0 and 2.0"):
            CarbonMonitoringService.calculate_soc_stock(
                soc_percent=2.5,
                bulk_density=-0.5,
                depth_cm=30
            )
    
    def test_soc_stock_invalid_bulk_density_too_high(self):
        """Test that unrealistic bulk density raises ValueError"""
        with pytest.raises(ValueError, match="Bulk density must be between 0 and 2.0"):
            CarbonMonitoringService.calculate_soc_stock(
                soc_percent=2.5,
                bulk_density=2.5,
                depth_cm=30
            )
    
    def test_soc_stock_invalid_depth_negative(self):
        """Test that negative depth raises ValueError"""
        with pytest.raises(ValueError, match="Depth must be positive"):
            CarbonMonitoringService.calculate_soc_stock(
                soc_percent=2.5,
                bulk_density=1.3,
                depth_cm=-10
            )
    
    def test_soc_stock_invalid_depth_zero(self):
        """Test that zero depth raises ValueError"""
        with pytest.raises(ValueError, match="Depth must be positive"):
            CarbonMonitoringService.calculate_soc_stock(
                soc_percent=2.5,
                bulk_density=1.3,
                depth_cm=0
            )


class TestVegetationCarbonCalculation:
    """Test vegetation carbon calculations"""
    
    def test_vegetation_carbon_basic(self):
        """Test basic vegetation carbon calculation"""
        # Example from docstring:
        # Biomass = 10.0 t/ha
        # Carbon = 10.0 × 0.45 = 4.5 t/ha
        result = CarbonMonitoringService.calculate_vegetation_carbon(
            dry_biomass_t_ha=10.0
        )
        
        assert result == pytest.approx(4.5, rel=0.01)
    
    def test_vegetation_carbon_high_biomass(self):
        """Test vegetation carbon with high biomass"""
        # Forest or high-yielding crop
        # Biomass = 50.0 t/ha
        result = CarbonMonitoringService.calculate_vegetation_carbon(
            dry_biomass_t_ha=50.0
        )
        
        # 50.0 × 0.45 = 22.5 t/ha
        assert result == pytest.approx(22.5, rel=0.01)
    
    def test_vegetation_carbon_low_biomass(self):
        """Test vegetation carbon with low biomass"""
        # Sparse vegetation
        # Biomass = 2.0 t/ha
        result = CarbonMonitoringService.calculate_vegetation_carbon(
            dry_biomass_t_ha=2.0
        )
        
        # 2.0 × 0.45 = 0.9 t/ha
        assert result == pytest.approx(0.9, rel=0.01)
    
    def test_vegetation_carbon_zero_biomass(self):
        """Test vegetation carbon with zero biomass"""
        result = CarbonMonitoringService.calculate_vegetation_carbon(
            dry_biomass_t_ha=0.0
        )
        
        assert result == 0.0
    
    def test_vegetation_carbon_decimal_biomass(self):
        """Test vegetation carbon with decimal biomass"""
        # Biomass = 7.5 t/ha
        result = CarbonMonitoringService.calculate_vegetation_carbon(
            dry_biomass_t_ha=7.5
        )
        
        # 7.5 × 0.45 = 3.375 → 3.38 t/ha (rounded)
        assert result == pytest.approx(3.38, rel=0.01)
    
    def test_vegetation_carbon_invalid_negative(self):
        """Test that negative biomass raises ValueError"""
        with pytest.raises(ValueError, match="Biomass cannot be negative"):
            CarbonMonitoringService.calculate_vegetation_carbon(
                dry_biomass_t_ha=-5.0
            )


class TestCarbonCalculationEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_soc_very_large_values(self):
        """Test SOC calculation with very large values"""
        # Deep peat soil
        # SOC = 50%, BD = 0.5 g/cm³, Depth = 200 cm
        result = CarbonMonitoringService.calculate_soc_stock(
            soc_percent=50.0,
            bulk_density=0.5,
            depth_cm=200
        )
        
        # 50 × 0.5 × 200 × 100 / 1000 = 500 t/ha
        assert result == pytest.approx(500.0, rel=0.01)
    
    def test_vegetation_very_large_biomass(self):
        """Test vegetation carbon with very large biomass"""
        # Old-growth forest
        result = CarbonMonitoringService.calculate_vegetation_carbon(
            dry_biomass_t_ha=200.0
        )
        
        # 200 × 0.45 = 90 t/ha
        assert result == pytest.approx(90.0, rel=0.01)
    
    def test_soc_typical_agricultural_range(self):
        """Test SOC for typical agricultural soils"""
        # Typical agricultural soil: 1-3% SOC
        results = []
        for soc in [1.0, 2.0, 3.0]:
            result = CarbonMonitoringService.calculate_soc_stock(
                soc_percent=soc,
                bulk_density=1.3,
                depth_cm=30
            )
            results.append(result)
        
        # Expected: 3.9, 7.8, 11.7 t/ha
        assert results[0] == pytest.approx(3.9, rel=0.01)
        assert results[1] == pytest.approx(7.8, rel=0.01)
        assert results[2] == pytest.approx(11.7, rel=0.01)


class TestScientificAccuracy:
    """Test scientific accuracy against known values"""
    
    def test_carbon_fraction_constant(self):
        """Verify carbon fraction of 0.45 (45%)"""
        # Standard assumption: 45% of dry biomass is carbon
        result = CarbonMonitoringService.calculate_vegetation_carbon(
            dry_biomass_t_ha=1.0
        )
        
        assert result == pytest.approx(0.45, rel=0.01)
    
    def test_soc_formula_components(self):
        """Verify SOC formula components"""
        # Test that formula correctly multiplies all components
        # Stock = SOC × BD × Depth × 100 / 1000
        soc = 2.0
        bd = 1.5
        depth = 40
        
        result = CarbonMonitoringService.calculate_soc_stock(
            soc_percent=soc,
            bulk_density=bd,
            depth_cm=depth
        )
        
        expected = soc * bd * depth * 100 / 1000
        assert result == pytest.approx(expected, rel=0.01)
    
    def test_typical_bulk_density_range(self):
        """Test with typical bulk density range (1.0-1.6 g/cm³)"""
        # Agricultural soils typically have BD between 1.0-1.6
        results = []
        for bd in [1.0, 1.3, 1.6]:
            result = CarbonMonitoringService.calculate_soc_stock(
                soc_percent=2.0,
                bulk_density=bd,
                depth_cm=30
            )
            results.append(result)
        
        # Expected: 6.0, 7.8, 9.6 t/ha
        assert results[0] == pytest.approx(6.0, rel=0.01)
        assert results[1] == pytest.approx(7.8, rel=0.01)
        assert results[2] == pytest.approx(9.6, rel=0.01)
    
    def test_standard_sampling_depths(self):
        """Test with standard sampling depths (30 cm and 100 cm)"""
        # Standard depths for SOC measurement
        result_30 = CarbonMonitoringService.calculate_soc_stock(
            soc_percent=2.0,
            bulk_density=1.3,
            depth_cm=30
        )
        
        result_100 = CarbonMonitoringService.calculate_soc_stock(
            soc_percent=2.0,
            bulk_density=1.3,
            depth_cm=100
        )
        
        # 100 cm should be ~3.33× the 30 cm value
        assert result_100 / result_30 == pytest.approx(3.33, rel=0.01)
    
    def test_typical_crop_biomass_range(self):
        """Test with typical crop biomass range"""
        # Typical crop biomass: 5-15 t/ha
        results = []
        for biomass in [5.0, 10.0, 15.0]:
            result = CarbonMonitoringService.calculate_vegetation_carbon(
                dry_biomass_t_ha=biomass
            )
            results.append(result)
        
        # Expected: 2.25, 4.5, 6.75 t C/ha
        assert results[0] == pytest.approx(2.25, rel=0.01)
        assert results[1] == pytest.approx(4.5, rel=0.01)
        assert results[2] == pytest.approx(6.75, rel=0.01)


class TestResultPrecision:
    """Test result rounding and precision"""
    
    def test_soc_result_rounded_to_two_decimals(self):
        """Test that SOC results are rounded to 2 decimal places"""
        result = CarbonMonitoringService.calculate_soc_stock(
            soc_percent=2.333,
            bulk_density=1.333,
            depth_cm=30
        )
        
        # Result should be rounded to 2 decimals
        assert isinstance(result, float)
        # Check it has at most 2 decimal places
        assert result == round(result, 2)
    
    def test_vegetation_result_rounded_to_two_decimals(self):
        """Test that vegetation carbon results are rounded to 2 decimal places"""
        result = CarbonMonitoringService.calculate_vegetation_carbon(
            dry_biomass_t_ha=7.777
        )
        
        # Result should be rounded to 2 decimals
        assert isinstance(result, float)
        assert result == round(result, 2)

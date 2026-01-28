"""
Unit Tests for Emissions Calculator Service

Tests IPCC-based emission calculations for agricultural activities.

Scientific Basis:
    - IPCC 2006 Guidelines for National Greenhouse Gas Inventories
    - N2O GWP = 298 (IPCC AR5)
    - Standard emission factors for fertilizers, fuels, irrigation
"""

import pytest
from datetime import date
from app.services.emissions_calculator_service import EmissionsCalculatorService


class TestFertilizerEmissions:
    """Test fertilizer emission calculations"""
    
    def test_nitrogen_emissions_basic(self):
        """Test basic nitrogen fertilizer emission calculation"""
        # 100 kg N × 4.0 (production) + 100 × 0.015 × 298 (N2O) = 400 + 447 = 847 kg CO2e
        result = EmissionsCalculatorService.calculate_fertilizer_emissions(
            n_kg=100,
            fertilizer_type="generic"
        )
        
        assert result["n_emissions"] == pytest.approx(400.0, rel=0.01)
        assert result["n2o_emissions"] == pytest.approx(447.0, rel=0.01)
        assert result["total_emissions"] == pytest.approx(847.0, rel=0.01)
    
    def test_phosphorus_emissions(self):
        """Test phosphorus fertilizer emissions"""
        # 50 kg P2O5 × 1.0 = 50 kg CO2e
        result = EmissionsCalculatorService.calculate_fertilizer_emissions(
            p_kg=50,
            fertilizer_type="generic"
        )
        
        assert result["p_emissions"] == pytest.approx(50.0, rel=0.01)
        assert result["total_emissions"] == pytest.approx(50.0, rel=0.01)
    
    def test_potassium_emissions(self):
        """Test potassium fertilizer emissions"""
        # 30 kg K2O × 0.5 = 15 kg CO2e
        result = EmissionsCalculatorService.calculate_fertilizer_emissions(
            k_kg=30,
            fertilizer_type="generic"
        )
        
        assert result["k_emissions"] == pytest.approx(15.0, rel=0.01)
        assert result["total_emissions"] == pytest.approx(15.0, rel=0.01)
    
    def test_combined_npk_emissions(self):
        """Test combined NPK fertilizer emissions"""
        result = EmissionsCalculatorService.calculate_fertilizer_emissions(
            n_kg=100,
            p_kg=50,
            k_kg=30,
            fertilizer_type="generic"
        )
        
        # N: 400 + 447 (N2O) = 847
        # P: 50
        # K: 15
        # Total: 912
        assert result["total_emissions"] == pytest.approx(912.0, rel=0.01)
    
    def test_zero_quantity(self):
        """Test zero quantity returns zero emissions"""
        result = EmissionsCalculatorService.calculate_fertilizer_emissions(
            n_kg=0,
            p_kg=0,
            k_kg=0
        )
        
        assert result["total_emissions"] == 0


class TestFuelEmissions:
    """Test fuel combustion emission calculations"""
    
    def test_diesel_emissions_basic(self):
        """Test basic diesel emission calculation"""
        # Diesel: 2.7 kg CO2e per liter
        result = EmissionsCalculatorService.calculate_fuel_emissions(
            diesel_liters=100
        )
        
        # 100 L × 2.7 = 270 kg CO2e
        assert result["diesel_emissions"] == pytest.approx(270.0, rel=0.01)
        assert result["total_emissions"] == pytest.approx(270.0, rel=0.01)
    
    def test_petrol_emissions(self):
        """Test petrol emission calculation"""
        # Petrol: 2.3 kg CO2e per liter
        result = EmissionsCalculatorService.calculate_fuel_emissions(
            petrol_liters=50
        )
        
        # 50 L × 2.3 = 115 kg CO2e
        assert result["petrol_emissions"] == pytest.approx(115.0, rel=0.01)
        assert result["total_emissions"] == pytest.approx(115.0, rel=0.01)
    
    def test_combined_fuel_emissions(self):
        """Test combined diesel and petrol emissions"""
        result = EmissionsCalculatorService.calculate_fuel_emissions(
            diesel_liters=100,
            petrol_liters=50
        )
        
        # Diesel: 270, Petrol: 115, Total: 385
        assert result["total_emissions"] == pytest.approx(385.0, rel=0.01)
    
    def test_zero_fuel_quantity(self):
        """Test zero fuel quantity returns zero emissions"""
        result = EmissionsCalculatorService.calculate_fuel_emissions(
            diesel_liters=0,
            petrol_liters=0
        )
        
        assert result["total_emissions"] == 0


class TestIrrigationEmissions:
    """Test irrigation pumping emission calculations"""
    
    def test_grid_electricity_emissions_basic(self):
        """Test grid electricity emission calculation"""
        # Grid electricity: 0.8 kg CO2e per kWh
        result = EmissionsCalculatorService.calculate_irrigation_emissions(
            kwh=1000,
            energy_source="grid"
        )
        
        # 1000 kWh × 0.8 = 800 kg CO2e
        assert result["emissions"] == pytest.approx(800.0, rel=0.01)
        assert result["energy_source"] == "grid"
        assert result["emission_factor"] == 0.8
    
    def test_coal_electricity_emissions(self):
        """Test coal-heavy grid emission calculation"""
        # Coal grid: 1.2 kg CO2e per kWh
        result = EmissionsCalculatorService.calculate_irrigation_emissions(
            kwh=500,
            energy_source="coal"
        )
        
        # 500 kWh × 1.2 = 600 kg CO2e
        assert result["emissions"] == pytest.approx(600.0, rel=0.01)
        assert result["energy_source"] == "coal"
    
    def test_renewable_electricity_emissions(self):
        """Test renewable energy emission calculation"""
        # Renewable: 0.1 kg CO2e per kWh
        result = EmissionsCalculatorService.calculate_irrigation_emissions(
            kwh=1000,
            energy_source="renewable"
        )
        
        # 1000 kWh × 0.1 = 100 kg CO2e
        assert result["emissions"] == pytest.approx(100.0, rel=0.01)
        assert result["energy_source"] == "renewable"
    
    def test_zero_irrigation_quantity(self):
        """Test zero irrigation quantity returns zero emissions"""
        result = EmissionsCalculatorService.calculate_irrigation_emissions(
            kwh=0,
            energy_source="grid"
        )
        
        assert result["emissions"] == 0


class TestEmissionCalculationEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_very_large_quantity(self):
        """Test calculation with very large quantity"""
        result = EmissionsCalculatorService.calculate_fertilizer_emissions(
            n_kg=1000000  # 1 million kg
        )
        
        # Should handle large numbers correctly
        # 1M × 4.0 + 1M × 0.015 × 298 = 4M + 4.47M = 8.47M
        assert result["total_emissions"] > 0
        assert result["total_emissions"] == pytest.approx(8470000, rel=0.01)
    
    def test_very_small_quantity(self):
        """Test calculation with very small quantity"""
        result = EmissionsCalculatorService.calculate_fuel_emissions(
            diesel_liters=0.01  # 10 ml
        )
        
        # Should handle small numbers correctly
        # 0.01 L × 2.7 = 0.027 kg CO2e
        assert result["diesel_emissions"] == pytest.approx(0.03, rel=0.1)
    
    def test_decimal_quantity(self):
        """Test calculation with decimal quantity"""
        result = EmissionsCalculatorService.calculate_fertilizer_emissions(
            n_kg=45.5
        )
        
        # 45.5 × 4.0 + 45.5 × 0.015 × 298 = 182 + 203.49 = 385.49
        assert result["total_emissions"] == pytest.approx(385.49, rel=0.01)


class TestEmissionResultStructure:
    """Test emission calculation result structure"""
    
    def test_fertilizer_result_contains_all_fields(self):
        """Test fertilizer result contains all required fields"""
        result = EmissionsCalculatorService.calculate_fertilizer_emissions(
            n_kg=100,
            p_kg=50,
            k_kg=30
        )
        
        assert "n_emissions" in result
        assert "p_emissions" in result
        assert "k_emissions" in result
        assert "n2o_emissions" in result
        assert "total_emissions" in result
    
    def test_fuel_result_contains_all_fields(self):
        """Test fuel result contains all required fields"""
        result = EmissionsCalculatorService.calculate_fuel_emissions(
            diesel_liters=50,
            petrol_liters=25
        )
        
        assert "diesel_emissions" in result
        assert "petrol_emissions" in result
        assert "total_emissions" in result
    
    def test_irrigation_result_contains_all_fields(self):
        """Test irrigation result contains all required fields"""
        result = EmissionsCalculatorService.calculate_irrigation_emissions(
            kwh=1000,
            energy_source="grid"
        )
        
        assert "emissions" in result
        assert "energy_source" in result
        assert "emission_factor" in result


# Scientific validation tests
class TestScientificAccuracy:
    """Test scientific accuracy against known values"""
    
    def test_ipcc_nitrogen_factor(self):
        """Verify IPCC emission factor for nitrogen"""
        # Generic N: 4.0 kg CO2e per kg N (production)
        result = EmissionsCalculatorService.calculate_fertilizer_emissions(
            n_kg=1
        )
        
        assert result["n_emissions"] == pytest.approx(4.0, rel=0.01)
    
    def test_ipcc_n2o_gwp(self):
        """Verify N2O global warming potential"""
        # N2O GWP = 298
        # 1 kg N × 0.015 (emission factor) × 298 (GWP) = 4.47 kg CO2e
        result = EmissionsCalculatorService.calculate_fertilizer_emissions(
            n_kg=1
        )
        
        assert result["n2o_emissions"] == pytest.approx(4.47, rel=0.01)
    
    def test_ipcc_diesel_factor(self):
        """Verify IPCC emission factor for diesel"""
        # Diesel = 2.7 kg CO2e per liter
        result = EmissionsCalculatorService.calculate_fuel_emissions(
            diesel_liters=1
        )
        
        assert result["diesel_emissions"] == pytest.approx(2.7, rel=0.01)
    
    def test_grid_electricity_factor(self):
        """Verify grid electricity emission factor"""
        # Grid electricity = 0.8 kg CO2e per kWh
        result = EmissionsCalculatorService.calculate_irrigation_emissions(
            kwh=1,
            energy_source="grid"
        )
        
        assert result["emission_factor"] == pytest.approx(0.8, rel=0.01)

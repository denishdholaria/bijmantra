"""
Emissions Calculator Service

Calculates agricultural emissions for carbon footprint analysis.

Scientific Basis:
    Fertilizer Emissions:
        - Urea: 4.5 kg CO2e/kg N (production + N2O)
        - Ammonium Nitrate: 3.8 kg CO2e/kg N
        - DAP: 1.2 kg CO2e/kg P2O5
        - N2O from soil: 1-3% of applied N converts to N2O
        - N2O has GWP = 298 (298× more potent than CO2)
    
    Fuel Combustion:
        - Diesel: 2.7 kg CO2e/L
        - Petrol: 2.3 kg CO2e/L
        - Includes combustion + upstream emissions
    
    Irrigation:
        - Electricity: 0.5-1.5 kg CO2e/kWh (grid average)
        - Varies by energy mix (coal vs. renewable)
    
    Carbon Intensity:
        CI (kg CO2e/kg yield) = Total Emissions / Total Yield
        
        Typical ranges:
        - Rice: 2-4 kg CO2e/kg grain
        - Wheat: 0.4-0.8 kg CO2e/kg grain
        - Maize: 0.3-0.6 kg CO2e/kg grain
        - Soybean: 0.2-0.5 kg CO2e/kg grain
"""

import logging
from typing import Optional, List, Dict
from datetime import date
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.climate import (
    EmissionSource,
    EmissionFactor,
    VarietyFootprint,
    EmissionCategory
)
from app.models.phenotyping import Observation, ObservationVariable

logger = logging.getLogger(__name__)


# Standard IPCC-based emission factors
DEFAULT_EMISSION_FACTORS = {
    EmissionCategory.FERTILIZER: {
        "urea": {"value": 4.5, "unit": "kg CO2e/kg N"},
        "ammonium_nitrate": {"value": 3.8, "unit": "kg CO2e/kg N"},
        "dap": {"value": 1.2, "unit": "kg CO2e/kg P2O5"},
        "mop": {"value": 0.6, "unit": "kg CO2e/kg K2O"},
        "generic_n": {"value": 4.0, "unit": "kg CO2e/kg N"},
        "generic_p": {"value": 1.0, "unit": "kg CO2e/kg P2O5"},
        "generic_k": {"value": 0.5, "unit": "kg CO2e/kg K2O"},
    },
    EmissionCategory.FUEL: {
        "diesel": {"value": 2.7, "unit": "kg CO2e/L"},
        "petrol": {"value": 2.3, "unit": "kg CO2e/L"},
        "lpg": {"value": 1.7, "unit": "kg CO2e/kg"},
    },
    EmissionCategory.IRRIGATION: {
        "electricity_grid": {"value": 0.8, "unit": "kg CO2e/kWh"},
        "electricity_coal": {"value": 1.2, "unit": "kg CO2e/kWh"},
        "electricity_renewable": {"value": 0.1, "unit": "kg CO2e/kWh"},
    },
    EmissionCategory.PESTICIDE: {
        "herbicide": {"value": 6.3, "unit": "kg CO2e/kg"},
        "insecticide": {"value": 5.1, "unit": "kg CO2e/kg"},
        "fungicide": {"value": 3.9, "unit": "kg CO2e/kg"},
    },
}


class EmissionsCalculatorService:
    """
    Service for calculating agricultural emissions.
    
    Handles:
    - Emission calculations from inputs
    - Emission factor management
    - Variety carbon footprint calculation
    - Emissions aggregation and reporting
    """
    
    @staticmethod
    def calculate_fertilizer_emissions(
        n_kg: float = 0,
        p_kg: float = 0,
        k_kg: float = 0,
        fertilizer_type: str = "generic"
    ) -> Dict[str, float]:
        """
        Calculate emissions from fertilizer application.
        
        Emissions include:
        1. Production emissions (manufacturing)
        2. N2O emissions from soil (1.5% of applied N)
        
        N2O Calculation:
            N2O (kg) = N applied (kg) × 0.015 (1.5% emission factor)
            CO2e = N2O × 298 (GWP of N2O)
        
        Args:
            n_kg: Nitrogen applied (kg)
            p_kg: Phosphorus applied (kg P2O5)
            k_kg: Potassium applied (kg K2O)
            fertilizer_type: Type of fertilizer
        
        Returns:
            dict: {
                'n_emissions': float,
                'p_emissions': float,
                'k_emissions': float,
                'n2o_emissions': float,
                'total_emissions': float
            }
        
        Example:
            >>> calculate_fertilizer_emissions(100, 50, 30)
            {
                'n_emissions': 400.0,  # 100 kg N × 4.0
                'p_emissions': 50.0,   # 50 kg P × 1.0
                'k_emissions': 15.0,   # 30 kg K × 0.5
                'n2o_emissions': 447.0, # 100 × 0.015 × 298
                'total_emissions': 912.0
            }
        """
        factors = DEFAULT_EMISSION_FACTORS[EmissionCategory.FERTILIZER]
        
        # Production emissions
        n_factor = factors.get(f"{fertilizer_type}_n", factors["generic_n"])["value"]
        p_factor = factors.get(f"{fertilizer_type}_p", factors["generic_p"])["value"]
        k_factor = factors.get(f"{fertilizer_type}_k", factors["generic_k"])["value"]
        
        n_emissions = n_kg * n_factor
        p_emissions = p_kg * p_factor
        k_emissions = k_kg * k_factor
        
        # N2O emissions from soil
        # 1.5% of applied N converts to N2O
        # N2O has GWP = 298
        n2o_kg = n_kg * 0.015
        n2o_emissions = n2o_kg * 298
        
        total = n_emissions + p_emissions + k_emissions + n2o_emissions
        
        return {
            'n_emissions': round(n_emissions, 2),
            'p_emissions': round(p_emissions, 2),
            'k_emissions': round(k_emissions, 2),
            'n2o_emissions': round(n2o_emissions, 2),
            'total_emissions': round(total, 2)
        }
    
    @staticmethod
    def calculate_fuel_emissions(
        diesel_liters: float = 0,
        petrol_liters: float = 0
    ) -> Dict[str, float]:
        """
        Calculate emissions from fuel combustion.
        
        Emission Factors:
            - Diesel: 2.7 kg CO2e/L
            - Petrol: 2.3 kg CO2e/L
        
        Includes combustion + upstream (extraction, refining, transport).
        
        Args:
            diesel_liters: Diesel consumed (liters)
            petrol_liters: Petrol consumed (liters)
        
        Returns:
            dict: {
                'diesel_emissions': float,
                'petrol_emissions': float,
                'total_emissions': float
            }
        
        Example:
            >>> calculate_fuel_emissions(100, 50)
            {
                'diesel_emissions': 270.0,  # 100 L × 2.7
                'petrol_emissions': 115.0,  # 50 L × 2.3
                'total_emissions': 385.0
            }
        """
        factors = DEFAULT_EMISSION_FACTORS[EmissionCategory.FUEL]
        
        diesel_emissions = diesel_liters * factors["diesel"]["value"]
        petrol_emissions = petrol_liters * factors["petrol"]["value"]
        
        total = diesel_emissions + petrol_emissions
        
        return {
            'diesel_emissions': round(diesel_emissions, 2),
            'petrol_emissions': round(petrol_emissions, 2),
            'total_emissions': round(total, 2)
        }
    
    @staticmethod
    def calculate_irrigation_emissions(
        kwh: float,
        energy_source: str = "grid"
    ) -> Dict[str, float]:
        """
        Calculate emissions from irrigation pumping.
        
        Emission Factors:
            - Grid average: 0.8 kg CO2e/kWh
            - Coal-heavy grid: 1.2 kg CO2e/kWh
            - Renewable: 0.1 kg CO2e/kWh
        
        Args:
            kwh: Electricity consumed (kWh)
            energy_source: Energy source (grid, coal, renewable)
        
        Returns:
            dict: {
                'emissions': float,
                'energy_source': str,
                'emission_factor': float
            }
        
        Example:
            >>> calculate_irrigation_emissions(1000, "grid")
            {
                'emissions': 800.0,  # 1000 kWh × 0.8
                'energy_source': 'grid',
                'emission_factor': 0.8
            }
        """
        factors = DEFAULT_EMISSION_FACTORS[EmissionCategory.IRRIGATION]
        
        source_key = f"electricity_{energy_source}"
        if source_key not in factors:
            source_key = "electricity_grid"
        
        factor = factors[source_key]["value"]
        emissions = kwh * factor
        
        return {
            'emissions': round(emissions, 2),
            'energy_source': energy_source,
            'emission_factor': factor
        }
    
    async def create_emission_source(
        self,
        db: AsyncSession,
        organization_id: int,
        location_id: int,
        activity_date: date,
        category: EmissionCategory,
        source_name: str,
        quantity: float,
        unit: str,
        trial_id: Optional[int] = None,
        study_id: Optional[int] = None,
        emission_factor_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> EmissionSource:
        """
        Create emission source record.
        
        Automatically calculates CO2e emissions based on category and quantity.
        
        Args:
            db: Database session
            organization_id: Organization ID
            location_id: Location ID
            activity_date: Date of activity
            category: Emission category
            source_name: Source name
            quantity: Quantity of input
            unit: Unit of quantity
            trial_id: Trial ID (optional)
            study_id: Study ID (optional)
            emission_factor_id: Custom emission factor (optional)
            notes: Additional notes
        
        Returns:
            EmissionSource: Created emission source
        """
        # Calculate emissions based on category
        co2e_emissions = 0.0
        
        if category == EmissionCategory.FERTILIZER:
            # Parse fertilizer type and nutrient
            if "n" in source_name.lower() or "nitrogen" in source_name.lower():
                result = self.calculate_fertilizer_emissions(n_kg=quantity)
                co2e_emissions = result['total_emissions']
            elif "p" in source_name.lower() or "phosphorus" in source_name.lower():
                result = self.calculate_fertilizer_emissions(p_kg=quantity)
                co2e_emissions = result['total_emissions']
            elif "k" in source_name.lower() or "potassium" in source_name.lower():
                result = self.calculate_fertilizer_emissions(k_kg=quantity)
                co2e_emissions = result['total_emissions']
        
        elif category == EmissionCategory.FUEL:
            if "diesel" in source_name.lower():
                result = self.calculate_fuel_emissions(diesel_liters=quantity)
                co2e_emissions = result['diesel_emissions']
            elif "petrol" in source_name.lower():
                result = self.calculate_fuel_emissions(petrol_liters=quantity)
                co2e_emissions = result['petrol_emissions']
        
        elif category == EmissionCategory.IRRIGATION:
            result = self.calculate_irrigation_emissions(quantity)
            co2e_emissions = result['emissions']
        
        # Create emission source
        emission_source = EmissionSource(
            organization_id=organization_id,
            location_id=location_id,
            trial_id=trial_id,
            study_id=study_id,
            activity_date=activity_date,
            category=category,
            source_name=source_name,
            quantity=quantity,
            unit=unit,
            emission_factor_id=emission_factor_id,
            co2e_emissions=co2e_emissions,
            notes=notes
        )
        
        db.add(emission_source)
        await db.commit()
        await db.refresh(emission_source)
        
        logger.info(
            f"Created emission source {emission_source.id}: "
            f"{source_name} = {co2e_emissions} kg CO2e"
        )
        
        return emission_source
    
    async def get_emission_sources(
        self,
        db: AsyncSession,
        organization_id: int,
        location_id: Optional[int] = None,
        trial_id: Optional[int] = None,
        study_id: Optional[int] = None,
        category: Optional[EmissionCategory] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[EmissionSource]:
        """
        Get emission sources with filters.
        
        Args:
            db: Database session
            organization_id: Organization ID
            location_id: Filter by location (optional)
            trial_id: Filter by trial (optional)
            study_id: Filter by study (optional)
            category: Filter by category (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            limit: Maximum results
            offset: Results offset
        
        Returns:
            list: List of EmissionSource records
        """
        query = select(EmissionSource).where(
            EmissionSource.organization_id == organization_id
        )
        
        if location_id:
            query = query.where(EmissionSource.location_id == location_id)
        
        if trial_id:
            query = query.where(EmissionSource.trial_id == trial_id)
        
        if study_id:
            query = query.where(EmissionSource.study_id == study_id)
        
        if category:
            query = query.where(EmissionSource.category == category)
        
        if start_date:
            query = query.where(EmissionSource.activity_date >= start_date)
        
        if end_date:
            query = query.where(EmissionSource.activity_date <= end_date)
        
        query = query.order_by(EmissionSource.activity_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def calculate_variety_footprint(
        self,
        db: AsyncSession,
        organization_id: int,
        germplasm_id: int,
        trial_id: int,
        study_id: int,
        location_id: int,
        season_id: Optional[int] = None,
        measurement_date: Optional[date] = None
    ) -> Optional[VarietyFootprint]:
        """
        Calculate carbon footprint for a variety.
        
        Aggregates all emissions for a variety in a trial/study and
        calculates carbon intensity (kg CO2e/kg yield).
        
        Carbon Intensity:
            CI = Total Emissions (kg CO2e/ha) / Total Yield (kg/ha)
        
        Args:
            db: Database session
            organization_id: Organization ID
            germplasm_id: Variety ID
            trial_id: Trial ID
            study_id: Study ID
            location_id: Location ID
            season_id: Season ID (optional)
            measurement_date: Date of calculation (optional)
        
        Returns:
            VarietyFootprint: Calculated footprint
            None if insufficient data
        """
        # Get all emission sources for this trial/study
        emissions = await self.get_emission_sources(
            db, organization_id,
            trial_id=trial_id,
            study_id=study_id
        )
        
        if not emissions:
            logger.warning(f"No emissions found for trial {trial_id}, study {study_id}")
            return None
        
        # Aggregate emissions by category
        emissions_by_category = {}
        total_emissions = 0.0
        
        for emission in emissions:
            category = emission.category.value
            if category not in emissions_by_category:
                emissions_by_category[category] = 0.0
            emissions_by_category[category] += emission.co2e_emissions
            total_emissions += emission.co2e_emissions
        
        # Get yield data from observations
        stmt = (
            select(Observation.value)
            .join(ObservationVariable)
            .where(
                and_(
                    Observation.study_id == study_id,
                    Observation.germplasm_id == germplasm_id,
                    ObservationVariable.observation_variable_name.ilike("%yield%")
                )
            )
        )

        result = await db.execute(stmt)
        values = result.scalars().all()

        # Calculate average yield
        valid_yields = []
        for val in values:
            try:
                # Handle potential string format issues or non-numeric values
                if val:
                    valid_yields.append(float(val))
            except (ValueError, TypeError):
                continue

        if valid_yields:
            total_yield = sum(valid_yields) / len(valid_yields)
        else:
            total_yield = 0.0
            logger.warning(
                f"No yield data found for germplasm {germplasm_id} in study {study_id}. "
                "Using total_yield=0.0"
            )
        
        # Calculate carbon intensity
        carbon_intensity = total_emissions / total_yield if total_yield > 0 else 0
        
        # Create variety footprint
        footprint = VarietyFootprint(
            organization_id=organization_id,
            germplasm_id=germplasm_id,
            trial_id=trial_id,
            study_id=study_id,
            season_id=season_id,
            location_id=location_id,
            total_emissions=total_emissions,
            total_yield=total_yield,
            carbon_intensity=carbon_intensity,
            emissions_by_category=emissions_by_category,
            measurement_date=measurement_date or date.today(),
            notes="Auto-calculated from emission sources"
        )
        
        db.add(footprint)
        await db.commit()
        await db.refresh(footprint)
        
        logger.info(
            f"Created variety footprint {footprint.id}: "
            f"CI = {carbon_intensity:.3f} kg CO2e/kg yield"
        )
        
        return footprint
    
    async def get_emission_factor(
        self,
        db: AsyncSession,
        organization_id: int,
        category: EmissionCategory,
        source_name: str
    ) -> Optional[EmissionFactor]:
        """
        Get emission factor from database.
        
        Args:
            db: Database session
            organization_id: Organization ID
            category: Emission category
            source_name: Source name
        
        Returns:
            EmissionFactor: Emission factor if found
            None otherwise
        """
        query = select(EmissionFactor).where(
            and_(
                EmissionFactor.organization_id == organization_id,
                EmissionFactor.category == category,
                EmissionFactor.source_name == source_name
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()


# Singleton instance
_emissions_service = None

def get_emissions_calculator_service() -> EmissionsCalculatorService:
    """Get singleton emissions calculator service instance."""
    global _emissions_service
    if _emissions_service is None:
        _emissions_service = EmissionsCalculatorService()
    return _emissions_service

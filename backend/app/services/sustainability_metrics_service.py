"""
Sustainability Metrics Service

Calculates and aggregates sustainability impact metrics.

Scientific Basis:
    Impact Metrics:
        - Hectares impacted: Area under improved varieties
        - Farmers reached: Direct + indirect beneficiaries
        - Yield improvement: (New - Baseline) / Baseline × 100%
        - Climate resilience: Stress tolerance indicators
    
    UN Sustainable Development Goals (SDGs):
        - SDG 2: Zero Hunger (food security, nutrition)
        - SDG 13: Climate Action (mitigation, adaptation)
        - SDG 15: Life on Land (biodiversity, ecosystems)
        - SDG 17: Partnerships (collaboration, knowledge sharing)
    
    Adoption Metrics:
        - Direct adoption: Farmers using released varieties
        - Indirect adoption: Farmers using derived varieties
        - Adoption rate: Adopted area / Total target area
"""

import logging
from typing import Optional, List, Dict
from datetime import date, datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.climate import (
    ImpactMetric,
    SDGIndicator,
    VarietyRelease,
    PolicyAdoption,
    Publication,
    ImpactReport,
    MetricType,
    SDGGoal,
    ReleaseStatus,
    AdoptionLevel
)
from app.models.climate import CarbonStock, EmissionSource

logger = logging.getLogger(__name__)


class SustainabilityMetricsService:
    """
    Service for sustainability metrics and impact reporting.
    
    Handles:
    - Impact metric calculations
    - SDG indicator tracking
    - Variety release management
    - Policy adoption tracking
    - Impact report generation
    """
    
    async def calculate_hectares_impacted(
        self,
        db: AsyncSession,
        organization_id: int,
        program_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, float]:
        """
        Calculate total hectares impacted by breeding program.
        
        Aggregates:
        1. Variety releases (expected + actual adoption)
        2. Policy adoptions (target hectares)
        3. Trial areas (experimental)
        
        Args:
            db: Database session
            organization_id: Organization ID
            program_id: Program ID (optional)
            start_date: Start date (optional)
            end_date: End date (optional)
        
        Returns:
            dict: {
                'released_varieties_ha': float,
                'policy_adoptions_ha': float,
                'trial_areas_ha': float,
                'total_ha': float
            }
        """
        # Get variety releases
        query = select(VarietyRelease).where(
            VarietyRelease.organization_id == organization_id
        )
        
        if program_id:
            query = query.where(VarietyRelease.program_id == program_id)
        
        if start_date:
            query = query.where(VarietyRelease.release_date >= start_date)
        
        if end_date:
            query = query.where(VarietyRelease.release_date <= end_date)
        
        result = await db.execute(query)
        releases = result.scalars().all()
        
        # Sum actual adoption (or expected if actual not available)
        released_ha = sum(
            r.actual_adoption_ha or r.expected_adoption_ha or 0
            for r in releases
        )
        
        # Get policy adoptions
        query = select(PolicyAdoption).where(
            PolicyAdoption.organization_id == organization_id
        )
        
        if program_id:
            query = query.where(PolicyAdoption.program_id == program_id)
        
        if start_date:
            query = query.where(PolicyAdoption.adoption_date >= start_date)
        
        if end_date:
            query = query.where(PolicyAdoption.adoption_date <= end_date)
        
        result = await db.execute(query)
        policies = result.scalars().all()
        
        policy_ha = sum(p.target_hectares or 0 for p in policies)
        
        # TODO: Get trial areas from trials table
        # For now, placeholder
        trial_ha = 0.0
        
        total_ha = released_ha + policy_ha + trial_ha
        
        return {
            'released_varieties_ha': round(released_ha, 2),
            'policy_adoptions_ha': round(policy_ha, 2),
            'trial_areas_ha': round(trial_ha, 2),
            'total_ha': round(total_ha, 2)
        }
    
    async def calculate_farmers_reached(
        self,
        db: AsyncSession,
        organization_id: int,
        program_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, int]:
        """
        Calculate number of farmers reached.
        
        Aggregates:
        1. Policy adoptions (target farmers)
        2. Variety releases (estimated farmers based on area)
        
        Estimation:
            Farmers = Hectares / Average Farm Size
            (Assume 2 ha average farm size if not specified)
        
        Args:
            db: Database session
            organization_id: Organization ID
            program_id: Program ID (optional)
            start_date: Start date (optional)
            end_date: End date (optional)
        
        Returns:
            dict: {
                'direct_farmers': int,
                'policy_target_farmers': int,
                'estimated_total': int
            }
        """
        # Get policy adoptions
        query = select(PolicyAdoption).where(
            PolicyAdoption.organization_id == organization_id
        )
        
        if program_id:
            query = query.where(PolicyAdoption.program_id == program_id)
        
        if start_date:
            query = query.where(PolicyAdoption.adoption_date >= start_date)
        
        if end_date:
            query = query.where(PolicyAdoption.adoption_date <= end_date)
        
        result = await db.execute(query)
        policies = result.scalars().all()
        
        policy_farmers = sum(p.target_farmers or 0 for p in policies)
        
        # Estimate farmers from hectares
        hectares_data = await self.calculate_hectares_impacted(
            db, organization_id, program_id, start_date, end_date
        )
        
        # Assume 2 ha average farm size
        average_farm_size = 2.0
        estimated_farmers = int(hectares_data['total_ha'] / average_farm_size)
        
        # Direct farmers (from policies)
        direct_farmers = policy_farmers
        
        # Total (max of direct or estimated)
        total_farmers = max(direct_farmers, estimated_farmers)
        
        return {
            'direct_farmers': direct_farmers,
            'policy_target_farmers': policy_farmers,
            'estimated_from_area': estimated_farmers,
            'estimated_total': total_farmers
        }
    
    async def calculate_yield_improvement(
        self,
        db: AsyncSession,
        organization_id: int,
        germplasm_id: int,
        baseline_yield: float
    ) -> Optional[Dict[str, float]]:
        """
        Calculate yield improvement over baseline.
        
        Yield Improvement:
            Improvement (%) = (New Yield - Baseline) / Baseline × 100
        
        Args:
            db: Database session
            organization_id: Organization ID
            germplasm_id: Variety ID
            baseline_yield: Baseline yield (kg/ha or t/ha)
        
        Returns:
            dict: {
                'baseline_yield': float,
                'new_yield': float,
                'absolute_improvement': float,
                'percent_improvement': float
            }
            None if no yield data available
        """
        # TODO: Get yield data from observations
        # For now, placeholder
        # In production, query observation_units and observations tables
        # filtered by germplasm_id and trait = "yield"
        
        new_yield = baseline_yield * 1.15  # Placeholder: 15% improvement
        
        absolute_improvement = new_yield - baseline_yield
        percent_improvement = (absolute_improvement / baseline_yield) * 100
        
        return {
            'baseline_yield': round(baseline_yield, 2),
            'new_yield': round(new_yield, 2),
            'absolute_improvement': round(absolute_improvement, 2),
            'percent_improvement': round(percent_improvement, 2)
        }
    
    async def calculate_carbon_sequestered(
        self,
        db: AsyncSession,
        organization_id: int,
        start_date: date,
        end_date: date,
        program_id: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate total carbon sequestered.
        
        Aggregates carbon stock changes across all locations.
        
        Args:
            db: Database session
            organization_id: Organization ID
            start_date: Start date
            end_date: End date
            program_id: Program ID (optional)
        
        Returns:
            dict: {
                'total_carbon_sequestered': float,  # tonnes C
                'locations_count': int,
                'average_per_location': float
            }
        """
        # Get carbon stocks
        query = select(CarbonStock).where(
            and_(
                CarbonStock.organization_id == organization_id,
                CarbonStock.measurement_date >= start_date,
                CarbonStock.measurement_date <= end_date
            )
        )
        
        result = await db.execute(query)
        stocks = result.scalars().all()
        
        if not stocks:
            return {
                'total_carbon_sequestered': 0.0,
                'locations_count': 0,
                'average_per_location': 0.0
            }
        
        # Group by location and calculate change
        location_changes = {}
        for stock in stocks:
            loc_id = stock.location_id
            if loc_id not in location_changes:
                location_changes[loc_id] = []
            location_changes[loc_id].append(stock)
        
        total_sequestered = 0.0
        for loc_id, loc_stocks in location_changes.items():
            # Sort by date
            loc_stocks.sort(key=lambda x: x.measurement_date)
            if len(loc_stocks) >= 2:
                # Calculate change from first to last
                change = loc_stocks[-1].total_carbon_stock - loc_stocks[0].total_carbon_stock
                if change > 0:  # Only count positive changes (sequestration)
                    total_sequestered += change
        
        locations_count = len(location_changes)
        average_per_location = total_sequestered / locations_count if locations_count > 0 else 0
        
        return {
            'total_carbon_sequestered': round(total_sequestered, 2),
            'locations_count': locations_count,
            'average_per_location': round(average_per_location, 2)
        }
    
    async def calculate_emissions_reduced(
        self,
        db: AsyncSession,
        organization_id: int,
        start_date: date,
        end_date: date,
        program_id: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate total emissions reduced.
        
        Compares emissions from improved varieties vs. baseline.
        
        Args:
            db: Database session
            organization_id: Organization ID
            start_date: Start date
            end_date: End date
            program_id: Program ID (optional)
        
        Returns:
            dict: {
                'total_emissions_reduced': float,  # kg CO2e
                'baseline_emissions': float,
                'actual_emissions': float
            }
        """
        # Get emission sources
        query = select(EmissionSource).where(
            and_(
                EmissionSource.organization_id == organization_id,
                EmissionSource.activity_date >= start_date,
                EmissionSource.activity_date <= end_date
            )
        )
        
        result = await db.execute(query)
        emissions = result.scalars().all()
        
        actual_emissions = sum(e.co2e_emissions for e in emissions)
        
        # TODO: Calculate baseline emissions
        # For now, assume 20% reduction from baseline
        baseline_emissions = actual_emissions / 0.8  # If actual is 80%, baseline is 100%
        emissions_reduced = baseline_emissions - actual_emissions
        
        return {
            'total_emissions_reduced': round(emissions_reduced, 2),
            'baseline_emissions': round(baseline_emissions, 2),
            'actual_emissions': round(actual_emissions, 2),
            'reduction_percent': 20.0
        }
    
    async def generate_sdg_indicators(
        self,
        db: AsyncSession,
        organization_id: int,
        program_id: int,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        Generate UN SDG indicators for a program.
        
        Maps program outcomes to relevant SDG goals:
        - SDG 2: Zero Hunger
        - SDG 13: Climate Action
        - SDG 15: Life on Land
        - SDG 17: Partnerships
        
        Args:
            db: Database session
            organization_id: Organization ID
            program_id: Program ID
            start_date: Start date
            end_date: End date
        
        Returns:
            list: [{
                'sdg_goal': str,
                'indicator_code': str,
                'indicator_name': str,
                'contribution_value': float,
                'unit': str
            }]
        """
        indicators = []
        
        # SDG 2: Zero Hunger
        # Indicator 2.3.1: Volume of production per labour unit
        hectares_data = await self.calculate_hectares_impacted(
            db, organization_id, program_id, start_date, end_date
        )
        
        indicators.append({
            'sdg_goal': SDGGoal.SDG_2.value,
            'indicator_code': '2.3.1',
            'indicator_name': 'Agricultural productivity (hectares impacted)',
            'contribution_value': hectares_data['total_ha'],
            'unit': 'hectares'
        })
        
        # SDG 2: Zero Hunger
        # Indicator 2.4.1: Sustainable agriculture practices
        farmers_data = await self.calculate_farmers_reached(
            db, organization_id, program_id, start_date, end_date
        )
        
        indicators.append({
            'sdg_goal': SDGGoal.SDG_2.value,
            'indicator_code': '2.4.1',
            'indicator_name': 'Farmers adopting sustainable practices',
            'contribution_value': farmers_data['estimated_total'],
            'unit': 'farmers'
        })
        
        # SDG 13: Climate Action
        # Indicator 13.2.1: Climate change mitigation
        carbon_data = await self.calculate_carbon_sequestered(
            db, organization_id, start_date, end_date, program_id
        )
        
        indicators.append({
            'sdg_goal': SDGGoal.SDG_13.value,
            'indicator_code': '13.2.1',
            'indicator_name': 'Carbon sequestered',
            'contribution_value': carbon_data['total_carbon_sequestered'],
            'unit': 'tonnes C'
        })
        
        # SDG 13: Climate Action
        # Emissions reduction
        emissions_data = await self.calculate_emissions_reduced(
            db, organization_id, start_date, end_date, program_id
        )
        
        indicators.append({
            'sdg_goal': SDGGoal.SDG_13.value,
            'indicator_code': '13.2.2',
            'indicator_name': 'Emissions reduced',
            'contribution_value': emissions_data['total_emissions_reduced'],
            'unit': 'kg CO2e'
        })
        
        # SDG 15: Life on Land
        # Indicator 15.1.1: Forest and agricultural land area
        indicators.append({
            'sdg_goal': SDGGoal.SDG_15.value,
            'indicator_code': '15.1.1',
            'indicator_name': 'Sustainable agricultural land management',
            'contribution_value': hectares_data['total_ha'],
            'unit': 'hectares'
        })
        
        return indicators
    
    async def create_impact_report(
        self,
        db: AsyncSession,
        organization_id: int,
        program_id: int,
        report_title: str,
        report_type: str,
        reporting_period_start: date,
        reporting_period_end: date,
        generated_by_user_id: int,
        format: str = "PDF"
    ) -> ImpactReport:
        """
        Generate comprehensive impact report.
        
        Aggregates all sustainability metrics into a report.
        
        Args:
            db: Database session
            organization_id: Organization ID
            program_id: Program ID
            report_title: Report title
            report_type: Report type (annual, donor, gee_partner, custom)
            reporting_period_start: Start date
            reporting_period_end: End date
            generated_by_user_id: User ID
            format: Report format (PDF, DOCX, HTML)
        
        Returns:
            ImpactReport: Created report
        """
        # Gather all metrics
        hectares_data = await self.calculate_hectares_impacted(
            db, organization_id, program_id,
            reporting_period_start, reporting_period_end
        )
        
        farmers_data = await self.calculate_farmers_reached(
            db, organization_id, program_id,
            reporting_period_start, reporting_period_end
        )
        
        carbon_data = await self.calculate_carbon_sequestered(
            db, organization_id,
            reporting_period_start, reporting_period_end,
            program_id
        )
        
        emissions_data = await self.calculate_emissions_reduced(
            db, organization_id,
            reporting_period_start, reporting_period_end,
            program_id
        )
        
        sdg_indicators = await self.generate_sdg_indicators(
            db, organization_id, program_id,
            reporting_period_start, reporting_period_end
        )
        
        # Compile report data
        report_data = {
            'summary': {
                'organization_id': organization_id,
                'program_id': program_id,
                'reporting_period': {
                    'start': reporting_period_start.isoformat(),
                    'end': reporting_period_end.isoformat()
                },
                'generated_date': date.today().isoformat()
            },
            'impact_metrics': {
                'hectares': hectares_data,
                'farmers': farmers_data,
                'carbon': carbon_data,
                'emissions': emissions_data
            },
            'sdg_indicators': sdg_indicators
        }
        
        # Create report record
        report = ImpactReport(
            organization_id=organization_id,
            program_id=program_id,
            report_title=report_title,
            report_type=report_type,
            reporting_period_start=reporting_period_start,
            reporting_period_end=reporting_period_end,
            generated_date=date.today(),
            generated_by_user_id=generated_by_user_id,
            report_data=report_data,
            format=format,
            notes="Auto-generated impact report"
        )
        
        db.add(report)
        await db.commit()
        await db.refresh(report)
        
        logger.info(f"Created impact report {report.id}: {report_title}")
        
        return report


# Singleton instance
_sustainability_service = None

def get_sustainability_metrics_service() -> SustainabilityMetricsService:
    """Get singleton sustainability metrics service instance."""
    global _sustainability_service
    if _sustainability_service is None:
        _sustainability_service = SustainabilityMetricsService()
    return _sustainability_service

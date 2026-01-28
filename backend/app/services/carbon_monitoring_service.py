"""
Carbon Monitoring Service

Business logic for carbon stock calculations and monitoring.

Scientific Basis:
    Soil Organic Carbon (SOC) Stock Calculation:
        Stock (t/ha) = SOC (%) × BD (g/cm³) × Depth (cm) × 100
        
        Where:
        - SOC = Soil organic carbon percentage by weight
        - BD = Bulk density of soil
        - Depth = Sampling depth in cm
        - Factor 100 converts to tonnes per hectare
        
        Example:
        SOC = 2.5%, BD = 1.3 g/cm³, Depth = 30 cm
        Stock = 2.5 × 1.3 × 30 × 100 = 9,750 kg/ha = 9.75 t/ha
    
    Vegetation Carbon:
        Carbon (t/ha) = Dry Biomass (t/ha) × 0.45
        
        Carbon fraction = 0.45 (45% of dry biomass is carbon)
    
    Total Ecosystem Carbon:
        Total = Soil Carbon + Vegetation Carbon
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime, date
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.climate import (
    CarbonStock,
    CarbonMeasurement,
    CarbonMeasurementType
)
from app.services.gee_integration_service import get_gee_service

logger = logging.getLogger(__name__)


class CarbonMonitoringService:
    """
    Service for carbon stock monitoring and calculations.
    
    Handles:
    - Carbon stock creation and retrieval
    - SOC calculations from measurements
    - Satellite-based carbon estimation
    - Time series analysis
    """
    
    @staticmethod
    def calculate_soc_stock(
        soc_percent: float,
        bulk_density: float,
        depth_cm: int
    ) -> float:
        """
        Calculate soil organic carbon stock.
        
        Formula:
            Stock (t/ha) = SOC (%) × BD (g/cm³) × Depth (cm) × 100
        
        Args:
            soc_percent: Soil organic carbon percentage (0-100)
            bulk_density: Soil bulk density in g/cm³ (typically 1.0-1.6)
            depth_cm: Sampling depth in cm (typically 30 or 100)
        
        Returns:
            float: Carbon stock in tonnes per hectare
        
        Example:
            >>> calculate_soc_stock(2.5, 1.3, 30)
            9.75  # tonnes C/ha
        """
        if soc_percent < 0 or soc_percent > 100:
            raise ValueError("SOC percent must be between 0 and 100")
        if bulk_density <= 0 or bulk_density > 2.0:
            raise ValueError("Bulk density must be between 0 and 2.0 g/cm³")
        if depth_cm <= 0:
            raise ValueError("Depth must be positive")
        
        stock = soc_percent * bulk_density * depth_cm * 100 / 1000
        return round(stock, 2)
    
    @staticmethod
    def calculate_vegetation_carbon(
        dry_biomass_t_ha: float
    ) -> float:
        """
        Calculate vegetation carbon from dry biomass.
        
        Formula:
            Carbon (t/ha) = Dry Biomass (t/ha) × 0.45
        
        Carbon fraction = 0.45 (45% of dry biomass)
        
        Args:
            dry_biomass_t_ha: Dry biomass in tonnes per hectare
        
        Returns:
            float: Vegetation carbon in tonnes per hectare
        
        Example:
            >>> calculate_vegetation_carbon(10.0)
            4.5  # tonnes C/ha
        """
        if dry_biomass_t_ha < 0:
            raise ValueError("Biomass cannot be negative")
        
        carbon = dry_biomass_t_ha * 0.45
        return round(carbon, 2)
    
    async def create_carbon_stock(
        self,
        db: AsyncSession,
        organization_id: int,
        location_id: int,
        measurement_date: date,
        measurement_type: CarbonMeasurementType,
        soil_carbon_stock: Optional[float] = None,
        vegetation_carbon_stock: Optional[float] = None,
        measurement_depth_cm: int = 30,
        confidence_level: float = 0.8,
        gee_image_id: Optional[str] = None,
        additional_data: Optional[Dict] = None
    ) -> CarbonStock:
        """
        Create a new carbon stock record.
        
        Args:
            db: Database session
            organization_id: Organization ID
            location_id: Location/field ID
            measurement_date: Date of measurement
            measurement_type: Type of measurement
            soil_carbon_stock: Soil carbon (t/ha), optional
            vegetation_carbon_stock: Vegetation carbon (t/ha), optional
            measurement_depth_cm: Soil sampling depth
            confidence_level: Confidence (0-1)
            gee_image_id: Google Earth Engine image ID
            additional_data: Additional metadata
        
        Returns:
            CarbonStock: Created carbon stock record
        
        Raises:
            ValueError: If neither soil nor vegetation carbon provided
        """
        # Calculate total carbon
        total_carbon = 0.0
        if soil_carbon_stock:
            total_carbon += soil_carbon_stock
        if vegetation_carbon_stock:
            total_carbon += vegetation_carbon_stock
        
        if total_carbon == 0:
            raise ValueError("At least one carbon component must be provided")
        
        # Create carbon stock
        carbon_stock = CarbonStock(
            organization_id=organization_id,
            location_id=location_id,
            measurement_date=measurement_date,
            soil_carbon_stock=soil_carbon_stock,
            vegetation_carbon_stock=vegetation_carbon_stock,
            total_carbon_stock=total_carbon,
            measurement_depth_cm=measurement_depth_cm,
            measurement_type=measurement_type,
            confidence_level=confidence_level,
            gee_image_id=gee_image_id,
            additional_data=additional_data
        )
        
        db.add(carbon_stock)
        await db.commit()
        await db.refresh(carbon_stock)
        
        logger.info(
            f"Created carbon stock {carbon_stock.id} for location {location_id}: "
            f"{total_carbon} t/ha"
        )
        
        return carbon_stock
    
    async def get_carbon_stocks(
        self,
        db: AsyncSession,
        organization_id: int,
        location_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        measurement_type: Optional[CarbonMeasurementType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CarbonStock]:
        """
        Get carbon stocks with filters.
        
        Args:
            db: Database session
            organization_id: Organization ID
            location_id: Filter by location (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            measurement_type: Filter by measurement type (optional)
            limit: Maximum results
            offset: Results offset
        
        Returns:
            list: List of CarbonStock records
        """
        query = select(CarbonStock).where(
            CarbonStock.organization_id == organization_id
        )
        
        if location_id:
            query = query.where(CarbonStock.location_id == location_id)
        
        if start_date:
            query = query.where(CarbonStock.measurement_date >= start_date)
        
        if end_date:
            query = query.where(CarbonStock.measurement_date <= end_date)
        
        if measurement_type:
            query = query.where(CarbonStock.measurement_type == measurement_type)
        
        query = query.order_by(CarbonStock.measurement_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_carbon_time_series(
        self,
        db: AsyncSession,
        organization_id: int,
        location_id: int,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        Get carbon stock time series for a location.
        
        Args:
            db: Database session
            organization_id: Organization ID
            location_id: Location ID
            start_date: Start date
            end_date: End date
        
        Returns:
            list: [{
                'date': date,
                'soil_carbon': float,
                'vegetation_carbon': float,
                'total_carbon': float,
                'measurement_type': str
            }]
        """
        stocks = await self.get_carbon_stocks(
            db, organization_id, location_id, start_date, end_date
        )
        
        time_series = []
        for stock in stocks:
            time_series.append({
                'date': stock.measurement_date.isoformat(),
                'soil_carbon': stock.soil_carbon_stock,
                'vegetation_carbon': stock.vegetation_carbon_stock,
                'total_carbon': stock.total_carbon_stock,
                'measurement_type': stock.measurement_type.value,
                'confidence': stock.confidence_level
            })
        
        return time_series
    
    async def estimate_carbon_from_satellite(
        self,
        db: AsyncSession,
        organization_id: int,
        location_id: int,
        latitude: float,
        longitude: float,
        measurement_date: date,
        crop_type: str = "generic"
    ) -> Optional[CarbonStock]:
        """
        Estimate carbon stock from satellite imagery.
        
        Uses Google Earth Engine to:
        1. Estimate soil carbon from multispectral indices
        2. Estimate vegetation carbon from NDVI/biomass
        3. Create carbon stock record
        
        Args:
            db: Database session
            organization_id: Organization ID
            location_id: Location ID
            latitude: Latitude
            longitude: Longitude
            measurement_date: Date for estimation
            crop_type: Crop type for biomass model
        
        Returns:
            CarbonStock: Created carbon stock record
            None if estimation fails
        """
        gee_service = get_gee_service()
        
        # Estimate soil carbon
        soc_data = await gee_service.get_soil_carbon_estimate(
            latitude, longitude, datetime.combine(measurement_date, datetime.min.time())
        )
        
        if not soc_data:
            logger.warning(f"SOC estimation failed for location {location_id}")
            return None
        
        # Estimate vegetation carbon
        veg_data = await gee_service.calculate_vegetation_carbon(
            latitude, longitude,
            datetime.combine(measurement_date, datetime.min.time()),
            crop_type
        )
        
        if not veg_data:
            logger.warning(f"Vegetation carbon estimation failed for location {location_id}")
            vegetation_carbon = None
            confidence = soc_data['confidence']
        else:
            vegetation_carbon = veg_data['vegetation_carbon']
            # Combined confidence (average)
            confidence = (soc_data['confidence'] + veg_data['confidence']) / 2
        
        # Estimate soil carbon stock from SOC percentage
        # Assume standard bulk density and depth if not provided
        bulk_density = 1.3  # g/cm³ (typical for agricultural soils)
        depth_cm = 30  # Standard depth
        
        soil_carbon_stock = self.calculate_soc_stock(
            soc_data['soc_estimate'],
            bulk_density,
            depth_cm
        )
        
        # Create carbon stock record
        carbon_stock = await self.create_carbon_stock(
            db=db,
            organization_id=organization_id,
            location_id=location_id,
            measurement_date=measurement_date,
            measurement_type=CarbonMeasurementType.SATELLITE_ESTIMATED,
            soil_carbon_stock=soil_carbon_stock,
            vegetation_carbon_stock=vegetation_carbon,
            measurement_depth_cm=depth_cm,
            confidence_level=confidence,
            gee_image_id=soc_data['image_id'],
            additional_data={
                'soc_percent': soc_data['soc_estimate'],
                'bulk_density_assumed': bulk_density,
                'indices': soc_data.get('indices', {}),
                'vegetation_data': veg_data,
                'cloud_cover': soc_data['cloud_cover']
            }
        )
        
        logger.info(
            f"Created satellite-based carbon stock for location {location_id}: "
            f"Soil={soil_carbon_stock} t/ha, Veg={vegetation_carbon} t/ha"
        )
        
        return carbon_stock
    
    async def calculate_carbon_sequestration_rate(
        self,
        db: AsyncSession,
        organization_id: int,
        location_id: int,
        start_date: date,
        end_date: date
    ) -> Optional[Dict]:
        """
        Calculate carbon sequestration rate over time.
        
        Sequestration Rate:
            Rate (t C/ha/year) = (C_final - C_initial) / Years
            
            Typical rates: 0.2-1.0 t C/ha/year for agricultural soils
        
        Args:
            db: Database session
            organization_id: Organization ID
            location_id: Location ID
            start_date: Start date
            end_date: End date
        
        Returns:
            dict: {
                'initial_carbon': float,
                'final_carbon': float,
                'change': float,
                'rate_per_year': float,
                'years': float
            }
            None if insufficient data
        """
        stocks = await self.get_carbon_stocks(
            db, organization_id, location_id, start_date, end_date
        )
        
        if len(stocks) < 2:
            logger.warning(f"Insufficient data for sequestration rate calculation")
            return None
        
        # Sort by date
        stocks = sorted(stocks, key=lambda x: x.measurement_date)
        
        initial = stocks[0]
        final = stocks[-1]
        
        # Calculate time difference in years
        days = (final.measurement_date - initial.measurement_date).days
        years = days / 365.25
        
        if years == 0:
            return None
        
        # Calculate change and rate
        change = final.total_carbon_stock - initial.total_carbon_stock
        rate_per_year = change / years
        
        return {
            'initial_carbon': initial.total_carbon_stock,
            'final_carbon': final.total_carbon_stock,
            'change': round(change, 2),
            'rate_per_year': round(rate_per_year, 2),
            'years': round(years, 2),
            'initial_date': initial.measurement_date.isoformat(),
            'final_date': final.measurement_date.isoformat()
        }


# Singleton instance
_carbon_service = None

def get_carbon_monitoring_service() -> CarbonMonitoringService:
    """Get singleton carbon monitoring service instance."""
    global _carbon_service
    if _carbon_service is None:
        _carbon_service = CarbonMonitoringService()
    return _carbon_service

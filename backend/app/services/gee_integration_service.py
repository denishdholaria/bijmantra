"""
Google Earth Engine Integration Service

Provides wrapper functions for Google Earth Engine API to support:
- Soil carbon monitoring via satellite imagery
- Vegetation indices (NDVI, EVI, LAI)
- Climate data retrieval
- Habitat suitability mapping

Scientific Basis:
    Soil Organic Carbon (SOC) Estimation:
        - Uses Sentinel-2 multispectral data
        - Empirical models: SOC = f(NDVI, SAVI, BSI, brightness)
        - Typical R² = 0.6-0.8 for calibrated models
    
    Vegetation Carbon:
        - Biomass estimation from NDVI/LAI
        - Carbon fraction = 0.45 (45% of dry biomass)
        - Above-ground biomass (AGB) models vary by crop
    
    Data Sources:
        - Sentinel-2: 10m resolution, 5-day revisit
        - Landsat 8/9: 30m resolution, 16-day revisit
        - MODIS: 250m resolution, daily
        - ERA5: Climate reanalysis data
        - CHIRPS: Precipitation data
"""

import os
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


class GEEIntegrationService:
    """
    Google Earth Engine integration service.
    
    Handles authentication, data retrieval, and processing of satellite imagery
    and climate data for climate-smart agriculture applications.
    """
    
    def __init__(self):
        """Initialize GEE service."""
        self._authenticated = False
        self._ee = None
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Google Earth Engine.
        
        Uses service account credentials from environment variables:
        - GEE_SERVICE_ACCOUNT_EMAIL: Service account email
        - GEE_PRIVATE_KEY_PATH: Path to service account JSON key
        
        Returns:
            bool: True if authentication successful, False otherwise
        
        Raises:
            ValueError: If credentials not found in environment
            Exception: If authentication fails
        """
        if self._authenticated:
            return True
        
        try:
            import ee
            self._ee = ee
            
            # Get credentials from environment
            service_account = os.getenv('GEE_SERVICE_ACCOUNT_EMAIL')
            key_file = os.getenv('GEE_PRIVATE_KEY_PATH')
            
            if not service_account or not key_file:
                logger.warning(
                    "GEE credentials not found. Set GEE_SERVICE_ACCOUNT_EMAIL "
                    "and GEE_PRIVATE_KEY_PATH environment variables."
                )
                return False
            
            # Authenticate
            credentials = ee.ServiceAccountCredentials(
                email=service_account,
                key_file=key_file
            )
            ee.Initialize(credentials)
            
            self._authenticated = True
            logger.info("Successfully authenticated with Google Earth Engine")
            return True
            
        except ImportError:
            logger.error(
                "earthengine-api not installed. "
                "Install with: pip install earthengine-api"
            )
            return False
        except Exception as e:
            logger.error(f"GEE authentication failed: {str(e)}")
            return False
    
    async def get_soil_carbon_estimate(
        self,
        latitude: float,
        longitude: float,
        date: datetime,
        buffer_meters: int = 100
    ) -> Optional[Dict]:
        """
        Estimate soil organic carbon from satellite imagery.
        
        Uses Sentinel-2 multispectral data to estimate SOC percentage.
        
        Scientific Method:
            SOC estimation uses empirical relationship:
            SOC (%) ≈ a + b×NDVI + c×SAVI + d×BSI + e×Brightness
            
            Where:
            - NDVI = (NIR - Red) / (NIR + Red)
            - SAVI = ((NIR - Red) / (NIR + Red + L)) × (1 + L), L = 0.5
            - BSI = ((SWIR + Red) - (NIR + Blue)) / ((SWIR + Red) + (NIR + Blue))
            - Brightness = sqrt(Red² + NIR² + SWIR²)
            
            Coefficients (a,b,c,d,e) are region-specific and require calibration.
            Default model provides relative estimates only.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            date: Date for imagery acquisition
            buffer_meters: Buffer radius around point (default 100m)
        
        Returns:
            dict: {
                'soc_estimate': float,  # Estimated SOC percentage
                'confidence': float,    # Confidence level (0-1)
                'image_id': str,        # GEE image ID used
                'cloud_cover': float,   # Cloud cover percentage
                'acquisition_date': str # Actual image date
            }
            None if estimation fails
        """
        if not await self.authenticate():
            return None
        
        try:
            ee = self._ee
            
            # Create point geometry
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(buffer_meters)
            
            # Get Sentinel-2 image collection
            start_date = (date - timedelta(days=15)).strftime('%Y-%m-%d')
            end_date = (date + timedelta(days=15)).strftime('%Y-%m-%d')
            
            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                         .filterBounds(region)
                         .filterDate(start_date, end_date)
                         .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                         .sort('CLOUDY_PIXEL_PERCENTAGE'))
            
            # Get best image
            if collection.size().getInfo() == 0:
                logger.warning(f"No Sentinel-2 images found for {latitude}, {longitude} on {date}")
                return None
            
            image = collection.first()
            
            # Calculate indices
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            
            # SAVI (Soil Adjusted Vegetation Index)
            L = 0.5
            savi = (image.select('B8').subtract(image.select('B4'))
                   .divide(image.select('B8').add(image.select('B4')).add(L))
                   .multiply(1 + L)
                   .rename('SAVI'))
            
            # BSI (Bare Soil Index)
            bsi = (image.select('B11').add(image.select('B4'))
                  .subtract(image.select('B8').add(image.select('B2')))
                  .divide(image.select('B11').add(image.select('B4'))
                  .add(image.select('B8')).add(image.select('B2')))
                  .rename('BSI'))
            
            # Brightness
            brightness = (image.select('B4').pow(2)
                         .add(image.select('B8').pow(2))
                         .add(image.select('B11').pow(2))
                         .sqrt()
                         .rename('Brightness'))
            
            # Combine indices
            indices = ee.Image.cat([ndvi, savi, bsi, brightness])
            
            # Get values at point
            values = indices.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=10,
                maxPixels=1e9
            ).getInfo()
            
            # Simple empirical model (requires calibration for production)
            # This is a placeholder - real model needs regional calibration
            soc_estimate = (
                1.5 +  # Baseline
                2.0 * values.get('NDVI', 0) +
                1.5 * values.get('SAVI', 0) -
                1.0 * values.get('BSI', 0) +
                0.001 * values.get('Brightness', 0)
            )
            
            # Clamp to reasonable range
            soc_estimate = max(0.5, min(5.0, soc_estimate))
            
            # Get image metadata
            image_info = image.getInfo()
            properties = image_info.get('properties', {})
            
            return {
                'soc_estimate': round(soc_estimate, 2),
                'confidence': 0.6,  # Medium confidence for uncalibrated model
                'image_id': image_info.get('id', ''),
                'cloud_cover': properties.get('CLOUDY_PIXEL_PERCENTAGE', 0),
                'acquisition_date': properties.get('system:time_start', ''),
                'indices': {
                    'ndvi': round(values.get('NDVI', 0), 3),
                    'savi': round(values.get('SAVI', 0), 3),
                    'bsi': round(values.get('BSI', 0), 3),
                    'brightness': round(values.get('Brightness', 0), 1)
                }
            }
            
        except Exception as e:
            logger.error(f"SOC estimation failed: {str(e)}")
            return None
    
    async def get_ndvi_time_series(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
        buffer_meters: int = 100
    ) -> Optional[List[Dict]]:
        """
        Get NDVI time series from satellite imagery.
        
        NDVI (Normalized Difference Vegetation Index):
            NDVI = (NIR - Red) / (NIR + Red)
            
            Interpretation:
            - NDVI < 0.2: Bare soil, rock, water
            - NDVI 0.2-0.4: Sparse vegetation
            - NDVI 0.4-0.6: Moderate vegetation
            - NDVI > 0.6: Dense vegetation
            
            For crops:
            - Peak NDVI indicates maximum biomass
            - NDVI decline indicates senescence
            - Temporal profile indicates phenology
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            start_date: Start date for time series
            end_date: End date for time series
            buffer_meters: Buffer radius around point
        
        Returns:
            list: [{
                'date': str,
                'ndvi': float,
                'evi': float,
                'cloud_cover': float,
                'image_id': str
            }]
            None if retrieval fails
        """
        if not await self.authenticate():
            return None
        
        try:
            ee = self._ee
            
            # Create point geometry
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(buffer_meters)
            
            # Get Sentinel-2 collection
            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                         .filterBounds(region)
                         .filterDate(
                             start_date.strftime('%Y-%m-%d'),
                             end_date.strftime('%Y-%m-%d')
                         )
                         .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)))
            
            # Calculate NDVI and EVI for each image
            def add_indices(image):
                ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
                
                # EVI (Enhanced Vegetation Index)
                evi = (image.select('B8').subtract(image.select('B4'))
                      .divide(image.select('B8')
                      .add(image.select('B4').multiply(6))
                      .subtract(image.select('B2').multiply(7.5))
                      .add(1))
                      .multiply(2.5)
                      .rename('EVI'))
                
                return image.addBands([ndvi, evi])
            
            collection = collection.map(add_indices)
            
            # Get time series
            def extract_values(image):
                values = image.select(['NDVI', 'EVI']).reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=region,
                    scale=10,
                    maxPixels=1e9
                )
                
                return ee.Feature(None, {
                    'date': image.date().format('YYYY-MM-dd'),
                    'ndvi': values.get('NDVI'),
                    'evi': values.get('EVI'),
                    'cloud_cover': image.get('CLOUDY_PIXEL_PERCENTAGE'),
                    'image_id': image.id()
                })
            
            features = collection.map(extract_values).getInfo()
            
            # Extract time series data
            time_series = []
            for feature in features.get('features', []):
                props = feature.get('properties', {})
                if props.get('ndvi') is not None:
                    time_series.append({
                        'date': props.get('date'),
                        'ndvi': round(props.get('ndvi', 0), 3),
                        'evi': round(props.get('evi', 0), 3),
                        'cloud_cover': props.get('cloud_cover', 0),
                        'image_id': props.get('image_id', '')
                    })
            
            # Sort by date
            time_series.sort(key=lambda x: x['date'])
            
            return time_series
            
        except Exception as e:
            logger.error(f"NDVI time series retrieval failed: {str(e)}")
            return None
    
    async def calculate_vegetation_carbon(
        self,
        latitude: float,
        longitude: float,
        date: datetime,
        crop_type: str = "generic",
        buffer_meters: int = 100
    ) -> Optional[Dict]:
        """
        Estimate vegetation carbon from satellite imagery.
        
        Vegetation Carbon Estimation:
            1. Estimate biomass from NDVI/LAI
            2. Convert to carbon: C = Biomass × 0.45
            
            Biomass models (crop-specific):
            - Generic: AGB (kg/ha) = 1000 × (NDVI - 0.1) / 0.7
            - Rice: AGB = 15000 × NDVI²
            - Wheat: AGB = 12000 × NDVI²
            - Maize: AGB = 18000 × NDVI²
            
            Carbon fraction = 0.45 (45% of dry biomass)
            
            Note: These are simplified models. Production use requires
            crop-specific calibration with ground truth data.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            date: Date for estimation
            crop_type: Crop type for biomass model
            buffer_meters: Buffer radius around point
        
        Returns:
            dict: {
                'vegetation_carbon': float,  # tonnes C/ha
                'biomass': float,            # tonnes dry matter/ha
                'ndvi': float,
                'confidence': float,
                'image_id': str
            }
            None if estimation fails
        """
        if not await self.authenticate():
            return None
        
        try:
            # Get NDVI
            ndvi_data = await self.get_ndvi_time_series(
                latitude, longitude,
                date - timedelta(days=7),
                date + timedelta(days=7),
                buffer_meters
            )
            
            if not ndvi_data:
                return None
            
            # Use closest date
            closest = min(ndvi_data, key=lambda x: abs(
                datetime.strptime(x['date'], '%Y-%m-%d') - date
            ))
            
            ndvi = closest['ndvi']
            
            # Biomass models by crop type
            biomass_models = {
                'generic': lambda n: 1000 * (n - 0.1) / 0.7,
                'rice': lambda n: 15000 * n ** 2,
                'wheat': lambda n: 12000 * n ** 2,
                'maize': lambda n: 18000 * n ** 2,
                'soybean': lambda n: 10000 * n ** 2,
            }
            
            model = biomass_models.get(crop_type.lower(), biomass_models['generic'])
            biomass_kg_ha = max(0, model(ndvi))
            biomass_t_ha = biomass_kg_ha / 1000
            
            # Convert to carbon (45% of dry biomass)
            carbon_t_ha = biomass_t_ha * 0.45
            
            return {
                'vegetation_carbon': round(carbon_t_ha, 2),
                'biomass': round(biomass_t_ha, 2),
                'ndvi': ndvi,
                'confidence': 0.7 if crop_type != 'generic' else 0.5,
                'image_id': closest['image_id'],
                'acquisition_date': closest['date']
            }
            
        except Exception as e:
            logger.error(f"Vegetation carbon estimation failed: {str(e)}")
            return None
    
    async def get_climate_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict]:
        """
        Get climate data from ERA5 reanalysis.
        
        Retrieves temperature, precipitation, and other climate variables.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            start_date: Start date
            end_date: End date
        
        Returns:
            dict: Climate data summary
            None if retrieval fails
        """
        if not await self.authenticate():
            return None
        
        try:
            ee = self._ee
            
            point = ee.Geometry.Point([longitude, latitude])
            
            # ERA5 daily aggregates
            collection = (ee.ImageCollection('ECMWF/ERA5/DAILY')
                         .filterBounds(point)
                         .filterDate(
                             start_date.strftime('%Y-%m-%d'),
                             end_date.strftime('%Y-%m-%d')
                         ))
            
            # Calculate statistics
            stats = collection.select([
                'mean_2m_air_temperature',
                'total_precipitation',
                'surface_solar_radiation_downwards'
            ]).reduce(ee.Reducer.mean()).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=27830,  # ERA5 resolution ~28km
                maxPixels=1e9
            ).getInfo()
            
            return {
                'mean_temperature_k': stats.get('mean_2m_air_temperature_mean'),
                'mean_temperature_c': stats.get('mean_2m_air_temperature_mean', 273.15) - 273.15,
                'total_precipitation_m': stats.get('total_precipitation_mean'),
                'solar_radiation_j_m2': stats.get('surface_solar_radiation_downwards_mean')
            }
            
        except Exception as e:
            logger.error(f"Climate data retrieval failed: {str(e)}")
            return None


# Singleton instance
_gee_service = None

def get_gee_service() -> GEEIntegrationService:
    """Get singleton GEE service instance."""
    global _gee_service
    if _gee_service is None:
        _gee_service = GEEIntegrationService()
    return _gee_service

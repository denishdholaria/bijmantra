"""
NASA POWER API integration for BijMantra.

Downloads global agroclimatology data from NASA's Prediction Of Worldwide
Energy Resources (POWER) project.

All downloads go DIRECTLY to /Volumes/hfs/nasa-power-data/ with NO intermediate
caching on the primary macOS drive.

API Documentation: https://power.larc.nasa.gov/docs/
Data Coverage: Global (0.5° × 0.5°), 1981-present, daily/monthly/annual
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
import requests
from datetime import datetime, date

logger = logging.getLogger(__name__)

# Import download configuration to ensure external drive usage
from app.integrations.download_config import get_data_dir

# NASA POWER API endpoint
NASA_POWER_API = "https://power.larc.nasa.gov/api/temporal"

# Agricultural parameters
AG_PARAMETERS = {
    # Temperature
    "T2M": "Temperature at 2 Meters (°C)",
    "T2M_MAX": "Maximum Temperature at 2 Meters (°C)",
    "T2M_MIN": "Minimum Temperature at 2 Meters (°C)",
    
    # Precipitation
    "PRECTOTCORR": "Precipitation Corrected (mm/day)",
    
    # Solar Radiation
    "ALLSKY_SFC_SW_DWN": "All Sky Surface Shortwave Downward Irradiance (MJ/m²/day)",
    
    # Humidity
    "RH2M": "Relative Humidity at 2 Meters (%)",
    
    # Wind
    "WS2M": "Wind Speed at 2 Meters (m/s)",
    
    # Evapotranspiration
    "EVPTRNS": "Evapotranspiration Energy Flux (MJ/m²/day)",
    
    # Frost
    "FROST_DAYS": "Frost Days (days with T2M_MIN <= 0°C)",
}


class NASAPowerClient:
    """
    Client for downloading NASA POWER agroclimatology data.
    
    Usage:
        client = NASAPowerClient()
        data = client.get_point_data(
            latitude=30.9,
            longitude=75.8,
            start_date=date(2020, 1, 1),
            end_date=date(2020, 12, 31),
            parameters=["T2M", "PRECTOTCORR"]
        )
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize NASA POWER client.
        
        Args:
            cache_dir: Directory to cache downloaded data.
                      Defaults to /Volumes/hfs/nasa-power-data/
        """
        self.cache_dir = cache_dir or get_data_dir("nasa_power")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BijMantra/1.0 (Agricultural Research Platform)"
        })
    
    def get_point_data(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        parameters: Optional[List[str]] = None,
        temporal_api: str = "daily"
    ) -> Dict[str, Any]:
        """
        Get climate data for a specific point location.
        
        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            start_date: Start date
            end_date: End date
            parameters: List of parameter codes (default: all AG parameters)
            temporal_api: "daily", "monthly", or "climatology"
            
        Returns:
            Dictionary with climate data
        """
        if parameters is None:
            parameters = list(AG_PARAMETERS.keys())
        
        # Build API URL
        params_str = ",".join(parameters)
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        url = (
            f"{NASA_POWER_API}/{temporal_api}/point"
            f"?parameters={params_str}"
            f"&community=AG"
            f"&longitude={longitude}"
            f"&latitude={latitude}"
            f"&start={start_str}"
            f"&end={end_str}"
            f"&format=JSON"
        )
        
        # Check cache
        cache_key = f"point_{latitude}_{longitude}_{start_str}_{end_str}_{temporal_api}"
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            logger.info(f"Using cached data from {cache_file}")
            import json
            with open(cache_file) as f:
                return json.load(f)
        
        # Fetch from API
        logger.info(f"Fetching NASA POWER data for ({latitude}, {longitude})")
        logger.debug(f"URL: {url}")
        
        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            import json
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"✓ Cached data to {cache_file}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch NASA POWER data: {e}")
            raise
    
    def get_regional_data(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: date,
        end_date: date,
        parameters: Optional[List[str]] = None,
        temporal_api: str = "daily"
    ) -> Dict[str, Any]:
        """
        Get climate data for a bounding box region.
        
        Args:
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            start_date: Start date
            end_date: End date
            parameters: List of parameter codes
            temporal_api: "daily", "monthly", or "climatology"
            
        Returns:
            Dictionary with regional climate data
        """
        if parameters is None:
            parameters = list(AG_PARAMETERS.keys())
        
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # Build API URL
        params_str = ",".join(parameters)
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        url = (
            f"{NASA_POWER_API}/{temporal_api}/regional"
            f"?parameters={params_str}"
            f"&community=AG"
            f"&longitude-min={min_lon}"
            f"&longitude-max={max_lon}"
            f"&latitude-min={min_lat}"
            f"&latitude-max={max_lat}"
            f"&start={start_str}"
            f"&end={end_str}"
            f"&format=JSON"
        )
        
        # Check cache
        cache_key = f"regional_{min_lon}_{min_lat}_{max_lon}_{max_lat}_{start_str}_{end_str}_{temporal_api}"
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            logger.info(f"Using cached data from {cache_file}")
            import json
            with open(cache_file) as f:
                return json.load(f)
        
        # Fetch from API
        logger.info(f"Fetching NASA POWER regional data for bbox {bbox}")
        logger.debug(f"URL: {url}")
        
        try:
            response = self.session.get(url, timeout=300)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            import json
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"✓ Cached data to {cache_file}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch NASA POWER regional data: {e}")
            raise
    
    def get_climatology(
        self,
        latitude: float,
        longitude: float,
        parameters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get 30-year climatology (1991-2020) for a location.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            parameters: List of parameter codes
            
        Returns:
            Dictionary with climatology data (monthly averages)
        """
        if parameters is None:
            parameters = list(AG_PARAMETERS.keys())
        
        params_str = ",".join(parameters)
        
        url = (
            f"{NASA_POWER_API}/climatology/point"
            f"?parameters={params_str}"
            f"&community=AG"
            f"&longitude={longitude}"
            f"&latitude={latitude}"
            f"&format=JSON"
        )
        
        # Check cache
        cache_key = f"climatology_{latitude}_{longitude}"
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            logger.info(f"Using cached climatology from {cache_file}")
            import json
            with open(cache_file) as f:
                return json.load(f)
        
        # Fetch from API
        logger.info(f"Fetching NASA POWER climatology for ({latitude}, {longitude})")
        
        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            import json
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"✓ Cached climatology to {cache_file}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch NASA POWER climatology: {e}")
            raise
    
    def parse_daily_data(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse NASA POWER daily response into a list of records.
        
        Args:
            response: Raw API response
            
        Returns:
            List of daily records with date and parameter values
        """
        parameters = response.get("properties", {}).get("parameter", {})
        
        if not parameters:
            return []
        
        # Get all dates from the first parameter
        first_param = list(parameters.values())[0]
        dates = sorted(first_param.keys())
        
        records = []
        for date_str in dates:
            record = {"date": date_str}
            
            for param_code, values in parameters.items():
                value = values.get(date_str)
                # NASA POWER uses -999 for missing data
                if value != -999:
                    record[param_code] = value
                else:
                    record[param_code] = None
            
            records.append(record)
        
        return records


def download_location_climate_data(
    latitude: float,
    longitude: float,
    start_year: int = 2010,
    end_year: int = 2023,
    force: bool = False
) -> Path:
    """
    Download climate data for a specific location.
    
    Args:
        latitude: Latitude
        longitude: Longitude
        start_year: Start year
        end_year: End year
        force: Re-download even if cached
        
    Returns:
        Path to the downloaded data file
    """
    client = NASAPowerClient()
    
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    
    cache_file = client.cache_dir / f"location_{latitude}_{longitude}_{start_year}_{end_year}.json"
    
    if cache_file.exists() and not force:
        logger.info(f"Using cached data from {cache_file}")
        return cache_file
    
    logger.info(f"Downloading NASA POWER data for ({latitude}, {longitude})")
    response = client.get_point_data(latitude, longitude, start_date, end_date)
    
    # Parse into records
    records = client.parse_daily_data(response)
    
    import json
    with open(cache_file, "w") as f:
        json.dump(records, f, indent=2)
    
    logger.info(f"✓ Downloaded {len(records)} daily records to {cache_file}")
    return cache_file


if __name__ == "__main__":
    # Quick test
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("BijMantra NASA POWER Integration Test")
    print("=" * 50)
    
    try:
        client = NASAPowerClient()
        print(f"✓ NASA POWER client initialized")
        print(f"  Cache directory: {client.cache_dir}")
        
        # Test with a sample location (Punjab, India)
        print("\nFetching sample data for Punjab, India (30.9°N, 75.8°E)...")
        print("  Date range: 2023-01-01 to 2023-01-07 (7 days)")
        
        data = client.get_point_data(
            latitude=30.9,
            longitude=75.8,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 7),
            parameters=["T2M", "PRECTOTCORR", "RH2M"]
        )
        
        records = client.parse_daily_data(data)
        print(f"✓ Fetched {len(records)} daily records")
        
        if records:
            print(f"\nSample record (2023-01-01):")
            print(f"  Temperature: {records[0].get('T2M')}°C")
            print(f"  Precipitation: {records[0].get('PRECTOTCORR')} mm/day")
            print(f"  Humidity: {records[0].get('RH2M')}%")
        
        print("\n✓ NASA POWER integration is ready to use")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

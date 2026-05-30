"""
FAOSTAT API integration for BijMantra.

Downloads global agricultural production, yield, and trade data from the
UN Food and Agriculture Organization's statistical database.

All downloads go DIRECTLY to /Volumes/hfs/faostat-data/ with NO intermediate
caching on the primary macOS drive.

API Documentation: https://www.fao.org/faostat/en/#data
Data Coverage: 245 countries, 200+ crops, 1961-present
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Import download configuration to ensure external drive usage
from app.integrations.download_config import get_data_dir, get_temp_dir

# FAOSTAT API endpoints
FAOSTAT_API_BASE = "https://fenixservices.fao.org/faostat/api/v1/en"
FAOSTAT_BULK_BASE = "https://fenixservices.fao.org/faostat/static/bulkdownloads"

# Common domain codes
DOMAINS = {
    "QCL": "Crops and livestock products",  # Production data
    "QV": "Value of Agricultural Production",
    "QI": "Production Indices",
    "RL": "Land Use",
    "RY": "Yield",
    "TP": "Trade - Crops and livestock products",
    "TM": "Trade - Detailed trade matrix",
    "PP": "Producer Prices",
    "CP": "Consumer Prices",
}


class FAOSTATClient:
    """
    Client for downloading FAOSTAT agricultural data.
    
    Usage:
        client = FAOSTATClient()
        data = client.get_production_data(
            countries=["India", "United States"],
            crops=["Wheat", "Rice"],
            years=range(2010, 2021)
        )
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize FAOSTAT client.
        
        Args:
            cache_dir: Directory to cache downloaded data.
                      Defaults to /Volumes/hfs/faostat-data/
        """
        self.cache_dir = cache_dir or get_data_dir("faostat")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BijMantra/1.0 (Agricultural Research Platform)"
        })
        
    def get_dimensions(self, domain: str = "QCL") -> Dict[str, Any]:
        """
        Get available dimensions (countries, crops, years) for a domain.
        
        Args:
            domain: FAOSTAT domain code (default: QCL for production)
            
        Returns:
            Dictionary with available dimensions
        """
        url = f"{FAOSTAT_API_BASE}/dimensions/{domain}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get dimensions for {domain}: {e}")
            raise
    
    def get_production_data(
        self,
        countries: Optional[List[str]] = None,
        crops: Optional[List[str]] = None,
        years: Optional[range] = None,
        elements: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get crop production data from FAOSTAT.
        
        Args:
            countries: List of country names (default: all)
            crops: List of crop names (default: all)
            years: Range of years (default: 2010-2023)
            elements: Data elements to fetch (default: ["Production", "Yield", "Area harvested"])
            
        Returns:
            List of production records
        """
        if years is None:
            years = range(2010, 2024)
        
        if elements is None:
            elements = ["Production", "Yield", "Area harvested"]
        
        # Use bulk download for large queries
        return self._bulk_download("QCL", countries, crops, years, elements)
    
    def get_trade_data(
        self,
        countries: Optional[List[str]] = None,
        crops: Optional[List[str]] = None,
        years: Optional[range] = None
    ) -> List[Dict[str, Any]]:
        """
        Get crop trade data (imports/exports) from FAOSTAT.
        
        Args:
            countries: List of country names
            crops: List of crop names
            years: Range of years
            
        Returns:
            List of trade records
        """
        if years is None:
            years = range(2010, 2024)
        
        return self._bulk_download("TP", countries, crops, years, ["Import Quantity", "Export Quantity"])
    
    def get_price_data(
        self,
        countries: Optional[List[str]] = None,
        crops: Optional[List[str]] = None,
        years: Optional[range] = None
    ) -> List[Dict[str, Any]]:
        """
        Get producer price data from FAOSTAT.
        
        Args:
            countries: List of country names
            crops: List of crop names
            years: Range of years
            
        Returns:
            List of price records
        """
        if years is None:
            years = range(2010, 2024)
        
        return self._bulk_download("PP", countries, crops, years, ["Producer Price"])
    
    def _bulk_download(
        self,
        domain: str,
        countries: Optional[List[str]],
        crops: Optional[List[str]],
        years: range,
        elements: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Download data using FAOSTAT bulk download API.
        
        This is more efficient than the query API for large datasets.
        """
        # Check cache first
        cache_key = f"{domain}_{min(years)}_{max(years)}"
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            logger.info(f"Using cached data from {cache_file}")
            import json
            with open(cache_file) as f:
                data = json.load(f)
        else:
            # Download bulk file
            url = f"{FAOSTAT_BULK_BASE}/{domain}_E_All_Data_(Normalized).zip"
            logger.info(f"Downloading bulk data from {url}")
            
            try:
                response = self.session.get(url, timeout=300, stream=True)
                response.raise_for_status()
                
                # Save and extract ZIP
                zip_path = self.cache_dir / f"{domain}.zip"
                with open(zip_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Downloaded {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
                
                # Extract CSV
                import zipfile
                import csv
                
                with zipfile.ZipFile(zip_path) as zf:
                    csv_name = [n for n in zf.namelist() if n.endswith(".csv")][0]
                    with zf.open(csv_name) as csv_file:
                        # Parse CSV
                        import io
                        text_file = io.TextIOWrapper(csv_file, encoding="utf-8")
                        reader = csv.DictReader(text_file)
                        data = list(reader)
                
                # Cache the parsed data
                import json
                with open(cache_file, "w") as f:
                    json.dump(data, f)
                
                logger.info(f"Cached {len(data)} records to {cache_file}")
                
            except Exception as e:
                logger.error(f"Failed to download bulk data: {e}")
                raise
        
        # Filter data
        filtered = data
        
        if countries:
            country_set = set(c.lower() for c in countries)
            filtered = [r for r in filtered if r.get("Area", "").lower() in country_set]
        
        if crops:
            crop_set = set(c.lower() for c in crops)
            filtered = [r for r in filtered if r.get("Item", "").lower() in crop_set]
        
        if years:
            year_set = set(str(y) for y in years)
            filtered = [r for r in filtered if r.get("Year") in year_set]
        
        if elements:
            element_set = set(e.lower() for e in elements)
            filtered = [r for r in filtered if r.get("Element", "").lower() in element_set]
        
        logger.info(f"Filtered to {len(filtered)} records")
        return filtered
    
    def get_crop_list(self) -> List[Dict[str, str]]:
        """
        Get list of all crops available in FAOSTAT.
        
        Returns:
            List of crop dictionaries with code and name
        """
        url = f"{FAOSTAT_API_BASE}/codes/items/QCL"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            logger.error(f"Failed to get crop list: {e}")
            raise
    
    def get_country_list(self) -> List[Dict[str, str]]:
        """
        Get list of all countries available in FAOSTAT.
        
        Returns:
            List of country dictionaries with code and name
        """
        url = f"{FAOSTAT_API_BASE}/codes/areas"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            logger.error(f"Failed to get country list: {e}")
            raise


def download_global_production_data(
    years: Optional[range] = None,
    force: bool = False
) -> Path:
    """
    Download global crop production data from FAOSTAT.
    
    Args:
        years: Range of years to download (default: 2010-2023)
        force: Re-download even if cached
        
    Returns:
        Path to the downloaded data file
    """
    client = FAOSTATClient()
    
    if years is None:
        years = range(2010, 2024)
    
    cache_file = client.cache_dir / f"production_{min(years)}_{max(years)}.json"
    
    if cache_file.exists() and not force:
        logger.info(f"Using cached data from {cache_file}")
        return cache_file
    
    logger.info(f"Downloading FAOSTAT production data for {min(years)}-{max(years)}")
    data = client.get_production_data(years=years)
    
    import json
    with open(cache_file, "w") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"✓ Downloaded {len(data)} records to {cache_file}")
    return cache_file


if __name__ == "__main__":
    # Quick test
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("BijMantra FAOSTAT Integration Test")
    print("=" * 50)
    
    try:
        client = FAOSTATClient()
        print(f"✓ FAOSTAT client initialized")
        print(f"  Cache directory: {client.cache_dir}")
        
        # Get crop list
        print("\nFetching crop list...")
        crops = client.get_crop_list()
        print(f"✓ Found {len(crops)} crops")
        print(f"  Sample crops: {', '.join(c['label'] for c in crops[:5])}")
        
        # Get country list
        print("\nFetching country list...")
        countries = client.get_country_list()
        print(f"✓ Found {len(countries)} countries")
        
        print("\n✓ FAOSTAT integration is ready to use")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""
Public data source fetchers for BijMantra data pipeline.

These fetchers download datasets from government agencies, research institutions,
and scientific publications. All downloads go to /Volumes/hfs/ to preserve disk space.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from data_pipeline.fetchers.base import BaseFetcher, FetchResult


class FAOSTATProductionFetcher(BaseFetcher):
    """
    Fetches global crop production data from FAOSTAT (UN FAO).
    
    Source: https://www.fao.org/faostat/en/#data/QCL
    Data: Global agricultural production, yield, area harvested
    Coverage:
    - 245 countries/territories
    - 200+ crops
    - 1961-present (60+ years)
    - Production, yield, area, trade, prices
    
    Size: ~5 GB (full dataset)
    Format: CSV via API
    License: CC BY-NC-SA 3.0 IGO
    Quality: ⭐⭐⭐⭐⭐ (official UN data)
    """
    
    source_name = "faostat_production"
    
    async def fetch(self, force_fetch: bool = False, **params: Any) -> FetchResult:
        """
        Download and parse FAOSTAT production data.
        
        Parameters:
            start_year: Start year (default: 2010)
            end_year: End year (default: 2023)
            countries: List of country names (default: all)
            crops: List of crop names (default: all)
        """
        cached = self._cache_result("faostat_production", force_fetch=force_fetch)
        if cached:
            return cached
        
        try:
            # Import here to avoid requiring faostat for other fetchers
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
            from app.integrations.faostat_client import FAOSTATClient
            
            # Get parameters
            start_year = params.get("start_year", 2010)
            end_year = params.get("end_year", 2023)
            countries = params.get("countries")
            crops = params.get("crops")
            
            # Download the dataset
            client = FAOSTATClient()
            data = client.get_production_data(
                countries=countries,
                crops=crops,
                years=range(start_year, end_year + 1)
            )
            
            # Transform to pipeline format
            payload = []
            for row in data:
                try:
                    # FAOSTAT columns: Area, Item, Element, Year, Value, Unit
                    element = row.get("Element", "")
                    
                    # Only process production, yield, and area data
                    if element not in ["Production", "Yield", "Area harvested"]:
                        continue
                    
                    value = row.get("Value")
                    if not value or value == "":
                        continue
                    
                    payload.append({
                        "country": row.get("Area", ""),
                        "crop": row.get("Item", ""),
                        "year": int(row.get("Year", 0)),
                        "element": element,
                        "value": float(value),
                        "unit": row.get("Unit", ""),
                        "source": "faostat_production",
                    })
                except (ValueError, TypeError):
                    # Skip malformed rows
                    continue
            
            return self._write_payload(
                "faostat_production",
                payload,
                {
                    "start_year": start_year,
                    "end_year": end_year,
                    "record_count": len(payload),
                }
            )
            
        except Exception as exc:
            return self._write_error("faostat_production", exc)


class NASAPowerClimateFetcher(BaseFetcher):
    """
    Fetches global climate data from NASA POWER (Agroclimatology).
    
    Source: https://power.larc.nasa.gov/
    Data: Global climate data for agriculture
    Coverage:
    - Global coverage (0.5° × 0.5° resolution)
    - 1981-present (40+ years)
    - Temperature, rainfall, solar radiation, humidity, wind
    - Daily, monthly, annual data
    
    Size: 100+ GB (full archive)
    Format: JSON (API)
    License: Public domain (NASA)
    Quality: ⭐⭐⭐⭐⭐ (satellite-derived)
    """
    
    source_name = "nasa_power_climate"
    
    async def fetch(self, force_fetch: bool = False, **params: Any) -> FetchResult:
        """
        Download and parse NASA POWER climate data.
        
        Parameters:
            locations: List of (latitude, longitude) tuples (required)
            start_year: Start year (default: 2010)
            end_year: End year (default: 2023)
            parameters: List of parameter codes (default: T2M, PRECTOTCORR, RH2M)
        """
        cached = self._cache_result("nasa_power_climate", force_fetch=force_fetch)
        if cached:
            return cached
        
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
            from app.integrations.nasa_power_client import NASAPowerClient
            
            # Get parameters
            locations = params.get("locations")
            if not locations:
                raise ValueError("locations parameter is required (list of (lat, lon) tuples)")
            
            start_year = params.get("start_year", 2010)
            end_year = params.get("end_year", 2023)
            parameters = params.get("parameters", ["T2M", "PRECTOTCORR", "RH2M"])
            
            # Download data for each location
            client = NASAPowerClient()
            payload = []
            
            for lat, lon in locations:
                try:
                    data = client.get_point_data(
                        latitude=lat,
                        longitude=lon,
                        start_date=date(start_year, 1, 1),
                        end_date=date(end_year, 12, 31),
                        parameters=parameters
                    )
                    
                    # Parse daily records
                    records = client.parse_daily_data(data)
                    
                    # Add location info
                    for record in records:
                        record["latitude"] = lat
                        record["longitude"] = lon
                        record["source"] = "nasa_power_climate"
                        payload.append(record)
                    
                except Exception as e:
                    # Log error but continue with other locations
                    import logging
                    logging.error(f"Failed to fetch data for ({lat}, {lon}): {e}")
                    continue
            
            return self._write_payload(
                "nasa_power_climate",
                payload,
                {
                    "locations": len(locations),
                    "start_year": start_year,
                    "end_year": end_year,
                    "record_count": len(payload),
                }
            )
            
        except Exception as exc:
            return self._write_error("nasa_power_climate", exc)


class USDANASSFetcher(BaseFetcher):
    """
    Fetches US agricultural statistics from USDA NASS Quick Stats.
    
    Source: https://www.nass.usda.gov/Data_and_Statistics/
    Data: Comprehensive US agricultural statistics
    Coverage:
    - All US states and counties
    - 100+ crops
    - 1866-present (150+ years)
    - Yield, production, area, prices, costs
    
    Size: 10+ GB
    Format: CSV, API
    License: Public domain (US government)
    Quality: ⭐⭐⭐⭐⭐ (official USDA data)
    
    Note: Requires USDA NASS API key (free registration)
    """
    
    source_name = "usda_nass"
    
    async def fetch(self, force_fetch: bool = False, **params: Any) -> FetchResult:
        """
        Download and parse USDA NASS data.
        
        Parameters:
            api_key: USDA NASS API key (required)
            start_year: Start year (default: 2010)
            end_year: End year (default: 2023)
            states: List of state names (default: all)
            crops: List of crop names (default: major crops)
        """
        cached = self._cache_result("usda_nass", force_fetch=force_fetch)
        if cached:
            return cached
        
        try:
            import requests
            
            # Get parameters
            api_key = params.get("api_key")
            if not api_key:
                raise ValueError("api_key parameter is required (get from https://quickstats.nass.usda.gov/api)")
            
            start_year = params.get("start_year", 2010)
            end_year = params.get("end_year", 2023)
            states = params.get("states")
            crops = params.get("crops", ["CORN", "WHEAT", "SOYBEANS", "RICE"])
            
            # Build API request
            base_url = "https://quickstats.nass.usda.gov/api/api_GET/"
            
            payload = []
            
            for crop in crops:
                for year in range(start_year, end_year + 1):
                    try:
                        params_dict = {
                            "key": api_key,
                            "commodity_desc": crop,
                            "year": year,
                            "statisticcat_desc": "YIELD",
                            "format": "JSON"
                        }
                        
                        if states:
                            params_dict["state_name"] = ",".join(states)
                        
                        response = requests.get(base_url, params=params_dict, timeout=60)
                        response.raise_for_status()
                        data = response.json()
                        
                        # Parse records
                        for record in data.get("data", []):
                            payload.append({
                                "state": record.get("state_name", ""),
                                "county": record.get("county_name", ""),
                                "crop": record.get("commodity_desc", ""),
                                "year": int(record.get("year", 0)),
                                "value": float(record.get("Value", 0)) if record.get("Value") else None,
                                "unit": record.get("unit_desc", ""),
                                "source": "usda_nass",
                            })
                        
                    except Exception as e:
                        import logging
                        logging.error(f"Failed to fetch {crop} {year}: {e}")
                        continue
            
            return self._write_payload(
                "usda_nass",
                payload,
                {
                    "start_year": start_year,
                    "end_year": end_year,
                    "crops": len(crops),
                    "record_count": len(payload),
                }
            )
            
        except Exception as exc:
            return self._write_error("usda_nass", exc)


# Register public source fetchers
PUBLIC_SOURCE_FETCHER_REGISTRY = {
    "faostat_production": FAOSTATProductionFetcher,
    "nasa_power_climate": NASAPowerClimateFetcher,
    "usda_nass": USDANASSFetcher,
}

# Also export as FETCHER_REGISTRY for compatibility with data pipeline
FETCHER_REGISTRY = PUBLIC_SOURCE_FETCHER_REGISTRY

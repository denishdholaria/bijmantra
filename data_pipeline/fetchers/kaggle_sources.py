"""
Kaggle data source fetchers for BijMantra data pipeline.

These fetchers download datasets from Kaggle and transform them into
the pipeline's expected format. All downloads go to /Volumes/hfs/kaggle-data/
to preserve local disk space.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from data_pipeline.fetchers.base import BaseFetcher, FetchResult


class KaggleCropYieldFetcher(BaseFetcher):
    """
    Fetches crop yield data from Kaggle.
    
    Replaces the broken FAOSTAT source with real historical yield data
    from the "Crop Yield Prediction Dataset" on Kaggle.
    
    Dataset: patelris/crop-yield-prediction-dataset
    Size: ~10 MB
    Format: CSV with columns: Country, Crop, Year, Yield (tons/hectare)
    """
    
    source_name = "kaggle_crop_yield"
    
    async def fetch(self, force_fetch: bool = False, **params: Any) -> FetchResult:
        """
        Download and parse the Kaggle crop yield dataset.
        
        This is a synchronous operation wrapped in async for consistency
        with other fetchers. The actual download happens via kagglehub.
        """
        cached = self._cache_result("kaggle_crop_yield", force_fetch=force_fetch)
        if cached:
            return cached
        
        try:
            # Import here to avoid requiring kaggle for other fetchers
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
            from app.integrations.kaggle_client import download_crop_yield_dataset
            
            # Download the dataset (goes to /Volumes/hfs/kaggle-data/)
            dataset_path = download_crop_yield_dataset(force=force_fetch)
            
            # Find the yield_df.csv file specifically (not the other CSVs)
            csv_path = dataset_path / "yield_df.csv"
            if not csv_path.exists():
                # Fallback to any CSV if yield_df.csv doesn't exist
                csv_files = list(dataset_path.glob("*.csv"))
                if not csv_files:
                    raise FileNotFoundError(f"No CSV files found in {dataset_path}")
                csv_path = csv_files[0]
            
            # Parse CSV into pipeline format
            payload = []
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Transform to pipeline format
                    # yield_df.csv columns: Area, Item, Year, hg/ha_yield, average_rain_fall_mm_per_year, pesticides_tonnes, avg_temp
                    try:
                        yield_hg_ha = float(row.get("hg/ha_yield", 0))
                        # Convert hectograms/hectare to tonnes/hectare (1 tonne = 10,000 hg)
                        yield_tonnes = yield_hg_ha / 10000.0 if yield_hg_ha else 0.0
                        
                        payload.append({
                            "country": row.get("Area", ""),
                            "crop": row.get("Item", ""),
                            "year": int(row.get("Year", 0)) if row.get("Year") else 0,
                            "yield_tonnes_per_hectare": yield_tonnes,
                            "rainfall_mm": float(row.get("average_rain_fall_mm_per_year", 0)) if row.get("average_rain_fall_mm_per_year") else None,
                            "pesticides_tonnes": float(row.get("pesticides_tonnes", 0)) if row.get("pesticides_tonnes") else None,
                            "avg_temp_celsius": float(row.get("avg_temp", 0)) if row.get("avg_temp") else None,
                            "source": "kaggle_crop_yield",
                        })
                    except (ValueError, TypeError) as e:
                        # Skip malformed rows
                        continue
            
            return self._write_payload(
                "kaggle_crop_yield",
                payload,
                {
                    "dataset_path": str(dataset_path),
                    "csv_file": csv_path.name,
                    "record_count": len(payload),
                }
            )
            
        except Exception as exc:
            return self._write_error("kaggle_crop_yield", exc)


class KaggleCropRecommendationFetcher(BaseFetcher):
    """
    Fetches crop recommendation training data from Kaggle.
    
    Dataset: atharvaingle/crop-recommendation-dataset
    Size: ~1 MB
    Format: CSV with soil parameters + weather → crop label
    
    Columns: N, P, K, temperature, humidity, ph, rainfall, label (crop name)
    """
    
    source_name = "kaggle_crop_recommendation"
    
    async def fetch(self, force_fetch: bool = False, **params: Any) -> FetchResult:
        cached = self._cache_result("kaggle_crop_recommendation", force_fetch=force_fetch)
        if cached:
            return cached
        
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
            from app.integrations.kaggle_client import download_crop_recommendation_dataset
            
            dataset_path = download_crop_recommendation_dataset(force=force_fetch)
            
            csv_files = list(dataset_path.glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError(f"No CSV files found in {dataset_path}")
            
            csv_path = csv_files[0]
            
            payload = []
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    payload.append({
                        "nitrogen": float(row.get("N", 0)),
                        "phosphorus": float(row.get("P", 0)),
                        "potassium": float(row.get("K", 0)),
                        "temperature": float(row.get("temperature", 0)),
                        "humidity": float(row.get("humidity", 0)),
                        "ph": float(row.get("ph", 0)),
                        "rainfall": float(row.get("rainfall", 0)),
                        "recommended_crop": row.get("label", ""),
                        "source": "kaggle_crop_recommendation",
                    })
            
            return self._write_payload(
                "kaggle_crop_recommendation",
                payload,
                {
                    "dataset_path": str(dataset_path),
                    "csv_file": csv_path.name,
                    "record_count": len(payload),
                }
            )
            
        except Exception as exc:
            return self._write_error("kaggle_crop_recommendation", exc)


class KagglePlantDiseaseMetadataFetcher(BaseFetcher):
    """
    Fetches metadata about the plant disease image dataset.
    
    Does NOT download the images (3-5 GB) — just catalogs what's available.
    The actual images are used by Plant Vision training, not the data pipeline.
    
    Dataset: vipoooool/new-plant-diseases-dataset
    Size: 87,900 images (~3-5 GB)
    """
    
    source_name = "kaggle_plant_disease_metadata"
    
    async def fetch(self, force_fetch: bool = False, **params: Any) -> FetchResult:
        cached = self._cache_result("kaggle_plant_disease_metadata", force_fetch=force_fetch)
        if cached:
            return cached
        
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
            from app.integrations.kaggle_client import KaggleClient
            
            client = KaggleClient()
            
            # Get metadata without downloading the full dataset
            info = client.get_dataset_info("vipoooool/new-plant-diseases-dataset")
            
            # Check if already downloaded
            downloaded = client.list_downloaded()
            dataset_exists = any(
                d.name == "new-plant-diseases-dataset" 
                for d in downloaded["datasets"]
            )
            
            payload = {
                "title": info["title"],
                "size_bytes": info["size"],
                "url": info["url"],
                "description": info["description"],
                "downloaded": dataset_exists,
                "local_path": str(client.data_dir / "new-plant-diseases-dataset") if dataset_exists else None,
                "source": "kaggle_plant_disease_metadata",
            }
            
            return self._write_payload(
                "kaggle_plant_disease_metadata",
                payload,
                {"metadata_only": True}
            )
            
        except Exception as exc:
            return self._write_error("kaggle_plant_disease_metadata", exc)


class KaggleFertilizerFetcher(BaseFetcher):
    """
    Fetches fertilizer prediction data from Kaggle.
    
    Dataset: gdabhishek/fertilizer-prediction
    Size: ~500 KB
    Format: CSV with soil type, crop type, N/P/K levels → fertilizer name and amount
    """
    
    source_name = "kaggle_fertilizer"
    
    async def fetch(self, force_fetch: bool = False, **params: Any) -> FetchResult:
        cached = self._cache_result("kaggle_fertilizer", force_fetch=force_fetch)
        if cached:
            return cached
        
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
            from app.integrations.kaggle_client import download_fertilizer_prediction_dataset
            
            dataset_path = download_fertilizer_prediction_dataset(force=force_fetch)
            
            csv_files = list(dataset_path.glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError(f"No CSV files found in {dataset_path}")
            
            csv_path = csv_files[0]
            
            payload = []
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    payload.append({
                        "soil_type": row.get("Soil Type", ""),
                        "crop_type": row.get("Crop Type", ""),
                        "nitrogen": float(row.get("Nitrogen", 0)) if row.get("Nitrogen") else None,
                        "phosphorus": float(row.get("Phosphorous", 0)) if row.get("Phosphorous") else None,
                        "potassium": float(row.get("Potassium", 0)) if row.get("Potassium") else None,
                        "fertilizer_name": row.get("Fertilizer Name", ""),
                        "source": "kaggle_fertilizer",
                    })
            
            return self._write_payload(
                "kaggle_fertilizer",
                payload,
                {
                    "dataset_path": str(dataset_path),
                    "csv_file": csv_path.name,
                    "record_count": len(payload),
                }
            )
            
        except Exception as exc:
            return self._write_error("kaggle_fertilizer", exc)


class KaggleWeatherFetcher(BaseFetcher):
    """
    Fetches daily climate time series data from Kaggle.
    
    Dataset: sumanthvrao/daily-climate-time-series-data
    Size: ~50 MB
    Format: CSV with daily weather data (temperature, humidity, wind, etc.)
    """
    
    source_name = "kaggle_weather"
    
    async def fetch(self, force_fetch: bool = False, **params: Any) -> FetchResult:
        cached = self._cache_result("kaggle_weather", force_fetch=force_fetch)
        if cached:
            return cached
        
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
            from app.integrations.kaggle_client import download_weather_time_series_dataset
            
            dataset_path = download_weather_time_series_dataset(force=force_fetch)
            
            csv_files = list(dataset_path.glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError(f"No CSV files found in {dataset_path}")
            
            csv_path = csv_files[0]
            
            payload = []
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    payload.append({
                        "date": row.get("Date", ""),
                        "mean_temp": float(row.get("meantemp", 0)) if row.get("meantemp") else None,
                        "humidity": float(row.get("humidity", 0)) if row.get("humidity") else None,
                        "wind_speed": float(row.get("wind_speed", 0)) if row.get("wind_speed") else None,
                        "mean_pressure": float(row.get("meanpressure", 0)) if row.get("meanpressure") else None,
                        "source": "kaggle_weather",
                    })
            
            return self._write_payload(
                "kaggle_weather",
                payload,
                {
                    "dataset_path": str(dataset_path),
                    "csv_file": csv_path.name,
                    "record_count": len(payload),
                }
            )
            
        except Exception as exc:
            return self._write_error("kaggle_weather", exc)


class KaggleIndianAgricultureFetcher(BaseFetcher):
    """
    Fetches Indian agriculture crop production data from Kaggle.
    
    Dataset: abhinand05/crop-production-in-india
    Size: ~2 MB
    Format: CSV with state-level crop production data (1997-2015)
    """
    
    source_name = "kaggle_indian_agriculture"
    
    async def fetch(self, force_fetch: bool = False, **params: Any) -> FetchResult:
        cached = self._cache_result("kaggle_indian_agriculture", force_fetch=force_fetch)
        if cached:
            return cached
        
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
            from app.integrations.kaggle_client import download_indian_agriculture_dataset
            
            dataset_path = download_indian_agriculture_dataset(force=force_fetch)
            
            csv_files = list(dataset_path.glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError(f"No CSV files found in {dataset_path}")
            
            csv_path = csv_files[0]
            
            payload = []
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    payload.append({
                        "state": row.get("State_Name", ""),
                        "district": row.get("District_Name", ""),
                        "crop_year": row.get("Crop_Year", ""),
                        "season": row.get("Season", ""),
                        "crop": row.get("Crop", ""),
                        "area": float(row.get("Area", 0)) if row.get("Area") else None,
                        "production": float(row.get("Production", 0)) if row.get("Production") else None,
                        "source": "kaggle_indian_agriculture",
                    })
            
            return self._write_payload(
                "kaggle_indian_agriculture",
                payload,
                {
                    "dataset_path": str(dataset_path),
                    "csv_file": csv_path.name,
                    "record_count": len(payload),
                }
            )
            
        except Exception as exc:
            return self._write_error("kaggle_indian_agriculture", exc)


# Register Kaggle fetchers
KAGGLE_FETCHER_REGISTRY = {
    "kaggle_crop_yield": KaggleCropYieldFetcher,
    "kaggle_crop_recommendation": KaggleCropRecommendationFetcher,
    "kaggle_plant_disease_metadata": KagglePlantDiseaseMetadataFetcher,
    "kaggle_fertilizer": KaggleFertilizerFetcher,
    "kaggle_weather": KaggleWeatherFetcher,
    "kaggle_indian_agriculture": KaggleIndianAgricultureFetcher,
}

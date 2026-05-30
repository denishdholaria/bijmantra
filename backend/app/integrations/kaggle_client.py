"""
Kaggle integration for BijMantra.

Downloads datasets and models from Kaggle to the configured data directory.
All downloads go DIRECTLY to /Volumes/hfs/kaggle-data/ with NO intermediate
caching on the primary macOS drive.
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Import download configuration to ensure external drive usage
from app.integrations.download_config import get_data_dir, configure_kagglehub_cache

# Default data directory on the large external drive
DEFAULT_KAGGLE_DATA_DIR = Path("/Volumes/hfs/kaggle-data")


class KaggleClient:
    """
    Client for downloading Kaggle datasets and models.
    
    Usage:
        client = KaggleClient()
        path = client.download_dataset("vipoooool/new-plant-diseases-dataset")
        print(f"Dataset downloaded to: {path}")
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize Kaggle client.
        
        Args:
            data_dir: Directory to store downloaded data. 
                     Defaults to /Volumes/hfs/kaggle-data/
        """
        # Configure kagglehub to cache on external drive (NOT primary drive)
        configure_kagglehub_cache()
        
        self.data_dir = data_dir or get_data_dir("kaggle")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify Kaggle credentials are available
        self._verify_credentials()
        
    def _verify_credentials(self) -> None:
        """Check if Kaggle credentials are configured."""
        kaggle_dir = Path.home() / ".kaggle"
        
        # Check for either kaggle.json or access_token
        has_json = (kaggle_dir / "kaggle.json").exists()
        has_token = (kaggle_dir / "access_token").exists()
        
        if not (has_json or has_token):
            raise RuntimeError(
                "Kaggle credentials not found. Please set up ~/.kaggle/kaggle.json "
                "or ~/.kaggle/access_token. See: https://www.kaggle.com/docs/api"
            )
        
        logger.info(f"✓ Kaggle credentials found in {kaggle_dir}")
    
    def download_dataset(
        self, 
        dataset_slug: str, 
        force: bool = False,
        unzip: bool = True
    ) -> Path:
        """
        Download a Kaggle dataset.
        
        Args:
            dataset_slug: Dataset identifier (e.g., "vipoooool/new-plant-diseases-dataset")
            force: Re-download even if already exists
            unzip: Automatically unzip downloaded files
            
        Returns:
            Path to the downloaded dataset directory
            
        Example:
            >>> client = KaggleClient()
            >>> path = client.download_dataset("vipoooool/new-plant-diseases-dataset")
            >>> print(path)
            /Volumes/hfs/kaggle-data/new-plant-diseases-dataset
        """
        import kagglehub
        
        # Extract dataset name from slug
        dataset_name = dataset_slug.split("/")[-1]
        target_dir = self.data_dir / dataset_name
        
        # Check if already downloaded
        if target_dir.exists() and not force:
            logger.info(f"Dataset already exists at {target_dir} (use force=True to re-download)")
            return target_dir
        
        logger.info(f"Downloading Kaggle dataset: {dataset_slug}")
        logger.info(f"Target directory: {target_dir}")
        
        try:
            # kagglehub downloads to its own cache first
            cache_path = kagglehub.dataset_download(dataset_slug)
            cache_path = Path(cache_path)
            
            logger.info(f"Downloaded to cache: {cache_path}")
            
            # Create symlink to our data directory for easy access
            if not target_dir.exists():
                target_dir.symlink_to(cache_path)
                logger.info(f"✓ Dataset linked to: {target_dir}")
            
            return target_dir
            
        except Exception as e:
            logger.error(f"Failed to download dataset {dataset_slug}: {e}")
            raise
    
    def download_model(
        self,
        model_slug: str,
        force: bool = False
    ) -> Path:
        """
        Download a pre-trained model from Kaggle.
        
        Args:
            model_slug: Model identifier (e.g., "google/mobilenet-v2/frameworks/tfLite")
            force: Re-download even if already exists
            
        Returns:
            Path to the downloaded model directory
            
        Example:
            >>> client = KaggleClient()
            >>> path = client.download_model("tensorflow/efficientnet/frameworks/tfLite")
            >>> print(path)
            /Volumes/hfs/kaggle-data/models/efficientnet
        """
        import kagglehub
        
        # Extract model name from slug
        model_name = model_slug.split("/")[1]  # e.g., "mobilenet-v2"
        models_dir = self.data_dir / "models"
        models_dir.mkdir(exist_ok=True)
        target_dir = models_dir / model_name
        
        # Check if already downloaded
        if target_dir.exists() and not force:
            logger.info(f"Model already exists at {target_dir} (use force=True to re-download)")
            return target_dir
        
        logger.info(f"Downloading Kaggle model: {model_slug}")
        logger.info(f"Target directory: {target_dir}")
        
        try:
            # kagglehub downloads to its own cache first
            cache_path = kagglehub.model_download(model_slug)
            cache_path = Path(cache_path)
            
            logger.info(f"Downloaded to cache: {cache_path}")
            
            # Create symlink to our data directory
            if not target_dir.exists():
                target_dir.symlink_to(cache_path)
                logger.info(f"✓ Model linked to: {target_dir}")
            
            return target_dir
            
        except Exception as e:
            logger.error(f"Failed to download model {model_slug}: {e}")
            raise
    
    def list_downloaded(self) -> dict[str, list[Path]]:
        """
        List all downloaded datasets and models.
        
        Returns:
            Dictionary with 'datasets' and 'models' keys, each containing a list of Paths
        """
        datasets = []
        models = []
        
        # List datasets (direct children of data_dir)
        if self.data_dir.exists():
            for item in self.data_dir.iterdir():
                if item.is_dir() and item.name != "models":
                    datasets.append(item)
        
        # List models
        models_dir = self.data_dir / "models"
        if models_dir.exists():
            models = [item for item in models_dir.iterdir() if item.is_dir()]
        
        return {
            "datasets": sorted(datasets),
            "models": sorted(models)
        }
    
    def get_dataset_info(self, dataset_slug: str) -> dict:
        """
        Get metadata about a Kaggle dataset without downloading it.
        
        Args:
            dataset_slug: Dataset identifier
            
        Returns:
            Dictionary with dataset metadata (title, size, files, etc.)
        """
        from kaggle.api.kaggle_api_extended import KaggleApi
        
        api = KaggleApi()
        api.authenticate()
        
        owner, dataset_name = dataset_slug.split("/")
        dataset = api.dataset_view(owner, dataset_name)
        
        return {
            "title": dataset.title,
            "size": dataset.totalBytes,
            "url": dataset.url,
            "description": dataset.description,
            "files": dataset.files if hasattr(dataset, 'files') else []
        }


# Convenience functions for common BijMantra use cases

def download_plant_disease_dataset(force: bool = False) -> Path:
    """
    Download the standard plant disease image dataset.
    
    This is the "New Plant Diseases Dataset" with 87,900 images
    across 38 disease classes covering 14 crop species.
    
    Returns:
        Path to the dataset directory
    """
    client = KaggleClient()
    return client.download_dataset("vipoooool/new-plant-diseases-dataset", force=force)


def download_crop_yield_dataset(force: bool = False) -> Path:
    """
    Download crop yield prediction dataset.
    
    Contains historical yield data by country, crop, and year.
    Can replace the broken FAOSTAT source in the data pipeline.
    
    Returns:
        Path to the dataset directory
    """
    client = KaggleClient()
    return client.download_dataset("patelris/crop-yield-prediction-dataset", force=force)


def download_crop_recommendation_dataset(force: bool = False) -> Path:
    """
    Download crop recommendation dataset.
    
    Contains soil parameters (N, P, K, pH) + weather → crop recommendations.
    Useful for training REEVU's recommendation models.
    
    Returns:
        Path to the dataset directory
    """
    client = KaggleClient()
    return client.download_dataset("atharvaingle/crop-recommendation-dataset", force=force)


def download_fertilizer_prediction_dataset(force: bool = False) -> Path:
    """
    Download fertilizer prediction dataset.
    
    Contains soil type, crop type, N/P/K levels → fertilizer name and amount.
    Enables REEVU to recommend specific fertilizer quantities.
    
    Returns:
        Path to the dataset directory
    """
    client = KaggleClient()
    return client.download_dataset("gdabhishek/fertilizer-prediction", force=force)


def download_weather_time_series_dataset(force: bool = False) -> Path:
    """
    Download daily climate time series dataset.
    
    Contains 10+ years of daily weather data (temperature, humidity, wind, etc.).
    Useful for weather-yield correlation models.
    
    Returns:
        Path to the dataset directory
    """
    client = KaggleClient()
    return client.download_dataset("sumanthvrao/daily-climate-time-series-data", force=force)


def download_rice_disease_dataset(force: bool = False) -> Path:
    """
    Download rice disease image dataset.
    
    Contains ~10,000 rice disease images for training Plant Vision.
    
    Returns:
        Path to the dataset directory
    """
    client = KaggleClient()
    return client.download_dataset("minhhuy2810/rice-diseases-image-dataset", force=force)


def download_wheat_disease_dataset(force: bool = False) -> Path:
    """
    Download wheat leaf disease dataset.
    
    Contains ~5,000 wheat leaf images for training Plant Vision.
    
    Returns:
        Path to the dataset directory
    """
    client = KaggleClient()
    return client.download_dataset("olyadgetch/wheat-leaf-dataset", force=force)


def download_indian_agriculture_dataset(force: bool = False) -> Path:
    """
    Download Indian agriculture crop production dataset.
    
    Contains ~250,000 crop production records for India (1997-2015).
    State-level granularity for regional yield modeling.
    
    Returns:
        Path to the dataset directory
    """
    client = KaggleClient()
    return client.download_dataset("abhinand05/crop-production-in-india", force=force)


if __name__ == "__main__":
    # Quick test
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("BijMantra Kaggle Integration Test")
    print("=" * 50)
    
    try:
        client = KaggleClient()
        print(f"✓ Kaggle client initialized")
        print(f"  Data directory: {client.data_dir}")
        
        # List what's already downloaded
        downloaded = client.list_downloaded()
        print(f"\nCurrently downloaded:")
        print(f"  Datasets: {len(downloaded['datasets'])}")
        for ds in downloaded['datasets']:
            print(f"    - {ds.name}")
        print(f"  Models: {len(downloaded['models'])}")
        for model in downloaded['models']:
            print(f"    - {model.name}")
        
        print("\n✓ Kaggle integration is ready to use")
        print("\nTo download a dataset:")
        print("  python -m app.integrations.kaggle_client")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

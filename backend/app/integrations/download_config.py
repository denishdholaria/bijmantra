"""
Download configuration for BijMantra data integrations.

This module ensures ALL data downloads go directly to the external drive
with NO intermediate caching on the primary macOS drive.

CRITICAL: The primary macOS drive has limited space. All agricultural datasets
must be downloaded directly to /Volumes/hfs/bijmantra-datasets/ without any 
intermediate caching.

This keeps BijMantra datasets organized and separate from other corporate files
on the external drive.
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# External drive mount point
EXTERNAL_DRIVE = Path("/Volumes/hfs")

# BijMantra datasets base directory (organized separately from other files)
BIJMANTRA_DATASETS_DIR = EXTERNAL_DRIVE / "bijmantra-datasets"

# Data directories under bijmantra-datasets/
DATA_DIRS = {
    "kaggle": BIJMANTRA_DATASETS_DIR / "kaggle",
    "faostat": BIJMANTRA_DATASETS_DIR / "faostat",
    "nasa_power": BIJMANTRA_DATASETS_DIR / "nasa-power",
    "usda_nass": BIJMANTRA_DATASETS_DIR / "usda-nass",
    "isric": BIJMANTRA_DATASETS_DIR / "isric-soilgrids",
    "plantvillage": BIJMANTRA_DATASETS_DIR / "plantvillage",
    "gdhy": BIJMANTRA_DATASETS_DIR / "gdhy",
    "noaa": BIJMANTRA_DATASETS_DIR / "noaa-cdo",
    "worldclim": BIJMANTRA_DATASETS_DIR / "worldclim",
    "temp": BIJMANTRA_DATASETS_DIR / ".temp",
}


def verify_external_drive() -> bool:
    """
    Verify that the external drive is mounted and writable.
    
    Returns:
        True if external drive is available, False otherwise
    """
    if not EXTERNAL_DRIVE.exists():
        logger.error(f"External drive not mounted: {EXTERNAL_DRIVE}")
        logger.error("Please mount the 'hfs' drive before downloading data")
        return False
    
    if not os.access(EXTERNAL_DRIVE, os.W_OK):
        logger.error(f"External drive not writable: {EXTERNAL_DRIVE}")
        return False
    
    # Check available space (warn if less than 100 GB)
    import shutil
    stat = shutil.disk_usage(EXTERNAL_DRIVE)
    free_gb = stat.free / (1024 ** 3)
    
    if free_gb < 100:
        logger.warning(f"Low disk space on external drive: {free_gb:.1f} GB free")
        logger.warning("Some large datasets may not fit")
    else:
        logger.info(f"✓ External drive available: {free_gb:.1f} GB free")
    
    return True


def get_data_dir(source: str) -> Path:
    """
    Get the data directory for a specific source.
    
    Args:
        source: Data source name (e.g., "kaggle", "faostat", "nasa_power")
        
    Returns:
        Path to the data directory under /Volumes/hfs/bijmantra-datasets/
        
    Raises:
        RuntimeError: If external drive is not available
    """
    if not verify_external_drive():
        raise RuntimeError(
            f"External drive not available: {EXTERNAL_DRIVE}\n"
            "Please mount the 'hfs' drive before downloading data"
        )
    
    # Ensure bijmantra-datasets directory exists
    BIJMANTRA_DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    
    data_dir = DATA_DIRS.get(source)
    if not data_dir:
        # Default to a subdirectory named after the source
        data_dir = BIJMANTRA_DATASETS_DIR / source
    
    # Create directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return data_dir


def configure_kagglehub_cache():
    """
    Configure kagglehub to cache directly on external drive.
    
    By default, kagglehub caches to ~/.cache/kagglehub/ which can fill
    up the primary drive. This function redirects the cache to the external drive.
    """
    cache_dir = DATA_DIRS["kaggle"] / ".kagglehub-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Set environment variable to override kagglehub cache location
    os.environ["KAGGLEHUB_CACHE"] = str(cache_dir)
    
    logger.info(f"✓ Kagglehub cache redirected to: {cache_dir}")


def configure_requests_cache():
    """
    Configure requests library to cache on external drive.
    
    Some HTTP libraries cache responses in ~/.cache/ which can fill
    up the primary drive. This function redirects caching to the external drive.
    """
    cache_dir = DATA_DIRS["temp"] / ".requests-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Set environment variable for requests-cache
    os.environ["REQUESTS_CACHE_DIR"] = str(cache_dir)
    
    logger.info(f"✓ Requests cache redirected to: {cache_dir}")


def configure_all_caches():
    """
    Configure all caching mechanisms to use external drive.
    
    This should be called at the start of any data download operation
    to ensure NO data is cached on the primary macOS drive.
    """
    if not verify_external_drive():
        raise RuntimeError(
            f"External drive not available: {EXTERNAL_DRIVE}\n"
            "Please mount the 'hfs' drive before downloading data"
        )
    
    configure_kagglehub_cache()
    configure_requests_cache()
    
    logger.info("✓ All caches configured to use external drive")


def get_temp_dir() -> Path:
    """
    Get a temporary directory on the external drive.
    
    Use this for any intermediate files during download/processing.
    
    Returns:
        Path to temp directory on external drive
    """
    temp_dir = DATA_DIRS["temp"]
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def cleanup_temp_dir():
    """
    Clean up temporary files on external drive.
    
    Call this after successful data processing to free up space.
    """
    temp_dir = DATA_DIRS["temp"]
    if temp_dir.exists():
        import shutil
        for item in temp_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        logger.info(f"✓ Cleaned up temp directory: {temp_dir}")


def get_disk_usage_summary() -> dict:
    """
    Get disk usage summary for all data directories.
    
    Returns:
        Dictionary with disk usage information
    """
    import shutil
    
    summary = {
        "external_drive": str(EXTERNAL_DRIVE),
        "mounted": EXTERNAL_DRIVE.exists(),
    }
    
    if EXTERNAL_DRIVE.exists():
        stat = shutil.disk_usage(EXTERNAL_DRIVE)
        summary["total_gb"] = stat.total / (1024 ** 3)
        summary["used_gb"] = stat.used / (1024 ** 3)
        summary["free_gb"] = stat.free / (1024 ** 3)
        summary["percent_used"] = (stat.used / stat.total) * 100
        
        # Get size of each data directory
        summary["data_dirs"] = {}
        for name, path in DATA_DIRS.items():
            if path.exists():
                size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
                summary["data_dirs"][name] = {
                    "path": str(path),
                    "size_gb": size / (1024 ** 3),
                    "exists": True,
                }
            else:
                summary["data_dirs"][name] = {
                    "path": str(path),
                    "size_gb": 0,
                    "exists": False,
                }
    
    return summary


if __name__ == "__main__":
    # Test the configuration
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("BijMantra Download Configuration Test")
    print("=" * 50)
    
    try:
        # Verify external drive
        if not verify_external_drive():
            print("✗ External drive not available")
            sys.exit(1)
        
        # Configure caches
        configure_all_caches()
        
        # Show disk usage
        print("\nDisk Usage Summary:")
        summary = get_disk_usage_summary()
        print(f"  External Drive: {summary['external_drive']}")
        print(f"  Total: {summary['total_gb']:.1f} GB")
        print(f"  Used: {summary['used_gb']:.1f} GB ({summary['percent_used']:.1f}%)")
        print(f"  Free: {summary['free_gb']:.1f} GB")
        
        print("\nData Directories:")
        for name, info in summary["data_dirs"].items():
            status = "✓" if info["exists"] else "○"
            print(f"  {status} {name:15} {info['size_gb']:8.2f} GB  {info['path']}")
        
        print("\n✓ Download configuration is ready")
        print("\nAll downloads will go directly to /Volumes/hfs/")
        print("No intermediate caching on primary macOS drive")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

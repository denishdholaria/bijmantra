#!/usr/bin/env python3
"""
Kaggle dataset downloader for BijMantra.

Simple CLI to download datasets and models from Kaggle.
All data goes to /Volumes/hfs/kaggle-data/ to preserve local disk space.

Usage:
    # Download plant disease images
    uv run python scripts/kaggle_download.py plant-diseases
    
    # Download crop yield data
    uv run python scripts/kaggle_download.py crop-yield
    
    # Download crop recommendation data
    uv run python scripts/kaggle_download.py crop-recommendation
    
    # Download any dataset by slug
    uv run python scripts/kaggle_download.py dataset vipoooool/new-plant-diseases-dataset
    
    # List what's downloaded
    uv run python scripts/kaggle_download.py list
"""

import sys
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.integrations.kaggle_client import (
    KaggleClient,
    download_plant_disease_dataset,
    download_crop_yield_dataset,
    download_crop_recommendation_dataset,
    download_fertilizer_prediction_dataset,
    download_weather_time_series_dataset,
    download_rice_disease_dataset,
    download_wheat_disease_dataset,
    download_indian_agriculture_dataset,
)


def main():
    parser = argparse.ArgumentParser(
        description="Download Kaggle datasets for BijMantra",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "command",
        choices=[
            "plant-diseases",
            "crop-yield", 
            "crop-recommendation",
            "fertilizer",
            "weather",
            "rice-diseases",
            "wheat-diseases",
            "indian-agriculture",
            "dataset",
            "model",
            "list",
            "info"
        ],
        help="What to download or query"
    )
    
    parser.add_argument(
        "slug",
        nargs="?",
        help="Dataset or model slug (e.g., 'owner/dataset-name')"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if already exists"
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == "plant-diseases":
            print("Downloading plant disease image dataset...")
            print("This is 87,900 images (~3-5 GB) - will take a few minutes")
            path = download_plant_disease_dataset(force=args.force)
            print(f"\n✓ Downloaded to: {path}")
            print(f"  Use this path in Plant Vision training")
            
        elif args.command == "crop-yield":
            print("Downloading crop yield dataset...")
            path = download_crop_yield_dataset(force=args.force)
            print(f"\n✓ Downloaded to: {path}")
            print(f"  Use this to replace FAOSTAT in data pipeline")
            
        elif args.command == "crop-recommendation":
            print("Downloading crop recommendation dataset...")
            path = download_crop_recommendation_dataset(force=args.force)
            print(f"\n✓ Downloaded to: {path}")
            print(f"  Use this to train REEVU recommendation models")
            
        elif args.command == "fertilizer":
            print("Downloading fertilizer prediction dataset...")
            path = download_fertilizer_prediction_dataset(force=args.force)
            print(f"\n✓ Downloaded to: {path}")
            print(f"  Use this to train REEVU fertilizer recommendation models")
            
        elif args.command == "weather":
            print("Downloading daily climate time series dataset...")
            print("This is 10+ years of daily weather data (~50 MB)")
            path = download_weather_time_series_dataset(force=args.force)
            print(f"\n✓ Downloaded to: {path}")
            print(f"  Use this for weather-yield correlation models")
            
        elif args.command == "rice-diseases":
            print("Downloading rice disease image dataset...")
            print("This is ~10,000 rice disease images (~500 MB)")
            path = download_rice_disease_dataset(force=args.force)
            print(f"\n✓ Downloaded to: {path}")
            print(f"  Use this for Plant Vision rice disease detection")
            
        elif args.command == "wheat-diseases":
            print("Downloading wheat leaf disease dataset...")
            print("This is ~5,000 wheat leaf images (~300 MB)")
            path = download_wheat_disease_dataset(force=args.force)
            print(f"\n✓ Downloaded to: {path}")
            print(f"  Use this for Plant Vision wheat disease detection")
            
        elif args.command == "indian-agriculture":
            print("Downloading Indian agriculture crop production dataset...")
            print("This is ~250,000 records of state-level crop production (1997-2015)")
            path = download_indian_agriculture_dataset(force=args.force)
            print(f"\n✓ Downloaded to: {path}")
            print(f"  Use this for regional yield modeling in India")
            
        elif args.command == "dataset":
            if not args.slug:
                print("Error: dataset command requires a slug")
                print("Example: uv run python scripts/kaggle_download.py dataset owner/dataset-name")
                sys.exit(1)
            
            client = KaggleClient()
            path = client.download_dataset(args.slug, force=args.force)
            print(f"\n✓ Downloaded to: {path}")
            
        elif args.command == "model":
            if not args.slug:
                print("Error: model command requires a slug")
                print("Example: uv run python scripts/kaggle_download.py model google/mobilenet-v2/frameworks/tfLite")
                sys.exit(1)
            
            client = KaggleClient()
            path = client.download_model(args.slug, force=args.force)
            print(f"\n✓ Downloaded to: {path}")
            
        elif args.command == "list":
            client = KaggleClient()
            downloaded = client.list_downloaded()
            
            print(f"\nKaggle data directory: {client.data_dir}")
            print(f"\nDatasets ({len(downloaded['datasets'])}):")
            if downloaded['datasets']:
                for ds in downloaded['datasets']:
                    size = sum(f.stat().st_size for f in ds.rglob('*') if f.is_file())
                    size_gb = size / (1024**3)
                    print(f"  • {ds.name} ({size_gb:.2f} GB)")
            else:
                print("  (none downloaded yet)")
            
            print(f"\nModels ({len(downloaded['models'])}):")
            if downloaded['models']:
                for model in downloaded['models']:
                    size = sum(f.stat().st_size for f in model.rglob('*') if f.is_file())
                    size_mb = size / (1024**2)
                    print(f"  • {model.name} ({size_mb:.1f} MB)")
            else:
                print("  (none downloaded yet)")
            
        elif args.command == "info":
            if not args.slug:
                print("Error: info command requires a slug")
                print("Example: uv run python scripts/kaggle_download.py info owner/dataset-name")
                sys.exit(1)
            
            client = KaggleClient()
            info = client.get_dataset_info(args.slug)
            
            print(f"\nDataset: {info['title']}")
            print(f"Size: {info['size'] / (1024**3):.2f} GB")
            print(f"URL: https://www.kaggle.com{info['url']}")
            if info['description']:
                print(f"\nDescription:")
                print(f"  {info['description'][:200]}...")
            
    except KeyboardInterrupt:
        print("\n\nDownload cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

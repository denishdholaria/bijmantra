#!/bin/bash
#
# Download Priority Agricultural Datasets
#
# This script downloads high-priority open web datasets for BijMantra:
# - NASA POWER: Global climate data (1981-present)
# - FAOSTAT: Global crop production (1961-present) 
# - USDA NASS: US agricultural statistics (1866-present)
# - PlantVillage: Plant disease images (54K images)
# - GDHY: Global historical yields (1981-2016)
#
# Usage:
#   bash scripts/download_priority_datasets.sh [--all|--nasa|--faostat|--usda|--images]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
DATA_DIR="/Volumes/hfs/bijmantra-datasets"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}BijMantra Priority Dataset Downloader${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${YELLOW}Creating BijMantra datasets directory: $DATA_DIR${NC}"
    mkdir -p "$DATA_DIR"
fi

echo -e "${GREEN}✓ Data directory: $DATA_DIR${NC}"
echo ""

# Function to download NASA POWER data
download_nasa_power() {
    echo -e "${BLUE}Downloading NASA POWER Climate Data...${NC}"
    echo -e "${YELLOW}  Coverage: Global, 1981-present${NC}"
    echo -e "${YELLOW}  Parameters: Temperature, Precipitation, Humidity${NC}"
    echo ""
    
    # Major agricultural regions
    # Punjab, India (30.9, 75.8)
    # Iowa, USA (42.0, -93.5)
    # São Paulo, Brazil (-23.5, -46.6)
    # Punjab, Pakistan (31.5, 74.3)
    # Henan, China (34.8, 113.6)
    
    cd "$BACKEND_DIR"
    
    PYTHONPATH=.. uv run python -m data_pipeline fetch --source nasa_power_climate \
        --locations "[(30.9, 75.8), (42.0, -93.5), (-23.5, -46.6), (31.5, 74.3), (34.8, 113.6)]" \
        --start_year 2010 \
        --end_year 2023 \
        --parameters "T2M,PRECTOTCORR,RH2M,WS2M"
    
    echo -e "${GREEN}✓ NASA POWER data downloaded${NC}"
    echo ""
}

# Function to download FAOSTAT data
download_faostat() {
    echo -e "${BLUE}Downloading FAOSTAT Production Data...${NC}"
    echo -e "${YELLOW}  Coverage: 245 countries, 200+ crops, 1961-present${NC}"
    echo -e "${YELLOW}  Elements: Production, Yield, Area Harvested${NC}"
    echo ""
    
    cd "$BACKEND_DIR"
    
    PYTHONPATH=.. uv run python -m data_pipeline fetch --source faostat_production \
        --start_year 2010 \
        --end_year 2023
    
    echo -e "${GREEN}✓ FAOSTAT data downloaded${NC}"
    echo ""
}

# Function to download USDA NASS data
download_usda_nass() {
    echo -e "${BLUE}Downloading USDA NASS Data...${NC}"
    echo -e "${YELLOW}  Coverage: US states, 100+ crops, 1866-present${NC}"
    echo ""
    
    # Check for API key
    if [ -z "$USDA_NASS_API_KEY" ]; then
        echo -e "${RED}✗ USDA_NASS_API_KEY not set${NC}"
        echo -e "${YELLOW}  Get a free API key from: https://quickstats.nass.usda.gov/api${NC}"
        echo -e "${YELLOW}  Then run: export USDA_NASS_API_KEY=your_key_here${NC}"
        return 1
    fi
    
    cd "$BACKEND_DIR"
    
    PYTHONPATH=.. uv run python -m data_pipeline fetch --source usda_nass \
        --api_key "$USDA_NASS_API_KEY" \
        --start_year 2010 \
        --end_year 2023 \
        --crops "CORN,WHEAT,SOYBEANS,RICE,COTTON"
    
    echo -e "${GREEN}✓ USDA NASS data downloaded${NC}"
    echo ""
}

# Function to download PlantVillage images
download_plantvillage() {
    echo -e "${BLUE}Downloading PlantVillage Disease Images...${NC}"
    echo -e "${YELLOW}  Coverage: 54,305 images, 38 disease classes, 14 crops${NC}"
    echo ""
    
    PLANTVILLAGE_DIR="$DATA_DIR/plantvillage"
    
    if [ -d "$PLANTVILLAGE_DIR" ]; then
        echo -e "${YELLOW}  PlantVillage already exists at $PLANTVILLAGE_DIR${NC}"
        echo -e "${YELLOW}  Skipping download (use --force to re-download)${NC}"
    else
        cd "$DATA_DIR"
        git clone https://github.com/spMohanty/PlantVillage-Dataset.git plantvillage
        echo -e "${GREEN}✓ PlantVillage images downloaded${NC}"
    fi
    echo ""
}

# Function to download GDHY (Global Dataset of Historical Yields)
download_gdhy() {
    echo -e "${BLUE}Downloading GDHY (Global Historical Yields)...${NC}"
    echo -e "${YELLOW}  Coverage: Global, 1981-2016, 4 major crops${NC}"
    echo ""
    
    GDHY_DIR="$DATA_DIR/gdhy"
    
    if [ -d "$GDHY_DIR" ]; then
        echo -e "${YELLOW}  GDHY already exists at $GDHY_DIR${NC}"
        echo -e "${YELLOW}  Skipping download${NC}"
    else
        mkdir -p "$GDHY_DIR"
        cd "$GDHY_DIR"
        
        echo -e "${YELLOW}  Downloading from Zenodo...${NC}"
        curl -L -o GDHY_v1.2.zip "https://zenodo.org/record/3712282/files/GDHY_v1.2.zip"
        
        echo -e "${YELLOW}  Extracting...${NC}"
        unzip GDHY_v1.2.zip
        rm GDHY_v1.2.zip
        
        echo -e "${GREEN}✓ GDHY data downloaded${NC}"
    fi
    echo ""
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Usage: $0 [--all|--nasa|--faostat|--usda|--images]${NC}"
    echo ""
    echo "Options:"
    echo "  --all       Download all priority datasets"
    echo "  --nasa      Download NASA POWER climate data"
    echo "  --faostat   Download FAOSTAT production data"
    echo "  --usda      Download USDA NASS data (requires API key)"
    echo "  --images    Download plant disease image datasets"
    echo ""
    exit 0
fi

case "$1" in
    --all)
        download_nasa_power
        download_faostat
        download_usda_nass || echo -e "${YELLOW}Skipping USDA NASS (no API key)${NC}"
        download_plantvillage
        download_gdhy
        ;;
    --nasa)
        download_nasa_power
        ;;
    --faostat)
        download_faostat
        ;;
    --usda)
        download_usda_nass
        ;;
    --images)
        download_plantvillage
        download_gdhy
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo -e "${YELLOW}Use --all, --nasa, --faostat, --usda, or --images${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Download Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Run the data pipeline: cd backend && PYTHONPATH=.. uv run python -m data_pipeline run"
echo "  2. Seed the database: cd backend && PYTHONPATH=.. uv run python -m app.db.seed --only=pipeline_observations --scope=system"
echo "  3. Test REEVU: Open http://localhost:5656 and ask about crop yields"
echo ""

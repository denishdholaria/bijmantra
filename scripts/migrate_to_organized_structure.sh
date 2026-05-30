#!/bin/bash
#
# Migrate existing datasets to organized structure
#
# This script moves existing datasets from /Volumes/hfs/*-data/ 
# to /Volumes/hfs/bijmantra-datasets/ for better organization.
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Migrate to Organized Structure${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

EXTERNAL_DRIVE="/Volumes/hfs"
NEW_BASE="$EXTERNAL_DRIVE/bijmantra-datasets"

# Check if external drive is mounted
if [ ! -d "$EXTERNAL_DRIVE" ]; then
    echo -e "${RED}✗ External drive not mounted: $EXTERNAL_DRIVE${NC}"
    exit 1
fi

# Create new base directory if it doesn't exist
mkdir -p "$NEW_BASE"
echo -e "${GREEN}✓ Base directory: $NEW_BASE${NC}"
echo ""

# Function to migrate a directory
migrate_dir() {
    local old_name=$1
    local new_name=$2
    local old_path="$EXTERNAL_DRIVE/$old_name"
    local new_path="$NEW_BASE/$new_name"
    
    if [ -d "$old_path" ]; then
        echo -e "${YELLOW}Migrating: $old_name → bijmantra-datasets/$new_name${NC}"
        
        # Check if destination already exists
        if [ -d "$new_path" ]; then
            echo -e "${YELLOW}  Destination already exists, merging...${NC}"
            rsync -av "$old_path/" "$new_path/"
            echo -e "${YELLOW}  Removing old directory...${NC}"
            rm -rf "$old_path"
        else
            # Simple move
            mv "$old_path" "$new_path"
        fi
        
        echo -e "${GREEN}  ✓ Migrated${NC}"
        
        # Show size
        size=$(du -sh "$new_path" | cut -f1)
        echo -e "${GREEN}  Size: $size${NC}"
        echo ""
    else
        echo -e "${BLUE}  ○ $old_name not found (skipping)${NC}"
    fi
}

# Migrate existing directories
echo -e "${BLUE}Migrating existing datasets...${NC}"
echo ""

migrate_dir "kaggle-data" "kaggle"
migrate_dir "faostat-data" "faostat"
migrate_dir "nasa-power-data" "nasa-power"
migrate_dir "usda-nass-data" "usda-nass"
migrate_dir "plantvillage-data" "plantvillage"
migrate_dir "gdhy-data" "gdhy"
migrate_dir "noaa-cdo-data" "noaa-cdo"
migrate_dir "worldclim-data" "worldclim"
migrate_dir "temp-downloads" ".temp"

# Migrate old kagglehub cache
if [ -d "$EXTERNAL_DRIVE/kagglehub-cache" ]; then
    echo -e "${YELLOW}Migrating kagglehub cache...${NC}"
    mkdir -p "$NEW_BASE/kaggle/.kagglehub-cache"
    rsync -av "$EXTERNAL_DRIVE/kagglehub-cache/" "$NEW_BASE/kaggle/.kagglehub-cache/"
    rm -rf "$EXTERNAL_DRIVE/kagglehub-cache"
    echo -e "${GREEN}  ✓ Migrated${NC}"
    echo ""
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Migration Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo "New structure:"
echo "  $NEW_BASE/"
ls -lh "$NEW_BASE" | tail -n +2 | awk '{print "    " $9 " (" $5 ")"}'
echo ""

echo "Total size:"
du -sh "$NEW_BASE"
echo ""

echo -e "${GREEN}✓ All datasets are now organized under bijmantra-datasets/${NC}"

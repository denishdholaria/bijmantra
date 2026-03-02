#!/bin/bash
#
# BijMantra Backup Script — APFS to exFAT
# Syncs project to T9 drive while handling macOS metadata properly
#
# Usage: ./scripts/backup_to_t9.sh
#

set -e

# === Configuration ===
SOURCE="/Volumes/ai/PlantBreedingAPP/bijmantra/"
DEST="/Volumes/T9/Work/APP_DEV/bijmantra/"
LOG_FILE="$HOME/.bijmantra_backup.log"

# === Colors ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# === Functions ===
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[WARNING] $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[ERROR] $1" >> "$LOG_FILE"
    exit 1
}

# === Pre-flight Checks ===
log "Starting BijMantra backup..."

# Check source exists
if [ ! -d "$SOURCE" ]; then
    error "Source directory not found: $SOURCE"
fi

# Check T9 drive is mounted
if [ ! -d "/Volumes/T9" ]; then
    error "T9 drive not mounted. Please connect the drive."
fi

# Create destination if needed
mkdir -p "$DEST"

# === Clean macOS metadata from source first (optional) ===
log "Cleaning macOS metadata files from source..."
find "$SOURCE" -name '.DS_Store' -delete 2>/dev/null || true
find "$SOURCE" -name '._*' -delete 2>/dev/null || true
find "$SOURCE" -name '.AppleDouble' -type d -exec rm -rf {} + 2>/dev/null || true
find "$SOURCE" -name '.Spotlight-V100' -type d -exec rm -rf {} + 2>/dev/null || true
find "$SOURCE" -name '.Trashes' -type d -exec rm -rf {} + 2>/dev/null || true
find "$SOURCE" -name '.fseventsd' -type d -exec rm -rf {} + 2>/dev/null || true

# === Rsync with exFAT-safe options ===
log "Syncing to T9 drive (exFAT)..."

rsync -av --progress \
    --delete \
    --exclude='.DS_Store' \
    --exclude='._*' \
    --exclude='.AppleDouble' \
    --exclude='.Spotlight-V100' \
    --exclude='.Trashes' \
    --exclude='.fseventsd' \
    --exclude='.TemporaryItems' \
    --exclude='Thumbs.db' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='backend/venv' \
    --exclude='frontend/dist' \
    --exclude='*.log' \
    --exclude='.env' \
    --exclude='.env.local' \
    --exclude='logs/' \
    --exclude='backend/logs/' \
    --no-perms \
    --no-owner \
    --no-group \
    --modify-window=1 \
    "$SOURCE" "$DEST"

# === Post-sync cleanup on destination ===
log "Cleaning any stray metadata on destination..."
find "$DEST" -name '.DS_Store' -delete 2>/dev/null || true
find "$DEST" -name '._*' -delete 2>/dev/null || true

# === Verification ===
log "Verifying backup..."
SOURCE_COUNT=$(find "$SOURCE" -type f \
    ! -name '.DS_Store' \
    ! -name '._*' \
    ! -path '*/.git/*' \
    ! -path '*/node_modules/*' \
    ! -path '*/venv/*' \
    ! -path '*/__pycache__/*' \
    ! -name '*.pyc' \
    ! -name '*.log' \
    2>/dev/null | wc -l | tr -d ' ')

DEST_COUNT=$(find "$DEST" -type f \
    ! -name '.DS_Store' \
    ! -name '._*' \
    2>/dev/null | wc -l | tr -d ' ')

log "Source files: $SOURCE_COUNT"
log "Destination files: $DEST_COUNT"

# === Summary ===
BACKUP_SIZE=$(du -sh "$DEST" 2>/dev/null | cut -f1)
log "Backup complete!"
log "Location: $DEST"
log "Size: $BACKUP_SIZE"
log "Log: $LOG_FILE"

echo ""
echo -e "${GREEN}✅ Backup successful!${NC}"
echo ""
echo "To restore or work from T9:"
echo "  1. cd $DEST"
echo "  2. python3 -m venv backend/venv"
echo "  3. source backend/venv/bin/activate"
echo "  4. pip install -r backend/requirements.txt"
echo "  5. cd frontend && npm install"

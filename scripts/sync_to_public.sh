#!/bin/bash
# Sync private repo to public repo (one-way, history-clean)
# Usage: ./scripts/sync_to_public.sh

set -e

PRIVATE_REPO="git@github.com:denishdholaria/bijmantraorg.git"
PUBLIC_REPO="git@github.com:denishdholaria/bijmantra.git"
TEMP_BASE="/tmp/bijmantra-public-sync"
SRC_DIR="$TEMP_BASE/private"
DEST_DIR="$TEMP_BASE/public"
EXCLUDE_FILE=".public-exclude"

echo "🔒 Starting private → public sync..."

# Clean up any existing temp directory
rm -rf "$TEMP_BASE"
mkdir -p "$TEMP_BASE"

# Clone private repo
echo "📥 Cloning private repo..."
git clone "$PRIVATE_REPO" "$SRC_DIR"

if [ ! -f "$SRC_DIR/$EXCLUDE_FILE" ]; then
    echo "❌ Missing $EXCLUDE_FILE in private repository root"
    exit 1
fi

echo "🧾 Using exclude rules from $EXCLUDE_FILE"

# Copy filtered content to a clean tree.
echo "🧹 Building filtered public snapshot..."
mkdir -p "$DEST_DIR"
rsync -a --delete --exclude-from="$SRC_DIR/$EXCLUDE_FILE" --exclude=".git/" "$SRC_DIR/" "$DEST_DIR/"

SOURCE_COMMIT=$(git -C "$SRC_DIR" rev-parse HEAD)

# Remove git history
echo "🗑️  Removing git history..."
rm -rf "$DEST_DIR/.git"

# Initialize fresh git repo (no history)
echo "🆕 Creating fresh git history..."
cd "$DEST_DIR"
git init
git add .
git commit -m "chore: sync from private repo (source: $SOURCE_COMMIT)"

# Force push to public repo
echo "📤 Pushing to public repo..."
git remote add public "$PUBLIC_REPO"
git push public main --force

# Cleanup
rm -rf "$TEMP_BASE"

echo "✅ Sync complete! Public repo updated with clean history."

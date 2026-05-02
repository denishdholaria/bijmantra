#!/bin/bash
# Final step: Publish reviewed snapshot to public repo
# Only run after reviewing snapshot and security scan

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SNAPSHOT_DIR="$HOME/Downloads/bijmantra-public-snapshot"
PUBLIC_REPO="git@github.com:denishdholaria/bijmantra.git"

echo "🚀 BijMantra Public Repo Publisher"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if snapshot exists
if [[ ! -d "$SNAPSHOT_DIR" ]]; then
    echo "❌ ERROR: Snapshot not found at $SNAPSHOT_DIR"
    echo "   Run: ./scripts/create_public_snapshot.sh first"
    exit 1
fi

# Check if security scan was run
if [[ ! -f "$SNAPSHOT_DIR/SECURITY_SCAN.txt" ]]; then
    echo "⚠️  WARNING: Security scan not found!"
    echo "   Run: ./scripts/scan_public_snapshot.sh first"
    echo ""
    read -p "Continue anyway? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        echo "❌ Aborted"
        exit 1
    fi
fi

# Final confirmation
echo "📍 Snapshot location: $SNAPSHOT_DIR"
echo "🎯 Target repo:       $PUBLIC_REPO"
echo ""
echo "⚠️  This will FORCE PUSH to the public repository!"
echo "   All existing history will be replaced with a clean snapshot."
echo ""
read -p "Are you sure you want to publish? (type 'PUBLISH' to confirm): " confirm

if [[ "$confirm" != "PUBLISH" ]]; then
    echo "❌ Aborted"
    exit 1
fi

echo ""
echo "📦 Preparing git repository..."

cd "$SNAPSHOT_DIR"

# Initialize fresh git repo if needed
if [[ ! -d ".git" ]]; then
    git init --initial-branch=main
    git config user.name "Denish Dholaria"
    git config user.email "hello@bijmantra.org"
fi

# Remove scan reports (don't publish these)
rm -f SNAPSHOT_REPORT.txt SECURITY_SCAN.txt

# Stage all files
echo "📝 Staging files..."
git add -A

# Create commit
COMMIT_MSG="chore: public snapshot $(date +%Y-%m-%d)"
echo "💾 Creating commit: $COMMIT_MSG"
git commit -m "$COMMIT_MSG" || echo "No changes to commit"

# Add remote if not exists
if ! git remote | grep -q "^public$"; then
    echo "🔗 Adding public remote..."
    git remote add public "$PUBLIC_REPO"
fi

# Push to public repo
echo ""
echo "🚀 Pushing to public repository..."
git push public main --force

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Successfully published to public repository!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 View at: https://github.com/denishdholaria/bijmantra"
echo ""

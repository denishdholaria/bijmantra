#!/bin/bash
# Simple script to create a reviewable public snapshot
# Manual control: review before pushing to public repo

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SNAPSHOT_DIR="$HOME/Downloads/bijmantra-public-snapshot"

echo "🔍 BijMantra Public Snapshot Creator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if .public-exclude exists
if [[ ! -f "$REPO_ROOT/.public-exclude" ]]; then
    echo "❌ ERROR: .public-exclude file not found in repo root"
    exit 1
fi

# Clean previous snapshot
if [[ -d "$SNAPSHOT_DIR" ]]; then
    echo "🗑️  Removing previous snapshot at: $SNAPSHOT_DIR"
    rm -rf "$SNAPSHOT_DIR"
fi

echo "📦 Creating fresh snapshot..."
mkdir -p "$SNAPSHOT_DIR"

# Copy files excluding patterns from .public-exclude
echo "📋 Applying exclusion rules from .public-exclude..."
rsync -a \
    --exclude-from="$REPO_ROOT/.public-exclude" \
    --exclude='.git/' \
    --exclude='.git-hooks/' \
    --exclude='node_modules/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='bun.lock' \
    --exclude='package-lock.json' \
    --exclude='poetry.lock' \
    --exclude='Cargo.lock' \
    "$REPO_ROOT/" \
    "$SNAPSHOT_DIR/"

# Create a manifest of what was excluded
echo ""
echo "📊 Generating exclusion report..."
REPORT_FILE="$SNAPSHOT_DIR/SNAPSHOT_REPORT.txt"

cat > "$REPORT_FILE" << EOF
BijMantra Public Snapshot Report
Generated: $(date)
Source: $REPO_ROOT
Snapshot: $SNAPSHOT_DIR

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXCLUDED PATTERNS (from .public-exclude):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

grep -v '^#' "$REPO_ROOT/.public-exclude" | grep -v '^$' >> "$REPORT_FILE" || true

echo "" >> "$REPORT_FILE"
echo "FILES EXCLUDED:" >> "$REPORT_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$REPORT_FILE"

# Find files that exist in source but not in snapshot
cd "$REPO_ROOT"
while IFS= read -r pattern; do
    # Skip comments and empty lines
    [[ "$pattern" =~ ^#.*$ ]] && continue
    [[ -z "$pattern" ]] && continue
    
    # Find matching files
    if [[ -d "$pattern" ]] || [[ -f "$pattern" ]]; then
        echo "  - $pattern" >> "$REPORT_FILE"
    else
        # Pattern-based search
        find . -path "./$pattern" -o -name "$pattern" 2>/dev/null | sed 's|^\./||' | while read -r file; do
            if [[ -e "$file" ]]; then
                echo "  - $file" >> "$REPORT_FILE"
            fi
        done
    fi
done < "$REPO_ROOT/.public-exclude"

# Count files
TOTAL_FILES=$(find "$REPO_ROOT" -type f | wc -l | tr -d ' ')
SNAPSHOT_FILES=$(find "$SNAPSHOT_DIR" -type f | wc -l | tr -d ' ')
EXCLUDED_COUNT=$((TOTAL_FILES - SNAPSHOT_FILES))

cat >> "$REPORT_FILE" << EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATISTICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total files in source:    $TOTAL_FILES
Files in snapshot:         $SNAPSHOT_FILES
Files excluded:            $EXCLUDED_COUNT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Review the snapshot at: $SNAPSHOT_DIR
2. Check for any sensitive files that shouldn't be public
3. Run security scan: ./scripts/scan_public_snapshot.sh
4. If safe, push manually to public repo

⚠️  IMPORTANT: Always review before publishing!
EOF

echo ""
echo "✅ Snapshot created successfully!"
echo ""
echo "📍 Location: $SNAPSHOT_DIR"
echo "📄 Report:   $SNAPSHOT_DIR/SNAPSHOT_REPORT.txt"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Statistics:"
echo "   Total files in source:  $TOTAL_FILES"
echo "   Files in snapshot:      $SNAPSHOT_FILES"
echo "   Files excluded:         $EXCLUDED_COUNT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔍 Next steps:"
echo "   1. Review snapshot:  open $SNAPSHOT_DIR"
echo "   2. Security scan:    ./scripts/scan_public_snapshot.sh"
echo "   3. View report:      cat $SNAPSHOT_DIR/SNAPSHOT_REPORT.txt"
echo ""

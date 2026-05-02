#!/bin/bash
# Security scanner for public snapshot
# Checks for common secrets and sensitive patterns

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SNAPSHOT_DIR="$HOME/Downloads/bijmantra-public-snapshot"

echo "🔐 BijMantra Public Snapshot Security Scanner"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [[ ! -d "$SNAPSHOT_DIR" ]]; then
    echo "❌ ERROR: Snapshot not found at $SNAPSHOT_DIR"
    echo "   Run: ./scripts/create_public_snapshot.sh first"
    exit 1
fi

ISSUES_FOUND=0
SCAN_REPORT="$SNAPSHOT_DIR/SECURITY_SCAN.txt"

cat > "$SCAN_REPORT" << EOF
BijMantra Public Snapshot Security Scan
Generated: $(date)
Snapshot: $SNAPSHOT_DIR

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECURITY CHECKS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

cd "$SNAPSHOT_DIR"

# Check 1: Environment files
echo "🔍 Checking for environment files..."
if find . -name ".env*" -o -name "*.env" | grep -q .; then
    echo "⚠️  WARNING: Found .env files:" | tee -a "$SCAN_REPORT"
    find . -name ".env*" -o -name "*.env" | tee -a "$SCAN_REPORT"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
    echo "" >> "$SCAN_REPORT"
else
    echo "✅ No .env files found" | tee -a "$SCAN_REPORT"
fi

# Check 2: Private keys
echo "🔍 Checking for private keys..."
if find . \( -name "*.key" -o -name "*.pem" -o -name "*.p12" -o -name "*.pfx" \) | grep -q .; then
    echo "⚠️  WARNING: Found private key files:" | tee -a "$SCAN_REPORT"
    find . \( -name "*.key" -o -name "*.pem" -o -name "*.p12" -o -name "*.pfx" \) | tee -a "$SCAN_REPORT"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
    echo "" >> "$SCAN_REPORT"
else
    echo "✅ No private key files found" | tee -a "$SCAN_REPORT"
fi

# Check 3: Sensitive folder names
echo "🔍 Checking for sensitive folders..."
SENSITIVE_DIRS=(".kiro" ".agent" ".ai" "ops-private" ".bijmantra" ".openclaw" ".nemoclaw" "confidential" "private")
for dir in "${SENSITIVE_DIRS[@]}"; do
    if find . -type d -name "$dir" | grep -q .; then
        echo "⚠️  WARNING: Found sensitive directory: $dir" | tee -a "$SCAN_REPORT"
        find . -type d -name "$dir" | tee -a "$SCAN_REPORT"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        echo "" >> "$SCAN_REPORT"
    fi
done

# Check 4: Common secret patterns in files
echo "🔍 Scanning file contents for secrets..."
SECRET_PATTERNS=(
    "api[_-]?key"
    "api[_-]?secret"
    "password\s*="
    "token\s*="
    "secret\s*="
    "private[_-]?key"
    "access[_-]?token"
    "auth[_-]?token"
    "bearer\s+[A-Za-z0-9\-\._~\+\/]+"
    "sk-[A-Za-z0-9]{20,}"
    "ghp_[A-Za-z0-9]{36}"
    "gho_[A-Za-z0-9]{36}"
)

for pattern in "${SECRET_PATTERNS[@]}"; do
    matches=$(grep -r -i -n "$pattern" --include="*.py" --include="*.js" --include="*.ts" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.toml" --include="*.sh" . 2>/dev/null || true)
    if [[ -n "$matches" ]]; then
        echo "⚠️  WARNING: Found potential secret pattern: $pattern" | tee -a "$SCAN_REPORT"
        echo "$matches" | head -5 | tee -a "$SCAN_REPORT"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        echo "" >> "$SCAN_REPORT"
    fi
done

# Check 5: Hardcoded IPs and domains
echo "🔍 Checking for hardcoded IPs and internal domains..."
if grep -r -n -E "([0-9]{1,3}\.){3}[0-9]{1,3}" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | grep -v "0.0.0.0" | grep -v "127.0.0.1" | grep -v "localhost" | head -5 | grep -q .; then
    echo "⚠️  WARNING: Found hardcoded IP addresses:" | tee -a "$SCAN_REPORT"
    grep -r -n -E "([0-9]{1,3}\.){3}[0-9]{1,3}" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | grep -v "0.0.0.0" | grep -v "127.0.0.1" | grep -v "localhost" | head -5 | tee -a "$SCAN_REPORT"
    echo "" >> "$SCAN_REPORT"
fi

# Check 6: TODO/FIXME with sensitive context
echo "🔍 Checking for sensitive TODOs..."
if grep -r -n -i "TODO.*\(secret\|password\|key\|token\|private\)" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | head -5 | grep -q .; then
    echo "⚠️  WARNING: Found TODOs mentioning secrets:" | tee -a "$SCAN_REPORT"
    grep -r -n -i "TODO.*\(secret\|password\|key\|token\|private\)" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | head -5 | tee -a "$SCAN_REPORT"
    echo "" >> "$SCAN_REPORT"
fi

# Summary
echo "" | tee -a "$SCAN_REPORT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$SCAN_REPORT"
echo "SCAN SUMMARY:" | tee -a "$SCAN_REPORT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$SCAN_REPORT"

if [[ $ISSUES_FOUND -eq 0 ]]; then
    echo "✅ No security issues found!" | tee -a "$SCAN_REPORT"
    echo "   Snapshot appears safe for public release." | tee -a "$SCAN_REPORT"
    echo "" | tee -a "$SCAN_REPORT"
    echo "📋 Full report saved to: $SCAN_REPORT"
    exit 0
else
    echo "⚠️  Found $ISSUES_FOUND potential security issue(s)" | tee -a "$SCAN_REPORT"
    echo "   Review the issues above before publishing." | tee -a "$SCAN_REPORT"
    echo "" | tee -a "$SCAN_REPORT"
    echo "📋 Full report saved to: $SCAN_REPORT"
    exit 1
fi

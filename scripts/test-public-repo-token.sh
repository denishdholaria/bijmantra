#!/bin/bash
# =============================================================================
# Test PUBLIC_REPO_TOKEN Access
# =============================================================================
# This script tests if your GitHub token can push to the public repo
# Run this locally to verify before enabling the GitHub Action
#
# Usage: ./scripts/test-public-repo-token.sh YOUR_TOKEN_HERE
# =============================================================================

set -e

TOKEN="$1"

if [ -z "$TOKEN" ]; then
    echo "❌ Usage: $0 YOUR_GITHUB_TOKEN"
    echo ""
    echo "To get a token:"
    echo "1. Go to https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Select 'repo' scope (full control of private repositories)"
    echo "4. Copy the token and run this script"
    exit 1
fi

echo "🔍 Testing token access to public repo..."
echo ""

# Test 1: Check if token can access the repo
echo "Test 1: Checking repo access..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/denishdholaria/bijmantra")

if [ "$RESPONSE" = "200" ]; then
    echo "  ✅ Can access repo (HTTP $RESPONSE)"
else
    echo "  ❌ Cannot access repo (HTTP $RESPONSE)"
    echo "     Token may be invalid or expired"
    exit 1
fi

# Test 2: Check if token has push permission
echo "Test 2: Checking push permission..."
PERMISSIONS=$(curl -s \
    -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/denishdholaria/bijmantra" | grep -o '"push":[^,]*' | head -1)

if echo "$PERMISSIONS" | grep -q "true"; then
    echo "  ✅ Has push permission"
else
    echo "  ❌ No push permission"
    echo "     Token needs 'repo' scope"
    exit 1
fi

# Test 3: Check token scopes
echo "Test 3: Checking token scopes..."
SCOPES=$(curl -s -I \
    -H "Authorization: token $TOKEN" \
    "https://api.github.com/user" | grep -i "x-oauth-scopes:" | cut -d: -f2-)

echo "  Token scopes: $SCOPES"

if echo "$SCOPES" | grep -q "repo"; then
    echo "  ✅ Has 'repo' scope"
else
    echo "  ⚠️  Missing 'repo' scope - token may not work for pushing"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    ✅ Token looks good!                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. Go to: https://gitlab.com/denishdholaria/bijmantraorg/settings/secrets/actions"
echo "2. Delete the existing PUBLIC_REPO_TOKEN secret"
echo "3. Create a new secret named PUBLIC_REPO_TOKEN with this token"
echo "4. Re-enable the workflow:"
echo "   mv .github/workflows/sync-to-public.yml.disabled .github/workflows/sync-to-public.yml"
echo "5. Push to trigger the sync"

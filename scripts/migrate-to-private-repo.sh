#!/bin/bash
# =============================================================================
# Migrate to Private Repository
# =============================================================================
# This script migrates your working repo from public to private origin.
# Run ONCE to set up the new architecture.
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║       🔄 Migrate to Private Repository Architecture           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check current remotes
echo -e "${YELLOW}Current git remotes:${NC}"
git remote -v
echo ""

# Confirm
echo -e "${YELLOW}This script will:${NC}"
echo "  1. Rename 'origin' (public) to 'public'"
echo "  2. Add private repo as new 'origin'"
echo "  3. Push all content to private repo"
echo ""
echo -e "${RED}Make sure you have SSH access to:${NC}"
echo "  git@github.com:denishdholaria/bijmantraorg.git"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Step 1: Rename current origin to 'public'
echo -e "\n${YELLOW}Step 1: Renaming origin to public...${NC}"
if git remote get-url public &>/dev/null; then
    echo "  'public' remote already exists, skipping rename"
else
    git remote rename origin public
    echo -e "${GREEN}  ✅ Renamed origin → public${NC}"
fi

# Step 2: Add private repo as origin
echo -e "\n${YELLOW}Step 2: Adding private repo as origin...${NC}"
if git remote get-url origin &>/dev/null; then
    echo "  'origin' remote already exists"
    CURRENT_ORIGIN=$(git remote get-url origin)
    if [[ "$CURRENT_ORIGIN" == *"bijmantraorg"* ]]; then
        echo -e "${GREEN}  ✅ Already pointing to private repo${NC}"
    else
        echo -e "${RED}  ⚠️  Origin points to: $CURRENT_ORIGIN${NC}"
        echo "  Updating to private repo..."
        git remote set-url origin git@github.com:denishdholaria/bijmantraorg.git
        echo -e "${GREEN}  ✅ Updated origin to private repo${NC}"
    fi
else
    git remote add origin git@github.com:denishdholaria/bijmantraorg.git
    echo -e "${GREEN}  ✅ Added private repo as origin${NC}"
fi

# Step 3: Push to private repo
echo -e "\n${YELLOW}Step 3: Pushing to private repo...${NC}"
echo "  This may take a moment..."
git push -u origin main --force
echo -e "${GREEN}  ✅ Pushed to private repo${NC}"

# Step 4: Push tags
echo -e "\n${YELLOW}Step 4: Pushing tags...${NC}"
git push origin --tags 2>/dev/null || echo "  No tags to push"
echo -e "${GREEN}  ✅ Tags pushed${NC}"

# Summary
echo -e "\n${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    🎉 Migration Complete!                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}New git remotes:${NC}"
git remote -v
echo ""

echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Go to https://gitlab.com/denishdholaria/bijmantraorg/settings/secrets/actions"
echo "  2. Add secret: PUBLIC_REPO_TOKEN (Personal Access Token with repo scope)"
echo "  3. Push a commit to test the sync workflow"
echo ""
echo -e "${GREEN}From now on:${NC}"
echo "  - Work in this repo (private)"
echo "  - Push to 'origin' (private repo)"
echo "  - Public repo auto-syncs via GitHub Action"
echo ""

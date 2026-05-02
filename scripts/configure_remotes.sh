#!/bin/bash
# Configure git remotes for safety

set -e

echo "🔧 Configuring git remotes..."

# Remove public remote if it exists
git remote remove origin 2>/dev/null || true

# Set private repo as the only remote
git remote add origin git@github.com:denishdholaria/bijmantraorg.git 2>/dev/null || \
git remote set-url origin git@github.com:denishdholaria/bijmantraorg.git

echo "✅ Git remotes configured!"
echo "📋 Only private repo (bijmantraorg) is configured"
echo "🔒 Public repo can only be updated via sync script"

git remote -v

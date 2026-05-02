#!/bin/bash
# Setup git hooks to prevent accidental public repo pushes

set -e

echo "🔧 Setting up git hooks..."

# Make hooks executable
chmod +x .git-hooks/pre-push

# Prefer a repo-local hooks path so hooks survive clone/reinstall workflows.
git config core.hooksPath .git-hooks

# Backward-compatible install for tooling that only checks .git/hooks.
mkdir -p .git/hooks
cp .git-hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push

echo "✅ Git hooks installed!"
echo "✅ core.hooksPath set to .git-hooks"
echo "📋 Direct pushes to public repo are now blocked"
echo "🔒 Use ./scripts/sync_to_public.sh to sync to public"

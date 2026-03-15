#!/bin/bash
# Complete setup for repo security

set -e

echo "🔐 Setting up repository security..."
echo ""

# 1. Configure remotes
echo "Step 1: Configuring git remotes..."
bash scripts/configure_remotes.sh
echo ""

# 2. Install git hooks
echo "Step 2: Installing git hooks..."
bash scripts/setup_git_hooks.sh
echo ""

# 3. Make sync script executable
echo "Step 3: Setting up sync script..."
chmod +x scripts/sync_to_public.sh
echo "✅ Sync script ready"
echo ""

# 4. Add reminder to .bashrc or .zshrc
echo "Step 4: Adding safety reminder..."
cat >> ~/.zshrc << 'EOF'

# Bijmantra repo safety reminder
alias git-push-public='echo "⚠️  Use: ./scripts/sync_to_public.sh" && echo "❌ Direct push blocked by hooks"'
EOF

echo "✅ All security measures installed!"
echo ""
echo "📋 Summary:"
echo "  - Only private repo (bijmantraorg) is configured as remote"
echo "  - Git hooks block accidental public pushes"
echo "  - Use ./scripts/sync_to_public.sh to update public repo"
echo "  - Excluded patterns defined in .public-exclude"
echo ""
echo "🔒 Your secrets are now protected!"

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

# 4. Keep the shared bpro workspace out of any parent home-level git repo.
echo "Step 4: Installing local workspace boundary ignore..."
HOME_GIT_DIR="$HOME/.git"
HOME_GIT_EXCLUDE="$HOME_GIT_DIR/info/exclude"
WORKSPACE_IGNORE="Documents/bpro/"

if [ -d "$HOME_GIT_DIR" ]; then
	mkdir -p "$(dirname "$HOME_GIT_EXCLUDE")"
	if ! grep -Fqx "$WORKSPACE_IGNORE" "$HOME_GIT_EXCLUDE" 2>/dev/null; then
		echo "" >> "$HOME_GIT_EXCLUDE"
		echo "# Local workspace boundaries" >> "$HOME_GIT_EXCLUDE"
		echo "# Keep BijMantra code and confidential docs out of the home-level repo." >> "$HOME_GIT_EXCLUDE"
		echo "$WORKSPACE_IGNORE" >> "$HOME_GIT_EXCLUDE"
	fi
	echo "✅ Parent home-level repo ignore updated"
else
	echo "⚠️  No home-level git repo found at $HOME_GIT_DIR; skipped local exclude update"
fi
echo ""

# 5. Add reminder to .bashrc or .zshrc
echo "Step 5: Adding safety reminder..."
cat >> ~/.zshrc << 'EOF'

# Bijmantra repo safety reminder
alias git-push-public='echo "⚠️  Use: ./scripts/sync_to_public.sh" && echo "❌ Direct push blocked by hooks"'
EOF

echo "✅ All security measures installed!"
echo ""
echo "📋 Summary:"
echo "  - Only private repo (bijmantraorg) is configured as remote"
echo "  - Git hooks block accidental public pushes"
echo "  - Parent home repo ignores Documents/bpro/ locally"
echo "  - Use ./scripts/sync_to_public.sh to update public repo"
echo "  - Excluded patterns defined in .public-exclude"
echo ""
echo "🔒 Your secrets are now protected!"

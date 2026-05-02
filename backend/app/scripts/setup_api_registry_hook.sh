#!/bin/bash
# Setup pre-commit hook for API registry regeneration

HOOK_FILE=".git/hooks/pre-commit"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

if [ -z "$REPO_ROOT" ]; then
    echo "Error: Not in a git repository"
    exit 1
fi

HOOK_PATH="$REPO_ROOT/$HOOK_FILE"

# Create hooks directory if it doesn't exist
mkdir -p "$(dirname "$HOOK_PATH")"

# Create or append to pre-commit hook
cat > "$HOOK_PATH" << 'EOF'
#!/bin/bash
# Pre-commit hook: Regenerate API registry on API changes

# Check if any API files have changed
API_FILES_CHANGED=$(git diff --cached --name-only | grep -E '(backend/app/(api|modules)/.*\.py|backend/app/main\.py)')

if [ -n "$API_FILES_CHANGED" ]; then
    echo "API files changed, regenerating API registry..."
    
    # Run the registry generator
    cd backend
    python3 -m app.scripts.generate_api_registry
    
    if [ $? -eq 0 ]; then
        # Add the generated files to the commit
        git add ../docs/api/API_REGISTRY.md
        git add ../docs/api/API_REGISTRY.json
        echo "✓ API registry updated and staged"
    else
        echo "✗ Failed to generate API registry"
        exit 1
    fi
fi

exit 0
EOF

# Make the hook executable
chmod +x "$HOOK_PATH"

echo "✓ Pre-commit hook installed at $HOOK_PATH"
echo ""
echo "The hook will automatically regenerate the API registry when:"
echo "  - API endpoint files are modified"
echo "  - Module routers are changed"
echo "  - main.py is updated"
echo ""
echo "To manually regenerate the registry:"
echo "  cd backend && python3 -m app.scripts.generate_api_registry"

#!/bin/bash

# Legacy compatibility wrapper for first-time setup.
# Prefer using ./setup.sh directly.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "InitializeApp.sh is kept as a compatibility alias."
echo "Prefer: bash ./setup.sh"
echo ""

exec bash "$SCRIPT_DIR/setup.sh"

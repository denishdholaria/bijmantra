#!/bin/bash

# Backward-compatible launcher for the clearly named main app startup script.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "start.sh is kept as a compatibility alias."
echo "Prefer: bash ./start-bijmantra-app.sh"
echo ""

exec bash "$SCRIPT_DIR/start-bijmantra-app.sh"

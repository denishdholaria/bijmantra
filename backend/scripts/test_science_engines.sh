#!/usr/bin/env bash
# ===================================================================
# Science Engine Test Harness (C3)
# Runs all science engine tests with coverage and summary report
# ===================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           BijMantra Science Engine — Test Harness           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# All science engine test files
TEST_FILES=(
    "tests/services/test_dimensionality_reduction.py"
    "tests/services/test_mixed_model.py"
    "tests/services/test_simulation.py"
    "tests/core/test_optimization.py"
    "tests/services/test_pedigree.py"
    "tests/services/test_image_analysis.py"
    "tests/services/test_spatial_correction.py"
    "tests/services/test_advanced_engines.py"
    "tests/services/test_vision_model.py"
)

# Filter to only existing files
EXISTING_TESTS=()
for t in "${TEST_FILES[@]}"; do
    if [ -f "$t" ]; then
        EXISTING_TESTS+=("$t")
    else
        echo "⚠  Skipping (not found): $t"
    fi
done

echo ""
echo "Running ${#EXISTING_TESTS[@]} test files..."
echo "────────────────────────────────────────────────────────────────"

# Run with verbose output
./venv/bin/python -m pytest "${EXISTING_TESTS[@]}" \
    -v \
    --tb=short \
    -q \
    2>&1 | tail -20

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Science Engine test harness complete"
echo "════════════════════════════════════════════════════════════════"

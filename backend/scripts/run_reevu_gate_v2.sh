#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

run_step() {
  local header="$1"
  local cmd="$2"
  local start_time end_time elapsed

  echo
  echo "============================================================"
  echo "$header"
  echo "Command: $cmd"
  echo "============================================================"

  start_time=$(date +%s)
  if ! eval "$cmd"; then
    echo
    echo "❌ Gate failed."
    echo "Failing command: $cmd"
    exit 1
  fi
  end_time=$(date +%s)
  elapsed=$((end_time - start_time))
  echo "✅ Completed in ${elapsed}s"
}

run_step "[1/5] API v2 unit tests" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt --with pytest pytest tests/units/api/v2 -q"
run_step "[2/5] Stage C regression tests" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt --with pytest pytest tests/units/test_reevu_stage_c.py -q"
run_step "[3/5] Reevu metrics tests" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt --with pytest pytest tests/units/test_reevu_metrics.py -q"
run_step "[4/5] Cross-domain reasoning evaluation" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt python scripts/eval_cross_domain_reasoning.py"
run_step "[5/5] Reevu ops report generation" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt python scripts/generate_reevu_ops_report.py"

echo
echo "############################################################"
echo "✅ Reevu Gate v2 completed successfully"
echo "All 5 validation commands passed."
echo "############################################################"

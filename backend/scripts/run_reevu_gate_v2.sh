#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MANAGED_EVAL_BASE_URL="${REEVU_MANAGED_EVAL_BASE_URL:-}"
MANAGED_EVAL_TOKEN="${REEVU_MANAGED_EVAL_TOKEN:-}"

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

run_step "[gate] API v2 unit tests" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt --with pytest pytest tests/units/api/v2 -q"
run_step "[gate] Stage C regression tests" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt --with pytest pytest tests/units/test_reevu_stage_c.py -q"
run_step "[gate] Reevu metrics tests" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt --with pytest pytest tests/units/test_reevu_metrics.py -q"
run_step "[gate] Cross-domain reasoning evaluation" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt python scripts/eval_cross_domain_reasoning.py"
run_step "[gate] Local real-question benchmark" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt python scripts/eval_real_question_benchmark.py --runtime-path local --json-output test_reports/reevu_real_question_local.json --local-readiness-census-output test_reports/reevu_local_readiness_census.json --fail-on-failed-cases"
run_step "[gate] Local authority-gap report" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt python scripts/generate_reevu_authority_gap_report.py --benchmark-artifact test_reports/reevu_real_question_local.json --readiness-census-artifact test_reports/reevu_local_readiness_census.json --json-output test_reports/reevu_authority_gap_report.json"

required_runtime_paths="local"
if [[ -n "$MANAGED_EVAL_BASE_URL" ]]; then
  managed_eval_cmd="cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt python scripts/eval_real_question_benchmark.py --runtime-path managed --managed-base-url \"$MANAGED_EVAL_BASE_URL\" --json-output test_reports/reevu_real_question_managed.json --fail-on-failed-cases"
  if [[ -n "$MANAGED_EVAL_TOKEN" ]]; then
    managed_eval_cmd+=" --managed-auth-token \"$MANAGED_EVAL_TOKEN\""
  else
    echo
    echo "============================================================"
    echo "[gate] Managed real-question benchmark"
    echo "Note: REEVU_MANAGED_EVAL_TOKEN is not set; proceeding without managed bearer auth"
    echo "============================================================"
  fi
  run_step "[gate] Managed real-question benchmark" "$managed_eval_cmd"
  required_runtime_paths="local managed"
else
  echo
  echo "============================================================"
  echo "[gate] Managed real-question benchmark"
  echo "Skipped: REEVU_MANAGED_EVAL_BASE_URL is not set"
  echo "Pending: final acceptance remains blocked until managed runtime is configured and evaluated"
  echo "============================================================"
fi

run_step "[gate] Reevu ops report generation" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt python scripts/generate_reevu_ops_report.py"
run_step "[gate] Reevu artifact integrity validation" "cd \"$BACKEND_DIR\" && uv run --with-requirements requirements.txt python scripts/validate_reevu_artifacts.py --required-runtime-paths ${required_runtime_paths}"

echo
echo "############################################################"
echo "✅ Reevu Gate v2 completed successfully"
echo "All configured validation commands passed."
if [[ -z "$MANAGED_EVAL_BASE_URL" ]]; then
  echo "Managed runtime evidence is still pending configuration for final acceptance."
fi
echo "############################################################"

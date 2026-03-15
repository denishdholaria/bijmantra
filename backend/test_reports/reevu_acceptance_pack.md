# REEVU Final Acceptance Pack

**Generated at (UTC):** 2026-02-27T07:42:55.422110+00:00  
**Commit:** `b90241b9434a56e7219fce7899dca6af0f6f9e52`  
**Overall acceptance status:** **PASSED**

## Gate Command Outcomes

| Command | Status | Duration (s) | Return code |
|---------|--------|--------------|-------------|
| `uv run pytest tests/units/api/v2 -q` | ✅ passed | 19.153 | 0 |
| `uv run pytest tests/units/test_reevu_stage_c.py -q` | ✅ passed | 11.306 | 0 |
| `uv run pytest tests/units/test_reevu_metrics.py -q` | ✅ passed | 11.096 | 0 |
| `uv run python scripts/eval_cross_domain_reasoning.py` | ✅ passed | 0.194 | 0 |
| `uv run python scripts/generate_reevu_ops_report.py` | ✅ passed | 0.043 | 0 |

## KPI Deltas vs Comparator

| KPI | Current | Comparator | Delta | Floor | Floor met |
|-----|---------|------------|-------|-------|-----------|
| trace_completeness | 100.00% | N/A | N/A | 99.00% | ✅ |
| tool_call_precision | 100.00% | N/A | N/A | 92.00% | ✅ |
| domain_detection_accuracy | 96.97% | N/A | N/A | 85.00% | ✅ |
| compound_classification | 90.91% | N/A | N/A | 80.00% | ✅ |
| step_adequacy | 100.00% | N/A | N/A | 85.00% | ✅ |

## Artifact Integrity

**All artifacts valid:** ✅ yes

| Artifact | Exists | Valid | Details |
|----------|--------|-------|---------|
| trace_completeness_baseline | ✅ | ✅ | valid JSON |
| top_intent_routing_baseline | ✅ | ✅ | valid JSON |
| stage_a_kpi_report | ✅ | ✅ | valid JSON |
| cross_domain_reasoning_baseline | ✅ | ✅ | valid JSON |
| ops_report_json | ✅ | ✅ | valid JSON |
| ops_report_markdown | ✅ | ✅ | non-empty text |

## Explicit Blockers

- None.

## Risk Notes (Placeholder)

- [ ] Add operational and release risk notes.

## Rollback Checklist (Placeholder)

- [ ] Revert `backend/scripts/generate_reevu_acceptance_pack.py` if acceptance format is unsuitable.
- [ ] Revert generated acceptance artifacts under `backend/test_reports/`.
- [ ] Revert generated summary doc under `docs/development/reevu/`.

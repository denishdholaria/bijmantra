# REEVU Ops Report

**Generated:** 2026-04-05T10:38:24.285099+00:00  
**Stages evaluated:** A, C  
**Overall floor met:** ✅ met

## KPI Summary

| Metric | Value | Floor | Status |
|--------|-------|-------|--------|
| trace_completeness | 100.00% | 99.00% | ✅ met |
| tool_call_precision | 100.00% | 92.00% | ✅ met |
| domain_detection_accuracy | 96.97% | 85.00% | ✅ met |
| compound_classification | 90.91% | 80.00% | ✅ met |
| step_adequacy | 100.00% | 85.00% | ✅ met |

## Runtime Readiness

### Local Runtime

**Status:** `blocked`  
**Selected local org:** 1  
**Pass rate:** 21.43% (3/14 passed)  
**Authority-gap status:** `selected_local_org_blocked`  
**Benchmark-ready org IDs:** 2

### Local Readiness Blockers

- observations.empty
- bio_gwas_runs.empty
- bio_qtls.empty

### Local Readiness Warnings

- germplasm.sparse
- trials.sparse

### Common Blockers Across Blocked Orgs

- bio_gwas_runs.empty
- bio_qtls.empty
- observations.empty

### Local Selection Guidance

- Benchmark-ready local coverage currently comes from demo-dataset tenant(s): 2 (Demo Organization). The canonical demo dataset is isolated from production and staging; do not mirror demo-seeded benchmark data into selected non-demo organization 1 (Default Organization). Use the ready demo tenant for supplementary local executor verification or provision authoritative data for the selected organization.

### Local Remediation Guidance

- observations.empty: Provision authoritative observations for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=observation.
- bio_gwas_runs.empty: Persist authoritative GWAS runs for the selected organization through the authenticated GWAS execution surface at /api/v2/bio-analytics/gwas/run using authoritative genotype and phenotype inputs.
- bio_qtls.empty: Provision authoritative BioQTL rows for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=qtl.
- germplasm.sparse: Expand authoritative germplasm coverage for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=germplasm.
- trials.sparse: Expand authoritative trial coverage for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=trial.

### Managed Runtime

Managed runtime artifact not present.

## Sources

- **trace_completeness**: `test_reports/reevu_trace_completeness_baseline.json`
- **top_intent_routing**: `test_reports/reevu_top_intent_routing_baseline.json`
- **stage_a_kpi**: `test_reports/reevu_stage_a_kpi_report.json`
- **cross_domain_reasoning**: `test_reports/reevu_cross_domain_reasoning_baseline.json`
- **real_question_local**: `test_reports/reevu_real_question_local.json`
- **local_readiness_census**: `test_reports/reevu_local_readiness_census.json`
- **authority_gap_report**: `test_reports/reevu_authority_gap_report.json`
- **real_question_managed**: `test_reports/reevu_real_question_managed.json`

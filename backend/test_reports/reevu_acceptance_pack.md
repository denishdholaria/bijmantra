# REEVU Final Acceptance Pack

**Generated at (UTC):** 2026-04-05T10:38:24.332771+00:00  
**Commit:** `81bc2ac702ae20b75238312f58694ccb393fb116`  
**Overall acceptance status:** **BLOCKED**

## Gate Command Outcomes

| Command | Status | Duration (s) | Return code |
|---------|--------|--------------|-------------|
| `/Users/denish/Documents/bpro/bijmantraorg/backend/venv/bin/python -m pytest tests/units/api/v2 -q` | ✅ passed | 17.677 | 0 |
| `/Users/denish/Documents/bpro/bijmantraorg/backend/venv/bin/python -m pytest tests/units/test_reevu_stage_c.py -q` | ✅ passed | 12.048 | 0 |
| `/Users/denish/Documents/bpro/bijmantraorg/backend/venv/bin/python -m pytest tests/units/test_reevu_metrics.py -q` | ✅ passed | 12.403 | 0 |
| `/Users/denish/Documents/bpro/bijmantraorg/backend/venv/bin/python scripts/eval_cross_domain_reasoning.py` | ✅ passed | 0.276 | 0 |
| `/Users/denish/Documents/bpro/bijmantraorg/backend/venv/bin/python scripts/eval_real_question_benchmark.py --runtime-path local --json-output test_reports/reevu_real_question_local.json --local-readiness-census-output test_reports/reevu_local_readiness_census.json --fail-on-failed-cases` | ❌ failed | 10.663 | 1 |
| `/Users/denish/Documents/bpro/bijmantraorg/backend/venv/bin/python scripts/generate_reevu_authority_gap_report.py --benchmark-artifact test_reports/reevu_real_question_local.json --readiness-census-artifact test_reports/reevu_local_readiness_census.json --json-output test_reports/reevu_authority_gap_report.json` | ✅ passed | 0.05 | 0 |
| `/Users/denish/Documents/bpro/bijmantraorg/backend/venv/bin/python scripts/generate_reevu_ops_report.py` | ✅ passed | 0.034 | 0 |
| `/Users/denish/Documents/bpro/bijmantraorg/backend/venv/bin/python scripts/validate_reevu_artifacts.py --required-runtime-paths local` | ✅ passed | 0.042 | 0 |

## KPI Deltas vs Comparator

| KPI | Current | Comparator | Delta | Floor | Floor met |
|-----|---------|------------|-------|-------|-----------|
| trace_completeness | 100.00% | N/A | N/A | 99.00% | ✅ |
| tool_call_precision | 100.00% | N/A | N/A | 92.00% | ✅ |
| domain_detection_accuracy | 96.97% | N/A | N/A | 85.00% | ✅ |
| compound_classification | 90.91% | N/A | N/A | 80.00% | ✅ |
| step_adequacy | 100.00% | N/A | N/A | 85.00% | ✅ |

## Real-Question Readiness

| Runtime path | Present | Status | Local org | Target | Passed | Failed | Total | Pass rate |
|--------------|---------|--------|-----------|--------|--------|--------|-------|-----------|
| local | ✅ | blocked | 1 | in_process_app | 3 | 11 | 14 | 21.43% |

### Runtime Readiness Notes

- local blockers: observations.empty, bio_gwas_runs.empty, bio_qtls.empty
- local warnings: germplasm.sparse, trials.sparse

## Managed Runtime Preflight

**Status:** `pending_configuration`  
**Counts toward final acceptance:** no  
**Managed target supplied:** not supplied  
**Managed auth token supplied:** no  
**Managed gate outcome:** `not_requested`  
**Managed artifact present:** no  

Managed runtime evaluation is pending configuration because no managed base URL was supplied for this acceptance run.

## Local Readiness Census

**Selection mode:** `default`  
**Selected local org:** 1  
**Organizations scanned:** 2  
**Benchmark-ready local orgs:** 2 (Demo Organization), demo dataset

### Local Selection Guidance

- Benchmark-ready local coverage currently comes from demo-dataset tenant(s): 2 (Demo Organization). The canonical demo dataset is isolated from production and staging; do not mirror demo-seeded benchmark data into selected non-demo organization 1 (Default Organization). Use the ready demo tenant for supplementary local executor verification or provision authoritative data for the selected organization.

### Local Remediation Guidance

- observations.empty: Provision authoritative observations for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=observation.
- bio_gwas_runs.empty: Persist authoritative GWAS runs for the selected organization through the authenticated GWAS execution surface at /api/v2/bio-analytics/gwas/run using authoritative genotype and phenotype inputs.
- bio_qtls.empty: Provision authoritative BioQTL rows for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=qtl.
- germplasm.sparse: Expand authoritative germplasm coverage for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=germplasm.
- trials.sparse: Expand authoritative trial coverage for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=trial.

| Org ID | Name | Selected | Status | Blockers | Warnings |
|--------|------|----------|--------|----------|----------|
| 1 | Default Organization | ✅ | blocked | observations.empty, bio_gwas_runs.empty, bio_qtls.empty | germplasm.sparse, trials.sparse |
| 2 | Demo Organization |  | ready | none | trials.sparse |

## Authority-Gap Report

**Overall gap status:** `selected_local_org_blocked`  
**Selected local org:** 1  
**Organizations scanned:** 2  
**Common blockers across blocked orgs:** bio_gwas_runs.empty, bio_qtls.empty, observations.empty

### Authority-Gap Selection Guidance

- Benchmark-ready local coverage currently comes from demo-dataset tenant(s): 2 (Demo Organization). The canonical demo dataset is isolated from production and staging; do not mirror demo-seeded benchmark data into selected non-demo organization 1 (Default Organization). Use the ready demo tenant for supplementary local executor verification or provision authoritative data for the selected organization.

### Authority-Gap Remediation Guidance

- observations.empty: Provision authoritative observations for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=observation.
- bio_gwas_runs.empty: Persist authoritative GWAS runs for the selected organization through the authenticated GWAS execution surface at /api/v2/bio-analytics/gwas/run using authoritative genotype and phenotype inputs.
- bio_qtls.empty: Provision authoritative BioQTL rows for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=qtl.
- germplasm.sparse: Expand authoritative germplasm coverage for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=germplasm.
- trials.sparse: Expand authoritative trial coverage for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=trial.

| Surface | Trust | Failed | Total | Gap status | Common blockers |
|---------|-------|--------|-------|------------|-----------------|
| Breeding germplasm detail | trusted | 1 | 2 | blocked_selected_local_org | bio_gwas_runs.empty, bio_qtls.empty, observations.empty |
| Breeding phenotype summary and comparison | trusted | 2 | 2 | blocked_selected_local_org | bio_gwas_runs.empty, bio_qtls.empty, observations.empty |
| Trial summary and ranking | trusted | 2 | 3 | blocked_selected_local_org | bio_gwas_runs.empty, bio_qtls.empty, observations.empty |
| Genomics marker and QTL lookup | trusted | 1 | 1 | blocked_selected_local_org | bio_gwas_runs.empty, bio_qtls.empty, observations.empty |
| Deterministic breeding-value compute | trusted | 1 | 1 | blocked_selected_local_org | bio_gwas_runs.empty, bio_qtls.empty, observations.empty |
| Cross-domain orchestration | trusted | 4 | 5 | blocked_selected_local_org | bio_gwas_runs.empty, bio_qtls.empty, observations.empty |
| Weather enrichment inside cross-domain queries | partial | 1 | 1 | blocked_selected_local_org | bio_gwas_runs.empty, bio_qtls.empty, observations.empty |
| Speed-breeding protocol enrichment inside cross-domain queries | partial | 1 | 1 | blocked_selected_local_org | bio_gwas_runs.empty, bio_qtls.empty, observations.empty |

### Failed Case Attribution

- Breeding germplasm detail: rq-01: function_result / insufficient_retrieval_scope ; missing specific germplasm identifier ; searched germplasm_lookup, germplasm_search_service ; attribution selected_local_org_readiness_warning ; relevant warnings germplasm.sparse ; The selected local organization is sparse on benchmark-relevant data surfaces for the expected REEVU domains in this case.
- Breeding phenotype summary and comparison: rq-02: function_result / insufficient_retrieval_scope ; missing resolvable germplasm identifiers ; searched phenotype_comparison.statistics, germplasm_search_service ; attribution selected_local_org_readiness_blocker ; relevant blockers observations.empty ; relevant warnings germplasm.sparse ; The selected local organization is blocked on benchmark-relevant data surfaces for the expected REEVU domains in this case.
- Breeding phenotype summary and comparison: rq-03: function_result / insufficient_retrieval_scope ; missing at least two resolvable germplasm identifiers ; searched phenotype_comparison.compare, germplasm_search_service ; attribution selected_local_org_readiness_blocker ; relevant blockers observations.empty ; relevant warnings germplasm.sparse ; The selected local organization is blocked on benchmark-relevant data surfaces for the expected REEVU domains in this case.
- Trial summary and ranking: rq-04: function_result / insufficient_retrieval_scope ; missing specific trial identifier ; searched trial_summary, trial_search_service ; attribution selected_local_org_readiness_warning ; relevant warnings trials.sparse ; The selected local organization is sparse on benchmark-relevant data surfaces for the expected REEVU domains in this case.
- Trial summary and ranking: rq-05: function_result / insufficient_retrieval_scope ; missing specific trial identifier ; searched trial_summary, trial_search_service ; attribution selected_local_org_readiness_warning ; relevant warnings trials.sparse ; The selected local organization is sparse on benchmark-relevant data surfaces for the expected REEVU domains in this case.
- Genomics marker and QTL lookup: rq-06: function_result / insufficient_retrieval_scope ; missing single authoritative genomics trait ; searched QTLMappingService.get_traits, QTLMappingService.get_gwas_results ; attribution selected_local_org_readiness_blocker ; relevant blockers bio_gwas_runs.empty, bio_qtls.empty ; The selected local organization is blocked on benchmark-relevant data surfaces for the expected REEVU domains in this case.
- Deterministic breeding-value compute: rq-07: function_result / insufficient_compute_inputs ; attribution selected_local_org_readiness_blocker ; relevant blockers observations.empty ; The selected local organization is blocked on benchmark-relevant data surfaces for the expected REEVU domains in this case.
- Cross-domain orchestration: rq-08: function_result / insufficient_retrieval_scope ; missing breeding ; searched germplasm_search_service.search, trait_search_service.search, trial_search_service.search ; attribution selected_local_org_readiness_warning ; relevant warnings germplasm.sparse, trials.sparse ; The selected local organization is sparse on benchmark-relevant data surfaces for the expected REEVU domains in this case.
- Cross-domain orchestration: rq-09: function_result / insufficient_retrieval_scope ; missing genomics, breeding, analytics ; searched germplasm_search_service.search, trait_search_service.search, QTLMappingService.get_traits, QTLMappingService.list_qtls, QTLMappingService.get_gwas_results ; attribution selected_local_org_readiness_blocker ; relevant blockers bio_gwas_runs.empty, bio_qtls.empty ; relevant warnings germplasm.sparse ; The selected local organization is blocked on benchmark-relevant data surfaces for the expected REEVU domains in this case.
- Cross-domain orchestration: rq-10: function_result / insufficient_retrieval_scope ; missing weather, trials, breeding, analytics ; searched germplasm_search_service.search, trial_search_service.search, weather_location_coordinate_resolution, observation_search_service.search ; attribution selected_local_org_readiness_blocker ; relevant blockers observations.empty ; relevant warnings trials.sparse ; The selected local organization is blocked on benchmark-relevant data surfaces for the expected REEVU domains in this case. Unmapped expected domains: weather.
- Cross-domain orchestration: rq-11: function_result / insufficient_retrieval_scope ; missing breeding, protocols, analytics ; searched germplasm_search_service.search, trait_search_service.search, speed_breeding_service.get_protocols ; attribution selected_local_org_readiness_blocker ; relevant blockers observations.empty ; relevant warnings germplasm.sparse ; The selected local organization is blocked on benchmark-relevant data surfaces for the expected REEVU domains in this case.
- Weather enrichment inside cross-domain queries: rq-10: function_result / insufficient_retrieval_scope ; missing weather, trials, breeding, analytics ; searched germplasm_search_service.search, trial_search_service.search, weather_location_coordinate_resolution, observation_search_service.search ; attribution selected_local_org_readiness_blocker ; relevant blockers observations.empty ; relevant warnings trials.sparse ; The selected local organization is blocked on benchmark-relevant data surfaces for the expected REEVU domains in this case. Unmapped expected domains: weather.
- Speed-breeding protocol enrichment inside cross-domain queries: rq-11: function_result / insufficient_retrieval_scope ; missing breeding, protocols, analytics ; searched germplasm_search_service.search, trait_search_service.search, speed_breeding_service.get_protocols ; attribution selected_local_org_readiness_blocker ; relevant blockers observations.empty ; relevant warnings germplasm.sparse ; The selected local organization is blocked on benchmark-relevant data surfaces for the expected REEVU domains in this case.

## Artifact Integrity

**All artifacts valid:** ✅ yes

| Artifact | Exists | Valid | Details |
|----------|--------|-------|---------|
| trace_completeness_baseline | ✅ | ✅ | valid JSON |
| top_intent_routing_baseline | ✅ | ✅ | valid JSON |
| stage_a_kpi_report | ✅ | ✅ | valid JSON |
| cross_domain_reasoning_baseline | ✅ | ✅ | valid JSON |
| real_question_local | ✅ | ✅ | valid JSON |
| ops_report_json | ✅ | ✅ | valid JSON |
| ops_report_markdown | ✅ | ✅ | non-empty text |
| local_readiness_census | ✅ | ✅ | valid JSON |
| authority_gap_report | ✅ | ✅ | valid JSON |

## Explicit Blockers

- Managed runtime evaluation is pending configuration: supply a managed base URL and rerun the managed real-question benchmark before final acceptance.
- Selected local runtime organization 1 is not benchmark-ready: observations.empty, bio_gwas_runs.empty, bio_qtls.empty. Benchmark-ready local organizations discovered: 2 (Demo Organization), demo dataset. Benchmark-ready local coverage currently comes from demo-dataset tenant(s): 2 (Demo Organization). The canonical demo dataset is isolated from production and staging; do not mirror demo-seeded benchmark data into selected non-demo organization 1 (Default Organization). Use the ready demo tenant for supplementary local executor verification or provision authoritative data for the selected organization. Recommended remediation: observations.empty: Provision authoritative observations for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=observation. bio_gwas_runs.empty: Persist authoritative GWAS runs for the selected organization through the authenticated GWAS execution surface at /api/v2/bio-analytics/gwas/run using authoritative genotype and phenotype inputs. bio_qtls.empty: Provision authoritative BioQTL rows for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=qtl. germplasm.sparse: Expand authoritative germplasm coverage for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=germplasm. trials.sparse: Expand authoritative trial coverage for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=trial.

## Risk Notes (Placeholder)

- [ ] Add operational and release risk notes.

## Rollback Checklist (Placeholder)

- [ ] Revert `backend/scripts/generate_reevu_acceptance_pack.py` if acceptance format is unsuitable.
- [ ] Revert generated acceptance artifacts under `backend/test_reports/`.
- [ ] Revert generated summary doc under `docs/development/reevu/`.

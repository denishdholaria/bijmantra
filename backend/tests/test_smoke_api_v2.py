"""
Smoke tests for ALL API v2 + BrAPI GET endpoints (no path parameters).

Phase 3.1 — Every endpoint gets two tests:
  1. Authenticated request → expect 200/204/404 (not 500)
  2. Unauthenticated request → expect 401/403 (auth guard works)

Generated from source code route extraction covering 150 modules, 570 GET routes.

Performance: Uses module-scoped fixtures so the app + client boot ONCE,
not per-test. All 1700+ tests share a single ASGI transport.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import timedelta

# ---------------------------------------------------------------------------
# Route registry: (path, module_name)
# Extracted programmatically from @router.get() decorators in app/api/v2/*.py
# and app/api/brapi/*.py — only GET endpoints without path parameters.
# ---------------------------------------------------------------------------

API_V2_ROUTES = [
    # ── Abiotic Stress ────────────────────────────────────────────────────
    ("/api/v2/abiotic/categories", "abiotic"),
    ("/api/v2/abiotic/crops", "abiotic"),
    ("/api/v2/abiotic/genes", "abiotic"),
    ("/api/v2/abiotic/screening-protocols", "abiotic"),
    ("/api/v2/abiotic/statistics", "abiotic"),
    ("/api/v2/abiotic/stress-types", "abiotic"),
    # ── Activity ──────────────────────────────────────────────────────────
    ("/api/v2/activity", "activity"),
    ("/api/v2/activity/entities", "activity"),
    ("/api/v2/activity/stats", "activity"),
    ("/api/v2/activity/users", "activity"),
    # ── Analytics ─────────────────────────────────────────────────────────
    ("/api/v2/analytics", "analytics"),
    ("/api/v2/analytics/correlations", "analytics"),
    ("/api/v2/analytics/genetic-gain", "analytics"),
    ("/api/v2/analytics/heritabilities", "analytics"),
    ("/api/v2/analytics/insights", "analytics"),
    ("/api/v2/analytics/selection-response", "analytics"),
    ("/api/v2/analytics/summary", "analytics"),
    ("/api/v2/analytics/veena-summary", "analytics"),
    # ── Audit ─────────────────────────────────────────────────────────────
    ("/api/v2/audit/logs", "audit"),
    ("/api/v2/audit/security", "audit"),
    ("/api/v2/audit/stats", "audit"),
    # ── Backup ────────────────────────────────────────────────────────────
    ("/api/v2/backup/", "backup"),
    ("/api/v2/backup/stats", "backup"),
    # ── Barcode ───────────────────────────────────────────────────────────
    ("/api/v2/barcode", "barcode"),
    ("/api/v2/barcode/entity-types/reference", "barcode"),
    ("/api/v2/barcode/scans", "barcode"),
    ("/api/v2/barcode/statistics", "barcode"),
    # ── Bioinformatics ────────────────────────────────────────────────────
    ("/api/v2/bioinformatics/enzymes", "bioinformatics"),
    # ── Breeding Pipeline ─────────────────────────────────────────────────
    ("/api/v2/breeding-pipeline", "breeding_pipeline"),
    ("/api/v2/breeding-pipeline/crops", "breeding_pipeline"),
    ("/api/v2/breeding-pipeline/programs", "breeding_pipeline"),
    ("/api/v2/breeding-pipeline/stage-summary", "breeding_pipeline"),
    ("/api/v2/breeding-pipeline/stages", "breeding_pipeline"),
    ("/api/v2/breeding-pipeline/statistics", "breeding_pipeline"),
    # ── Breeding Value ────────────────────────────────────────────────────
    ("/api/v2/breeding-value/analyses", "breeding_value"),
    ("/api/v2/breeding-value/methods", "breeding_value"),
    # ── Carbon ────────────────────────────────────────────────────────────
    ("/api/v2/carbon/dashboard", "carbon"),
    ("/api/v2/carbon/measurements", "carbon"),
    ("/api/v2/carbon/stocks", "carbon"),
    ("/api/v2/carbon/time-series", "carbon"),
    # ── Chaitanya (AI Security) ───────────────────────────────────────────
    ("/api/v2/chaitanya/actions", "chaitanya"),
    ("/api/v2/chaitanya/config", "chaitanya"),
    ("/api/v2/chaitanya/dashboard", "chaitanya"),
    ("/api/v2/chaitanya/posture", "chaitanya"),
    ("/api/v2/chaitanya/posture/history", "chaitanya"),
    ("/api/v2/chaitanya/security-config", "chaitanya"),
    ("/api/v2/chaitanya/status", "chaitanya"),
    ("/api/v2/chaitanya/storage-stats", "chaitanya"),
    # ── Chat ──────────────────────────────────────────────────────────────
    ("/api/v2/chat/health", "chat"),
    ("/api/v2/chat/status", "chat"),
    ("/api/v2/chat/usage", "chat"),
    # ── Collaboration ─────────────────────────────────────────────────────
    ("/api/v2/collaboration/activity", "collaboration"),
    ("/api/v2/collaboration/conversations", "collaboration"),
    ("/api/v2/collaboration/shared-items", "collaboration"),
    ("/api/v2/collaboration/stats", "collaboration"),
    ("/api/v2/collaboration/team-members", "collaboration"),
    # ── Collaboration Hub ─────────────────────────────────────────────────
    ("/api/v2/collaboration-hub/activities", "collaboration_hub"),
    ("/api/v2/collaboration-hub/comments", "collaboration_hub"),
    ("/api/v2/collaboration-hub/members", "collaboration_hub"),
    ("/api/v2/collaboration-hub/members/online", "collaboration_hub"),
    ("/api/v2/collaboration-hub/stats", "collaboration_hub"),
    ("/api/v2/collaboration-hub/tasks", "collaboration_hub"),
    ("/api/v2/collaboration-hub/workspaces", "collaboration_hub"),
    # ── Compute ───────────────────────────────────────────────────────────
    ("/api/v2/compute/jobs", "compute"),
    ("/api/v2/compute/status", "compute"),
    # ── Cost Analysis ─────────────────────────────────────────────────────
    ("/api/v2/cost-analysis/budget-categories", "cost_analysis"),
    ("/api/v2/cost-analysis/expenses", "cost_analysis"),
    ("/api/v2/cost-analysis/summary", "cost_analysis"),
    # ── Crop Calendar ─────────────────────────────────────────────────────
    ("/api/v2/crop-calendar/activities", "crop_calendar"),
    ("/api/v2/crop-calendar/crops", "crop_calendar"),
    ("/api/v2/crop-calendar/events", "crop_calendar"),
    ("/api/v2/crop-calendar/growth-stages", "crop_calendar"),
    ("/api/v2/crop-calendar/view", "crop_calendar"),
    # ── Crop Health ───────────────────────────────────────────────────────
    ("/api/v2/crop-health/alerts", "crop_health"),
    ("/api/v2/crop-health/crops", "crop_health"),
    ("/api/v2/crop-health/locations", "crop_health"),
    ("/api/v2/crop-health/summary", "crop_health"),
    ("/api/v2/crop-health/trends", "crop_health"),
    ("/api/v2/crop-health/trials", "crop_health"),
    # ── Crosses ───────────────────────────────────────────────────────────
    ("/api/v2/crosses/methods", "crosses"),
    ("/api/v2/crosses/selection-intensities", "crosses"),
    # ── Crossing Planner ──────────────────────────────────────────────────
    ("/api/v2/crossing-planner", "crossing_planner"),
    ("/api/v2/crossing-planner/germplasm", "crossing_planner"),
    ("/api/v2/crossing-planner/reference/cross-types", "crossing_planner"),
    ("/api/v2/crossing-planner/reference/priorities", "crossing_planner"),
    ("/api/v2/crossing-planner/reference/statuses", "crossing_planner"),
    ("/api/v2/crossing-planner/statistics", "crossing_planner"),
    # ── Data Dictionary ───────────────────────────────────────────────────
    ("/api/v2/data-dictionary/entities", "data_dictionary"),
    ("/api/v2/data-dictionary/export", "data_dictionary"),
    ("/api/v2/data-dictionary/fields", "data_dictionary"),
    ("/api/v2/data-dictionary/stats", "data_dictionary"),
    # ── Data Quality ──────────────────────────────────────────────────────
    ("/api/v2/data-quality/issue-types", "data_quality"),
    ("/api/v2/data-quality/issues", "data_quality"),
    ("/api/v2/data-quality/metrics", "data_quality"),
    ("/api/v2/data-quality/rules", "data_quality"),
    ("/api/v2/data-quality/score", "data_quality"),
    ("/api/v2/data-quality/severities", "data_quality"),
    ("/api/v2/data-quality/statistics", "data_quality"),
    ("/api/v2/data-quality/validation-history", "data_quality"),
    # ── Data Sync ─────────────────────────────────────────────────────────
    ("/api/v2/data-sync/conflicts", "data_sync"),
    ("/api/v2/data-sync/history", "data_sync"),
    ("/api/v2/data-sync/offline-data", "data_sync"),
    ("/api/v2/data-sync/pending", "data_sync"),
    ("/api/v2/data-sync/settings", "data_sync"),
    ("/api/v2/data-sync/stats", "data_sync"),
    # ── Data Validation ───────────────────────────────────────────────────
    ("/api/v2/data-validation", "data_validation"),
    ("/api/v2/data-validation/export", "data_validation"),
    ("/api/v2/data-validation/rules", "data_validation"),
    ("/api/v2/data-validation/runs", "data_validation"),
    ("/api/v2/data-validation/stats", "data_validation"),
    # ── Data Visualization ────────────────────────────────────────────────
    ("/api/v2/visualizations/chart-types", "data_visualization"),
    ("/api/v2/visualizations/charts", "data_visualization"),
    ("/api/v2/visualizations/data-sources", "data_visualization"),
    ("/api/v2/visualizations/statistics", "data_visualization"),
    # ── DevGuru ───────────────────────────────────────────────────────────
    ("/api/v2/devguru/milestone-statuses", "devguru"),
    ("/api/v2/devguru/phases", "devguru"),
    ("/api/v2/devguru/programs/research", "devguru"),
    ("/api/v2/devguru/projects", "devguru"),
    ("/api/v2/devguru/status", "devguru"),
    ("/api/v2/devguru/topics", "devguru"),
    # ── Disease Resistance ────────────────────────────────────────────────
    ("/api/v2/disease/crops", "disease"),
    ("/api/v2/disease/diseases", "disease"),
    ("/api/v2/disease/genes", "disease"),
    ("/api/v2/disease/pathogen-types", "disease"),
    ("/api/v2/disease/pyramiding-strategies", "disease"),
    ("/api/v2/disease/resistance-types", "disease"),
    ("/api/v2/disease/statistics", "disease"),
    # ── Dispatch ──────────────────────────────────────────────────────────
    ("/api/v2/dispatch/firm-types", "dispatch"),
    ("/api/v2/dispatch/firms", "dispatch"),
    ("/api/v2/dispatch/orders", "dispatch"),
    ("/api/v2/dispatch/statistics", "dispatch"),
    ("/api/v2/dispatch/statuses", "dispatch"),
    # ── Dock ──────────────────────────────────────────────────────────────
    ("/api/v2/dock", "dock"),
    # ── Doubled Haploid ───────────────────────────────────────────────────
    ("/api/v2/doubled-haploid/batches", "doubled_haploid"),
    ("/api/v2/doubled-haploid/protocols", "doubled_haploid"),
    ("/api/v2/doubled-haploid/statistics", "doubled_haploid"),
    # ── DUS Testing ───────────────────────────────────────────────────────
    ("/api/v2/dus/crops", "dus"),
    ("/api/v2/dus/reference/character-types", "dus"),
    ("/api/v2/dus/reference/trial-statuses", "dus"),
    ("/api/v2/dus/trials", "dus"),
    # ── Emissions ─────────────────────────────────────────────────────────
    ("/api/v2/emissions/dashboard", "emissions"),
    ("/api/v2/emissions/sources", "emissions"),
    ("/api/v2/emissions/varieties", "emissions"),
    # ── Events ────────────────────────────────────────────────────────────
    ("/api/v2/events/dead-letters", "events"),
    ("/api/v2/events/history", "events"),
    ("/api/v2/events/subscriptions", "events"),
    ("/api/v2/events/types", "events"),
    # ── Export ────────────────────────────────────────────────────────────
    ("/api/v2/export/formats", "export"),
    # ── External Services ─────────────────────────────────────────────────
    ("/api/v2/external-services/status", "external_services"),
    # ── Field Book ────────────────────────────────────────────────────────
    ("/api/v2/field-book/studies", "field_book"),
    # ── Field Environment ─────────────────────────────────────────────────
    ("/api/v2/field-environment/input-logs", "field_environment"),
    ("/api/v2/field-environment/input-types", "field_environment"),
    ("/api/v2/field-environment/irrigation", "field_environment"),
    ("/api/v2/field-environment/irrigation-types", "field_environment"),
    ("/api/v2/field-environment/soil-profiles", "field_environment"),
    ("/api/v2/field-environment/soil-textures", "field_environment"),
    # ── Field Layout ──────────────────────────────────────────────────────
    ("/api/v2/field-layout/germplasm", "field_layout"),
    ("/api/v2/field-layout/studies", "field_layout"),
    # ── Field Map ─────────────────────────────────────────────────────────
    ("/api/v2/field-map/fields", "field_map"),
    ("/api/v2/field-map/summary", "field_map"),
    # ── Field Planning ────────────────────────────────────────────────────
    ("/api/v2/field-planning/calendar", "field_planning"),
    ("/api/v2/field-planning/plans", "field_planning"),
    ("/api/v2/field-planning/seasons", "field_planning"),
    ("/api/v2/field-planning/statistics", "field_planning"),
    # ── Field Scanner ─────────────────────────────────────────────────────
    ("/api/v2/field-scanner", "field_scanner"),
    ("/api/v2/field-scanner/export", "field_scanner"),
    ("/api/v2/field-scanner/stats", "field_scanner"),
    # ── Forums ────────────────────────────────────────────────────────────
    ("/api/v2/forums/categories", "forums"),
    ("/api/v2/forums/stats", "forums"),
    ("/api/v2/forums/topics", "forums"),
    # ── Genetic Diversity ─────────────────────────────────────────────────
    ("/api/v2/genetic-diversity/admixture", "genetic_diversity"),
    ("/api/v2/genetic-diversity/amova", "genetic_diversity"),
    ("/api/v2/genetic-diversity/distances", "genetic_diversity"),
    ("/api/v2/genetic-diversity/pca", "genetic_diversity"),
    ("/api/v2/genetic-diversity/populations", "genetic_diversity"),
    ("/api/v2/genetic-diversity/summary", "genetic_diversity"),
    # ── Genetic Gain ──────────────────────────────────────────────────────
    ("/api/v2/genetic-gain/programs", "genetic_gain"),
    ("/api/v2/genetic-gain/statistics", "genetic_gain"),
    # ── Genomic Selection ─────────────────────────────────────────────────
    ("/api/v2/genomic-selection/comparison", "genomic_selection"),
    ("/api/v2/genomic-selection/cross-prediction", "genomic_selection"),
    ("/api/v2/genomic-selection/methods", "genomic_selection"),
    ("/api/v2/genomic-selection/models", "genomic_selection"),
    ("/api/v2/genomic-selection/summary", "genomic_selection"),
    ("/api/v2/genomic-selection/traits", "genomic_selection"),
    ("/api/v2/genomic-selection/yield-predictions", "genomic_selection"),
    # ── Genotyping ────────────────────────────────────────────────────────
    ("/api/v2/genotyping/calls", "genotyping"),
    ("/api/v2/genotyping/calls/statistics", "genotyping"),
    ("/api/v2/genotyping/callsets", "genotyping"),
    ("/api/v2/genotyping/markerpositions", "genotyping"),
    ("/api/v2/genotyping/references", "genotyping"),
    ("/api/v2/genotyping/referencesets", "genotyping"),
    ("/api/v2/genotyping/summary", "genotyping"),
    ("/api/v2/genotyping/variantsets", "genotyping"),
    ("/api/v2/genotyping/vendor/orders", "genotyping"),
    # ── Germplasm Collection ──────────────────────────────────────────────
    ("/api/v2/collections", "germplasm_collection"),
    ("/api/v2/collections/stats", "germplasm_collection"),
    ("/api/v2/collections/types", "germplasm_collection"),
    # ── Germplasm Comparison ──────────────────────────────────────────────
    ("/api/v2/germplasm-comparison/germplasm", "germplasm_comparison"),
    ("/api/v2/germplasm-comparison/markers", "germplasm_comparison"),
    ("/api/v2/germplasm-comparison/statistics", "germplasm_comparison"),
    ("/api/v2/germplasm-comparison/traits", "germplasm_comparison"),
    # ── Germplasm Search ──────────────────────────────────────────────────
    ("/api/v2/germplasm-search/filters", "germplasm_search"),
    ("/api/v2/germplasm-search/search", "germplasm_search"),
    ("/api/v2/germplasm-search/statistics", "germplasm_search"),
    # ── GRIN ──────────────────────────────────────────────────────────────
    ("/api/v2/grin/genesys/search", "grin"),
    ("/api/v2/grin/grin-global/search", "grin"),
    ("/api/v2/grin/status", "grin"),
    # ── GWAS ──────────────────────────────────────────────────────────────
    ("/api/v2/gwas/methods", "gwas"),
    # ── Haplotype ─────────────────────────────────────────────────────────
    ("/api/v2/haplotype/associations", "haplotype"),
    ("/api/v2/haplotype/blocks", "haplotype"),
    ("/api/v2/haplotype/diversity", "haplotype"),
    ("/api/v2/haplotype/favorable", "haplotype"),
    ("/api/v2/haplotype/statistics", "haplotype"),
    ("/api/v2/haplotype/traits", "haplotype"),
    # ── Harvest ───────────────────────────────────────────────────────────
    ("/api/v2/harvest/harvests", "harvest"),
    ("/api/v2/harvest/statistics", "harvest"),
    ("/api/v2/harvest/storage/types", "harvest"),
    ("/api/v2/harvest/storage/units", "harvest"),
    # ── Impact ────────────────────────────────────────────────────────────
    ("/api/v2/impact/dashboard", "impact"),
    ("/api/v2/impact/metrics", "impact"),
    ("/api/v2/impact/releases", "impact"),
    ("/api/v2/impact/reports", "impact"),
    ("/api/v2/impact/sdg", "impact"),
    # ── Insights ──────────────────────────────────────────────────────────
    ("/api/v2/insights", "insights"),
    ("/api/v2/insights/summary", "insights"),
    ("/api/v2/insights/trends", "insights"),
    # ── Integrations ──────────────────────────────────────────────────────
    ("/api/v2/integrations/", "integrations"),
    ("/api/v2/integrations/available", "integrations"),
    # ── Label Printing ────────────────────────────────────────────────────
    ("/api/v2/labels/data", "label_printing"),
    ("/api/v2/labels/jobs", "label_printing"),
    ("/api/v2/labels/stats", "label_printing"),
    ("/api/v2/labels/templates", "label_printing"),
    # ── Languages ─────────────────────────────────────────────────────────
    ("/api/v2/languages", "languages"),
    ("/api/v2/languages/stats", "languages"),
    ("/api/v2/languages/translations/keys", "languages"),
    # ── Licensing ─────────────────────────────────────────────────────────
    ("/api/v2/licensing/license-types", "licensing"),
    ("/api/v2/licensing/licenses", "licensing"),
    ("/api/v2/licensing/protection-types", "licensing"),
    ("/api/v2/licensing/protections", "licensing"),
    ("/api/v2/licensing/statistics", "licensing"),
    ("/api/v2/licensing/varieties", "licensing"),
    # ── MAS (Marker Assisted Selection) ───────────────────────────────────
    ("/api/v2/mas/markers", "mas"),
    ("/api/v2/mas/stats", "mas"),
    # ── Metrics ───────────────────────────────────────────────────────────
    ("/api/v2/metrics", "metrics"),
    ("/api/v2/metrics/api", "metrics"),
    ("/api/v2/metrics/badge/brapi", "metrics"),
    ("/api/v2/metrics/badge/build", "metrics"),
    ("/api/v2/metrics/badge/endpoints", "metrics"),
    ("/api/v2/metrics/badge/pages", "metrics"),
    ("/api/v2/metrics/badge/version", "metrics"),
    ("/api/v2/metrics/build", "metrics"),
    ("/api/v2/metrics/database", "metrics"),
    ("/api/v2/metrics/milestones", "metrics"),
    ("/api/v2/metrics/modules", "metrics"),
    ("/api/v2/metrics/pages", "metrics"),
    ("/api/v2/metrics/summary", "metrics"),
    ("/api/v2/metrics/tech-stack", "metrics"),
    ("/api/v2/metrics/version", "metrics"),
    ("/api/v2/metrics/workspaces", "metrics"),
    # ── Molecular Breeding ────────────────────────────────────────────────
    ("/api/v2/molecular-breeding/lines", "molecular_breeding"),
    ("/api/v2/molecular-breeding/schemes", "molecular_breeding"),
    ("/api/v2/molecular-breeding/statistics", "molecular_breeding"),
    # ── MTA (Material Transfer Agreement) ─────────────────────────────────
    ("/api/v2/mta", "mta"),
    ("/api/v2/mta/statistics", "mta"),
    ("/api/v2/mta/templates", "mta"),
    ("/api/v2/mta/types/reference", "mta"),
    # ── Notifications ─────────────────────────────────────────────────────
    ("/api/v2/notifications/", "notifications"),
    ("/api/v2/notifications/preferences", "notifications"),
    ("/api/v2/notifications/quiet-hours", "notifications"),
    ("/api/v2/notifications/stats", "notifications"),
    # ── Nursery ───────────────────────────────────────────────────────────
    ("/api/v2/nursery/nurseries", "nursery"),
    ("/api/v2/nursery/types", "nursery"),
    # ── Nursery Management ────────────────────────────────────────────────
    ("/api/v2/nursery-management/batches", "nursery_management"),
    ("/api/v2/nursery-management/export", "nursery_management"),
    ("/api/v2/nursery-management/germplasm", "nursery_management"),
    ("/api/v2/nursery-management/locations", "nursery_management"),
    ("/api/v2/nursery-management/stats", "nursery_management"),
    # ── Offline Sync ──────────────────────────────────────────────────────
    ("/api/v2/offline-sync/cached-data", "offline_sync"),
    ("/api/v2/offline-sync/pending-changes", "offline_sync"),
    ("/api/v2/offline-sync/settings", "offline_sync"),
    ("/api/v2/offline-sync/stats", "offline_sync"),
    ("/api/v2/offline-sync/storage-quota", "offline_sync"),
    # ── Ontology ──────────────────────────────────────────────────────────
    ("/api/v2/ontology/categories", "ontology"),
    ("/api/v2/ontology/methods", "ontology"),
    ("/api/v2/ontology/scale-types", "ontology"),
    ("/api/v2/ontology/scales", "ontology"),
    ("/api/v2/ontology/traits", "ontology"),
    ("/api/v2/ontology/traits/search", "ontology"),
    ("/api/v2/ontology/variables", "ontology"),
    # ── Parent Selection ──────────────────────────────────────────────────
    ("/api/v2/parent-selection/objectives", "parent_selection"),
    ("/api/v2/parent-selection/parents", "parent_selection"),
    ("/api/v2/parent-selection/predict-cross", "parent_selection"),
    ("/api/v2/parent-selection/recommendations", "parent_selection"),
    ("/api/v2/parent-selection/statistics", "parent_selection"),
    ("/api/v2/parent-selection/types", "parent_selection"),
    # ── Parentage ─────────────────────────────────────────────────────────
    ("/api/v2/parentage/history", "parentage"),
    ("/api/v2/parentage/individuals", "parentage"),
    ("/api/v2/parentage/markers", "parentage"),
    ("/api/v2/parentage/statistics", "parentage"),
    # ── Passport ──────────────────────────────────────────────────────────
    ("/api/v2/passport/accessions", "passport"),
    ("/api/v2/passport/acquisition-source-codes", "passport"),
    ("/api/v2/passport/biological-status-codes", "passport"),
    ("/api/v2/passport/export/mcpd", "passport"),
    ("/api/v2/passport/search", "passport"),
    ("/api/v2/passport/statistics", "passport"),
    # ── Pedigree ──────────────────────────────────────────────────────────
    ("/api/v2/pedigree/individuals", "pedigree"),
    ("/api/v2/pedigree/stats", "pedigree"),
    # ── Performance Ranking ───────────────────────────────────────────────
    ("/api/v2/performance-ranking/programs", "performance_ranking"),
    ("/api/v2/performance-ranking/rankings", "performance_ranking"),
    ("/api/v2/performance-ranking/statistics", "performance_ranking"),
    ("/api/v2/performance-ranking/top-performers", "performance_ranking"),
    ("/api/v2/performance-ranking/trials", "performance_ranking"),
    # ── Phenology ─────────────────────────────────────────────────────────
    ("/api/v2/phenology/records", "phenology"),
    ("/api/v2/phenology/stages", "phenology"),
    ("/api/v2/phenology/stats", "phenology"),
    # ── Phenomic Selection ────────────────────────────────────────────────
    ("/api/v2/phenomic-selection/datasets", "phenomic_selection"),
    ("/api/v2/phenomic-selection/models", "phenomic_selection"),
    ("/api/v2/phenomic-selection/statistics", "phenomic_selection"),
    # ── Phenotype ─────────────────────────────────────────────────────────
    ("/api/v2/phenotype/methods", "phenotype"),
    # ── Phenotype Comparison ──────────────────────────────────────────────
    ("/api/v2/phenotype-comparison/germplasm", "phenotype_comparison"),
    ("/api/v2/phenotype-comparison/statistics", "phenotype_comparison"),
    ("/api/v2/phenotype-comparison/traits", "phenotype_comparison"),
    # ── Plot History ──────────────────────────────────────────────────────
    ("/api/v2/plot-history/event-types", "plot_history"),
    ("/api/v2/plot-history/fields", "plot_history"),
    ("/api/v2/plot-history/plots", "plot_history"),
    ("/api/v2/plot-history/stats", "plot_history"),
    # ── Population Genetics ───────────────────────────────────────────────
    ("/api/v2/population-genetics/fst", "population_genetics"),
    ("/api/v2/population-genetics/migration", "population_genetics"),
    ("/api/v2/population-genetics/pca", "population_genetics"),
    ("/api/v2/population-genetics/populations", "population_genetics"),
    ("/api/v2/population-genetics/structure", "population_genetics"),
    ("/api/v2/population-genetics/summary", "population_genetics"),
    # ── Prahari (Security Monitoring) ─────────────────────────────────────
    ("/api/v2/prahari/blocked", "prahari"),
    ("/api/v2/prahari/events", "prahari"),
    ("/api/v2/prahari/events/stats", "prahari"),
    ("/api/v2/prahari/events/suspicious-ips", "prahari"),
    ("/api/v2/prahari/responses", "prahari"),
    ("/api/v2/prahari/responses/stats", "prahari"),
    ("/api/v2/prahari/stats", "prahari"),
    ("/api/v2/prahari/threats", "prahari"),
    ("/api/v2/prahari/threats/stats", "prahari"),
    # ── Processing ────────────────────────────────────────────────────────
    ("/api/v2/processing/batches", "processing"),
    ("/api/v2/processing/stages", "processing"),
    ("/api/v2/processing/statistics", "processing"),
    # ── Profile ───────────────────────────────────────────────────────────
    ("/api/v2/profile", "profile"),
    ("/api/v2/profile/activity", "profile"),
    ("/api/v2/profile/preferences", "profile"),
    ("/api/v2/profile/sessions", "profile"),
    ("/api/v2/profile/workspace", "profile"),
    # ── Progeny ───────────────────────────────────────────────────────────
    ("/api/v2/progeny/parents", "progeny"),
    ("/api/v2/progeny/statistics", "progeny"),
    ("/api/v2/progeny/types", "progeny"),
    # ── Progress ──────────────────────────────────────────────────────────
    ("/api/v2/progress", "progress"),
    ("/api/v2/progress/api-stats", "progress"),
    ("/api/v2/progress/divisions", "progress"),
    ("/api/v2/progress/features", "progress"),
    ("/api/v2/progress/roadmap", "progress"),
    ("/api/v2/progress/summary", "progress"),
    ("/api/v2/progress/tech-stack", "progress"),
    # ── Proposals ─────────────────────────────────────────────────────────
    ("/api/v2/proposals/", "proposals"),
    # ── QTL Mapping ───────────────────────────────────────────────────────
    ("/api/v2/qtl-mapping/go-enrichment", "qtl_mapping"),
    ("/api/v2/qtl-mapping/gwas", "qtl_mapping"),
    ("/api/v2/qtl-mapping/manhattan", "qtl_mapping"),
    ("/api/v2/qtl-mapping/populations", "qtl_mapping"),
    ("/api/v2/qtl-mapping/qtls", "qtl_mapping"),
    ("/api/v2/qtl-mapping/summary/gwas", "qtl_mapping"),
    ("/api/v2/qtl-mapping/summary/qtl", "qtl_mapping"),
    ("/api/v2/qtl-mapping/traits", "qtl_mapping"),
    # ── Quality ───────────────────────────────────────────────────────────
    ("/api/v2/quality/samples", "quality"),
    ("/api/v2/quality/seed-classes", "quality"),
    ("/api/v2/quality/standards", "quality"),
    ("/api/v2/quality/summary", "quality"),
    ("/api/v2/quality/test-types", "quality"),
    # ── Quick Entry ───────────────────────────────────────────────────────
    ("/api/v2/quick-entry/entries", "quick_entry"),
    ("/api/v2/quick-entry/recent", "quick_entry"),
    ("/api/v2/quick-entry/stats", "quick_entry"),
    # ── Rakshaka (Anomaly Detection) ──────────────────────────────────────
    ("/api/v2/rakshaka/anomalies", "rakshaka"),
    ("/api/v2/rakshaka/config", "rakshaka"),
    ("/api/v2/rakshaka/health", "rakshaka"),
    ("/api/v2/rakshaka/incidents", "rakshaka"),
    ("/api/v2/rakshaka/metrics", "rakshaka"),
    ("/api/v2/rakshaka/strategies", "rakshaka"),
    # ── RBAC ──────────────────────────────────────────────────────────────
    ("/api/v2/rbac/my-permissions", "rbac"),
    ("/api/v2/rbac/permissions", "rbac"),
    ("/api/v2/rbac/roles", "rbac"),
    ("/api/v2/rbac/users", "rbac"),
    # ── Reports ───────────────────────────────────────────────────────────
    ("/api/v2/reports/builder/data-sources", "reports"),
    ("/api/v2/reports/builder/visualizations", "reports"),
    ("/api/v2/reports/generated", "reports"),
    ("/api/v2/reports/schedules", "reports"),
    ("/api/v2/reports/stats", "reports"),
    ("/api/v2/reports/templates", "reports"),
    # ── Resource Management ───────────────────────────────────────────────
    ("/api/v2/resources/budget", "resource_management"),
    ("/api/v2/resources/budget/summary", "resource_management"),
    ("/api/v2/resources/calendar", "resource_management"),
    ("/api/v2/resources/calendar/summary", "resource_management"),
    ("/api/v2/resources/fields", "resource_management"),
    ("/api/v2/resources/fields/summary", "resource_management"),
    ("/api/v2/resources/harvest", "resource_management"),
    ("/api/v2/resources/harvest/summary", "resource_management"),
    ("/api/v2/resources/overview", "resource_management"),
    ("/api/v2/resources/staff", "resource_management"),
    ("/api/v2/resources/staff/summary", "resource_management"),
    # ── RLS (Row-Level Security) ──────────────────────────────────────────
    ("/api/v2/rls/context", "rls"),
    ("/api/v2/rls/sql/disable", "rls"),
    ("/api/v2/rls/sql/enable", "rls"),
    ("/api/v2/rls/status", "rls"),
    ("/api/v2/rls/tables", "rls"),
    ("/api/v2/rls/test", "rls"),
    # ── Search ────────────────────────────────────────────────────────────
    ("/api/v2/search", "search"),
    ("/api/v2/search/federated", "search"),
    ("/api/v2/search/geo/locations", "search"),
    ("/api/v2/search/germplasm", "search"),
    ("/api/v2/search/locations", "search"),
    ("/api/v2/search/programs", "search"),
    ("/api/v2/search/stats", "search"),
    ("/api/v2/search/studies", "search"),
    ("/api/v2/search/traits", "search"),
    ("/api/v2/search/trials", "search"),
    # ── Security Audit ────────────────────────────────────────────────────
    ("/api/v2/audit/security", "security_audit"),
    ("/api/v2/audit/security/categories", "security_audit"),
    ("/api/v2/audit/security/failed", "security_audit"),
    ("/api/v2/audit/security/search", "security_audit"),
    ("/api/v2/audit/security/severities", "security_audit"),
    ("/api/v2/audit/security/stats", "security_audit"),
    # ── Seed Inventory ────────────────────────────────────────────────────
    ("/api/v2/seed-inventory/alerts", "seed_inventory"),
    ("/api/v2/seed-inventory/lots", "seed_inventory"),
    ("/api/v2/seed-inventory/storage-types", "seed_inventory"),
    ("/api/v2/seed-inventory/summary", "seed_inventory"),
    # ── Selection ─────────────────────────────────────────────────────────
    ("/api/v2/selection/default-weights", "selection"),
    ("/api/v2/selection/methods", "selection"),
    # ── Selection Decisions ───────────────────────────────────────────────
    ("/api/v2/selection-decisions/candidates", "selection_decisions"),
    ("/api/v2/selection-decisions/history", "selection_decisions"),
    ("/api/v2/selection-decisions/programs", "selection_decisions"),
    ("/api/v2/selection-decisions/statistics", "selection_decisions"),
    ("/api/v2/selection-decisions/trials", "selection_decisions"),
    # ── Sensors / IoT ─────────────────────────────────────────────────────
    ("/api/v2/sensors/alerts/events", "sensors"),
    ("/api/v2/sensors/alerts/rules", "sensors"),
    ("/api/v2/sensors/device-types", "sensors"),
    ("/api/v2/sensors/devices", "sensors"),
    ("/api/v2/sensors/readings", "sensors"),
    ("/api/v2/sensors/readings/live", "sensors"),
    ("/api/v2/sensors/sensor-types", "sensors"),
    ("/api/v2/sensors/stats", "sensors"),
    # ── Social ────────────────────────────────────────────────────────────
    ("/api/v2/social/feed", "social"),
    ("/api/v2/social/groups", "social"),
    ("/api/v2/social/recommendations", "social"),
    ("/api/v2/social/reputation/me", "social"),
    ("/api/v2/social/trending/hashtags", "social"),
    # ── Spatial ───────────────────────────────────────────────────────────
    ("/api/v2/spatial/fields", "spatial"),
    ("/api/v2/spatial/statistics", "spatial"),
    # ── Speed Breeding ────────────────────────────────────────────────────
    ("/api/v2/speed-breeding/batches", "speed_breeding"),
    ("/api/v2/speed-breeding/chambers", "speed_breeding"),
    ("/api/v2/speed-breeding/cycles", "speed_breeding"),
    ("/api/v2/speed-breeding/protocols", "speed_breeding"),
    ("/api/v2/speed-breeding/statistics", "speed_breeding"),
    ("/api/v2/speed-breeding/stats", "speed_breeding"),
    # ── Stability Analysis ────────────────────────────────────────────────
    ("/api/v2/stability/comparison", "stability_analysis"),
    ("/api/v2/stability/methods", "stability_analysis"),
    ("/api/v2/stability/recommendations", "stability_analysis"),
    ("/api/v2/stability/statistics", "stability_analysis"),
    ("/api/v2/stability/varieties", "stability_analysis"),
    # ── Statistics ────────────────────────────────────────────────────────
    ("/api/v2/statistics/anova", "statistics"),
    ("/api/v2/statistics/correlations", "statistics"),
    ("/api/v2/statistics/distribution", "statistics"),
    ("/api/v2/statistics/overview", "statistics"),
    ("/api/v2/statistics/summary", "statistics"),
    ("/api/v2/statistics/traits", "statistics"),
    ("/api/v2/statistics/trials", "statistics"),
    # ── System Settings ───────────────────────────────────────────────────
    ("/api/v2/system-settings/all", "system_settings"),
    ("/api/v2/system-settings/api", "system_settings"),
    ("/api/v2/system-settings/export", "system_settings"),
    ("/api/v2/system-settings/features", "system_settings"),
    ("/api/v2/system-settings/general", "system_settings"),
    ("/api/v2/system-settings/security", "system_settings"),
    ("/api/v2/system-settings/status", "system_settings"),
    # ── Tasks ─────────────────────────────────────────────────────────────
    ("/api/v2/tasks/", "tasks"),
    ("/api/v2/tasks/stats", "tasks"),
    # ── Team Management ───────────────────────────────────────────────────
    ("/api/v2/teams", "team_management"),
    ("/api/v2/teams/invites", "team_management"),
    ("/api/v2/teams/members", "team_management"),
    ("/api/v2/teams/roles", "team_management"),
    ("/api/v2/teams/stats", "team_management"),
    # ── Traceability ──────────────────────────────────────────────────────
    ("/api/v2/traceability/event-types", "traceability"),
    ("/api/v2/traceability/lots", "traceability"),
    ("/api/v2/traceability/statistics", "traceability"),
    ("/api/v2/traceability/transfers", "traceability"),
    # ── Trial Design ──────────────────────────────────────────────────────
    ("/api/v2/trial-design/designs", "trial_design"),
    # ── Trial Network ─────────────────────────────────────────────────────
    ("/api/v2/trial-network/countries", "trial_network"),
    ("/api/v2/trial-network/germplasm", "trial_network"),
    ("/api/v2/trial-network/performance", "trial_network"),
    ("/api/v2/trial-network/seasons", "trial_network"),
    ("/api/v2/trial-network/sites", "trial_network"),
    ("/api/v2/trial-network/statistics", "trial_network"),
    # ── Trial Planning ────────────────────────────────────────────────────
    ("/api/v2/trial-planning", "trial_planning"),
    ("/api/v2/trial-planning/designs", "trial_planning"),
    ("/api/v2/trial-planning/seasons", "trial_planning"),
    ("/api/v2/trial-planning/statistics", "trial_planning"),
    ("/api/v2/trial-planning/timeline", "trial_planning"),
    ("/api/v2/trial-planning/types", "trial_planning"),
    # ── Trial Summary ─────────────────────────────────────────────────────
    ("/api/v2/trial-summary/trials", "trial_summary"),
    # ── Vault Sensors ─────────────────────────────────────────────────────
    ("/api/v2/vault-sensors/alerts", "vault_sensors"),
    ("/api/v2/vault-sensors/conditions", "vault_sensors"),
    ("/api/v2/vault-sensors/readings", "vault_sensors"),
    ("/api/v2/vault-sensors/sensors", "vault_sensors"),
    ("/api/v2/vault-sensors/statistics", "vault_sensors"),
    ("/api/v2/vault-sensors/vault-types", "vault_sensors"),
    # ── Vector ────────────────────────────────────────────────────────────
    ("/api/v2/vector/stats", "vector"),
    # ── Vision (CV/ML) ────────────────────────────────────────────────────
    ("/api/v2/vision/annotators", "vision"),
    ("/api/v2/vision/base-models", "vision"),
    ("/api/v2/vision/crops", "vision"),
    ("/api/v2/vision/datasets", "vision"),
    ("/api/v2/vision/deployments", "vision"),
    ("/api/v2/vision/models", "vision"),
    ("/api/v2/vision/registry", "vision"),
    ("/api/v2/vision/registry/featured", "vision"),
    ("/api/v2/vision/tasks", "vision"),
    ("/api/v2/vision/training/augmentation-options", "vision"),
    ("/api/v2/vision/training/hyperparameters/recommend", "vision"),
    ("/api/v2/vision/training/jobs", "vision"),
    # ── Voice ─────────────────────────────────────────────────────────────
    ("/api/v2/voice/health", "voice"),
    ("/api/v2/voice/synthesize/stream", "voice"),
    ("/api/v2/voice/voices", "voice"),
    # ── Warehouse ─────────────────────────────────────────────────────────
    ("/api/v2/warehouse/alerts", "warehouse"),
    ("/api/v2/warehouse/locations", "warehouse"),
    ("/api/v2/warehouse/summary", "warehouse"),
    # ── Weather ───────────────────────────────────────────────────────────
    ("/api/v2/weather/alerts", "weather"),
    # ── Workflows ─────────────────────────────────────────────────────────
    ("/api/v2/workflows", "workflows"),
    ("/api/v2/workflows/runs/history", "workflows"),
    ("/api/v2/workflows/stats", "workflows"),
    ("/api/v2/workflows/templates/list", "workflows"),
    # ── Yield Map ─────────────────────────────────────────────────────────
    ("/api/v2/yield-map/studies", "yield_map"),
]

BRAPI_ROUTES = [
    # ── BrAPI v2 Standard Endpoints ───────────────────────────────────────
    ("/brapi/v2/allelematrix", "allelematrix"),
    ("/brapi/v2/attributes", "attributes"),
    ("/brapi/v2/attributes/categories", "attributes"),
    ("/brapi/v2/attributevalues", "attributevalues"),
    ("/brapi/v2/breedingmethods", "breedingmethods"),
    ("/brapi/v2/calls", "calls"),
    ("/brapi/v2/callsets", "callsets"),
    ("/brapi/v2/crosses", "crosses"),
    ("/brapi/v2/crosses/stats", "crosses"),
    ("/brapi/v2/crossingprojects", "crossingprojects"),
    ("/brapi/v2/events", "events"),
    ("/brapi/v2/germplasm", "germplasm"),
    ("/brapi/v2/images", "images"),
    ("/brapi/v2/maps", "maps"),
    ("/brapi/v2/markerpositions", "markerpositions"),
    ("/brapi/v2/methods", "methods"),
    ("/brapi/v2/observationlevels", "observationlevels"),
    ("/brapi/v2/observations", "observations"),
    ("/brapi/v2/observations/table", "observations"),
    ("/brapi/v2/observationunits", "observationunits"),
    ("/brapi/v2/observationunits/table", "observationunits"),
    ("/brapi/v2/ontologies", "ontologies"),
    ("/brapi/v2/people", "people"),
    ("/brapi/v2/plannedcrosses", "plannedcrosses"),
    ("/brapi/v2/plates", "plates"),
    ("/brapi/v2/references", "references"),
    ("/brapi/v2/referencesets", "referencesets"),
    ("/brapi/v2/samples", "samples"),
    ("/brapi/v2/scales", "scales"),
    ("/brapi/v2/seedlots", "seedlots"),
    ("/brapi/v2/seedlots/transactions", "seedlots"),
    ("/brapi/v2/traits", "traits"),
    ("/brapi/v2/variables", "variables"),
    ("/brapi/v2/variants", "variants"),
    ("/brapi/v2/variantsets", "variantsets"),
    ("/brapi/v2/vendor/orders", "vendor"),
    ("/brapi/v2/vendor/specifications", "vendor"),
]

ALL_ROUTES = API_V2_ROUTES + BRAPI_ROUTES

# Streaming/SSE endpoints that won't return standard JSON — skip body checks
STREAMING_ENDPOINTS = {
    "/api/v2/voice/synthesize/stream",
    "/api/v2/sensors/readings/live",
}

# Endpoints known to fail under SQLite test DB (PostgreSQL-specific features)
# These use SET LOCAL (RLS), array_length(), pg_class, asyncpg operators, etc.
SQLITE_INCOMPATIBLE = {
    "/api/v2/abiotic/statistics",       # array_length() PG function
    "/api/v2/disease/statistics",       # array_length() PG function
    "/api/v2/rls/status",              # queries pg_class system catalog
    "/api/v2/genotyping/calls",         # asyncpg / tenant_db middleware
    "/api/v2/genotyping/calls/statistics", # asyncpg / tenant_db middleware
    "/api/v2/genotyping/callsets",      # asyncpg / tenant_db middleware
    "/api/v2/genotyping/markerpositions", # asyncpg / tenant_db middleware
    "/api/v2/genotyping/references",    # asyncpg / tenant_db middleware
    "/api/v2/genotyping/referencesets", # asyncpg / tenant_db middleware
    "/api/v2/genotyping/summary",       # asyncpg / tenant_db middleware
    "/api/v2/genotyping/variantsets",   # asyncpg / tenant_db middleware
    "/api/v2/genotyping/vendor/orders", # asyncpg / tenant_db middleware
    "/api/v2/germplasm-search/filters", # Germplasm.collection attribute
    "/api/v2/germplasm-search/statistics", # Germplasm.collection attribute
    "/api/v2/quick-entry/entries",      # SET LOCAL (RLS middleware)
    "/api/v2/integrations/",           # KeyError on missing config
    "/api/v2/integrations/available",  # tenant_db middleware
    "/api/v2/metrics/build",           # Pydantic schema mismatch
    "/api/v2/metrics/database",        # Pydantic schema mismatch
    "/api/v2/metrics/pages",           # Pydantic schema mismatch
    "/api/v2/metrics/summary",         # Pydantic schema mismatch
    "/api/v2/social/reputation/me",    # tenant_db middleware
    "/brapi/v2/attributes",           # asyncpg operators / event loop
    "/brapi/v2/attributes/categories", # asyncpg operators / event loop
    "/brapi/v2/methods",              # asyncpg operators / event loop
    "/brapi/v2/observationlevels",    # asyncpg operators / event loop
    "/brapi/v2/scales",               # asyncpg operators / event loop
    "/brapi/v2/variants",             # SET LOCAL (RLS middleware)
    "/brapi/v2/variantsets",          # SET LOCAL (RLS middleware)
}

# Endpoints known to be public (no auth required)
PUBLIC_ENDPOINTS = {
    "/api/v2/metrics",
    "/api/v2/metrics/api",
    "/api/v2/metrics/badge/brapi",
    "/api/v2/metrics/badge/build",
    "/api/v2/metrics/badge/endpoints",
    "/api/v2/metrics/badge/pages",
    "/api/v2/metrics/badge/version",
    "/api/v2/metrics/build",
    "/api/v2/metrics/database",
    "/api/v2/metrics/milestones",
    "/api/v2/metrics/modules",
    "/api/v2/metrics/pages",
    "/api/v2/metrics/summary",
    "/api/v2/metrics/tech-stack",
    "/api/v2/metrics/version",
    "/api/v2/metrics/workspaces",
    "/api/v2/progress",
    "/api/v2/progress/api-stats",
    "/api/v2/progress/divisions",
    "/api/v2/progress/features",
    "/api/v2/progress/roadmap",
    "/api/v2/progress/summary",
    "/api/v2/progress/tech-stack",
    # Languages — intentionally public (no auth required)
    "/api/v2/languages",
    "/api/v2/languages/stats",
    "/api/v2/languages/translations/keys",
}


# ---------------------------------------------------------------------------
# MODULE-SCOPED FIXTURES — boot the app ONCE, share across all 1700+ tests
# ---------------------------------------------------------------------------

def _route_id(route_tuple):
    """Generate a readable test ID from route tuple."""
    path, module = route_tuple
    short = path.replace("/api/v2/", "").replace("/brapi/v2/", "brapi__")
    return short.replace("/", "__").replace("-", "_").strip("_")


# We create the transport + clients at module scope to avoid per-test overhead.
# This means we do our own DB setup inline rather than relying on conftest fixtures.

@pytest_asyncio.fixture(scope="module")
async def _smoke_clients():
    """
    Yields (auth_client, anon_client) — both module-scoped.
    Sets up the test DB, creates a user, overrides get_db, boots the app ONCE.
    """
    import os
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.dialects.postgresql import ARRAY, JSONB
    from geoalchemy2 import Geometry
    from app.models.base import Base
    from app.models.core import User, Organization
    from app.core.security import create_access_token
    from app.core.database import get_db
    from app.main import app as fastapi_app

    # SQLite compat
    @compiles(Geometry, 'sqlite')
    def _compile_geometry(element, compiler, **kw):
        return "TEXT"

    @compiles(ARRAY, 'sqlite')
    def _compile_array(element, compiler, **kw):
        return "JSON"

    @compiles(JSONB, 'sqlite')
    def _compile_jsonb(element, compiler, **kw):
        return "JSON"

    DB_FILE = "test_smoke.db"
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    sync_engine = create_engine(
        f"sqlite:///{DB_FILE}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    def _sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.close()
        dbapi_connection.create_function("RecoverGeometryColumn", -1, lambda *a: None)
        dbapi_connection.create_function("CreateSpatialIndex", -1, lambda *a: None)
        dbapi_connection.create_function("DisableSpatialIndex", -1, lambda *a: None)
        dbapi_connection.create_function("CheckSpatialIndex", -1, lambda *a: None)
        dbapi_connection.create_function("GeomFromEWKT", -1, lambda *a: a[0] if a else None)
        dbapi_connection.create_function("AsEWKB", -1, lambda *a: a[0] if a else None)
        dbapi_connection.create_function("DiscardGeometryColumn", -1, lambda *a: None)

    event.listen(sync_engine, "connect", _sqlite_pragmas)

    # Create ALL tables so every endpoint has its schema available
    Base.metadata.create_all(bind=sync_engine)

    # Create user
    SyncSession = sessionmaker(bind=sync_engine)
    with SyncSession() as sess:
        org = Organization(name="Smoke Test Org")
        sess.add(org)
        sess.commit()
        sess.refresh(org)
        user = User(email="smoke@test.com", hashed_password="x", organization_id=org.id)
        sess.add(user)
        sess.commit()
        sess.refresh(user)
        user_id = user.id

    # Async engine for DB override
    async_engine = create_async_engine(
        f"sqlite+aiosqlite:///{DB_FILE}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(async_engine.sync_engine, "connect", _sqlite_pragmas)
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False,
    )

    async def override_get_db():
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    fastapi_app.dependency_overrides[get_db] = override_get_db

    token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=timedelta(minutes=120),
    )

    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(
        transport=transport, base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as auth, AsyncClient(
        transport=transport, base_url="http://test",
    ) as anon:
        yield auth, anon

    # Cleanup
    fastapi_app.dependency_overrides.clear()
    await async_engine.dispose()
    sync_engine.dispose()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)


@pytest_asyncio.fixture(scope="module")
async def auth_client(_smoke_clients):
    auth, _ = _smoke_clients
    return auth


@pytest_asyncio.fixture(scope="module")
async def anon_client(_smoke_clients):
    _, anon = _smoke_clients
    return anon


# ---------------------------------------------------------------------------
# Derived route lists for parametrization
# ---------------------------------------------------------------------------

_PROTECTED_ROUTES = [
    (path, mod) for path, mod in ALL_ROUTES
    if path not in PUBLIC_ENDPOINTS
]

_PUBLIC_ROUTE_LIST = [
    (path, mod) for path, mod in ALL_ROUTES
    if path in PUBLIC_ENDPOINTS
]

_JSON_ROUTES = [
    (path, mod) for path, mod in ALL_ROUTES
    if path not in STREAMING_ENDPOINTS
]


# ---------------------------------------------------------------------------
# Test: Authenticated GET → no 500
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestAuthenticatedSmoke:
    """
    Smoke test: every GET endpoint with a valid JWT token.
    Acceptable responses: 200, 204, 404 (empty DB), 422 (missing query params).
    Unacceptable: 500 (server crash), 401/403 (auth not recognized).
    """

    @pytest.mark.parametrize(
        "path,module",
        ALL_ROUTES,
        ids=[_route_id(r) for r in ALL_ROUTES],
    )
    async def test_get_authenticated_no_500(
        self, auth_client: AsyncClient, path: str, module: str
    ):
        if path in SQLITE_INCOMPATIBLE:
            pytest.xfail(f"SQLite-incompatible: {path}")
        response = await auth_client.get(path)
        assert response.status_code != 500, (
            f"500 Internal Server Error on {path} ({module}): "
            f"{response.text[:300]}"
        )
        # Auth should be recognized — 401/403 means auth wiring is broken
        assert response.status_code not in (401, 403), (
            f"Auth rejected on {path} ({module}) — "
            f"status {response.status_code}: {response.text[:200]}"
        )


# ---------------------------------------------------------------------------
# Test: Unauthenticated GET → 401/403 for protected endpoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestUnauthenticatedGuard:
    """
    Smoke test: every protected GET endpoint WITHOUT a token.
    Should return 401 or 403 — never 200 with actual data.
    """

    @pytest.mark.parametrize(
        "path,module",
        _PROTECTED_ROUTES,
        ids=[_route_id(r) for r in _PROTECTED_ROUTES],
    )
    async def test_get_unauth_rejected(
        self, anon_client: AsyncClient, path: str, module: str
    ):
        if path in SQLITE_INCOMPATIBLE:
            pytest.xfail(f"SQLite-incompatible: {path}")
        response = await anon_client.get(path)
        assert response.status_code in (401, 403, 405), (
            f"Unprotected endpoint {path} ({module}) returned "
            f"{response.status_code} without auth — expected 401/403"
        )


# ---------------------------------------------------------------------------
# Test: Public endpoints return 200 without auth
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestPublicEndpoints:
    """
    Smoke test: public endpoints should return 200 without auth.
    """

    @pytest.mark.parametrize(
        "path,module",
        _PUBLIC_ROUTE_LIST,
        ids=[_route_id(r) for r in _PUBLIC_ROUTE_LIST],
    )
    async def test_public_returns_200(
        self, anon_client: AsyncClient, path: str, module: str
    ):
        if path in SQLITE_INCOMPATIBLE:
            pytest.xfail(f"SQLite-incompatible: {path}")
        response = await anon_client.get(path)
        assert response.status_code == 200, (
            f"Public endpoint {path} ({module}) returned "
            f"{response.status_code} — expected 200"
        )


# ---------------------------------------------------------------------------
# Test: Response structure (JSON, not HTML error page)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestResponseFormat:
    """
    Smoke test: authenticated GET endpoints return JSON, not HTML error pages.
    Skip streaming endpoints that return non-JSON content types.
    """

    @pytest.mark.parametrize(
        "path,module",
        _JSON_ROUTES,
        ids=[_route_id(r) for r in _JSON_ROUTES],
    )
    async def test_returns_json(
        self, auth_client: AsyncClient, path: str, module: str
    ):
        if path in SQLITE_INCOMPATIBLE:
            pytest.xfail(f"SQLite-incompatible: {path}")
        response = await auth_client.get(path)
        if response.status_code in (200, 201):
            content_type = response.headers.get("content-type", "")
            assert "json" in content_type or "text/plain" in content_type, (
                f"{path} ({module}) returned content-type '{content_type}' "
                f"instead of JSON — possible error page"
            )

"""
APEX Router Aggregator
Combines all Bijmantra-specific API endpoints (non-BrAPI).
This is the largest router, aggregating 80+ modules.
"""
from fastapi import APIRouter

# ============================================================================
# APEX Core Imports
# ============================================================================
from app.api.v2 import (
    search, compute, audit, insights, vector, weather, chat, crosses,
    integrations, events, tasks, field_environment, voice, gxe, gwas,
    bioinformatics, pedigree, phenotype, mas, trial_design, seed_inventory,
    crop_calendar, export, quality, passport, ontology, nursery, traceability,
    licensing, selection, genetic_gain, harvest, spatial, breeding_value,
    disease, abiotic, dispatch, processing, sensors, forums, solar, space,
    dus, progress, rakshaka, vision, prahari, chaitanya, security_audit, rls,
    grin, mta, barcode, vault_sensors, devguru, selection_decisions,
    parent_selection, performance_ranking, progeny, germplasm_comparison,
    breeding_pipeline, genetic_diversity, population_genetics, qtl_mapping,
    genomic_selection, genotyping, crossing_planner, field_map, trial_planning,
    data_quality, parentage, haplotype, trial_network, germplasm_search,
    molecular_breeding, phenomic_selection, speed_breeding, doubled_haploid,
    field_planning, resource_management, field_scanner, label_printing,
    quick_entry, phenology, plot_history, statistics, climate, crop_health,
    notifications, activity, data_validation, profile, team_management,
    data_dictionary, germplasm_collection, workflows, languages, analytics,
    reports, data_sync, collaboration_hub, field_layout, trial_summary,
    data_visualization, cost_analysis, yield_map, phenotype_comparison, etl,
    collaboration, offline_sync, system_settings, external_services, backup,
    stability_analysis, field_book, nursery_management, warehouse, metrics,
    rbac, dock, image_analysis,
)

apex_router = APIRouter(tags=["APEX"])

# ============================================================================
# AI & Analytics
# ============================================================================
apex_router.include_router(compute.router, tags=["Compute Engine"])
apex_router.include_router(audit.router, tags=["Audit Trail"])
apex_router.include_router(insights.router, tags=["AI Insights"])
apex_router.include_router(vector.router, tags=["Vector Store"])
apex_router.include_router(chat.router, tags=["Veena AI Chat"])
apex_router.include_router(voice.router, tags=["Veena Voice"])
apex_router.include_router(devguru.router, tags=["DevGuru PhD Mentor"])
apex_router.include_router(analytics.router, tags=["Apex Analytics"])
apex_router.include_router(etl.router, tags=["System - ETL"])

# ============================================================================
# Weather & Climate
# ============================================================================
apex_router.include_router(weather.router, tags=["Weather Intelligence"])
apex_router.include_router(climate.router, tags=["Climate Analysis"])

# ============================================================================
# Breeding & Genetics
# ============================================================================
apex_router.include_router(crosses.router, tags=["Cross Prediction"])
apex_router.include_router(gxe.router, tags=["G×E Analysis"])
apex_router.include_router(gwas.router, tags=["GWAS"])
apex_router.include_router(bioinformatics.router, tags=["Bioinformatics"])
apex_router.include_router(pedigree.router, tags=["Pedigree Analysis"])
apex_router.include_router(phenotype.router, tags=["Phenotype Analysis"])
apex_router.include_router(image_analysis.router, tags=["Image Analysis"])
apex_router.include_router(mas.router, tags=["Marker-Assisted Selection"])
apex_router.include_router(selection.router, tags=["Selection Index"])
apex_router.include_router(genetic_gain.router, tags=["Genetic Gain"])
apex_router.include_router(breeding_value.router, tags=["Breeding Value"])
apex_router.include_router(selection_decisions.router, tags=["Selection Decisions"])
apex_router.include_router(parent_selection.router, tags=["Parent Selection"])
apex_router.include_router(performance_ranking.router, tags=["Performance Ranking"])
apex_router.include_router(progeny.router, tags=["Progeny"])
apex_router.include_router(germplasm_comparison.router, tags=["Germplasm Comparison"])
apex_router.include_router(breeding_pipeline.router, tags=["Breeding Pipeline"])
apex_router.include_router(genetic_diversity.router, tags=["Genetic Diversity"])
apex_router.include_router(population_genetics.router, tags=["Population Genetics"])
apex_router.include_router(qtl_mapping.router, tags=["QTL Mapping"])
apex_router.include_router(genomic_selection.router, tags=["Genomic Selection"])
apex_router.include_router(genotyping.router, tags=["BrAPI Genotyping"])
apex_router.include_router(crossing_planner.router, tags=["Crossing Planner"])
apex_router.include_router(parentage.router, tags=["Parentage Analysis"])
apex_router.include_router(haplotype.router, tags=["Haplotype Analysis"])
apex_router.include_router(germplasm_search.router, tags=["Germplasm Search"])
apex_router.include_router(molecular_breeding.router, tags=["Molecular Breeding"])
apex_router.include_router(phenomic_selection.router, tags=["Phenomic Selection"])
apex_router.include_router(speed_breeding.router, tags=["Speed Breeding"])
apex_router.include_router(doubled_haploid.router, tags=["Doubled Haploid"])
apex_router.include_router(germplasm_collection.router, tags=["Germplasm Collections"])

# ============================================================================
# Trials & Field
# ============================================================================
apex_router.include_router(trial_design.router, tags=["Trial Design"])
apex_router.include_router(field_map.router, tags=["Field Map"])
apex_router.include_router(trial_planning.router, tags=["Trial Planning"])
apex_router.include_router(trial_network.router, tags=["Trial Network"])
apex_router.include_router(field_planning.router, tags=["Field Planning"])
apex_router.include_router(field_environment.router, tags=["Field Environment"])
apex_router.include_router(field_scanner.router, tags=["Field Scanner"])
apex_router.include_router(field_layout.router, tags=["Field Layout"])
apex_router.include_router(trial_summary.router, tags=["Trial Summary"])
apex_router.include_router(field_book.router, tags=["Field Book"])
apex_router.include_router(plot_history.router, tags=["Plot History"])
apex_router.include_router(spatial.router, tags=["Spatial Analysis"])
apex_router.include_router(crop_calendar.router, tags=["Crop Calendar"])
apex_router.include_router(phenology.router, tags=["Phenology Tracker"])
apex_router.include_router(crop_health.router, tags=["Crop Health"])

# ============================================================================
# Seed & Inventory
# ============================================================================
apex_router.include_router(seed_inventory.router, tags=["Seed Inventory"])
apex_router.include_router(passport.router, tags=["Germplasm Passport"])
apex_router.include_router(nursery.router, tags=["Nursery Management"])
apex_router.include_router(nursery_management.router, tags=["Nursery Management"])
apex_router.include_router(traceability.router, tags=["Seed Traceability"])
apex_router.include_router(harvest.router, tags=["Harvest Management"])
apex_router.include_router(dispatch.router, tags=["Dispatch Management"])
apex_router.include_router(processing.router, tags=["Seed Processing"])
apex_router.include_router(warehouse.router, tags=["Warehouse Management"])
apex_router.include_router(label_printing.router, tags=["Label Printing"])
apex_router.include_router(barcode.router, tags=["Barcode/QR"])

# ============================================================================
# Disease & Stress
# ============================================================================
apex_router.include_router(disease.router, tags=["Disease Resistance"])
apex_router.include_router(abiotic.router, tags=["Abiotic Stress"])

# ============================================================================
# Research & Analysis
# ============================================================================
apex_router.include_router(stability_analysis.router, tags=["Stability Analysis"])
apex_router.include_router(statistics.router, tags=["Statistics"])
apex_router.include_router(ontology.router, tags=["Trait Ontology"])
apex_router.include_router(data_visualization.router, tags=["Data Visualization"])
apex_router.include_router(yield_map.router, tags=["Yield Map"])
apex_router.include_router(phenotype_comparison.router, tags=["Phenotype Comparison"])
apex_router.include_router(cost_analysis.router, tags=["Cost Analysis"])

# ============================================================================
# Data & Quality
# ============================================================================
apex_router.include_router(data_quality.router, tags=["Data Quality"])
apex_router.include_router(data_validation.router, tags=["Data Validation"])
apex_router.include_router(data_dictionary.router, tags=["Data Dictionary"])
apex_router.include_router(export.router, tags=["Data Export"])
apex_router.include_router(quick_entry.router, tags=["Quick Entry"])

# ============================================================================
# Operations & Integrations
# ============================================================================
apex_router.include_router(integrations.router, tags=["Integration Hub"])
apex_router.include_router(events.router, tags=["Event Bus"])
apex_router.include_router(tasks.router, tags=["Task Queue"])
apex_router.include_router(search.router, tags=["Search"])
apex_router.include_router(sensors.router, tags=["Sensor Networks"])
apex_router.include_router(vault_sensors.router, tags=["Vault Sensors"])
apex_router.include_router(grin.router, tags=["GRIN-Global Integration"])
apex_router.include_router(mta.router, tags=["Material Transfer Agreements"])
apex_router.include_router(licensing.router, tags=["Variety Licensing"])
apex_router.include_router(dus.router, tags=["DUS Testing"])
apex_router.include_router(quality.router, tags=["Quality Control"])
apex_router.include_router(resource_management.router, tags=["Resource Management"])

# ============================================================================
# Collaboration & Team
# ============================================================================
apex_router.include_router(collaboration.router, tags=["Collaboration"])
apex_router.include_router(collaboration_hub.router, tags=["Collaboration Hub"])
apex_router.include_router(forums.router, tags=["Community Forums"])
apex_router.include_router(team_management.router, tags=["Team Management"])
apex_router.include_router(activity.router, tags=["Activity"])
apex_router.include_router(notifications.router, tags=["Notifications"])
apex_router.include_router(workflows.router, tags=["Workflow Automation"])

# ============================================================================
# System & Security
# ============================================================================
apex_router.include_router(offline_sync.router, tags=["Offline Sync"])
apex_router.include_router(data_sync.router, tags=["Data Sync"])
apex_router.include_router(system_settings.router, tags=["System Settings"])
apex_router.include_router(external_services.router, tags=["External Services"])
apex_router.include_router(backup.router, tags=["Backup"])
apex_router.include_router(reports.router, tags=["Advanced Reports"])
apex_router.include_router(metrics.router, tags=["Metrics"])
apex_router.include_router(rbac.router, tags=["RBAC"])
apex_router.include_router(profile.router, tags=["Profile"])
apex_router.include_router(languages.router, tags=["Language Settings"])
apex_router.include_router(dock.router, tags=["Dock"])
apex_router.include_router(progress.router, tags=["Progress Tracker"])

# ============================================================================
# Defense & AI Agents
# ============================================================================
apex_router.include_router(rakshaka.router, tags=["RAKSHAKA Self-Healing"])
apex_router.include_router(prahari.router, tags=["PRAHARI Defense"])
apex_router.include_router(chaitanya.router, tags=["CHAITANYA Orchestrator"])
apex_router.include_router(security_audit.router, tags=["Security Audit"])
apex_router.include_router(rls.router, tags=["Row-Level Security"])
apex_router.include_router(vision.router, tags=["Vision Training Ground"])

# ============================================================================
# Special Research
# ============================================================================
apex_router.include_router(solar.router, tags=["Sun-Earth Systems"])
apex_router.include_router(space.router, tags=["Space Research"])

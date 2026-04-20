"""
Route registration for Bijmantra API.

This module centralizes all router includes following domain organization.
Extracted from main.py as part of Task 16.
"""

import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def register_core_routes(app: FastAPI):
    """Register core authentication and system routes."""
    from app.api import auth
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    
    from app.modules.core.router import router as core_router
    app.include_router(core_router, prefix="/api/v2")
    
    from app.api.v1.endpoints import pedigree as pedigree_v1
    app.include_router(pedigree_v1.router, prefix="/api/v1")


def register_brapi_routes(app: FastAPI):
    """Register BrAPI v2.1 routes."""
    # BrAPI Core
    from app.api.v2.core.router import brapi_core_router
    app.include_router(brapi_core_router, prefix="/brapi/v2")
    
    # BrAPI Germplasm & Phenotyping
    from app.api.brapi.router import brapi_germplasm_router
    app.include_router(brapi_germplasm_router, prefix="/brapi/v2")
    
    # BrAPI Genotyping
    from app.api.brapi.genotyping_router import brapi_genotyping_router
    app.include_router(brapi_genotyping_router, prefix="/brapi/v2")
    
    # BrAPI Phenotyping - Additional endpoints
    from app.api.brapi import (
        methods as brapi_methods,
        observationlevels as brapi_observationlevels,
        ontologies as brapi_ontologies,
        scales as brapi_scales,
    )
    app.include_router(brapi_methods.router, prefix="/brapi/v2", tags=["Methods"])
    app.include_router(brapi_scales.router, prefix="/brapi/v2", tags=["Scales"])
    app.include_router(brapi_ontologies.router, prefix="/brapi/v2", tags=["Ontologies"])
    app.include_router(brapi_observationlevels.router, prefix="/brapi/v2", tags=["Observation Levels"])
    
    # BrAPI Genotyping endpoints
    from app.api.brapi import (
        allelematrix as brapi_allelematrix,
        calls as brapi_calls,
        callsets as brapi_callsets,
        maps as brapi_maps,
        markerpositions as brapi_markerpositions,
        plates as brapi_plates,
        references as brapi_references,
        referencesets as brapi_referencesets,
        search as brapi_search,
        variants as brapi_variants,
        variantsets as brapi_variantsets,
        vendor as brapi_vendor,
    )
    app.include_router(brapi_calls.router, prefix="/brapi/v2", tags=["Genotyping - Calls"])
    app.include_router(brapi_callsets.router, prefix="/brapi/v2", tags=["Genotyping - CallSets"])
    app.include_router(brapi_variants.router, prefix="/brapi/v2", tags=["Genotyping - Variants"])
    app.include_router(brapi_variantsets.router, prefix="/brapi/v2", tags=["Genotyping - VariantSets"])
    app.include_router(brapi_plates.router, prefix="/brapi/v2", tags=["Genotyping - Plates"])
    app.include_router(brapi_references.router, prefix="/brapi/v2", tags=["Genotyping - References"])
    app.include_router(brapi_referencesets.router, prefix="/brapi/v2", tags=["Genotyping - ReferenceSets"])
    app.include_router(brapi_maps.router, prefix="/brapi/v2", tags=["Genotyping - Maps"])
    app.include_router(brapi_markerpositions.router, prefix="/brapi/v2", tags=["Genotyping - Marker Positions"])
    app.include_router(brapi_allelematrix.router, prefix="/brapi/v2", tags=["Genotyping - Allele Matrix"])
    app.include_router(brapi_search.router, prefix="/brapi/v2", tags=["BrAPI Search"])
    app.include_router(brapi_vendor.router, prefix="/brapi/v2", tags=["Genotyping - Vendor"])
    
    # BrAPI Extensions
    from app.api.brapi.extensions import iot as brapi_iot
    app.include_router(brapi_iot.router, prefix="/brapi/v2", tags=["BrAPI IoT Extension"])


def register_domain_routes(app: FastAPI):
    """Register domain module routes (breeding, genomics, phenotyping, etc.)."""
    from app.modules.breeding.router import router as breeding_router
    from app.modules.genomics.router import router as genomics_router
    from app.modules.phenotyping.router import router as phenotyping_router
    from app.modules.germplasm.router import router as germplasm_router
    from app.modules.plant_sciences.router import router as plant_sciences_router
    from app.modules.environment.router import router as environment_router
    from app.modules.spatial.router import router as spatial_router
    from app.modules.ai.router import router as ai_router
    from app.modules.interop.router import router as interop_router
    
    app.include_router(breeding_router)
    app.include_router(genomics_router)
    app.include_router(phenotyping_router)
    app.include_router(germplasm_router)
    app.include_router(plant_sciences_router)
    app.include_router(environment_router)
    app.include_router(spatial_router)
    app.include_router(ai_router)
    app.include_router(interop_router)


def register_apex_routes(app: FastAPI):
    """Register APEX (Bijmantra-specific) API routes."""
    from app.api.v2.apex_router import apex_router
    app.include_router(apex_router, prefix="/api/v2")
    
    from app.api.v2.future.router import future_router
    app.include_router(future_router, prefix="/api/v2")


def register_pwa_routes(app: FastAPI):
    """Register PWA-related routes."""
    from app.api.v2 import pwa_notifications, pwa_sync
    from app.api.v2.new_routers import sso
    
    app.include_router(pwa_sync.router, prefix="/api/v2")
    app.include_router(pwa_notifications.router, prefix="/api/v2")
    app.include_router(sso.router, prefix="/api/v2")


def register_division_routes(app: FastAPI):
    """Register division-specific routes."""
    from app.modules.seed_bank.router import router as seed_bank_router
    from app.modules.space.gateway import router as space_gateway
    from app.modules.crop_calendar.router import router as crop_calendar_router
    from app.modules.soil.router import router as soil_router
    
    app.include_router(seed_bank_router, prefix="/api/v2", tags=["Seed Bank"])
    app.include_router(space_gateway, prefix="/api/v2/space", tags=["Space Division"])
    app.include_router(crop_calendar_router, prefix="/api/v2")
    app.include_router(soil_router, prefix="/api/v2/soil", tags=["Soil Division"])


def register_feature_routes(app: FastAPI):
    """Register feature-specific routes (compute, analytics, etc.)."""
    from app.api.v2 import (
        abiotic,
        activity,
        agronomy,
        analytics,
        audit,
        barcode,
        bioinformatics,
        breeding_pipeline,
        breeding_value,
        carbon,
        chaitanya,
        chat,
        collaboration,
        collaboration_hub,
        compliance,
        crop_health,
        crosses,
        data_dictionary,
        data_quality,
        data_sync,
        data_validation,
        data_visualization,
        devguru,
        disease,
        dispatch,
        doubled_haploid,
        dus,
        emissions,
        events,
        export,
        field_book,
        field_layout,
        field_planning,
        field_scanner,
        forums,
        genetic_diversity,
        genetic_gain,
        gxe,
        harvest,
        impact,
        insights,
        label_printing,
        languages,
        licensing,
        mta,
        notifications,
        nursery_management,
        offline_sync,
        ontology,
        performance_ranking,
        plot_history,
        prahari,
        processing,
        profile,
        progeny,
        progress,
        proposals,
        quality,
        quick_entry,
        rakshaka,
        reports,
        resource_management,
        rls,
        security_audit,
        seed_inventory,
        sensors,
        social,
        stability_analysis,
        statistics,
        tasks,
        team_management,
        traceability,
        vault_sensors,
        vector,
        workflows,
        yield_gap,
    )
    
    # Compute & Analytics
    from app.api.v2 import compute, monitoring, workers
    app.include_router(compute.router, prefix="/api/v2", tags=["Compute Engine"])
    app.include_router(workers.router, prefix="/api/v2", tags=["Worker Monitoring"])
    app.include_router(monitoring.router, prefix="/api/v2", tags=["Compute Monitoring"])
    
    # Core features
    app.include_router(agronomy.router, prefix="/api/v2", tags=["Agronomy"])
    app.include_router(audit.router, prefix="/api/v2", tags=["Audit Trail"])
    app.include_router(insights.router, prefix="/api/v2", tags=["AI Insights"])
    app.include_router(vector.router, prefix="/api/v2", tags=["Vector Store"])
    app.include_router(carbon.router, prefix="/api/v2", tags=["Carbon Monitoring"])
    app.include_router(emissions.router, prefix="/api/v2", tags=["Emissions Tracking"])
    app.include_router(impact.router, prefix="/api/v2", tags=["Impact Metrics"])
    app.include_router(yield_gap.router, prefix="/api/v2", tags=["Yield Gap Analysis"])
    app.include_router(chat.router, prefix="/api/v2", tags=["AI Chat"])
    app.include_router(proposals.router, prefix="/api/v2", tags=["Proposals (AI Scribe)"])
    app.include_router(events.router, prefix="/api/v2", tags=["Event Bus"])
    app.include_router(tasks.router, prefix="/api/v2", tags=["Task Queue"])
    app.include_router(gxe.router, prefix="/api/v2", tags=["G×E Analysis"])
    app.include_router(bioinformatics.router, prefix="/api/v2", tags=["Bioinformatics"])
    app.include_router(seed_inventory.router, prefix="/api/v2", tags=["Seed Inventory"])
    app.include_router(export.router, prefix="/api/v2", tags=["Data Export"])
    app.include_router(quality.router, prefix="/api/v2", tags=["Quality Control"])
    app.include_router(ontology.router, prefix="/api/v2", tags=["Trait Ontology"])
    app.include_router(traceability.router, prefix="/api/v2", tags=["Seed Traceability"])
    app.include_router(licensing.router, prefix="/api/v2", tags=["Variety Licensing"])
    app.include_router(genetic_gain.router, prefix="/api/v2", tags=["Genetic Gain"])
    app.include_router(harvest.router, prefix="/api/v2", tags=["Harvest Management"])
    app.include_router(disease.router, prefix="/api/v2", tags=["Disease Resistance"])
    app.include_router(abiotic.router, prefix="/api/v2", tags=["Abiotic Stress"])
    app.include_router(dispatch.router, prefix="/api/v2", tags=["Dispatch Management"])
    app.include_router(processing.router, prefix="/api/v2", tags=["Seed Processing"])
    app.include_router(sensors.router, prefix="/api/v2", tags=["Sensor Networks"])
    app.include_router(forums.router, prefix="/api/v2", tags=["Community Forums"])
    app.include_router(social.router, prefix="/api/v2/social")
    app.include_router(dus.router, prefix="/api/v2", tags=["DUS Testing"])
    app.include_router(progress.router, prefix="/api/v2", tags=["Progress Tracker"])
    app.include_router(rakshaka.router, prefix="/api/v2", tags=["RAKSHAKA Self-Healing"])
    app.include_router(prahari.router, prefix="/api/v2", tags=["PRAHARI Defense"])
    app.include_router(chaitanya.router, prefix="/api/v2", tags=["CHAITANYA Orchestrator"])
    app.include_router(security_audit.router, prefix="/api/v2", tags=["Security Audit"])
    app.include_router(rls.router, prefix="/api/v2", tags=["Row-Level Security"])
    app.include_router(mta.router, prefix="/api/v2", tags=["Material Transfer Agreements"])
    app.include_router(barcode.router, prefix="/api/v2", tags=["Barcode/QR"])
    app.include_router(vault_sensors.router, prefix="/api/v2", tags=["Vault Sensors"])
    app.include_router(performance_ranking.router, prefix="/api/v2", tags=["Performance Ranking"])
    app.include_router(progeny.router, prefix="/api/v2", tags=["Progeny"])
    app.include_router(genetic_diversity.router, prefix="/api/v2", tags=["Genetic Diversity"])
    app.include_router(data_quality.router, prefix="/api/v2", tags=["Data Quality"])
    app.include_router(doubled_haploid.router, prefix="/api/v2", tags=["Doubled Haploid"])
    app.include_router(field_planning.router, prefix="/api/v2", tags=["Field Planning"])
    app.include_router(resource_management.router, prefix="/api/v2", tags=["Resource Management"])
    app.include_router(field_scanner.router, prefix="/api/v2", tags=["Field Scanner"])
    app.include_router(label_printing.router, prefix="/api/v2", tags=["Label Printing"])
    app.include_router(quick_entry.router, prefix="/api/v2", tags=["Quick Entry"])
    app.include_router(plot_history.router, prefix="/api/v2", tags=["Plot History"])
    app.include_router(statistics.router, prefix="/api/v2", tags=["Statistics"])
    app.include_router(crop_health.router, prefix="/api/v2", tags=["Crop Health"])
    app.include_router(notifications.router, prefix="/api/v2", tags=["Notifications"])
    app.include_router(activity.router, prefix="/api/v2", tags=["Activity"])
    app.include_router(data_validation.router, prefix="/api/v2", tags=["Data Validation"])
    app.include_router(profile.router, prefix="/api/v2", tags=["Profile"])
    app.include_router(team_management.router, prefix="/api/v2", tags=["Team Management"])
    app.include_router(data_dictionary.router, prefix="/api/v2", tags=["Data Dictionary"])
    app.include_router(collaboration.router, prefix="/api/v2", tags=["Collaboration"])
    app.include_router(offline_sync.router, prefix="/api/v2", tags=["Offline Sync"])
    app.include_router(workflows.router, prefix="/api/v2", tags=["Workflow Automation"])
    app.include_router(languages.router, prefix="/api/v2", tags=["Language Settings"])
    app.include_router(analytics.router, prefix="/api/v2", tags=["Apex Analytics"])
    app.include_router(reports.router, prefix="/api/v2", tags=["Advanced Reports"])
    app.include_router(compliance.router, prefix="/api/v2", tags=["Compliance"])
    app.include_router(data_sync.router, prefix="/api/v2", tags=["Data Sync"])
    app.include_router(collaboration_hub.router, prefix="/api/v2", tags=["Collaboration Hub"])
    app.include_router(field_layout.router, prefix="/api/v2", tags=["Field Layout"])
    app.include_router(data_visualization.router, prefix="/api/v2", tags=["Data Visualization"])
    app.include_router(stability_analysis.router, prefix="/api/v2", tags=["Stability Analysis"])
    app.include_router(field_book.router, prefix="/api/v2", tags=["Field Book"])
    app.include_router(nursery_management.router, prefix="/api/v2", tags=["Nursery Management"])
    
    # Import/Export
    from app.api.v2.import_api import router as import_router
    app.include_router(import_router, prefix="/api/v2", tags=["Data Import"])
    
    # System
    from app.api.v2 import (
        backup,
        dock,
        external_services,
        metrics,
        rbac,
        system_settings,
        warehouse,
    )
    app.include_router(system_settings.router, prefix="/api/v2", tags=["System Settings"])
    app.include_router(external_services.router, prefix="/api/v2", tags=["External Services"])
    app.include_router(backup.router, prefix="/api/v2", tags=["Backup"])
    app.include_router(metrics.router, prefix="/api/v2", tags=["Metrics"])
    app.include_router(rbac.router, prefix="/api/v2", tags=["RBAC"])
    app.include_router(dock.router, prefix="/api/v2", tags=["Dock"])
    app.include_router(warehouse.router, prefix="/api/v2", tags=["Warehouse Management"])


def register_future_routes(app: FastAPI):
    """Register future/experimental routes."""
    from app.api.v2.future import (
        carbon_sequestration,
        crop_suitability,
        disease_risk_forecast,
        fertilizer_recommendation,
        gdd,
        ipm_strategy,
        irrigation_schedule,
        pest_observation,
        soil_health,
        soil_moisture,
        soil_test,
        spray_application,
        water_balance,
        yield_prediction,
    )
    
    app.include_router(crop_suitability.router, prefix="/api/v2/future", tags=["Crop Suitability"])
    app.include_router(gdd.router, prefix="/api/v2/future", tags=["Growing Degree Days"])
    app.include_router(soil_test.router, prefix="/api/v2/future", tags=["Soil Tests"])
    app.include_router(fertilizer_recommendation.router, prefix="/api/v2/future", tags=["Fertilizer Recommendations"])
    app.include_router(soil_health.router, prefix="/api/v2/future", tags=["Soil Health"])
    app.include_router(carbon_sequestration.router, prefix="/api/v2/future", tags=["Carbon Sequestration"])
    app.include_router(pest_observation.router, prefix="/api/v2/future", tags=["Pest Observations"])
    app.include_router(disease_risk_forecast.router, prefix="/api/v2/future", tags=["Disease Risk Forecasts"])
    app.include_router(spray_application.router, prefix="/api/v2/future", tags=["Spray Applications"])
    app.include_router(ipm_strategy.router, prefix="/api/v2/future", tags=["IPM Strategies"])
    app.include_router(irrigation_schedule.router, prefix="/api/v2/future", tags=["Irrigation Schedules"])
    app.include_router(water_balance.router, prefix="/api/v2/future", tags=["Water Balance"])
    app.include_router(soil_moisture.router, prefix="/api/v2/future", tags=["Soil Moisture"])
    app.include_router(yield_prediction.router, prefix="/api/v2/future", tags=["Yield Prediction"])


def register_iot_routes(app: FastAPI):
    """Register IoT extension routes."""
    from app.api.v2.iot import devices as iot_devices
    from app.api.v2.iot import telemetry as iot_telemetry
    
    app.include_router(iot_devices.router, prefix="/api/v2")
    app.include_router(iot_telemetry.router, prefix="/api/v2")


def register_economics_routes(app: FastAPI):
    """Register agricultural economics routes."""
    from app.api.v2.economics import router as economics_router
    app.include_router(economics_router, prefix="/api/v2/economics", tags=["Agricultural Economics"])


def register_biosimulation_routes(app: FastAPI):
    """Register biosimulation routes."""
    from app.api.v2.biosimulation import router as biosimulation_router
    app.include_router(biosimulation_router, prefix="/api/v2/biosimulation", tags=["Biosimulation Engine"])


def register_trial_summary_routes(app: FastAPI):
    """Register trial summary routes."""
    from app.api.v2 import trial_summary
    app.include_router(trial_summary.router, prefix="/api/v2", tags=["Trial Summary"])


def register_performance_routes(app: FastAPI):
    """Register performance optimization routes."""
    from app.api.v2 import performance
    app.include_router(performance.router, prefix="/api/v2", tags=["Performance Optimization"])


def register_robotics_routes(app: FastAPI):
    """Register robotics simulator routes (optional)."""
    try:
        from app.api.v2 import robotics
        app.include_router(robotics.router, prefix="/api/v2/robotics", tags=["Robotics Simulator"])
    except Exception as robotics_import_error:
        logger.warning("Robotics routes disabled due to missing dependencies: %s", robotics_import_error)


def register_all_routes(app: FastAPI):
    """
    Register all application routes.
    
    This is the main entry point for route registration.
    Routes are organized by domain and responsibility.
    """
    logger.info("Registering routes...")
    
    register_core_routes(app)
    register_brapi_routes(app)
    register_domain_routes(app)
    register_apex_routes(app)
    register_pwa_routes(app)
    register_division_routes(app)
    register_feature_routes(app)
    register_future_routes(app)
    register_iot_routes(app)
    register_economics_routes(app)
    register_biosimulation_routes(app)
    register_trial_summary_routes(app)
    register_performance_routes(app)
    register_robotics_routes(app)
    
    logger.info("All routes registered successfully")

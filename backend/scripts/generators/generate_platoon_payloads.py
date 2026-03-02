import json
import os
from pathlib import Path

# Goal: Auto-generate 60 copy-paste agent prompts based on the Platoon Expansion Master Plan
OUTPUT_DIR = Path("docs/development/platoons")

# Platoon Definitions
PLATOONS = {
    "A": {
        "name": "Platoon Alpha",
        "bot_type": "Gemini Pro",
        "focus": "Deep AI, Analytics Data Foundation & REEVU DAG Scaling",
        "constraint": "Builds new standalone services in `backend/app/services/analytics/` and `backend/app/services/reevu/expansions/`.",
        "jobs": [
            ("A01", "Build `dag_topological_sorter.py` and `dag_fallback_path.py` for Step Adequacy."),
            ("A02", "Build `nlp_token_normalizer.py` and `domain_matcher.py` for Domain Detection accuracy."),
            ("A03", "Build `duckdb_parquet_writer.py` for Analytics Data Foundation Sprint 1."),
            ("A04", "Build `etl_phenotype_extractor.py` for daily data lake syncing."),
            ("A05", "Scaffold `latent_state_encoder.py` (Draft 1) for sensorimotor input streams."),
            ("A06", "Scaffold `growth_stage_transition_model.py` (vision + time representations)."),
            ("A07", "Build `ssp_scenario_parser.py` (Climate 2030/2050 data ingester)."),
            ("A08", "Build `gxe_interaction_scorer.py` matrix calculator."),
            ("A09", "Scaffold `gwas_plink_adapter.py` for backend integration."),
            ("A10", "Scaffold `gblup_matrix_solver.py` for trait prediction."),
            ("A11", "Build `yield_env_covariate_matrix.py` calculation service."),
            ("A12", "Build `crop_ontology_sync_worker.py` for external API polling."),
            ("A13", "Build `seed_inventory_barcode_generator.py`."),
            ("A14", "Build `cold_storage_3d_mapper.py` internal data structure."),
            ("A15", "Build `custom_report_weasyprint_engine.py` (PDF generation).")
        ]
    },
    "B": {
        "name": "Platoon Bravo",
        "bot_type": "Gemini Pro",
        "focus": "Infrastructure, Geospatial, Enterprise Auth, & Data Pipelines",
        "constraint": "Focuses on infra/external integrations in `backend/app/services/infra/` and `backend/app/api/v2/new_routers/`.",
        "jobs": [
            ("B01", "Build `gee_auth_manager.py` (Server-to-server JWT generation)."),
            ("B02", "Build `gee_ndvi_raster_fetcher.py`."),
            ("B03", "Build `gee_field_boundary_extractor.py`."),
            ("B04", "Build `uav_orthomosaic_stitcher_webhook.py`."),
            ("B05", "Build `ml_bounding_box_extractor.py` for plot identification."),
            ("B06", "Build `saml_oidc_auth_provider.py` (SSO)."),
            ("B07", "Build `rbac_row_level_security_middleware.py`."),
            ("B08", "Build `mqtt_lorawan_ingestion_node.py`."),
            ("B09", "Build `websocket_crdt_sync_manager.py` (Live presence state)."),
            ("B10", "Build `experimental_design_generator.py` (RCBD, Alpha-Lattice math)."),
            ("B11", "Build `cfr_part11_audit_logger.py` (immutable log appending)."),
            ("B12", "Build `event_trigger_rule_engine.py`."),
            ("B13", "Build `marketplace_webhook_dispatcher.py`."),
            ("B14", "Build `csv_enterprise_regex_mapper.py`."),
            ("B15", "Build `image_leaf_area_calculator.py` (Biometric visual parsing).")
        ]
    },
    "C": {
        "name": "Platoon Charlie",
        "bot_type": "Gemini Flash",
        "focus": "Independent Frontend UI/UX & Data Visualizations (React/Tailwind)",
        "constraint": "Must create strictly NEW standalone components in `frontend/src/components/isolated_features/` or new hooks. No editing `App.tsx` or global routers.",
        "jobs": [
            ("C01", "Build `PdfReportTemplateRenderer.tsx` (React component for print layouts)."),
            ("C02", "Build `ManhattanPlotViewer.tsx` (Genomics visualization canvas)."),
            ("C03", "Build `RecursivePedigreeGraph.tsx` (D3/Canvas circular tree)."),
            ("C04", "Build `DragAndDropAnalyticsGrid.tsx`."),
            ("C05", "Build `EnterpriseSSOLoginCard.tsx`."),
            ("C06", "Build `IndexedDbSyncQueueManager.ts` (Data layer logic hook)."),
            ("C07", "Build `SpatialFieldMapLayout.tsx` (Plot grid visualization)."),
            ("C08", "Build `LiveSensorTelemetryChart.tsx` (ECharts streaming component)."),
            ("C09", "Build `BiometricImageAnnotator.tsx` (Canvas bounding box tool)."),
            ("C10", "Build `NotificationInboxPanel.tsx`."),
            ("C11", "Build `GanttChartTimeline.tsx` (Breeding cycle planner)."),
            ("C12", "Build `PluginDiscoveryGrid.tsx`."),
            ("C13", "Build `GxEMatrixHeatmap.tsx`."),
            ("C14", "Build `BluetoothScaleListenerHook.ts`."),
            ("C15", "Build `VirtualizedPhenotypeGrid.tsx` (100k row capability).")
        ]
    },
    "D": {
        "name": "Platoon Delta",
        "bot_type": "Gemini Flash",
        "focus": "Massive Verification, Schema Expansions, & Independent Observability Scripts",
        "constraint": "Builds isolated scripts in `backend/scripts/` and completely isolated unit tests in `backend/tests/units/isolated/`.",
        "jobs": [
            ("D01", "Write `eval_domain_accuracy_matrix.py` (Standalone script)."),
            ("D02", "Write `test_dag_fallback_isolated.py` (Mocked test fixture)."),
            ("D03", "Write `brapi_v2_1_compliance_validator.py` (Schema tester)."),
            ("D04", "Write `parquet_schema_validator_script.py`."),
            ("D05", "Define `schema_climate_ssp_models.py` (Pydantic models only)."),
            ("D06", "Define `schema_iot_sensor_payloads.py`."),
            ("D07", "Define `schema_gwas_results.py`."),
            ("D08", "Write `docs/gupt/manuals/ENTERPRISE_SSO_GUIDE.md`."),
            ("D09", "Write `docs/gupt/manuals/GEE_TILE_SERVER_ARCH.md`."),
            ("D10", "Write `docs/gupt/manuals/OFFLINE_CRDT_SYNC_SPEC.md`."),
            ("D11", "Write `test_yield_matrix_math.py`."),
            ("D12", "Write `test_experimental_designs.py`."),
            ("D13", "Write `test_audit_log_immutability.py`."),
            ("D14", "Write `github_action_nightly_etl_simulate.yml` (Workflow file)."),
            ("D15", "Write `migration_seed_inventory_tables.sql` (Raw DB schema script).")
        ]
    }
}

TEMPLATE = """# BIJMANTRA JULES JOB CARD: {job_id} 
**Bot Tier Assigned:** {bot_type} ({platoon_name})

## 🚨 STRATEGIC DIRECTIVES (CRITICAL)
1. **Zero Git Conflict Rule**: You are 1 of 60 agents operating simultaneously. To prevent merge conflicts, you MUST operate in strict isolation. 
2. **Isolation Constraint**: {constraint}
3. **Canonical AI Rule**: REEVU is the singular canonical AI reasoning framework across genomics, trials, weather, etc. Veena is fully DEPRECATED and frozen for legacy compatibility only. Do NOT add new Veena endpoints or refer to Veena in new code.
4. **Execution Style**: You are a fast, autonomous software engineer. You do not ask for permission. Analyze the codebase, scaffold the assigned files, write the tests, build the UI (if applicable), and execute in one prompt.

---

## 🚀 YOUR SPECIFIC OBJECTIVE
**Assigned Task:** {job_description}

### Expected 10-Step Execution Flow:
1. `view_file` the architecture/domain standards if unfamiliar.
2. Formulate a 30-item implementation checklist in your `task.md`.
3. Scaffold the isolated file (e.g., the new `.py` service, the `.tsx` component, or `.sql` script).
4. Implement the strict business logic (Types/Interfaces/Schemas first).
5. Implement the core functionality (avoiding `App.tsx`, `main.py`, or global route edits).
6. Verify against REEVU metrics (if AI/DAG task), or generic unit tests (if logic).
7. Ensure BrAPI v2.1 compliance (if building an API boundary).
8. Ensure UI components use pure TailwindCSS + Shadcn patterns.
9. Format code and run `npm run lint` or `pytest`/`flake8` to cleanly test your isolated file.
10. `notify_user` with a short completion summary.

---

## CONTEXT REMINDER
* **Frontend**: React 19, Vite 7, Zustand 4, TailwindCSS v4, Lucide React.
* **Backend**: FastAPI, Python 3.13, SQLAlchemy, Alembic, PostgreSQL + pgvector, WeasyPrint 68.1, Celery.
* **Environment Context**: You are executing this inside the BijMantra repository.

**Now, claim Job {job_id} and execute!**
"""

def generate_payloads():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    
    for platoon_key, platoon_data in PLATOONS.items():
        platoon_dir = OUTPUT_DIR / f"{platoon_key}_{str(platoon_data['name']).replace(' ', '_')}"
        platoon_dir.mkdir(exist_ok=True)
        
        for job_id, job_desc in platoon_data['jobs']:
            prompt_content = TEMPLATE.format(
                job_id=job_id,
                bot_type=platoon_data['bot_type'],
                platoon_name=platoon_data['name'],
                constraint=platoon_data['constraint'],
                job_description=job_desc
            )
            
            file_path = platoon_dir / f"{job_id}-prompt.txt"
            with open(file_path, "w") as f:
                f.write(prompt_content)
            count += 1
            
    print(f"✅ Generated {count} Job Card Prompts in {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_payloads()

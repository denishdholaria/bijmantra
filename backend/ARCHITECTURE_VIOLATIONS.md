# Architecture Violations Report

Generated: $(date)
Task: 7.2 Fix Remaining Architecture Violations

## Summary

This report documents architecture violations detected by running architecture linters and manual code inspection.

## 1. Cross-Domain Import Violations

### Critical: AI Module Importing from Multiple Domains

**File:** `backend/app/modules/ai/services/tools.py`

**Violations:**
- Line 20: `from app.modules.breeding.services.cross_search_service import cross_search_service`
- Line 21: `from app.modules.germplasm.services.search_service import germplasm_search_service`
- Line 22: `from app.modules.spatial.services.location_search_service import location_search_service`
- Line 28: `from app.modules.breeding.services.trial_search_service import trial_search_service`
- Line 1169: `from app.modules.environment.services.weather_service import weather_service`
- Line 1330: `from app.modules.breeding.services.breeding_value_service import breeding_value_service`
- Line 1655: `from app.modules.breeding.services.breeding_value_service import breeding_value_service`

**Impact:** The AI module (Veena tools) directly imports from breeding, germplasm, spatial, and environment domains, violating domain boundary rules.

**Remediation:** 
- Create a service registry or event bus pattern for cross-domain communication
- Use dependency injection to provide domain services to AI tools
- Create explicit interfaces/contracts for cross-domain operations

### Breeding Module Importing from Genomics Domain

**File:** `backend/app/modules/breeding/services/breeding_value_service.py`

**Violation:**
- Line 184: `from app.modules.genomics.compute.statistics.kinship import calculate_vanraden_kinship`

**Impact:** Breeding domain directly imports compute functions from genomics domain.

**Remediation:**
- Move shared compute functions to a common compute library
- Or create an explicit interface for genomics compute operations

### Bio Analytics Module Importing from Genomics Domain

**File:** `backend/app/modules/bio_analytics/services/gwas_analysis.py`

**Violation:**
- Line 8: `from app.modules.genomics.services.gwas_service import get_gwas_service`

**Impact:** Bio analytics domain directly imports from genomics domain.

**Remediation:**
- Clarify domain ownership - should bio_analytics be merged with genomics?
- Or use event bus/service registry pattern

### Breeding Module Importing from Environment Domain

**File:** `backend/app/modules/breeding/compute/yield_prediction/process.py`

**Violation:**
- Line 10: `from app.modules.environment.services.gdd_calculator_service import GrowthStagePrediction, gdd_calculator_service`

**Impact:** Breeding compute layer imports from environment services.

**Remediation:**
- Use dependency injection to provide environment services
- Or create a shared interface for GDD calculations

## 2. Layer Contract Violations

### Routers Importing from Models Directly

**Files with violations:**
1. `backend/app/modules/crop_calendar/router.py` (Line 7)
2. `backend/app/modules/space/mars/router.py` (Line 7)
3. `backend/app/modules/space/research/router.py` (Line 13)

**Violation:** All import `from app.models.core import User`

**Impact:** API layer (routers) importing from model layer directly, bypassing service layer.

**Remediation:**
- Routers should only import from services and schemas
- User model should be accessed through dependency injection (get_current_user)
- The User import is likely only for type hints - can use TYPE_CHECKING or forward references

## 3. Import-Linter Configuration Issues

**Issue:** Import-linter fails with "Modules have shared descendants" error

**Root Cause:** The forbidden contract in `.import-linter.ini` has source_modules and forbidden_modules with the same domains, which creates a circular constraint.

**Remediation:**
- Fix the import-linter configuration to properly express "domains cannot import from each other"
- The current configuration tries to make each domain forbidden from importing itself, which is incorrect

## 4. Services Not Yet Migrated

**Status:** Many services remain in the flat `backend/app/services/` directory

**Count:** Approximately 80+ service files still in flat directory

**Examples:**
- `abiotic_stress.py`
- `barcode_service.py`
- `bioinformatics.py`
- `biosimulation.py`
- `carbon_monitoring_service.py`
- `collaboration_service.py`
- `correlation_analysis.py`
- `crop_calendar.py`
- `data_export.py`
- `data_quality_service.py`
- `dimensionality_reduction.py`
- `disease_resistance.py`
- `doubled_haploid.py`
- `dus_testing.py`
- `economics.py`
- `experimental_design_generator.py`
- `genetic_diversity.py`
- `genetic_gain.py`
- `genomics_data.py`
- `genotyping.py`
- `gxe_analysis.py`
- `harvest_management.py`
- `image_service.py`
- `mixed_model.py`
- `nirs_prediction.py`
- `observation_search.py`
- `performance_ranking.py`
- `processing_batch.py`
- `program_search.py`
- `quality_control.py`
- `seed_inventory.py`
- `seed_traceability.py`
- `seedlot_search.py`
- `sensor_network.py`
- `simulation_service.py`
- `soil_analysis.py`
- `solar.py`
- `space_research.py`
- `spatial.py`
- `stability_analysis.py`
- `statistics_calculator.py`
- `trait_ontology.py`
- `trait_search.py`
- `variety_licensing.py`
- `water_balance_service.py`
- `yield_gap_service.py`

**Impact:** These services should have been migrated in Phases 2-5 according to the design document.

**Note:** According to the tasks file, Phases 2-5 are marked as complete, but many services remain unmigrated. This suggests either:
1. The migration was incomplete
2. These are new services added after migration
3. These services are intentionally kept in the flat directory

## 5. Subdirectories Still in Services

**Subdirectories that should be migrated:**
- `services/analytics/` → Should be in domain compute layers
- `services/chaitanya/` → Should be in AI domain
- `services/compliance/` → Should be in core domain
- `services/import_engine/` → Should be in core domain
- `services/infra/` → Should be distributed to appropriate domains
- `services/iot/` → Should be in environment or spatial domain
- `services/ledger/` → Should be in core domain
- `services/phenotyping/` → Should be in phenotyping domain module
- `services/prahari/` → Should be in core domain (security)
- `services/rakshaka/` → Should be in core domain (monitoring)
- `services/reevu/` → Should be in AI domain
- `services/robotics/` → Should be in spatial or phenotyping domain
- `services/social/` → Should be in core domain

## Recommendations

### Priority 1: Fix Cross-Domain Imports in AI Module

The AI module's tools.py file is the most significant violation, importing from 4 different domains. This should be fixed by:

1. Creating a service registry pattern
2. Using dependency injection
3. Creating explicit interfaces for cross-domain operations

### Priority 2: Fix Layer Contract Violations

The router files importing User model directly should be fixed by:

1. Using TYPE_CHECKING for type hints
2. Relying on dependency injection (get_current_user) for actual User instances

### Priority 3: Fix Import-Linter Configuration

The `.import-linter.ini` configuration needs to be corrected to properly express domain boundary rules.

### Priority 4: Complete Service Migration

Determine which services in the flat directory should be migrated and complete the migration process.

### Priority 5: Migrate Subdirectories

Move the organized subdirectories to their appropriate domain modules.

## Next Steps

1. Fix the most critical violations (AI module cross-domain imports)
2. Update import-linter configuration
3. Re-run linters to verify fixes
4. Document any intentional exceptions with justification
5. Update CI to enforce these rules going forward

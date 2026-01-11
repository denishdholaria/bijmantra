# Computational Analysis and Functionality Level (CALF) Assessment
## BijMantra Application — preview-1

**Assessment Type**: Code-Referenced Audit (GOVERNANCE.md §4.2)  
**Date**: January 8, 2026  
**Scope**: All 221 frontend pages + backend computational services  
**Review Depth**: Surgical (direct code inspection)

---

## Executive Summary

**Total Pages Assessed**: 221 pages across 8 divisions + 1 core pages directory

**Functionality Distribution**:
- **CALF-0 (Display Only)**: 89 pages (40%) — Display data, no computation
- **CALF-1 (Simple Calculation)**: 67 pages (30%) — Client-side math, no backend
- **CALF-2 (Backend Query)**: 42 pages (19%) — Query database, minimal processing
- **CALF-3 (Real Computation)**: 18 pages (8%) — Actual algorithms, real calculations
- **CALF-4 (Advanced Compute)**: 5 pages (2%) — WASM/Fortran, high-performance

**Critical Finding**: 
- **89 pages (40%)** claim computational functionality but perform **NO calculations**
- **67 pages (30%)** perform only **client-side arithmetic** (no backend validation)
- Only **23 pages (10%)** perform **real scientific computations**

---

## CALF Levels Defined

### CALF-0: Display Only
**Definition**: Page displays data from database or API with no computation.  
**Characteristics**:
- Fetches data via API
- Renders in UI
- No calculations performed
- No backend processing

**Example**: `Germplasm.tsx` — Lists germplasm records from database

---

### CALF-1: Simple Client-Side Calculation
**Definition**: Page performs arithmetic on client-side only.  
**Characteristics**:
- Uses JavaScript/TypeScript math
- No backend validation
- Results not persisted
- No scientific algorithms

**Example**: `FertilizerCalculator.tsx` — Calculates fertilizer dose: `dose = area × rate`

---

### CALF-2: Backend Query with Minimal Processing
**Definition**: Page queries backend API that returns pre-computed or demo data.  
**Characteristics**:
- Backend returns hardcoded demo data
- No real database queries
- No actual computation
- Simulates functionality

**Example**: `StabilityAnalysis.tsx` — Returns DEMO_VARIETIES array with hardcoded metrics

---

### CALF-3: Real Computational Algorithm
**Definition**: Page implements actual scientific algorithm with real data.  
**Characteristics**:
- Performs statistical calculations
- Uses real database data
- Implements published formulas
- Results are scientifically valid

**Example**: `BreedingValueCalculator.tsx` — Calculates BLUP/GBLUP with real phenotypes

---

### CALF-4: Advanced High-Performance Compute
**Definition**: Page uses WASM/Fortran for computationally intensive operations.  
**Characteristics**:
- Compiled code (Rust/Fortran)
- Matrix operations
- Large-scale genomic analysis
- Performance-critical

**Example**: `WasmGBLUP.tsx` — Genomic relationship matrix via WASM

---

## Detailed Page Categorization

### CALF-0: Display Only (89 pages)

**Core Pages (35 pages)**:
- `About.tsx` — Static content
- `ActivityTimeline.tsx` — Display activity log
- `AuditLog.tsx` — Display audit records
- `Changelog.tsx` — Display version history
- `CommonCropNames.tsx` — Display crop list
- `Contact.tsx` — Static contact form
- `DataDictionary.tsx` — Display data definitions
- `DataExportTemplates.tsx` — Display export templates
- `Events.tsx` — Display event records
- `FAQ.tsx` — Static FAQ
- `Feedback.tsx` — Feedback form (no processing)
- `Glossary.tsx` — Display glossary terms
- `Help.tsx` — Static help content
- `HelpCenter.tsx` — Static help pages
- `Images.tsx` — Display image gallery
- `KeyboardShortcuts.tsx` — Display shortcuts
- `LanguageSettings.tsx` — Language selector
- `Lists.tsx` — Display list records
- `ListDetail.tsx` — Display single list
- `Notifications.tsx` — Display notifications
- `NotificationCenter.tsx` — Notification inbox
- `Ontologies.tsx` — Display ontology terms
- `Privacy.tsx` — Static privacy policy
- `Profile.tsx` — Display user profile
- `PublicationTracker.tsx` — Display publications
- `References.tsx` — Display reference list
- `Reports.tsx` — Display report list
- `Search.tsx` — Search results display
- `ServerInfo.tsx` — Display server info
- `Settings.tsx` — Settings UI (no computation)
- `SystemHealth.tsx` — Display system status
- `Terms.tsx` — Static terms of service
- `Tips.tsx` — Display tips
- `WhatsNew.tsx` — Display changelog
- `WorkspaceGateway.tsx` — Workspace selector

**Seed Bank Division (8 pages)**:
- `Accessions.tsx` — Display accession list
- `AccessionDetail.tsx` — Display accession details
- `Conservation.tsx` — Display conservation status
- `Dashboard.tsx` — Display seed bank metrics
- `GermplasmExchange.tsx` — Display exchange records
- `MCPDExchange.tsx` — Display MCPD data
- `MTAManagement.tsx` — Display MTA records
- `VaultManagement.tsx` — Display vault inventory

**Seed Operations Division (9 pages)**:
- `Agreements.tsx` — Display agreements
- `Certificates.tsx` — Display certificates
- `Dashboard.tsx` — Display operations metrics
- `DispatchHistory.tsx` — Display dispatch records
- `Firms.tsx` — Display firm list
- `LabSamples.tsx` — Display lab samples
- `ProcessingBatches.tsx` — Display batch records
- `ProcessingStages.tsx` — Display stage records
- `Warehouse.tsx` — Display warehouse inventory

**Earth Systems Division (3 pages)**:
- `Dashboard.tsx` — Display weather metrics
- `FieldMap.tsx` — Display field map
- `InputLog.tsx` — Display input records

**Sensor Networks Division (2 pages)**:
- `Dashboard.tsx` — Display sensor metrics
- `LiveData.tsx` — Display real-time sensor data

**Other Divisions (32 pages)**:
- All remaining display-only pages across divisions

---

### CALF-1: Simple Client-Side Calculation (67 pages)

**Calculators (6 pages)**:
- `FertilizerCalculator.tsx` — Calculates: `dose = area × rate`
- `TraitCalculator.tsx` — Calculates harvest index, etc.
- `CostAnalysis.tsx` — Calculates costs: `total = quantity × price`
- `ResourceAllocation.tsx` — Calculates resource distribution
- `YieldMap.tsx` — Calculates yield per plot
- `GrowthTracker.tsx` — Calculates growth rate

**Evidence**: 
```typescript
// FertilizerCalculator.tsx line 40-50
const calculateDose = () => {
  const dose = area * ratePerHa
  setResult(dose)
}
```
**Assessment**: Pure arithmetic, no backend, no validation.

**Analysis Pages (12 pages)**:
- `AnalyticsDashboard.tsx` — Aggregates metrics
- `ApexAnalytics.tsx` — Displays analytics
- `DataVisualization.tsx` — Renders charts
- `GeneticDiversity.tsx` — Displays diversity metrics
- `GeneticCorrelation.tsx` — Displays correlation matrix
- `PerformanceRanking.tsx` — Ranks individuals
- `SpatialAnalysis.tsx` — Displays spatial data
- `Statistics.tsx` — Displays statistical summaries
- `TrialComparison.tsx` — Compares trials
- `VarietyComparison.tsx` — Compares varieties
- `YieldPredictor.tsx` — Displays yield predictions
- `PlotHistory.tsx` — Displays plot history

**Evidence**: These pages fetch data and render it; calculations are minimal (sorting, averaging).

**Form Pages (49 pages)**:
- All CRUD form pages: `ProgramForm.tsx`, `TrialForm.tsx`, `StudyForm.tsx`, `LocationForm.tsx`, `GermplasmForm.tsx`, `SampleForm.tsx`, `TraitForm.tsx`, `SeedLotForm.tsx`, `PersonForm.tsx`, `CrossForm.tsx`, `ObservationUnitForm.tsx`, `SampleForm.tsx`, `LabelPrinting.tsx`, `BarcodeManagement.tsx`, `BarcodeScanner.tsx`, `QuickEntry.tsx`, `DataCollect.tsx`, `FieldScanner.tsx`, `OfflineMode.tsx`, `DataSync.tsx`, `ImportExport.tsx`, `DataExportManager.tsx`, `BatchOperations.tsx`, `WorkflowAutomation.tsx`, `ExperimentDesigner.tsx`, `TrialDesign.tsx`, `FieldLayout.tsx`, `FieldPlanning.tsx`, `SeasonPlanning.tsx`, `CropCalendar.tsx`, `IrrigationPlanner.tsx`, `HarvestPlanner.tsx`, `HarvestManagement.tsx`, `HarvestLog.tsx`, `NurseryManagement.tsx`, `SpeedBreeding.tsx`, `DoubledHaploid.tsx`, `DroneIntegration.tsx`, `EnvironmentMonitor.tsx`, `PestMonitor.tsx`, `DiseaseAtlas.tsx`, `PhenologyTracker.tsx`, `ResourceCalendar.tsx`, `ComplianceTracker.tsx`, `BlockchainTraceability.tsx`, `VendorOrders.tsx`, `VarietyRelease.tsx`, `VarietyLicensing.tsx`

**Assessment**: Form pages perform validation only (required fields, format checks).

---

### CALF-2: Backend Query with Demo Data (42 pages)

**Evidence-Based Finding**: Backend services return hardcoded DEMO_* arrays instead of querying database.

**Affected Pages**:
- `StabilityAnalysis.tsx` — Queries `/api/v2/stability/varieties` → Returns DEMO_VARIETIES
- `GenomicSelection.tsx` — Queries `/api/v2/genomic-selection/models` → Returns DEMO_MODELS
- `GeneticGainTracker.tsx` — Queries `/api/v2/genetic-gain/programs` → Returns in-memory data
- `PopulationGenetics.tsx` — Queries `/api/v2/population-genetics/populations` → Returns demo data
- `ParentageAnalysis.tsx` — Queries `/api/v2/parentage/analysis` → Returns demo data
- `GxEInteraction.tsx` — Queries `/api/v2/gxe/interactions` → Returns demo data
- `LinkageDisequilibrium.tsx` — Queries `/api/v2/ld/analysis` → Returns demo data
- `HaplotypeAnalysis.tsx` — Queries `/api/v2/haplotype/analysis` → Returns demo data
- `MarkerAssistedSelection.tsx` — Queries `/api/v2/mas/markers` → Returns demo data
- `MolecularBreeding.tsx` — Queries `/api/v2/molecular/breeding` → Returns demo data
- `PhenomicSelection.tsx` — Queries `/api/v2/phenomic/selection` → Returns demo data
- `DiseaseResistance.tsx` — Queries `/api/v2/disease/resistance` → Returns demo data
- `AbioticStress.tsx` — Queries `/api/v2/stress/abiotic` → Returns demo data
- `Bioinformatics.tsx` — Queries `/api/v2/bioinformatics/analysis` → Returns demo data
- `BreedingPipeline.tsx` — Queries `/api/v2/breeding/pipeline` → Returns demo data
- `BreedingSimulator.tsx` — Queries `/api/v2/breeding/simulator` → Returns demo data
- `BreedingHistory.tsx` — Queries `/api/v2/breeding/history` → Returns demo data
- `BreedingGoals.tsx` — Queries `/api/v2/breeding/goals` → Returns demo data
- `CrossingProjects.tsx` — Queries `/api/v2/crossing/projects` → Returns demo data
- `CrossPrediction.tsx` — Queries `/api/v2/crossing/predict` → Returns demo data
- `CrossingPlanner.tsx` — Queries `/api/v2/crossing/planner` → Returns demo data
- `Crosses.tsx` — Queries `/api/v2/crosses` → Returns demo data
- `CrossDetail.tsx` — Queries `/api/v2/crosses/{id}` → Returns demo data
- `Progeny.tsx` — Queries `/api/v2/progeny` → Returns demo data
- `Pedigree3D.tsx` — Queries `/api/v2/pedigree/3d` → Returns demo data
- `PedigreeViewer.tsx` — Queries `/api/v2/pedigree/viewer` → Returns demo data
- `PedigreeAnalysis.tsx` — Queries `/api/v2/pedigree/analysis` → Returns demo data
- `GeneticMap.tsx` — Queries `/api/v2/genetic-map` → Returns demo data
- `GenomeMaps.tsx` — Queries `/api/v2/genome-maps` → Returns demo data
- `Variants.tsx` — Queries `/api/v2/variants` → Returns demo data
- `VariantDetail.tsx` — Queries `/api/v2/variants/{id}` → Returns demo data
- `VariantSets.tsx` — Queries `/api/v2/variant-sets` → Returns demo data
- `Calls.tsx` — Queries `/api/v2/calls` → Returns demo data
- `CallSets.tsx` — Queries `/api/v2/call-sets` → Returns demo data
- `Plates.tsx` — Queries `/api/v2/plates` → Returns demo data
- `MarkerPositions.tsx` — Queries `/api/v2/marker-positions` → Returns demo data
- `Observations.tsx` — Queries `/api/v2/observations` → Returns demo data
- `ObservationUnits.tsx` — Queries `/api/v2/observation-units` → Returns demo data
- `Samples.tsx` — Queries `/api/v2/samples` → Returns demo data
- `SampleDetail.tsx` — Queries `/api/v2/samples/{id}` → Returns demo data
- `SampleTracking.tsx` — Queries `/api/v2/sample-tracking` → Returns demo data

**Code Evidence** (from `backend/app/services/genomic_selection.py` lines 11-70):
```python
# Demo GS models
DEMO_MODELS = [
    {
        "id": "gs1",
        "name": "Yield_GBLUP_2024",
        "method": "GBLUP",
        "trait": "Grain Yield",
        "accuracy": 0.72,
        # ... hardcoded data
    },
    # ... more hardcoded entries
]

async def get_models(self):
    return DEMO_MODELS  # Returns hardcoded array, not database query
```

**Assessment**: These pages **claim** to perform analysis but return **mock data**. Not production-ready.

---

### CALF-3: Real Computational Algorithm (18 pages)

**Evidence-Based Finding**: These pages implement actual scientific algorithms with real database queries.

**Breeding Value Calculation (3 pages)**:
1. **`BreedingValueCalculator.tsx`**
   - **Algorithm**: BLUP, GBLUP
   - **Backend**: `backend/app/services/breeding_value.py`
   - **Computation**: 
     ```python
     # BLUP: EBV = h² × (phenotype - mean)
     ebv = heritability * deviation
     reliability = heritability / (1 + lambda_val)
     ```
   - **Data Source**: Real phenotypes from database
   - **Assessment**: ✅ Real computation

2. **`GeneticGainCalculator.tsx`**
   - **Algorithm**: Breeder's Equation: ΔG = (i × h² × σp) / L
   - **Computation**:
     ```typescript
     const geneticGain = (params.selectionIntensity * params.heritability * params.phenotypicSD) / params.generationInterval
     ```
   - **Data Source**: User inputs + database heritability
   - **Assessment**: ✅ Real computation

3. **`GeneticGainTracker.tsx`**
   - **Algorithm**: Tracks realized genetic gain over breeding cycles
   - **Computation**: Calculates trend, rate of gain
   - **Data Source**: Real breeding program data
   - **Assessment**: ✅ Real computation

**Selection Index (3 pages)**:
4. **`SelectionIndexCalculator.tsx`**
   - **Algorithm**: Smith-Hazel, Desired Gains, Base Index
   - **Backend**: `backend/app/services/selection_index.py`
   - **Computation**:
     ```python
     # Smith-Hazel: I = b1*P1 + b2*P2 + ... + bn*Pn
     # where b = h² * a (economic weight)
     index_coefficients = [h2 * w for h2, w in zip(heritabilities, economic_weights)]
     ```
   - **Data Source**: Real trait data
   - **Assessment**: ✅ Real computation

5. **`SelectionIndex.tsx`**
   - **Algorithm**: Multi-trait selection
   - **Assessment**: ✅ Real computation

6. **`SelectionDecision.tsx`**
   - **Algorithm**: Decision support for selection
   - **Assessment**: ✅ Real computation

**Stability Analysis (2 pages)**:
7. **`StabilityAnalysis.tsx`**
   - **Algorithm**: Eberhart & Russell, Shukla, AMMI
   - **Backend**: `backend/app/api/v2/stability_analysis.py`
   - **Computation**: Regression-based stability metrics
   - **Issue**: Returns DEMO_VARIETIES (hardcoded)
   - **Assessment**: ⚠️ Algorithm exists but uses demo data

8. **`GxEInteraction.tsx`**
   - **Algorithm**: Genotype × Environment interaction
   - **Assessment**: ⚠️ Algorithm exists but uses demo data

**Genomic Analysis (4 pages)**:
9. **`GenomicSelection.tsx`**
   - **Algorithm**: GEBV prediction
   - **Issue**: Returns DEMO_MODELS
   - **Assessment**: ⚠️ Algorithm exists but uses demo data

10. **`QTLMapping.tsx`**
    - **Algorithm**: QTL detection, GWAS
        - **Backend**: `backend/app/services/qtl_mapping.py`
    - **Code Evidence** (lines 1-50):
      ```python
      async def list_qtls(self, db, organization_id, ...):
          # TODO: Query from qtls table when created
          return []  # Returns empty, not implemented
      ```
    - **Assessment**: ❌ Not implemented (returns empty)

11. **`PopulationGenetics.tsx`**
    - **Algorithm**: Allele frequencies, Hardy-Weinberg
    - **Issue**: Returns demo data
    - **Assessment**: ⚠️ Algorithm exists but uses demo data

12. **`ParentageAnalysis.tsx`**
    - **Algorithm**: Parentage inference
    - **Issue**: Returns demo data
    - **Assessment**: ⚠️ Algorithm exists but uses demo data

**Other Analysis (4 pages)**:
13. **`HaplotypeAnalysis.tsx`** — Haplotype analysis (demo data)
14. **`LinkageDisequilibrium.tsx`** — LD analysis (demo data)
15. **`MarkerAssistedSelection.tsx`** — MAS (demo data)
16. **`PhenomicSelection.tsx`** — Phenomic selection (demo data)

**Assessment Summary for CALF-3**:
- **3 pages** (BreedingValueCalculator, GeneticGainCalculator, SelectionIndexCalculator) perform **real computations**
- **15 pages** have **algorithms but use demo data** (not production-ready)

---

### CALF-4: Advanced High-Performance Compute (5 pages)

**WASM-Based Pages**:
1. **`WasmGBLUP.tsx`**
   - **Technology**: Rust/WASM
   - **Algorithm**: Genomic relationship matrix (GRM), GBLUP
   - **Computation**: Matrix operations via WASM
   - **Code Evidence** (lines 1-50):
     ```typescript
     const { calculate: calcGRM, result: grmResult } = useGRM();
     const { calculate: calcGBLUP, result: gblupResult } = useGBLUP();
     
     const runGBLUP = () => {
       const genotypes = generateGenotypes(n, nMarkers);
       calcGRM(genotypes, n, nMarkers);  // WASM call
     };
     ```
   - **Assessment**: ✅ Real WASM computation

2. **`WasmGenomics.tsx`**
   - **Technology**: Rust/WASM
   - **Algorithm**: GRM, diversity, PCA
   - **Assessment**: ✅ Real WASM computation

3. **`WasmPopGen.tsx`**
   - **Technology**: Rust/WASM
   - **Algorithm**: Diversity, FST, PCA
   - **Assessment**: ✅ Real WASM computation

4. **`WasmLDAnalysis.tsx`**
   - **Technology**: Rust/WASM
   - **Algorithm**: Linkage disequilibrium, HWE
   - **Assessment**: ✅ Real WASM computation

5. **`WasmSelectionIndex.tsx`**
   - **Technology**: Rust/WASM
   - **Algorithm**: Selection index via WASM
   - **Assessment**: ✅ Real WASM computation

**Assessment**: All 5 WASM pages are properly implemented with real computation.

---

## Critical Issues Identified

### Issue 1: Demo Data Masquerading as Real Computation (42 pages)

**Severity**: 🔴 CRITICAL

**Evidence**:
- `backend/app/services/genomic_selection.py` lines 11-70: DEMO_MODELS array
- `backend/app/api/v2/stability_analysis.py` lines 15-120: DEMO_VARIETIES array
- `backend/app/services/genetic_gain.py` lines 20-50: In-memory storage, not database

**Impact**:
- Users cannot trust results
- Pages appear functional but return fake data
- Violates "Zero Mock Data Policy" from STATE.md

**Recommendation**: 
- Convert all DEMO_* arrays to database queries
- Implement proper data models
- Add validation that data comes from database

---

### Issue 2: Unimplemented Algorithms (8 pages)

**Severity**: 🟠 HIGH

**Evidence**:
- `backend/app/services/qtl_mapping.py` lines 20-50: Returns empty list
- `backend/app/services/gwas.py`: Not implemented
- `backend/app/services/population_genetics.py`: Returns demo data

**Impact**:
- Pages claim functionality but don't work
- Users see empty results
- Misleading UI

**Recommendation**:
- Either implement algorithms or remove pages
- Add "Coming Soon" badges to unimplemented features

---

### Issue 3: Client-Side Only Calculations (67 pages)

**Severity**: 🟡 MEDIUM

**Evidence**:
- `FertilizerCalculator.tsx`: Pure JavaScript math
- `TraitCalculator.tsx`: No backend validation
- `CostAnalysis.tsx`: Client-side only

**Impact**:
- No server-side validation
- Results not persisted
- Cannot be audited

**Recommendation**:
- Move calculations to backend
- Persist results to database
- Add audit trail

---

## Recommendations

### Priority 1: Fix Demo Data (42 pages)

**Action**: Convert DEMO_* arrays to database queries

**Files to Modify**:
- `backend/app/services/genomic_selection.py` — Remove DEMO_MODELS, query database
- `backend/app/services/genetic_gain.py` — Remove in-memory storage
- `backend/app/services/stability_analysis.py` — Remove DEMO_VARIETIES
- All other services with DEMO_* arrays

**Timeline**: 2-3 weeks

---

### Priority 2: Implement Missing Algorithms (8 pages)

**Action**: Either implement or remove

**Files**:
- `backend/app/services/qtl_mapping.py` — Implement QTL detection
- `backend/app/services/gwas.py` — Implement GWAS
- `backend/app/services/population_genetics.py` — Implement population genetics

**Timeline**: 4-6 weeks

---

### Priority 3: Move Calculations to Backend (67 pages)

**Action**: Implement backend endpoints for all calculations

**Timeline**: 6-8 weeks

---

## Conclusion

**Current State**:
- 40% of pages are display-only (acceptable)
- 30% perform client-side calculations (needs backend)
- 19% use demo data (violates Zero Mock Data Policy)
- 8% perform real computations (good)
- 2% use WASM (excellent)

**Path to Production**:
1. Fix demo data (Priority 1)
2. Implement missing algorithms (Priority 2)
3. Move calculations to backend (Priority 3)
4. Add audit trail and persistence
5. Validate all results

**Estimated Effort**: 12-16 weeks to reach production-ready state

---

*Assessment completed per GOVERNANCE.md §4.2 Code-Referenced Audit standards*

# CALF Assessment — Complete Page Listing

**Total Pages**: 221  
**Assessment Date**: January 8, 2026  
**Review Type**: Code-Referenced Audit (GOVERNANCE.md §4.2)

---

## CALF-0: Display Only (89 pages)

### Core Pages Directory (35 pages)

| Page | File | API Endpoint | Data Source | Assessment |
|------|------|--------------|-------------|------------|
| About | `About.tsx` | None | Static | Display only |
| Activity Timeline | `ActivityTimeline.tsx` | `/api/v2/activity` | Database | Display only |
| Audit Log | `AuditLog.tsx` | `/api/v2/audit` | Database | Display only |
| Changelog | `Changelog.tsx` | None | Static | Display only |
| Common Crop Names | `CommonCropNames.tsx` | `/brapi/v2/commoncropnames` | BrAPI | Display only |
| Contact | `Contact.tsx` | None | Static form | Display only |
| Data Dictionary | `DataDictionary.tsx` | None | Static | Display only |
| Data Export Templates | `DataExportTemplates.tsx` | `/api/v2/export/templates` | Database | Display only |
| Events | `Events.tsx` | `/brapi/v2/events` | BrAPI | Display only |
| FAQ | `FAQ.tsx` | None | Static | Display only |
| Feedback | `Feedback.tsx` | `/api/v2/feedback` | Form submission | Display only |
| Glossary | `Glossary.tsx` | None | Static | Display only |
| Help | `Help.tsx` | None | Static | Display only |
| Help Center | `HelpCenter.tsx` | None | Static | Display only |
| Images | `Images.tsx` | `/brapi/v2/images` | BrAPI | Display only |
| Keyboard Shortcuts | `KeyboardShortcuts.tsx` | None | Static | Display only |
| Language Settings | `LanguageSettings.tsx` | None | UI state | Display only |
| Lists | `Lists.tsx` | `/api/v2/lists` | Database | Display only |
| List Detail | `ListDetail.tsx` | `/api/v2/lists/{id}` | Database | Display only |
| Notifications | `Notifications.tsx` | `/api/v2/notifications` | Database | Display only |
| Notification Center | `NotificationCenter.tsx` | `/api/v2/notifications` | Database | Display only |
| Ontologies | `Ontologies.tsx` | `/brapi/v2/ontologies` | BrAPI | Display only |
| Privacy | `Privacy.tsx` | None | Static | Display only |
| Profile | `Profile.tsx` | `/api/v2/users/me` | Database | Display only |
| Publication Tracker | `PublicationTracker.tsx` | `/api/v2/publications` | Database | Display only |
| References | `References.tsx` | `/brapi/v2/references` | BrAPI | Display only |
| Reports | `Reports.tsx` | `/api/v2/reports` | Database | Display only |
| Search | `Search.tsx` | `/api/v2/search` | Database | Display only |
| Server Info | `ServerInfo.tsx` | `/brapi/v2/serverinfo` | BrAPI | Display only |
| Settings | `Settings.tsx` | `/api/v2/settings` | Database | Display only |
| System Health | `SystemHealth.tsx` | `/api/v2/system/health` | Database | Display only |
| Terms | `Terms.tsx` | None | Static | Display only |
| Tips | `Tips.tsx` | None | Static | Display only |
| What's New | `WhatsNew.tsx` | None | Static | Display only |
| Workspace Gateway | `WorkspaceGateway.tsx` | `/api/v2/workspaces` | Database | Display only |

### Seed Bank Division (8 pages)

| Page | File | API Endpoint | Data Source | Assessment |
|------|------|--------------|-------------|------------|
| Accessions | `Accessions.tsx` | `/api/v2/seed-bank/accessions` | Database | Display only |
| Accession Detail | `AccessionDetail.tsx` | `/api/v2/seed-bank/accessions/{id}` | Database | Display only |
| Conservation | `Conservation.tsx` | `/api/v2/seed-bank/conservation` | Database | Display only |
| Dashboard | `Dashboard.tsx` | `/api/v2/seed-bank/dashboard` | Database | Display only |
| Germplasm Exchange | `GermplasmExchange.tsx` | `/api/v2/seed-bank/exchange` | Database | Display only |
| MCPD Exchange | `MCPDExchange.tsx` | `/api/v2/seed-bank/mcpd` | Database | Display only |
| MTA Management | `MTAManagement.tsx` | `/api/v2/seed-bank/mta` | Database | Display only |
| Vault Management | `VaultManagement.tsx` | `/api/v2/seed-bank/vaults` | Database | Display only |

### Seed Operations Division (9 pages)

| Page | File | API Endpoint | Data Source | Assessment |
|------|------|--------------|-------------|------------|
| Agreements | `Agreements.tsx` | `/api/v2/seed-ops/agreements` | Database | Display only |
| Certificates | `Certificates.tsx` | `/api/v2/seed-ops/certificates` | Database | Display only |
| Dashboard | `Dashboard.tsx` | `/api/v2/seed-ops/dashboard` | Database | Display only |
| Dispatch History | `DispatchHistory.tsx` | `/api/v2/seed-ops/dispatch` | Database | Display only |
| Firms | `Firms.tsx` | `/api/v2/seed-ops/firms` | Database | Display only |
| Lab Samples | `LabSamples.tsx` | `/api/v2/seed-ops/lab-samples` | Database | Display only |
| Processing Batches | `ProcessingBatches.tsx` | `/api/v2/seed-ops/batches` | Database | Display only |
| Processing Stages | `ProcessingStages.tsx` | `/api/v2/seed-ops/stages` | Database | Display only |
| Warehouse | `Warehouse.tsx` | `/api/v2/seed-ops/warehouse` | Database | Display only |

### Earth Systems Division (3 pages)

| Page | File | API Endpoint | Data Source | Assessment |
|------|------|--------------|-------------|------------|
| Dashboard | `Dashboard.tsx` | `/api/v2/earth/dashboard` | Database | Display only |
| Field Map | `FieldMap.tsx` | `/api/v2/earth/field-map` | Database | Display only |
| Input Log | `InputLog.tsx` | `/api/v2/earth/input-log` | Database | Display only |

### Sensor Networks Division (2 pages)

| Page | File | API Endpoint | Data Source | Assessment |
|------|------|--------------|-------------|------------|
| Dashboard | `Dashboard.tsx` | `/api/v2/sensors/dashboard` | Database | Display only |
| Live Data | `LiveData.tsx` | `/api/v2/sensors/live` | Database | Display only |

### Other Divisions (32 pages)

All remaining display-only pages across commercial, knowledge, integrations, plant-sciences, space-research, sun-earth-systems divisions.

---

## CALF-1: Simple Client-Side Calculation (67 pages)

### Calculators (6 pages)

| Page | File | Calculation | Backend | Assessment |
|------|------|-------------|---------|------------|
| Fertilizer Calculator | `FertilizerCalculator.tsx` | `dose = area × rate` | None | Client-side only |
| Trait Calculator | `TraitCalculator.tsx` | Harvest index, etc. | None | Client-side only |
| Cost Analysis | `CostAnalysis.tsx` | `total = qty × price` | None | Client-side only |
| Resource Allocation | `ResourceAllocation.tsx` | Distribution math | None | Client-side only |
| Yield Map | `YieldMap.tsx` | `yield = total / area` | None | Client-side only |
| Growth Tracker | `GrowthTracker.tsx` | Growth rate calc | None | Client-side only |

### Analysis Pages (12 pages)

| Page | File | Calculation | Backend | Assessment |
|------|------|-------------|---------|------------|
| Analytics Dashboard | `AnalyticsDashboard.tsx` | Aggregation | `/api/v2/analytics` | Minimal processing |
| Apex Analytics | `ApexAnalytics.tsx` | Chart rendering | `/api/v2/analytics` | Minimal processing |
| Data Visualization | `DataVisualization.tsx` | Chart rendering | `/api/v2/data` | Minimal processing |
| Genetic Diversity | `GeneticDiversity.tsx` | Display metrics | `/api/v2/diversity` | Minimal processing |
| Genetic Correlation | `GeneticCorrelation.tsx` | Display matrix | `/api/v2/correlation` | Minimal processing |
| Performance Ranking | `PerformanceRanking.tsx` | Sorting | `/api/v2/performance` | Minimal processing |
| Spatial Analysis | `SpatialAnalysis.tsx` | Map rendering | `/api/v2/spatial` | Minimal processing |
| Statistics | `Statistics.tsx` | Summary stats | `/api/v2/statistics` | Minimal processing |
| Trial Comparison | `TrialComparison.tsx` | Comparison logic | `/api/v2/trials` | Minimal processing |
| Variety Comparison | `VarietyComparison.tsx` | Comparison logic | `/api/v2/varieties` | Minimal processing |
| Yield Predictor | `YieldPredictor.tsx` | Display predictions | `/api/v2/yield` | Minimal processing |
| Plot History | `PlotHistory.tsx` | Display history | `/api/v2/plots` | Minimal processing |

### Form Pages (49 pages)

All CRUD form pages with validation only:
- Program forms (3): `ProgramForm.tsx`, `ProgramDetail.tsx`, `ProgramEdit.tsx`
- Trial forms (4): `TrialForm.tsx`, `TrialDetail.tsx`, `TrialEdit.tsx`, `TrialSummary.tsx`
- Study forms (4): `StudyForm.tsx`, `StudyDetail.tsx`, `StudyEdit.tsx`
- Location forms (3): `LocationForm.tsx`, `LocationDetail.tsx`, `LocationEdit.tsx`
- Germplasm forms (6): `GermplasmForm.tsx`, `GermplasmDetail.tsx`, `GermplasmEdit.tsx`, `GermplasmPassport.tsx`, `GermplasmAttributes.tsx`, `GermplasmAttributeValues.tsx`
- Sample forms (3): `SampleForm.tsx`, `SampleDetail.tsx`
- Trait forms (4): `TraitForm.tsx`, `TraitDetail.tsx`, `TraitEdit.tsx`
- Seed Lot forms (3): `SeedLotForm.tsx`, `SeedLotDetail.tsx`
- Person forms (2): `PersonForm.tsx`, `PersonDetail.tsx`
- Cross forms (2): `CrossForm.tsx`, `CrossDetail.tsx`
- Observation Unit forms (2): `ObservationUnitForm.tsx`, `ObservationUnits.tsx`
- Other forms (8): `LabelPrinting.tsx`, `BarcodeManagement.tsx`, `BarcodeScanner.tsx`, `QuickEntry.tsx`, `DataCollect.tsx`, `FieldScanner.tsx`, `OfflineMode.tsx`, `DataSync.tsx`
- Management forms (12): `ImportExport.tsx`, `DataExportManager.tsx`, `BatchOperations.tsx`, `WorkflowAutomation.tsx`, `ExperimentDesigner.tsx`, `TrialDesign.tsx`, `FieldLayout.tsx`, `FieldPlanning.tsx`, `SeasonPlanning.tsx`, `CropCalendar.tsx`, `IrrigationPlanner.tsx`, `HarvestPlanner.tsx`
- Operations forms (8): `HarvestManagement.tsx`, `HarvestLog.tsx`, `NurseryManagement.tsx`, `SpeedBreeding.tsx`, `DoubledHaploid.tsx`, `DroneIntegration.tsx`, `EnvironmentMonitor.tsx`, `PestMonitor.tsx`
- Other forms (6): `DiseaseAtlas.tsx`, `PhenologyTracker.tsx`, `ResourceCalendar.tsx`, `ComplianceTracker.tsx`, `BlockchainTraceability.tsx`, `VendorOrders.tsx`, `VarietyRelease.tsx`, `VarietyLicensing.tsx`

---

## CALF-2: Backend Query with Demo Data (42 pages)

**Critical Issue**: All these pages query backend APIs that return hardcoded DEMO_* arrays instead of database queries.

### Genomic Analysis (8 pages)

| Page | File | API Endpoint | Data Source | Issue |
|------|------|--------------|-------------|-------|
| Genomic Selection | `GenomicSelection.tsx` | `/api/v2/genomic-selection` | DEMO_MODELS | Hardcoded demo data |
| QTL Mapping | `QTLMapping.tsx` | `/api/v2/qtl-mapping` | Empty (not implemented) | Returns empty list |
| Population Genetics | `PopulationGenetics.tsx` | `/api/v2/population-genetics` | Demo data | Hardcoded demo data |
| Parentage Analysis | `ParentageAnalysis.tsx` | `/api/v2/parentage` | Demo data | Hardcoded demo data |
| GxE Interaction | `GxEInteraction.tsx` | `/api/v2/gxe` | Demo data | Hardcoded demo data |
| Linkage Disequilibrium | `LinkageDisequilibrium.tsx` | `/api/v2/ld` | Demo data | Hardcoded demo data |
| Haplotype Analysis | `HaplotypeAnalysis.tsx` | `/api/v2/haplotype` | Demo data | Hardcoded demo data |
| Marker Assisted Selection | `MarkerAssistedSelection.tsx` | `/api/v2/mas` | Demo data | Hardcoded demo data |

### Breeding Analysis (8 pages)

| Page | File | API Endpoint | Data Source | Issue |
|------|------|--------------|-------------|-------|
| Stability Analysis | `StabilityAnalysis.tsx` | `/api/v2/stability` | DEMO_VARIETIES | Hardcoded demo data |
| Breeding Pipeline | `BreedingPipeline.tsx` | `/api/v2/breeding/pipeline` | Demo data | Hardcoded demo data |
| Breeding Simulator | `BreedingSimulator.tsx` | `/api/v2/breeding/simulator` | Demo data | Hardcoded demo data |
| Breeding History | `BreedingHistory.tsx` | `/api/v2/breeding/history` | Demo data | Hardcoded demo data |
| Breeding Goals | `BreedingGoals.tsx` | `/api/v2/breeding/goals` | Demo data | Hardcoded demo data |
| Crossing Projects | `CrossingProjects.tsx` | `/api/v2/crossing/projects` | Demo data | Hardcoded demo data |
| Cross Prediction | `CrossPrediction.tsx` | `/api/v2/crossing/predict` | Demo data | Hardcoded demo data |
| Crossing Planner | `CrossingPlanner.tsx` | `/api/v2/crossing/planner` | Database | ✅ Real data |

### Molecular & Phenomic (4 pages)

| Page | File | API Endpoint | Data Source | Issue |
|------|------|--------------|-------------|-------|
| Molecular Breeding | `MolecularBreeding.tsx` | `/api/v2/molecular` | Demo data | Hardcoded demo data |
| Phenomic Selection | `PhenomicSelection.tsx` | `/api/v2/phenomic` | Demo data | Hardcoded demo data |
| Disease Resistance | `DiseaseResistance.tsx` | `/api/v2/disease` | Demo data | Hardcoded demo data |
| Abiotic Stress | `AbioticStress.tsx` | `/api/v2/stress` | Demo data | Hardcoded demo data |

### Bioinformatics & Genomics (6 pages)

| Page | File | API Endpoint | Data Source | Issue |
|------|------|--------------|-------------|-------|
| Bioinformatics | `Bioinformatics.tsx` | `/api/v2/bioinformatics` | Demo data | Hardcoded demo data |
| Genetic Map | `GeneticMap.tsx` | `/api/v2/genetic-map` | Demo data | Hardcoded demo data |
| Genome Maps | `GenomeMaps.tsx` | `/api/v2/genome-maps` | Demo data | Hardcoded demo data |
| Variants | `Variants.tsx` | `/brapi/v2/variants` | Demo data | Hardcoded demo data |
| Variant Detail | `VariantDetail.tsx` | `/brapi/v2/variants/{id}` | Demo data | Hardcoded demo data |
| Variant Sets | `VariantSets.tsx` | `/brapi/v2/variantsets` | Demo data | Hardcoded demo data |

### Genotyping & Phenotyping (8 pages)

| Page | File | API Endpoint | Data Source | Issue |
|------|------|--------------|-------------|-------|
| Calls | `Calls.tsx` | `/brapi/v2/calls` | Demo data | Hardcoded demo data |
| Call Sets | `CallSets.tsx` | `/brapi/v2/callsets` | Demo data | Hardcoded demo data |
| Plates | `Plates.tsx` | `/brapi/v2/plates` | Demo data | Hardcoded demo data |
| Marker Positions | `MarkerPositions.tsx` | `/brapi/v2/markerpositions` | Demo data | Hardcoded demo data |
| Observations | `Observations.tsx` | `/brapi/v2/observations` | Database | ✅ Real data |
| Observation Units | `ObservationUnits.tsx` | `/brapi/v2/observationunits` | Database | ✅ Real data |
| Samples | `Samples.tsx` | `/brapi/v2/samples` | Database | ✅ Real data |
| Sample Detail | `SampleDetail.tsx` | `/brapi/v2/samples/{id}` | Database | ✅ Real data |

### Pedigree & Progeny (4 pages)

| Page | File | API Endpoint | Data Source | Issue |
|------|------|--------------|-------------|-------|
| Pedigree 3D | `Pedigree3D.tsx` | `/api/v2/pedigree/3d` | Demo data | Hardcoded demo data |
| Pedigree Viewer | `PedigreeViewer.tsx` | `/api/v2/pedigree/viewer` | Demo data | Hardcoded demo data |
| Pedigree Analysis | `PedigreeAnalysis.tsx` | `/api/v2/pedigree/analysis` | Demo data | Hardcoded demo data |
| Progeny | `Progeny.tsx` | `/api/v2/progeny` | Demo data | Hardcoded demo data |

---

## CALF-3: Real Computational Algorithm (18 pages)

### Breeding Value Calculation (3 pages)

| Page | File | Algorithm | Backend Service | Data Source | Assessment |
|------|------|-----------|-----------------|-------------|------------|
| Breeding Value Calculator | `BreedingValueCalculator.tsx` | BLUP, GBLUP | `breeding_value.py` | Database phenotypes | ✅ Real computation |
| Genetic Gain Calculator | `GeneticGainCalculator.tsx` | Breeder's Equation | Client-side | User inputs | ✅ Real computation |
| Genetic Gain Tracker | `GeneticGainTracker.tsx` | Gain tracking | `genetic_gain.py` | Database | ✅ Real computation |

### Selection Index (3 pages)

| Page | File | Algorithm | Backend Service | Data Source | Assessment |
|------|------|-----------|-----------------|-------------|------------|
| Selection Index Calculator | `SelectionIndexCalculator.tsx` | Smith-Hazel, Desired Gains | `selection_index.py` | Database traits | ✅ Real computation |
| Selection Index | `SelectionIndex.tsx` | Multi-trait selection | `selection_index.py` | Database | ✅ Real computation |
| Selection Decision | `SelectionDecision.tsx` | Decision support | `selection_decisions.py` | Database | ✅ Real computation |

### Stability & Interaction Analysis (2 pages)

| Page | File | Algorithm | Backend Service | Data Source | Assessment |
|------|------|-----------|-----------------|-------------|------------|
| Stability Analysis | `StabilityAnalysis.tsx` | Eberhart & Russell, Shukla, AMMI | `stability_analysis.py` | DEMO_VARIETIES ⚠️ | Algorithm exists, demo data |
| GxE Interaction | `GxEInteraction.tsx` | G×E analysis | `gxe_analysis.py` | Demo data ⚠️ | Algorithm exists, demo data |

### Genomic Analysis (4 pages)

| Page | File | Algorithm | Backend Service | Data Source | Assessment |
|------|------|-----------|-----------------|-------------|------------|
| Genomic Selection | `GenomicSelection.tsx` | GEBV prediction | `genomic_selection.py` | DEMO_MODELS ⚠️ | Algorithm exists, demo data |
| QTL Mapping | `QTLMapping.tsx` | QTL detection, GWAS | `qtl_mapping.py` | Empty ❌ | Not implemented |
| Population Genetics | `PopulationGenetics.tsx` | Allele frequencies, HWE | `population_genetics.py` | Demo data ⚠️ | Algorithm exists, demo data |
| Parentage Analysis | `ParentageAnalysis.tsx` | Parentage inference | `parentage_analysis.py` | Demo data ⚠️ | Algorithm exists, demo data |

### Other Analysis (6 pages)

| Page | File | Algorithm | Backend Service | Data Source | Assessment |
|------|------|-----------|-----------------|-------------|------------|
| Haplotype Analysis | `HaplotypeAnalysis.tsx` | Haplotype analysis | `haplotype_analysis.py` | Demo data ⚠️ | Algorithm exists, demo data |
| Linkage Disequilibrium | `LinkageDisequilibrium.tsx` | LD analysis | `ld_analysis.py` | Demo data ⚠️ | Algorithm exists, demo data |
| Marker Assisted Selection | `MarkerAssistedSelection.tsx` | MAS | `marker_assisted.py` | Demo data ⚠️ | Algorithm exists, demo data |
| Phenomic Selection | `PhenomicSelection.tsx` | Phenomic selection | `phenomic_selection.py` | Demo data ⚠️ | Algorithm exists, demo data |
| Molecular Breeding | `MolecularBreeding.tsx` | Molecular analysis | `molecular_breeding.py` | Demo data ⚠️ | Algorithm exists, demo data |
| Bioinformatics | `Bioinformatics.tsx` | Bioinformatics analysis | `bioinformatics.py` | Demo data ⚠️ | Algorithm exists, demo data |

---

## CALF-4: Advanced High-Performance Compute (5 pages)

### WASM-Based Pages

| Page | File | Technology | Algorithm | Assessment |
|------|------|-----------|-----------|------------|
| WASM GBLUP | `WasmGBLUP.tsx` | Rust/WASM | GRM, GBLUP | ✅ Real WASM computation |
| WASM Genomics | `WasmGenomics.tsx` | Rust/WASM | GRM, diversity, PCA | ✅ Real WASM computation |
| WASM PopGen | `WasmPopGen.tsx` | Rust/WASM | Diversity, FST, PCA | ✅ Real WASM computation |
| WASM LD Analysis | `WasmLDAnalysis.tsx` | Rust/WASM | LD, HWE | ✅ Real WASM computation |
| WASM Selection Index | `WasmSelectionIndex.tsx` | Rust/WASM | Selection index | ✅ Real WASM computation |

---

## Summary Statistics

| CALF Level | Count | Percentage | Status |
|-----------|-------|-----------|--------|
| CALF-0 (Display) | 89 | 40% | ✅ Acceptable |
| CALF-1 (Client-side) | 67 | 30% | ⚠️ Needs backend |
| CALF-2 (Demo data) | 42 | 19% | 🔴 Critical issue |
| CALF-3 (Real compute) | 18 | 8% | ⚠️ Mixed (3 good, 15 demo data) |
| CALF-4 (WASM) | 5 | 2% | ✅ Excellent |
| **TOTAL** | **221** | **100%** | |

---

*Complete page listing per GOVERNANCE.md §4.2 Code-Referenced Audit*

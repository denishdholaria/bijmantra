<![CDATA[# Bijmantra Page Audit

**Last Updated:** December 25, 2025  
**Total Pages:** 219 (consolidated from 302)  
**Status:** ✅ Functional (192) · 🟡 Demo (10) · 🔴 UI Only (5) · 📦 Removed (12)

---

## 🎄 New Year 2026 Restructure

> **10 divisions → 8 focused modules** for better UX

| Change | Before | After |
|--------|--------|-------|
| Plant Sciences split | 1 module (110 pages) | 3 modules: Breeding (35), Phenotyping (25), Genomics (35) |
| Sensors merged | Separate module (7 pages) | Part of Environment |
| Integration Hub moved | Separate module (1 page) | Part of Settings |
| Commercial renamed | "Commercial" | "Seed Operations" |
| Knowledge trimmed | 10 pages (6 empty) | 5 pages (functional only) |
| Space Research | Separate module | Part of "Research & Innovation" |

---

## Status Legend

| Status | Meaning |
|:------:|:--------|
| ✅ | Functional — Connected to real backend API |
| 🟡 | Demo — UI works with mock/demo data |
| 🔴 | UI Only — Visual mockup, no functionality |
| 📦 | Removed — Empty placeholder removed |

---

## Module 1: Breeding (35 pages)

### Core (8 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Programs | `/programs` | `/brapi/v2/programs` | ✅ |
| Trials | `/trials` | `/brapi/v2/trials` | ✅ |
| Studies | `/studies` | `/brapi/v2/studies` | ✅ |
| Germplasm | `/germplasm` | `/brapi/v2/germplasm` | ✅ |
| Germplasm Comparison | `/germplasm-comparison` | `/api/v2/germplasm-comparison` | ✅ |
| Locations | `/locations` | `/brapi/v2/locations` | ✅ |
| Seasons | `/seasons` | `/brapi/v2/seasons` | ✅ |
| Pipeline | `/pipeline` | `/api/v2/breeding-pipeline` | ✅ |

### Crossing (7 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Crosses | `/crosses` | `/brapi/v2/crosses` | ✅ |
| Crossing Projects | `/crossingprojects` | `/brapi/v2/crossingprojects` | ✅ |
| Planned Crosses | `/plannedcrosses` | `/brapi/v2/plannedcrosses` | ✅ |
| Progeny | `/progeny` | `/api/v2/progeny` | ✅ |
| Pedigree Viewer | `/pedigree` | `/api/v2/pedigree` | ✅ |
| 3D Pedigree Explorer | `/pedigree-3d` | Three.js Client | ✅ |
| Crossing Planner | `/crossingplanner` | `/api/v2/crossing-planner` | ✅ |

### Selection (9 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Selection Index | `/selectionindex` | `/api/v2/selection` | ✅ |
| Index Calculator | `/selection-index-calculator` | `/api/v2/selection` | ✅ |
| Selection Decision | `/selection-decision` | `/api/v2/selection-decisions` | ✅ |
| Parent Selection | `/parent-selection` | `/api/v2/parent-selection` | ✅ |
| Cross Prediction | `/cross-prediction` | `/api/v2/crosses/predict` | ✅ |
| Performance Ranking | `/performance-ranking` | `/api/v2/performance-ranking` | ✅ |
| Genetic Gain | `/geneticgain` | `/api/v2/genetic-gain` | ✅ |
| Gain Tracker | `/genetic-gain-tracker` | `/api/v2/genetic-gain` | ✅ |
| Gain Calculator | `/genetic-gain-calculator` | Client-side | ✅ |

### Phenotyping (8 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Traits | `/traits` | `/brapi/v2/variables` | ✅ |
| Observations | `/observations` | `/brapi/v2/observations` | ✅ |
| Collect Data | `/observations/collect` | `/brapi/v2/observations` | ✅ |
| Observation Units | `/observationunits` | `/brapi/v2/observationunits` | ✅ |
| Events | `/events` | `/brapi/v2/events` | ✅ |
| Images | `/images` | `/brapi/v2/images` | ✅ |
| Data Quality | `/dataquality` | `/api/v2/data-quality` | ✅ |
| Ontologies | `/ontologies` | `/api/v2/ontology` | ✅ |

### Genotyping (11 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Samples | `/samples` | `/brapi/v2/samples` | ✅ |
| Variants | `/variants` | `/api/v2/gwas/variants` | ✅ |
| Allele Matrix | `/allelematrix` | `/brapi/v2/allelematrix` | ✅ |
| Plates | `/plates` | `/brapi/v2/plates` | ✅ |
| Genome Maps | `/genomemaps` | `/brapi/v2/maps` | ✅ |
| Variant Sets | `/variantsets` | `/api/v2/genotyping/variant-sets` | ✅ |
| Calls | `/calls` | `/api/v2/genotyping/calls` | ✅ |
| Call Sets | `/callsets` | `/api/v2/genotyping/call-sets` | ✅ |
| References | `/references` | `/api/v2/genotyping/references` | ✅ |
| Marker Positions | `/markerpositions` | `/api/v2/genotyping/marker-positions` | ✅ |
| Vendor Orders | `/vendororders` | `/api/v2/genotyping/vendor-orders` | ✅ |
]]>
<![CDATA[
### Genomics (18 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Genetic Diversity | `/genetic-diversity` | `/api/v2/genetic-diversity` | ✅ |
| Population Genetics | `/population-genetics` | `/api/v2/population-genetics` | ✅ |
| LD Analysis | `/linkage-disequilibrium` | `/api/v2/gwas/ld` | ✅ |
| Haplotype Analysis | `/haplotype-analysis` | `/api/v2/haplotype` | ✅ |
| Breeding Values | `/breeding-values` | `/api/v2/breeding-value` | ✅ |
| BLUP Calculator | `/breeding-value-calculator` | `/api/v2/breeding-value` | ✅ |
| Genomic Selection | `/genomic-selection` | `/api/v2/genomic-selection` | ✅ |
| Genetic Correlation | `/genetic-correlation` | `/api/v2/phenotype/correlation` | ✅ |
| QTL Mapping | `/qtl-mapping` | `/api/v2/qtl-mapping` | ✅ |
| MAS | `/marker-assisted-selection` | `/api/v2/mas` | ✅ |
| Parentage Analysis | `/parentage-analysis` | `/api/v2/parentage` | ✅ |
| GxE Interaction | `/gxe-interaction` | `/api/v2/gxe` | ✅ |
| Stability Analysis | `/stability-analysis` | `/api/v2/gxe/finlay-wilkinson` | ✅ |
| Trial Network | `/trial-network` | `/api/v2/trial-network` | ✅ |
| Molecular Breeding | `/molecular-breeding` | `/api/v2/molecular-breeding` | ✅ |
| Phenomic Selection | `/phenomic-selection` | `/api/v2/phenomic-selection` | ✅ |
| Speed Breeding | `/speed-breeding` | `/api/v2/speed-breeding` | ✅ |
| Doubled Haploid | `/doubled-haploid` | `/api/v2/doubled-haploid` | ✅ |

### Field Operations (18 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Field Layout | `/fieldlayout` | `/brapi/v2/studies/{id}/layout` | ✅ |
| Field Book | `/fieldbook` | `/brapi/v2/observations` | ✅ |
| Field Map | `/field-map` | `/api/v2/field-map` | ✅ |
| Field Planning | `/field-planning` | `/api/v2/field-planning` | ✅ |
| Field Scanner | `/field-scanner` | `/api/v2/field-scanner` | ✅ |
| Trial Design | `/trialdesign` | `/api/v2/trial-design` | ✅ |
| Trial Planning | `/trialplanning` | `/api/v2/trial-planning` | ✅ |
| Season Planning | `/season-planning` | `/api/v2/field-planning/seasons` | ✅ |
| Resource Allocation | `/resource-allocation` | `/api/v2/resources/*` | ✅ |
| Resource Calendar | `/resource-calendar` | `/api/v2/resources/calendar` | ✅ |
| Harvest | `/harvest` | `/api/v2/harvest` | ✅ |
| Harvest Management | `/harvest-management` | `/api/v2/harvest` | ✅ |
| Harvest Log | `/harvest-log` | `/api/v2/resources/harvest` | ✅ |
| Nursery | `/nursery` | `/api/v2/nursery` | ✅ |
| Phenology Tracker | `/phenology` | `/api/v2/phenology` | ✅ |
| Plot History | `/plot-history` | `/api/v2/plot-history` | ✅ |
| Label Printing | `/labels` | `/api/v2/labels` | ✅ |
| Quick Entry | `/quick-entry` | `/api/v2/quick-entry` | ✅ |

### Analysis Tools (12 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Disease Resistance | `/disease-resistance` | `/api/v2/disease` | ✅ |
| Abiotic Stress | `/abiotic-stress` | `/api/v2/abiotic` | ✅ |
| Bioinformatics | `/bioinformatics` | `/api/v2/bioinformatics` | ✅ |
| Crop Calendar | `/crop-calendar` | `/api/v2/crop-calendar` | ✅ |
| Spatial Analysis | `/spatial-analysis` | `/api/v2/spatial` | ✅ |
| Pedigree Analysis | `/pedigree-analysis` | `/api/v2/pedigree` | ✅ |
| Phenotype Analysis | `/phenotype-analysis` | `/api/v2/phenotype` | ✅ |
| Statistics | `/statistics` | `/api/v2/statistics` | ✅ |
| Phenotype Comparison | `/comparison` | `/brapi/v2/germplasm,observations` | ✅ |
| Trait Calculator | `/calculator` | Client-side | ✅ |
| Soil Analysis | `/soil` | — | 🟡 |
| Fertilizer Calculator | `/fertilizer` | Client-side | ✅ |

### AI & Compute (12 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| WASM Genomics | `/wasm-genomics` | Client-side | ✅ |
| WASM GBLUP | `/wasm-gblup` | Client-side | ✅ |
| WASM PopGen | `/wasm-popgen` | Client-side | ✅ |
| WASM LD Analysis | `/wasm-ld` | Client-side | ✅ |
| WASM Selection Index | `/wasm-selection` | Client-side | ✅ |
| Yield Predictor | `/yield-predictor` | `/api/v2/genomic-selection/yield-predictions` | ✅ |
| Breeding Simulator | `/breeding-simulator` | Three.js Client | ✅ |
| Plant Vision | `/plant-vision` | `/api/v2/vision/*` | ✅ |
| Vision Strategy | `/plant-vision/strategy` | — | 🔴 |
| Disease Atlas | `/disease-atlas` | `/api/v2/disease/*` | ✅ |
| Crop Health | `/crop-health` | `/api/v2/crop-health/*` | ✅ |
| Yield Map | `/yieldmap` | `/brapi/v2/studies,observationunits` | ✅ |

### Germplasm Management (8 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Germplasm Attributes | `/germplasmattributes` | `/brapi/v2/attributes` | ✅ |
| Attribute Values | `/attributevalues` | `/brapi/v2/attributevalues` | ✅ |
| Germplasm Passport | `/germplasm-passport` | `/api/v2/passport` | ✅ |
| Germplasm Search | `/germplasm-search` | `/api/v2/germplasm-search` | ✅ |
| Common Crop Names | `/crops` | `/brapi/v2/commoncropnames` | ✅ |
| Seed Lots | `/seedlots` | `/brapi/v2/seedlots` | ✅ |
| Seed Inventory | `/inventory` | `/api/v2/seed-inventory` | ✅ |
| Germplasm Collection | `/collections` | `/api/v2/collections` | ✅ |

---

## Division 2: Seed Bank (15 pages)

| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Dashboard | `/seed-bank` | Multiple | ✅ |
| Vault Management | `/seed-bank/vault` | `/api/v2/seed-bank/vaults` | ✅ |
| Vault Monitoring | `/seed-bank/monitoring` | `/api/v2/vault-sensors` | ✅ |
| Accessions | `/seed-bank/accessions` | `/api/v2/seed-bank/accessions` | ✅ |
| Register New | `/seed-bank/accessions/new` | `/api/v2/seed-bank/accessions` | ✅ |
| Accession Detail | `/seed-bank/accessions/:id` | `/api/v2/seed-bank/accessions` | ✅ |
| Conservation Status | `/seed-bank/conservation` | `/api/v2/seed-bank/conservation` | ✅ |
| Viability Testing | `/seed-bank/viability` | `/api/v2/seed-bank/viability` | ✅ |
| Regeneration Planning | `/seed-bank/regeneration` | `/api/v2/seed-bank/regeneration` | ✅ |
| Germplasm Exchange | `/seed-bank/exchange` | `/api/v2/seed-bank/exchanges` | ✅ |
| MCPD Exchange | `/seed-bank/mcpd` | `/api/v2/seed-bank/mcpd` | ✅ |
| MTA Management | `/seed-bank/mta` | `/api/v2/mta` | ✅ |
| GRIN/Genesys Search | `/seed-bank/grin-search` | `/api/v2/grin` | ✅ |
| Taxonomy Validator | `/seed-bank/taxonomy` | `/api/v2/grin/validate-taxonomy` | ✅ |
| Offline Data Entry | `/seed-bank/offline` | LocalStorage | 🟡 |

---

## Division 3: Environment (13 pages)

> Merged from Earth Systems + Sun-Earth Systems

### Weather & Climate (9 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Dashboard | `/earth-systems` | `/api/v2/weather/forecast` | ✅ |
| Weather Forecast | `/earth-systems/weather` | `/api/v2/weather/*` | ✅ |
| Soil Data | `/earth-systems/soil` | `/api/v2/field-environment/soil` | ✅ |
| Input Log | `/earth-systems/inputs` | `/api/v2/field-environment/inputs` | ✅ |
| Irrigation | `/earth-systems/irrigation` | `/api/v2/field-environment/irrigation` | ✅ |
| Climate Analysis | `/earth-systems/climate` | `/api/v2/climate/analysis` | ✅ |
| Growing Degrees | `/earth-systems/gdd` | `/api/v2/weather/gdd` | ✅ |
| Drought Monitor | `/earth-systems/drought` | `/api/v2/climate/drought` | ✅ |
| Field Map | `/earth-systems/map` | `/api/v2/field-map` | ✅ |

### Solar & Light (4 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Dashboard | `/sun-earth-systems` | `/api/v2/solar/current` | ✅ |
| Solar Activity | `/sun-earth-systems/solar-activity` | `/api/v2/solar/*` | ✅ |
| Photoperiod | `/sun-earth-systems/photoperiod` | `/api/v2/solar/photoperiod` | ✅ |
| UV Index | `/sun-earth-systems/uv-index` | `/api/v2/solar/uv-index` | ✅ |

---

## Division 4: Sensor Networks (7 pages)

| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Dashboard | `/sensor-networks` | `/api/v2/sensors/stats` | ✅ |
| Devices | `/sensor-networks/devices` | `/api/v2/sensors/devices` | ✅ |
| Live Data | `/sensor-networks/live` | `/api/v2/sensors/readings/live` | ✅ |
| Alerts | `/sensor-networks/alerts` | `/api/v2/sensors/alerts` | ✅ |
| Telemetry | `/sensor-networks/telemetry` | `/brapi/v2/extensions/iot/telemetry` | ✅ |
| Aggregates | `/sensor-networks/aggregates` | `/brapi/v2/extensions/iot/aggregates` | ✅ |
| Environment Link | `/sensor-networks/environment-link` | `/brapi/v2/extensions/iot/devices` | ✅ |

---

## Division 5: Seed Operations & Commercial (22 pages)

### Seed Operations (18 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Dashboard | `/seed-operations` | Multiple | ✅ |
| Samples | `/seed-operations/samples` | `/api/v2/quality/samples` | ✅ |
| Tests | `/seed-operations/testing` | `/api/v2/quality/tests` | ✅ |
| Certificates | `/seed-operations/certificates` | `/api/v2/quality/certificates` | ✅ |
| Quality Gate | `/seed-operations/quality-gate` | `/api/v2/traceability` | ✅ |
| Batches | `/seed-operations/batches` | `/api/v2/processing/batches` | ✅ |
| Stages | `/seed-operations/stages` | `/api/v2/processing/batches/{id}/stages` | ✅ |
| Seed Lots | `/seed-operations/lots` | `/api/v2/traceability/lots` | ✅ |
| Warehouse | `/seed-operations/warehouse` | `/api/v2/seed-inventory` | ✅ |
| Alerts | `/seed-operations/alerts` | `/api/v2/seed-inventory/alerts` | ✅ |
| Create Dispatch | `/seed-operations/dispatch` | `/api/v2/dispatch/orders` | ✅ |
| History | `/seed-operations/dispatch-history` | `/api/v2/dispatch/orders` | ✅ |
| Firms | `/seed-operations/firms` | `/api/v2/dispatch/firms` | ✅ |
| Track Lot | `/seed-operations/track` | `/api/v2/traceability/lots/{id}` | ✅ |
| Lineage | `/seed-operations/lineage` | `/api/v2/traceability/lots/{id}/lineage` | ✅ |
| Barcode Scanner | `/barcode` | `/api/v2/barcode` | ✅ |
| Varieties | `/seed-operations/varieties` | `/api/v2/licensing/varieties` | ✅ |
| Agreements | `/seed-operations/agreements` | `/api/v2/licensing/licenses` | ✅ |

### Commercial/DUS (4 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Dashboard | `/commercial` | `/api/v2/dus/trials`, `/api/v2/licensing` | ✅ |
| DUS Trials | `/commercial/dus-trials` | `/api/v2/dus/trials` | ✅ |
| Crop Templates | `/commercial/dus-crops` | `/api/v2/dus/crops` | ✅ |
| Trial Detail | `/commercial/dus-trials/:id` | `/api/v2/dus/trials/{id}` | ✅ |

---

## Division 6: Space Research (4 pages)

| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Dashboard | `/space-research` | `/api/v2/space/missions,agencies` | ✅ |
| Space Crops | `/space-research/crops` | `/api/v2/space/crops` | ✅ |
| Radiation | `/space-research/radiation` | `/api/v2/space/radiation` | ✅ |
| Life Support | `/space-research/life-support` | `/api/v2/space/life-support` | ✅ |

---

## Division 7: Integration Hub (1 page)

| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Integration Hub | `/integrations` | `/api/v2/integrations` | ✅ |

---

## Division 8: Knowledge (10 pages)

| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Community Forums | `/knowledge/forums` | `/api/v2/forums` | ✅ |
| Forum Topic | `/knowledge/forums/:topicId` | `/api/v2/forums` | ✅ |
| New Topic | `/knowledge/forums/new` | `/api/v2/forums` | ✅ |
| Dashboard | `/knowledge` | — | 🔴 |
| Help Center | `/help` | — | 🔴 |
| Training Hub | `/knowledge/training` | — | 🟡 |
| Glossary | `/glossary` | — | 🔴 |
| FAQ | `/faq` | — | 🔴 |
| About | `/about` | — | 🔴 |
| Vision | `/vision` | — | 🔴 |

---

## Division 9-10: Settings, Admin & Home (32 pages)

### Settings & Admin (20 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Users | `/users` | `/api/v2/users` | ✅ |
| People | `/people` | `/brapi/v2/people` | ✅ |
| Audit Log | `/auditlog` | `/api/v2/audit/security` | ✅ |
| System Health | `/system-health` | `/api/v2/rakshaka` | ✅ |
| Security Dashboard | `/security` | `/api/v2/prahari`, `/api/v2/chaitanya` | ✅ |
| API Explorer | `/serverinfo` | `/api/v2/server/info` | ✅ |
| Dev Progress | `/dev-progress` | `/api/v2/progress` | ✅ |
| Settings | `/settings` | LocalStorage + useDemoMode | ✅ |
| Profile | `/profile` | `/api/v2/profile` | ✅ |
| Team Management | `/team-management` | `/api/v2/teams` | ✅ |
| Collaboration | `/collaboration` | — | 🟡 |
| Workflows | `/workflows` | — | 🟡 |
| System Settings | `/system-settings` | — | 🟡 |
| Offline Mode | `/offline` | — | 🟡 |
| Backup Restore | `/backup` | — | 🟡 |
| Data Dictionary | `/data-dictionary` | `/api/v2/data-dictionary` | ✅ |
| Language Settings | `/languages` | LocalStorage | 🟡 |
| Notification Center | `/notification-center` | — | 🟡 |
| Mobile App | `/mobile-app` | — | 🔴 |
| Keyboard Shortcuts | `/keyboard-shortcuts` | — | 🔴 |

### Home & Dashboard (12 pages)
| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Dashboard | `/dashboard` | Multiple | ✅ |
| AI Insights | `/insights` | `/api/v2/insights` | ✅ |
| Search | `/search` | `/api/v2/search` | ✅ |
| Import/Export | `/import-export` | `/api/v2/export` | ✅ |
| Lists | `/lists` | `/brapi/v2/lists` | ✅ |
| Apex Analytics | `/apex-analytics` | — | 🟡 |
| Notifications | `/notifications` | `/api/v2/notifications` | ✅ |
| Activity | `/activity` | `/api/v2/activity` | ✅ |
| Reports | `/reports` | `/brapi/v2/programs,germplasm,trials,studies,observations` | ✅ |
| Advanced Reports | `/advanced-reports` | — | 🟡 |
| Data Sync | `/data-sync` | — | 🟡 |
| Data Validation | `/data-validation` | `/api/v2/data-validation` | ✅ |

---

## AI Vision Training Ground (5 pages)

| Page | Route | API | Status |
|:-----|:------|:----|:------:|
| Vision Dashboard | `/ai-vision` | `/api/v2/vision/datasets,models` | ✅ |
| Datasets | `/ai-vision/datasets` | `/api/v2/vision/datasets` | ✅ |
| Training | `/ai-vision/training` | `/api/v2/vision/training` | ✅ |
| Registry | `/ai-vision/registry` | `/api/v2/vision/registry` | ✅ |
| Annotate | `/ai-vision/annotate/:id` | `/api/v2/vision/annotations` | ✅ |

---

*Built with 💚 for the global plant breeding community*
]]>
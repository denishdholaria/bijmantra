# Bijmantra Project Status

**Last Updated**: December 13, 2025  
**Version**: 1.0.0  
**Status**: Active Development

---

## Overview

Bijmantra is a BrAPI v2.1 compatible Progressive Web Application for plant breeding management, built on the **Parashakti Framework**.

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| **Frontend Pages** | 298 total | ~190 (64%) Functional |
| **Backend APIs** | 730 endpoints | 100% implemented |
| **BrAPI 2.1** | 74/135 endpoints | 55% compliant |
| **Modules** | 11 divisions | All Active |
| **Build Size** | 5.5MB (PWA) | 113 entries precached |

### Production Readiness

| Status | Count | % |
|--------|-------|---|
| Functional (API connected) | ~190 | 64% |
| Demo Data (mock/hardcoded) | ~70 | 23% |
| UI Only (no backend) | ~38 | 13% |

---

## Infrastructure

| Service | Status | URL |
|---------|--------|-----|
| Frontend | Running | http://localhost:5173 |
| Backend | Running | http://localhost:8000 |
| PostgreSQL | Running | localhost:5432 |
| Redis | Running | localhost:6379 |

---

## Complete Page Audit

**Legend:** FE=Frontend | BE=Backend | F=Functional | D=Demo | U=UI Only

### Division 1: Plant Sciences - Core (8 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Programs | `/programs` | Y | Y | `/brapi/v2/programs` | F |
| Trials | `/trials` | Y | Y | `/brapi/v2/trials` | F |
| Studies | `/studies` | Y | Y | `/brapi/v2/studies` | F |
| Germplasm | `/germplasm` | Y | Y | `/brapi/v2/germplasm` | F |
| Germplasm Comparison | `/germplasm-comparison` | Y | Y | `/api/v2/germplasm-comparison` | F |
| Locations | `/locations` | Y | Y | `/brapi/v2/locations` | F |
| Seasons | `/seasons` | Y | Y | `/brapi/v2/seasons` | F |
| Pipeline | `/pipeline` | Y | Y | `/api/v2/breeding-pipeline` | F |

### Division 1: Plant Sciences - Crossing (6 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Crosses | `/crosses` | Y | Y | `/brapi/v2/crosses` | F |
| Crossing Projects | `/crossingprojects` | Y | Y | `/brapi/v2/crossingprojects` | F |
| Planned Crosses | `/plannedcrosses` | Y | Y | `/brapi/v2/plannedcrosses` | F |
| Progeny | `/progeny` | Y | Y | `/api/v2/progeny` | F |
| Pedigree Viewer | `/pedigree` | Y | Y | `/api/v2/pedigree` | F |
| Crossing Planner | `/crossingplanner` | Y | Y | `/api/v2/crossing-planner` | F |

### Division 1: Plant Sciences - Selection (9 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Selection Index | `/selectionindex` | Y | Y | `/api/v2/selection` | F |
| Index Calculator | `/selection-index-calculator` | Y | Y | `/api/v2/selection` | F |
| Selection Decision | `/selection-decision` | Y | Y | `/api/v2/selection-decisions` | F |
| Parent Selection | `/parent-selection` | Y | Y | `/api/v2/parent-selection` | F |
| Cross Prediction | `/cross-prediction` | Y | Y | `/api/v2/crosses/predict` | F |
| Performance Ranking | `/performance-ranking` | Y | Y | `/api/v2/performance-ranking` | F |
| Genetic Gain | `/geneticgain` | Y | Y | `/api/v2/genetic-gain` | F |
| Gain Tracker | `/genetic-gain-tracker` | Y | Y | `/api/v2/genetic-gain` | F |
| Gain Calculator | `/genetic-gain-calculator` | Y | - | Client-side | F |

### Division 1: Plant Sciences - Phenotyping (8 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Traits | `/traits` | Y | Y | `/brapi/v2/variables` | F |
| Observations | `/observations` | Y | Y | `/brapi/v2/observations` | F |
| Collect Data | `/observations/collect` | Y | Y | `/brapi/v2/observations` | F |
| Observation Units | `/observationunits` | Y | Y | `/brapi/v2/observationunits` | F |
| Events | `/events` | Y | Y | `/brapi/v2/events` | F |
| Images | `/images` | Y | Y | `/brapi/v2/images` | F |
| Data Quality | `/dataquality` | Y | Y | `/api/v2/data-quality` | F |
| Ontologies | `/ontologies` | Y | Y | `/api/v2/ontology` | F |

### Division 1: Plant Sciences - Genotyping (11 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Samples | `/samples` | Y | Y | `/brapi/v2/samples` | F |
| Variants | `/variants` | Y | Y | `/api/v2/gwas/variants` | F |
| Allele Matrix | `/allelematrix` | Y | Y | `/brapi/v2/allelematrix` | F |
| Plates | `/plates` | Y | Y | `/brapi/v2/plates` | F |
| Genome Maps | `/genomemaps` | Y | Y | `/brapi/v2/maps` | F |
| Variant Sets | `/variantsets` | Y | N | None | D |
| Calls | `/calls` | Y | N | None | D |
| Call Sets | `/callsets` | Y | N | None | D |
| References | `/references` | Y | N | None | D |
| Marker Positions | `/markerpositions` | Y | N | None | D |
| Vendor Orders | `/vendororders` | Y | N | None | D |

### Division 1: Plant Sciences - Genomics (18 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Genetic Diversity | `/genetic-diversity` | Y | Y | `/api/v2/genetic-diversity` | F |
| Population Genetics | `/population-genetics` | Y | Y | `/api/v2/population-genetics` | F |
| LD Analysis | `/linkage-disequilibrium` | Y | D | `/api/v2/gwas/ld` | D |
| Haplotype Analysis | `/haplotype-analysis` | Y | N | None | D |
| Breeding Values | `/breeding-values` | Y | Y | `/api/v2/breeding-value` | F |
| BLUP Calculator | `/breeding-value-calculator` | Y | Y | `/api/v2/breeding-value` | F |
| Genomic Selection | `/genomic-selection` | Y | Y | `/api/v2/genomic-selection` | F |
| Genetic Correlation | `/genetic-correlation` | Y | Y | `/api/v2/phenotype/correlation` | F |
| QTL Mapping | `/qtl-mapping` | Y | Y | `/api/v2/qtl-mapping` | F |
| MAS | `/marker-assisted-selection` | Y | Y | `/api/v2/mas` | F |
| Parentage Analysis | `/parentage-analysis` | Y | N | None | D |
| GxE Interaction | `/gxe-interaction` | Y | Y | `/api/v2/gxe` | F |
| Stability Analysis | `/stability-analysis` | Y | Y | `/api/v2/gxe/finlay-wilkinson` | F |
| Trial Network | `/trial-network` | Y | N | None | D |
| Molecular Breeding | `/molecular-breeding` | Y | N | None | D |
| Phenomic Selection | `/phenomic-selection` | Y | N | None | D |
| Speed Breeding | `/speed-breeding` | Y | N | None | D |
| Doubled Haploid | `/doubled-haploid` | Y | N | None | D |


### Division 1: Plant Sciences - Field Ops (18 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Field Layout | `/fieldlayout` | Y | Y | `/brapi/v2/studies/{id}/layout` | F |
| Field Book | `/fieldbook` | Y | Y | `/brapi/v2/observations` | F |
| Field Map | `/field-map` | Y | Y | `/api/v2/field-map` | F |
| Field Planning | `/field-planning` | Y | N | None | D |
| Field Scanner | `/field-scanner` | Y | N | None | D |
| Trial Design | `/trialdesign` | Y | Y | `/api/v2/trial-design` | F |
| Trial Planning | `/trialplanning` | Y | Y | `/api/v2/trial-planning` | F |
| Season Planning | `/season-planning` | Y | N | None | D |
| Resource Allocation | `/resource-allocation` | Y | N | None | D |
| Resource Calendar | `/resource-calendar` | Y | N | None | D |
| Harvest | `/harvest` | Y | Y | `/api/v2/harvest` | F |
| Harvest Management | `/harvest-management` | Y | Y | `/api/v2/harvest` | F |
| Harvest Log | `/harvest-log` | Y | N | None | D |
| Nursery | `/nursery` | Y | Y | `/api/v2/nursery` | F |
| Phenology Tracker | `/phenology` | Y | N | None | D |
| Plot History | `/plot-history` | Y | N | None | D |
| Label Printing | `/labels` | Y | N | None | D |
| Quick Entry | `/quick-entry` | Y | N | None | D |

### Division 1: Plant Sciences - Analysis Tools (12 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Disease Resistance | `/disease-resistance` | Y | Y | `/api/v2/disease` | F |
| Abiotic Stress | `/abiotic-stress` | Y | Y | `/api/v2/abiotic` | F |
| Bioinformatics | `/bioinformatics` | Y | Y | `/api/v2/bioinformatics` | F |
| Crop Calendar | `/crop-calendar` | Y | Y | `/api/v2/crop-calendar` | F |
| Spatial Analysis | `/spatial-analysis` | Y | Y | `/api/v2/spatial` | F |
| Pedigree Analysis | `/pedigree-analysis` | Y | Y | `/api/v2/pedigree` | F |
| Phenotype Analysis | `/phenotype-analysis` | Y | Y | `/api/v2/phenotype` | F |
| Phenotype Comparison | `/comparison` | Y | N | None | D |
| Trait Calculator | `/calculator` | Y | N | None | D |
| Statistics | `/statistics` | Y | N | None | D |
| Soil Analysis | `/soil` | Y | N | None | D |
| Fertilizer Calculator | `/fertilizer` | Y | N | None | D |

### Division 1: Plant Sciences - AI & Compute (12 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| WASM Genomics | `/wasm-genomics` | Y | - | Client-side | F |
| WASM GBLUP | `/wasm-gblup` | Y | - | Client-side | F |
| WASM PopGen | `/wasm-popgen` | Y | - | Client-side | F |
| WASM LD Analysis | `/wasm-ld` | Y | - | Client-side | F |
| WASM Selection Index | `/wasm-selection` | Y | - | Client-side | F |
| Plant Vision | `/plant-vision` | Y | N | None | D |
| Vision Strategy | `/plant-vision/strategy` | Y | N | None | U |
| Disease Atlas | `/disease-atlas` | Y | N | None | D |
| Crop Health | `/crop-health` | Y | N | None | D |
| Yield Predictor | `/yield-predictor` | Y | Y | `/api/v2/genomic-selection/yield-predictions` | F |
| Yield Map | `/yieldmap` | Y | N | None | D |
| Breeding Simulator | `/breeding-simulator` | Y | N | None | D |

### Division 1: Plant Sciences - Germplasm Management (8 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Germplasm Attributes | `/germplasmattributes` | Y | Y | `/brapi/v2/attributes` | F |
| Attribute Values | `/attributevalues` | Y | Y | `/brapi/v2/attributevalues` | F |
| Germplasm Passport | `/germplasm-passport` | Y | Y | `/api/v2/passport` | F |
| Germplasm Search | `/germplasm-search` | Y | N | None | D |
| Germplasm Collection | `/collections` | Y | N | None | D |
| Common Crop Names | `/crops` | Y | Y | `/brapi/v2/commoncropnames` | F |
| Seed Lots | `/seedlots` | Y | Y | `/brapi/v2/seedlots` | F |
| Seed Inventory | `/inventory` | Y | Y | `/api/v2/seed-inventory` | F |

### Division 2: Seed Bank (15 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Dashboard | `/seed-bank` | Y | Y | Multiple | F |
| Vault Management | `/seed-bank/vault` | Y | Y | `/api/v2/seed-bank/vaults` | F |
| Vault Monitoring | `/seed-bank/monitoring` | Y | Y | `/api/v2/vault-sensors` | F |
| Offline Data Entry | `/seed-bank/offline` | Y | D | LocalStorage | D |
| Accessions | `/seed-bank/accessions` | Y | Y | `/api/v2/seed-bank/accessions` | F |
| Register New | `/seed-bank/accessions/new` | Y | Y | `/api/v2/seed-bank/accessions` | F |
| Accession Detail | `/seed-bank/accessions/:id` | Y | Y | `/api/v2/seed-bank/accessions` | F |
| Conservation Status | `/seed-bank/conservation` | Y | Y | `/api/v2/seed-bank/conservation` | F |
| Viability Testing | `/seed-bank/viability` | Y | Y | `/api/v2/seed-bank/viability` | F |
| Regeneration Planning | `/seed-bank/regeneration` | Y | Y | `/api/v2/seed-bank/regeneration` | F |
| Germplasm Exchange | `/seed-bank/exchange` | Y | Y | `/api/v2/seed-bank/exchanges` | F |
| MCPD Exchange | `/seed-bank/mcpd` | Y | Y | `/api/v2/seed-bank/mcpd` | F |
| MTA Management | `/seed-bank/mta` | Y | Y | `/api/v2/mta` | F |
| GRIN/Genesys Search | `/seed-bank/grin-search` | Y | D | `/api/v2/grin` | D |
| Taxonomy Validator | `/seed-bank/taxonomy` | Y | D | `/api/v2/grin/validate-taxonomy` | D |

### Division 3: Earth Systems (9 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Dashboard | `/earth-systems` | Y | Y | `/api/v2/weather/forecast` | D |
| Weather Forecast | `/earth-systems/weather` | Y | Y | `/api/v2/weather/*` | D |
| Climate Analysis | `/earth-systems/climate` | Y | N | None | D |
| Growing Degrees | `/earth-systems/gdd` | Y | N | None | D |
| Drought Monitor | `/earth-systems/drought` | Y | N | None | D |
| Soil Data | `/earth-systems/soil` | Y | Y | `/api/v2/field-environment/soil` | F |
| Input Log | `/earth-systems/inputs` | Y | Y | `/api/v2/field-environment/inputs` | F |
| Irrigation | `/earth-systems/irrigation` | Y | Y | `/api/v2/field-environment/irrigation` | F |
| Field Map | `/earth-systems/map` | Y | N | None | D |

### Division 4: Sun-Earth Systems (4 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Dashboard | `/sun-earth-systems` | Y | Y | `/api/v2/solar/current` | F |
| Solar Activity | `/sun-earth-systems/solar-activity` | Y | Y | `/api/v2/solar/*` | F |
| Photoperiod | `/sun-earth-systems/photoperiod` | Y | Y | `/api/v2/solar/photoperiod` | F |
| UV Index | `/sun-earth-systems/uv-index` | Y | Y | `/api/v2/solar/uv-index` | F |

### Division 5: Sensor Networks (4 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Dashboard | `/sensor-networks` | Y | Y | `/api/v2/sensors/stats` | F |
| Devices | `/sensor-networks/devices` | Y | Y | `/api/v2/sensors/devices` | F |
| Live Data | `/sensor-networks/live` | Y | Y | `/api/v2/sensors/readings/live` | F |
| Alerts | `/sensor-networks/alerts` | Y | Y | `/api/v2/sensors/alerts` | F |

### Division 6: Seed Operations (18 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Dashboard | `/seed-operations` | Y | Y | Multiple | F |
| Samples | `/seed-operations/samples` | Y | Y | `/api/v2/quality/samples` | F |
| Tests | `/seed-operations/testing` | Y | Y | `/api/v2/quality/tests` | F |
| Certificates | `/seed-operations/certificates` | Y | Y | `/api/v2/quality/certificates` | F |
| Quality Gate | `/seed-operations/quality-gate` | Y | Y | `/api/v2/traceability` | F |
| Batches | `/seed-operations/batches` | Y | Y | `/api/v2/processing/batches` | F |
| Stages | `/seed-operations/stages` | Y | Y | `/api/v2/processing/batches/{id}/stages` | F |
| Seed Lots | `/seed-operations/lots` | Y | Y | `/api/v2/traceability/lots` | F |
| Warehouse | `/seed-operations/warehouse` | Y | Y | `/api/v2/seed-inventory` | F |
| Alerts | `/seed-operations/alerts` | Y | Y | `/api/v2/seed-inventory/alerts` | F |
| Create Dispatch | `/seed-operations/dispatch` | Y | Y | `/api/v2/dispatch/orders` | F |
| History | `/seed-operations/dispatch-history` | Y | Y | `/api/v2/dispatch/orders` | F |
| Firms | `/seed-operations/firms` | Y | Y | `/api/v2/dispatch/firms` | F |
| Track Lot | `/seed-operations/track` | Y | Y | `/api/v2/traceability/lots/{id}` | F |
| Lineage | `/seed-operations/lineage` | Y | Y | `/api/v2/traceability/lots/{id}/lineage` | F |
| Barcode Scanner | `/barcode` | Y | Y | `/api/v2/barcode` | F |
| Varieties | `/seed-operations/varieties` | Y | Y | `/api/v2/licensing/varieties` | F |
| Agreements | `/seed-operations/agreements` | Y | Y | `/api/v2/licensing/licenses` | F |

### Division 6b: Commercial/DUS (4 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Dashboard | `/commercial` | Y | Y | `/api/v2/dus/trials`, `/api/v2/licensing` | F |
| DUS Trials | `/commercial/dus-trials` | Y | Y | `/api/v2/dus/trials` | F |
| Crop Templates | `/commercial/dus-crops` | Y | Y | `/api/v2/dus/crops` | F |
| Trial Detail | `/commercial/dus-trials/:id` | Y | Y | `/api/v2/dus/trials/{id}` | F |

### Division 7: Space Research (4 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Dashboard | `/space-research` | Y | Y | `/api/v2/space/missions,agencies` | F |
| Space Crops | `/space-research/crops` | Y | Y | `/api/v2/space/crops` | F |
| Radiation | `/space-research/radiation` | Y | Y | `/api/v2/space/radiation` | F |
| Life Support | `/space-research/life-support` | Y | Y | `/api/v2/space/life-support` | F |

### Division 8: Integration Hub (1 page)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Integration Hub | `/integrations` | Y | Y | `/api/v2/integrations` | F |


### Division 9: Knowledge (10 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Dashboard | `/knowledge` | Y | N | None | U |
| Help Center | `/help` | Y | N | None | U |
| Training Hub | `/knowledge/training` | Y | N | None | D |
| Community Forums | `/knowledge/forums` | Y | Y | `/api/v2/forums` | F |
| Forum Topic | `/knowledge/forums/:topicId` | Y | Y | `/api/v2/forums` | F |
| New Topic | `/knowledge/forums/new` | Y | Y | `/api/v2/forums` | F |
| Glossary | `/glossary` | Y | N | None | U |
| FAQ | `/faq` | Y | N | None | U |
| About | `/about` | Y | N | None | U |
| Vision | `/vision` | Y | N | None | U |

### Division 10: Settings & Admin (20 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Settings | `/settings` | Y | N | LocalStorage | D |
| Profile | `/profile` | Y | N | LocalStorage | D |
| Users | `/users` | Y | Y | `/api/v2/users` | F |
| People | `/people` | Y | Y | `/brapi/v2/people` | F |
| Team Management | `/team-management` | Y | N | None | D |
| Collaboration | `/collaboration` | Y | N | None | D |
| Workflows | `/workflows` | Y | N | None | D |
| Audit Log | `/auditlog` | Y | Y | `/api/v2/audit/security` | F |
| System Health | `/system-health` | Y | Y | `/api/v2/rakshaka` | F |
| Security Dashboard | `/security` | Y | Y | `/api/v2/prahari`, `/api/v2/chaitanya` | F |
| System Settings | `/system-settings` | Y | N | None | D |
| Offline Mode | `/offline` | Y | N | None | D |
| Mobile App | `/mobile-app` | Y | N | None | U |
| API Explorer | `/serverinfo` | Y | Y | `/api/v2/server/info` | F |
| Dev Progress | `/dev-progress` | Y | Y | `/api/v2/progress` | F |
| Backup Restore | `/backup` | Y | N | None | D |
| Data Dictionary | `/data-dictionary` | Y | N | None | D |
| Language Settings | `/languages` | Y | N | LocalStorage | D |
| Keyboard Shortcuts | `/keyboard-shortcuts` | Y | N | None | U |
| Notification Center | `/notification-center` | Y | N | None | D |

### Division 11: Home & Dashboard (12 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Dashboard | `/dashboard` | Y | Y | Multiple | F |
| AI Insights | `/insights` | Y | Y | `/api/v2/insights` | F |
| Apex Analytics | `/apex-analytics` | Y | N | None | D |
| Search | `/search` | Y | Y | `/api/v2/search` | F |
| Notifications | `/notifications` | Y | N | None | D |
| Activity | `/activity` | Y | N | None | D |
| Reports | `/reports` | Y | N | None | D |
| Advanced Reports | `/advanced-reports` | Y | N | None | D |
| Import/Export | `/import-export` | Y | Y | `/api/v2/export` | F |
| Lists | `/lists` | Y | Y | `/brapi/v2/lists` | F |
| Data Sync | `/data-sync` | Y | N | None | D |
| Data Validation | `/data-validation` | Y | N | None | D |

### AI Vision Training Ground (5 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Vision Dashboard | `/ai-vision` | Y | Y | `/api/v2/vision/datasets,models` | F |
| Datasets | `/ai-vision/datasets` | Y | Y | `/api/v2/vision/datasets` | F |
| Training | `/ai-vision/training` | Y | D | `/api/v2/vision/training` | D |
| Registry | `/ai-vision/registry` | Y | D | `/api/v2/vision/registry` | D |
| Annotate | `/ai-vision/annotate/:id` | Y | D | `/api/v2/vision/annotations` | D |

### Miscellaneous Pages (20 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Weather | `/weather` | Y | Y | `/api/v2/weather` | D |
| Weather Forecast | `/weather-forecast` | Y | Y | `/api/v2/weather` | D |
| AI Settings | `/ai-settings` | Y | N | None | D |
| AI Assistant | `/ai-assistant` | Y | Y | `/api/v2/chat` | F |
| Chrome AI | `/chrome-ai` | Y | N | Client-side | D |
| Quick Guide | `/quick-guide` | Y | N | None | U |
| Whats New | `/whats-new` | Y | N | None | U |
| Feedback | `/feedback` | Y | N | None | U |
| Tips | `/tips` | Y | N | None | U |
| Changelog | `/changelog` | Y | N | None | U |
| Contact | `/contact` | Y | N | None | U |
| Privacy | `/privacy` | Y | N | None | U |
| Terms | `/terms` | Y | N | None | U |
| Variety Comparison | `/varietycomparison` | Y | N | None | D |
| Variety Release | `/variety-release` | Y | N | None | D |
| Seed Request | `/seedrequest` | Y | N | None | D |
| Breeding Goals | `/breeding-goals` | Y | N | None | D |
| Breeding History | `/breeding-history` | Y | N | None | D |
| Gene Bank | `/genebank` | Y | N | None | D |
| Genetic Map | `/genetic-map` | Y | N | None | D |

### Additional Utility Pages (15 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Trial Comparison | `/trial-comparison` | Y | N | None | D |
| Trial Summary | `/trial-summary` | Y | N | None | D |
| Data Visualization | `/visualization` | Y | N | None | D |
| API Explorer | `/api-explorer` | Y | N | None | D |
| Batch Operations | `/batch-operations` | Y | N | None | D |
| Sample Tracking | `/sample-tracking` | Y | N | None | D |
| Irrigation Planner | `/irrigation` | Y | N | None | D |
| Pest Monitor | `/pest-monitor` | Y | N | None | D |
| Growth Tracker | `/growth-tracker` | Y | N | None | D |
| Drone Integration | `/drones` | Y | N | None | D |
| IoT Sensors | `/iot-sensors` | Y | N | None | D |
| Blockchain Traceability | `/blockchain` | Y | N | None | D |
| Analytics Dashboard | `/analytics` | Y | N | None | D |
| Workflow Automation | `/workflows` | Y | N | None | D |
| Export Templates | `/export-templates` | Y | N | None | D |

### Research & Planning Pages (12 pages)
| Page | Route | FE | BE | API | Status |
|------|-------|:--:|:--:|-----|:------:|
| Protocol Library | `/protocols` | Y | N | None | D |
| Experiment Designer | `/experiment-designer` | Y | N | None | D |
| Environment Monitor | `/environment-monitor` | Y | N | None | D |
| Cost Analysis | `/cost-analysis` | Y | N | None | D |
| Publication Tracker | `/publications` | Y | N | None | D |
| Compliance Tracker | `/compliance` | Y | N | None | D |
| Market Analysis | `/market-analysis` | Y | N | None | D |
| Stakeholder Portal | `/stakeholders` | Y | N | None | D |
| Training Hub | `/training` | Y | N | None | D |
| Scanner | `/scanner` | Y | Y | `/api/v2/barcode` | F |
| Barcode Management | `/barcode` | Y | Y | `/api/v2/barcode` | F |
| Login | `/login` | Y | Y | `/api/auth` | F |

---

## BrAPI 2.1 Compliance

| Module | Implemented | Total | Coverage |
|--------|-------------|-------|----------|
| BrAPI-Core | 22 | 27 | 81% |
| BrAPI-Phenotyping | 24 | 35 | 69% |
| BrAPI-Genotyping | 12 | 47 | 26% |
| BrAPI-Germplasm | 16 | 26 | 62% |
| **TOTAL** | **74** | **135** | **55%** |

### Key BrAPI Gaps
- **Search Endpoints**: All `/search/*` async endpoints missing (20+)
- **Genotyping**: Calls, CallSets, References, VariantSets not implemented
- **Lists Module**: No list management endpoints
- **Germplasm Sub-endpoints**: MCPD, Pedigree, Progeny endpoints missing

---

## External Integrations

| Integration | API | Status | Notes |
|-------------|-----|:------:|-------|
| BrAPI | Standard | F | 74/135 endpoints |
| GRIN-Global | USDA API | D | Needs API key |
| Genesys | GCDT API | D | Needs API key |
| OpenWeather | Weather API | D | Backend uses mock data |
| NCBI | Bioinformatics | U | Not implemented |

---

## Tech Stack

### Frontend
- React 18 + TypeScript 5 + Vite 5
- Tailwind CSS + shadcn/ui
- TanStack Query + Zustand
- PWA with Workbox

### Backend
- Python 3.11+ + FastAPI
- SQLAlchemy 2.0 async
- PostgreSQL 15 + PostGIS + pgvector
- Redis + MinIO

### Compute Engines
- Python (API, ML)
- Rust/WASM (Genomics)
- Fortran (BLUP, REML)

---

## Quick Start

```bash
make dev              # Start infrastructure
make dev-backend      # http://localhost:8000
make dev-frontend     # http://localhost:5173
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Project overview |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical architecture |
| [.kiro/steering/STATE.md](.kiro/steering/STATE.md) | Current development state |

---

## Audit History

| Date | Changes |
|------|---------|
| 2025-12-13 | MAJOR CORRECTION: Page count updated from 177 to 298 (actual codebase audit) |
| 2025-12-13 | Added missing pages: VariantSets, Calls, CallSets, References, VendorOrders, etc. |
| 2025-12-13 | Added missing routes: /inventory, /crossingplanner, /comparison, /statistics, etc. |
| 2025-12-13 | Corrected status percentages: 60% Functional, 27% Demo, 13% UI Only |
| 2025-12-12 | Weather Forecast corrected to Demo (uses mock data) |
| 2025-12-12 | Initial consolidated audit (merged FUNCTIONALITY_AUDIT + BRAPI_AUDIT) |

---

**Jay Shree Ganeshay Namo Namah!**

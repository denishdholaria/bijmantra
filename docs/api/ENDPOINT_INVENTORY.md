# BijMantra API Endpoint Inventory

**Generated:** 2026-01-03 18:19
**Total Endpoints:** 1447
**Method:** Automated extraction from source code

---

## Summary by Category

| Category | Count |
|----------|-------|
| BrAPI Core | 133 |
| Vision | 50 |
| BrAPI Search | 48 |
| Other | 46 |
| Devguru | 38 |
| Collaboration Hub | 22 |
| Resource Management | 19 |
| Dispatch | 18 |
| Prahari | 18 |
| Sensors | 18 |
| Data Quality | 17 |
| Dus | 17 |
| Licensing | 17 |
| Data Sync | 16 |
| Genotyping | 16 |
| Reports | 16 |
| Harvest | 15 |
| Metrics | 15 |
| Traceability | 15 |
| Vault Sensors | 15 |
| Field Environment | 14 |
| Trial Planning | 14 |
| Chaitanya | 13 |
| Forums | 13 |
| Mta | 13 |
| System Settings | 13 |
| Team Management | 13 |
| Offline Sync | 12 |
| Processing | 12 |
| Rbac | 12 |
| Data Visualization | 11 |
| Ontology | 11 |
| Pedigree | 11 |
| Progress | 11 |
| Qtl Mapping | 11 |
| Search | 11 |
| Seed Inventory | 11 |
| Solar | 11 |
| Space | 11 |
| Spatial | 11 |
| Crop Calendar | 10 |
| Crop Health | 10 |
| Genetic Gain | 10 |
| Genomic Selection | 10 |
| Mas | 10 |
| Notifications | 10 |
| Nursery | 10 |
| Nursery Management | 10 |
| Profile | 10 |
| Quick Entry | 10 |
| Rakshaka | 10 |
| Abiotic | 9 |
| Analytics | 9 |
| Barcode | 9 |
| Collaboration | 9 |
| Crossing Planner | 9 |
| Disease | 9 |
| Field Layout | 9 |
| Field Map | 9 |
| Grin | 9 |
| Label Printing | 9 |
| Languages | 9 |
| Passport | 9 |
| Plot History | 9 |
| Population Genetics | 9 |
| Quality | 9 |
| Selection | 9 |
| Vector | 9 |
| Workflows | 9 |
| Breeding Value | 8 |
| Compute | 8 |
| Data Validation | 8 |
| Events | 8 |
| Field Book | 8 |
| Genetic Diversity | 8 |
| Gwas | 8 |
| Haplotype | 8 |
| Parent Selection | 8 |
| Parentage | 8 |
| Phenology | 8 |
| Rls | 8 |
| Security Audit | 8 |
| Selection Decisions | 8 |
| Trial Network | 8 |
| Trial Summary | 8 |
| Bioinformatics | 7 |
| BrAPI IoT Extensions | 7 |
| Breeding Pipeline | 7 |
| Doubled Haploid | 7 |
| Export | 7 |
| Field Planning | 7 |
| Integrations | 7 |
| Lists | 7 |
| Performance Ranking | 7 |
| Phenotype | 7 |
| Speed Breeding | 7 |
| Stability Analysis | 7 |
| Statistics | 7 |
| Trial Design | 7 |
| Warehouse | 7 |
| Audit | 6 |
| Backup | 6 |
| Field Scanner | 6 |
| Germplasm Collection | 6 |
| Phenomic Selection | 6 |
| Progeny | 6 |
| Tasks | 6 |
| Weather | 6 |
| Data Dictionary | 5 |
| Germplasm Comparison | 5 |
| Gxe | 5 |
| Locations | 5 |
| Molecular Breeding | 5 |
| Phenotype Comparison | 5 |
| Programs | 5 |
| Seasons | 5 |
| Studies | 5 |
| Trials | 5 |
| Yield Map | 5 |
| Authentication | 4 |
| Chat | 4 |
| Crosses | 4 |
| Germplasm Search | 4 |
| Voice | 4 |
| Activity | 3 |
| Climate | 3 |
| Insights | 2 |
| Commoncropnames | 1 |
| Serverinfo | 1 |
| Studytypes | 1 |

---

## Summary by HTTP Method

| Method | Count |
|--------|-------|
| GET | 894 |
| POST | 387 |
| PUT | 65 |
| PATCH | 37 |
| DELETE | 64 |

---

## Complete Endpoint Listing

### Abiotic (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/calculate/indices` | api/v2/abiotic.py |
| GET | `/api/v2/categories` | api/v2/abiotic.py |
| GET | `/api/v2/crops` | api/v2/abiotic.py |
| GET | `/api/v2/genes` | api/v2/abiotic.py |
| GET | `/api/v2/genes/{gene_id}` | api/v2/abiotic.py |
| GET | `/api/v2/screening-protocols` | api/v2/abiotic.py |
| GET | `/api/v2/statistics` | api/v2/abiotic.py |
| GET | `/api/v2/stress-types` | api/v2/abiotic.py |
| GET | `/api/v2/stress-types/{stress_id}` | api/v2/abiotic.py |

### Activity (3 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/entities` | api/v2/activity.py |
| GET | `/api/v2/stats` | api/v2/activity.py |
| GET | `/api/v2/users` | api/v2/activity.py |

### Analytics (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/compute/gblup` | api/v2/analytics.py |
| GET | `/api/v2/compute/{job_id}` | api/v2/analytics.py |
| GET | `/api/v2/correlations` | api/v2/analytics.py |
| GET | `/api/v2/genetic-gain` | api/v2/analytics.py |
| GET | `/api/v2/heritabilities` | api/v2/analytics.py |
| GET | `/api/v2/insights` | api/v2/analytics.py |
| GET | `/api/v2/selection-response` | api/v2/analytics.py |
| GET | `/api/v2/summary` | api/v2/analytics.py |
| GET | `/api/v2/veena-summary` | api/v2/analytics.py |

### Audit (6 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/entity/{entity_type}/{entity_id}/diff` | api/v2/audit.py |
| GET | `/api/v2/entity/{entity_type}/{entity_id}/history` | api/v2/audit.py |
| GET | `/api/v2/logs` | api/v2/audit.py |
| GET | `/api/v2/security` | api/v2/audit.py |
| GET | `/api/v2/stats` | api/v2/audit.py |
| GET | `/api/v2/user/{user_id}/activity` | api/v2/audit.py |

### Authentication (4 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/login` | api/auth.py |
| GET | `/api/me` | api/auth.py |
| POST | `/api/register` | api/auth.py |
| POST | `/api/reset-rate-limit` | api/auth.py |

### Backup (6 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/` | api/v2/backup.py |
| POST | `/api/v2/create` | api/v2/backup.py |
| GET | `/api/v2/download/{backup_id}` | api/v2/backup.py |
| POST | `/api/v2/restore` | api/v2/backup.py |
| GET | `/api/v2/stats` | api/v2/backup.py |
| DELETE | `/api/v2/{backup_id}` | api/v2/backup.py |

### Barcode (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/entity-types/reference` | api/v2/barcode.py |
| POST | `/api/v2/generate` | api/v2/barcode.py |
| GET | `/api/v2/lookup/{barcode_value}` | api/v2/barcode.py |
| POST | `/api/v2/print` | api/v2/barcode.py |
| POST | `/api/v2/scan` | api/v2/barcode.py |
| GET | `/api/v2/scans` | api/v2/barcode.py |
| GET | `/api/v2/statistics` | api/v2/barcode.py |
| DELETE | `/api/v2/{barcode_id}` | api/v2/barcode.py |
| GET | `/api/v2/{barcode_id}` | api/v2/barcode.py |

### Bioinformatics (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/analyze` | api/v2/bioinformatics.py |
| GET | `/api/v2/enzymes` | api/v2/bioinformatics.py |
| POST | `/api/v2/primers` | api/v2/bioinformatics.py |
| POST | `/api/v2/restriction` | api/v2/bioinformatics.py |
| POST | `/api/v2/reverse-complement` | api/v2/bioinformatics.py |
| POST | `/api/v2/tm` | api/v2/bioinformatics.py |
| POST | `/api/v2/translate` | api/v2/bioinformatics.py |

### BrAPI Core (133 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/brapi/v2/allelematrix` | api/brapi/allelematrix.py |
| GET | `/brapi/v2/attributes` | api/brapi/attributes.py |
| POST | `/brapi/v2/attributes` | api/brapi/attributes.py |
| GET | `/brapi/v2/attributes/categories` | api/brapi/attributes.py |
| GET | `/brapi/v2/attributes/{attributeDbId}` | api/brapi/attributes.py |
| PUT | `/brapi/v2/attributes/{attributeDbId}` | api/brapi/attributes.py |
| GET | `/brapi/v2/attributevalues` | api/brapi/attributevalues.py |
| POST | `/brapi/v2/attributevalues` | api/brapi/attributevalues.py |
| GET | `/brapi/v2/attributevalues/{attributeValueDbId}` | api/brapi/attributevalues.py |
| PUT | `/brapi/v2/attributevalues/{attributeValueDbId}` | api/brapi/attributevalues.py |
| GET | `/brapi/v2/breedingmethods` | api/brapi/breedingmethods.py |
| GET | `/brapi/v2/breedingmethods/{breedingMethodDbId}` | api/brapi/breedingmethods.py |
| GET | `/brapi/v2/calls` | api/brapi/calls.py |
| PUT | `/brapi/v2/calls` | api/brapi/calls.py |
| GET | `/brapi/v2/callsets` | api/brapi/callsets.py |
| GET | `/brapi/v2/callsets/{callSetDbId}` | api/brapi/callsets.py |
| GET | `/brapi/v2/callsets/{callSetDbId}/calls` | api/brapi/callsets.py |
| GET | `/brapi/v2/crosses` | api/brapi/crosses.py |
| POST | `/brapi/v2/crosses` | api/brapi/crosses.py |
| PUT | `/brapi/v2/crosses` | api/brapi/crosses.py |
| GET | `/brapi/v2/crosses/{crossDbId}` | api/brapi/crosses.py |
| GET | `/brapi/v2/crossingprojects` | api/brapi/crossingprojects.py |
| POST | `/brapi/v2/crossingprojects` | api/brapi/crossingprojects.py |
| DELETE | `/brapi/v2/crossingprojects/{crossingProjectDbId}` | api/brapi/crossingprojects.py |
| GET | `/brapi/v2/crossingprojects/{crossingProjectDbId}` | api/brapi/crossingprojects.py |
| PUT | `/brapi/v2/crossingprojects/{crossingProjectDbId}` | api/brapi/crossingprojects.py |
| POST | `/brapi/v2/delete/images` | api/brapi/images.py |
| POST | `/brapi/v2/delete/observations` | api/brapi/observations.py |
| GET | `/brapi/v2/events` | api/brapi/events.py |
| POST | `/brapi/v2/events` | api/brapi/events.py |
| GET | `/brapi/v2/events/{eventDbId}` | api/brapi/events.py |
| GET | `/brapi/v2/germplasm` | api/brapi/germplasm.py |
| POST | `/brapi/v2/germplasm` | api/brapi/germplasm.py |
| DELETE | `/brapi/v2/germplasm/{germplasmDbId}` | api/brapi/germplasm.py |
| GET | `/brapi/v2/germplasm/{germplasmDbId}` | api/brapi/germplasm.py |
| PUT | `/brapi/v2/germplasm/{germplasmDbId}` | api/brapi/germplasm.py |
| GET | `/brapi/v2/germplasm/{germplasmDbId}/mcpd` | api/brapi/germplasm.py |
| GET | `/brapi/v2/germplasm/{germplasmDbId}/pedigree` | api/brapi/germplasm.py |
| GET | `/brapi/v2/germplasm/{germplasmDbId}/progeny` | api/brapi/germplasm.py |
| GET | `/brapi/v2/images` | api/brapi/images.py |
| POST | `/brapi/v2/images` | api/brapi/images.py |
| GET | `/brapi/v2/images/{imageDbId}` | api/brapi/images.py |
| PUT | `/brapi/v2/images/{imageDbId}` | api/brapi/images.py |
| PUT | `/brapi/v2/images/{imageDbId}/imagecontent` | api/brapi/images.py |
| GET | `/brapi/v2/maps` | api/brapi/maps.py |
| GET | `/brapi/v2/maps/{mapDbId}` | api/brapi/maps.py |
| GET | `/brapi/v2/maps/{mapDbId}/linkagegroups` | api/brapi/maps.py |
| GET | `/brapi/v2/markerpositions` | api/brapi/markerpositions.py |
| GET | `/brapi/v2/methods` | api/brapi/methods.py |
| POST | `/brapi/v2/methods` | api/brapi/methods.py |
| GET | `/brapi/v2/methods/{methodDbId}` | api/brapi/methods.py |
| PUT | `/brapi/v2/methods/{methodDbId}` | api/brapi/methods.py |
| GET | `/brapi/v2/observationlevels` | api/brapi/observationlevels.py |
| GET | `/brapi/v2/observations` | api/brapi/observations.py |
| POST | `/brapi/v2/observations` | api/brapi/observations.py |
| PUT | `/brapi/v2/observations` | api/brapi/observations.py |
| GET | `/brapi/v2/observations/table` | api/brapi/observations.py |
| GET | `/brapi/v2/observations/{observationDbId}` | api/brapi/observations.py |
| PUT | `/brapi/v2/observations/{observationDbId}` | api/brapi/observations.py |
| GET | `/brapi/v2/observationunits` | api/brapi/observationunits.py |
| POST | `/brapi/v2/observationunits` | api/brapi/observationunits.py |
| PUT | `/brapi/v2/observationunits` | api/brapi/observationunits.py |
| GET | `/brapi/v2/observationunits/table` | api/brapi/observationunits.py |
| GET | `/brapi/v2/observationunits/{observationUnitDbId}` | api/brapi/observationunits.py |
| PUT | `/brapi/v2/observationunits/{observationUnitDbId}` | api/brapi/observationunits.py |
| GET | `/brapi/v2/ontologies` | api/brapi/ontologies.py |
| POST | `/brapi/v2/ontologies` | api/brapi/ontologies.py |
| DELETE | `/brapi/v2/ontologies/{ontologyDbId}` | api/brapi/ontologies.py |
| GET | `/brapi/v2/ontologies/{ontologyDbId}` | api/brapi/ontologies.py |
| PUT | `/brapi/v2/ontologies/{ontologyDbId}` | api/brapi/ontologies.py |
| GET | `/brapi/v2/people` | api/brapi/people.py |
| POST | `/brapi/v2/people` | api/brapi/people.py |
| DELETE | `/brapi/v2/people/{personDbId}` | api/brapi/people.py |
| GET | `/brapi/v2/people/{personDbId}` | api/brapi/people.py |
| PUT | `/brapi/v2/people/{personDbId}` | api/brapi/people.py |
| GET | `/brapi/v2/plannedcrosses` | api/brapi/plannedcrosses.py |
| POST | `/brapi/v2/plannedcrosses` | api/brapi/plannedcrosses.py |
| PUT | `/brapi/v2/plannedcrosses` | api/brapi/plannedcrosses.py |
| DELETE | `/brapi/v2/plannedcrosses/{plannedCrossDbId}` | api/brapi/plannedcrosses.py |
| GET | `/brapi/v2/plannedcrosses/{plannedCrossDbId}` | api/brapi/plannedcrosses.py |
| GET | `/brapi/v2/plates` | api/brapi/plates.py |
| POST | `/brapi/v2/plates` | api/brapi/plates.py |
| PUT | `/brapi/v2/plates` | api/brapi/plates.py |
| DELETE | `/brapi/v2/plates/{plateDbId}` | api/brapi/plates.py |
| GET | `/brapi/v2/plates/{plateDbId}` | api/brapi/plates.py |
| GET | `/brapi/v2/references` | api/brapi/references.py |
| GET | `/brapi/v2/references/{referenceDbId}` | api/brapi/references.py |
| GET | `/brapi/v2/references/{referenceDbId}/bases` | api/brapi/references.py |
| GET | `/brapi/v2/referencesets` | api/brapi/referencesets.py |
| GET | `/brapi/v2/referencesets/{referenceSetDbId}` | api/brapi/referencesets.py |
| GET | `/brapi/v2/samples` | api/brapi/samples.py |
| POST | `/brapi/v2/samples` | api/brapi/samples.py |
| PUT | `/brapi/v2/samples` | api/brapi/samples.py |
| DELETE | `/brapi/v2/samples/{sampleDbId}` | api/brapi/samples.py |
| GET | `/brapi/v2/samples/{sampleDbId}` | api/brapi/samples.py |
| PUT | `/brapi/v2/samples/{sampleDbId}` | api/brapi/samples.py |
| GET | `/brapi/v2/scales` | api/brapi/scales.py |
| POST | `/brapi/v2/scales` | api/brapi/scales.py |
| GET | `/brapi/v2/scales/{scaleDbId}` | api/brapi/scales.py |
| PUT | `/brapi/v2/scales/{scaleDbId}` | api/brapi/scales.py |
| GET | `/brapi/v2/seedlots` | api/brapi/seedlots.py |
| POST | `/brapi/v2/seedlots` | api/brapi/seedlots.py |
| GET | `/brapi/v2/seedlots/transactions` | api/brapi/seedlots.py |
| POST | `/brapi/v2/seedlots/transactions` | api/brapi/seedlots.py |
| GET | `/brapi/v2/seedlots/{seedLotDbId}` | api/brapi/seedlots.py |
| PUT | `/brapi/v2/seedlots/{seedLotDbId}` | api/brapi/seedlots.py |
| GET | `/brapi/v2/seedlots/{seedLotDbId}/transactions` | api/brapi/seedlots.py |
| GET | `/brapi/v2/traits` | api/brapi/traits.py |
| POST | `/brapi/v2/traits` | api/brapi/traits.py |
| GET | `/brapi/v2/traits/{observationVariableDbId}` | api/brapi/traits.py |
| PUT | `/brapi/v2/traits/{traitDbId}` | api/brapi/traits.py |
| GET | `/brapi/v2/variables` | api/brapi/variables.py |
| POST | `/brapi/v2/variables` | api/brapi/variables.py |
| DELETE | `/brapi/v2/variables/{observationVariableDbId}` | api/brapi/variables.py |
| GET | `/brapi/v2/variables/{observationVariableDbId}` | api/brapi/variables.py |
| PUT | `/brapi/v2/variables/{observationVariableDbId}` | api/brapi/variables.py |
| GET | `/brapi/v2/variants` | api/brapi/variants.py |
| GET | `/brapi/v2/variants/{variantDbId}` | api/brapi/variants.py |
| GET | `/brapi/v2/variants/{variantDbId}/calls` | api/brapi/variants.py |
| GET | `/brapi/v2/variantsets` | api/brapi/variantsets.py |
| POST | `/brapi/v2/variantsets/extract` | api/brapi/variantsets.py |
| GET | `/brapi/v2/variantsets/{variantSetDbId}` | api/brapi/variantsets.py |
| GET | `/brapi/v2/variantsets/{variantSetDbId}/calls` | api/brapi/variantsets.py |
| GET | `/brapi/v2/variantsets/{variantSetDbId}/callsets` | api/brapi/variantsets.py |
| GET | `/brapi/v2/variantsets/{variantSetDbId}/variants` | api/brapi/variantsets.py |
| GET | `/brapi/v2/vendor/orders` | api/brapi/vendor.py |
| POST | `/brapi/v2/vendor/orders` | api/brapi/vendor.py |
| GET | `/brapi/v2/vendor/orders/{orderId}/plates` | api/brapi/vendor.py |
| GET | `/brapi/v2/vendor/orders/{orderId}/results` | api/brapi/vendor.py |
| GET | `/brapi/v2/vendor/orders/{orderId}/status` | api/brapi/vendor.py |
| POST | `/brapi/v2/vendor/plates` | api/brapi/vendor.py |
| GET | `/brapi/v2/vendor/plates/{submissionId}` | api/brapi/vendor.py |
| GET | `/brapi/v2/vendor/specifications` | api/brapi/vendor.py |

### BrAPI IoT Extensions (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/brapi/v2/extensions/iot/aggregates` | api/brapi/extensions/iot.py |
| GET | `/brapi/v2/extensions/iot/alerts` | api/brapi/extensions/iot.py |
| GET | `/brapi/v2/extensions/iot/devices` | api/brapi/extensions/iot.py |
| GET | `/brapi/v2/extensions/iot/environmental-parameters` | api/brapi/extensions/iot.py |
| GET | `/brapi/v2/extensions/iot/sensor-types` | api/brapi/extensions/iot.py |
| GET | `/brapi/v2/extensions/iot/sensors` | api/brapi/extensions/iot.py |
| GET | `/brapi/v2/extensions/iot/telemetry` | api/brapi/extensions/iot.py |

### BrAPI Search (48 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/brapi/v2/search/allelematrix` | api/brapi/search.py |
| GET | `/brapi/v2/search/allelematrix/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/attributes` | api/brapi/search.py |
| GET | `/brapi/v2/search/attributes/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/attributevalues` | api/brapi/search.py |
| GET | `/brapi/v2/search/attributevalues/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/calls` | api/brapi/search.py |
| GET | `/brapi/v2/search/calls/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/callsets` | api/brapi/search.py |
| GET | `/brapi/v2/search/callsets/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/germplasm` | api/brapi/search.py |
| GET | `/brapi/v2/search/germplasm/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/images` | api/brapi/search.py |
| GET | `/brapi/v2/search/images/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/lists` | api/brapi/search.py |
| GET | `/brapi/v2/search/lists/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/locations` | api/brapi/search.py |
| GET | `/brapi/v2/search/locations/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/markerpositions` | api/brapi/search.py |
| GET | `/brapi/v2/search/markerpositions/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/observations` | api/brapi/search.py |
| GET | `/brapi/v2/search/observations/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/observationunits` | api/brapi/search.py |
| GET | `/brapi/v2/search/observationunits/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/pedigree` | api/brapi/search.py |
| GET | `/brapi/v2/search/pedigree/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/people` | api/brapi/search.py |
| GET | `/brapi/v2/search/people/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/plates` | api/brapi/search.py |
| GET | `/brapi/v2/search/plates/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/programs` | api/brapi/search.py |
| GET | `/brapi/v2/search/programs/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/references` | api/brapi/search.py |
| GET | `/brapi/v2/search/references/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/referencesets` | api/brapi/search.py |
| GET | `/brapi/v2/search/referencesets/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/samples` | api/brapi/search.py |
| GET | `/brapi/v2/search/samples/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/studies` | api/brapi/search.py |
| GET | `/brapi/v2/search/studies/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/trials` | api/brapi/search.py |
| GET | `/brapi/v2/search/trials/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/variables` | api/brapi/search.py |
| GET | `/brapi/v2/search/variables/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/variants` | api/brapi/search.py |
| GET | `/brapi/v2/search/variants/{searchResultsDbId}` | api/brapi/search.py |
| POST | `/brapi/v2/search/variantsets` | api/brapi/search.py |
| GET | `/brapi/v2/search/variantsets/{searchResultsDbId}` | api/brapi/search.py |

### Breeding Pipeline (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/crops` | api/v2/breeding_pipeline.py |
| GET | `/api/v2/programs` | api/v2/breeding_pipeline.py |
| GET | `/api/v2/stage-summary` | api/v2/breeding_pipeline.py |
| GET | `/api/v2/stages` | api/v2/breeding_pipeline.py |
| GET | `/api/v2/statistics` | api/v2/breeding_pipeline.py |
| GET | `/api/v2/{entry_id}` | api/v2/breeding_pipeline.py |
| POST | `/api/v2/{entry_id}/advance` | api/v2/breeding_pipeline.py |

### Breeding Value (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/accuracy` | api/v2/breeding_value.py |
| GET | `/api/v2/analyses` | api/v2/breeding_value.py |
| GET | `/api/v2/analyses/{analysis_id}` | api/v2/breeding_value.py |
| POST | `/api/v2/blup` | api/v2/breeding_value.py |
| POST | `/api/v2/gblup` | api/v2/breeding_value.py |
| GET | `/api/v2/methods` | api/v2/breeding_value.py |
| POST | `/api/v2/predict-cross` | api/v2/breeding_value.py |
| POST | `/api/v2/rank-candidates` | api/v2/breeding_value.py |

### Chaitanya (13 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/actions` | api/v2/chaitanya.py |
| POST | `/api/v2/anomaly` | api/v2/chaitanya.py |
| PUT | `/api/v2/auto-response` | api/v2/chaitanya.py |
| GET | `/api/v2/config` | api/v2/chaitanya.py |
| PUT | `/api/v2/config/thresholds` | api/v2/chaitanya.py |
| GET | `/api/v2/dashboard` | api/v2/chaitanya.py |
| POST | `/api/v2/event` | api/v2/chaitanya.py |
| GET | `/api/v2/posture` | api/v2/chaitanya.py |
| PUT | `/api/v2/posture` | api/v2/chaitanya.py |
| GET | `/api/v2/posture/history` | api/v2/chaitanya.py |
| GET | `/api/v2/security-config` | api/v2/chaitanya.py |
| GET | `/api/v2/status` | api/v2/chaitanya.py |
| GET | `/api/v2/storage-stats` | api/v2/chaitanya.py |

### Chat (4 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/` | api/v2/chat.py |
| POST | `/api/v2/context` | api/v2/chat.py |
| GET | `/api/v2/health` | api/v2/chat.py |
| GET | `/api/v2/status` | api/v2/chat.py |

### Climate (3 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/analysis/{location_id}` | api/v2/climate.py |
| GET | `/api/v2/drought/{location_id}` | api/v2/climate.py |
| GET | `/api/v2/trends/{location_id}` | api/v2/climate.py |

### Collaboration (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/activity` | api/v2/collaboration.py |
| GET | `/api/v2/conversations` | api/v2/collaboration.py |
| POST | `/api/v2/messages` | api/v2/collaboration.py |
| GET | `/api/v2/messages/{conversation_id}` | api/v2/collaboration.py |
| POST | `/api/v2/presence` | api/v2/collaboration.py |
| POST | `/api/v2/share-item` | api/v2/collaboration.py |
| GET | `/api/v2/shared-items` | api/v2/collaboration.py |
| GET | `/api/v2/stats` | api/v2/collaboration.py |
| GET | `/api/v2/team-members` | api/v2/collaboration.py |

### Collaboration Hub (22 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/activities` | api/v2/collaboration_hub.py |
| POST | `/api/v2/activities` | api/v2/collaboration_hub.py |
| GET | `/api/v2/comments` | api/v2/collaboration_hub.py |
| POST | `/api/v2/comments` | api/v2/collaboration_hub.py |
| DELETE | `/api/v2/comments/{comment_id}` | api/v2/collaboration_hub.py |
| GET | `/api/v2/members` | api/v2/collaboration_hub.py |
| GET | `/api/v2/members/online` | api/v2/collaboration_hub.py |
| GET | `/api/v2/members/{member_id}` | api/v2/collaboration_hub.py |
| PATCH | `/api/v2/members/{member_id}/status` | api/v2/collaboration_hub.py |
| POST | `/api/v2/presence/heartbeat` | api/v2/collaboration_hub.py |
| POST | `/api/v2/presence/join` | api/v2/collaboration_hub.py |
| POST | `/api/v2/presence/leave` | api/v2/collaboration_hub.py |
| GET | `/api/v2/stats` | api/v2/collaboration_hub.py |
| GET | `/api/v2/tasks` | api/v2/collaboration_hub.py |
| POST | `/api/v2/tasks` | api/v2/collaboration_hub.py |
| DELETE | `/api/v2/tasks/{task_id}` | api/v2/collaboration_hub.py |
| PATCH | `/api/v2/tasks/{task_id}` | api/v2/collaboration_hub.py |
| GET | `/api/v2/workspaces` | api/v2/collaboration_hub.py |
| POST | `/api/v2/workspaces` | api/v2/collaboration_hub.py |
| GET | `/api/v2/workspaces/{workspace_id}` | api/v2/collaboration_hub.py |
| POST | `/api/v2/workspaces/{workspace_id}/members` | api/v2/collaboration_hub.py |
| DELETE | `/api/v2/workspaces/{workspace_id}/members/{member_id}` | api/v2/collaboration_hub.py |

### Commoncropnames (1 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/commoncropnames` | api/v2/core/commoncropnames.py |

### Compute (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/gblup` | api/v2/compute.py |
| POST | `/api/v2/gblup/async` | api/v2/compute.py |
| POST | `/api/v2/grm` | api/v2/compute.py |
| GET | `/api/v2/jobs` | api/v2/compute.py |
| DELETE | `/api/v2/jobs/{job_id}` | api/v2/compute.py |
| GET | `/api/v2/jobs/{job_id}` | api/v2/compute.py |
| POST | `/api/v2/reml` | api/v2/compute.py |
| GET | `/api/v2/status` | api/v2/compute.py |

### Crop Calendar (10 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/activities` | api/v2/crop_calendar.py |
| POST | `/api/v2/activities/{activity_id}/complete` | api/v2/crop_calendar.py |
| GET | `/api/v2/crops` | api/v2/crop_calendar.py |
| POST | `/api/v2/crops` | api/v2/crop_calendar.py |
| GET | `/api/v2/events` | api/v2/crop_calendar.py |
| POST | `/api/v2/events` | api/v2/crop_calendar.py |
| POST | `/api/v2/gdd` | api/v2/crop_calendar.py |
| GET | `/api/v2/growth-stage/{event_id}` | api/v2/crop_calendar.py |
| GET | `/api/v2/growth-stages` | api/v2/crop_calendar.py |
| GET | `/api/v2/view` | api/v2/crop_calendar.py |

### Crop Health (10 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/alerts` | api/v2/crop_health.py |
| GET | `/api/v2/alerts/{alert_id}` | api/v2/crop_health.py |
| PATCH | `/api/v2/alerts/{alert_id}/acknowledge` | api/v2/crop_health.py |
| GET | `/api/v2/crops` | api/v2/crop_health.py |
| GET | `/api/v2/locations` | api/v2/crop_health.py |
| GET | `/api/v2/summary` | api/v2/crop_health.py |
| GET | `/api/v2/trends` | api/v2/crop_health.py |
| GET | `/api/v2/trials` | api/v2/crop_health.py |
| GET | `/api/v2/trials/{trial_id}` | api/v2/crop_health.py |
| POST | `/api/v2/trials/{trial_id}/scan` | api/v2/crop_health.py |

### Crosses (4 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/methods` | api/v2/crosses.py |
| POST | `/api/v2/predict` | api/v2/crosses.py |
| POST | `/api/v2/rank` | api/v2/crosses.py |
| GET | `/api/v2/selection-intensities` | api/v2/crosses.py |

### Crossing Planner (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/germplasm` | api/v2/crossing_planner.py |
| GET | `/api/v2/reference/cross-types` | api/v2/crossing_planner.py |
| GET | `/api/v2/reference/priorities` | api/v2/crossing_planner.py |
| GET | `/api/v2/reference/statuses` | api/v2/crossing_planner.py |
| GET | `/api/v2/statistics` | api/v2/crossing_planner.py |
| DELETE | `/api/v2/{crossId}` | api/v2/crossing_planner.py |
| GET | `/api/v2/{crossId}` | api/v2/crossing_planner.py |
| PUT | `/api/v2/{crossId}` | api/v2/crossing_planner.py |
| PUT | `/api/v2/{crossId}/status` | api/v2/crossing_planner.py |

### Data Dictionary (5 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/entities` | api/v2/data_dictionary.py |
| GET | `/api/v2/entities/{entity_id}` | api/v2/data_dictionary.py |
| GET | `/api/v2/export` | api/v2/data_dictionary.py |
| GET | `/api/v2/fields` | api/v2/data_dictionary.py |
| GET | `/api/v2/stats` | api/v2/data_dictionary.py |

### Data Quality (17 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/issue-types` | api/v2/data_quality.py |
| GET | `/api/v2/issues` | api/v2/data_quality.py |
| POST | `/api/v2/issues` | api/v2/data_quality.py |
| GET | `/api/v2/issues/{issue_id}` | api/v2/data_quality.py |
| POST | `/api/v2/issues/{issue_id}/ignore` | api/v2/data_quality.py |
| POST | `/api/v2/issues/{issue_id}/reopen` | api/v2/data_quality.py |
| POST | `/api/v2/issues/{issue_id}/resolve` | api/v2/data_quality.py |
| GET | `/api/v2/metrics` | api/v2/data_quality.py |
| GET | `/api/v2/metrics/{entity}` | api/v2/data_quality.py |
| GET | `/api/v2/rules` | api/v2/data_quality.py |
| POST | `/api/v2/rules` | api/v2/data_quality.py |
| PUT | `/api/v2/rules/{rule_id}/toggle` | api/v2/data_quality.py |
| GET | `/api/v2/score` | api/v2/data_quality.py |
| GET | `/api/v2/severities` | api/v2/data_quality.py |
| GET | `/api/v2/statistics` | api/v2/data_quality.py |
| POST | `/api/v2/validate` | api/v2/data_quality.py |
| GET | `/api/v2/validation-history` | api/v2/data_quality.py |

### Data Sync (16 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/conflicts` | api/v2/data_sync.py |
| GET | `/api/v2/conflicts/{item_id}` | api/v2/data_sync.py |
| POST | `/api/v2/conflicts/{item_id}/resolve` | api/v2/data_sync.py |
| POST | `/api/v2/download` | api/v2/data_sync.py |
| GET | `/api/v2/history` | api/v2/data_sync.py |
| GET | `/api/v2/offline-data` | api/v2/data_sync.py |
| DELETE | `/api/v2/offline-data/{category}` | api/v2/data_sync.py |
| POST | `/api/v2/offline-data/{category}/refresh` | api/v2/data_sync.py |
| GET | `/api/v2/pending` | api/v2/data_sync.py |
| DELETE | `/api/v2/pending/{item_id}` | api/v2/data_sync.py |
| GET | `/api/v2/settings` | api/v2/data_sync.py |
| PATCH | `/api/v2/settings` | api/v2/data_sync.py |
| GET | `/api/v2/stats` | api/v2/data_sync.py |
| POST | `/api/v2/sync` | api/v2/data_sync.py |
| GET | `/api/v2/sync/{sync_id}` | api/v2/data_sync.py |
| POST | `/api/v2/upload` | api/v2/data_sync.py |

### Data Validation (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/export` | api/v2/data_validation.py |
| DELETE | `/api/v2/issues/{issue_id}` | api/v2/data_validation.py |
| PATCH | `/api/v2/issues/{issue_id}` | api/v2/data_validation.py |
| GET | `/api/v2/rules` | api/v2/data_validation.py |
| PATCH | `/api/v2/rules/{rule_id}` | api/v2/data_validation.py |
| POST | `/api/v2/run` | api/v2/data_validation.py |
| GET | `/api/v2/runs` | api/v2/data_validation.py |
| GET | `/api/v2/stats` | api/v2/data_validation.py |

### Data Visualization (11 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/chart-types` | api/v2/data_visualization.py |
| GET | `/api/v2/charts` | api/v2/data_visualization.py |
| POST | `/api/v2/charts` | api/v2/data_visualization.py |
| DELETE | `/api/v2/charts/{chart_id}` | api/v2/data_visualization.py |
| GET | `/api/v2/charts/{chart_id}` | api/v2/data_visualization.py |
| PUT | `/api/v2/charts/{chart_id}` | api/v2/data_visualization.py |
| GET | `/api/v2/charts/{chart_id}/data` | api/v2/data_visualization.py |
| POST | `/api/v2/charts/{chart_id}/export` | api/v2/data_visualization.py |
| GET | `/api/v2/data-sources` | api/v2/data_visualization.py |
| POST | `/api/v2/preview` | api/v2/data_visualization.py |
| GET | `/api/v2/statistics` | api/v2/data_visualization.py |

### Devguru (38 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| PUT | `/api/v2/chapters/{chapter_id}` | api/v2/devguru.py |
| POST | `/api/v2/chapters/{chapter_id}/sessions` | api/v2/devguru.py |
| POST | `/api/v2/chat` | api/v2/devguru.py |
| PUT | `/api/v2/committee/{member_id}` | api/v2/devguru.py |
| GET | `/api/v2/experiments/{trial_id}/studies` | api/v2/devguru.py |
| PUT | `/api/v2/feedback/{feedback_id}` | api/v2/devguru.py |
| PUT | `/api/v2/meetings/{meeting_id}` | api/v2/devguru.py |
| GET | `/api/v2/milestone-statuses` | api/v2/devguru.py |
| DELETE | `/api/v2/papers/{paper_id}` | api/v2/devguru.py |
| PUT | `/api/v2/papers/{paper_id}` | api/v2/devguru.py |
| POST | `/api/v2/papers/{paper_id}/link-experiment` | api/v2/devguru.py |
| GET | `/api/v2/phases` | api/v2/devguru.py |
| GET | `/api/v2/programs/research` | api/v2/devguru.py |
| GET | `/api/v2/projects` | api/v2/devguru.py |
| POST | `/api/v2/projects` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/chapters` | api/v2/devguru.py |
| POST | `/api/v2/projects/{project_id}/chapters` | api/v2/devguru.py |
| POST | `/api/v2/projects/{project_id}/chapters/generate-defaults` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/collaboration-stats` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/committee` | api/v2/devguru.py |
| POST | `/api/v2/projects/{project_id}/committee` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/experiments` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/feedback` | api/v2/devguru.py |
| POST | `/api/v2/projects/{project_id}/feedback` | api/v2/devguru.py |
| POST | `/api/v2/projects/{project_id}/link-program` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/literature-stats` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/meetings` | api/v2/devguru.py |
| POST | `/api/v2/projects/{project_id}/meetings` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/milestones` | api/v2/devguru.py |
| PUT | `/api/v2/projects/{project_id}/milestones/{milestone_id}` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/papers` | api/v2/devguru.py |
| POST | `/api/v2/projects/{project_id}/papers` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/suggestions` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/synthesis` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/timeline` | api/v2/devguru.py |
| GET | `/api/v2/projects/{project_id}/writing-stats` | api/v2/devguru.py |
| GET | `/api/v2/status` | api/v2/devguru.py |

### Disease (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/crops` | api/v2/disease.py |
| GET | `/api/v2/diseases` | api/v2/disease.py |
| GET | `/api/v2/diseases/{disease_id}` | api/v2/disease.py |
| GET | `/api/v2/genes` | api/v2/disease.py |
| GET | `/api/v2/genes/{gene_id}` | api/v2/disease.py |
| GET | `/api/v2/pathogen-types` | api/v2/disease.py |
| GET | `/api/v2/pyramiding-strategies` | api/v2/disease.py |
| GET | `/api/v2/resistance-types` | api/v2/disease.py |
| GET | `/api/v2/statistics` | api/v2/disease.py |

### Dispatch (18 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/firm-types` | api/v2/dispatch.py |
| GET | `/api/v2/firms` | api/v2/dispatch.py |
| POST | `/api/v2/firms` | api/v2/dispatch.py |
| DELETE | `/api/v2/firms/{firm_id}` | api/v2/dispatch.py |
| GET | `/api/v2/firms/{firm_id}` | api/v2/dispatch.py |
| PUT | `/api/v2/firms/{firm_id}` | api/v2/dispatch.py |
| GET | `/api/v2/orders` | api/v2/dispatch.py |
| POST | `/api/v2/orders` | api/v2/dispatch.py |
| GET | `/api/v2/orders/{dispatch_id}` | api/v2/dispatch.py |
| POST | `/api/v2/orders/{dispatch_id}/approve` | api/v2/dispatch.py |
| POST | `/api/v2/orders/{dispatch_id}/cancel` | api/v2/dispatch.py |
| POST | `/api/v2/orders/{dispatch_id}/deliver` | api/v2/dispatch.py |
| POST | `/api/v2/orders/{dispatch_id}/items/{item_id}/picked` | api/v2/dispatch.py |
| POST | `/api/v2/orders/{dispatch_id}/pick` | api/v2/dispatch.py |
| POST | `/api/v2/orders/{dispatch_id}/ship` | api/v2/dispatch.py |
| POST | `/api/v2/orders/{dispatch_id}/submit` | api/v2/dispatch.py |
| GET | `/api/v2/statistics` | api/v2/dispatch.py |
| GET | `/api/v2/statuses` | api/v2/dispatch.py |

### Doubled Haploid (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/batches` | api/v2/doubled_haploid.py |
| GET | `/api/v2/batches/{batch_id}` | api/v2/doubled_haploid.py |
| POST | `/api/v2/calculate-efficiency` | api/v2/doubled_haploid.py |
| GET | `/api/v2/protocols` | api/v2/doubled_haploid.py |
| GET | `/api/v2/protocols/{protocol_id}` | api/v2/doubled_haploid.py |
| GET | `/api/v2/statistics` | api/v2/doubled_haploid.py |
| GET | `/api/v2/workflow/{protocol_id}` | api/v2/doubled_haploid.py |

### Dus (17 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/crops` | api/v2/dus.py |
| GET | `/api/v2/crops/{crop_code}` | api/v2/dus.py |
| GET | `/api/v2/crops/{crop_code}/characters` | api/v2/dus.py |
| GET | `/api/v2/reference/character-types` | api/v2/dus.py |
| GET | `/api/v2/reference/trial-statuses` | api/v2/dus.py |
| GET | `/api/v2/trials` | api/v2/dus.py |
| POST | `/api/v2/trials` | api/v2/dus.py |
| GET | `/api/v2/trials/{trial_id}` | api/v2/dus.py |
| GET | `/api/v2/trials/{trial_id}/distinctness/{entry_id}` | api/v2/dus.py |
| GET | `/api/v2/trials/{trial_id}/entries` | api/v2/dus.py |
| POST | `/api/v2/trials/{trial_id}/entries` | api/v2/dus.py |
| GET | `/api/v2/trials/{trial_id}/entries/{entry_id}/scores` | api/v2/dus.py |
| POST | `/api/v2/trials/{trial_id}/entries/{entry_id}/scores` | api/v2/dus.py |
| POST | `/api/v2/trials/{trial_id}/entries/{entry_id}/scores/bulk` | api/v2/dus.py |
| GET | `/api/v2/trials/{trial_id}/report/{entry_id}` | api/v2/dus.py |
| POST | `/api/v2/trials/{trial_id}/stability/{entry_id}` | api/v2/dus.py |
| POST | `/api/v2/trials/{trial_id}/uniformity/{entry_id}` | api/v2/dus.py |

### Events (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| DELETE | `/api/v2/dead-letters` | api/v2/events.py |
| GET | `/api/v2/dead-letters` | api/v2/events.py |
| POST | `/api/v2/dead-letters/{index}/retry` | api/v2/events.py |
| DELETE | `/api/v2/history` | api/v2/events.py |
| GET | `/api/v2/history` | api/v2/events.py |
| POST | `/api/v2/publish` | api/v2/events.py |
| GET | `/api/v2/subscriptions` | api/v2/events.py |
| GET | `/api/v2/types` | api/v2/events.py |

### Export (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/custom` | api/v2/export.py |
| POST | `/api/v2/field-book` | api/v2/export.py |
| GET | `/api/v2/formats` | api/v2/export.py |
| POST | `/api/v2/markers` | api/v2/export.py |
| POST | `/api/v2/pedigree` | api/v2/export.py |
| POST | `/api/v2/phenotype-matrix` | api/v2/export.py |
| POST | `/api/v2/trial` | api/v2/export.py |

### Field Book (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/observations` | api/v2/field_book.py |
| POST | `/api/v2/observations/bulk` | api/v2/field_book.py |
| DELETE | `/api/v2/observations/{study_id}/{plot_id}/{trait_id}` | api/v2/field_book.py |
| GET | `/api/v2/studies` | api/v2/field_book.py |
| GET | `/api/v2/studies/{study_id}/entries` | api/v2/field_book.py |
| GET | `/api/v2/studies/{study_id}/progress` | api/v2/field_book.py |
| GET | `/api/v2/studies/{study_id}/summary` | api/v2/field_book.py |
| GET | `/api/v2/studies/{study_id}/traits` | api/v2/field_book.py |

### Field Environment (14 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/history` | api/v2/field_environment.py |
| GET | `/api/v2/history/{field_id}` | api/v2/field_environment.py |
| GET | `/api/v2/input-logs` | api/v2/field_environment.py |
| POST | `/api/v2/input-logs` | api/v2/field_environment.py |
| GET | `/api/v2/input-types` | api/v2/field_environment.py |
| GET | `/api/v2/irrigation` | api/v2/field_environment.py |
| POST | `/api/v2/irrigation` | api/v2/field_environment.py |
| GET | `/api/v2/irrigation-types` | api/v2/field_environment.py |
| GET | `/api/v2/irrigation/summary/{field_id}` | api/v2/field_environment.py |
| GET | `/api/v2/soil-profiles` | api/v2/field_environment.py |
| POST | `/api/v2/soil-profiles` | api/v2/field_environment.py |
| GET | `/api/v2/soil-profiles/{profile_id}` | api/v2/field_environment.py |
| GET | `/api/v2/soil-profiles/{profile_id}/recommendations` | api/v2/field_environment.py |
| GET | `/api/v2/soil-textures` | api/v2/field_environment.py |

### Field Layout (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/export/{study_id}` | api/v2/field_layout.py |
| GET | `/api/v2/germplasm` | api/v2/field_layout.py |
| GET | `/api/v2/studies` | api/v2/field_layout.py |
| GET | `/api/v2/studies/{study_id}` | api/v2/field_layout.py |
| POST | `/api/v2/studies/{study_id}/generate` | api/v2/field_layout.py |
| GET | `/api/v2/studies/{study_id}/layout` | api/v2/field_layout.py |
| GET | `/api/v2/studies/{study_id}/plots` | api/v2/field_layout.py |
| GET | `/api/v2/studies/{study_id}/plots/{plot_number}` | api/v2/field_layout.py |
| PUT | `/api/v2/studies/{study_id}/plots/{plot_number}` | api/v2/field_layout.py |

### Field Map (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/stations` | api/v2/field_map.py |
| GET | `/api/v2/statuses` | api/v2/field_map.py |
| GET | `/api/v2/summary` | api/v2/field_map.py |
| DELETE | `/api/v2/{field_id}` | api/v2/field_map.py |
| GET | `/api/v2/{field_id}` | api/v2/field_map.py |
| PUT | `/api/v2/{field_id}` | api/v2/field_map.py |
| GET | `/api/v2/{field_id}/plots` | api/v2/field_map.py |
| GET | `/api/v2/{field_id}/plots/{plot_id}` | api/v2/field_map.py |
| PUT | `/api/v2/{field_id}/plots/{plot_id}` | api/v2/field_map.py |

### Field Planning (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/calendar` | api/v2/field_planning.py |
| GET | `/api/v2/plans` | api/v2/field_planning.py |
| GET | `/api/v2/plans/{plan_id}` | api/v2/field_planning.py |
| GET | `/api/v2/resources/{plan_id}` | api/v2/field_planning.py |
| GET | `/api/v2/seasons` | api/v2/field_planning.py |
| GET | `/api/v2/seasons/{plan_id}` | api/v2/field_planning.py |
| GET | `/api/v2/statistics` | api/v2/field_planning.py |

### Field Scanner (6 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/export` | api/v2/field_scanner.py |
| GET | `/api/v2/plot/{plot_id}/history` | api/v2/field_scanner.py |
| GET | `/api/v2/stats` | api/v2/field_scanner.py |
| DELETE | `/api/v2/{scan_id}` | api/v2/field_scanner.py |
| GET | `/api/v2/{scan_id}` | api/v2/field_scanner.py |
| PATCH | `/api/v2/{scan_id}` | api/v2/field_scanner.py |

### Forums (13 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/categories` | api/v2/forums.py |
| POST | `/api/v2/categories` | api/v2/forums.py |
| GET | `/api/v2/categories/{category_id}` | api/v2/forums.py |
| GET | `/api/v2/stats` | api/v2/forums.py |
| GET | `/api/v2/topics` | api/v2/forums.py |
| POST | `/api/v2/topics` | api/v2/forums.py |
| GET | `/api/v2/topics/{topic_id}` | api/v2/forums.py |
| PUT | `/api/v2/topics/{topic_id}` | api/v2/forums.py |
| POST | `/api/v2/topics/{topic_id}/close` | api/v2/forums.py |
| POST | `/api/v2/topics/{topic_id}/like` | api/v2/forums.py |
| POST | `/api/v2/topics/{topic_id}/pin` | api/v2/forums.py |
| POST | `/api/v2/topics/{topic_id}/replies` | api/v2/forums.py |
| POST | `/api/v2/topics/{topic_id}/replies/{reply_id}/like` | api/v2/forums.py |

### Genetic Diversity (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/admixture` | api/v2/genetic_diversity.py |
| GET | `/api/v2/amova` | api/v2/genetic_diversity.py |
| GET | `/api/v2/distances` | api/v2/genetic_diversity.py |
| GET | `/api/v2/pca` | api/v2/genetic_diversity.py |
| GET | `/api/v2/populations` | api/v2/genetic_diversity.py |
| GET | `/api/v2/populations/{population_id}` | api/v2/genetic_diversity.py |
| GET | `/api/v2/populations/{population_id}/metrics` | api/v2/genetic_diversity.py |
| GET | `/api/v2/summary` | api/v2/genetic_diversity.py |

### Genetic Gain (10 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/programs` | api/v2/genetic_gain.py |
| POST | `/api/v2/programs` | api/v2/genetic_gain.py |
| GET | `/api/v2/programs/{program_id}` | api/v2/genetic_gain.py |
| GET | `/api/v2/programs/{program_id}/check-comparison` | api/v2/genetic_gain.py |
| POST | `/api/v2/programs/{program_id}/cycles` | api/v2/genetic_gain.py |
| GET | `/api/v2/programs/{program_id}/gain` | api/v2/genetic_gain.py |
| GET | `/api/v2/programs/{program_id}/projection` | api/v2/genetic_gain.py |
| GET | `/api/v2/programs/{program_id}/realized-heritability` | api/v2/genetic_gain.py |
| POST | `/api/v2/programs/{program_id}/releases` | api/v2/genetic_gain.py |
| GET | `/api/v2/statistics` | api/v2/genetic_gain.py |

### Genomic Selection (10 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/comparison` | api/v2/genomic_selection.py |
| GET | `/api/v2/cross-prediction` | api/v2/genomic_selection.py |
| GET | `/api/v2/methods` | api/v2/genomic_selection.py |
| GET | `/api/v2/models` | api/v2/genomic_selection.py |
| GET | `/api/v2/models/{model_id}` | api/v2/genomic_selection.py |
| GET | `/api/v2/models/{model_id}/predictions` | api/v2/genomic_selection.py |
| GET | `/api/v2/models/{model_id}/selection-response` | api/v2/genomic_selection.py |
| GET | `/api/v2/summary` | api/v2/genomic_selection.py |
| GET | `/api/v2/traits` | api/v2/genomic_selection.py |
| GET | `/api/v2/yield-predictions` | api/v2/genomic_selection.py |

### Genotyping (16 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/calls` | api/v2/genotyping.py |
| GET | `/api/v2/calls/statistics` | api/v2/genotyping.py |
| GET | `/api/v2/callsets` | api/v2/genotyping.py |
| GET | `/api/v2/callsets/{callSetDbId}` | api/v2/genotyping.py |
| GET | `/api/v2/markerpositions` | api/v2/genotyping.py |
| GET | `/api/v2/references` | api/v2/genotyping.py |
| GET | `/api/v2/references/{referenceDbId}` | api/v2/genotyping.py |
| GET | `/api/v2/referencesets` | api/v2/genotyping.py |
| GET | `/api/v2/summary` | api/v2/genotyping.py |
| GET | `/api/v2/variantsets` | api/v2/genotyping.py |
| POST | `/api/v2/variantsets` | api/v2/genotyping.py |
| GET | `/api/v2/variantsets/{variantSetDbId}` | api/v2/genotyping.py |
| GET | `/api/v2/vendor/orders` | api/v2/genotyping.py |
| POST | `/api/v2/vendor/orders` | api/v2/genotyping.py |
| GET | `/api/v2/vendor/orders/{vendorOrderDbId}` | api/v2/genotyping.py |
| PUT | `/api/v2/vendor/orders/{vendorOrderDbId}/status` | api/v2/genotyping.py |

### Germplasm Collection (6 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/stats` | api/v2/germplasm_collection.py |
| GET | `/api/v2/types` | api/v2/germplasm_collection.py |
| DELETE | `/api/v2/{collection_id}` | api/v2/germplasm_collection.py |
| GET | `/api/v2/{collection_id}` | api/v2/germplasm_collection.py |
| PATCH | `/api/v2/{collection_id}` | api/v2/germplasm_collection.py |
| POST | `/api/v2/{collection_id}/accessions` | api/v2/germplasm_collection.py |

### Germplasm Comparison (5 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/compare` | api/v2/germplasm_comparison.py |
| GET | `/api/v2/entry/{germplasm_id}` | api/v2/germplasm_comparison.py |
| GET | `/api/v2/markers` | api/v2/germplasm_comparison.py |
| GET | `/api/v2/statistics` | api/v2/germplasm_comparison.py |
| GET | `/api/v2/traits` | api/v2/germplasm_comparison.py |

### Germplasm Search (4 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/filters` | api/v2/germplasm_search.py |
| GET | `/api/v2/search` | api/v2/germplasm_search.py |
| GET | `/api/v2/statistics` | api/v2/germplasm_search.py |
| GET | `/api/v2/{germplasm_id}` | api/v2/germplasm_search.py |

### Grin (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/genesys/accession/{institute_code}/{accession_number}` | api/v2/grin.py |
| GET | `/api/v2/genesys/crops/{crop}/statistics` | api/v2/grin.py |
| GET | `/api/v2/genesys/search` | api/v2/grin.py |
| GET | `/api/v2/grin-global/accession/{accession_number}` | api/v2/grin.py |
| GET | `/api/v2/grin-global/search` | api/v2/grin.py |
| POST | `/api/v2/grin-global/validate-taxonomy` | api/v2/grin.py |
| POST | `/api/v2/import/genesys` | api/v2/grin.py |
| POST | `/api/v2/import/grin-global` | api/v2/grin.py |
| GET | `/api/v2/status` | api/v2/grin.py |

### Gwas (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/glm` | api/v2/gwas.py |
| POST | `/api/v2/kinship` | api/v2/gwas.py |
| POST | `/api/v2/ld` | api/v2/gwas.py |
| GET | `/api/v2/ld/demo` | api/v2/gwas.py |
| POST | `/api/v2/ld/pruning` | api/v2/gwas.py |
| GET | `/api/v2/methods` | api/v2/gwas.py |
| POST | `/api/v2/mlm` | api/v2/gwas.py |
| POST | `/api/v2/pca` | api/v2/gwas.py |

### Gxe (5 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/ammi` | api/v2/gxe.py |
| POST | `/api/v2/finlay-wilkinson` | api/v2/gxe.py |
| POST | `/api/v2/gge` | api/v2/gxe.py |
| POST | `/api/v2/mega-environments` | api/v2/gxe.py |
| GET | `/api/v2/methods` | api/v2/gxe.py |

### Haplotype (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/associations` | api/v2/haplotype.py |
| GET | `/api/v2/blocks` | api/v2/haplotype.py |
| GET | `/api/v2/blocks/{block_id}` | api/v2/haplotype.py |
| GET | `/api/v2/blocks/{block_id}/haplotypes` | api/v2/haplotype.py |
| GET | `/api/v2/diversity` | api/v2/haplotype.py |
| GET | `/api/v2/favorable` | api/v2/haplotype.py |
| GET | `/api/v2/statistics` | api/v2/haplotype.py |
| GET | `/api/v2/traits` | api/v2/haplotype.py |

### Harvest (15 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/calculate/dry-weight` | api/v2/harvest.py |
| GET | `/api/v2/harvests` | api/v2/harvest.py |
| POST | `/api/v2/harvests` | api/v2/harvest.py |
| GET | `/api/v2/harvests/{harvest_id}` | api/v2/harvest.py |
| GET | `/api/v2/harvests/{harvest_id}/quality` | api/v2/harvest.py |
| POST | `/api/v2/harvests/{harvest_id}/quality` | api/v2/harvest.py |
| PUT | `/api/v2/harvests/{harvest_id}/record` | api/v2/harvest.py |
| GET | `/api/v2/statistics` | api/v2/harvest.py |
| GET | `/api/v2/storage/types` | api/v2/harvest.py |
| GET | `/api/v2/storage/units` | api/v2/harvest.py |
| POST | `/api/v2/storage/units` | api/v2/harvest.py |
| GET | `/api/v2/storage/units/{unit_id}` | api/v2/harvest.py |
| GET | `/api/v2/storage/units/{unit_id}/history` | api/v2/harvest.py |
| POST | `/api/v2/storage/units/{unit_id}/store` | api/v2/harvest.py |
| POST | `/api/v2/storage/units/{unit_id}/withdraw` | api/v2/harvest.py |

### Insights (2 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/summary` | api/v2/insights.py |
| GET | `/api/v2/trends` | api/v2/insights.py |

### Integrations (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/` | api/v2/integrations.py |
| POST | `/api/v2/` | api/v2/integrations.py |
| GET | `/api/v2/available` | api/v2/integrations.py |
| DELETE | `/api/v2/{integration_id}` | api/v2/integrations.py |
| GET | `/api/v2/{integration_id}` | api/v2/integrations.py |
| PATCH | `/api/v2/{integration_id}` | api/v2/integrations.py |
| POST | `/api/v2/{integration_id}/test` | api/v2/integrations.py |

### Label Printing (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/data` | api/v2/label_printing.py |
| GET | `/api/v2/jobs` | api/v2/label_printing.py |
| POST | `/api/v2/jobs` | api/v2/label_printing.py |
| GET | `/api/v2/jobs/{job_id}` | api/v2/label_printing.py |
| PATCH | `/api/v2/jobs/{job_id}/status` | api/v2/label_printing.py |
| GET | `/api/v2/stats` | api/v2/label_printing.py |
| GET | `/api/v2/templates` | api/v2/label_printing.py |
| POST | `/api/v2/templates` | api/v2/label_printing.py |
| GET | `/api/v2/templates/{template_id}` | api/v2/label_printing.py |

### Languages (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/export` | api/v2/languages.py |
| POST | `/api/v2/import` | api/v2/languages.py |
| GET | `/api/v2/stats` | api/v2/languages.py |
| GET | `/api/v2/translations/keys` | api/v2/languages.py |
| POST | `/api/v2/translations/keys` | api/v2/languages.py |
| PATCH | `/api/v2/translations/keys/{key}` | api/v2/languages.py |
| GET | `/api/v2/{language_code}` | api/v2/languages.py |
| PATCH | `/api/v2/{language_code}` | api/v2/languages.py |
| POST | `/api/v2/{language_code}/auto-translate` | api/v2/languages.py |

### Licensing (17 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/license-types` | api/v2/licensing.py |
| GET | `/api/v2/licenses` | api/v2/licensing.py |
| POST | `/api/v2/licenses` | api/v2/licensing.py |
| GET | `/api/v2/licenses/{license_id}` | api/v2/licensing.py |
| PUT | `/api/v2/licenses/{license_id}/activate` | api/v2/licensing.py |
| POST | `/api/v2/licenses/{license_id}/royalties` | api/v2/licensing.py |
| PUT | `/api/v2/licenses/{license_id}/terminate` | api/v2/licensing.py |
| GET | `/api/v2/protection-types` | api/v2/licensing.py |
| GET | `/api/v2/protections` | api/v2/licensing.py |
| POST | `/api/v2/protections` | api/v2/licensing.py |
| GET | `/api/v2/protections/{protection_id}` | api/v2/licensing.py |
| PUT | `/api/v2/protections/{protection_id}/grant` | api/v2/licensing.py |
| GET | `/api/v2/statistics` | api/v2/licensing.py |
| GET | `/api/v2/varieties` | api/v2/licensing.py |
| POST | `/api/v2/varieties` | api/v2/licensing.py |
| GET | `/api/v2/varieties/{variety_id}` | api/v2/licensing.py |
| GET | `/api/v2/varieties/{variety_id}/royalties` | api/v2/licensing.py |

### Lists (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/lists` | api/v2/core/lists.py |
| POST | `/api/v2/lists` | api/v2/core/lists.py |
| DELETE | `/api/v2/lists/{listDbId}` | api/v2/core/lists.py |
| GET | `/api/v2/lists/{listDbId}` | api/v2/core/lists.py |
| PUT | `/api/v2/lists/{listDbId}` | api/v2/core/lists.py |
| POST | `/api/v2/lists/{listDbId}/data` | api/v2/core/lists.py |
| POST | `/api/v2/lists/{listDbId}/items` | api/v2/core/lists.py |

### Locations (5 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/locations` | api/v2/core/locations.py |
| POST | `/api/v2/locations` | api/v2/core/locations.py |
| DELETE | `/api/v2/locations/{locationDbId}` | api/v2/core/locations.py |
| GET | `/api/v2/locations/{locationDbId}` | api/v2/core/locations.py |
| PUT | `/api/v2/locations/{locationDbId}` | api/v2/core/locations.py |

### Mas (10 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/background` | api/v2/mas.py |
| POST | `/api/v2/foreground` | api/v2/mas.py |
| GET | `/api/v2/genotypes/{individual_id}` | api/v2/mas.py |
| POST | `/api/v2/mabc` | api/v2/mas.py |
| GET | `/api/v2/markers` | api/v2/mas.py |
| POST | `/api/v2/markers` | api/v2/mas.py |
| POST | `/api/v2/markers/bulk` | api/v2/mas.py |
| GET | `/api/v2/markers/{marker_id}` | api/v2/mas.py |
| POST | `/api/v2/score` | api/v2/mas.py |
| GET | `/api/v2/stats` | api/v2/mas.py |

### Metrics (15 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/api` | api/v2/metrics.py |
| GET | `/api/v2/badge/brapi` | api/v2/metrics.py |
| GET | `/api/v2/badge/build` | api/v2/metrics.py |
| GET | `/api/v2/badge/endpoints` | api/v2/metrics.py |
| GET | `/api/v2/badge/pages` | api/v2/metrics.py |
| GET | `/api/v2/badge/version` | api/v2/metrics.py |
| GET | `/api/v2/build` | api/v2/metrics.py |
| GET | `/api/v2/database` | api/v2/metrics.py |
| GET | `/api/v2/milestones` | api/v2/metrics.py |
| GET | `/api/v2/modules` | api/v2/metrics.py |
| GET | `/api/v2/pages` | api/v2/metrics.py |
| GET | `/api/v2/summary` | api/v2/metrics.py |
| GET | `/api/v2/tech-stack` | api/v2/metrics.py |
| GET | `/api/v2/version` | api/v2/metrics.py |
| GET | `/api/v2/workspaces` | api/v2/metrics.py |

### Molecular Breeding (5 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/lines` | api/v2/molecular_breeding.py |
| GET | `/api/v2/pyramiding/{scheme_id}` | api/v2/molecular_breeding.py |
| GET | `/api/v2/schemes` | api/v2/molecular_breeding.py |
| GET | `/api/v2/schemes/{scheme_id}` | api/v2/molecular_breeding.py |
| GET | `/api/v2/statistics` | api/v2/molecular_breeding.py |

### Mta (13 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/by-exchange/{exchange_id}` | api/v2/mta.py |
| GET | `/api/v2/by-number/{mta_number}` | api/v2/mta.py |
| GET | `/api/v2/statistics` | api/v2/mta.py |
| GET | `/api/v2/templates` | api/v2/mta.py |
| GET | `/api/v2/templates/{template_id}` | api/v2/mta.py |
| GET | `/api/v2/types/reference` | api/v2/mta.py |
| GET | `/api/v2/{mta_id}` | api/v2/mta.py |
| POST | `/api/v2/{mta_id}/approve` | api/v2/mta.py |
| GET | `/api/v2/{mta_id}/compliance` | api/v2/mta.py |
| POST | `/api/v2/{mta_id}/reject` | api/v2/mta.py |
| POST | `/api/v2/{mta_id}/sign` | api/v2/mta.py |
| POST | `/api/v2/{mta_id}/submit` | api/v2/mta.py |
| POST | `/api/v2/{mta_id}/terminate` | api/v2/mta.py |

### Notifications (10 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/` | api/v2/notifications.py |
| POST | `/api/v2/` | api/v2/notifications.py |
| POST | `/api/v2/mark-all-read` | api/v2/notifications.py |
| POST | `/api/v2/mark-read` | api/v2/notifications.py |
| GET | `/api/v2/preferences` | api/v2/notifications.py |
| PUT | `/api/v2/preferences` | api/v2/notifications.py |
| GET | `/api/v2/quiet-hours` | api/v2/notifications.py |
| PUT | `/api/v2/quiet-hours` | api/v2/notifications.py |
| GET | `/api/v2/stats` | api/v2/notifications.py |
| DELETE | `/api/v2/{notification_id}` | api/v2/notifications.py |

### Nursery (10 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/advance` | api/v2/nursery.py |
| POST | `/api/v2/entries/{entry_id}/selection` | api/v2/nursery.py |
| GET | `/api/v2/nurseries` | api/v2/nursery.py |
| POST | `/api/v2/nurseries` | api/v2/nursery.py |
| GET | `/api/v2/nurseries/{nursery_id}` | api/v2/nursery.py |
| POST | `/api/v2/nurseries/{nursery_id}/entries` | api/v2/nursery.py |
| POST | `/api/v2/nurseries/{nursery_id}/entries/bulk` | api/v2/nursery.py |
| PATCH | `/api/v2/nurseries/{nursery_id}/status` | api/v2/nursery.py |
| GET | `/api/v2/nurseries/{nursery_id}/summary` | api/v2/nursery.py |
| GET | `/api/v2/types` | api/v2/nursery.py |

### Nursery Management (10 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/batches` | api/v2/nursery_management.py |
| POST | `/api/v2/batches` | api/v2/nursery_management.py |
| DELETE | `/api/v2/batches/{batch_id}` | api/v2/nursery_management.py |
| GET | `/api/v2/batches/{batch_id}` | api/v2/nursery_management.py |
| PATCH | `/api/v2/batches/{batch_id}/counts` | api/v2/nursery_management.py |
| PATCH | `/api/v2/batches/{batch_id}/status` | api/v2/nursery_management.py |
| GET | `/api/v2/export` | api/v2/nursery_management.py |
| GET | `/api/v2/germplasm` | api/v2/nursery_management.py |
| GET | `/api/v2/locations` | api/v2/nursery_management.py |
| GET | `/api/v2/stats` | api/v2/nursery_management.py |

### Offline Sync (12 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/cached-data` | api/v2/offline_sync.py |
| DELETE | `/api/v2/clear-cache` | api/v2/offline_sync.py |
| GET | `/api/v2/pending-changes` | api/v2/offline_sync.py |
| DELETE | `/api/v2/pending-changes/{item_id}` | api/v2/offline_sync.py |
| POST | `/api/v2/queue-change` | api/v2/offline_sync.py |
| POST | `/api/v2/resolve-conflict/{item_id}` | api/v2/offline_sync.py |
| GET | `/api/v2/settings` | api/v2/offline_sync.py |
| PATCH | `/api/v2/settings` | api/v2/offline_sync.py |
| GET | `/api/v2/stats` | api/v2/offline_sync.py |
| GET | `/api/v2/storage-quota` | api/v2/offline_sync.py |
| POST | `/api/v2/sync-now` | api/v2/offline_sync.py |
| POST | `/api/v2/update-cache/{category}` | api/v2/offline_sync.py |

### Ontology (11 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/categories` | api/v2/ontology.py |
| GET | `/api/v2/methods` | api/v2/ontology.py |
| POST | `/api/v2/methods` | api/v2/ontology.py |
| GET | `/api/v2/scale-types` | api/v2/ontology.py |
| GET | `/api/v2/scales` | api/v2/ontology.py |
| POST | `/api/v2/scales` | api/v2/ontology.py |
| GET | `/api/v2/traits` | api/v2/ontology.py |
| POST | `/api/v2/traits` | api/v2/ontology.py |
| GET | `/api/v2/traits/search` | api/v2/ontology.py |
| GET | `/api/v2/variables` | api/v2/ontology.py |
| POST | `/api/v2/variables` | api/v2/ontology.py |

### Other (46 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/` | integrations/routes.py |
| GET | `/api/v2/` | modules/plant_sciences/router.py |
| GET | `/api/v2/accessions` | modules/seed_bank/router.py |
| POST | `/api/v2/accessions` | modules/seed_bank/router.py |
| GET | `/api/v2/accessions/{accession_id}` | modules/seed_bank/router.py |
| PATCH | `/api/v2/accessions/{accession_id}` | modules/seed_bank/router.py |
| GET | `/api/v2/dashboard` | modules/plant_sciences/breeding/routes.py |
| GET | `/api/v2/dashboard` | modules/plant_sciences/genotyping/routes.py |
| GET | `/api/v2/dashboard` | modules/plant_sciences/phenotyping/routes.py |
| GET | `/api/v2/data-quality` | modules/plant_sciences/phenotyping/routes.py |
| GET | `/api/v2/diversity` | modules/plant_sciences/genomics/routes.py |
| GET | `/api/v2/exchanges` | modules/seed_bank/router.py |
| POST | `/api/v2/exchanges` | modules/seed_bank/router.py |
| POST | `/api/v2/gebv/predict` | modules/plant_sciences/genomics/routes.py |
| GET | `/api/v2/genetic-gain` | modules/plant_sciences/breeding/routes.py |
| POST | `/api/v2/grm/calculate` | modules/plant_sciences/genomics/routes.py |
| GET | `/api/v2/ld/{chromosome}` | modules/plant_sciences/genomics/routes.py |
| GET | `/api/v2/marker-summary` | modules/plant_sciences/genotyping/routes.py |
| GET | `/api/v2/mcpd/codes/acquisition-source` | modules/seed_bank/router.py |
| GET | `/api/v2/mcpd/codes/biological-status` | modules/seed_bank/router.py |
| GET | `/api/v2/mcpd/codes/countries` | modules/seed_bank/router.py |
| GET | `/api/v2/mcpd/codes/storage-type` | modules/seed_bank/router.py |
| GET | `/api/v2/mcpd/export/csv` | modules/seed_bank/router.py |
| GET | `/api/v2/mcpd/export/json` | modules/seed_bank/router.py |
| POST | `/api/v2/mcpd/import` | modules/seed_bank/router.py |
| GET | `/api/v2/mcpd/template` | modules/seed_bank/router.py |
| GET | `/api/v2/pipeline` | modules/plant_sciences/breeding/routes.py |
| GET | `/api/v2/population-structure` | modules/plant_sciences/genomics/routes.py |
| GET | `/api/v2/programs` | middleware/tenant_context.py |
| GET | `/api/v2/programs` | middleware/tenant_context.py |
| GET | `/api/v2/programs` | middleware/tenant_context.py |
| GET | `/api/v2/programs` | core/permissions.py |
| GET | `/api/v2/programs` | core/permissions.py |
| GET | `/api/v2/regeneration-tasks` | modules/seed_bank/router.py |
| POST | `/api/v2/regeneration-tasks` | modules/seed_bank/router.py |
| GET | `/api/v2/sample-tracking` | modules/plant_sciences/genotyping/routes.py |
| GET | `/api/v2/stats` | modules/seed_bank/router.py |
| GET | `/api/v2/trait-correlations` | modules/plant_sciences/phenotyping/routes.py |
| GET | `/api/v2/vaults` | modules/seed_bank/router.py |
| POST | `/api/v2/vaults` | modules/seed_bank/router.py |
| GET | `/api/v2/vaults/{vault_id}` | modules/seed_bank/router.py |
| GET | `/api/v2/viability-tests` | modules/seed_bank/router.py |
| POST | `/api/v2/viability-tests` | modules/seed_bank/router.py |
| GET | `/api/v2/{integration_id}` | integrations/routes.py |
| POST | `/api/v2/{integration_id}/sync` | integrations/routes.py |
| POST | `/api/v2/{integration_id}/test` | integrations/routes.py |

### Parent Selection (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/objectives` | api/v2/parent_selection.py |
| PUT | `/api/v2/objectives` | api/v2/parent_selection.py |
| GET | `/api/v2/parents` | api/v2/parent_selection.py |
| GET | `/api/v2/parents/{parent_id}` | api/v2/parent_selection.py |
| GET | `/api/v2/predict-cross` | api/v2/parent_selection.py |
| GET | `/api/v2/recommendations` | api/v2/parent_selection.py |
| GET | `/api/v2/statistics` | api/v2/parent_selection.py |
| GET | `/api/v2/types` | api/v2/parent_selection.py |

### Parentage (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/demo` | api/v2/parentage.py |
| POST | `/api/v2/find-parents` | api/v2/parentage.py |
| GET | `/api/v2/history` | api/v2/parentage.py |
| GET | `/api/v2/individuals` | api/v2/parentage.py |
| GET | `/api/v2/individuals/{individual_id}` | api/v2/parentage.py |
| GET | `/api/v2/markers` | api/v2/parentage.py |
| GET | `/api/v2/statistics` | api/v2/parentage.py |
| POST | `/api/v2/verify` | api/v2/parentage.py |

### Passport (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/accessions` | api/v2/passport.py |
| POST | `/api/v2/accessions` | api/v2/passport.py |
| GET | `/api/v2/accessions/{accession_id}` | api/v2/passport.py |
| POST | `/api/v2/accessions/{accession_id}/collection-site` | api/v2/passport.py |
| GET | `/api/v2/acquisition-source-codes` | api/v2/passport.py |
| GET | `/api/v2/biological-status-codes` | api/v2/passport.py |
| GET | `/api/v2/export/mcpd` | api/v2/passport.py |
| GET | `/api/v2/search` | api/v2/passport.py |
| GET | `/api/v2/statistics` | api/v2/passport.py |

### Pedigree (11 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/ancestors/{individual_id}` | api/v2/pedigree.py |
| POST | `/api/v2/coancestry` | api/v2/pedigree.py |
| GET | `/api/v2/descendants/{individual_id}` | api/v2/pedigree.py |
| GET | `/api/v2/individual/{individual_id}` | api/v2/pedigree.py |
| GET | `/api/v2/individuals` | api/v2/pedigree.py |
| POST | `/api/v2/load` | api/v2/pedigree.py |
| GET | `/api/v2/pedigree` | api/v2/core/pedigree.py |
| POST | `/api/v2/pedigree` | api/v2/core/pedigree.py |
| PUT | `/api/v2/pedigree` | api/v2/core/pedigree.py |
| POST | `/api/v2/relationship-matrix` | api/v2/pedigree.py |
| GET | `/api/v2/stats` | api/v2/pedigree.py |

### Performance Ranking (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/compare` | api/v2/performance_ranking.py |
| GET | `/api/v2/entries/{entry_id}` | api/v2/performance_ranking.py |
| GET | `/api/v2/programs` | api/v2/performance_ranking.py |
| GET | `/api/v2/rankings` | api/v2/performance_ranking.py |
| GET | `/api/v2/statistics` | api/v2/performance_ranking.py |
| GET | `/api/v2/top-performers` | api/v2/performance_ranking.py |
| GET | `/api/v2/trials` | api/v2/performance_ranking.py |

### Phenology (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/records` | api/v2/phenology.py |
| POST | `/api/v2/records` | api/v2/phenology.py |
| GET | `/api/v2/records/{record_id}` | api/v2/phenology.py |
| PATCH | `/api/v2/records/{record_id}` | api/v2/phenology.py |
| GET | `/api/v2/records/{record_id}/observations` | api/v2/phenology.py |
| POST | `/api/v2/records/{record_id}/observations` | api/v2/phenology.py |
| GET | `/api/v2/stages` | api/v2/phenology.py |
| GET | `/api/v2/stats` | api/v2/phenology.py |

### Phenomic Selection (6 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/datasets` | api/v2/phenomic_selection.py |
| GET | `/api/v2/datasets/{dataset_id}` | api/v2/phenomic_selection.py |
| GET | `/api/v2/models` | api/v2/phenomic_selection.py |
| POST | `/api/v2/predict` | api/v2/phenomic_selection.py |
| GET | `/api/v2/spectral/{dataset_id}` | api/v2/phenomic_selection.py |
| GET | `/api/v2/statistics` | api/v2/phenomic_selection.py |

### Phenotype (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/anova` | api/v2/phenotype.py |
| POST | `/api/v2/correlation` | api/v2/phenotype.py |
| POST | `/api/v2/heritability` | api/v2/phenotype.py |
| GET | `/api/v2/methods` | api/v2/phenotype.py |
| POST | `/api/v2/selection-index` | api/v2/phenotype.py |
| POST | `/api/v2/selection-response` | api/v2/phenotype.py |
| POST | `/api/v2/stats` | api/v2/phenotype.py |

### Phenotype Comparison (5 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/compare` | api/v2/phenotype_comparison.py |
| GET | `/api/v2/germplasm` | api/v2/phenotype_comparison.py |
| POST | `/api/v2/observations` | api/v2/phenotype_comparison.py |
| GET | `/api/v2/statistics` | api/v2/phenotype_comparison.py |
| GET | `/api/v2/traits` | api/v2/phenotype_comparison.py |

### Plot History (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/event-types` | api/v2/plot_history.py |
| DELETE | `/api/v2/events/{event_id}` | api/v2/plot_history.py |
| PATCH | `/api/v2/events/{event_id}` | api/v2/plot_history.py |
| GET | `/api/v2/fields` | api/v2/plot_history.py |
| GET | `/api/v2/plots` | api/v2/plot_history.py |
| GET | `/api/v2/plots/{plot_id}` | api/v2/plot_history.py |
| GET | `/api/v2/plots/{plot_id}/events` | api/v2/plot_history.py |
| POST | `/api/v2/plots/{plot_id}/events` | api/v2/plot_history.py |
| GET | `/api/v2/stats` | api/v2/plot_history.py |

### Population Genetics (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/fst` | api/v2/population_genetics.py |
| GET | `/api/v2/hardy-weinberg/{population_id}` | api/v2/population_genetics.py |
| GET | `/api/v2/migration` | api/v2/population_genetics.py |
| GET | `/api/v2/pca` | api/v2/population_genetics.py |
| GET | `/api/v2/populations` | api/v2/population_genetics.py |
| GET | `/api/v2/populations/{population_id}` | api/v2/population_genetics.py |
| GET | `/api/v2/populations/{population_id}/statistics` | api/v2/population_genetics.py |
| GET | `/api/v2/structure` | api/v2/population_genetics.py |
| GET | `/api/v2/summary` | api/v2/population_genetics.py |

### Prahari (18 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/analyze` | api/v2/prahari.py |
| POST | `/api/v2/block` | api/v2/prahari.py |
| DELETE | `/api/v2/block/ip/{ip}` | api/v2/prahari.py |
| DELETE | `/api/v2/block/user/{user_id}` | api/v2/prahari.py |
| GET | `/api/v2/blocked` | api/v2/prahari.py |
| GET | `/api/v2/check/ip/{ip}` | api/v2/prahari.py |
| GET | `/api/v2/check/user/{user_id}` | api/v2/prahari.py |
| GET | `/api/v2/events` | api/v2/prahari.py |
| GET | `/api/v2/events/stats` | api/v2/prahari.py |
| GET | `/api/v2/events/suspicious-ips` | api/v2/prahari.py |
| POST | `/api/v2/reputation/bad` | api/v2/prahari.py |
| POST | `/api/v2/reputation/good` | api/v2/prahari.py |
| GET | `/api/v2/reputation/{ip}` | api/v2/prahari.py |
| GET | `/api/v2/responses` | api/v2/prahari.py |
| GET | `/api/v2/responses/stats` | api/v2/prahari.py |
| GET | `/api/v2/stats` | api/v2/prahari.py |
| GET | `/api/v2/threats` | api/v2/prahari.py |
| GET | `/api/v2/threats/stats` | api/v2/prahari.py |

### Processing (12 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/batches` | api/v2/processing.py |
| POST | `/api/v2/batches` | api/v2/processing.py |
| GET | `/api/v2/batches/{batch_id}` | api/v2/processing.py |
| POST | `/api/v2/batches/{batch_id}/hold` | api/v2/processing.py |
| POST | `/api/v2/batches/{batch_id}/quality-checks` | api/v2/processing.py |
| POST | `/api/v2/batches/{batch_id}/reject` | api/v2/processing.py |
| POST | `/api/v2/batches/{batch_id}/resume` | api/v2/processing.py |
| POST | `/api/v2/batches/{batch_id}/stages` | api/v2/processing.py |
| PUT | `/api/v2/batches/{batch_id}/stages/{stage_id}` | api/v2/processing.py |
| GET | `/api/v2/batches/{batch_id}/summary` | api/v2/processing.py |
| GET | `/api/v2/stages` | api/v2/processing.py |
| GET | `/api/v2/statistics` | api/v2/processing.py |

### Profile (10 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/activity` | api/v2/profile.py |
| POST | `/api/v2/change-password` | api/v2/profile.py |
| GET | `/api/v2/preferences` | api/v2/profile.py |
| PATCH | `/api/v2/preferences` | api/v2/profile.py |
| GET | `/api/v2/sessions` | api/v2/profile.py |
| DELETE | `/api/v2/sessions/{session_id}` | api/v2/profile.py |
| GET | `/api/v2/workspace` | api/v2/profile.py |
| PATCH | `/api/v2/workspace` | api/v2/profile.py |
| DELETE | `/api/v2/workspace/default` | api/v2/profile.py |
| PUT | `/api/v2/workspace/default` | api/v2/profile.py |

### Progeny (6 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/germplasm/{germplasm_id}` | api/v2/progeny.py |
| GET | `/api/v2/lineage/{germplasm_id}` | api/v2/progeny.py |
| GET | `/api/v2/parents` | api/v2/progeny.py |
| GET | `/api/v2/parents/{parent_id}` | api/v2/progeny.py |
| GET | `/api/v2/statistics` | api/v2/progeny.py |
| GET | `/api/v2/types` | api/v2/progeny.py |

### Programs (5 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/programs` | api/v2/core/programs.py |
| POST | `/api/v2/programs` | api/v2/core/programs.py |
| DELETE | `/api/v2/programs/{programDbId}` | api/v2/core/programs.py |
| GET | `/api/v2/programs/{programDbId}` | api/v2/core/programs.py |
| PUT | `/api/v2/programs/{programDbId}` | api/v2/core/programs.py |

### Progress (11 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/api-stats` | api/v2/progress.py |
| GET | `/api/v2/divisions` | api/v2/progress.py |
| GET | `/api/v2/divisions/{division_id}` | api/v2/progress.py |
| PATCH | `/api/v2/divisions/{division_id}` | api/v2/progress.py |
| GET | `/api/v2/features` | api/v2/progress.py |
| POST | `/api/v2/features` | api/v2/progress.py |
| PATCH | `/api/v2/features/{feature_id}` | api/v2/progress.py |
| GET | `/api/v2/roadmap` | api/v2/progress.py |
| GET | `/api/v2/summary` | api/v2/progress.py |
| PATCH | `/api/v2/summary` | api/v2/progress.py |
| GET | `/api/v2/tech-stack` | api/v2/progress.py |

### Qtl Mapping (11 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/go-enrichment` | api/v2/qtl_mapping.py |
| GET | `/api/v2/gwas` | api/v2/qtl_mapping.py |
| GET | `/api/v2/lod-profile/{chromosome}` | api/v2/qtl_mapping.py |
| GET | `/api/v2/manhattan` | api/v2/qtl_mapping.py |
| GET | `/api/v2/populations` | api/v2/qtl_mapping.py |
| GET | `/api/v2/qtls` | api/v2/qtl_mapping.py |
| GET | `/api/v2/qtls/{qtl_id}` | api/v2/qtl_mapping.py |
| GET | `/api/v2/qtls/{qtl_id}/candidates` | api/v2/qtl_mapping.py |
| GET | `/api/v2/summary/gwas` | api/v2/qtl_mapping.py |
| GET | `/api/v2/summary/qtl` | api/v2/qtl_mapping.py |
| GET | `/api/v2/traits` | api/v2/qtl_mapping.py |

### Quality (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/certificates` | api/v2/quality.py |
| GET | `/api/v2/samples` | api/v2/quality.py |
| POST | `/api/v2/samples` | api/v2/quality.py |
| GET | `/api/v2/samples/{sample_id}` | api/v2/quality.py |
| GET | `/api/v2/seed-classes` | api/v2/quality.py |
| GET | `/api/v2/standards` | api/v2/quality.py |
| GET | `/api/v2/summary` | api/v2/quality.py |
| GET | `/api/v2/test-types` | api/v2/quality.py |
| POST | `/api/v2/tests` | api/v2/quality.py |

### Quick Entry (10 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/cross` | api/v2/quick_entry.py |
| GET | `/api/v2/entries` | api/v2/quick_entry.py |
| DELETE | `/api/v2/entries/{entry_id}` | api/v2/quick_entry.py |
| GET | `/api/v2/entries/{entry_id}` | api/v2/quick_entry.py |
| POST | `/api/v2/germplasm` | api/v2/quick_entry.py |
| POST | `/api/v2/observation` | api/v2/quick_entry.py |
| GET | `/api/v2/options/{option_type}` | api/v2/quick_entry.py |
| GET | `/api/v2/recent` | api/v2/quick_entry.py |
| GET | `/api/v2/stats` | api/v2/quick_entry.py |
| POST | `/api/v2/trial` | api/v2/quick_entry.py |

### Rakshaka (10 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/anomalies` | api/v2/rakshaka.py |
| POST | `/api/v2/anomalies/{anomaly_id}/resolve` | api/v2/rakshaka.py |
| GET | `/api/v2/config` | api/v2/rakshaka.py |
| PUT | `/api/v2/config` | api/v2/rakshaka.py |
| POST | `/api/v2/heal` | api/v2/rakshaka.py |
| GET | `/api/v2/health` | api/v2/rakshaka.py |
| GET | `/api/v2/incidents` | api/v2/rakshaka.py |
| GET | `/api/v2/metrics` | api/v2/rakshaka.py |
| POST | `/api/v2/simulate` | api/v2/rakshaka.py |
| GET | `/api/v2/strategies` | api/v2/rakshaka.py |

### Rbac (12 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/my-permissions` | api/v2/rbac.py |
| GET | `/api/v2/permissions` | api/v2/rbac.py |
| GET | `/api/v2/roles` | api/v2/rbac.py |
| POST | `/api/v2/roles` | api/v2/rbac.py |
| DELETE | `/api/v2/roles/{role_id}` | api/v2/rbac.py |
| GET | `/api/v2/roles/{role_id}` | api/v2/rbac.py |
| PATCH | `/api/v2/roles/{role_id}` | api/v2/rbac.py |
| GET | `/api/v2/users` | api/v2/rbac.py |
| GET | `/api/v2/users/{user_id}/roles` | api/v2/rbac.py |
| POST | `/api/v2/users/{user_id}/roles` | api/v2/rbac.py |
| PUT | `/api/v2/users/{user_id}/roles` | api/v2/rbac.py |
| DELETE | `/api/v2/users/{user_id}/roles/{role_id}` | api/v2/rbac.py |

### Reports (16 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/builder/data-sources` | api/v2/reports.py |
| POST | `/api/v2/builder/preview` | api/v2/reports.py |
| GET | `/api/v2/builder/visualizations` | api/v2/reports.py |
| GET | `/api/v2/download/{report_id}` | api/v2/reports.py |
| POST | `/api/v2/generate` | api/v2/reports.py |
| GET | `/api/v2/generated` | api/v2/reports.py |
| DELETE | `/api/v2/generated/{report_id}` | api/v2/reports.py |
| GET | `/api/v2/schedules` | api/v2/reports.py |
| POST | `/api/v2/schedules` | api/v2/reports.py |
| DELETE | `/api/v2/schedules/{schedule_id}` | api/v2/reports.py |
| GET | `/api/v2/schedules/{schedule_id}` | api/v2/reports.py |
| PATCH | `/api/v2/schedules/{schedule_id}` | api/v2/reports.py |
| POST | `/api/v2/schedules/{schedule_id}/run` | api/v2/reports.py |
| GET | `/api/v2/stats` | api/v2/reports.py |
| GET | `/api/v2/templates` | api/v2/reports.py |
| GET | `/api/v2/templates/{template_id}` | api/v2/reports.py |

### Resource Management (19 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/budget` | api/v2/resource_management.py |
| GET | `/api/v2/budget/summary` | api/v2/resource_management.py |
| PATCH | `/api/v2/budget/{category_id}` | api/v2/resource_management.py |
| GET | `/api/v2/calendar` | api/v2/resource_management.py |
| POST | `/api/v2/calendar` | api/v2/resource_management.py |
| GET | `/api/v2/calendar/date/{target_date}` | api/v2/resource_management.py |
| GET | `/api/v2/calendar/summary` | api/v2/resource_management.py |
| DELETE | `/api/v2/calendar/{event_id}` | api/v2/resource_management.py |
| PATCH | `/api/v2/calendar/{event_id}/status` | api/v2/resource_management.py |
| GET | `/api/v2/fields` | api/v2/resource_management.py |
| GET | `/api/v2/fields/summary` | api/v2/resource_management.py |
| GET | `/api/v2/harvest` | api/v2/resource_management.py |
| POST | `/api/v2/harvest` | api/v2/resource_management.py |
| GET | `/api/v2/harvest/summary` | api/v2/resource_management.py |
| DELETE | `/api/v2/harvest/{record_id}` | api/v2/resource_management.py |
| PATCH | `/api/v2/harvest/{record_id}` | api/v2/resource_management.py |
| GET | `/api/v2/overview` | api/v2/resource_management.py |
| GET | `/api/v2/staff` | api/v2/resource_management.py |
| GET | `/api/v2/staff/summary` | api/v2/resource_management.py |

### Rls (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/context` | api/v2/rls.py |
| GET | `/api/v2/sql/disable` | api/v2/rls.py |
| GET | `/api/v2/sql/enable` | api/v2/rls.py |
| GET | `/api/v2/status` | api/v2/rls.py |
| GET | `/api/v2/tables` | api/v2/rls.py |
| GET | `/api/v2/test` | api/v2/rls.py |
| GET | `/api/v2/test/{table_name}` | api/v2/rls.py |
| POST | `/api/v2/verify-isolation` | api/v2/rls.py |

### Search (11 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/search` | api/v2/search.py |
| GET | `/api/v2/search/federated` | api/v2/search.py |
| GET | `/api/v2/search/geo/locations` | api/v2/search.py |
| GET | `/api/v2/search/germplasm` | api/v2/search.py |
| GET | `/api/v2/search/locations` | api/v2/search.py |
| GET | `/api/v2/search/programs` | api/v2/search.py |
| GET | `/api/v2/search/similar/{index_name}/{document_id}` | api/v2/search.py |
| GET | `/api/v2/search/stats` | api/v2/search.py |
| GET | `/api/v2/search/studies` | api/v2/search.py |
| GET | `/api/v2/search/traits` | api/v2/search.py |
| GET | `/api/v2/search/trials` | api/v2/search.py |

### Seasons (5 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/seasons` | api/v2/core/seasons.py |
| POST | `/api/v2/seasons` | api/v2/core/seasons.py |
| DELETE | `/api/v2/seasons/{seasonDbId}` | api/v2/core/seasons.py |
| GET | `/api/v2/seasons/{seasonDbId}` | api/v2/core/seasons.py |
| PUT | `/api/v2/seasons/{seasonDbId}` | api/v2/core/seasons.py |

### Security Audit (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/actor/{actor}` | api/v2/security_audit.py |
| GET | `/api/v2/categories` | api/v2/security_audit.py |
| POST | `/api/v2/export` | api/v2/security_audit.py |
| GET | `/api/v2/failed` | api/v2/security_audit.py |
| GET | `/api/v2/search` | api/v2/security_audit.py |
| GET | `/api/v2/severities` | api/v2/security_audit.py |
| GET | `/api/v2/stats` | api/v2/security_audit.py |
| GET | `/api/v2/target/{target:path}` | api/v2/security_audit.py |

### Seed Inventory (11 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/alerts` | api/v2/seed_inventory.py |
| GET | `/api/v2/lots` | api/v2/seed_inventory.py |
| POST | `/api/v2/lots` | api/v2/seed_inventory.py |
| GET | `/api/v2/lots/{lot_id}` | api/v2/seed_inventory.py |
| POST | `/api/v2/requests` | api/v2/seed_inventory.py |
| POST | `/api/v2/requests/{request_id}/approve` | api/v2/seed_inventory.py |
| POST | `/api/v2/requests/{request_id}/ship` | api/v2/seed_inventory.py |
| GET | `/api/v2/storage-types` | api/v2/seed_inventory.py |
| GET | `/api/v2/summary` | api/v2/seed_inventory.py |
| POST | `/api/v2/viability` | api/v2/seed_inventory.py |
| GET | `/api/v2/viability/{lot_id}` | api/v2/seed_inventory.py |

### Selection (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/base-index` | api/v2/selection.py |
| GET | `/api/v2/default-weights` | api/v2/selection.py |
| POST | `/api/v2/desired-gains` | api/v2/selection.py |
| POST | `/api/v2/differential` | api/v2/selection.py |
| POST | `/api/v2/independent-culling` | api/v2/selection.py |
| GET | `/api/v2/methods` | api/v2/selection.py |
| POST | `/api/v2/predict-response` | api/v2/selection.py |
| POST | `/api/v2/smith-hazel` | api/v2/selection.py |
| POST | `/api/v2/tandem` | api/v2/selection.py |

### Selection Decisions (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/candidates` | api/v2/selection_decisions.py |
| GET | `/api/v2/candidates/{candidate_id}` | api/v2/selection_decisions.py |
| POST | `/api/v2/candidates/{candidate_id}/decision` | api/v2/selection_decisions.py |
| POST | `/api/v2/decisions/bulk` | api/v2/selection_decisions.py |
| GET | `/api/v2/history` | api/v2/selection_decisions.py |
| GET | `/api/v2/programs` | api/v2/selection_decisions.py |
| GET | `/api/v2/statistics` | api/v2/selection_decisions.py |
| GET | `/api/v2/trials` | api/v2/selection_decisions.py |

### Sensors (18 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/alerts/events` | api/v2/sensors.py |
| POST | `/api/v2/alerts/events/{event_id}/acknowledge` | api/v2/sensors.py |
| GET | `/api/v2/alerts/rules` | api/v2/sensors.py |
| POST | `/api/v2/alerts/rules` | api/v2/sensors.py |
| DELETE | `/api/v2/alerts/rules/{rule_id}` | api/v2/sensors.py |
| PUT | `/api/v2/alerts/rules/{rule_id}` | api/v2/sensors.py |
| GET | `/api/v2/device-types` | api/v2/sensors.py |
| GET | `/api/v2/devices` | api/v2/sensors.py |
| POST | `/api/v2/devices` | api/v2/sensors.py |
| DELETE | `/api/v2/devices/{device_id}` | api/v2/sensors.py |
| GET | `/api/v2/devices/{device_id}` | api/v2/sensors.py |
| PUT | `/api/v2/devices/{device_id}/status` | api/v2/sensors.py |
| GET | `/api/v2/readings` | api/v2/sensors.py |
| POST | `/api/v2/readings` | api/v2/sensors.py |
| GET | `/api/v2/readings/live` | api/v2/sensors.py |
| GET | `/api/v2/readings/{device_id}/latest` | api/v2/sensors.py |
| GET | `/api/v2/sensor-types` | api/v2/sensors.py |
| GET | `/api/v2/stats` | api/v2/sensors.py |

### Serverinfo (1 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/serverinfo` | api/v2/core/serverinfo.py |

### Solar (11 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/agricultural-impacts` | api/v2/solar.py |
| GET | `/api/v2/current` | api/v2/solar.py |
| GET | `/api/v2/forecast` | api/v2/solar.py |
| GET | `/api/v2/magnetic` | api/v2/solar.py |
| GET | `/api/v2/photoperiod` | api/v2/solar.py |
| POST | `/api/v2/photoperiod` | api/v2/solar.py |
| GET | `/api/v2/photoperiod/series` | api/v2/solar.py |
| GET | `/api/v2/radiation` | api/v2/solar.py |
| POST | `/api/v2/radiation` | api/v2/solar.py |
| GET | `/api/v2/uv-index` | api/v2/solar.py |
| POST | `/api/v2/uv-index` | api/v2/solar.py |

### Space (11 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/agencies` | api/v2/space.py |
| GET | `/api/v2/crops` | api/v2/space.py |
| GET | `/api/v2/crops/{crop_id}` | api/v2/space.py |
| GET | `/api/v2/crops/{crop_id}/environment` | api/v2/space.py |
| GET | `/api/v2/experiments` | api/v2/space.py |
| GET | `/api/v2/experiments/{exp_id}` | api/v2/space.py |
| GET | `/api/v2/life-support` | api/v2/space.py |
| POST | `/api/v2/life-support` | api/v2/space.py |
| GET | `/api/v2/missions` | api/v2/space.py |
| GET | `/api/v2/radiation` | api/v2/space.py |
| POST | `/api/v2/radiation` | api/v2/space.py |

### Spatial (11 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/analyze/autocorrelation` | api/v2/spatial.py |
| POST | `/api/v2/analyze/moving-average` | api/v2/spatial.py |
| POST | `/api/v2/analyze/nearest-neighbor` | api/v2/spatial.py |
| POST | `/api/v2/analyze/row-column-trend` | api/v2/spatial.py |
| POST | `/api/v2/calculate/distance` | api/v2/spatial.py |
| GET | `/api/v2/fields` | api/v2/spatial.py |
| POST | `/api/v2/fields` | api/v2/spatial.py |
| GET | `/api/v2/fields/{field_id}` | api/v2/spatial.py |
| GET | `/api/v2/fields/{field_id}/plots` | api/v2/spatial.py |
| POST | `/api/v2/fields/{field_id}/plots` | api/v2/spatial.py |
| GET | `/api/v2/statistics` | api/v2/spatial.py |

### Speed Breeding (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/batches` | api/v2/speed_breeding.py |
| GET | `/api/v2/batches/{batch_id}` | api/v2/speed_breeding.py |
| GET | `/api/v2/chambers` | api/v2/speed_breeding.py |
| GET | `/api/v2/protocols` | api/v2/speed_breeding.py |
| GET | `/api/v2/protocols/{protocol_id}` | api/v2/speed_breeding.py |
| GET | `/api/v2/statistics` | api/v2/speed_breeding.py |
| POST | `/api/v2/timeline` | api/v2/speed_breeding.py |

### Stability Analysis (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/analyze` | api/v2/stability_analysis.py |
| GET | `/api/v2/comparison` | api/v2/stability_analysis.py |
| GET | `/api/v2/methods` | api/v2/stability_analysis.py |
| GET | `/api/v2/recommendations` | api/v2/stability_analysis.py |
| GET | `/api/v2/statistics` | api/v2/stability_analysis.py |
| GET | `/api/v2/varieties` | api/v2/stability_analysis.py |
| GET | `/api/v2/varieties/{variety_id}` | api/v2/stability_analysis.py |

### Statistics (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/anova` | api/v2/statistics.py |
| GET | `/api/v2/correlations` | api/v2/statistics.py |
| GET | `/api/v2/distribution` | api/v2/statistics.py |
| GET | `/api/v2/overview` | api/v2/statistics.py |
| GET | `/api/v2/summary` | api/v2/statistics.py |
| GET | `/api/v2/traits` | api/v2/statistics.py |
| GET | `/api/v2/trials` | api/v2/statistics.py |

### Studies (5 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/studies` | api/v2/core/studies.py |
| POST | `/api/v2/studies` | api/v2/core/studies.py |
| DELETE | `/api/v2/studies/{studyDbId}` | api/v2/core/studies.py |
| GET | `/api/v2/studies/{studyDbId}` | api/v2/core/studies.py |
| PUT | `/api/v2/studies/{studyDbId}` | api/v2/core/studies.py |

### Studytypes (1 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/studytypes` | api/v2/core/studytypes.py |

### System Settings (13 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/all` | api/v2/system_settings.py |
| GET | `/api/v2/api` | api/v2/system_settings.py |
| PATCH | `/api/v2/api` | api/v2/system_settings.py |
| GET | `/api/v2/export` | api/v2/system_settings.py |
| GET | `/api/v2/features` | api/v2/system_settings.py |
| PATCH | `/api/v2/features` | api/v2/system_settings.py |
| GET | `/api/v2/general` | api/v2/system_settings.py |
| PATCH | `/api/v2/general` | api/v2/system_settings.py |
| POST | `/api/v2/import` | api/v2/system_settings.py |
| POST | `/api/v2/reset-defaults` | api/v2/system_settings.py |
| GET | `/api/v2/security` | api/v2/system_settings.py |
| PATCH | `/api/v2/security` | api/v2/system_settings.py |
| GET | `/api/v2/status` | api/v2/system_settings.py |

### Tasks (6 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/` | api/v2/tasks.py |
| POST | `/api/v2/cleanup` | api/v2/tasks.py |
| GET | `/api/v2/stats` | api/v2/tasks.py |
| DELETE | `/api/v2/{task_id}` | api/v2/tasks.py |
| GET | `/api/v2/{task_id}` | api/v2/tasks.py |
| POST | `/api/v2/{task_id}/cancel` | api/v2/tasks.py |

### Team Management (13 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/invites` | api/v2/team_management.py |
| POST | `/api/v2/invites` | api/v2/team_management.py |
| DELETE | `/api/v2/invites/{invite_id}` | api/v2/team_management.py |
| POST | `/api/v2/invites/{invite_id}/resend` | api/v2/team_management.py |
| GET | `/api/v2/members` | api/v2/team_management.py |
| DELETE | `/api/v2/members/{member_id}` | api/v2/team_management.py |
| GET | `/api/v2/members/{member_id}` | api/v2/team_management.py |
| PATCH | `/api/v2/members/{member_id}` | api/v2/team_management.py |
| GET | `/api/v2/roles` | api/v2/team_management.py |
| GET | `/api/v2/stats` | api/v2/team_management.py |
| DELETE | `/api/v2/{team_id}` | api/v2/team_management.py |
| GET | `/api/v2/{team_id}` | api/v2/team_management.py |
| PATCH | `/api/v2/{team_id}` | api/v2/team_management.py |

### Traceability (15 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/event-types` | api/v2/traceability.py |
| GET | `/api/v2/lots` | api/v2/traceability.py |
| POST | `/api/v2/lots` | api/v2/traceability.py |
| GET | `/api/v2/lots/{lot_id}` | api/v2/traceability.py |
| GET | `/api/v2/lots/{lot_id}/certifications` | api/v2/traceability.py |
| POST | `/api/v2/lots/{lot_id}/certifications` | api/v2/traceability.py |
| GET | `/api/v2/lots/{lot_id}/descendants` | api/v2/traceability.py |
| POST | `/api/v2/lots/{lot_id}/events` | api/v2/traceability.py |
| GET | `/api/v2/lots/{lot_id}/history` | api/v2/traceability.py |
| GET | `/api/v2/lots/{lot_id}/lineage` | api/v2/traceability.py |
| GET | `/api/v2/lots/{lot_id}/qr` | api/v2/traceability.py |
| GET | `/api/v2/lots/{lot_id}/transfers` | api/v2/traceability.py |
| POST | `/api/v2/lots/{lot_id}/transfers` | api/v2/traceability.py |
| GET | `/api/v2/statistics` | api/v2/traceability.py |
| GET | `/api/v2/transfers` | api/v2/traceability.py |

### Trial Design (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/alpha-lattice` | api/v2/trial_design.py |
| POST | `/api/v2/augmented` | api/v2/trial_design.py |
| POST | `/api/v2/crd` | api/v2/trial_design.py |
| GET | `/api/v2/designs` | api/v2/trial_design.py |
| POST | `/api/v2/field-map` | api/v2/trial_design.py |
| POST | `/api/v2/rcbd` | api/v2/trial_design.py |
| POST | `/api/v2/split-plot` | api/v2/trial_design.py |

### Trial Network (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/compare` | api/v2/trial_network.py |
| GET | `/api/v2/countries` | api/v2/trial_network.py |
| GET | `/api/v2/germplasm` | api/v2/trial_network.py |
| GET | `/api/v2/performance` | api/v2/trial_network.py |
| GET | `/api/v2/seasons` | api/v2/trial_network.py |
| GET | `/api/v2/sites` | api/v2/trial_network.py |
| GET | `/api/v2/sites/{site_id}` | api/v2/trial_network.py |
| GET | `/api/v2/statistics` | api/v2/trial_network.py |

### Trial Planning (14 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/designs` | api/v2/trial_planning.py |
| GET | `/api/v2/seasons` | api/v2/trial_planning.py |
| GET | `/api/v2/statistics` | api/v2/trial_planning.py |
| GET | `/api/v2/timeline` | api/v2/trial_planning.py |
| GET | `/api/v2/types` | api/v2/trial_planning.py |
| DELETE | `/api/v2/{trial_id}` | api/v2/trial_planning.py |
| GET | `/api/v2/{trial_id}` | api/v2/trial_planning.py |
| PUT | `/api/v2/{trial_id}` | api/v2/trial_planning.py |
| POST | `/api/v2/{trial_id}/approve` | api/v2/trial_planning.py |
| POST | `/api/v2/{trial_id}/cancel` | api/v2/trial_planning.py |
| POST | `/api/v2/{trial_id}/complete` | api/v2/trial_planning.py |
| GET | `/api/v2/{trial_id}/resources` | api/v2/trial_planning.py |
| POST | `/api/v2/{trial_id}/resources` | api/v2/trial_planning.py |
| POST | `/api/v2/{trial_id}/start` | api/v2/trial_planning.py |

### Trial Summary (8 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/trials` | api/v2/trial_summary.py |
| GET | `/api/v2/trials/{trial_id}` | api/v2/trial_summary.py |
| POST | `/api/v2/trials/{trial_id}/export` | api/v2/trial_summary.py |
| GET | `/api/v2/trials/{trial_id}/locations` | api/v2/trial_summary.py |
| GET | `/api/v2/trials/{trial_id}/statistics` | api/v2/trial_summary.py |
| GET | `/api/v2/trials/{trial_id}/summary` | api/v2/trial_summary.py |
| GET | `/api/v2/trials/{trial_id}/top-performers` | api/v2/trial_summary.py |
| GET | `/api/v2/trials/{trial_id}/traits` | api/v2/trial_summary.py |

### Trials (5 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/trials` | api/v2/core/trials.py |
| POST | `/api/v2/trials` | api/v2/core/trials.py |
| DELETE | `/api/v2/trials/{trialDbId}` | api/v2/core/trials.py |
| GET | `/api/v2/trials/{trialDbId}` | api/v2/core/trials.py |
| PUT | `/api/v2/trials/{trialDbId}` | api/v2/core/trials.py |

### Vault Sensors (15 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/alerts` | api/v2/vault_sensors.py |
| GET | `/api/v2/alerts/{alert_id}` | api/v2/vault_sensors.py |
| POST | `/api/v2/alerts/{alert_id}/acknowledge` | api/v2/vault_sensors.py |
| GET | `/api/v2/conditions` | api/v2/vault_sensors.py |
| GET | `/api/v2/conditions/{vault_id}` | api/v2/vault_sensors.py |
| POST | `/api/v2/link` | api/v2/vault_sensors.py |
| GET | `/api/v2/readings` | api/v2/vault_sensors.py |
| GET | `/api/v2/sensors` | api/v2/vault_sensors.py |
| GET | `/api/v2/sensors/{sensor_id}` | api/v2/vault_sensors.py |
| POST | `/api/v2/sensors/{sensor_id}/readings` | api/v2/vault_sensors.py |
| GET | `/api/v2/statistics` | api/v2/vault_sensors.py |
| GET | `/api/v2/thresholds/{vault_id}` | api/v2/vault_sensors.py |
| POST | `/api/v2/thresholds/{vault_id}` | api/v2/vault_sensors.py |
| DELETE | `/api/v2/unlink/{sensor_id}` | api/v2/vault_sensors.py |
| GET | `/api/v2/vault-types` | api/v2/vault_sensors.py |

### Vector (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/index` | api/v2/vector.py |
| POST | `/api/v2/index/germplasm` | api/v2/vector.py |
| POST | `/api/v2/index/protocol` | api/v2/vector.py |
| POST | `/api/v2/index/trial` | api/v2/vector.py |
| POST | `/api/v2/initialize` | api/v2/vector.py |
| POST | `/api/v2/search` | api/v2/vector.py |
| POST | `/api/v2/similar` | api/v2/vector.py |
| GET | `/api/v2/stats` | api/v2/vector.py |
| DELETE | `/api/v2/{doc_id}` | api/v2/vector.py |

### Vision (50 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| POST | `/api/v2/annotations/bounding-box` | api/v2/vision.py |
| POST | `/api/v2/annotations/segmentation` | api/v2/vision.py |
| DELETE | `/api/v2/annotations/{annotation_id}` | api/v2/vision.py |
| PUT | `/api/v2/annotations/{annotation_id}` | api/v2/vision.py |
| POST | `/api/v2/annotations/{annotation_id}/review` | api/v2/vision.py |
| POST | `/api/v2/annotations/{annotation_id}/submit` | api/v2/vision.py |
| GET | `/api/v2/annotators` | api/v2/vision.py |
| GET | `/api/v2/annotators/{annotator_id}/stats` | api/v2/vision.py |
| GET | `/api/v2/base-models` | api/v2/vision.py |
| GET | `/api/v2/crops` | api/v2/vision.py |
| GET | `/api/v2/datasets` | api/v2/vision.py |
| POST | `/api/v2/datasets` | api/v2/vision.py |
| DELETE | `/api/v2/datasets/{dataset_id}` | api/v2/vision.py |
| GET | `/api/v2/datasets/{dataset_id}` | api/v2/vision.py |
| PUT | `/api/v2/datasets/{dataset_id}` | api/v2/vision.py |
| POST | `/api/v2/datasets/{dataset_id}/export` | api/v2/vision.py |
| GET | `/api/v2/datasets/{dataset_id}/images` | api/v2/vision.py |
| POST | `/api/v2/datasets/{dataset_id}/images` | api/v2/vision.py |
| GET | `/api/v2/datasets/{dataset_id}/quality` | api/v2/vision.py |
| GET | `/api/v2/datasets/{dataset_id}/stats` | api/v2/vision.py |
| POST | `/api/v2/datasets/{dataset_id}/tasks` | api/v2/vision.py |
| GET | `/api/v2/deployments` | api/v2/vision.py |
| DELETE | `/api/v2/deployments/{deploy_id}` | api/v2/vision.py |
| GET | `/api/v2/deployments/{deploy_id}` | api/v2/vision.py |
| GET | `/api/v2/deployments/{deploy_id}/stats` | api/v2/vision.py |
| GET | `/api/v2/images/{image_id}/annotations` | api/v2/vision.py |
| GET | `/api/v2/models` | api/v2/vision.py |
| GET | `/api/v2/models/{model_id}` | api/v2/vision.py |
| POST | `/api/v2/models/{model_id}/deploy` | api/v2/vision.py |
| POST | `/api/v2/models/{model_id}/export` | api/v2/vision.py |
| POST | `/api/v2/models/{model_id}/publish` | api/v2/vision.py |
| GET | `/api/v2/models/{model_id}/versions` | api/v2/vision.py |
| GET | `/api/v2/models/{model_id}/versions/latest` | api/v2/vision.py |
| POST | `/api/v2/predict` | api/v2/vision.py |
| GET | `/api/v2/registry` | api/v2/vision.py |
| GET | `/api/v2/registry/featured` | api/v2/vision.py |
| GET | `/api/v2/registry/{registry_id}` | api/v2/vision.py |
| POST | `/api/v2/registry/{registry_id}/download` | api/v2/vision.py |
| POST | `/api/v2/registry/{registry_id}/like` | api/v2/vision.py |
| GET | `/api/v2/tasks` | api/v2/vision.py |
| GET | `/api/v2/tasks/{task_id}` | api/v2/vision.py |
| GET | `/api/v2/training/augmentation-options` | api/v2/vision.py |
| GET | `/api/v2/training/hyperparameters/recommend` | api/v2/vision.py |
| GET | `/api/v2/training/jobs` | api/v2/vision.py |
| POST | `/api/v2/training/jobs` | api/v2/vision.py |
| POST | `/api/v2/training/jobs/compare` | api/v2/vision.py |
| GET | `/api/v2/training/jobs/{job_id}` | api/v2/vision.py |
| POST | `/api/v2/training/jobs/{job_id}/cancel` | api/v2/vision.py |
| GET | `/api/v2/training/jobs/{job_id}/logs` | api/v2/vision.py |
| POST | `/api/v2/training/jobs/{job_id}/start` | api/v2/vision.py |

### Voice (4 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/health` | api/v2/voice.py |
| POST | `/api/v2/synthesize` | api/v2/voice.py |
| GET | `/api/v2/synthesize/stream` | api/v2/voice.py |
| GET | `/api/v2/voices` | api/v2/voice.py |

### Warehouse (7 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/alerts` | api/v2/warehouse.py |
| GET | `/api/v2/locations` | api/v2/warehouse.py |
| POST | `/api/v2/locations` | api/v2/warehouse.py |
| DELETE | `/api/v2/locations/{location_id}` | api/v2/warehouse.py |
| GET | `/api/v2/locations/{location_id}` | api/v2/warehouse.py |
| PATCH | `/api/v2/locations/{location_id}` | api/v2/warehouse.py |
| GET | `/api/v2/summary` | api/v2/warehouse.py |

### Weather (6 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/activity-windows/{location_id}` | api/v2/weather.py |
| GET | `/api/v2/alerts` | api/v2/weather.py |
| GET | `/api/v2/forecast/{location_id}` | api/v2/weather.py |
| GET | `/api/v2/gdd/{location_id}` | api/v2/weather.py |
| GET | `/api/v2/impacts/{location_id}` | api/v2/weather.py |
| GET | `/api/v2/veena/summary/{location_id}` | api/v2/weather.py |

### Workflows (9 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/runs/history` | api/v2/workflows.py |
| GET | `/api/v2/stats` | api/v2/workflows.py |
| GET | `/api/v2/templates/list` | api/v2/workflows.py |
| POST | `/api/v2/templates/{template_id}/use` | api/v2/workflows.py |
| DELETE | `/api/v2/{workflow_id}` | api/v2/workflows.py |
| GET | `/api/v2/{workflow_id}` | api/v2/workflows.py |
| PATCH | `/api/v2/{workflow_id}` | api/v2/workflows.py |
| POST | `/api/v2/{workflow_id}/run` | api/v2/workflows.py |
| POST | `/api/v2/{workflow_id}/toggle` | api/v2/workflows.py |

### Yield Map (5 endpoints)

| Method | Path | Source File |
|--------|------|-------------|
| GET | `/api/v2/studies` | api/v2/yield_map.py |
| GET | `/api/v2/studies/{study_id}/plots` | api/v2/yield_map.py |
| GET | `/api/v2/studies/{study_id}/spatial-analysis` | api/v2/yield_map.py |
| GET | `/api/v2/studies/{study_id}/stats` | api/v2/yield_map.py |
| GET | `/api/v2/studies/{study_id}/traits` | api/v2/yield_map.py |

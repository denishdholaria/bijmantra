<![CDATA[# Bijmantra API Reference

**Last Updated:** January 3, 2026  
**Total Endpoints:** 1,447  
**API Version:** v2.0 + BrAPI v2.1

> ⚠️ **Note:** Endpoint counts verified via `scripts/extract_endpoints.py`. See `docs/api/ENDPOINT_INVENTORY.md` for complete listing.

---

## BrAPI v2.1 Standard (201 endpoints)

### Core Module (50 endpoints)

| Resource | Endpoints | Operations |
|:---------|----------:|:-----------|
| Programs | 5 | CRUD + search |
| Locations | 5 | CRUD + search |
| Trials | 5 | CRUD + search |
| Studies | 5 | CRUD + search |
| Seasons | 5 | CRUD + search |
| Lists | 7 | CRUD + items |
| Pedigree | 3 | Query ancestry |
| Server Info | 1 | Metadata |
| Common Crop Names | 1 | Reference |
| Study Types | 1 | Reference |
| Search (Core) | 12 | Async POST/GET |

### Germplasm Module (39 endpoints)

| Resource | Endpoints | Operations |
|:---------|----------:|:-----------|
| Germplasm | 8 | CRUD + pedigree/progeny/MCPD |
| Seed Lots | 7 | CRUD + transactions |
| Crosses | 4 | CRUD |
| Crossing Projects | 5 | CRUD |
| Planned Crosses | 5 | CRUD |
| Attributes | 5 | CRUD + categories |
| Attribute Values | 4 | CRUD |
| Breeding Methods | 2 | Reference |
| People | 5 | CRUD |
| Search (Germplasm) | 10 | Async POST/GET |

### Phenotyping Module (51 endpoints)

| Resource | Endpoints | Operations |
|:---------|----------:|:-----------|
| Observations | 7 | CRUD + table format |
| Observation Units | 6 | CRUD + table format |
| Variables | 5 | CRUD |
| Traits | 4 | CRUD |
| Methods | 4 | CRUD |
| Scales | 4 | CRUD |
| Ontologies | 5 | CRUD |
| Images | 6 | CRUD + content |
| Samples | 6 | CRUD |
| Events | 3 | CRUD |
| Observation Levels | 1 | Reference |
| Search (Phenotyping) | 14 | Async POST/GET |

### Genotyping Module (61 endpoints)

| Resource | Endpoints | Operations |
|:---------|----------:|:-----------|
| Variant Sets | 6 | CRUD + extract |
| Variants | 3 | Query |
| Call Sets | 3 | Query |
| Calls | 2 | Query |
| Plates | 5 | CRUD |
| References | 3 | Query + bases |
| Reference Sets | 2 | Query |
| Maps | 3 | Query + linkage groups |
| Marker Positions | 1 | Query |
| Allele Matrix | 1 | Query |
| Vendor | 8 | Orders, plates, results |
| Search (Genotyping) | 12 | Async POST/GET |
| Delete | 8 | Bulk delete operations |

### BrAPI IoT Extension (7 endpoints)

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/extensions/iot/devices` | GET | IoT device metadata |
| `/extensions/iot/sensors` | GET | Sensor catalog |
| `/extensions/iot/telemetry` | GET | Time-series data |
| `/extensions/iot/aggregates` | GET | Environmental summaries |
| `/extensions/iot/alerts` | GET | Alert events |
| `/extensions/iot/sensor-types` | GET | Reference data |
| `/extensions/iot/environmental-parameters` | GET | G×E parameters |

---

## Custom APIs (1,246 endpoints)

### Plant Sciences (312 endpoints)

| Service | Endpoints | Purpose |
|:--------|----------:|:--------|
| crossing_planner.py | 11 | Cross planning workflow |
| selection.py | 9 | Selection index calculations |
| selection_decisions.py | 8 | Selection decision records |
| parent_selection.py | 8 | Parent selection |
| breeding_pipeline.py | 9 | Pipeline stage tracking |
| breeding_value.py | 8 | BLUP/GBLUP estimation |
| genetic_gain.py | 10 | Genetic gain tracking |
| performance_ranking.py | 7 | Entry ranking |
| progeny.py | 6 | Progeny management |
| germplasm_comparison.py | 6 | Side-by-side comparison |
| genotyping.py | 16 | Genotyping data |
| qtl_mapping.py | 11 | QTL analysis |
| genomic_selection.py | 10 | GS models |
| population_genetics.py | 9 | Population structure |
| genetic_diversity.py | 8 | Diversity metrics |
| mas.py | 10 | Marker-assisted selection |
| haplotype.py | 8 | Haplotype analysis |
| gwas.py | 8 | GWAS pipeline |
| field_map.py | 11 | Field/plot management |
| field_planning.py | 7 | Season planning |
| field_environment.py | 14 | Soil, irrigation, inputs |
| trial_design.py | 7 | Experimental design |
| trial_planning.py | 16 | Trial workflow |
| phenotype.py | 7 | Phenotype analysis |
| pedigree.py | 8 | Pedigree analysis |
| gxe.py | 5 | G×E interaction |
| spatial.py | 11 | Spatial analysis |
| statistics.py | 7 | Statistical summaries |

### Seed Bank (59 endpoints)

| Service | Endpoints | Purpose |
|:--------|----------:|:--------|
| seed_bank/router.py | 22 | Vaults, accessions, viability |
| vault_sensors.py | 15 | Environmental monitoring |
| mta.py | 15 | Material transfer agreements |
| grin.py | 9 | GRIN-Global integration |
| barcode.py | 10 | Barcode/QR management |

### Seed Operations (96 endpoints)

| Service | Endpoints | Purpose |
|:--------|----------:|:--------|
| quality.py | 9 | QC testing & certificates |
| processing.py | 12 | Seed processing workflow |
| dus.py | 17 | DUS testing (UPOV) |
| seed_inventory.py | 11 | Lot management |
| dispatch.py | 18 | Order & shipping |
| traceability.py | 14 | Chain of custody |
| licensing.py | 17 | Variety licensing |

### Environment (54 endpoints)

| Service | Endpoints | Purpose |
|:--------|----------:|:--------|
| weather.py | 6 | Weather forecasts, GDD |
| solar.py | 11 | Solar radiation, photoperiod |
| sensors.py | 18 | IoT device management |

### AI & Compute (95 endpoints)

| Service | Endpoints | Purpose |
|:--------|----------:|:--------|
| vision.py | 50 | Plant disease detection |
| chat.py | 4 | Veena AI chat |
| voice.py | 4 | Voice synthesis |
| insights.py | 5 | AI-generated insights |
| compute.py | 6 | GBLUP, statistical compute |
| vector.py | 9 | Vector search (RAG) |
| search.py | 4 | Full-text search |

### Security & System (72 endpoints)

| Service | Endpoints | Purpose |
|:--------|----------:|:--------|
| prahari.py | 18 | Threat detection |
| chaitanya.py | 13 | AI orchestration |
| rakshaka.py | 10 | Self-healing |
| audit.py | 6 | Audit trail |
| events.py | 8 | Event bus |
| tasks.py | 6 | Background tasks |
| progress.py | 12 | Dev progress |

### Research & Knowledge (35 endpoints)

| Service | Endpoints | Purpose |
|:--------|----------:|:--------|
| space.py | 11 | Interplanetary agriculture |
| forums.py | 13 | Community forums |
| devguru.py | 11 | PhD mentoring |

### Field Tools (46 endpoints)

| Service | Endpoints | Purpose |
|:--------|----------:|:--------|
| quick_entry.py | 10 | Quick data entry |
| label_printing.py | 9 | Label generation |
| harvest.py | 15 | Harvest management |
| resource_management.py | 19 | Resource allocation |

---

## Verification Commands

```bash
# Count API endpoints
grep -r "@router\." backend/app/api/ --include="*.py" | grep -E "\.(get|post|put|patch|delete)\(" | wc -l
grep -r "@router\." backend/app/modules/ --include="*.py" | grep -E "\.(get|post|put|patch|delete)\(" | wc -l
```

---

*Built with 💚 for the global plant breeding community*
]]>

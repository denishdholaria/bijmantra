# LOKAS Architecture — Domain Boundaries

**Status**: Planning  
**Created**: January 3, 2026  
**Last Updated**: January 3, 2026

---

## Overview

LOKAS (लोक — "Worlds/Realms") defines the bounded contexts for BijMantra's modular monolith architecture. Each LOKA is a sovereign domain with clear responsibilities and boundaries.

**Principle**: LOKAs communicate via **events**, not direct imports.

**Import Enforcement**: AANAYAN (आनयन) — from Ānayana-maryādā-niyama (आनयन-मर्यादा-नियम)

---

## The Seven LOKAs

| LOKA | Sanskrit | Meaning | Responsibility |
|------|----------|---------|----------------|
| **SRISTI** | सृष्टि | Creation | Breeding programs, crosses, trials, selection |
| **BIJA-KOSHA** | बीज-कोष | Seed Treasury | Germplasm, inventory, seedlots, accessions |
| **RUPA** | रूप | Form | Phenotyping, traits, observations, images |
| **KSHETRA** | क्षेत्र | Field | Locations, field ops, sensors, weather |
| **MEDHA** | मेधा | Intelligence | Analytics, genomics, AI, statistics |
| **VANI** | वाणी | Commerce | Licensing, DUS, traceability, orders |
| **VIDYA** | विद्या | Knowledge | Forums, DevGuru, training, documentation |

---

## Directory Structure (Target)

```
backend/app/
├── api/                    # Entry points (unchanged)
│   ├── brapi/              # BrAPI compliance
│   └── v2/                 # Custom APIs
│
├── lokas/                  # Domain boundaries
│   ├── __init__.py
│   │
│   ├── sristi/             # 🌱 Breeding Core
│   │   ├── __init__.py
│   │   ├── services/
│   │   ├── schemas/
│   │   └── events.py
│   │
│   ├── bija_kosha/         # 🏦 Germplasm & Inventory
│   │   ├── __init__.py
│   │   ├── services/
│   │   ├── schemas/
│   │   └── events.py
│   │
│   ├── rupa/               # 📊 Phenomics
│   │   ├── __init__.py
│   │   ├── services/
│   │   ├── schemas/
│   │   └── events.py
│   │
│   ├── kshetra/            # 🌍 Field Operations
│   │   ├── __init__.py
│   │   ├── services/
│   │   ├── schemas/
│   │   └── events.py
│   │
│   ├── medha/              # 🧠 Intelligence
│   │   ├── __init__.py
│   │   ├── services/
│   │   ├── schemas/
│   │   └── events.py
│   │
│   ├── vani/               # 💼 Commercial
│   │   ├── __init__.py
│   │   ├── services/
│   │   ├── schemas/
│   │   └── events.py
│   │
│   └── vidya/              # 📚 Knowledge
│       ├── __init__.py
│       ├── services/
│       ├── schemas/
│       └── events.py
│
├── models/                 # Shared data layer (unchanged)
├── services/               # Legacy services (gradual migration)
├── core/                   # Infrastructure (unchanged)
└── modules/                # Deprecated → migrate to lokas/
```

---

## Service-to-LOKA Mapping

### SRISTI (Breeding Core)
```
breeding_pipeline.py
breeding_value.py
cross_prediction.py
crossing_planner.py
doubled_haploid.py
parent_selection.py
progeny.py
selection_decisions.py
selection_index.py
speed_breeding.py
```

### BIJA-KOSHA (Germplasm & Inventory)
```
seed_inventory.py
seed_traceability.py
germplasm_comparison.py
germplasm_passport.py
germplasm_search.py
nursery.py
```

### RUPA (Phenomics)
```
phenotype_analysis.py
phenology.py
phenomic_selection.py
trait_ontology.py
vision_annotation.py
vision_datasets.py
vision_deployment.py
vision_training.py
```

### KSHETRA (Field Operations)
```
field_environment.py
field_map.py
field_planning.py
field_scanner.py
harvest_management.py
plot_history.py
sensor_network.py
spatial_analysis.py
weather_service.py
vault_sensors.py
iot_aggregation.py
```

### MEDHA (Intelligence)
```
bioinformatics.py
compute_engine.py
genetic_diversity.py
genetic_gain.py
genomic_selection.py
genotyping.py
gwas.py
gxe_analysis.py
haplotype_analysis.py
marker_assisted.py
molecular_breeding.py
population_genetics.py
qtl_mapping.py
statistics.py
llm_service.py
vector_store.py
```

### VANI (Commercial)
```
dispatch_management.py
dus_testing.py
dus_crops.py
processing_batch.py
quality_control.py
variety_licensing.py
```

### VIDYA (Knowledge)
```
devguru_service.py
forums.py
```

---

## Import Rules

### ✅ ALLOWED

```python
# Import from shared infrastructure
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings

# Import from shared models
from app.models.germplasm import Germplasm
from app.models.core import Program, Trial

# Import event bus for cross-domain communication
from app.services.event_bus import event_bus

# Import within same LOKA
from app.lokas.sristi.services.breeding_pipeline import BreedingPipeline
```

### ❌ FORBIDDEN

```python
# Direct cross-LOKA imports
from app.lokas.bija_kosha.services.seed_inventory import SeedInventory  # NO!
from app.lokas.medha.services.genomic_selection import GenomicSelection  # NO!
```

### ✅ CORRECT Cross-Domain Communication

```python
# In sristi/services/crossing_planner.py
from app.services.event_bus import event_bus

async def complete_cross(cross_id: int):
    # ... perform cross logic ...
    
    # Emit event instead of importing bija_kosha
    await event_bus.emit("sristi.cross_completed", {
        "cross_id": cross_id,
        "seeds_produced": seed_count,
        "parent1_id": parent1.id,
        "parent2_id": parent2.id,
    })

# In bija_kosha/subscribers.py
from app.services.event_bus import event_bus

@event_bus.on("sristi.cross_completed")
async def handle_cross_completed(data: dict):
    # Create seedlot from cross
    await create_seedlot(
        source_type="cross",
        source_id=data["cross_id"],
        quantity=data["seeds_produced"],
    )
```

---

## Event Contracts

### SRISTI Events
| Event | Payload | Consumers |
|-------|---------|-----------|
| `sristi.cross_completed` | cross_id, parent1_id, parent2_id, seeds_produced | bija_kosha |
| `sristi.selection_made` | germplasm_ids, trial_id, criteria | medha |
| `sristi.trial_advanced` | trial_id, stage, germplasm_count | kshetra |

### BIJA-KOSHA Events
| Event | Payload | Consumers |
|-------|---------|-----------|
| `bija_kosha.seedlot_created` | seedlot_id, germplasm_id, quantity | sristi, kshetra |
| `bija_kosha.germplasm_added` | germplasm_id, accession_number | medha |
| `bija_kosha.inventory_low` | seedlot_id, current_quantity, threshold | vani |

### RUPA Events
| Event | Payload | Consumers |
|-------|---------|-----------|
| `rupa.observation_recorded` | observation_id, trait_id, value | medha |
| `rupa.phenotype_complete` | study_id, observation_count | sristi |

### KSHETRA Events
| Event | Payload | Consumers |
|-------|---------|-----------|
| `kshetra.trial_planted` | trial_id, location_id, plot_count | sristi, rupa |
| `kshetra.harvest_completed` | trial_id, yield_data | bija_kosha, medha |
| `kshetra.weather_alert` | location_id, alert_type, severity | sristi |

### MEDHA Events
| Event | Payload | Consumers |
|-------|---------|-----------|
| `medha.analysis_completed` | analysis_id, type, results_url | sristi, vidya |
| `medha.gebv_calculated` | germplasm_ids, trait_id, values | sristi |

### VANI Events
| Event | Payload | Consumers |
|-------|---------|-----------|
| `vani.license_granted` | variety_id, license_id, territory | bija_kosha |
| `vani.order_placed` | order_id, seedlot_id, quantity | bija_kosha |

### VIDYA Events
| Event | Payload | Consumers |
|-------|---------|-----------|
| `vidya.question_asked` | question_id, topic, user_id | medha |

---

## Migration Strategy

### Phase 1: Linting Rules (Current)
- ✅ Create `pyproject.toml` with ruff configuration
- ✅ Document LOKAS structure
- No code movement yet

### Phase 2: New Code in LOKAs
- New services created in `lokas/*/services/`
- Existing code stays in `services/` until touched

### Phase 3: Gradual Migration
- When modifying a service → move to appropriate LOKA
- Add re-export in old location for backward compatibility
- Update imports in dependent files

### Phase 4: Deprecate Legacy
- Remove `backend/app/modules/` (migrate to lokas)
- Remove re-exports after all imports updated

---

## Future LOKAs (Reserved)

| LOKA | Sanskrit | Purpose |
|------|----------|---------|
| PRITHVI | पृथ्वी | Soil science, carbon sequestration |
| JALA | जल | Irrigation, water management |
| VAYU | वायु | Climate modeling, emissions |
| AGNI | अग्नि | Energy, biofuels |

---

## Enforcement — AANAYAN (आनयन)

### Automated (ruff)
- Import sorting
- Code style
- Future: Custom rules for cross-LOKA imports

### Manual (Code Review)
- Verify no direct cross-LOKA imports
- Verify events used for cross-domain communication
- Verify new services placed in correct LOKA

---

*This document is the authority for LOKAS architecture decisions.*

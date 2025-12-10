# Bijmantra Architecture

**Last Updated**: December 10, 2025

Bijmantra is an aerospace-grade plant breeding platform built on the **Parashakti Framework**, combining high-precision numerical computing with modern web technologies.

---

## Vision

> "Build tools that solve real problems, not encyclopedias that document everything."

- **100% Open Source** — No proprietary dependencies
- **PWA-First** — Offline-capable, installable, field-ready
- **Modular Architecture** — Modules that evolve independently
- **Multi-Engine Compute** — Python, Rust/WASM, Fortran
- **AI-First** — Veena assistant with RAG and voice

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE LAYER                        │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │ React PWA │  │ Veena AI  │  │  Voice    │  │  Mobile   │    │
│  │   (Web)   │  │    🪷     │  │ Commands  │  │(Capacitor)│    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                      APPLICATION LAYER                           │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  FastAPI  │  │ WebSocket │  │  BrAPI    │  │   Auth    │    │
│  │  REST API │  │ Real-time │  │   v2.1    │  │   JWT     │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                       COMPUTE LAYER                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              HYBRID COMPUTE ENGINE                       │    │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │    │
│  │  │Fortran │  │  Rust  │  │  WASM  │  │ WebGPU │        │    │
│  │  │  HPC   │  │  FFI   │  │Browser │  │  GPU   │        │    │
│  │  └────────┘  └────────┘  └────────┘  └────────┘        │    │
│  │              BLAS / LAPACK / MKL                         │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                        DATA LAYER                                │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │PostgreSQL │  │   Redis   │  │Meilisearch│  │ IndexedDB │    │
│  │+ pgvector │  │   Cache   │  │  Search   │  │  Offline  │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18+ | UI framework |
| TypeScript | 5+ | Type safety |
| Vite | 5+ | Build tool |
| Tailwind CSS | 3+ | Styling |
| shadcn/ui | Latest | Components |
| TanStack Query | 5+ | Server state |
| Zustand | 4+ | Client state |
| Dexie.js | Latest | IndexedDB |
| Workbox | 7+ | Service worker |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Main language |
| FastAPI | 0.110+ | REST API |
| SQLAlchemy | 2.0+ | ORM |
| Pydantic | 2+ | Validation |
| asyncpg | Latest | Async PostgreSQL |

### Database & Storage
| Technology | Purpose |
|------------|---------|
| PostgreSQL 16+ | Primary database |
| PostGIS 3.4+ | Spatial data |
| pgvector 0.6+ | Vector embeddings |
| Redis 7+ | Caching |
| MinIO | Object storage |
| Meilisearch | Full-text search |

### Compute Engines
| Engine | Use Case |
|--------|----------|
| Fortran | BLUP, GBLUP, REML, kinship matrices |
| Rust/WASM | Browser genomics, matrices |
| Python | API, ML inference |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| Podman | Rootless containers |
| Caddy | Reverse proxy, auto HTTPS |

---

## Compute Architecture

### Why Fortran for Numerical Computing?

| Aspect | Fortran | Python/NumPy | Rust |
|--------|---------|--------------|------|
| Numerical Precision | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| BLAS/LAPACK | Native | Wrapper | FFI |
| Scientific Heritage | 60+ years | 20 years | 5 years |
| Reproducibility | Deterministic | Platform-dependent | Good |

### Fortran Modules
| Module | Purpose |
|--------|---------|
| `blup_solver.f90` | BLUP, GBLUP, MME solver |
| `reml_engine.f90` | AI-REML, EM-REML |
| `kinship.f90` | VanRaden, Yang matrices |
| `pca_svd.f90` | Truncated SVD, PCA |
| `ld_analysis.f90` | r², D', LD decay |
| `gxe_analysis.f90` | AMMI, GGE biplot |

### WASM Genomics Engine
```
┌─────────────────────────────────────────────┐
│         Rust/WebAssembly Engine             │
├─────────────────────────────────────────────┤
│  Genomics        │  Matrix Operations       │
│  - Allele Freq   │  - GRM (VanRaden)        │
│  - LD (r², D')   │  - A-Matrix (Pedigree)   │
│  - HWE Test      │  - IBS Matrix            │
├──────────────────┼──────────────────────────┤
│  Statistics      │  Population Genetics     │
│  - BLUP/GBLUP    │  - Diversity Metrics     │
│  - Selection     │  - Fst, PCA              │
│  - Heritability  │  - AMMI (G×E)            │
└─────────────────────────────────────────────┘
Performance: ~100x faster │ Memory Safe │ Browser Native
```

---

## Project Structure

```
bijmantra/
├── frontend/src/
│   ├── framework/           # Parashakti core
│   │   ├── registry/        # Module registry
│   │   └── shell/           # Navigation, layout
│   ├── components/          # Shared components
│   ├── pages/               # 271+ page components
│   ├── lib/                 # Utilities, API client
│   └── store/               # Zustand stores
├── backend/app/
│   ├── api/v2/              # BrAPI v2.1 endpoints
│   ├── core/                # Auth, config, database
│   ├── models/              # SQLAlchemy models
│   └── schemas/             # Pydantic schemas
├── fortran/                 # HPC compute modules
├── rust/                    # WASM modules
└── docs/                    # Documentation
```

---

## Offline Architecture

```
┌─────────────────────────────────────────────┐
│          Service Worker (Workbox)           │
├─────────────────────────────────────────────┤
│  Static Assets    → Cache First             │
│  BrAPI Metadata   → Stale While Revalidate  │
│  Observation Data → Network First + Queue   │
│  Plant Images     → Cache First (7 days)    │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│           IndexedDB (Dexie.js)              │
├─────────────────────────────────────────────┤
│  observations (pending sync)                │
│  traits (cached metadata)                   │
│  studies, germplasm (cached data)           │
│  sync_queue (CRDT operations)               │
└─────────────────────────────────────────────┘
```

---

## AI/ML Integration

### Current Status

| Component | UI | Backend | Status |
|-----------|:--:|:-------:|--------|
| Veena AI Assistant 🪷 | ✅ | ✅ | Complete with RAG |
| Veena Voice | ✅ | ✅ | VibeVoice + Edge TTS |
| Plant Vision | ✅ | ❌ | UI done, needs TensorFlow.js models |
| Field Scanner | ✅ | ❌ | UI done, needs CV models |
| Yield Predictor | ✅ | ❌ | UI done, needs ML backend |
| WASM Genomics | ✅ | ❌ | UI done, needs Rust compilation |
| pgvector | - | ✅ | Ready |
| MCP Server | - | ✅ | ChatGPT/Claude integration |
| Disease Resistance | ✅ | ✅ | Complete (Dec 10) |
| Abiotic Stress | ✅ | ✅ | Complete (Dec 10) |
| DUS Testing | ✅ | ✅ | Complete (Dec 10) |
| MCPD Exchange | ✅ | ✅ | Complete (Dec 10) |

### Veena AI Assistant 🪷
Named after Goddess Saraswati's sacred instrument:
- Natural language queries for breeding data
- Voice commands ("Hey Veena")
- RAG-powered responses (pgvector)
- Multi-tier TTS (VibeVoice → Edge TTS → Web Speech)
- 8 voice options (US/UK/India English + Hindi)
- 384-dimensional embeddings (MiniLM)

### AI/ML Roadmap

#### ✅ Phase 1: Foundation — COMPLETE
| Task | Status | Endpoint |
|------|--------|----------|
| Embedding Service | ✅ Done | `backend/app/services/vector_store.py` |
| Vector Search API | ✅ Done | `/api/v2/vector/search` |
| Veena RAG Backend | ✅ Done | `/api/v2/chat` |
| Veena Voice | ✅ Done | `/api/v2/voice` |

#### ✅ Phase 2: Genomic Selection — COMPLETE
| Task | Status | Endpoint |
|------|--------|----------|
| GBLUP Backend | ✅ Done | `/api/v2/breeding-value/gblup` |
| BLUP Backend | ✅ Done | `/api/v2/breeding-value/blup` |
| Cross Prediction | ✅ Done | `/api/v2/crosses` |
| Breeding Values API | ✅ Done | `/api/v2/breeding-value` |

#### 🔄 Phase 3: Computer Vision — IN PROGRESS
| Task | Status | Notes |
|------|--------|-------|
| Disease Detection Model | ❌ Pending | TensorFlow.js model needed |
| Growth Stage Classifier | ❌ Pending | BBCH scale |
| Plant Vision Backend | ❌ Pending | Model serving |

#### ✅ Phase 4: MCP Integration — COMPLETE
| Task | Status | Location |
|------|--------|----------|
| MCP Server | ✅ Done | `backend/app/mcp/server.py` |
| BrAPI Tools | ✅ Done | Trial, germplasm, cross prediction |

#### ✅ Phase 5: Advanced Analytics — COMPLETE
| Task | Status | Endpoint |
|------|--------|----------|
| GWAS Pipeline | ✅ Done | `/api/v2/gwas` |
| G×E Analysis | ✅ Done | `/api/v2/gxe` |
| Selection Index | ✅ Done | `/api/v2/selection` |
| Genetic Gain | ✅ Done | `/api/v2/genetic-gain` |
| Spatial Analysis | ✅ Done | `/api/v2/spatial` |

#### 🔄 Phase 6: WASM Compilation — PENDING
| Task | Status | Notes |
|------|--------|-------|
| Compile Rust to WASM | ❌ Pending | GRM, LD, PCA |

### Enhanced BrAPI for AI/ML

Future BrAPI improvements for ML-readiness:

```json
// Enhanced Observation with ML metadata
{
  "observationDbId": "obs12345",
  "value": 172.3,
  "valueUnit": "cm",
  "dataQuality": {
    "qualityFlag": "PASS",
    "confidenceScore": 0.95
  },
  "sensorMetadata": {
    "sensorType": "Drone RGB Camera",
    "flightHeightMeters": 15.0
  },
  "mlHints": {
    "featureImportanceRank": 3,
    "encodingRecommended": "numeric"
  }
}
```

### AI Tools Summary

| Tool | Route | Purpose |
|------|-------|---------|
| Plant Vision | `/plant-vision` | Disease, growth stage, stress |
| Field Scanner | `/field-scanner` | Real-time camera capture |
| Disease Atlas | `/disease-atlas` | Reference database |
| Crop Health | `/crop-health` | Trial monitoring |
| Yield Predictor | `/yield-predictor` | AI predictions |
| WASM Genomics | `/wasm-genomics` | Browser-side compute |
| WASM GBLUP | `/wasm-gblup` | Genomic BLUP |
| WASM PopGen | `/wasm-popgen` | Diversity, Fst, PCA |
| Insights | `/insights` | AI recommendations |

---

## Security

- JWT tokens (24h access, 7d refresh)
- RBAC with module-level permissions
- Multi-tenant isolation via organization_id
- Row-level security in PostgreSQL
- HTTPS only (Caddy auto-TLS)

---

## BrAPI v2.1 Compliance

### Modules Implemented
- **Core**: Programs, Trials, Studies, Locations, People, Lists, Seasons
- **Germplasm**: Germplasm, Seed Lots, Crosses, Pedigree, Attributes
- **Phenotyping**: Observations, Variables, Traits, Scales, Methods, Images
- **Genotyping**: Samples, Variants, Calls, Allele Matrix, Plates, Maps

**Status**: 34/34 endpoints (100%)

---

## Development

### Quick Start
```bash
make dev              # Start infrastructure
make dev-backend      # http://localhost:8000
make dev-frontend     # http://localhost:5173
```

### Testing
```bash
cd frontend && npm run test:run   # Frontend tests
cd backend && pytest              # Backend tests
```

---

## Resources

- [Parashakti Specification](framework/PARASHAKTI_SPECIFICATION.md)
- [BrAPI Specification](https://brapi.org)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)

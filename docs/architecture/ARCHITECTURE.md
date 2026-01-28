# Bijmantra Architecture

**Last Updated**: January 12, 2026  
**Version**: preview-1 Prathama

Bijmantra is a plant breeding platform built on the **Parashakti Framework**, combining high-precision numerical computing with modern web technologies.

---

## Vision

> "Build tools that solve real problems, not encyclopedias that document everything."

- **Open Source** — Source available, free for non-commercial use (see LICENSE)
- **PWA-First** — Offline-capable, installable, field-ready
- **Modular Architecture** — 8 modules that evolve independently
- **Multi-Engine Compute** — Python, Rust/WASM, Fortran
- **AI-First** — Veena assistant with RAG and voice

---

## Current Status (CALF Assessment)

> **Important**: As of preview-1, the CALF assessment revealed:
> - 221 total pages, but only 23 (10%) are fully functional with real computation
> - 42 pages (19%) return demo data instead of database queries
> - See `docs/CALF.md` for complete assessment

| CALF Level | Description | Count | Status |
|------------|-------------|-------|--------|
| CALF-0 | Display Only | 89 (40%) | ✅ Acceptable |
| CALF-1 | Client-Side Calculation | 67 (30%) | ⚠️ Needs backend |
| CALF-2 | Backend Query (Demo Data) | 42 (19%) | 🔴 Critical |
| CALF-3 | Real Computation | 18 (8%) | ⚠️ Mixed |
| CALF-4 | WASM/High-Performance | 5 (2%) | ✅ Excellent |

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
| ECharts | Latest | Visualizations |
| Lucide React | Latest | Icons |

### Theme System
| Component | File | Purpose |
|-----------|------|---------|
| Theme Store | `frontend/src/store/themeStore.ts` | Zustand store for theme state |
| Theme Toggle | `frontend/src/components/ThemeToggle.tsx` | UI component (Light/Dark/System) |
| Prakruti CSS | `frontend/src/styles/prakruti.css` | Design system variables |
| Theme Utilities | `frontend/src/styles/theme-utilities.css` | Semantic CSS classes |
| useTheme Hook | `frontend/src/hooks/useTheme.ts` | React hook for theme access |

**Theme Options:**
- **Light** — Force light mode
- **Dark** — Force dark mode
- **System** — Follow OS preference

**Features:**
- Synchronous initialization (no flash of wrong theme)
- Cross-tab synchronization via localStorage
- System preference detection and auto-update
- Legacy migration support

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Main language |
| FastAPI | 0.110+ | REST API |
| SQLAlchemy | 2.0+ | ORM (async) |
| Pydantic | 2+ | Validation |
| asyncpg | Latest | Async PostgreSQL |

### Database & Storage
| Technology | Purpose |
|------------|---------|
| PostgreSQL 15+ | Primary database (121 tables) |
| PostGIS 3.4+ | Spatial data |
| pgvector 0.6+ | Vector embeddings (RAG) |
| Redis 7+ | Caching, rate limiting |
| MinIO | Object storage |
| Meilisearch | Full-text search |

### Compute Engines
| Engine | Use Case | Status |
|--------|----------|--------|
| Fortran | BLUP, GBLUP, REML, kinship matrices | ✅ Implemented |
| Rust/WASM | Browser genomics, matrices | ✅ Implemented |
| Python | API, ML inference | ✅ Implemented |
| WebGPU | GPU acceleration | ✅ Available (browser-dependent) |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| Podman | Rootless containers |
| Caddy | Reverse proxy, auto HTTPS |

---

## Container Runtime: Podman

> **For Docker users**: BijMantra uses **Podman** instead of Docker. All commands are compatible — just replace `docker` with `podman`.

### Why Podman?

| Factor | Podman | Docker | Decision |
|--------|--------|--------|----------|
| **Security** | Rootless by default | Requires root daemon | Podman ✓ |
| **Architecture** | Daemonless (no SPOF) | Central daemon | Podman ✓ |
| **OCI Compliance** | Native OCI images | OCI-compatible | Tie |
| **Kubernetes** | Native pod support | Requires conversion | Podman ✓ |
| **Command Compatibility** | `podman` = `docker` | — | Tie |

### Key Differences for Docker Users

```bash
# Docker command          →  Podman equivalent
docker compose up -d      →  podman compose up -d
docker ps                 →  podman ps
docker build              →  podman build
docker-compose.yml        →  compose.yaml (same format)
```

### For Production Deployments

Both Docker and Podman work in production. The `compose.yaml` file is compatible with both:

```bash
# Using Podman (recommended)
podman compose -f compose.yaml -f compose.prod.yaml up -d

# Using Docker (also works)
docker compose -f compose.yaml -f compose.prod.yaml up -d
```

---

## Compute Architecture

### Why Fortran for Numerical Computing?

| Aspect | Fortran | Python/NumPy | Rust |
|--------|---------|--------------|------|
| Numerical Precision | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| BLAS/LAPACK | Native | Wrapper | FFI |
| Scientific Heritage | 60+ years | 20 years | 5 years |
| Reproducibility | Deterministic | Platform-dependent | Good |

### Fortran Modules (fortran/src/)
| Module | Purpose |
|--------|---------|
| `blup_solver.f90` | BLUP, GBLUP, MME solver |
| `reml_engine.f90` | AI-REML, EM-REML |
| `kinship.f90` | VanRaden, Yang matrices |
| `pca_svd.f90` | Truncated SVD, PCA |
| `ld_analysis.f90` | r², D', LD decay |
| `gxe_analysis.f90` | AMMI, GGE biplot |
| `stability_analysis.f90` | Stability metrics |
| `selection_index.f90` | Selection indices |
| `c_interface.f90` | C/Rust FFI bindings |

### WASM Genomics Engine (rust/src/)
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
│   │   ├── auth/            # Authentication
│   │   ├── features/        # Feature flags
│   │   ├── hooks/           # Framework hooks
│   │   ├── registry/        # Module registry
│   │   ├── routing/         # Route management
│   │   ├── shell/           # Navigation, layout
│   │   └── sync/            # Offline sync
│   ├── components/          # Shared components
│   ├── divisions/           # Module-specific pages
│   ├── pages/               # 221 page components
│   ├── lib/                 # Utilities, API client
│   ├── store/               # Zustand stores
│   ├── styles/              # Prakruti design system
│   └── wasm/                # WASM bindings
├── backend/app/
│   ├── api/                 # API endpoints
│   │   ├── brapi/           # BrAPI v2.1 (201 endpoints)
│   │   └── v2/              # Custom APIs (1,181 endpoints)
│   ├── core/                # Auth, config, database
│   ├── crud/                # CRUD operations
│   ├── db/                  # Migrations, seeders
│   ├── integrations/        # External adapters
│   ├── mcp/                 # MCP server
│   ├── middleware/          # Request middleware
│   ├── models/              # SQLAlchemy models (111)
│   ├── modules/             # Domain modules
│   ├── schemas/             # Pydantic schemas
│   └── services/            # Business logic
├── fortran/src/             # HPC compute modules (9 files)
├── rust/src/                # WASM modules
└── docs/                    # Documentation
    ├── architecture/        # This file
    ├── api/                 # API documentation
    ├── gupt/                # Internal docs (not public)
    ├── operations/          # Deployment guides
    └── standards/           # RWT, agricultural standards
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
| pgvector Embeddings | - | ✅ | Ready |
| MCP Server | - | ✅ | ChatGPT/Claude integration |
| Disease Resistance | ✅ | ✅ | Complete |
| Abiotic Stress | ✅ | ✅ | Complete |
| DUS Testing | ✅ | ✅ | Complete |
| MCPD Exchange | ✅ | ✅ | Complete |
| Plant Vision | ✅ | ❌ | UI done, needs TensorFlow.js models |
| Field Scanner | ✅ | ❌ | UI done, needs CV models |
| Yield Predictor | ✅ | ❌ | UI done, needs ML backend |
| WASM Genomics | ✅ | ⚠️ | UI done, Rust code exists, needs compilation |

### Veena AI Assistant 🪷
Named after Goddess Saraswati's sacred instrument:
- Natural language queries for breeding data
- Voice commands ("Hey Veena")
- RAG-powered responses (pgvector)
- Multi-tier TTS (VibeVoice → Edge TTS → Web Speech)
- 8 voice options (US/UK/India English + Hindi)
- 384-dimensional embeddings (MiniLM)

### AI/ML Implementation Status

#### ✅ Phase 1: Foundation — COMPLETE
| Task | Status | Location |
|------|--------|----------|
| Embedding Service | ✅ Done | `backend/app/services/vector_store.py` |
| Vector Search API | ✅ Done | `/api/v2/vector/search` |
| Veena RAG Backend | ✅ Done | `/api/v2/chat` |
| Veena Voice | ✅ Done | `/api/v2/voice` |

#### ✅ Phase 2: Genomic Selection — COMPLETE
| Task | Status | Location |
|------|--------|----------|
| GBLUP Backend | ✅ Done | `/api/v2/breeding-value/gblup` |
| BLUP Backend | ✅ Done | `/api/v2/breeding-value/blup` |
| Cross Prediction | ✅ Done | `/api/v2/crosses` |
| Breeding Values API | ✅ Done | `/api/v2/breeding-value` |

#### ⚠️ Phase 3: Computer Vision — PENDING
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
| Task | Status | Location |
|------|--------|----------|
| GWAS Pipeline | ✅ Done | `/api/v2/gwas` |
| G×E Analysis | ✅ Done | `/api/v2/gxe` |
| Selection Index | ✅ Done | `/api/v2/selection` |
| Genetic Gain | ✅ Done | `/api/v2/genetic-gain` |
| Spatial Analysis | ✅ Done | `/api/v2/spatial` |

#### ⚠️ Phase 6: WASM Compilation — PENDING
| Task | Status | Notes |
|------|--------|-------|
| Compile Rust to WASM | ❌ Pending | GRM, LD, PCA — Rust code exists in `rust/src/` |

---

## Security

- JWT tokens (24h access, 7d refresh)
- RBAC with module-level permissions (5 default roles)
- Multi-tenant isolation via organization_id
- Row-level security in PostgreSQL (87 tables, 100% coverage)
- Redis-backed rate limiting
- HTTPS only (Caddy auto-TLS)

---

## BrAPI v2.1 Compliance

### Modules Implemented
- **Core**: Programs, Trials, Studies, Locations, People, Lists, Seasons
- **Germplasm**: Germplasm, Seed Lots, Crosses, Pedigree, Attributes
- **Phenotyping**: Observations, Variables, Traits, Scales, Methods, Images
- **Genotyping**: Samples, Variants, Calls, Allele Matrix, Plates, Maps

**Status**: 201/201 endpoints (100%)

---

## Metrics Summary

| Metric | Value |
|--------|-------|
| Total Pages | 221 |
| API Endpoints | 1,382 (201 BrAPI + 1,181 custom) |
| Database Tables | 121 |
| Database Models | 111 |
| Migrations | 28 |
| Seeders | 15 (2 always-run + 13 demo) |
| RLS Coverage | 100% (87 tables) |
| Total Tests | 352 (88 unit, 18 integration, 229 E2E, 17 a11y) |
| Modules | 8 |
| Workspaces | 5 |
| Build Size | ~8.3MB (56 PWA entries) |

**Source**: `/metrics.json` — Single source of truth

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

### Build
```bash
cd frontend && npm run build      # Production build (~8.3MB PWA)
```

---

## Data Architecture

BijMantra uses a **dual-plane architecture** separating operational and analytical concerns:

| Document | Purpose |
|----------|---------|
| [DATA_ARCHITECTURE_CURRENT.md](DATA_ARCHITECTURE_CURRENT.md) | Current PostgreSQL-based OLTP implementation |
| [DATA_LAKE_TARGET_ARCHITECTURE.md](DATA_LAKE_TARGET_ARCHITECTURE.md) | Target Parquet/Arrow analytical layer (roadmap) |

**Current State**: PostgreSQL is the sole data store. All 137 tables, BrAPI endpoints, and CRUD operations use SQLAlchemy async queries.

**Target State**: Hybrid architecture with PostgreSQL (operational) + Parquet/DuckDB (analytical) planes coexisting.

---

## Platform Law Stack

BijMantra is governed by a formal **Platform Law Stack** — a layered system of binding documents that define architecture, boundaries, standards, and operational rules.

See **[PLATFORM_LAW_INDEX.md](PLATFORM_LAW_INDEX.md)** for the complete governance framework.

| Layer | Documents | Purpose |
|-------|-----------|---------|
| Foundation | GOVERNANCE.md | Evidence-based review, anti-sycophancy |
| Architecture | ARCHITECTURE.md, DATA_ARCHITECTURE_*.md | System shape, data truth |
| External Law | interoperability_contract.md | BrAPI, MCPD, standards |
| Internal Law | DOMAIN_OWNERSHIP.md, schema_governance.md, AI_AGENT_GOVERNANCE.md | Boundaries, ownership |
| Operations | MODULE_ACCEPTANCE_CRITERIA.md, LOKAS_STRUCTURE.md, RISK_MITIGATION.md | Entry gate, resilience |
| Culture | CONTRIBUTOR_ONBOARDING.md | Mindset, expectations |

---

## Resources

- [CALF Assessment](../CALF.md) — Computational functionality analysis
- [Platform Law Index](PLATFORM_LAW_INDEX.md) — Complete governance framework
- [Data Architecture (Current)](DATA_ARCHITECTURE_CURRENT.md) — PostgreSQL implementation
- [Data Lake (Target)](DATA_LAKE_TARGET_ARCHITECTURE.md) — Parquet/Arrow roadmap
- [LOKAS Structure](LOKAS_STRUCTURE.md) — Domain boundary architecture
- [Parashakti Specification](framework/PARASHAKTI_SPECIFICATION.md)
- [BrAPI Specification](https://brapi.org)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)

# 🔬 BijMantra Technical Deep Dive

> **For senior engineers, architects, and technical evaluators.**

This document provides architectural depth beyond the main README. It covers compute engines, data flow, system boundaries, and technical decisions that shape BijMantra.

---

## 📊 System at a Glance

| Dimension | Value | Source |
|-----------|-------|--------|
| Total Pages | 230 | `metrics.json` |
| API Endpoints | 1,475 | `metrics.json` |
| Database Tables | 137 | `metrics.json` |
| RLS-Protected Tables | 103 | `metrics.json` |
| BrAPI v2.1 Coverage | 100% (201/201) | `metrics.json` |
| Test Count | 352 | `metrics.json` |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (PWA)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   React 18  │  │  WASM       │  │  IndexedDB (Dexie.js)   │  │
│  │  TypeScript │  │  Genomics   │  │  Offline Storage (IndexedDB)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  BrAPI v2.1 │  │  Custom API │  │  WebSocket (Veena AI)   │  │
│  │  201 endpts │  │  1,274 endpts│  │  Streaming responses    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     COMPUTE LAYER                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Python    │  │  Rust/WASM  │  │  Fortran (via FFI)      │  │
│  │  Services   │  │  Genomics   │  │  BLUP, REML, Kinship    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ PostgreSQL  │  │   Redis     │  │  MinIO (Object Store)   │  │
│  │ + PostGIS   │  │   Cache     │  │  Images, Files          │  │
│  │ + pgvector  │  │             │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧮 Multi-Engine Compute Architecture

BijMantra uses three compute engines, each optimized for specific workloads.

### Python (Primary)

**Role**: API logic, orchestration, ML pipelines, data transformation

**Location**: `backend/app/services/`

**Key Services**:
```
breeding_value_service.py    # EBV calculation, cross prediction
gxe_service.py               # G×E analysis (AMMI, GGE, Finlay-Wilkinson)
genetic_diversity_service.py # He, Ho, F, allelic richness
weather_service.py           # GDD calculation, forecast integration
gwas.py                      # Genome-wide association studies
qtl_mapping.py               # QTL detection
```

**Pattern**: All services are async, use `AsyncSession` for database access, and enforce `organization_id` for multi-tenant isolation.

### Rust/WASM (Browser-Side Genomics)

**Role**: High-performance matrix operations running in the browser

**Location**: `rust/src/`

**Key Modules**:
```
lib.rs                       # Main entry, PyO3 module definition
python_bindings.rs           # Python FFI (PyO3 0.27)
wasm_bindings.rs             # WASM exports for browser
```

**Capabilities**:
- Genomic Relationship Matrix (GRM) computation
- GBLUP calculations
- Kinship matrix operations
- Runs entirely client-side via WASM

**Build Targets**:
```bash
cargo build --release                           # Native
cargo build --target wasm32-unknown-unknown     # WASM
cargo build --features python                   # Python bindings
```

### Fortran (Numerical Kernels)

**Role**: Battle-tested statistical algorithms (BLUP, REML, variance components)

**Location**: `fortran/src/`

**Integration**: Called from Rust via FFI (`rust/build.rs`)

**Why Fortran?**
- Decades of validated implementations in plant breeding
- Numerical stability for large matrices
- Industry-standard algorithms (ASReml-compatible)

**Key Algorithms**:
```
blup.f90                     # Best Linear Unbiased Prediction
reml.f90                     # Restricted Maximum Likelihood
kinship.f90                  # Kinship/relationship matrices
```

---

## 🔐 Row-Level Security (RLS) Architecture

BijMantra implements PostgreSQL RLS as a first-class architectural primitive.

### Coverage

- **103 tables** with RLS policies enabled
- **100% coverage** of tables with `organization_id`

### Implementation

**Database Level** (`backend/alembic/versions/`):
```sql
-- Enable RLS on table
ALTER TABLE germplasm ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY germplasm_org_isolation ON germplasm
    USING (organization_id = current_setting('app.current_organization_id')::integer);
```

**Application Level** (`backend/app/core/rls.py`):
```python
RLS_ENABLED_TABLES = [
    "germplasm", "trials", "studies", "observations",
    "samples", "seedlots", "crosses", "programs",
    # ... 103 tables total
]
```

**Query Pattern**:
```python
async def get_germplasm(db: AsyncSession, organization_id: int):
    result = await db.execute(
        select(Germplasm)
        .where(Germplasm.organization_id == organization_id)
    )
    return result.scalars().all()
```

### Why RLS?

1. **Defense in depth** — Even if application logic fails, database enforces isolation
2. **Audit compliance** — Data boundaries are provable at database level
3. **Multi-tenant safety** — No accidental cross-organization data leakage

---

## 🌐 BrAPI v2.1 Implementation

BijMantra implements 100% of BrAPI v2.1 specification (201/201 endpoints).

### Endpoint Distribution

| Module | Endpoints | Location |
|--------|-----------|----------|
| Core | 50 | `backend/app/api/brapi/core/` |
| Germplasm | 39 | `backend/app/api/brapi/germplasm.py` |
| Phenotyping | 51 | `backend/app/api/brapi/observations.py`, `variables.py` |
| Genotyping | 61 | `backend/app/api/brapi/samples.py`, `variants.py` |

### Response Format

All BrAPI endpoints return standard wrapper:
```json
{
  "@context": ["https://brapi.org/jsonld/context/metadata.jsonld"],
  "metadata": {
    "pagination": { "currentPage": 0, "pageSize": 20, "totalCount": 100 },
    "status": [{ "messageType": "INFO", "message": "Request successful" }]
  },
  "result": { ... }
}
```

### Compliance Testing

```bash
cd backend
pytest tests/integration/test_brapi_live.py -v
```

Tests run against official BrAPI test server (`https://test-server.brapi.org/brapi/v2/`).

---

## 🤖 Veena AI Architecture

Veena (वीणा) is BijMantra's cross-domain AI assistant.

### Function Execution

**Location**: `backend/app/services/function_executor.py`

**Status**: 32 functions use real database queries (zero demo functions remaining)

### Function Categories

| Category | Functions | Backend |
|----------|-----------|---------|
| Search | 8 | `*_search_service.py` |
| Details | 7 | Direct DB queries |
| Utility | 4 | Statistics, comparison |
| Weather/GDD | 3 | `weather_service.py` |
| Breeding/Genetics | 3 | `breeding_value_service.py`, `genetic_diversity_service.py` |
| G×E Analysis | 1 | `gxe_service.py` |
| Write Operations | 3 | Direct DB writes |
| Export/Report | 2 | `DataExportService` |
| Navigation | 1 | Frontend routing |

### Cross-Domain Query

The `cross_domain_query` function surfaces insights across 6 domains:
- Germplasm
- Trials
- Traits
- Locations
- Seedlots
- Programs

**Insight Types**:
- `data_gap` — Germplasm without phenotypic observations
- `incomplete_trial` — Trials without studies/observations
- `trait_gap` — Traits without observations in queried germplasm
- `seed_availability` — Seedlots with low quantity
- `coverage_summary` — Location × germplasm coverage

---

## 📦 PWA Architecture

BijMantra is a Progressive Web App with offline capabilities for field data collection.

### Service Worker

**Technology**: Workbox (via vite-plugin-pwa)

**Strategy**: 
- Static assets: Cache-first
- API calls: Network-first with offline fallback
- Images: Stale-while-revalidate

### Offline Storage

**Technology**: Dexie.js (IndexedDB wrapper)

**Capabilities**:
- Queue mutations when offline
- Sync when connection restored
- Conflict resolution UI

### Bundle Size

| Chunk | Size |
|-------|------|
| Main bundle | ~2.9 MB |
| vendor-three | 666 KB |
| vendor-icons | 99 KB |
| vendor-echarts | 1.1 MB |
| **Total PWA** | **~8.3 MB** |

---

## 🗄️ Database Schema

### Core Entities

```
organizations (1)
    └── users (N)
    └── programs (N)
            └── trials (N)
                    └── studies (N)
                            └── observation_units (N)
                                    └── observations (N)
    └── germplasm (N)
            └── samples (N)
            └── seedlots (N)
    └── traits (N)
            └── observation_variables (N)
```

### Key Tables

| Table | Purpose | RLS |
|-------|---------|-----|
| `germplasm` | Plant genetic resources | ✅ |
| `trials` | Field experiments | ✅ |
| `studies` | Trial subdivisions | ✅ |
| `observations` | Phenotypic measurements | ✅ |
| `samples` | DNA/tissue samples | ✅ |
| `calls` | Genotype calls | ✅ |
| `variants` | Genetic variants | ✅ |

### Extensions

- **PostGIS** — Spatial queries for location data
- **pgvector** — Vector similarity for AI embeddings

---

## 🧪 Testing Architecture

### Test Pyramid

```
         ┌─────────┐
         │   E2E   │  229 tests (Playwright)
         │ (slow)  │
        ┌┴─────────┴┐
        │Integration│  18 tests (BrAPI live)
        │ (medium)  │
       ┌┴───────────┴┐
       │    Unit     │  88 tests (pytest)
       │   (fast)    │
       └─────────────┘
```

### E2E Framework

**Technology**: Playwright

**Coverage**:
- 221 page render tests
- Authentication flows
- CRUD operations
- Accessibility (axe-core)
- Visual regression
- Performance (Core Web Vitals)

**Location**: `frontend/e2e/`

### Backend Tests

**Technology**: pytest + pytest-asyncio

**Location**: `backend/tests/`

**Markers**:
```bash
pytest                      # All tests
pytest -m unit              # Unit only
pytest -m integration       # Integration only
```

---

## 📐 Governance as Code

BijMantra treats governance documents as executable constraints.

### Platform Law Stack

14 documents in 7 layers:

| Layer | Documents |
|-------|-----------|
| Foundation | GOVERNANCE.md |
| Architecture | ARCHITECTURE.md, DATA_ARCHITECTURE_CURRENT.md, DATA_LAKE_TARGET_ARCHITECTURE.md |
| External Law | INTEROPERABILITY_CONTRACT.md |
| Internal Law | DOMAIN_OWNERSHIP.md, SCHEMA_GOVERNANCE.md, AI_AGENT_GOVERNANCE.md |
| Operations | MODULE_ACCEPTANCE_CRITERIA.md, OPERATIONAL_PLAYBOOK.md, RELEASE_PROCESS.md |
| Resilience | RISK_MITIGATION.md, ADR_FRAMEWORK.md |
| Culture | CONTRIBUTOR_ONBOARDING.md |

### Key Constraints

1. **Evidence-based reviews** — No code judged without direct inspection
2. **Async safety** — Never mix async endpoints with blocking I/O
3. **Zero Mock Data** — All data from database, never in-memory arrays
4. **Cross-domain integration** — Every module must support domain interoperability

📄 **[PLATFORM_LAW_INDEX.md](docs/architecture/PLATFORM_LAW_INDEX.md)** — Complete framework

---

## 🔄 Data Flow Examples

### Breeding Value Calculation

```
User Request
    │
    ▼
FastAPI Endpoint (/api/v2/breeding/calculate-ebv)
    │
    ▼
breeding_value_service.py
    │
    ├── Query observations (PostgreSQL)
    ├── Query pedigree (PostgreSQL)
    │
    ▼
Rust/Fortran Compute
    │
    ├── Build relationship matrix (Rust)
    ├── BLUP calculation (Fortran)
    │
    ▼
Return EBV results
```

### Cross-Domain Query (Veena)

```
User: "What germplasm is drought-tolerant and suitable for low-nitrogen soils?"
    │
    ▼
Veena Chat Endpoint (/api/v2/chat/stream)
    │
    ▼
function_executor.py → cross_domain_query()
    │
    ├── germplasm_search_service (trait filter: drought tolerance)
    ├── trial_search_service (location filter)
    ├── observation_search_service (trait values)
    │
    ▼
Cross-domain insight generation
    │
    ├── data_gap: Germplasm without observations
    ├── trait_gap: Missing trait data
    ├── coverage_summary: Location × germplasm matrix
    │
    ▼
Streamed response with insights
```

---

## 🚀 Deployment Architecture

### Container Stack

```yaml
services:
  frontend:
    image: bijmantra-frontend
    ports: ["5173:5173"]
    
  backend:
    image: bijmantra-backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis]
    
  postgres:
    image: postgres:15
    extensions: [postgis, pgvector]
    
  redis:
    image: redis:7
    
  caddy:
    image: caddy:2
    # Reverse proxy + TLS
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/bijmantra

# Security
SECRET_KEY=<random-256-bit>
CORS_ORIGINS=["https://bijmantra.org"]

# AI (optional)
GOOGLE_API_KEY=<gemini-key>
OPENWEATHERMAP_API_KEY=<weather-key>

# Feature flags
SEED_DEMO_DATA=false  # Production: false
```

---

## 📈 Performance Characteristics

### Measured (E2E Tests)

| Metric | Value | Threshold |
|--------|-------|-----------|
| LCP | 1.5-1.9s | < 4s |
| CLS | 0.00017 | < 0.25 |
| Navigation | 1.2-1.3s | < 3s |
| Memory growth | 0 MB | < 50 MB |

### Bundle Analysis

```bash
cd frontend
npm run build -- --analyze
```

---

## 🔮 Future Architecture (Planned)

### LOKAS Domain Structure

```
backend/app/lokas/
    ├── sristi/      # Breeding Core
    ├── bija_kosha/  # Germplasm & Inventory
    ├── rupa/        # Phenomics
    ├── kshetra/     # Field Operations
    ├── medha/       # Intelligence/Analytics
    ├── vani/        # Commercial
    └── vidya/       # Knowledge
```

### Future Modules (11 planned)

| Tier | Modules |
|------|---------|
| Tier 1 | Crop Intelligence, Soil & Nutrients, Crop Protection, Water & Irrigation, Market & Economics |
| Tier 2 | Sustainability, Farm Operations, Robotics, Post-Harvest, Livestock |
| Tier 3 | Aquaculture & Fisheries |

---

## 📚 Further Reading

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | System architecture |
| [GOVERNANCE.md](docs/architecture/GOVERNANCE.md) | Platform law |
| [CALF.md](docs/CALF.md) | Computational assessment |
| [API_REFERENCE.md](docs/api/API_REFERENCE.md) | API documentation |
| [CONTRIBUTOR_ENTRY.md](CONTRIBUTOR_ENTRY.md) | Role-based entry points |

---

*This document is maintained alongside the codebase. Last updated: January 2026.*
